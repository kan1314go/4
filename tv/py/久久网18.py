# -*- coding: utf-8 -*-
# 久久网18.py - FongMi/TVBox python spider, converted from Hamo JS plugin com.hamo.source.jiujiu (久久网.js)

import hashlib
import json
import re
import time
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://www.jiujiu.live"
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
LINE_NAME = "蝴蝶专线"
TIMEOUT = 8
WAF_COOKIE_TTL = 86400
NO_SOURCE_TEXT = "未找到可播放片源"
DETAIL_FAIL_TEXT = "未找到该影片"
SUMMARY_TAIL = "🦋 蝴蝶影视专线直连 | 极速高清画质 | 官方交流群: @tvshare23"

STATIC_CLASSES = [
    ("23", "日本無碼"),
    ("9", "中文字幕"),
    ("82", "日韓無碼"),
    ("78", "AV明星"),
    ("31", "制服誘惑"),
    ("24", "日本有碼"),
    ("25", "歐美精品"),
    ("113", "無碼專區"),
    ("87", "動漫精品"),
    ("201", "歐美-高清無碼"),
    ("136", "歐美情色"),
    ("55", "成人動漫"),
    ("133", "歐美性愛"),
    ("271", "日韓精品"),
    ("116", "卡通動漫"),
    ("148", "倫理三級"),
    ("64", "巨乳美乳"),
    ("81", "童顏巨乳"),
    ("66", "亞洲有碼"),
    ("86", "歐美極品"),
    ("32", "AV解說"),
    ("110", "女優明星"),
    ("309", "歐美"),
    ("41", "倫理片"),
    ("100", "SWAG"),
    ("143", "人妻熟女"),
    ("8", "高清無碼"),
    ("358", "日本-素人"),
    ("90", "日本片商"),
    ("132", "卡通動畫"),
    ("71", "歐美激情"),
    ("155", "明星換臉"),
    ("176", "動漫卡通"),
    ("440", "無碼流出"),
    ("52", "AI換臉"),
    ("68", "亞洲無碼"),
    ("217", "日本-高清有碼"),
    ("122", "麻豆視頻"),
    ("163", "換臉明星"),
    ("269", "倫理影片"),
    ("238", "日本素人"),
    ("191", "獨家DMM"),
    ("101", "三級倫理"),
    ("109", "麻豆傳媒"),
    ("112", "歐美系列"),
    ("92", "激情動漫"),
    ("219", "日本-無碼流出"),
    ("331", "劇情介紹"),
    ("7", "3D動漫"),
    ("336", "日本精品"),
    ("193", "HEY誘惑"),
    ("200", "動漫-黃漫"),
    ("308", "華語AV"),
    ("203", "日本-一本道"),
    ("448", "動漫精選"),
    ("433", "歐美勁爆"),
    ("207", "傳媒-麻豆傳媒"),
    ("67", "日本女優"),
    ("402", "日本動漫"),
    ("73", "有碼精品"),
    ("199", "動漫-里番中字"),
    ("443", "高清有碼"),
    ("111", "歐美無碼"),
    ("489", "韓國三級"),
]

SORT_ROW = {
    "key": "sort",
    "name": "排序",
    "init": "",
    "value": [
        {"n": "最新发布", "v": ""},
        {"n": "最多播放", "v": "hits"},
    ],
}


def _encode_uri_component(s):
    return quote(str(s), safe="!*'()")


def _build_badge(meta):
    clean = re.sub(r"[\r\n\t]+", " ", str(meta or "")).strip()
    if clean:
        return "🦋 " + BRAND + " | " + clean
    return "🦋 " + BRAND


def _format_poster(raw_url, host):
    if not raw_url:
        return ""
    pic = str(raw_url).strip()
    if pic.startswith("data:image"):
        return ""
    if pic.startswith("//"):
        pic = "https:" + pic
    elif pic.startswith("/"):
        pic = host + pic
    pic = pic.split("@Referer")[0].split("@User-Agent")[0].strip()
    referer = _encode_uri_component(host + "/")
    ua = _encode_uri_component(DEFAULT_UA)
    return pic + "@Referer=" + referer + "&User-Agent=" + ua


def _clean_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        self.siteUrl = DEFAULT_HOST
        self._waf_cookie = ""
        self._waf_cookie_ts = 0.0

    def init(self, extend=""):
        host = ""
        if isinstance(extend, dict):
            host = str(extend.get("host") or "")
        elif isinstance(extend, str) and extend.strip():
            try:
                parsed = json.loads(extend)
                if isinstance(parsed, dict):
                    host = str(parsed.get("host") or "")
            except Exception:
                host = ""
        if host:
            self.siteUrl = host.rstrip("/")
        return self.siteUrl

    def getName(self):
        return "久久网"

    def _cookie_value(self):
        if self._waf_cookie and (time.time() - self._waf_cookie_ts) < WAF_COOKIE_TTL:
            return self._waf_cookie
        return ""

    def _solve_pow(self, waf_html, target_url):
        cfg_m = re.search(r"<script[^>]+id=[\"']__cdnlah_pow_config[\"'][^>]*>([\s\S]*?)</script>", waf_html, re.I)
        if not cfg_m:
            return False
        try:
            cfg = json.loads(cfg_m.group(1).strip())
        except Exception:
            return False
        if not isinstance(cfg, dict):
            return False
        seed = str(cfg.get("seed") or "")
        try:
            difficulty = int(cfg.get("difficulty") or 0)
        except Exception:
            difficulty = 0
        verify_path = cfg.get("verify_path") or "/__cdnlah/pow/verify"
        metadata_field = cfg.get("metadata_field") or "challenge_metadata"
        metadata_token = cfg.get("metadata_token") or ""
        challenge_cookie = cfg.get("challenge_cookie") or "_chg_waf_pow"
        redirect_val = cfg.get("redirect") or "/"
        if not seed or difficulty <= 0:
            return False
        target_prefix = "0" * difficulty
        nonce_hex = ""
        for n in range(1500000):
            cand_hex = "%016x" % n
            digest = hashlib.sha256((seed + cand_hex).encode("utf-8")).hexdigest()
            if digest.startswith(target_prefix):
                nonce_hex = cand_hex
                break
        if not nonce_hex:
            return False
        form_payload = {
            "seed": seed,
            "nonce": nonce_hex,
            "redirect": redirect_val,
            "challenge_cookie": challenge_cookie,
            metadata_field: metadata_token,
        }
        try:
            resp = requests.post(
                self.siteUrl + verify_path,
                data=form_payload,
                headers={
                    "User-Agent": DEFAULT_UA,
                    "Origin": self.siteUrl,
                    "Referer": target_url or (self.siteUrl + "/"),
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                },
                timeout=TIMEOUT,
            )
            set_cookie = resp.headers.get("Set-Cookie") or resp.headers.get("set-cookie") or ""
            cookie_m = re.search("(" + re.escape(str(challenge_cookie)) + r"=[^;,\s]+)", set_cookie)
            if cookie_m:
                self._waf_cookie = cookie_m.group(1).strip()
                self._waf_cookie_ts = time.time()
                return True
            jar_val = ""
            try:
                jar_val = resp.cookies.get(str(challenge_cookie)) or ""
            except Exception:
                jar_val = ""
            if jar_val:
                self._waf_cookie = str(challenge_cookie) + "=" + jar_val
                self._waf_cookie_ts = time.time()
                return True
        except Exception:
            return False
        return False

    def _request_get(self, url_path, referer=""):
        target_url = str(url_path or "")
        if target_url.startswith("//"):
            target_url = "https:" + target_url
        elif target_url.startswith("/"):
            target_url = self.siteUrl + target_url
        headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": referer or (self.siteUrl + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh-TW,zh;q=0.9,en;q=0.8",
        }
        cookie = self._cookie_value()
        if cookie:
            headers["Cookie"] = cookie
        for attempt in range(3):
            try:
                resp = requests.get(target_url, headers=headers, timeout=TIMEOUT)
                text = resp.content.decode("utf-8", "ignore") if resp.content else ""
                if "__cdnlah_pow_config" in text and attempt < 2:
                    if self._solve_pow(text, target_url):
                        cookie = self._cookie_value()
                        if cookie:
                            headers["Cookie"] = cookie
                        continue
                return text
            except Exception:
                if attempt < 2:
                    continue
                return ""
        return ""

    def _parse_cards(self, html):
        items = []
        if not html:
            return items
        seen = set()
        blocks = str(html).split('<div class="col-')
        for block in blocks[1:]:
            href_m = re.search(r"href=[\"'](?:https?://[^/]+)?/(\d+)[\"']", block, re.I)
            if not href_m:
                continue
            vid = href_m.group(1).strip()
            if vid in seen:
                continue
            seen.add(vid)
            title = ""
            lines_m = re.search(r"<div[^>]+class=[\"'][^\"']*\blines\b[^\"']*[\"'][^>]*>([\s\S]*?)</div>", block, re.I)
            if lines_m:
                title = re.sub(r"<[^>]+>", "", lines_m.group(1)).strip()
            if not title:
                alt_m = re.search(r"<img[^>]+alt=[\"']([^\"']+)[\"']", block, re.I)
                if alt_m:
                    title = alt_m.group(1).strip()
            if not title:
                title = "影片 " + vid
            pic = ""
            for attr in ("data-original", "data-src", "data-url", "src"):
                attr_m = re.search(attr + r"=[\"']([^\"']+)[\"']", block, re.I)
                if attr_m:
                    cand = attr_m.group(1).strip()
                    if not cand.startswith("data:image"):
                        pic = cand
                        break
            badge_m = re.search(r"<span[^>]+class=[\"'][^\"']*\bbadge\b[^\"']*[\"'][^>]*>([^<]+)</span>", block, re.I)
            meta = badge_m.group(1).strip() if badge_m else "HD"
            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": _format_poster(pic, self.siteUrl),
                "vod_remarks": _build_badge(meta),
            })
        return items

    def _brand_block(self):
        return "\n".join([
            "🦋 久久网官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.siteUrl,
            "━" * 28,
            "━" * 7,
        ])

    def _page_form(self, page, cards):
        n = len(cards)
        if n == 0:
            return {"page": page, "pagecount": page, "limit": 1, "total": 0, "list": []}
        return {"page": page, "pagecount": page + 1, "limit": n, "total": (page + 1) * n, "list": cards}

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in STATIC_CLASSES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, _cname in STATIC_CLASSES:
                filters[cid] = [dict(SORT_ROW, value=[dict(o) for o in SORT_ROW["value"]])]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        html = self._request_get("/c/23")
        return {"list": self._parse_cards(html)}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        category_id = str(tid or "23").strip() or "23"
        sort_val = ""
        if isinstance(extend, dict):
            sort_val = str(extend.get("sort") or "")
        query_parts = []
        if page > 1:
            query_parts.append("page=" + str(page))
        if sort_val:
            query_parts.append("sort=" + sort_val)
        query_str = ("?" + "&".join(query_parts)) if query_parts else ""
        html = self._request_get("/c/" + category_id + query_str)
        return self._page_form(page, self._parse_cards(html))

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_form(page, [])
        query_str = "?keyword=" + _encode_uri_component(keyword)
        if page > 1:
            query_str += "&page=" + str(page)
        html = self._request_get("/node/search" + query_str)
        return self._page_form(page, self._parse_cards(html))

    def detailContent(self, ids):
        if isinstance(ids, (list, tuple)):
            raw = str(ids[0]) if ids else ""
        else:
            raw = str(ids or "")
        vid = raw.strip()
        if not vid:
            return {"list": [], "msg": DETAIL_FAIL_TEXT}
        html = self._request_get("/" + vid)
        if not html:
            return {"list": [], "msg": DETAIL_FAIL_TEXT}
        title_m = re.search(r"<title>(.*?)</title>", html, re.I)
        if title_m:
            title = title_m.group(1).split("-")[0].strip()
        else:
            title = "影片 " + vid
        vod_pic_raw = ""
        poster_m = re.search(r"poster=[\"']([^\"']+)[\"']", html, re.I)
        if poster_m:
            vod_pic_raw = poster_m.group(1).strip()
        else:
            og_m = re.search(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']", html, re.I)
            if og_m:
                vod_pic_raw = og_m.group(1).strip()
        poster = _format_poster(vod_pic_raw, self.siteUrl)
        play_url = ""
        source_m = re.search(r"<source[^>]+src=[\"']([^\"']+\.m3u8[^\"']*)[\"']", html, re.I)
        if source_m:
            play_url = source_m.group(1).strip()
        else:
            all_m3u8 = re.findall(r"https?://[^\s\"'<>]+\.m3u8[^\s\"'<>]*", html, re.I)
            if all_m3u8:
                play_url = all_m3u8[0]
            else:
                video_m = re.search(r"<video[^>]+src=[\"']([^\"']+)[\"']", html, re.I)
                if video_m:
                    play_url = video_m.group(1).strip()
        content = self._brand_block() + "\n" + SUMMARY_TAIL
        if play_url:
            episodes = [_clean_ep_name("超清正片") + "$" + json.dumps({"playUrl": play_url}, ensure_ascii=False)]
        else:
            fallback_url = self.siteUrl + "/" + vid
            episodes = [_clean_ep_name("超清正片") + "$" + json.dumps({"playUrl": fallback_url}, ensure_ascii=False)]
        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": "🦋 蝴蝶影视",
            "vod_remarks": _build_badge("正片"),
            "vod_content": content,
            "vod_play_from": LINE_NAME,
            "vod_play_url": "#".join(episodes),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "")
        ref = {}
        if raw.startswith("{"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    ref = parsed
            except Exception:
                ref = {}
        if ref.get("notice"):
            return {"parse": 0, "msg": str(ref["notice"])}
        final_url = str(ref.get("playUrl") or "")
        if not final_url and not raw.startswith("{"):
            final_url = raw
        final_url = final_url.strip()
        if not final_url:
            return {"parse": 0, "jx": 0, "url": "", "msg": NO_SOURCE_TEXT}
        if not final_url.startswith("http"):
            final_url = self.siteUrl + (final_url if final_url.startswith("/") else "/" + final_url)
        low = final_url.lower()
        is_stream = (".m3u8" in low) or (".mp4" in low) or (".ts" in low)
        if is_stream and ".m3u8" not in low:
            sep = "&" if "?" in final_url else "?"
            final_url = final_url + sep + "format=.m3u8"
        return {
            "parse": 0 if is_stream else 1,
            "jx": 0,
            "url": final_url,
            "header": {
                "User-Agent": DEFAULT_UA,
                "Referer": self.siteUrl + "/",
                "Accept": "*/*",
            },
        }

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249782127&sig=751892c4943526b6
