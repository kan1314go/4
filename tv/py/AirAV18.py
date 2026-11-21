# -*- coding: utf-8 -*-
# AirAV18 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.airav)
import base64
import json
import re
import time
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://airavingg6.work"
NAV_URLS = ["https://x99dh.net", "https://x99dh.lat"]
SITE_NAME = "AirAV"
TARGET_NAME = "airav"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
MAIN_LINE = "🦋 蝴蝶专属线路"
RELATED_LINE = "相关推荐"
PAGE_SIZE = 60
HOME_CAP = 24
PIC_RATIO = 1.49
COVER_BASE = "https://airav.io/storage/cover/big/"

CLASSES = [
    ("latest", "最新视频"),
    ("today_hot", "今日熱門"),
    ("week_hot", "本周熱門"),
    ("month_hot", "本月熱門"),
    ("vr_zone", "VR专区"),
    ("filter@@factories", "發行商"),
    ("filter@@actors", "女優一覽"),
    ("filter@@tags", "類型一覽"),
]

LATEST_SORT = [
    ("", "最新上架"),
    ("3", "今日最熱"),
    ("4", "本週最熱"),
    ("5", "本月最熱"),
]

FALLBACK_ACTORS = [
    ("", "全部女優"),
    ("1", "三上悠亞"),
    ("2", "河北彩花"),
    ("3", "相澤南"),
    ("4", "波多野結衣"),
    ("5", "深田詠美"),
    ("6", "櫻空桃"),
    ("7", "安齋拉拉"),
    ("8", "明步萌衣"),
]

FALLBACK_FACTORIES = [
    ("", "全部發行商"),
    ("1", "S1 NO.1 STYLE"),
    ("2", "MOODYZ"),
    ("3", "IDEA POCKET"),
    ("4", "SOD CREATE"),
    ("5", "PRESTIGE"),
    ("6", "FALENO"),
    ("7", "WANZ FACTORY"),
    ("8", "MADONNA"),
]

FALLBACK_TAGS = [
    ("", "全部類型"),
    ("1", "巨乳"),
    ("2", "美乳"),
    ("3", "單體作品"),
    ("4", "痴女"),
    ("5", "人妻"),
    ("6", "制服"),
    ("7", "美腿"),
    ("8", "無碼流出"),
]

CARD_RE = re.compile(r"""<a[^>]+href=['"]([^'"]*?/video\?hid=([^"'&]+))['"][^>]*>([\s\S]*?)</a>""", re.I)
IMG_SRC_RE = re.compile(r"""<img[^>]+src=['"]([^'"]+)['"]""", re.I)
DATA_SRC_RE = re.compile(r"""data-src=['"]([^'"]+)['"]""", re.I)
TITLE_ATTR_RE = re.compile(r"""title=['"]([^'"]+)['"]""", re.I)
DURATION_RE = re.compile(r"""class=['"][^'"]*(?:duration|time)[^'"]*['"][^>]*>([^<]+)""", re.I)
TITLE_TAG_RE = re.compile(r"<title>([\s\S]*?)</title>", re.I)
COVER_RE = re.compile(r"""['"](https://airav\.io/storage/cover/big/[^'"]+)['"]""", re.I)
META_DESC_RE = re.compile(r"""<meta[^>]+name=['"]description['"][^>]+content=['"]([^'"]*)['"]""", re.I)
CONTENT_URL_RE = re.compile(r"""['"]contentUrl['"]\s*:\s*['"]([^'"]+\.m3u8[^'"]*)['"]""", re.I)
TAG_A_RE = re.compile(r"""<a[^>]+href=['"]/tag\?tid=\d+['"][^>]*>([^<]+)</a>""", re.I)
B64_RE = re.compile(r"""['"]([A-Za-z0-9+/=]{100,})['"]""")
ORIGIN_RE = re.compile(r"^(https?://[^/]+)", re.I)


def format_remarks(brand="蝴蝶影视", meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


def unescape_html(s):
    out = str(s or "")
    out = out.replace("&amp;", "&")
    out = out.replace("&lt;", "<")
    out = out.replace("&gt;", ">")
    out = out.replace("&quot;", '"')
    out = re.sub(r"&#0?39;", "'", out)
    out = out.replace("&nbsp;", " ")
    return out


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", str(s or ""))


def origin_of(u):
    m = ORIGIN_RE.match(str(u or ""))
    return m.group(1) if m else ""


class Spider(BaseSpider):

    def getName(self):
        return SITE_NAME

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        self._custom_host = False
        self._host_ready = False
        self._nav_hosts = None
        self._nav_fail_at = 0.0
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
            self._host_ready = True

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- host discovery ----------

    def _extract_nav_hosts(self, html_text):
        for m in B64_RE.finditer(str(html_text or "")):
            raw = m.group(1)
            try:
                decoded = base64.b64decode(raw + "=" * (-len(raw) % 4)).decode("utf-8")
            except Exception:
                continue
            unq = unquote(decoded)
            if "[" not in unq or "{" not in unq or TARGET_NAME not in unq.lower():
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
                nm = str(item.get("name") or "").strip()
                desc = str(item.get("desc") or item.get("description") or "")
                if TARGET_NAME not in nm.lower() and TARGET_NAME not in desc.lower():
                    continue
                hosts = []
                o = origin_of(item.get("url"))
                if o:
                    hosts.append(o)
                urls = item.get("urls")
                if isinstance(urls, list):
                    for uo in urls:
                        oo = origin_of(uo.get("url") if isinstance(uo, dict) else "")
                        if oo and oo not in hosts:
                            hosts.append(oo)
                if hosts:
                    return hosts
        return []

    def _fetch_nav_hosts(self, nav_url):
        headers = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        try:
            resp = requests.get(nav_url, headers=headers, timeout=8)
            return self._extract_nav_hosts(resp.text or "")
        except Exception:
            return []

    def _probe_host(self, host):
        try:
            resp = requests.get(host + "/", headers={"User-Agent": UA, "Referer": host + "/"}, timeout=8)
            return 200 <= resp.status_code < 400 and len(resp.text or "") > 200
        except Exception:
            return False

    def _get_nav_hosts(self):
        if self._nav_hosts:
            return self._nav_hosts
        if self._nav_fail_at and (time.time() - self._nav_fail_at) < 600:
            return []
        hosts = []
        for nav_url in NAV_URLS:
            hosts = self._fetch_nav_hosts(nav_url)
            if hosts:
                break
        if hosts:
            self._nav_hosts = hosts
            return hosts
        self._nav_fail_at = time.time()
        return []

    def _pick_host(self):
        nav_hosts = self._get_nav_hosts()
        candidates = []
        for h in list(nav_hosts) + [DEFAULT_HOST]:
            hh = str(h or "").strip().rstrip("/")
            if hh and re.match(r"https?://", hh) and hh not in candidates:
                candidates.append(hh)
        for cand in candidates[:12]:
            if self._probe_host(cand):
                return cand
        return None

    def _ensure_host(self):
        if self._custom_host or self._host_ready:
            return self.host
        winner = self._pick_host()
        self.host = winner if winner else DEFAULT_HOST
        self._host_ready = True
        return self.host

    def _rediscover(self):
        winner = self._pick_host()
        if winner and winner != self.host:
            self.host = winner
            self._host_ready = True
            return winner
        return None

    # ---------- fetch ----------

    def _fetch_page(self, path, referer="", _retried=False):
        host = self._ensure_host()
        full = str(path or "")
        if full.startswith("//"):
            full = "https:" + full
        elif full.startswith("/"):
            full = host + full
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else (host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        try:
            resp = requests.get(full, headers=headers, timeout=8)
            text = resp.text or ""
            status = resp.status_code
        except Exception:
            if not _retried and not self._custom_host:
                if self._rediscover():
                    return self._fetch_page(path, referer, True)
            raise
        if status >= 400 and not _retried and not self._custom_host:
            if self._rediscover():
                return self._fetch_page(path, referer, True)
        return text, status, host

    # ---------- cards ----------

    def _abs_url(self, u, host):
        s = str(u or "").strip()
        if not s:
            return ""
        if s.startswith("//"):
            return "https:" + s
        if s.startswith("/"):
            return host + s
        return s

    def _format_poster(self, raw_pic, host):
        if not raw_pic:
            return ""
        full = self._abs_url(str(raw_pic).strip().replace("&amp;", "&"), host)
        if not re.match(r"https?://", full, re.I):
            return ""
        return full + "@Referer=" + quote(host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def _parse_cards(self, html_text, host):
        items = []
        seen = set()
        for m in CARD_RE.finditer(str(html_text or "")):
            hid = m.group(2).strip() if m.group(2) else ""
            if not hid or hid in seen:
                continue
            seen.add(hid)
            chunk = m.group(0)
            pm = IMG_SRC_RE.search(chunk) or DATA_SRC_RE.search(chunk)
            cover = pm.group(1).strip() if pm else (COVER_BASE + hid + ".jpg")
            name = ""
            tm = TITLE_ATTR_RE.search(chunk)
            if tm:
                name = tm.group(1).strip()
            else:
                plain = re.sub(r"\s+", " ", strip_tags(m.group(3))).strip()
                if plain and len(plain) > 2:
                    name = plain
            if not name:
                name = hid
            dm = DURATION_RE.search(chunk)
            duration = dm.group(1).strip() if dm else ""
            status = format_remarks(BRAND, duration) if duration else format_remarks(BRAND, "高清")
            items.append({
                "vod_id": hid,
                "vod_name": unescape_html(name),
                "vod_pic": self._format_poster(cover, host),
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

    def _filter_row(self, key, name, options):
        return {
            "key": key,
            "name": name,
            "init": options[0][0] if options else "",
            "value": [{"n": n, "v": v} for v, n in options],
        }

    # ---------- home ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CLASSES]
        result = {"class": classes}
        if filter:
            result["filters"] = {
                "latest": [self._filter_row("sort", "排序", LATEST_SORT)],
                "filter@@factories": [self._filter_row("slug", "選擇發行商", FALLBACK_FACTORIES)],
                "filter@@actors": [self._filter_row("slug", "選擇女優", FALLBACK_ACTORS)],
                "filter@@tags": [self._filter_row("slug", "選擇類型", FALLBACK_TAGS)],
            }
        return result

    def homeVideoContent(self):
        try:
            text, status, host = self._fetch_page("/list")
        except Exception:
            return {"list": []}
        items = self._parse_cards(text, host)
        if len(items) > HOME_CAP:
            items = items[:HOME_CAP]
        return {"list": items}

    # ---------- category / search ----------

    def categoryContent(self, tid, pg, filter, extend):
        slug = re.sub(r"^/+|/+$", "", str(tid or ""))
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        ext = extend if isinstance(extend, dict) else {}
        sub_slug = str(ext.get("slug") or "").strip()
        if slug == "filter@@actors":
            path = ("/actor?id=" + quote(sub_slug, safe="")) if sub_slug else "/list?sort=4"
        elif slug == "filter@@factories":
            path = ("/tag?fid=" + quote(sub_slug, safe="")) if sub_slug else "/list?sort=3"
        elif slug == "filter@@tags":
            path = ("/tag?id=" + quote(sub_slug, safe="")) if sub_slug else "/list"
        elif slug == "today_hot":
            path = "/list?sort=3"
        elif slug == "week_hot":
            path = "/list?sort=4"
        elif slug == "month_hot":
            path = "/list?sort=5"
        elif slug == "vr_zone":
            path = "/tag?id=81"
        else:
            sort_val = str(ext.get("sort") or "")
            path = ("/list?sort=" + quote(sort_val, safe="")) if sort_val else "/list"
        if page > 1:
            path += ("&" if "?" in path else "?") + "page=" + str(page) + "&idx=" + str(page)
        try:
            text, status, host = self._fetch_page(path)
        except Exception:
            return self._page_form([], page)
        return self._page_form(self._parse_cards(text, host), page)

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        if not keyword:
            return self._page_form([], page)
        url = "/search?search=" + quote(keyword, safe="")
        if page > 1:
            url += "&page=" + str(page) + "&p=" + str(page)
        try:
            text, status, host = self._fetch_page(url)
        except Exception:
            return self._page_form([], page)
        return self._page_form(self._parse_cards(text, host), page)

    # ---------- detail ----------

    def _brand_block(self, host):
        return [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ]

    def detailContent(self, ids):
        hid = ""
        if ids:
            hid = str(ids[0] or "").strip()
        try:
            text, status, host = self._fetch_page("/video?hid=" + quote(hid, safe=""))
        except Exception:
            return {"list": []}
        if not text:
            return {"list": []}

        tm = TITLE_TAG_RE.search(text)
        raw_title = tm.group(1).replace("- airav.io", "", 1).strip() if tm else hid
        title = unescape_html(raw_title)

        pm = COVER_RE.search(text)
        cover = pm.group(1) if pm else (COVER_BASE + hid + ".jpg")
        poster = self._format_poster(cover, host)

        dm = META_DESC_RE.search(text)
        desc = dm.group(1).strip() if dm else ""

        mm = CONTENT_URL_RE.search(text)
        play_url = mm.group(1).replace("\\/", "/") if mm else ""

        if play_url:
            ep_value = json.dumps({"playUrl": play_url})
            main_eps = ["正片$" + ep_value]
        else:
            ep_value = json.dumps({"pageUrl": host + "/embedded?hid=" + hid, "hid": hid})
            main_eps = ["解析线路$" + ep_value]

        tags = []
        ti = text.find("標籤：")
        if ti != -1:
            seg = text[ti:ti + 1500]
            for am in TAG_A_RE.finditer(seg):
                tname = strip_tags(am.group(1)).strip()
                if tname and tname not in tags:
                    tags.append(tname)

        related_eps = []
        related_titles = []
        ri = text.find("相關推薦")
        if ri != -1:
            for card in self._parse_cards(text[ri:], host):
                if card["vod_id"] == hid:
                    continue
                related_eps.append(card["vod_name"].replace("$", "_").replace("#", "_") + "$rel:" + card["vod_id"])
                related_titles.append(card["vod_name"])

        from_parts = [MAIN_LINE]
        url_parts = ["#".join(main_eps)]
        if related_eps:
            from_parts.append(RELATED_LINE)
            url_parts.append("#".join(related_eps))

        content_parts = self._brand_block(host)
        if desc:
            content_parts.append(desc)
        else:
            content_parts.append("标题：" + title)
            content_parts.append("分类：" + "、".join(tags))
            content_parts.append("片源：" + "、".join(from_parts))
            content_parts.append("编号：" + hid)
            if related_titles:
                content_parts.append("相关推荐：" + "、".join(related_titles[:6]))

        vod = {
            "vod_id": hid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks(BRAND, "正片"),
            "vod_content": "\n".join(content_parts),
            "vod_play_from": "$$$".join(from_parts),
            "vod_play_url": "$$$".join(url_parts),
        }
        return {"list": [vod]}

    # ---------- player ----------

    def _resolve_hid(self, hid, headers):
        host = self._ensure_host()
        text = ""
        used_host = host
        try:
            text, status, used_host = self._fetch_page("/video?hid=" + quote(hid, safe=""))
        except Exception:
            text = ""
        mm = CONTENT_URL_RE.search(text or "")
        if mm:
            return {"parse": 0, "url": mm.group(1).replace("\\/", "/"), "header": headers}
        return {"parse": 1, "url": used_host + "/embedded?hid=" + hid, "header": headers}

    def playerContent(self, flag, id, vipFlags):
        host = self._ensure_host()
        headers = {"User-Agent": UA, "Referer": host + "/", "Origin": host}
        pid = str(id or "")
        if pid.startswith("rel:"):
            return self._resolve_hid(pid[4:].strip(), headers)
        data = None
        try:
            data = json.loads(pid)
        except Exception:
            data = None
        if isinstance(data, dict):
            play_url = str(data.get("playUrl") or "")
            if play_url:
                return {"parse": 0, "url": play_url, "header": headers}
            hid = str(data.get("hid") or "")
            if hid:
                return self._resolve_hid(hid, headers)
            page_url = str(data.get("pageUrl") or "")
            if page_url:
                return {"parse": 1, "url": page_url, "header": headers}
        return {"parse": 1, "url": host + "/", "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249960005&sig=927a049ee907afab
