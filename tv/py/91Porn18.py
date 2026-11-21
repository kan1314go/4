# -*- coding: utf-8 -*-
# 91Porn - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.91porn)
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://91porn.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
SITE_NAME = "91Porn"
BRAND = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专属直连"
PAGE_SIZE = 24
PIC_RATIO = 0.56
COOKIE = "language=cn_CN; watch_times=1"

CLASSES = [
    ("video", "全部视频", "next=watch"),
    ("ori", "91原创", "category=ori&viewtype=basic"),
    ("hot", "当前最热", "category=hot&viewtype=basic"),
    ("top", "本月最热", "category=top&viewtype=basic"),
    ("top_last", "上月最热", "category=top&m=-1&viewtype=basic"),
    ("rf", "最近加精", "category=rf&viewtype=basic"),
    ("long", "10分钟以上", "category=long&viewtype=basic"),
    ("longer", "20分钟以上", "category=longer&viewtype=basic"),
    ("tf", "本月收藏", "category=tf&viewtype=basic"),
    ("mf", "收藏最多", "category=mf&viewtype=basic"),
    ("md", "本月讨论", "category=md&viewtype=basic"),
    ("hd", "高清视频", "category=hd&viewtype=basic"),
]
CLASS_MAP = {}
for _cid, _cname, _cq in CLASSES:
    CLASS_MAP[_cid] = _cq

TITLE_BLACKLIST = ("91porn", "91porn.com", "首页", "登录", "注册", "视频", "watch")

CARD_RE = re.compile(
    r"<(?:article|div)[^>]+class=['\"][^'\"]*(?:vitem well-sm well|well\s+well-sm)[^'\"]*['\"][^>]*>"
    r"([\s\S]*?)"
    r"(?=(?:<(?:article|div)[^>]+class=['\"][^'\"]*(?:vitem well-sm well|well\s+well-sm)[^'\"]*['\"]|$))",
    re.I,
)
VIEWKEY_RE = re.compile(r"viewkey=([a-z0-9]+)", re.I)
THUMB_RE1 = re.compile(r"src=['\"](https?://[^'\"]+thumb[^'\"]+)['\"]", re.I)
THUMB_RE2 = re.compile(r"<img[^>]+src=['\"](https?://[^'\"]+\.(?:jpg|jpeg|png|webp)[^'\"]*)['\"]", re.I)
DUR_RE1 = re.compile(r"duration['\"]?>([^<]+)<", re.I)
DUR_RE2 = re.compile(r"class=['\"][^'\"]*duration[^'\"]*['\"][^>]*>([^<]+)<", re.I)
VNAME_RE = re.compile(r"<div[^>]+class=['\"]vname['\"][^>]*>([^<]+)</div>", re.I)
SPAN_TITLE_RE = re.compile(r"<span[^>]+class=['\"][^'\"]*(?:title|video-title)[^'\"]*['\"][^>]*>([\s\S]*?)</span>", re.I)
TITLE_ATTR_RE = re.compile(r"title=['\"]([^'\"]+)['\"]", re.I)
LINK_TITLE_RE = re.compile(r"<a[^>]+href=['\"][^'\"]*viewkey=[^'\"]*['\"][^>]*title=['\"]([^'\"]+)['\"]", re.I)
VT_DIV_RE = re.compile(r"class=['\"][^'\"]*video-title[^'\"]*['\"][^>]*>([\s\S]*?)</div>", re.I)
A_TITLE_RE = re.compile(r"<a[^>]*title=['\"]([^'\"]+)['\"]", re.I)
A_TEXT_RE = re.compile(r"<a[^>]*>([^<]+)</a>", re.I)
ALT_RE = re.compile(r"alt=['\"]([^'\"]{4,})['\"]", re.I)
TAG_RE = re.compile(r"<[^>]+>")
HEX_TITLE_RE = re.compile(r"^[0-9a-fA-F]{8,40}$")
DETAIL_DUR_RE = re.compile(r"时长:\s*<span[^>]*>([^<]+)</span>", re.I)
STRENCODE_RE = re.compile(r"strencode2\(\"([^\"]+)\"\)")
MP4_RE = re.compile(r"https?://[^\"']+\.mp4[^\"']*")
MEDIA_TAG_RE = re.compile(r"<(?:video|iframe)[^>]+src=['\"]([^'\"]+)['\"]", re.I)
SRC_QUOTE_RE = re.compile(r"src='([^']+)'")

TITLE_PATTERNS = [
    re.compile(r"<div[^>]+id=['\"]videodetails['\"][^>]*>[\s\S]*?<h4[^>]*>([\s\S]*?)</h4>", re.I),
    re.compile(r"<title>([\s\S]*?)</title>", re.I),
    re.compile(r"<div[^>]+id=['\"]viewvideo-title['\"][^>]*>\s*([^<]{2,300})", re.I),
    re.compile(r"id=['\"]viewvideo-title['\"][^>]*>([\s\S]*?)</div>", re.I),
    re.compile(r"property=['\"]og:title['\"][^>]*content=['\"]([^'\"]+)['\"]", re.I),
    re.compile(r"content=['\"]([^'\"]+)['\"][^>]*property=['\"]og:title['\"]", re.I),
    re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I),
    re.compile(r"class=['\"][^'\"]*login_registerHeader[^'\"]*['\"][^>]*>([\s\S]*?)</h4>", re.I),
    re.compile(r"id=['\"]player_one['\"][^>]*>[\s\S]*?<h4[^>]*>([\s\S]*?)</h4>", re.I),
    re.compile(r"<h4[^>]*>([\s\S]*?)</h4>", re.I),
    re.compile(r"class=['\"][^'\"]*video-title[^'\"]*['\"][^>]*>([\s\S]*?)</div>", re.I),
    re.compile(r"video_?title\s*[=:]\s*['\"]([^'\"]{2,200})['\"]", re.I),
    re.compile(r"<meta[^>]+name=['\"]description['\"][^>]+content=['\"]([^'\"]{2,200})['\"]", re.I),
]

PIC_PATTERNS = [
    re.compile(r"id=['\"]vid['\"][^>]+poster=['\"]([^'\"]+)['\"]", re.I),
    re.compile(r"<video[^>]+poster=['\"]([^'\"]+)['\"]", re.I),
    re.compile(r"property=['\"]og:image['\"][^>]*content=['\"]([^'\"]+)['\"]", re.I),
    re.compile(r"content=['\"]([^'\"]+)['\"][^>]*property=['\"]og:image['\"]", re.I),
    re.compile(r"poster=['\"]([^'\"]+)['\"]", re.I),
    re.compile(r"src=['\"](https?://[^'\"]+thumb[^'\"]+)['\"]", re.I),
]


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND, clean_meta)
    return BRAND


def _entity_char(m, base):
    try:
        return chr(int(m.group(1), base))
    except Exception:
        return m.group(0)


def clean_text(s):
    if not s:
        return ""
    t = str(s)
    for _ in range(3):
        prev = t
        t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        t = t.replace("&quot;", '"').replace("&apos;", "'")
        t = re.sub(r"&nbsp;", " ", t, flags=re.I)
        t = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: _entity_char(m, 16), t)
        t = re.sub(r"&#(\d+);", lambda m: _entity_char(m, 10), t)
        if t == prev:
            break
    try:
        if re.search(r"%[0-9A-Fa-f]{2}", t):
            u = unquote(t)
            if u != t and re.search(r"[一-龥]", u) and not re.search(r"[一-龥]", t):
                t = u
    except Exception:
        pass
    t = re.sub(r"[\r\n\t]", " ", t)
    t = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", t)
    t = re.sub(r"\s{2,}", " ", t)
    t = re.sub(r"^(91\s*porn(\.com)?)\s*[-|_]\s*", "", t, flags=re.I)
    t = re.sub(r"\s*[-|_]\s*(91\s*porn(\.com)?|91p\d+)\s*$", "", t, flags=re.I)
    t = re.sub(r"\s+\d{1,3}:\d{2}(:\d{2})?\s*$", "", t)
    return t.strip()


def valid_title(t, vid):
    if not t:
        return False
    s = str(t).strip()
    if len(s) < 2:
        return False
    if vid and s.lower() == str(vid).lower():
        return False
    if HEX_TITLE_RE.match(s) and re.search(r"[a-fA-F]", s):
        return False
    if not any(ch.isalpha() for ch in s):
        return False
    if s.lower() in TITLE_BLACKLIST:
        return False
    return True


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST
        self._titles = {}

    def init(self, extend=""):
        host = ""
        if isinstance(extend, dict):
            host = str(extend.get("host") or "").strip()
        elif isinstance(extend, str) and extend.strip():
            text = extend.strip()
            if text.startswith("{"):
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        host = str(data.get("host") or "").strip()
                except Exception:
                    host = ""
            else:
                host = text
        if host.startswith("http"):
            self.host = host.rstrip("/")

    def _fetch(self, path_or_url, is_detail):
        if path_or_url.startswith("http"):
            url = path_or_url
        elif path_or_url.startswith("//"):
            url = "https:" + path_or_url
        else:
            url = self.host + path_or_url
        headers = {
            "User-Agent": UA,
            "Referer": self.host + "/index.php",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Cookie": COOKIE,
        }
        if not is_detail:
            headers["X-Requested-With"] = "XMLHttpRequest"
        try:
            r = requests.get(url, headers=headers, timeout=8)
            if r.status_code < 400 and r.text:
                return r.text
        except Exception:
            pass
        try:
            r2 = requests.get(
                url,
                headers={"User-Agent": UA, "Referer": self.host + "/", "Cookie": COOKIE},
                timeout=8,
            )
            if r2.text:
                return r2.text
        except Exception:
            pass
        return ""

    def _format_poster(self, raw_url):
        if not raw_url:
            return ""
        raw = str(raw_url).strip().replace("&amp;", "&")
        full = raw
        if full.startswith("//"):
            full = "https:" + full
        elif full.startswith("/"):
            full = self.host + full
        elif not full.startswith("http"):
            full = "https://" + full
        return full + "@Referer=" + quote(self.host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def _remember_title(self, vid, title):
        if vid and title:
            self._titles[vid] = title

    def _known_title(self, vid):
        t = self._titles.get(vid) or ""
        if t and valid_title(t, vid):
            return t
        return ""

    def _card_title(self, chunk, vid):
        cands = []
        m = VNAME_RE.search(chunk)
        if m:
            cands.append(m.group(1))
        m = SPAN_TITLE_RE.search(chunk)
        if m:
            inner_txt = TAG_RE.sub("", m.group(1)).strip()
            if inner_txt:
                cands.append(inner_txt)
            tm = TITLE_ATTR_RE.search(m.group(1))
            if tm:
                cands.append(tm.group(1))
        m = LINK_TITLE_RE.search(chunk)
        if m:
            cands.append(m.group(1))
        m = VT_DIV_RE.search(chunk)
        if m:
            ta = A_TITLE_RE.search(m.group(1))
            tt = A_TEXT_RE.search(m.group(1))
            if ta:
                cands.append(ta.group(1))
            if tt:
                cands.append(tt.group(1))
        tl_re = re.compile(
            r"<a[^>]+href=['\"][^'\"]*viewkey=" + re.escape(vid) + r"[^'\"]*['\"][^>]*>([^<]{4,100})</a>",
            re.I,
        )
        m = tl_re.search(chunk)
        if m:
            cands.append(m.group(1))
        m = ALT_RE.search(chunk)
        if m:
            cands.append(m.group(1))
        for cand in cands:
            cleaned = clean_text(cand)
            if valid_title(cleaned, vid):
                return cleaned
        return ""

    def _parse_list(self, html_text):
        items = []
        if not html_text:
            return items
        seen = set()
        for m in CARD_RE.finditer(html_text):
            chunk = m.group(1)
            vk = VIEWKEY_RE.search(chunk)
            if not vk:
                continue
            vid = vk.group(1)
            if vid in seen:
                continue
            seen.add(vid)
            tm = THUMB_RE1.search(chunk) or THUMB_RE2.search(chunk)
            raw_thumb = tm.group(1) if tm else ""
            dm = DUR_RE1.search(chunk) or DUR_RE2.search(chunk)
            duration = clean_text(dm.group(1)) if dm else ""
            status = format_remarks(duration) if duration else format_remarks("正片")
            title = self._card_title(chunk, vid)
            if not title:
                title = self._known_title(vid)
            if not title:
                title = "视频 " + vid[-6:]
            self._remember_title(vid, title)
            items.append({
                "vod_id": vid + "@@" + quote(title, safe=""),
                "vod_name": title,
                "vod_pic": self._format_poster(raw_thumb),
                "vod_remarks": status,
                "style": {"type": "rect", "ratio": PIC_RATIO},
            })
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

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname, _q in CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        html_text = self._fetch("/v.php?next=watch&page=1", False)
        items = self._parse_list(html_text)
        if len(items) > 24:
            items = items[:24]
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        if tid not in CLASS_MAP:
            return self._page_form([], page)
        html_text = self._fetch("/v.php?" + CLASS_MAP[tid] + "&page=" + str(page), False)
        items = self._parse_list(html_text)
        return self._page_form(items, page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        kw = str(key or "").strip()
        if not kw:
            return self._page_form([], page)
        html_text = self._fetch(
            "/search_result.php?search_id=" + quote(kw, safe="") + "&page=" + str(page), False
        )
        items = self._parse_list(html_text)
        return self._page_form(items, page)


    def _extract_mp4(self, html_text):
        if not html_text:
            return ""
        m = STRENCODE_RE.search(html_text)
        if m:
            try:
                dec = unquote(m.group(1))
                sm = SRC_QUOTE_RE.search(dec)
                if sm:
                    return sm.group(1)
            except Exception:
                pass
        m2 = MP4_RE.search(html_text)
        if m2:
            return m2.group(0)
        m3 = MEDIA_TAG_RE.search(html_text)
        if m3:
            return m3.group(1)
        return ""

    def _pick_title(self, html_text, vid):
        for pat in TITLE_PATTERNS:
            m = pat.search(html_text)
            if not m:
                continue
            t = clean_text(TAG_RE.sub(" ", m.group(1)))
            if valid_title(t, vid):
                return t
        return ""

    def _detail_pic(self, html_text):
        for pat in PIC_PATTERNS:
            m = pat.search(html_text)
            if m:
                return m.group(1).strip()
        return ""

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return lines

    def _summary(self, title, vid, related_titles):
        lines = self._brand_block()
        lines.append("标题：" + title)
        lines.append("分类：")
        lines.append("片源：" + LINE_NAME)
        lines.append("编号：" + vid)
        if related_titles:
            lines.append("相关推荐：" + "、".join(related_titles[:6]))
        return "\n".join(lines)

    def detailContent(self, ids):
        raw_id = str(ids[0]) if ids else ""
        parts = raw_id.split("@@")
        vid = parts[0].strip()
        carried_title = ""
        if len(parts) > 1:
            carried_title = unquote(parts[1])
        if not vid:
            return {"list": []}
        html_text = self._fetch("/view_video.php?viewkey=" + vid, True)
        if not html_text:
            return {"list": []}
        url = self._extract_mp4(html_text)
        if not url:
            return {"list": []}
        title = self._pick_title(html_text, vid)
        if not title:
            if carried_title and valid_title(carried_title, vid):
                title = carried_title
            else:
                title = self._known_title(vid)
        if not title:
            title = "超清正片"
        self._remember_title(vid, title)
        dm = DETAIL_DUR_RE.search(html_text)
        duration = clean_text(dm.group(1)) if dm else ""
        status = format_remarks(duration) if duration else format_remarks("超清正片")
        poster = self._format_poster(self._detail_pic(html_text))
        related = []
        for item in self._parse_list(html_text):
            rid = item["vod_id"].split("@@")[0]
            if rid == vid:
                continue
            related.append(item)
            if len(related) >= 6:
                break
        episodes = ["正片$" + json.dumps({"directUrl": url, "vid": vid}, ensure_ascii=False)]
        related_titles = []
        for item in related:
            rid = item["vod_id"].split("@@")[0]
            rname = str(item["vod_name"]).replace("$", "_").replace("#", "_")
            related_titles.append(item["vod_name"])
            episodes.append(rname + "$" + json.dumps({"vid": rid}, ensure_ascii=False))
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": status,
            "vod_content": self._summary(title, vid, related_titles),
            "vod_play_from": LINE_NAME,
            "vod_play_url": "#".join(episodes),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        target = ""
        vid = ""
        text = str(id or "")
        try:
            data = json.loads(text)
            if isinstance(data, dict):
                target = str(data.get("directUrl") or "")
                vid = str(data.get("vid") or "")
        except Exception:
            target = ""
        if not target and vid:
            html_text = self._fetch("/view_video.php?viewkey=" + vid, True)
            target = self._extract_mp4(html_text)
        headers = {"User-Agent": UA, "Referer": self.host + "/"}
        if target:
            return {"parse": 0, "url": target, "header": headers}
        web_url = self.host + "/view_video.php?viewkey=" + quote(vid, safe="")
        return {"parse": 1, "url": web_url, "header": headers}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return None

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249378996&sig=b47c91fcc030c026
