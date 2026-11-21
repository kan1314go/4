# -*- coding: utf-8 -*-
# AV星球 (com.butterfly.avxingqiu)

import json
import re
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
DEFAULT_HOST = "https://xqxq1.cc"
CLEAN_WORKER = "https://clean.5568999.cc.cd/clean"
SITE_NAME = "AV星球"
BRAND = "蝴蝶影视"
ACTOR = "🦋 TG群: @tvshare23"
DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专属线路"
RELATED_LINE = "相关推荐"
HOT_LINE = "热门推荐"
PAGE_SIZE = 32
PIC_RATIO = 1.78

CLASSES = [
    ("66", "学生萝莉"), ("44", "日本av"), ("62", "口交自慰"), ("63", "群交多P"),
    ("67", "强奸迷奸"), ("68", "丝袜制服"), ("46", "国产AV"), ("45", "乱伦系列"),
    ("65", "素人特摄"), ("47", "探花约炮"), ("61", "日韩精选"), ("64", "VR专区"),
    ("48", "主播大秀"), ("70", "反差母狗"), ("50", "国产传媒"), ("49", "网曝吃瓜"),
    ("71", "异域风情"), ("53", "中文字幕"), ("51", "偷拍偷窥"), ("55", "色情动漫"),
]

CARD_RE = re.compile(r'<a class="poster[^"]*" href="(/index\.php/vod/play/id/(\d+)\.html)" data-url="([^"]+)">\s*<img[^>]+data-src="([^"]+)"[^>]*alt="([^"]*)"')
CARD_RE2 = re.compile(r'href="(/index\.php/vod/play/id/(\d+)\.html)"[^>]*data-url="([^"]+)"[\s\S]*?data-src="([^"]+)"[^>]*alt="([^"]*)"')
DURATION_RE = re.compile(r'<span class="text-sm">([^<]+)</span>')
H1_RE = re.compile(r"<h1[^>]*>([^<]+)</h1>")
OG_IMAGE_RE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"')
LET_POSTER_RE = re.compile(r"let poster = '([^']+)'")
CONST_SOURCE_RE = re.compile(r"const source = '([^']+)'")
M3U8_RE = re.compile(r"(https?://[^\s\"']+\.m3u8[^\s\"']*)")
MEDIA_EXT_RE = re.compile(r"\.(m3u8|mp4|flv|ts)(\?|$)", re.I)
M3U8_WASH_RE = re.compile(r"\.m3u8(\?|$)", re.I)
REL_ANCHOR_RE = re.compile(r'<a class="poster[^"]*" href="/index\.php/vod/play/id/(\d+)\.html" data-url="[^"]*">\s*<img[^>]+?(?:data-src|src)="[^"]+"[^>]*alt="([^"]*)"')
HOT_ANCHOR_RE = re.compile(r'<a class="w-1/2 flex-shrink-0 mr-1" href="/index\.php/vod/play/id/(\d+)\.html">[\s\S]*?<img[^>]+?alt="([^"]*)"')
NUM_ENTITY_RE = re.compile(r"&#(\d+);")
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND, clean_meta)
    return BRAND


def _num_entity(m):
    try:
        return chr(int(m.group(1), 10))
    except Exception:
        return m.group(0)


def unescape_html(s):
    s = str(s or "")
    s = s.replace("&amp;", "&")
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&quot;", '"')
    s = re.sub(r"&#0?39;", "'", s)
    s = s.replace("&nbsp;", " ")
    s = NUM_ENTITY_RE.sub(_num_entity, s)
    return s


def strip_tags(s):
    return TAG_RE.sub("", str(s or ""))


def clean_text(s):
    return WS_RE.sub(" ", unescape_html(strip_tags(str(s or "")))).strip()


def sanitize_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST

    # ---------- lifecycle ----------

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        custom = ""
        ext = extend
        if isinstance(ext, str) and ext.strip():
            try:
                parsed = json.loads(ext)
                if isinstance(parsed, dict):
                    ext = parsed
            except Exception:
                pass
        if isinstance(ext, dict):
            custom = str(ext.get("host") or "").strip()
        elif isinstance(ext, str):
            custom = ext.strip()
        if custom.startswith("http"):
            self.host = custom.rstrip("/")

    def destroy(self):
        pass

    # ---------- http ----------

    def _abs_url(self, u):
        u = str(u or "").strip()
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return self.host + u
        if u.startswith("http"):
            return u
        return self.host + "/" + u

    def _fetch(self, target, referer=""):
        url = str(target or "")
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.host + url
        elif not url.startswith("http"):
            url = self.host + "/" + url
        headers = {
            "User-Agent": UA,
            "Referer": referer or (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            return resp.content.decode("utf-8", "replace")
        except Exception:
            return ""

    # ---------- cards ----------

    def _collect_cards(self, h, pattern):
        items = []
        seen = set()
        for m in pattern.finditer(h):
            href, vid, pic, title = m.group(1), m.group(2), m.group(4), m.group(5)
            if vid in seen:
                continue
            seen.add(vid)
            duration = ""
            block_m = re.search(re.escape(href) + r'"[^>]*>[\s\S]*?</a>', h)
            if block_m:
                dm = DURATION_RE.search(block_m.group(0))
                if dm:
                    duration = dm.group(1).strip()
            name = clean_text(title) or ("视频 " + vid)
            items.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": self._abs_url(pic),
                "vod_remarks": format_remarks(duration if duration else "高清"),
                "style": {"type": "rect", "ratio": PIC_RATIO},
            })
        return items

    def _parse_cards(self, h):
        items = self._collect_cards(h, CARD_RE)
        if not items:
            items = self._collect_cards(h, CARD_RE2)
        return items

    def _page_form(self, items, page):
        if items:
            return {
                "list": items,
                "page": page,
                "pagecount": page + 1,
                "limit": PAGE_SIZE,
                "total": (page + 1) * PAGE_SIZE,
            }
        return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": 0}

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        h = self._fetch("/index.php/vod/type/id/66.html")
        return {"list": self._parse_cards(h)}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        tid = str(tid or "66").strip() or "66"
        if page > 1:
            url = self.host + "/index.php/vod/type.html?id=" + tid + "&page=" + str(page)
        else:
            url = self.host + "/index.php/vod/type/id/" + tid + ".html"
        h = self._fetch(url)
        return self._page_form(self._parse_cards(h), page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_form([], page)
        url = "/index.php/vod/search.html?wd=" + quote(keyword, safe="") + "&page=" + str(page)
        h = self._fetch(url)
        return self._page_form(self._parse_cards(h), page)

    # ---------- detail ----------

    def _extract_play_url(self, h, vid):
        play_url = ""
        src_m = CONST_SOURCE_RE.search(h)
        if src_m:
            play_url = src_m.group(1)
        if not play_url:
            dm = re.search(r'href="/index\.php/vod/play/id/' + re.escape(str(vid)) + r'\.html"[^>]*data-url="([^"]+)"', h)
            if dm:
                du = dm.group(1)
                play_url = "$".join(du.split("$")[1:]) if "$" in du else du
        if not play_url:
            mm = M3U8_RE.search(h)
            if mm:
                play_url = mm.group(1)
        return self._abs_url(play_url) if play_url else ""

    def _parse_related(self, h, self_vid):
        items = []
        seen = set()
        for m in REL_ANCHOR_RE.finditer(h):
            vid = m.group(1)
            if vid == str(self_vid) or vid in seen:
                continue
            seen.add(vid)
            title = clean_text(m.group(2)) or ("视频 " + vid)
            items.append((vid, title))
        return items

    def _parse_hot(self, h, self_vid):
        items = []
        seen = set()
        for m in HOT_ANCHOR_RE.finditer(h):
            vid = m.group(1)
            if vid == str(self_vid) or vid in seen:
                continue
            seen.add(vid)
            title = clean_text(m.group(2)) or ("视频 " + vid)
            items.append((vid, title))
        return items

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _summary(self, title, vid, related_titles):
        parts = [self._brand_block()]
        parts.append("标题：" + title)
        parts.append("分类：")
        parts.append("片源：" + LINE_NAME)
        parts.append("编号：" + str(vid))
        if related_titles:
            parts.append("相关推荐：" + "、".join(related_titles[:6]))
        return "\n".join(parts)

    def detailContent(self, ids):
        vid = str(ids[0]) if ids else ""
        if not vid:
            return {"list": []}
        play_page = self.host + "/index.php/vod/play/id/" + vid + ".html"
        h = self._fetch(play_page)
        if not h:
            return {"list": []}

        title = ""
        h1 = H1_RE.search(h)
        if h1:
            title = clean_text(h1.group(1))
        if not title:
            title = vid

        pic = ""
        og = OG_IMAGE_RE.search(h)
        if og:
            pic = og.group(1)
        if not pic:
            lp = LET_POSTER_RE.search(h)
            if lp:
                pic = lp.group(1)
        poster = self._abs_url(pic) if pic else ""

        play_url = self._extract_play_url(h, vid)
        if play_url:
            ep_ref = {"playUrl": play_url}
        else:
            ep_ref = {"pageUrl": play_page}

        related = self._parse_related(h, vid)
        hot = self._parse_hot(h, vid)

        from_names = [LINE_NAME]
        url_groups = ["正片$" + json.dumps(ep_ref, ensure_ascii=False)]
        if related:
            from_names.append(RELATED_LINE)
            eps = []
            for rvid, rtitle in related:
                eps.append(sanitize_ep_name(rtitle) + "$rel:" + rvid)
            url_groups.append("#".join(eps))
        if hot:
            from_names.append(HOT_LINE)
            eps = []
            for hvid, htitle in hot:
                eps.append(sanitize_ep_name(htitle) + "$rel:" + hvid)
            url_groups.append("#".join(eps))

        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": ACTOR,
            "vod_director": DIRECTOR,
            "vod_remarks": format_remarks("超清正片"),
            "vod_content": self._summary(title, vid, [t for _, t in related]),
            "vod_play_from": "$$$".join(from_names),
            "vod_play_url": "$$$".join(url_groups),
        }
        return {"list": [vod]}

    # ---------- player ----------

    def _wash_url(self, url):
        if not M3U8_WASH_RE.search(url or ""):
            return url
        return CLEAN_WORKER + "?u=" + quote(url, safe="") + "&r=" + quote(self.host + "/", safe="")

    def _play_headers(self):
        return {"User-Agent": UA, "Referer": self.host + "/"}

    def _resolve_stream(self, play_url):
        return {"parse": 0, "url": self._wash_url(play_url), "header": self._play_headers()}

    def _resolve_page(self, page_url):
        if MEDIA_EXT_RE.search(page_url or ""):
            return {"parse": 0, "url": page_url, "header": self._play_headers()}
        h = self._fetch(page_url)
        src_m = CONST_SOURCE_RE.search(h)
        if src_m:
            return self._resolve_stream(src_m.group(1))
        return {"parse": 1, "url": page_url, "header": self._play_headers()}

    def playerContent(self, flag, id, vipFlags):
        pid = str(id or "")
        if pid.startswith("rel:"):
            rid = pid[4:].strip()
            if not rid:
                return {"parse": 1, "url": self.host + "/", "header": self._play_headers()}
            page_url = self.host + "/index.php/vod/play/id/" + rid + ".html"
            h = self._fetch(page_url)
            play_url = self._extract_play_url(h, rid) if h else ""
            if play_url:
                return self._resolve_stream(play_url)
            return {"parse": 1, "url": page_url, "header": self._play_headers()}
        ref = {}
        try:
            parsed = json.loads(pid)
            if isinstance(parsed, dict):
                ref = parsed
        except Exception:
            ref = {}
        play_url = str(ref.get("playUrl") or "")
        if play_url:
            return self._resolve_stream(play_url)
        page_url = str(ref.get("pageUrl") or "")
        if page_url:
            return self._resolve_page(page_url)
        return {"parse": 1, "url": self.host + "/", "header": self._play_headers()}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249980022&sig=14b66d19feae50e6
