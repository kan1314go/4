# coding=utf-8
import sys, json, base64, re, requests
sys.path.append('..')
from base.spider import Spider

class Spider(Spider):
    def getName(self):
        return "AV空投軍團"

    def init(self, extend=""):
        try:
            cfg = json.loads(base64.b64decode(extend).decode()) if extend else {}
        except Exception:
            cfg = {}
        self.host = (cfg.get("host") or "https://ipornbase.com").rstrip("/")
        self.ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
        self.s = requests.Session()
        self.s.headers.update({"User-Agent": self.ua, "Referer": self.host + "/"})

    def isVideoFormat(self, url):
        return ".m3u8" in url or ".mp4" in url

    def manualVideoCheck(self):
        return True

    def _get(self, path):
        r = self.s.get(self.host + path, timeout=15, verify=False)
        r.encoding = "utf-8"
        return r.text

    # webp 派生图 -> 原图；相对路径 -> 绝对路径
    def _pic(self, u):
        if not u:
            return ""
        u = re.sub(r'/sites/default/files/styles/[^/]+/public/', '/sites/default/files/', u)
        u = re.sub(r'\.webp(\?|$)', r'\1', u)
        u = re.sub(r'\?itok=[^&]*', '', u)
        if u.startswith("/"):
            u = self.host + u
        return u

    def _cards(self, html):
        pics = {}
        for m in re.finditer(r'href="([^"]*/video/[^"]+)"[^>]*>\s*(?:<picture>.*?)?<img[^>]+src="([^"]+)"', html, re.S):
            pics[m.group(1).rsplit("/", 1)[-1]] = self._pic(m.group(2))

        out, seen = [], set()
        for m in re.finditer(r'<div class="videotitle[^"]*"><a href="([^"]*/video/[^"]+)"[^>]*>([^<]+)</a>', html):
            vid = m.group(1).rsplit("/", 1)[-1]
            name = m.group(2).strip()
            if not name or vid in seen:
                continue
            seen.add(vid)
            out.append({"vod_id": vid, "vod_name": name,
                        "vod_pic": pics.get(vid, ""), "vod_remarks": ""})
        return out

    def homeContent(self, filter):
        cats = [
            {"type_id": "asian/new", "type_name": "亞洲國產·最近更新"},
            {"type_id": "asian/release", "type_name": "亞洲國產·最新發行"},
            {"type_id": "asian/today-hot", "type_name": "亞洲國產·今日熱門"},
            {"type_id": "asian/hot", "type_name": "亞洲國產·總觀看"},
            {"type_id": "japanese/new", "type_name": "日本AV·最近更新"},
            {"type_id": "japanese/release", "type_name": "日本AV·最新發行"},
            {"type_id": "uncensored-leak/new", "type_name": "JAV無碼·最近更新"},
            {"type_id": "fc2/new", "type_name": "FC2素人"},
            {"type_id": "hentai/new", "type_name": "裏番"},
            {"type_id": "western/new", "type_name": "歐美"},
            {"type_id": "korean/new", "type_name": "韓國直播"},
            {"type_id": "ai/new", "type_name": "AI短劇"},
            {"type_id": "chinese-subtitles", "type_name": "中文字幕"},
        ]
        return {"class": cats, "list": self._cards(self._get("/asian/new"))}

    def categoryContent(self, tid, pg, filter, extend):
        html = self._get(f"/{tid}?page={max(int(pg) - 1, 0)}")
        return {"list": self._cards(html), "page": int(pg),
                "pagecount": 9999, "limit": 12, "total": 999999}

    def searchContent(self, key, quick, pg="1"):
        html = self._get(f"/search?fulltext={requests.utils.quote(key)}&page={max(int(pg) - 1, 0)}")
        return {"list": self._cards(html), "page": int(pg)}

    def _srcs(self, html):
        eps = []
        m = re.search(r'window\.m3u8List\s*=\s*(\[.*?\])', html, re.S)
        if m:
            try:
                eps = [x for x in json.loads(m.group(1)) if x]
            except Exception:
                eps = re.findall(r'"(https?://[^"]+)"', m.group(1))
        if not eps:
            eps = re.findall(r'"contentUrl"\s*:\s*"(https?://[^"]+)"', html)
        return list(dict.fromkeys(eps))

    def detailContent(self, ids):
        vid = ids[0]
        html = self._get(f"/video/{vid}")
        title = (re.search(r'<h1 class="vdtitle">([^<]+)', html) or [None, vid])[1].strip()
        pic = self._pic((re.search(r'property="og:image" content="([^"]+)"', html) or [None, ""])[1])
        desc = (re.search(r'name="description" content="([^"]*)"', html) or [None, ""])[1]

        eps = self._srcs(html)
        if eps:
            play_from = "默認"
            play_url = "#".join(f"線路{i+1}${u}" for i, u in enumerate(eps))
        else:
            play_from = "失效"
            play_url = ""

        return {"list": [{"vod_id": vid, "vod_name": title, "vod_pic": pic,
                          "vod_content": desc, "vod_play_from": play_from,
                          "vod_play_url": play_url}]}

    def playerContent(self, flag, id, vipFlags):
        hdr = json.dumps({"User-Agent": self.ua, "Referer": self.host + "/"})
        if ".m3u8" in id:
            token = base64.urlsafe_b64encode(id.encode()).decode()
            return {"parse": 0,
                    "url": "http://127.0.0.1:9978/proxy?do=py&type=m3u8&u=" + token,
                    "header": hdr}
        return {"parse": 0, "url": id, "header": hdr}

    def localProxy(self, param):
        raw = base64.urlsafe_b64decode(str(param.get("u")).encode()).decode()
        r = self.s.get(raw, timeout=15)
        base = raw.rsplit("/", 1)[0] + "/"
        lines = []
        for line in r.text.splitlines():
            t = line.strip()
            if not t or t.startswith("#"):
                lines.append(line)
            else:
                lines.append(t if t.startswith("http") else base + t)
        return [200, "application/vnd.apple.mpegurl", "\n".join(lines).encode(), {}]