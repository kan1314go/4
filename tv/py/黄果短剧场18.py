# -*- coding: utf-8 -*-
# 黄果剧场 蜘蛛（源自 Hamo 插件 com.butterfly.huangguo1 的解析逻辑移植）
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://huangguo.video"
    UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/27.0.1 Mobile/15E148 Safari/604.1"
    COOKIE = "hg_age=1"
    CLASSES = [
        ("1", "MV/音乐剧"), ("2", "短片"), ("3", "连续剧"), ("4", "片段"),
    ]
    TAG_OPTS = [
        ("全部", ""), ("都市", "1"), ("人妻", "2"), ("校园", "5"), ("职场", "6"),
        ("古风", "7"), ("乱伦", "8"), ("NTR", "9"), ("玄幻", "40"),
    ]
    CLASS_FILTERS = [
        {"key": "rating", "name": "尺度", "value": [
            {"n": "全部", "v": ""}, {"n": "安全", "v": "safe"}, {"n": "裸露", "v": "nude"}, {"n": "限制级", "v": "explicit"},
        ]},
        {"key": "tags", "name": "标签", "value": [{"n": n, "v": v} for n, v in TAG_OPTS]},
        {"key": "sort", "name": "排序", "value": [
            {"n": "最新发布", "v": "latest"}, {"n": "最热", "v": "hot"},
        ]},
    ]

    def getName(self):
        return "黄果剧场"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")

    def _fetch(self, url, referer=""):
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.host + url
        headers = {
            "User-Agent": self.UA,
            "Referer": referer or (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Cookie": self.COOKIE,
        }
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read()
                if raw:
                    text = raw.decode("utf-8", "replace")
                    if text.strip():
                        return text
            except Exception:
                pass
            time.sleep(0.5)
        return ""

    def _unescape(self, s):
        out = str(s or "")
        out = out.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        out = out.replace("&quot;", '"').replace("&#39;", "'").replace("&#039;", "'").replace("&nbsp;", " ")
        return out

    def _clean_text(self, s):
        return re.sub(r"\s+", " ", self._unescape(re.sub(r"<[^>]+>", "", str(s or "")))).strip()

    def _remarks(self, parts):
        clean = []
        for p in parts or []:
            t = str(p or "").strip()
            if t:
                clean.append(t)
        if not clean:
            return "蝴蝶影视"
        return "蝴蝶影视 | " + " · ".join(clean)

    def _parse_list(self, html):
        items = []
        seen = set()
        for m in re.finditer(r'<article class="(?:video-card|search-content-card)[^"]*">([\s\S]*?)</article>', html or ""):
            block = m.group(1)
            lm = re.search(r'<a\s+href="(/(?:video|series)/[^"]+)"', block)
            if not lm:
                continue
            path = lm.group(1).strip()
            if path.startswith("/video/"):
                vid = "video:" + path[7:].strip("/")
            else:
                vid = "series:" + path[8:].strip("/")
            if vid in seen:
                continue
            img_m = re.search(r'<img[^>]+src="([^"]+)"', block)
            cover = img_m.group(1).strip() if img_m else ""
            if cover.startswith("/"):
                cover = self.host + cover
            title = ""
            alt_m = re.search(r'<img[^>]+alt="([^"]*)"', block)
            if alt_m:
                title = alt_m.group(1).strip()
            if not title:
                t_m = re.search(r'<p[^>]*class="[^"]*(?:text-cream|font-display)[^"]*"[^>]*>([^<]+)</p>', block)
                if t_m:
                    title = t_m.group(1).strip()
            tag_m = re.search(r'<span class="absolute bottom-2 right-2[^"]*">([^<]+)</span>', block)
            sub_m = re.search(r'<p class="mt-2[^"]*font-mono-meta[^"]*">([\s\S]*?)</p>', block)
            sub = self._clean_text(sub_m.group(1)) if sub_m else ""
            seen.add(vid)
            items.append({
                "vod_id": vid,
                "vod_name": self._unescape(title),
                "vod_pic": cover,
                "vod_remarks": self._remarks([tag_m.group(1).strip() if tag_m else "", sub]),
            })
        return items

    def _extract_title(self, html):
        m = re.search(r"<title>([\s\S]*?)</title>", html or "")
        if not m:
            return ""
        return re.sub(r"\s*[-–|·]\s*黄果剧场.*$", "", m.group(1).strip()).strip()

    def _extract_cover(self, html):
        m = re.search(r'<meta\s+property="og:image"\s+content="([^"]+)"', html or "")
        if m:
            return m.group(1).strip()
        m = re.search(r'data-poster="([^"]+)"', html or "")
        if m:
            pic = m.group(1).strip()
            return pic if pic.startswith("http") else (self.host + pic)
        return ""

    def _extract_intro(self, html):
        m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', html or "")
        return m.group(1).strip() if m else ""

    def _extract_hls(self, html):
        m = re.search(r'data-hls="([^"]+)"', html or "")
        if not m:
            return ""
        url = m.group(1).strip()
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.host + url
        return url

    def _extract_episodes(self, html):
        eps = []
        seen = set()
        for m in re.finditer(r'<a[^>]+class="[^"]*ep-chip[^"]*"[^>]+href="(/video/[^"]+)"[^>]*>([^<]+)</a>', html or ""):
            path = m.group(1).strip()
            ep_id = path[7:].strip("/")
            if ep_id in seen:
                continue
            seen.add(ep_id)
            eps.append({"name": m.group(2).strip(), "ep_id": ep_id, "url": self.host + path})
        if not eps:
            for m in re.finditer(r'<a[^>]+href="(/video/[^"]+)"[^>]*class="[^"]*group[^"]*"[^>]*>([\s\S]*?)</a>', html or ""):
                p = m.group(1).strip()
                ep_id = p[7:].strip("/")
                if ep_id in seen:
                    continue
                nm = re.search(r'<p[^>]*class="[^"]*font-display[^"]*"[^>]*>([^<]+)</p>', m.group(2))
                seen.add(ep_id)
                eps.append({"name": nm.group(1).strip() if nm else ("第" + str(len(eps) + 1) + "集"), "ep_id": ep_id, "url": self.host + p})
        return eps

    def _extract_series_url(self, html):
        m = re.search(r'data-series-url="([^"]+)"', html or "")
        if not m:
            return ""
        url = m.group(1).strip()
        return url if url.startswith("http") else (self.host + url)

    def _mp4_from_m3u8(self, master_url, referer):
        if not master_url:
            return ""
        content = self._fetch(master_url, referer=referer or "")
        if not content:
            return ""
        m = re.search(r"https?://[^\s\"'<>\\]+\.mp4[^\s\"'<>\\]*", content)
        if m:
            return m.group(0)
        base = "/".join(master_url.split("/")[:-1])
        sub_urls = []
        for line in content.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("http") and ".m3u8" in line:
                sub_urls.append(line)
            elif ".m3u8" in line:
                sub_urls.append(base + "/" + line.lstrip("/"))
        priority = ["720p", "1080p", "480p", "360p"]

        def score(u):
            for j, p in enumerate(priority):
                if p in u:
                    return j
            return 99

        sub_urls.sort(key=score)
        for sub in sub_urls:
            sub_content = self._fetch(sub, referer=referer or "")
            if not sub_content:
                continue
            mm = re.search(r"https?://[^\s\"'<>\\]+\.mp4[^\s\"'<>\\]*", sub_content)
            if mm:
                return mm.group(0)
            sub_base = "/".join(sub.split("/")[:-1])
            for sline in sub_content.split("\n"):
                sline = sline.strip()
                if not sline or sline.startswith("#"):
                    continue
                if ".mp4" in sline:
                    if sline.startswith("http"):
                        return sline
                    if sline.startswith("/"):
                        return self.host + sline
                    return sub_base + "/" + sline
        return ""

    def homeContent(self, filter=False):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]
        result = {"class": classes}
        if filter:
            result["filters"] = dict((cid, self.CLASS_FILTERS) for cid, _ in self.CLASSES)
        return result

    def homeVideoContent(self):
        html = self._fetch("/videos")
        return {"list": self._parse_list(html)[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        q = ["category=" + str(tid or "1")]
        if isinstance(extend, dict):
            if extend.get("rating"):
                q.append("rating=" + urllib.parse.quote(str(extend["rating"]), safe=""))
            if extend.get("tags"):
                q.append("tags=" + urllib.parse.quote(str(extend["tags"]), safe=""))
            if extend.get("sort"):
                q.append("sort=" + urllib.parse.quote(str(extend["sort"]), safe=""))
        if page > 1:
            q.append("page=" + str(page))
        html = self._fetch("/videos?" + "&".join(q))
        items = self._parse_list(html)
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        path = "/search?q=" + urllib.parse.quote(str(key), safe="")
        if page > 1:
            path += "&page=" + str(page)
        items = self._parse_list(self._fetch(path))
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        raw = str(ids[0] or "").strip()
        kind = "video"
        real_id = raw
        if raw.startswith("video:"):
            kind = "video"
            real_id = raw[6:]
        elif raw.startswith("series:"):
            kind = "series"
            real_id = raw[7:]
        url = self.host + "/" + kind + "/" + real_id
        html = self._fetch(url)
        if not html:
            return {"list": []}
        title = self._extract_title(html) or real_id
        pic_raw = self._extract_cover(html)
        pic = pic_raw if pic_raw.startswith("http") else ""
        intro = self._extract_intro(html)
        episodes = []
        if kind == "series":
            for ep in self._extract_episodes(html):
                name = re.sub(r"[$#]", "", str(ep["name"]))
                val = json.dumps({"videoPage": ep["url"]}, ensure_ascii=False)
                episodes.append(name + "$" + val)
        else:
            series_url = self._extract_series_url(html)
            if series_url:
                s_html = self._fetch(series_url)
                for ep in self._extract_episodes(s_html):
                    name = re.sub(r"[$#]", "", str(ep["name"]))
                    val = json.dumps({"videoPage": ep["url"]}, ensure_ascii=False)
                    episodes.append(name + "$" + val)
            if not episodes:
                vurl = self._extract_hls(html)
                if vurl:
                    val = json.dumps({"directUrl": vurl}, ensure_ascii=False)
                    episodes.append("正片$" + val)
                else:
                    val = json.dumps({"videoPage": url}, ensure_ascii=False)
                    episodes.append("正片$" + val)
        lines = [
            "🦋 黄果短剧场官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        intro_clean = self._clean_text(intro)
        if intro_clean:
            lines.append(intro_clean)
        else:
            lines.append("标题：" + title)
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + raw)
        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": self._remarks(["共" + str(len(episodes)) + "集"]),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        video_page = ""
        direct_url = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                video_page = str(data.get("videoPage") or "")
                direct_url = str(data.get("directUrl") or "")
        except Exception:
            pass
        headers = {"User-Agent": self.UA, "Referer": self.host + "/", "Cookie": self.COOKIE}
        if direct_url:
            if ".m3u8" in direct_url:
                mp4 = self._mp4_from_m3u8(direct_url, self.host + "/")
                return {"parse": 0, "playUrl": "", "url": mp4 or direct_url, "header": headers}
            return {"parse": 0, "playUrl": "", "url": direct_url, "header": headers}
        if video_page:
            html = self._fetch(video_page)
            master = self._extract_hls(html)
            if master:
                mp4 = self._mp4_from_m3u8(master, video_page)
                play_headers = {"User-Agent": self.UA, "Referer": video_page, "Origin": self.host, "Cookie": self.COOKIE}
                return {"parse": 0, "playUrl": "", "url": mp4 or master, "header": play_headers}
            return {"parse": 1, "playUrl": "", "url": video_page, "header": headers}
        return {"parse": 1, "playUrl": "", "url": "", "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249721103&sig=7d6e163439750a1d
