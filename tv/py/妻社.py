# 妻社 Python蜘蛛

import gzip
import hashlib
import http.cookiejar
import json
import re
import ssl
import urllib.request
import zlib
from urllib.parse import quote

from base.spider import Spider as BaseSpider


VERSION = "V1.1"
DISCOVER = [
    "https://qsh5.xuanyipai.com/api.php",
    "https://qsh5.newfangchan.cn/api.php",
    "https://qs.qsazap2025by2.com/api.php",
]
FALLBACK_HOST = "h51.qisheh526222.org"
UA = ("Mozilla/5.0 (Linux; Android 14; Redmi K70) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36")
CATS = [
    ("0", "推荐"), ("2", "妻友圈"), ("4", "夫妻认证交友"),
    ("5", "夫妻交换"), ("6", "调教露出"), ("7", "素质单男"),
    ("9", "淫妻分享"), ("11", "绿帽献妻"),
    ("22", "经验分享"), ("25", "母狗公示榜"), ("44", "妻社私密树洞"),
]
CAT_NAMES = dict(CATS)
PAGE_SIZE_INDEX = 20
PAGE_SIZE_THREAD = 100
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"


def format_remarks(brand="蝴蝶影视", meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


class Spider(BaseSpider):
    def __init__(self):
        self._host = None
        self._cache = {}
        self.extend = ""
        self.options = {}
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=self.ctx)
        )

    def init(self, extend=""):
        self.extend = extend or ""
        if isinstance(extend, dict):
            self.options = extend
        elif extend:
            try:
                self.options = json.loads(extend)
            except Exception:
                self.options = {}
        return True

    def getName(self):
        return "妻社"

    def _gunzip(self, raw):
        if not raw:
            return b""
        if raw[:2] != b"\x1f\x8b":
            return raw
        try:
            return gzip.decompress(raw)
        except Exception:
            pass
        try:
            d = zlib.decompressobj(31)
            out = d.decompress(raw)
            out += d.flush()
            return out
        except Exception:
            return b""

    def _http(self, url, headers=None):
        hd = {"User-Agent": UA, "Accept-Encoding": "gzip"}
        if headers:
            hd.update(headers)
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=hd, method="GET")
                with self.opener.open(req, timeout=8) as r:
                    raw = r.read()
                    enc = (r.headers.get("Content-Encoding") or "").lower()
                    if raw[:2] == b"\x1f\x8b" or enc == "gzip":
                        raw = self._gunzip(raw)
                    return json.loads(raw.decode("utf-8", "ignore"))
            except Exception as e:
                part = getattr(e, "partial", None)
                if part:
                    try:
                        return json.loads(self._gunzip(part).decode("utf-8", "ignore"))
                    except Exception:
                        pass
        return None

    def _discover_host(self):
        if self._host:
            return self._host
        for u in DISCOVER:
            try:
                r = self._http(u)
                if isinstance(r, dict) and r.get("domain"):
                    self._host = r["domain"]
                    return self._host
            except Exception:
                continue
        self._host = FALLBACK_HOST
        return self._host

    def _sign(self, action):
        host = self._discover_host()
        s = "url=%s&version=%s&time=DATA&domain=%s" % (action, VERSION, host)
        return hashlib.md5(s.encode("utf-8")).hexdigest()

    def _api(self, action, params=None):
        host = self._discover_host()
        q = {
            "sign": self._sign(action),
            "version": VERSION,
            "token": "",
            "pushcid": "",
            "devicebrand": "Xiaomi",
            "platform": "h5",
        }
        if params:
            q.update(params)
        qs = "&".join("%s=%s" % (k, quote(str(v), safe="")) for k, v in q.items())
        url = "https://%s/source/plugin/qsts_app/index.php/%s?%s" % (host, action, qs)
        return self._http(url)

    def _site_url(self):
        return "https://" + (self._host or FALLBACK_HOST)

    def _abs_url(self, url):
        u = str(url or "").strip()
        if not u:
            return ""
        if u.startswith("https://") or u.startswith("http://"):
            return u
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return "https://" + (self._host or FALLBACK_HOST) + u
        return u

    def _videos_of(self, t):
        videos = []
        cover = ""
        try:
            atts = ((t.get("attachData") or {}).get("data") or [])
        except Exception:
            atts = []
        for a in atts:
            if not isinstance(a, dict):
                continue
            url = self._abs_url(a.get("defurl") or a.get("attachment") or "")
            if a.get("isimage") == "1" or a.get("isimage") == 1:
                if url and not cover:
                    cover = url
                continue
            if not url:
                continue
            if "m3u8" in url:
                orig = None
                ext = ""
                if url.endswith(".m3u8/ts.m3u8"):
                    orig = url[:-len(".m3u8/ts.m3u8")]
                    m = re.search(r"\.([A-Za-z0-9]+)$", orig)
                    ext = (m.group(1).upper() if m else "原片")
                videos.append({"m3u8": url, "orig": orig, "ext": ext})
            elif re.search(r"\.(mp4|mov|avi|mkv|flv|wmv)$", url, re.I):
                m = re.search(r"\.([A-Za-z0-9]+)$", url)
                videos.append({"m3u8": None, "orig": url,
                               "ext": (m.group(1).upper() if m else "原片")})
        return videos, cover

    def _meta_text(self, t):
        views = t.get("views") or ""
        replies = t.get("replies") or ""
        meta = ""
        if views:
            meta = "浏览%s" % views
        if replies:
            meta = (meta + " · " if meta else "") + "回复%s" % replies
        return meta

    def _vod(self, t):
        if not isinstance(t, dict):
            return None
        tid = str(t.get("tid") or "")
        if not tid:
            return None
        videos, cover = self._videos_of(t)
        if not videos:
            return None
        self._cache[tid] = t
        fid = str(t.get("fid") or "")
        subject = (t.get("subject") or "").strip() or tid
        return {
            "vod_id": "vod/" + tid + "@@" + fid,
            "vod_name": subject,
            "vod_pic": cover,
            "vod_remarks": format_remarks("蝴蝶影视", self._meta_text(t)),
            "style": {"type": "rect", "ratio": 1.78},
        }

    def _list_from(self, items):
        out = []
        for t in items or []:
            v = self._vod(t)
            if v:
                out.append(v)
        return out

    def homeContent(self, filter):
        result = {"class": [{"type_id": i, "type_name": n} for i, n in CATS]}
        if filter:
            result["filters"] = {}
        return result

    def homeVideoContent(self):
        items = []
        seen = set()
        for pg in ("1", "2", "3"):
            r = self._api("post.getIndexList", {"page": pg})
            page_items = []
            if isinstance(r, dict) and isinstance(r.get("data"), dict):
                page_items = r["data"].get("list") or []
            for t in page_items:
                tid = str(t.get("tid") or "")
                if tid and tid not in seen:
                    seen.add(tid)
                    items.append(t)
            if not page_items:
                break
        return {"list": self._list_from(items)}

    def _page(self, items, pg, size):
        try:
            page = max(1, int(pg))
        except (TypeError, ValueError):
            page = 1
        total = len(items)
        start = (page - 1) * size
        return {
            "list": items[start:start + size],
            "page": page,
            "pagecount": max(1, (total + size - 1) // size),
            "limit": size,
            "total": total,
        }

    def _page_server(self, items, pg, size, full):
        try:
            page = max(1, int(pg))
        except (TypeError, ValueError):
            page = 1
        n = len(items)
        if n == 0:
            return {"list": [], "page": page, "pagecount": 1, "limit": size, "total": 0}
        if full:
            return {"list": items, "page": page, "pagecount": page + 1,
                    "limit": size, "total": page * size + 100}
        return {"list": items, "page": page, "pagecount": page,
                "limit": size, "total": (page - 1) * size + n}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = max(1, int(pg))
        except (TypeError, ValueError):
            page = 1
        if str(tid) == "0":
            r = self._api("post.getIndexList", {"page": str(page)})
            items = []
            if isinstance(r, dict) and isinstance(r.get("data"), dict):
                items = r["data"].get("list") or []
            return self._page_server(self._list_from(items), page, PAGE_SIZE_INDEX,
                                    len(items) >= PAGE_SIZE_INDEX)
        r = self._api("postlist.getThreadList", {"fid": str(tid), "page": str(page), "perpage": "100"})
        items = []
        if isinstance(r, dict) and isinstance(r.get("data"), dict):
            items = r["data"].get("list") or []
        return self._page_server(self._list_from(items), page, PAGE_SIZE_THREAD,
                                len(items) >= PAGE_SIZE_THREAD)

    def _split_vod_id(self, raw):
        s = str(raw or "")
        if s.startswith("vod/"):
            s = s[4:]
        if "@@" in s:
            tid, fid = s.split("@@", 1)
            return tid, fid
        return s, ""

    def _find_in_forum(self, fid, tid):
        for pg in ("1", "2"):
            r = self._api("postlist.getThreadList", {"fid": fid, "page": pg, "perpage": "100"})
            items = []
            if isinstance(r, dict) and isinstance(r.get("data"), dict):
                items = r["data"].get("list") or []
            for t in items:
                if str(t.get("tid") or "") == tid:
                    return t
            if not items:
                break
        return None

    def _find_in_index(self, tid):
        for pg in ("1", "2", "3"):
            r = self._api("post.getIndexList", {"page": pg})
            items = []
            if isinstance(r, dict) and isinstance(r.get("data"), dict):
                items = r["data"].get("list") or []
            for t in items:
                if str(t.get("tid") or "") == tid:
                    return t
            if not items:
                break
        return None

    def _build_content(self, title, cat_name, message, tid):
        lines = []
        lines.append("🦋 蝴蝶影视官方交流群：@tvshare23")
        lines.append("当前主站域名：" + self._site_url())
        lines.append("━" * 28)
        lines.append("━" * 7)
        if message:
            lines.append(message)
            lines.append("TG群：https://t.me/tvshare23")
        else:
            lines.append("标题：" + title)
            lines.append("分类：" + cat_name)
            lines.append("片源：妻社")
            lines.append("编号：" + tid)
            lines.append("🦋 蝴蝶影视 | TG群: @tvshare23")
        return "\n".join(lines).replace("导演", "")

    def detailContent(self, ids):
        raw = str(ids[0] if ids else "")
        tid, fid = self._split_vod_id(raw)
        t = self._cache.get(tid)
        if t is None and fid:
            t = self._find_in_forum(fid, tid)
        if t is None:
            t = self._find_in_index(tid)
        if t is None:
            return {"list": [], "msg": "未找到该影片"}
        videos, cover = self._videos_of(t)
        if not videos:
            return {"list": [], "msg": "未找到该影片"}
        self._cache[tid] = t
        plays = []
        for i, v in enumerate(videos):
            if v.get("m3u8"):
                plays.append("视频%s$%s" % (i + 1, v["m3u8"]))
            if v.get("orig"):
                plays.append("视频%s-%s$%s" % (i + 1, v.get("ext") or "原片", v["orig"]))
        subject = (t.get("subject") or "").strip() or tid
        fid2 = str(t.get("fid") or fid or "")
        cat_name = CAT_NAMES.get(fid2, "")
        message = re.sub(r"<[^>]+>", "", str(t.get("message") or "")).strip()
        actor = (t.get("author") or "").strip() or BRAND_ACTOR
        item = {
            "vod_id": raw or tid,
            "vod_name": subject,
            "vod_pic": cover,
            "vod_bg": cover,
            "vod_background": cover,
            "vod_banner": cover,
            "vod_actor": actor,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks("蝴蝶影视", self._meta_text(t)),
            "vod_content": self._build_content(subject, cat_name, message, tid),
            "type_name": cat_name,
            "vod_play_from": "妻社",
            "vod_play_url": "#".join(plays),
        }
        return {"list": [item]}

    def searchContent(self, key, quick, pg="1"):
        query = str(key or "").strip()
        if not query:
            return self._page([], pg, PAGE_SIZE_INDEX)
        r = self._api("cearch.search", {"page": str(pg), "perpage": "10",
                                        "keywords": query, "isUser": "false", "type": "all"})
        if isinstance(r, dict) and r.get("code") == 200 and isinstance(r.get("data"), dict):
            threads = r["data"].get("threads") or []
            out = self._list_from(threads)
            if out:
                return self._page(out, pg, PAGE_SIZE_INDEX)
        out = []
        for p in ("1", "2", "3"):
            rr = self._api("post.getIndexList", {"page": p})
            items = []
            if isinstance(rr, dict) and isinstance(rr.get("data"), dict):
                items = rr["data"].get("list") or []
            for t in items:
                hay = str(t.get("subject") or "") + str(t.get("message") or "")
                if query in hay:
                    v = self._vod(t)
                    if v:
                        out.append(v)
            if out:
                break
        return self._page(out, pg, PAGE_SIZE_INDEX)

    def playerContent(self, flag, id, vipFlags):
        url = str(id or "").strip()
        if not url:
            return {"parse": 0, "msg": "未取得播放地址"}
        return {"parse": 0, "jx": 0, "url": url,
                "header": {"User-Agent": UA, "Referer": self._site_url() + "/"}}

    def action(self, action):
        return {"msg": "不支援此操作"}

    def liveContent(self):
        return ""

    def manualVideoCheck(self):
        return False

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        return any(k in low for k in (".m3u8", ".mp4", ".flv", ".mkv", ".avi", ".mov", ".wmv", ".ts", ".mpd"))

    def destroy(self):
        self.options = {}
