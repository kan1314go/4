# -*- coding: utf-8 -*-
# MissAVCN - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.missavcn)
import base64
import json
import re
from urllib.parse import quote, unquote, urljoin

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://www.thisav.my"
NAV_URLS = ["https://x99dh.net", "https://x99dh.lat", "https://x99dh.cc", "https://x99dh.one"]
SITE_NAME = "MissAV"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND = "蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
PAGE_SIZE = 12
PIC_RATIO = 1.78
FALLBACK_PIC_HOST = "https://spic2-147.71352.men/"

CATEGORIES = [
    ("/dm278/cn/chinese-subtitle", "中文字幕", "common"),
    ("/dm539/cn/new", "最近更新", "common"),
    ("/dm635/cn/release", "新作上市", "common"),
    ("/dm817/cn/uncensored-leak", "无码流出", "common"),
    ("/dm301/cn/today-hot", "今日热门", "common"),
    ("/dm170/cn/weekly-hot", "本週热门", "common"),
    ("/dm273/cn/monthly-hot", "本月热门", "common"),
    ("actresses", "💃 女优专区", "actress"),
    ("/cn/genres/VR", "🕶️ VR专区", "common"),
    ("/dm597/cn/fc2", "FC2", "common"),
    ("/dm2208642/cn/heyzo", "HEYZO", "common"),
    ("/dm42/cn/tokyohot", "东京热", "common"),
    ("/dm5199603/cn/1pondo", "一本道", "common"),
    ("/dm7704788/cn/caribbeancom", "加勒比", "common"),
    ("/dm7208981/cn/10musume", "天然素人", "common"),
    ("/dm3600557/cn/pacopacomama", "熟女俱乐部", "common"),
    ("/dm36/cn/siro", "SIRO", "common"),
    ("/dm34/cn/luxu", "LUXU", "common"),
    ("/dm63/cn/madou", "麻豆传媒", "common"),
]

COMMON_FILTERS = [
    ("sort", "排序", [
        ("", "默认排序"),
        ("released_at", "发行日期"),
        ("published_at", "最近更新"),
        ("saved", "收藏最多"),
        ("today_views", "今日浏览"),
        ("weekly_views", "本周浏览"),
        ("monthly_views", "本月浏览"),
        ("views", "总浏览数"),
    ]),
    ("filters", "过滤", [
        ("", "所有作品"),
        ("individual", "单人作品"),
        ("multiple", "多人作品"),
        ("chinese-subtitle", "中文字幕"),
    ]),
]

ACTRESS_FILTERS = [
    ("sort", "女优排序", [
        ("", "默认排序"),
        ("videos", "影片最多"),
    ]),
    ("cup", "罩杯筛选", [("", "全部罩杯")] + [(c, c + " 罩杯") for c in "ABCDEFGHIJK"]),
    ("age", "年龄", [
        ("", "全部年龄"),
        ("<20", "20 岁以下"),
        ("20-30", "20 - 30 岁"),
        ("30-40", "30 - 40 岁"),
        ("40-50", "40 - 50 岁"),
        (">50", "50 岁以上"),
    ]),
]

BANNED_SLUGS = {
    "chinese-subtitle", "new", "release", "uncensored-leak", "today-hot",
    "weekly-hot", "monthly-hot", "genres", "actresses", "makers", "series", "tags",
    "vip", "saved", "playlists", "history", "login", "register", "siro", "luxu", "gana",
}

B64_RE = re.compile(r"""["']([A-Za-z0-9+/=]{100,})["']""")
HOST_ORIGIN_RE = re.compile(r"^(https?://[^/]+)", re.I)
HREF_RE = re.compile(r'href=["\']([^"\']*\/(?:cn|dm\d+\/cn)\/([A-Za-z0-9_-]+))["\']')
NAME_DIV_RE = re.compile(r'<div[^>]*class=["\'][^"\']*(?:title|my-2|font-semibold)[^"\']*["\'][^>]*>([\s\S]*?)</div>', re.I)
ALT_RE = re.compile(r'alt=["\']([^"\']+)["\']', re.I)
ANCHOR_INNER_RE = re.compile(r'<a[^>]*>([\s\S]*?)</a>')
ANCHOR_FALLBACK_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^"\']+|/[^"\']+)["\'][^>]*>[\s\S]*?</a>')
PIC_RE = re.compile(r'(?:data-src|data-original|src)=["\']([^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', re.I)
DUR_RE = re.compile(r'(\d{1,2}:\d{2}(?::\d{2})?)')
TAG_RE = re.compile(r"<[^>]+>")
TITLE_TAG_RE = re.compile(r"<title>(.*?)</title>", re.I)
OG_IMAGE_RE = re.compile(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', re.I)
GENRE_RE = re.compile(r'/cn/genres/[^"\']+["\'][^>]*>([^<]+)</a>')
ID_FROM_URL_RE = re.compile(r'\/(?:cn|dm\d+\/cn)\/([A-Za-z0-9_-]+)')
PACKER_RE = re.compile(r'eval\(function\(p,a,c,k,e,[rd]\)[\s\S]*?\}\(([\'"][\s\S]*?[\'"])\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([\'"][^\'"]+[\'"])\.split', re.I)
SRC_1280_RE = re.compile(r"source1280\s*=\s*['\"]([^'\"]+)['\"]")
SRC_842_RE = re.compile(r"source842\s*=\s*['\"]([^'\"]+)['\"]")
SRC_AUTO_RE = re.compile(r"source\s*=\s*['\"]([^'\"]+)['\"]")
HLS_UUID_RE = re.compile(r'hls\.loadSource\(["\']https?://[^/]+/([a-f0-9-]{36})/playlist\.m3u8["\']\)', re.I)
PLAIN_UUID_RE = re.compile(r'https?://(?:surrit\.com|sixyik\.com)/([a-f0-9-]{36})/playlist\.m3u8', re.I)
JMPS_RE = re.compile(r"https?://(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,})/")
WORD_RE = re.compile(r"\b\w+\b", re.ASCII)
ORIGIN_PREFIX_RE = re.compile(r"^https?://[^/]+")

PACKER_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND, clean_meta)
    return BRAND


def int2base(x, base):
    if x < 0:
        return "-" + int2base(-x, base)
    res = ""
    while x > 0:
        res = PACKER_CHARS[x % base] + res
        x //= base
    return res or "0"


def unpack_packer(p, a, c, k):
    d = {}
    cc = c
    while cc > 0:
        cc -= 1
        key = int2base(cc, a)
        val = k[cc] if cc < len(k) and k[cc] else key
        d[key] = val
    return WORD_RE.sub(lambda m: d.get(m.group(0), m.group(0)), p)


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST
        self._custom_host = False
        self._discovered = ""
        self._discovery_done = False

    def getName(self):
        return SITE_NAME

    def init(self, extend=""):
        host = ""
        ext = extend
        if isinstance(ext, str) and ext.strip():
            text = ext.strip()
            if text.startswith("http"):
                host = text
            else:
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        host = str(data.get("host") or "")
                except Exception:
                    pass
        elif isinstance(ext, dict):
            host = str(ext.get("host") or "")
        if host.startswith("http"):
            self.host = host.rstrip("/")
            self._custom_host = True

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- host discovery ----------

    def _decode_b64_utf8(self, text):
        try:
            return base64.b64decode(text).decode("utf-8")
        except Exception:
            return ""

    def _discover_host(self):
        if self._custom_host:
            return self.host
        if self._discovered:
            return self._discovered
        if self._discovery_done:
            return DEFAULT_HOST
        headers = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        for nav in NAV_URLS:
            try:
                resp = requests.get(nav, headers=headers, timeout=8)
            except Exception:
                continue
            if resp is None or not (200 <= resp.status_code < 300) or not resp.text:
                continue
            for m in B64_RE.finditer(resp.text):
                dec = self._decode_b64_utf8(m.group(1))
                if not dec:
                    continue
                try:
                    unq = unquote(dec, errors="strict")
                except Exception:
                    continue
                if SITE_NAME not in unq or "[" not in unq or "{" not in unq:
                    continue
                try:
                    site_list = json.loads(unq)
                except Exception:
                    continue
                if not isinstance(site_list, list):
                    continue
                for item in site_list:
                    if not isinstance(item, dict):
                        continue
                    if str(item.get("name") or "").strip() == SITE_NAME and item.get("url"):
                        mm = HOST_ORIGIN_RE.match(str(item["url"]))
                        if mm:
                            self._discovered = mm.group(1)
                            self.host = self._discovered
                            return self._discovered
        self._discovery_done = True
        return DEFAULT_HOST

    def _active_host(self):
        if self._custom_host:
            return self.host
        if self._discovered:
            return self._discovered
        return self._discover_host()

    # ---------- fetch ----------

    def _resolve_url(self, url, base):
        u = str(url or "")
        if u.startswith("http"):
            return u
        if u.startswith("//"):
            return "https:" + u
        return urljoin(base + "/", u)

    def _fetch_page(self, target_url, referer=None):
        base = self._active_host()
        full = self._resolve_url(target_url, base)
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer is not None else (base + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(full, headers=headers, timeout=8)
            if resp is not None and 200 <= resp.status_code < 300:
                return (resp.text or "", base, resp.url or full)
            return ("", base, full)
        except Exception:
            self._discovered = ""
            self._discovery_done = False
            base2 = self._active_host()
            healed = ORIGIN_PREFIX_RE.sub(base2, full)
            headers2 = dict(headers)
            headers2["Referer"] = base2 + "/"
            try:
                resp2 = requests.get(healed, headers=headers2, timeout=8)
                if resp2 is None:
                    return ("", base2, healed)
                return (resp2.text or "", base2, resp2.url or healed)
            except Exception:
                return ("", base2, healed)

    # ---------- cards ----------

    def _format_image(self, raw_pic, base):
        pic = str(raw_pic or "").strip()
        if not pic:
            return ""
        if pic.startswith("//"):
            pic = "https:" + pic
        elif pic.startswith("/"):
            pic = urljoin(base + "/", pic)
        return pic + "@Referer=" + quote(base + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def _parse_cards(self, html_text, base):
        items = []
        body = str(html_text or "")
        if not body:
            return items
        if "</nav>" in body:
            body = body.split("</nav>")[1]
        elif "</header>" in body:
            body = body.split("</header>")[1]
        if 'class="relative group' in body:
            chunks = body.split('class="relative group')[1:]
        elif 'class="thumbnail' in body:
            chunks = body.split('class="thumbnail')[1:]
        else:
            chunks = ANCHOR_FALLBACK_RE.findall(body)
        seen = set()
        for ch in chunks:
            m = HREF_RE.search(ch)
            if not m:
                continue
            full_href = m.group(1)
            dvd_id = m.group(2)
            low = dvd_id.lower()
            if low in BANNED_SLUGS or low in seen or len(dvd_id) < 3:
                continue
            seen.add(low)
            title = ""
            dm = NAME_DIV_RE.search(ch)
            if dm:
                cand = TAG_RE.sub("", dm.group(1)).strip()
                if cand and cand.lower() != low and len(cand) >= len(dvd_id):
                    title = cand
            if not title:
                am = ALT_RE.search(ch)
                if am:
                    cand = am.group(1).strip()
                    if cand and cand.lower() != low and len(cand) >= len(dvd_id):
                        title = cand
            if not title:
                for a_inner in ANCHOR_INNER_RE.findall(ch):
                    t_str = TAG_RE.sub("", a_inner).strip()
                    if t_str and t_str.lower() != low and len(t_str) > len(dvd_id):
                        if not any(k in t_str for k in ("item.", "HD", "FHD", "4K", ":", "条影片")):
                            title = t_str
                            break
            if not title:
                title = dvd_id.upper()
            pm = PIC_RE.search(ch)
            if pm and "item.dvd_id" not in pm.group(1):
                raw_pic = pm.group(1).strip()
            else:
                raw_pic = FALLBACK_PIC_HOST + low + "/cover-n.jpg"
            dur = DUR_RE.search(ch)
            remarks = format_remarks(dur.group(1) if dur else "")
            full_url = full_href if full_href.startswith("http") else self._resolve_url(full_href, base)
            items.append({
                "vod_id": full_url,
                "vod_name": title,
                "vod_pic": self._format_image(raw_pic, base),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": PIC_RATIO},
            })
        return items

    # ---------- home / category / search ----------

    def _filter_rows(self, rows_src):
        rows = []
        for key, name, options in rows_src:
            rows.append({
                "key": key,
                "name": name,
                "init": "",
                "value": [{"n": opt_name, "v": opt_value} for opt_value, opt_name in options],
            })
        return rows

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname, _kind in CATEGORIES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, _cname, kind in CATEGORIES:
                filters[cid] = self._filter_rows(ACTRESS_FILTERS if kind == "actress" else COMMON_FILTERS)
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        base = self._active_host()
        text, res_base, _final = self._fetch_page(base + "/dm539/cn/new", base + "/")
        return {"list": self._parse_cards(text, res_base)}

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

    def _page_num(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def categoryContent(self, tid, pg, filter, extend):
        page = self._page_num(pg)
        ext = extend if isinstance(extend, dict) else {}
        base = self._active_host()
        tid = str(tid or "")
        if tid == "actresses":
            target = base + "/cn/actresses"
        elif tid.startswith("http"):
            target = tid
        else:
            target = base + re.sub(r"/+$", "", tid)
        parts = []
        if page > 1:
            parts.append("page=" + str(page))
        keys = ("cup", "age", "sort") if tid == "actresses" else ("sort", "filters")
        for key in keys:
            value = ext.get(key)
            if value:
                parts.append(key + "=" + quote(str(value), safe=""))
        if parts:
            target += ("&" if "?" in target else "?") + "&".join(parts)
        text, res_base, _final = self._fetch_page(target, base + "/dm247/cn")
        return self._page_form(self._parse_cards(text, res_base), page)

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = self._page_num(pg)
        if not keyword:
            return self._page_form([], page)
        base = self._active_host()
        url = base + "/cn/search/" + quote(keyword, safe="")
        if page > 1:
            url += "?page=" + str(page)
        text, res_base, _final = self._fetch_page(url, base + "/")
        return self._page_form(self._parse_cards(text, res_base), page)

    # ---------- detail ----------

    def _extract_genres(self, html_text):
        body = html_text
        if "</nav>" in body:
            body = body.split("</nav>", 1)[1]
        elif "</header>" in body:
            body = body.split("</header>", 1)[1]
        genres = []
        seen = set()
        for m in GENRE_RE.finditer(body):
            name = TAG_RE.sub("", m.group(1)).strip()
            if name and name not in seen:
                seen.add(name)
                genres.append(name)
        return genres

    def _ep_value(self, media_url, base, target, is_web):
        ref = {"mediaUrl": media_url, "baseHost": base, "targetUrl": target}
        if is_web:
            ref["isWeb"] = True
        return json.dumps(ref, ensure_ascii=False)

    def _build_episodes(self, html_text, res_base, target):
        episodes = []
        pm = PACKER_RE.search(html_text)
        if pm:
            p = pm.group(1)[1:-1]
            a = int(pm.group(2))
            c = int(pm.group(3))
            k = pm.group(4)[1:-1].split("|")
            unpacked = unpack_packer(p, a, c, k)
            unpacked = unpacked.replace("\\'", "'")
            for pat, ep_name in (
                (SRC_1280_RE, "🦋 1080P 超清专线"),
                (SRC_842_RE, "🦋 720P 高清专线"),
                (SRC_AUTO_RE, "🦋 自适应极速专线"),
            ):
                mm = pat.search(unpacked)
                if mm and "sample" not in mm.group(1) and "preview" not in mm.group(1):
                    episodes.append((ep_name, self._ep_value(mm.group(1), res_base, target, False)))
        if not episodes:
            uuid = ""
            hm = HLS_UUID_RE.search(html_text)
            if hm:
                uuid = hm.group(1)
            else:
                um = PLAIN_UUID_RE.search(html_text)
                if um:
                    uuid = um.group(1)
            if uuid:
                episodes.append(("🦋 官方原生线路", self._ep_value("https://surrit.com/" + uuid + "/playlist.m3u8", res_base, target, False)))
            else:
                episodes.append(("🦋 网页嗅探线路", self._ep_value(target, res_base, target, True)))
        return episodes

    def _summary(self, vod_name, genres, dvd_id, base):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + base,
            "━" * 28,
            "━" * 7,
            "标题：" + vod_name,
            "分类：" + "、".join(genres),
            "片源：" + LINE_NAME,
            "编号：" + dvd_id,
        ]
        return "\n".join(lines)

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        item_id = str(ids[0])
        base = self._active_host()
        target = item_id if item_id.startswith("http") else self._resolve_url(item_id, base)
        text, res_base, _final = self._fetch_page(target, base + "/")
        if not text:
            return {"list": []}
        vod_name = "Video"
        tm = TITLE_TAG_RE.search(text)
        if tm:
            vod_name = tm.group(1).split(" - ")[0].split(" | ")[0].strip()
        poster = ""
        om = OG_IMAGE_RE.search(text)
        if om:
            poster = self._format_image(om.group(1).strip(), res_base)
        genres = self._extract_genres(text)
        dvd_id = ""
        idm = ID_FROM_URL_RE.search(target)
        if idm:
            dvd_id = idm.group(1)
        episodes = self._build_episodes(text, res_base, target)
        ep_strs = []
        for ep_name, ep_value in episodes:
            clean_name = ep_name.replace("$", "_").replace("#", "_")
            ep_strs.append(clean_name + "$" + ep_value)
        vod = {
            "vod_id": target,
            "vod_name": vod_name,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": BRAND,
            "vod_content": self._summary(vod_name, genres, dvd_id, res_base),
            "vod_play_from": LINE_NAME,
            "vod_play_url": "#".join(ep_strs),
        }
        return {"list": [vod]}

    # ---------- player ----------

    def playerContent(self, flag, id, vipFlags):
        ref = {}
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                ref = data
        except Exception:
            ref = {}
        media = str(ref.get("mediaUrl") or "")
        target = str(ref.get("targetUrl") or "")
        base = str(ref.get("baseHost") or "") or self._active_host()
        headers = {"User-Agent": UA, "Referer": base + "/"}
        if ref.get("isWeb") or ".m3u8" not in media:
            return {"parse": 1, "url": media or target, "header": headers}
        play = JMPS_RE.sub(base + "/jmpres/", media, count=1)
        if ".m3u8" not in play.lower():
            play += ("&" if "?" in play else "?") + "format=.m3u8"
        return {"parse": 0, "url": play, "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250115843&sig=9bf5a1cd2651f0d5
