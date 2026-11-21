# -*- coding: utf-8 -*-
# Xanimu卡通 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.xanimu)
import base64
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://xanimu.one"
NAV_URLS = ["https://x99dh.cc", "https://x99dh.one", "https://x99dh.net", "https://x99dh.lat"]
SITE_NAME = "Xanimu"
BRAND_NAME = "Xanimu卡通"
SITE_DESC_KEY = "免费2D、3D、动漫性爱、漫画、卡通"
MIRROR_POOL = ["https://xanimu.ws", "https://www.xanimu.ws", "https://xanimu.com"]
ENTRY_PATH = "/zh-CN/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
LINE_NAME = "🦋 蝴蝶影视专线"
PLACEHOLDER_PIC = "https://img.icons8.com/color/480/anime.png"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
PAGE_SIZE = 47

STATIC_CATS = [
    ("/zh-CN/36900-2d/", "2D"),
    ("/zh-CN/5-3d-%E6%97%A0%E5%B0%BD/", "3D"),
    ("/zh-CN/17-ahegao-%E6%97%A0%E5%B0%BD/", "Ahegao"),
    ("/zh-CN/%E7%94%9F%E6%88%90%E4%BA%86-61627-%E4%B8%AA%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD/", "AI色情"),
    ("/zh-CN/47418%E5%A4%96%E6%98%9F%E4%BA%BA/", "外侨"),
]

FALLBACK_CATS = [
    ("/zh-CN/36900-2d/", "2D"),
    ("/zh-CN/5-3d-%E6%97%A0%E5%B0%BD/", "3D"),
    ("/zh-CN/17-ahegao-%E6%97%A0%E5%B0%BD/", "Ahegao"),
    ("/zh-CN/%E7%94%9F%E6%88%90%E4%BA%86-61627-%E4%B8%AA%E4%BA%BA%E5%B7%A5%E6%99%BA%E8%83%BD/", "AI色情"),
    ("/zh-CN/47418%E5%A4%96%E6%98%9F%E4%BA%BA/", "外侨"),
]

FALLBACK_ACTORS = [
    ("/zh-CN/?actors=13612-tifa-lockhart", "Tifa Lockhart"),
    ("/zh-CN/?actors=168-d-va", "D.Va"),
    ("/zh-CN/?actors=78442-honoka", "Honoka"),
    ("/zh-CN/?actors=78377-marie-rose", "Marie Rose"),
    ("/zh-CN/?actors=247-widowmaker", "Widowmaker"),
    ("/zh-CN/?actors=81405-loveskysanx", "LoveSkySan69"),
    ("/zh-CN/?actors=229-mercy", "Mercy"),
    ("/zh-CN/?actors=641-hinata-hyuga", "Hinata Hyuga"),
]

FALLBACK_TAGS = [
    ("/zh-CN/%E8%A1%8C%E6%9D%8E%E7%89%8C/1025%E5%A3%B0%E9%9F%B3/", "声音"),
    ("/zh-CN/%E8%A1%8C%E6%9D%8E%E7%89%8C/39%E6%B1%87%E7%BC%96/", "汇编"),
    ("/zh-CN/%E8%A1%8C%E6%9D%8E%E7%89%8C/731%E6%89%93%E6%89%8B%E6%9E%AA/", "手淫"),
    ("/zh-CN/%E8%A1%8C%E6%9D%8E%E7%89%8C/47877%E4%B9%B1%E4%BC%A6/", "乱伦"),
    ("/zh-CN/%E8%A1%8C%E6%9D%8E%E7%89%8C/10883-%E8%87%AD%E5%B1%81%E5%B1%81/", "斯库德巴特"),
    ("/zh-CN/%E8%A1%8C%E6%9D%8E%E7%89%8C/71210-%E6%9C%AC-10-%E6%A0%BC%E6%B8%A9/", "本 10 格温"),
]

TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
BLOCK_RE = re.compile(r'<div[^>]*class=["\']([^"\']*video-block[^"\']*)["\'][^>]*>([\s\S]*?)</div>\s*</div>')
HREF_RE = re.compile(r'href=["\']([^"\']+)["\']')
IMG_RE = re.compile(r'(?:data-src|src)=["\']([^"\']+)["\']')
TITLE_ATTR_RE = re.compile(r'title=["\']([^"\']+)["\']')
TITLE_SPAN_RE = re.compile(r'<span[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>([\s\S]*?)</span>')
DUR_RE = re.compile(r'class=["\'][^"\']*(?:duration|time)[^"\']*["\'][^>]*>([^<]*)<')
SLUG_RE = re.compile(r"/zh-CN/\d+-([^/]+)/?")
ANCHOR_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>')
TITLE_TAG_RE = re.compile(r"<title>([\s\S]*?)</title>", re.I)
OG_IMAGE_RE = re.compile(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']+)["\']', re.I)
VIDEO_POSTER_RE = re.compile(r'<video[^>]+poster=["\']([^"\']+)["\']', re.I)
VIDEO_SRC_RE = re.compile(r'<video[^>]+src=["\']([^"\']+)["\']', re.I)
MP4_POOL_RE = re.compile(r'["\'](https?:[^"\']+\.mp4[^"\']*)["\']', re.I)
DURATION_JSON_RE = re.compile(r'"duration":\s*"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?"')
NAV_B64_RE = re.compile(r'["\']([A-Za-z0-9+/=]{100,})["\']')
NAV_HREF_RE = re.compile(r'href=["\'](https?://[^"\'/?#]+)[^"\']*["\']', re.I)
HOST_ORIGIN_RE = re.compile(r"^(https?://[^/?#]+)", re.I)
ABS_PATH_RE = re.compile(r"^https?://[^/]+(/[^\"']*)$")


# ---------- text helpers ----------

def strip_tags(s):
    return TAG_RE.sub("", str(s or ""))


def decode_entities(s):
    t = str(s or "")
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    t = t.replace("&quot;", '"').replace("&#39;", "'").replace("&#039;", "'")
    t = t.replace("&nbsp;", " ")
    return t


def clean_text(s):
    return WS_RE.sub(" ", decode_entities(strip_tags(str(s or "")))).strip()


def normalize_host(raw):
    h = str(raw or "").strip()
    if not h:
        return ""
    if not re.match(r"^https?://", h, re.I):
        h = "https://" + h
    m = HOST_ORIGIN_RE.match(h)
    if m:
        return m.group(1).rstrip("/")
    return ""


def decode_base64_utf8(b64_str):
    if not b64_str:
        return ""
    clean = WS_RE.sub("", str(b64_str))
    try:
        raw = base64.b64decode(clean)
        return raw.decode("utf-8")
    except Exception:
        pass
    try:
        raw = base64.b64decode(clean + "=" * (-len(clean) % 4))
        return raw.decode("utf-8", "replace")
    except Exception:
        return ""


def abs_url(raw, host):
    u = str(raw or "").strip()
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return host + u
    return u


def path_of(raw, host):
    u = str(raw or "").strip()
    if not u:
        return ""
    if host and u.startswith(host):
        u = u[len(host):]
    m = ABS_PATH_RE.match(u)
    if m:
        u = m.group(1)
    return u


# ---------- spider ----------

class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST
        self._custom_host = False

    def getName(self):
        return BRAND_NAME

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
        normalized = normalize_host(host)
        if normalized:
            self.host = normalized
            self._custom_host = True

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    # ---------- fetch ----------

    def _page_headers(self, host):
        return {
            "User-Agent": UA,
            "Referer": host + ENTRY_PATH,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _get(self, url, host):
        try:
            resp = requests.get(url, headers=self._page_headers(host), timeout=8)
            text = resp.text if resp is not None else ""
            status = resp.status_code if resp is not None else 0
            final_url = resp.url if resp is not None else ""
            return text, status, final_url
        except Exception:
            return "", 0, ""

    def _resp_ok(self, text, status):
        if not text:
            return False
        return status == 0 or status < 400

    def _check_host_alive(self, base_url):
        clean_base = normalize_host(base_url)
        if not clean_base:
            return ""
        target = clean_base + ENTRY_PATH
        text, status, final_url = self._get(target, clean_base)
        if (status == 0 or 200 <= status < 400) and "video-block" in text:
            return normalize_host(final_url) or clean_base
        if target.startswith("https://"):
            http_target = "http://" + target[8:]
            text2, status2, final_url2 = self._get(http_target, clean_base)
            if (status2 == 0 or 200 <= status2 < 400) and "video-block" in text2:
                return normalize_host(final_url2) or clean_base
        return ""

    def _collect_candidate_base_urls(self, item):
        urls = []
        if not isinstance(item, dict):
            return urls
        raw_list = []
        for key in ("url", "link", "href", "directUrl", "bestUrl"):
            if item.get(key):
                raw_list.append(str(item.get(key)))
        if isinstance(item.get("urls"), list):
            for u_obj in item.get("urls"):
                if isinstance(u_obj, str):
                    raw_list.append(u_obj)
                elif isinstance(u_obj, dict):
                    if u_obj.get("url"):
                        raw_list.append(str(u_obj.get("url")))
                    if u_obj.get("href"):
                        raw_list.append(str(u_obj.get("href")))
        for raw in raw_list:
            base = normalize_host(raw)
            if base and base not in urls:
                urls.append(base)
        return urls

    def _fetch_nav_host(self):
        for nav in NAV_URLS:
            try:
                resp = requests.get(nav, headers={"User-Agent": UA, "Accept": "text/html,*/*"}, timeout=8)
                text = resp.text if resp is not None else ""
            except Exception:
                text = ""
            if not text:
                continue
            for m in NAV_B64_RE.finditer(text):
                dec = decode_base64_utf8(m.group(1))
                if not dec:
                    continue
                unq = dec
                if "%5B" in dec or "%7B" in dec:
                    try:
                        unq = unquote(dec)
                    except Exception:
                        pass
                if "[" not in unq or "{" not in unq:
                    continue
                if SITE_NAME.lower() not in unq.lower() and "动漫性爱" not in unq:
                    continue
                try:
                    lst = json.loads(unq)
                except Exception:
                    continue
                if not isinstance(lst, list):
                    continue
                for item in lst:
                    if not isinstance(item, dict):
                        continue
                    nm = str(item.get("name") or item.get("title") or "").strip().lower()
                    desc = str(item.get("desc") or item.get("description") or "").strip()
                    if SITE_NAME.lower() in nm or SITE_DESC_KEY in desc:
                        for cand in self._collect_candidate_base_urls(item):
                            alive = self._check_host_alive(cand)
                            if alive:
                                return alive
            card_idx = text.lower().find(SITE_NAME.lower())
            if card_idx != -1:
                snippet = text[max(0, card_idx - 100):card_idx + 500]
                for hm in NAV_HREF_RE.finditer(snippet):
                    cand = normalize_host(hm.group(1))
                    if cand and "x99dh" not in cand:
                        alive = self._check_host_alive(cand)
                        if alive:
                            return alive
        for mirror in MIRROR_POOL:
            alive = self._check_host_alive(mirror)
            if alive:
                return alive
        alive = self._check_host_alive(DEFAULT_HOST)
        if alive:
            return alive
        return ""

    def _fetch_text(self, url, host):
        best = None
        text, status, final_url = self._get(url, host)
        if self._resp_ok(text, status):
            eff = normalize_host(final_url) or host
            return text, eff
        if text and best is None:
            best = (text, host)
        if not self._custom_host:
            nav_host = self._fetch_nav_host()
            if nav_host and nav_host != host:
                url2 = url.replace(host, nav_host, 1)
                text2, status2, final_url2 = self._get(url2, nav_host)
                if self._resp_ok(text2, status2):
                    eff2 = normalize_host(final_url2) or nav_host
                    self.host = nav_host
                    return text2, eff2
                if text2 and best is None:
                    best = (text2, nav_host)
        if url.startswith("https://"):
            url3 = "http://" + url[8:]
            host3 = host.replace("https://", "http://", 1)
            text3, status3, final_url3 = self._get(url3, host3)
            if self._resp_ok(text3, status3):
                return text3, host3
            if text3 and best is None:
                best = (text3, host3)
        if best is not None:
            return best
        return "", host


    # ---------- posters and cards ----------

    def _image_address(self, raw_url, host):
        url = str(raw_url or "").strip()
        if not url:
            return ""
        if "icons8.com" in url:
            return url
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = host + url
        return url + "@Referer=" + quote(host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def _parse_cards(self, html, host):
        items = []
        seen = {}
        for bm in BLOCK_RE.finditer(html or ""):
            cls = bm.group(1)
            if "video-block" not in cls or "video-block-cat" in cls:
                continue
            b = bm.group(2)
            href_m = HREF_RE.search(b)
            img_m = IMG_RE.search(b)
            title_m = TITLE_ATTR_RE.search(b) or TITLE_SPAN_RE.search(b)
            dur_m = DUR_RE.search(b)
            if not href_m or (not img_m and not title_m):
                continue
            path = path_of(href_m.group(1), host)
            if not path.startswith("/zh-CN/"):
                continue
            if "/%E7%B1%BB%E5%88%AB/" in path or "/4875-" in path or "/%E8%A1%8C%E6%9D%8E%E7%89%8C/" in path:
                continue
            if path in ("/zh-CN/", "/zh-CN"):
                continue
            if path in seen:
                continue
            pic = img_m.group(1).strip() if img_m else ""
            if re.search(r"flags", pic, re.I) or re.search(r"logo", pic, re.I):
                pic = PLACEHOLDER_PIC
            title = clean_text(title_m.group(1)) if title_m else ""
            if not title:
                slug_m = SLUG_RE.search(path)
                if slug_m:
                    try:
                        title = unquote(slug_m.group(1)).replace("-", " ")
                    except Exception:
                        title = slug_m.group(1).replace("-", " ")
            if not title or len(title) < 2:
                continue
            seen[path] = True
            dur = clean_text(dur_m.group(1)) if dur_m else ""
            remarks = "🦋 蝴蝶影视 | " + dur if dur else "🦋 蝴蝶影视"
            vod = {
                "vod_id": path,
                "vod_name": title,
                "vod_pic": self._image_address(pic, host),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.78},
            }
            items.append(vod)
        return items

    # ---------- home / category / search ----------

    def _filter_row(self, name, options):
        values = [{"n": "全部", "v": ""}]
        for value, opt_name in options:
            values.append({"n": opt_name, "v": value})
        return [{"key": "slug", "name": name, "init": "", "value": values}]

    def homeContent(self, filter):
        classes = []
        for value, name in STATIC_CATS:
            classes.append({"type_id": value, "type_name": name})
        classes.append({"type_id": "filter@@cat", "type_name": "📁 分类"})
        classes.append({"type_id": "filter@@actor", "type_name": "👤 人物"})
        classes.append({"type_id": "filter@@tag", "type_name": "🏷️ 标签"})
        result = {"class": classes}
        if filter:
            result["filters"] = {
                "filter@@cat": self._filter_row("选择分类", FALLBACK_CATS),
                "filter@@actor": self._filter_row("选择人物", FALLBACK_ACTORS),
                "filter@@tag": self._filter_row("选择标签", FALLBACK_TAGS),
            }
        return result

    def homeVideoContent(self):
        text, eff_host = self._fetch_text(self.host + ENTRY_PATH, self.host)
        if not text:
            return {"list": []}
        return {"list": self._parse_cards(text, eff_host)[:20]}

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

    def _listing_url(self, host, value, page):
        base = value or ENTRY_PATH
        if "?" in base:
            return host + base + (("&page=" + str(page)) if page > 1 else "")
        p = base
        if not p.endswith("/"):
            p += "/"
        return host + p + (("page/" + str(page) + "/") if page > 1 else "")

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        category_id = str(tid or "")
        value = ""
        if category_id.startswith("filter@@"):
            slug = ""
            if isinstance(extend, dict):
                slug = str(extend.get("slug") or "")
            value = slug if slug else ENTRY_PATH
        else:
            value = category_id if category_id else ENTRY_PATH
        url = self._listing_url(self.host, value, page)
        text, eff_host = self._fetch_text(url, self.host)
        if not text:
            return self._page_form([], page)
        items = self._parse_cards(text, eff_host)
        if not items and page == 1:
            text2, eff_host2 = self._fetch_text(url, self.host)
            if text2:
                retry_items = self._parse_cards(text2, eff_host2)
                if retry_items:
                    items = retry_items
        return self._page_form(items, page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_form([], page)
        enc = quote(keyword, safe="")
        if page > 1:
            url = self.host + "/zh-CN/page/" + str(page) + "/?s=" + enc
        else:
            url = self.host + "/zh-CN/?s=" + enc
        text, eff_host = self._fetch_text(url, self.host)
        if not text:
            return self._page_form([], page)
        items = self._parse_cards(text, eff_host)
        if not items and page == 1:
            text2, eff_host2 = self._fetch_text(url, self.host)
            if text2:
                retry_items = self._parse_cards(text2, eff_host2)
                if retry_items:
                    items = retry_items
        return self._page_form(items, page)


    # ---------- detail ----------

    def _parse_duration_text(self, html):
        m = DURATION_JSON_RE.search(html or "")
        if not m:
            return ""
        days = int(m.group(1) or "0")
        hours = int(m.group(2) or "0")
        minutes = int(m.group(3) or "0")
        seconds = int(round(float(m.group(4) or "0")))
        total = days * 86400 + hours * 3600 + minutes * 60 + seconds
        if not total:
            return ""
        h = total // 3600
        mm = (total % 3600) // 60
        ss = total % 60
        if h > 0:
            return str(h) + ":" + ("0" + str(mm) if mm < 10 else str(mm)) + ":" + ("0" + str(ss) if ss < 10 else str(ss))
        return str(mm) + ":" + ("0" + str(ss) if ss < 10 else str(ss))

    def _parse_detail_tags(self, html):
        tags = []
        seen = {}
        for m in ANCHOR_RE.finditer(html or ""):
            if "/%E8%A1%8C%E6%9D%8E%E7%89%8C/" not in m.group(1):
                continue
            text = clean_text(m.group(2))
            if not text or len(text) > 30 or text in seen:
                continue
            if "显示更多" in text:
                continue
            seen[text] = True
            tags.append(text)
            if len(tags) >= 8:
                break
        return tags

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _summary(self, title, aid, related_titles):
        block = self._brand_block()
        fallback = [
            "标题：" + title,
            "分类：",
            "片源：" + LINE_NAME,
            "编号：" + aid,
        ]
        if related_titles:
            fallback.append("相关推荐：" + "、".join(related_titles[:6]))
        return block + "\n" + "\n".join(fallback)

    def detailContent(self, ids):
        item_id = str(ids[0]) if ids else ""
        if not item_id:
            return {"list": [], "msg": "缺少条目标识"}
        text, eff_host = self._fetch_text(self.host + item_id, self.host)
        if not text:
            return {"list": [], "msg": "详情请求失败，请稍后重试"}
        html = text
        title_m = TITLE_TAG_RE.search(html)
        if title_m:
            title = clean_text(title_m.group(1).split("-")[0])
        else:
            title = "动漫正片"
        pic_m = OG_IMAGE_RE.search(html)
        if not pic_m:
            pic_m = VIDEO_POSTER_RE.search(html)
        poster = self._image_address(pic_m.group(1), eff_host) if pic_m else ""
        tags = self._parse_detail_tags(html)
        duration = self._parse_duration_text(html)

        episode_strs = []
        first_name = "正片".replace("$", "_").replace("#", "_")
        episode_strs.append(first_name + "$" + item_id)
        related_titles = []
        related = self._parse_cards(html, eff_host)
        for card in related:
            if len(episode_strs) >= 20:
                break
            if card["vod_id"] == item_id:
                continue
            ep_name = card["vod_name"].replace("$", "_").replace("#", "_")
            episode_strs.append(ep_name + "$" + card["vod_id"])
            related_titles.append(card["vod_name"])

        remarks = "🦋 蝴蝶影视 | " + duration if duration else "🦋 蝴蝶影视"
        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": remarks,
            "vod_content": self._summary(title, item_id, related_titles),
            "vod_play_from": LINE_NAME,
            "vod_play_url": "#".join(episode_strs),
        }
        if tags:
            vod["vod_type"] = ",".join(tags)
        return {"list": [vod]}

    # ---------- player ----------

    def _extract_stream_url(self, html):
        v_m = VIDEO_SRC_RE.search(html or "")
        if v_m:
            return v_m.group(1)
        pool = []
        for m in MP4_POOL_RE.finditer(html or ""):
            u = m.group(1).replace("\\/", "/")
            if "trailer" in u or "preview" in u:
                continue
            pool.append(u)
        for u in pool:
            if "high" in u:
                return u
        return pool[0] if pool else ""

    def playerContent(self, flag, id, vipFlags):
        vod_id = str(id or "")
        if not vod_id:
            return {"parse": 1, "url": self.host + "/", "header": {"User-Agent": UA, "Referer": self.host + "/"}}
        text, eff_host = self._fetch_text(self.host + vod_id, self.host)
        headers = {"User-Agent": UA, "Referer": eff_host + "/"}
        if not text:
            return {"parse": 1, "url": eff_host + vod_id, "header": headers}
        url = self._extract_stream_url(text)
        if not url:
            return {"parse": 1, "url": eff_host + vod_id, "header": headers}
        return {"parse": 0, "url": abs_url(url, eff_host), "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250220827&sig=68be65859b2a2105
