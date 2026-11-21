# -*- coding: utf-8 -*-
# 591AV | com.butterfly.591av

import base64
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://591av.ws"
NAV_URLS = ["https://x99dh.net", "https://x99dh.lat"]
TARGET_SITE_NAME = "亚洲素人精选"
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
SITE_NAME = "591AV"
BRAND_NAME = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
RELATED_NAME = "相关推荐"
PAGE_SIZE = 24
PIC_RATIO = 1.78

CLASSES = [
    ("china-av", "中国AV"),
    ("japan-producer", "日本片商"),
    ("amateur", "素人自拍"),
    ("china", "中国"),
    ("taiwan", "台湾"),
    ("japan", "日本"),
    ("se-asia", "东南亚"),
    ("korea", "韩国"),
    ("hongkong", "香港"),
    ("cosplay", "Cosplay"),
    ("streamer", "主播"),
    ("first-person-pov", "主观视角"),
    ("bdsm", "凌辱"),
    ("drama", "剧情"),
    ("threesome", "多P"),
    ("91-tanhua", "探花"),
    ("released", "流出"),
    ("uncensored", "无码"),
    ("lesbian", "百合"),
    ("exhibitionists", "野外露出"),
    ("office-lady", "OL"),
    ("acg", "动漫"),
    ("costume", "古装"),
    ("maid", "女仆"),
    ("student", "学生"),
    ("cheongsam", "旗袍"),
    ("kemonomimi", "兽耳"),
    ("yoga-pants", "瑜伽裤"),
    ("dolfin-shorts", "真理裤"),
    ("flight-attendant", "空姐"),
    ("pantyhose", "丝袜"),
    ("nurse", "护士"),
    ("knee-socks", "过膝袜"),
]
CLASS_NAME_MAP = dict(CLASSES)

SORT_OPTIONS = [
    ("post_date", "新上架"),
    ("most_favourited", "收藏量"),
    ("month_views", "观看次数(本月)"),
    ("video_viewed", "观看次数(总计)"),
]

CARD_RE = re.compile(r"""<a[^>]+href=['"]([^'"]*?/v/([a-zA-Z0-9_\-]+)/?)['"][^>]*>([\s\S]*?)</a>""", re.I)
IMG_DATA_SRC_RE = re.compile(r"""data-src=['"]([^'"]+)['"]""", re.I)
IMG_ALT_SRC_RE = re.compile(r"""(?:data-original|data-poster|src)=['"]([^'"]+)['"]""", re.I)
ALT_ATTR_RE = re.compile(r"""alt=['"]([^'"]+)['"]""", re.I)
TITLE_ATTR_RE = re.compile(r"""title=['"]([^'"]+)['"]""", re.I)
DUR_CLASS_RE = re.compile(r"""class=['"][^'"]*?duration[^'"]*?['"][^>]*>([0-9:]+)""", re.I)
DUR_TEXT_RE = re.compile(r">\s*([0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?)\s*<")
TAG_RE = re.compile(r"<[^>]+>")
H1_RE = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
OG_IMAGE_RE = re.compile(r"""property=['"]og:image['"]\s+content=['"]([^'"]+)['"]""", re.I)
POSTER_ATTR_RE = re.compile(r"""poster=['"]([^'"]+)['"]""", re.I)
STREAM_VAR_RE = re.compile(r"""var\s+stream\s*=\s*['"]([^'"]+\.m3u8[^'"]*)['"]""", re.I)
STREAM_GEN_RE = re.compile(r"""['"](https?://[^'"]+?/stream/[^'"]+?\.m3u8[^'"]*)['"]""", re.I)
B64_BLOB_RE = re.compile(r"""['"]([A-Za-z0-9+/=]{100,})['"]""")
ORIGIN_RE = re.compile(r"^(https?://[^/]+)", re.I)
CAT_LINK_RE = re.compile(r"""href=['"][^'"]*?/categories/([a-z0-9\-]+)/?['"]""", re.I)


def strip_tags(s):
    return TAG_RE.sub("", str(s or ""))


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND_NAME, clean_meta)
    return BRAND_NAME


def clean_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def init(self, extend=""):
        self.host = DEFAULT_HOST
        self._custom_host = ""
        raw = extend
        if isinstance(raw, dict):
            cand = str(raw.get("host") or "").strip()
        elif isinstance(raw, str):
            text = raw.strip()
            cand = ""
            if text.startswith("http"):
                cand = text
            elif text.startswith("{"):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        cand = str(parsed.get("host") or "").strip()
                except Exception:
                    cand = ""
        else:
            cand = ""
        if cand and cand.startswith("http"):
            self._custom_host = cand.rstrip("/")
            self.host = self._custom_host
        self._active_host = ""
        self._nav_hosts = None

    # ---------- host discovery ----------

    def _page_headers(self, host):
        return {
            "User-Agent": DEFAULT_UA,
            "Referer": host + "/enter",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _nav_headers(self):
        return {
            "User-Agent": DEFAULT_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def _extract_nav_hosts(self, text):
        for m in B64_BLOB_RE.finditer(str(text or "")):
            try:
                decoded = base64.b64decode(m.group(1)).decode("utf-8")
                unquoted = unquote(decoded)
                if "[" in unquoted and "{" in unquoted and TARGET_SITE_NAME in unquoted:
                    site_list = json.loads(unquoted)
                    if isinstance(site_list, list):
                        for item in site_list:
                            if not isinstance(item, dict):
                                continue
                            if str(item.get("name") or "").strip() == TARGET_SITE_NAME:
                                target_url = str(item.get("url") or "").strip()
                                if target_url:
                                    om = ORIGIN_RE.match(target_url)
                                    if om:
                                        return [om.group(1)]
            except Exception:
                continue
        return None

    def _fetch_nav_hosts(self):
        if self._nav_hosts is not None:
            return self._nav_hosts
        hosts = None
        for nav in NAV_URLS:
            try:
                resp = requests.get(nav, headers=self._nav_headers(), timeout=6)
                found = self._extract_nav_hosts(resp.text or "")
                if found:
                    hosts = found
                    break
            except Exception:
                continue
        self._nav_hosts = hosts if hosts else []
        return self._nav_hosts

    def _probe_host(self, host):
        try:
            resp = requests.get(
                host + "/enter",
                headers={"User-Agent": DEFAULT_UA, "Referer": host + "/"},
                timeout=5,
            )
            body = resp.text or ""
            if 200 <= resp.status_code < 400 and len(body) > 200:
                return host
        except Exception:
            return None
        return None

    def _discover_host(self):
        pool = []
        for h in self._fetch_nav_hosts():
            pool.append(h)
        pool.append(DEFAULT_HOST)
        seen = set()
        candidates = []
        for h in pool:
            host = str(h or "").strip().rstrip("/")
            if not host or not host.startswith("http") or host in seen:
                continue
            seen.add(host)
            candidates.append(host)
        for host in candidates[:8]:
            if self._probe_host(host):
                return host
        return ""

    def _active(self):
        if self._custom_host:
            return self._custom_host
        if self._active_host:
            return self._active_host
        winner = self._discover_host()
        self._active_host = winner if winner else DEFAULT_HOST
        return self._active_host

    def _fetch_page(self, path, retry=True):
        host = self._active()
        full_url = str(path or "")
        if full_url.startswith("//"):
            full_url = "https:" + full_url
        elif full_url.startswith("/"):
            full_url = host + full_url
        text = ""
        status = 0
        error = False
        try:
            resp = requests.get(full_url, headers=self._page_headers(host), timeout=8)
            status = resp.status_code
            text = resp.text or ""
        except Exception:
            error = True
        if (error or status >= 400) and retry and not self._custom_host:
            self._active_host = ""
            winner = self._discover_host()
            if winner and winner != host:
                self._active_host = winner
                return self._fetch_page(path, retry=False)
            if winner:
                self._active_host = winner
            if error:
                return "", 0, host
        return text, status, host

    # ---------- parsing ----------

    def _format_poster(self, raw_pic, host):
        if not raw_pic:
            return ""
        pic = str(raw_pic).strip()
        if pic.startswith("//"):
            pic = "https:" + pic
        elif pic.startswith("/"):
            pic = host + pic
        return pic + "@Referer=" + quote(host + "/", safe="") + "&User-Agent=" + quote(DEFAULT_UA, safe="")

    def _parse_cards(self, html_body, host):
        html = str(html_body or "")
        items = []
        seen = set()
        for m in CARD_RE.finditer(html):
            vod_id = (m.group(2) or "").strip()
            if not vod_id or vod_id in seen:
                continue
            chunk = m.group(0)
            vod_pic = ""
            img_m = IMG_DATA_SRC_RE.search(chunk)
            if img_m:
                vod_pic = img_m.group(1).strip()
            if not vod_pic:
                alt_m = IMG_ALT_SRC_RE.search(chunk)
                if alt_m:
                    cand = alt_m.group(1).strip()
                    cand_low = cand.lower()
                    if "placeholder" not in cand_low and "logo.png" not in cand_low:
                        vod_pic = cand
            vod_name = ""
            title_m = ALT_ATTR_RE.search(chunk)
            if not title_m:
                title_m = TITLE_ATTR_RE.search(chunk)
            if title_m:
                vod_name = title_m.group(1).strip()
            else:
                clean = re.sub(r"\s+", " ", strip_tags(m.group(3) or "")).strip()
                if clean and len(clean) > 2:
                    vod_name = clean
            if not vod_name:
                vod_name = vod_id
            duration = ""
            dur_m = DUR_CLASS_RE.search(chunk)
            if not dur_m:
                dur_m = DUR_TEXT_RE.search(chunk)
            if dur_m:
                duration = dur_m.group(1).strip()
            seen.add(vod_id)
            items.append({
                "vod_id": vod_id,
                "vod_name": vod_name,
                "vod_pic": self._format_poster(vod_pic, host),
                "vod_remarks": format_remarks(duration),
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
            pn = int(pg)
        except Exception:
            pn = 1
        if pn < 1:
            pn = 1
        return pn

    # ---------- entries ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CLASSES]
        result = {"class": classes}
        if filter:
            sort_row = {
                "key": "sort",
                "name": "排序",
                "init": "post_date",
                "value": [{"n": name, "v": value} for value, name in SORT_OPTIONS],
            }
            filters = {}
            for cid, _cname in CLASSES:
                filters[cid] = [dict(sort_row)]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        text, _status, host = self._fetch_page("/categories/china-av/", retry=True)
        items = self._parse_cards(text, host)
        return {"list": items[:18]}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        tid = re.sub(r"^/+|/+$", "", str(tid or "").strip()) or "china-av"
        sort_by = ""
        if isinstance(extend, dict):
            sort_by = str(extend.get("sort") or "").strip()
        path_parts = ["categories", tid]
        if sort_by and sort_by != "post_date":
            path_parts.append(sort_by)
        if page > 1:
            path_parts.append(str(page))
        req_path = "/" + "/".join(path_parts) + "/"
        text, _status, host = self._fetch_page(req_path, retry=True)
        items = self._parse_cards(text, host)
        if not items:
            if page > 1:
                alt_path = "/categories/" + tid + "/" + str(page) + "/"
            else:
                alt_path = "/categories/" + tid + "/"
            if sort_by and sort_by != "post_date":
                alt_path = alt_path + "?sort_by=" + quote(sort_by, safe="")
            alt_text, _alt_status, alt_host = self._fetch_page(alt_path, retry=True)
            items = self._parse_cards(alt_text, alt_host)
        return self._page_form(items, page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": 0}
        encoded = quote(keyword, safe="")
        if page > 1:
            req_path = "/search/" + encoded + "/" + str(page) + "/"
        else:
            req_path = "/search/" + encoded + "/"
        text, _status, host = self._fetch_page(req_path, retry=True)
        items = self._parse_cards(text, host)
        return self._page_form(items, page)

    def _brand_block(self, host):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ]
        return lines

    def _detail_categories(self, html):
        names = []
        seen = set()
        for m in CAT_LINK_RE.finditer(html):
            cid = m.group(1)
            if cid in seen:
                continue
            seen.add(cid)
            if cid in CLASS_NAME_MAP:
                names.append(CLASS_NAME_MAP[cid])
        return names

    def _related_cards(self, html, host, vod_id):
        start = html.find("list_videos_related_videos_items")
        if start < 0:
            return []
        end = html.find("title--listing", start)
        seg = html[start:end] if end > start else html[start:]
        related = []
        for card in self._parse_cards(seg, host):
            if card["vod_id"] != vod_id:
                related.append(card)
        return related

    def detailContent(self, ids):
        vod_id = ""
        if ids:
            vod_id = str(ids[0] or "").strip()
        if not vod_id:
            return {"list": []}
        text, _status, host = self._fetch_page("/v/" + vod_id + "/", retry=True)
        html = text or ""
        if not html:
            return {"list": []}
        title = vod_id
        h1_m = H1_RE.search(html)
        if h1_m:
            found = strip_tags(h1_m.group(1)).strip()
            if found:
                title = found
        poster = ""
        pic_m = OG_IMAGE_RE.search(html)
        if not pic_m:
            pic_m = POSTER_ATTR_RE.search(html)
        if pic_m:
            poster = self._format_poster(pic_m.group(1).strip(), host)
        related = self._related_cards(html, host, vod_id)
        line_names = [LINE_NAME]
        play_parts = ["%s$%s" % ("超清正片", vod_id)]
        if related:
            rel_eps = []
            for card in related:
                rel_eps.append("%s$rel:%s" % (clean_ep_name(card["vod_name"]), card["vod_id"]))
            line_names.append(RELATED_NAME)
            play_parts.append("#".join(rel_eps))
        cat_names = self._detail_categories(html)
        content_lines = self._brand_block(host)
        content_lines.append("标题：" + title)
        content_lines.append("分类：" + "、".join(cat_names))
        content_lines.append("片源：" + "、".join(line_names))
        content_lines.append("编号：" + vod_id)
        if related:
            rel_titles = []
            for card in related[:6]:
                rel_titles.append(card["vod_name"])
            content_lines.append("相关推荐：" + "、".join(rel_titles))
        vod = {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": BRAND_NAME,
            "vod_content": "\n".join(content_lines),
            "vod_play_from": "$$$".join(line_names),
            "vod_play_url": "$$$".join(play_parts),
        }
        return {"list": [vod]}

    def _extract_stream(self, html):
        m = STREAM_VAR_RE.search(html or "")
        if m:
            return m.group(1).strip()
        m = STREAM_GEN_RE.search(html or "")
        if m:
            return m.group(1).strip()
        return ""

    def playerContent(self, flag, id, vipFlags):
        pid = str(id or "").strip()
        target = pid
        if pid.startswith("rel:"):
            target = pid[4:].strip()
        if not target:
            return {"parse": 1, "playUrl": "", "url": self._active(), "header": {}}
        detail_path = "/v/" + target + "/"
        text, _status, host = self._fetch_page(detail_path, retry=True)
        video_url = self._extract_stream(text or "")
        headers = {"User-Agent": DEFAULT_UA, "Referer": host + detail_path}
        if video_url:
            return {"parse": 0, "playUrl": "", "url": video_url, "header": headers}
        return {"parse": 1, "playUrl": "", "url": host + detail_path, "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249417679&sig=207f64c63663cd12
