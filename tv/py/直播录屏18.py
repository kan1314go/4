# 直播录屏18 蜘蛛（FongMi/TVBox 爬虫）
# 由 Hamo 插件「直播录屏」v1.0.2（com.hamo.lytvs.zhiboluping）按项目口径转换
import json
import re

import requests

from base.spider import Spider as BaseSpider

UA = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
DEFAULT_HOST = "https://www.lubosp.com"
HOST_CANDIDATES = ["https://www.lubosp.com", "https://www.lookluping.xyz"]
CLASSES = [("new", "最新视频"), ("hot", "热门精选"), ("zouguang", "走光合集"), ("free", "免费视频"),
           ("type01", "抖音快手"), ("type01c02", "百万粉丝博主"), ("type01c11", "十万粉丝博主"),
           ("type01c12", "高颜值女博主"), ("type27", "会议私播"), ("type28", "偷拍系列")]
VIP_CATS = {"type01": "type01", "type01c02": "type01/column02", "type01c11": "type01/column11",
            "type01c12": "type01/column12", "type27": "type27", "type28": "toupai/type28"}
POOL_BASES = ["type01", "type01/column02", "type01/column11", "type01/column12", "type27", "toupai/type28", "free"]
SEARCH_VIP_BASES = ["type01", "type01/column02", "type01/column11", "type01/column12", "type27", "toupai/type28"]
SIZE_NEW = 48
SIZE_PAGE = 24
SIZE_HOT = 15
SIZE_SEARCH = 80
FETCH_TIMEOUT = 8
PROBE_TIMEOUT = 6


def _clean_text(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"')
    s = re.sub(r"&#0?39;", "'", s)
    s = s.replace("&nbsp;", " ")
    return re.sub(r"\s+", " ", s).strip()


def _wrap_pic(pic, host):
    pic = (pic or "").strip()
    pic = re.sub(r"^[\"']", "", pic)
    pic = re.sub(r"[\"']$", "", pic)
    pic = pic.replace("&amp;", "&")
    if not pic:
        return ""
    if pic.startswith("//"):
        return "https:" + pic
    if not re.match(r"https?://", pic, re.I):
        return (host or "") + (pic if pic.startswith("/") else "/" + pic)
    return pic


def _parse_vip_items(html):
    items = []
    seen = set()
    for li in re.findall(r"<li[^>]*>[\s\S]*?</li>", html or "", re.I):
        im = re.search(r'<img[^>]+(?:data-original|src)="([^"]+)"', li, re.I)
        if not im or "vod.jpg" not in im.group(1):
            continue
        pic = im.group(1).replace("&amp;", "&").strip()
        if pic in seen:
            continue
        name = ""
        hm = re.search(r"<h2[^>]*>([\s\S]*?)</h2>", li, re.I)
        if hm:
            name = _clean_text(hm.group(1))
        if not name:
            tm = re.search(r'<a[^>]+title="([^"]*)"', li, re.I) or re.search(r'<img[^>]+alt="([^"]*)"', li, re.I)
            if tm:
                name = tm.group(1).strip()
        if not name or len(name) > 100:
            continue
        am = re.search(r'<a[^>]+href="([^"]+\.html)"', li, re.I)
        path = am.group(1).strip().lstrip("/").split("?")[0] if am else ""
        if path.endswith(".html"):
            path = path[:-5]
        if not re.match(r"^(free/|type|toupai/)", path):
            path = ""
        rm = re.search(r"ico-left[^>]*>([^<]+)<", li, re.I)
        seen.add(pic)
        items.append({
            "vod_id": "vip@" + pic.replace("vod.jpg", "index.m3u8") + "@@" + path,
            "vod_name": name[:50],
            "vod_pic": pic,
            "vod_remarks": rm.group(1).strip() if rm else "",
            "_path": path,
        })
    return items


def _parse_free_items(html, host):
    items = []
    seen = set()
    text = html or ""
    for m in re.finditer(r'<a href="([^"]*?/(\d+)\.html)"([^>]*)>([\s\S]*?)</a>', text, re.I):
        path = m.group(1).strip().lstrip("/")
        if not path.startswith("free/"):
            continue
        vid = m.group(2)
        if vid in seen:
            continue
        tm = re.search(r'title="([^"]*)"', m.group(3), re.I)
        name = tm.group(1).strip() if tm else _clean_text(m.group(4))
        if not name or len(name) > 100:
            continue
        seen.add(vid)
        after = text[m.end():m.end() + 800]
        img = re.search(r'<img[^>]+(?:data-original|original|src)="([^"]+)"', after, re.I)
        items.append({
            "vod_id": path,
            "vod_name": name[:50],
            "vod_pic": _wrap_pic(img.group(1) if img else "", host),
            "vod_remarks": "",
            "_path": path,
        })
    return items


def _parse_buy(html):
    b = re.search(r'buyvideo" classid="(\d+)" xxid="(\d+)"', html or "") or \
        re.search(r'classid="(\d+)"[^>]*xxid="(\d+)"', html or "")
    if b:
        return b.group(1), b.group(2)
    return "26", ""


def _pager_max(html):
    nums = [int(x) for x in re.findall(r"index_(\d+)\.(?:html|php)", html or "")]
    return max(nums) if nums else None


def _parse_related(html):
    text = html or ""
    idx = text.find("相关推荐")
    if idx < 0:
        return []
    ul = re.search(r"<ul[^>]*>([\s\S]*?)</ul>", text[idx:], re.I)
    if not ul:
        return []
    return _parse_vip_items(ul.group(1))


class Spider(BaseSpider):
    _host = None
    _pool = None

    def getName(self):
        return "直播录屏18"

    def initContent(self, extend=""):
        self._host = None
        self._pool = None

    def _clear_host(self, host):
        if self._host and self._host == host:
            self._host = None

    def _get_host(self):
        if self._host:
            return self._host
        for cand in HOST_CANDIDATES:
            try:
                resp = requests.get(cand + "/", headers={"User-Agent": UA, "Referer": cand + "/"},
                                    timeout=PROBE_TIMEOUT)
                body = resp.content.decode("utf-8", errors="replace") if resp.content else ""
                if 200 <= resp.status_code < 400 and len(body) > 100:
                    self._host = cand
                    return cand
            except Exception:
                continue
        self._host = DEFAULT_HOST
        return DEFAULT_HOST

    def _fetch(self, target, method="GET", form=None, referer=None):
        host = self._get_host()
        full = target or ""
        if full.startswith("//"):
            full = "https:" + full
        elif full.startswith("/"):
            full = host + full
        headers = {
            "User-Agent": UA,
            "Referer": referer or (host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            if method == "POST":
                resp = requests.post(full, data=form, headers=headers, timeout=FETCH_TIMEOUT)
            else:
                resp = requests.get(full, headers=headers, timeout=FETCH_TIMEOUT)
        except Exception:
            self._clear_host(host)
            raise
        if resp.status_code >= 400:
            self._clear_host(host)
        text = resp.content.decode("utf-8", errors="replace") if resp.content else ""
        fo = re.match(r"^(https?://[^/]+)", resp.url or full, re.I)
        return {"text": text, "status": resp.status_code, "host": fo.group(1) if fo else host}

    def _pub(self, item):
        return {"vod_id": item["vod_id"], "vod_name": item["vod_name"],
                "vod_pic": item["vod_pic"], "vod_remarks": item["vod_remarks"]}

    def _page_form(self, items, page, limit, pagecount, total):
        return {"list": [self._pub(it) for it in items], "page": page,
                "pagecount": pagecount, "limit": limit, "total": total}

    def _empty_form(self, page, limit):
        return {"list": [], "page": page, "pagecount": page, "limit": limit, "total": 0}

    def _get_pool(self):
        if self._pool is not None:
            return self._pool
        pool = []
        seen = set()
        for base in POOL_BASES:
            for pg in (1, 2, 3):
                url = "/" + base + "/" if pg == 1 else "/" + base + "/index_" + str(pg) + ".html"
                try:
                    html = self._fetch(url)["text"]
                except Exception:
                    break
                if not html or "信息提示" in html[:2000]:
                    break
                items = _parse_vip_items(html)
                if not items:
                    break
                for it in items:
                    if it["vod_id"] not in seen:
                        seen.add(it["vod_id"])
                        pool.append(it)
        self._pool = pool
        return pool

    def homeContent(self, filter):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in CLASSES]}

    def homeVideoContent(self):
        try:
            r = self._fetch("/")
            items = _parse_vip_items(r["text"])
            if not items:
                items = _parse_free_items(r["text"], r["host"])
            items = items[:SIZE_NEW]
        except Exception:
            items = []
        return {"list": [self._pub(it) for it in items]}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if pg else 1
        if tid == "new":
            if pg > 1:
                return self._empty_form(pg, SIZE_NEW)
            try:
                items = _parse_vip_items(self._fetch("/")["text"])[:SIZE_NEW]
            except Exception:
                items = []
            return self._page_form(items, pg, SIZE_NEW, 1, len(items))
        if tid == "hot":
            if pg > 1:
                return self._empty_form(pg, SIZE_HOT)
            try:
                text = self._fetch("/")["text"]
                hm = re.search(r'<div class="hide">\s*<ul[^>]*>([\s\S]*?)</ul>', text, re.I) or \
                    re.search(r'class="hide"[^>]*>\s*<ul[^>]*>([\s\S]*?)</ul>', text, re.I)
                items = _parse_vip_items(hm.group(1)) if hm else []
            except Exception:
                items = []
            return self._page_form(items, pg, len(items) or SIZE_HOT, 1, len(items))
        if tid == "zouguang":
            hits = [it for it in self._get_pool() if "走光" in it["vod_name"]]
            total = len(hits)
            if total == 0:
                return self._empty_form(pg, SIZE_PAGE)
            pagecount = (total + SIZE_PAGE - 1) // SIZE_PAGE
            start = (pg - 1) * SIZE_PAGE
            return self._page_form(hits[start:start + SIZE_PAGE], pg, SIZE_PAGE, pagecount, total)
        base = VIP_CATS.get(tid)
        if base:
            url = "/" + base + "/" if pg == 1 else "/" + base + "/index_" + str(pg) + ".html"
            try:
                html = self._fetch(url)["text"]
            except Exception:
                return self._empty_form(pg, SIZE_PAGE)
            if not html or "信息提示" in html[:2000]:
                return self._empty_form(pg, SIZE_PAGE)
            items = _parse_vip_items(html)
            pc = _pager_max(html)
            pagecount = pc if pc else pg
            total = pc * SIZE_PAGE if pc else (pg - 1) * SIZE_PAGE + len(items)
            return self._page_form(items, pg, SIZE_PAGE, pagecount, total)
        url = "/free/" if pg == 1 else "/free/index_" + str(pg) + ".html"
        try:
            r = self._fetch(url)
            html = r["text"]
        except Exception:
            return self._empty_form(pg, SIZE_PAGE)
        if not html or "信息提示" in html[:2000]:
            return self._empty_form(pg, SIZE_PAGE)
        items = _parse_free_items(html, r["host"])
        pc = _pager_max(html)
        pagecount = pc if pc else pg
        total = pc * SIZE_PAGE if pc else (pg - 1) * SIZE_PAGE + len(items)
        return self._page_form(items, pg, SIZE_PAGE, pagecount, total)

    def searchContent(self, wd, quick, pg=1):
        pg = int(pg) if pg else 1
        if pg > 1:
            return self._empty_form(pg, SIZE_SEARCH)
        key = (wd or "").strip().lower()
        if not key:
            return self._empty_form(1, SIZE_SEARCH)
        host = self._get_host()
        items = []
        seen = set()
        for p in (1, 2, 3, 4, 5):
            if len(items) >= SIZE_SEARCH:
                break
            url = "/free/" if p == 1 else "/free/index_" + str(p) + ".html"
            try:
                html = self._fetch(url)["text"]
            except Exception:
                break
            if not html or "信息提示" in html[:2000]:
                break
            for it in _parse_free_items(html, host):
                if key in it["vod_name"].lower() and it["vod_id"] not in seen:
                    seen.add(it["vod_id"])
                    items.append(it)
        if len(items) < SIZE_SEARCH:
            for base in SEARCH_VIP_BASES:
                try:
                    html = self._fetch("/" + base + "/")["text"]
                except Exception:
                    continue
                if not html or "信息提示" in html[:2000]:
                    continue
                for it in _parse_vip_items(html):
                    if key in it["vod_name"].lower() and it["vod_id"] not in seen:
                        seen.add(it["vod_id"])
                        items.append(it)
                if len(items) >= SIZE_SEARCH:
                    break
        items = items[:SIZE_SEARCH]
        return self._page_form(items, 1, len(items) if items else SIZE_SEARCH, 1, len(items))

    def _vod(self, vid, name, pic, genres, ep_value, rel_items=None):
        host = self._get_host()
        content = "\n".join([
            "🦋 直播录屏官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
            name,
        ])
        play_from = "直播录屏"
        play_url = "正片$" + ep_value
        rel_eps = []
        for it in rel_items or []:
            if it["vod_id"] == vid:
                continue
            ep_name = it["vod_name"].replace("$", "_").replace("#", "_")
            rel_eps.append(ep_name + "$rel:" + it["vod_id"])
        if rel_eps:
            play_from = play_from + "$$$相关推荐"
            play_url = play_url + "$$$" + "#".join(rel_eps)
        return {
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": pic,
            "vod_bg": pic,
            "vod_background": pic,
            "vod_banner": pic,
            "vod_class": genres,
            "vod_content": content,
            "vod_play_from": play_from,
            "vod_play_url": play_url,
        }

    def detailContent(self, ids):
        vid = ids[0] if ids else ""
        if vid.startswith("rel:"):
            vid = vid[4:]
        host = self._get_host()
        if vid.startswith("vip@"):
            parts = vid[4:].split("@@")
            m3u8 = parts[0]
            path = parts[1] if len(parts) > 1 else ""
            name = "会员视频"
            pic = m3u8.replace("index.m3u8", "vod.jpg") if m3u8 else ""
            rel_items = []
            if path:
                try:
                    text = self._fetch("/" + path + ".html")["text"]
                    hm = re.search(r"<h1[^>]*>([^<]+)</h1>", text, re.I)
                    if hm and hm.group(1).strip():
                        name = hm.group(1).strip()
                    segs = m3u8.split("/")
                    hash_seg = segs[-2] if len(segs) >= 2 else ""
                    own = ""
                    for u in re.findall(r'<img[^>]+src="([^"]*?/video/[^"]+)"', text, re.I):
                        if hash_seg and hash_seg in u:
                            own = u
                            break
                    if own:
                        pic = _wrap_pic(own, host)
                    rel_items = _parse_related(text)
                except Exception:
                    pass
            return {"list": [self._vod(vid, name, pic, "会员视频", vid, rel_items)]}
        path = re.sub(r"\.html$", "", (vid or "").lstrip("/"))
        try:
            html = self._fetch("/" + path + ".html")["text"]
        except Exception as e:
            return {"list": [], "msg": str(e)}
        if not html or "buyvideo" not in html:
            return {"list": [], "msg": "Detail page invalid"}
        name = ""
        h1 = re.search(r"<h1[^>]*>([^<]+)</h1>", html, re.I)
        if h1:
            name = h1.group(1).strip()
        if not name:
            t = re.search(r"<title>([^<]*)</title>", html, re.I)
            name = t.group(1).strip() if t else vid
        pic = ""
        for x in _parse_vip_items(html):
            if x["_path"] == path:
                pic = x["vod_pic"]
                break
        cid, buy_xid = _parse_buy(html)
        aidm = re.search(r"(\d+)", path)
        xid = buy_xid or (aidm.group(1) if aidm else "")
        ep = "free@" + path + "@@" + cid + "@@" + xid
        return {"list": [self._vod(vid, name, pic, "免费视频", ep, _parse_related(html))]}

    def playerContent(self, flag, id, vipFlags):
        headers = {"User-Agent": UA, "Referer": self._get_host() + "/"}
        try:
            return self._resolve(id, headers)
        except Exception as e:
            return {"parse": 0, "msg": str(e)}

    def _resolve(self, ep, headers):
        host = self._get_host()
        ep = ep or ""
        path = ""
        cid = ""
        xid = ""
        if ep.startswith("vip@"):
            parts = ep[4:].split("@@")
            m3u8 = parts[0]
            path = parts[1] if len(parts) > 1 else ""
            if m3u8 and ".m3u8" in m3u8:
                return {"parse": 0, "url": m3u8, "header": headers}
        elif ep.startswith("free@"):
            rest = ep[5:].split("@@")
            path = rest[0]
            cid = rest[1] if len(rest) > 1 else ""
            xid = rest[2] if len(rest) > 2 else ""
        else:
            raise ValueError("Invalid resolve target")
        path = re.sub(r"\.html$", "", path.lstrip("/"))
        if not path:
            raise ValueError("Invalid resolve target")
        if not xid:
            text = self._fetch("/" + path + ".html")["text"]
            if not text or "buyvideo" not in text:
                raise ValueError("Play page invalid")
            cid, buy_xid = _parse_buy(text)
            aidm = re.search(r"(\d+)", path)
            xid = buy_xid or (aidm.group(1) if aidm else "")
        resp = self._fetch("/e/moyublog/bofang/", method="POST",
                           form={"id": xid, "classid": cid}, referer=host + "/")
        nr = resp["text"] or ""
        try:
            obj = json.loads(nr)
            if isinstance(obj, dict) and obj.get("nr"):
                nr = str(obj["nr"])
        except Exception:
            pass
        m = re.search(r"url:\s*[\"']([^\"']+)[\"']", nr)
        if m:
            return {"parse": 0, "url": m.group(1).replace("\\/", "/"), "header": headers}
        sm = re.search(r"src\s*=\s*[\"']?\s*\\?(/e/DownSys/play/[^\"']+)", nr)
        if sm:
            page_url = host + sm.group(1).replace("\\/", "/").replace(" ", "")
            text = self._fetch(page_url)["text"]
            m2 = re.search(r"url:\s*[\"']([^\"']+)[\"']", text)
            if m2:
                return {"parse": 0, "url": m2.group(1).replace("\\/", "/"), "header": headers}
        raise ValueError("No stream url")

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249949558&sig=ec066c0e093421fa
