# -*- coding: utf-8 -*-
# 2048核基地18.py - FongMi/TVBox python spider, converted from Hamo JS plugin com.butterfly.base2048 (2048核基地.js)

import json
import re
import time
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

BRAND_NAME = "🦋 蝴蝶影视"
DEFAULT_HOST = "https://s7t8u9v0.luanlunba15.cc"
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
PUBLISH_PAGES = [
    "https://www.luanlunba.cc",
    "https://s7t8u9v0.luanlunba13.cc",
    "https://s7t8u9v0.luanlunba14.cc",
]
LINE_NAME = "🦋 蝴蝶专线"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
TIMEOUT = 8
PROBE_TIMEOUT = 4
HOST_CACHE_TTL = 21600
DETAIL_FAIL_TEXT = "未找到该影片"

CATEGORIES_DATA = [
    ("1", "国产传媒"),
    ("2", "国产剧情"),
    ("58", "网曝黑料"),
    ("3", "特色仓库"),
    ("69", "精品资源"),
    ("78", "热播片库"),
    ("6", "麻豆视频"),
    ("7", "91制片厂"),
    ("8", "天美传媒"),
    ("9", "蜜桃传媒"),
    ("10", "皇家华人"),
    ("11", "星空传媒"),
    ("12", "精东影业"),
    ("20", "乐播传媒"),
    ("57", "兔子先生"),
    ("21", "杏吧原创"),
    ("22", "糖心Vlog"),
    ("24", "玩偶姐姐"),
    ("25", "mini传媒"),
    ("26", "大象传媒"),
    ("30", "成人头条"),
    ("31", "乌鸦传媒"),
    ("60", "国产精品"),
    ("61", "华语AV"),
    ("62", "黑料吃瓜"),
    ("63", "学生合集"),
    ("64", "乱伦精品"),
    ("65", "探花约炮"),
    ("66", "日本无码"),
    ("67", "主播网红"),
    ("37", "国产自拍"),
    ("32", "强奸乱伦"),
    ("33", "女优明星"),
    ("34", "欧美激情"),
    ("28", "重口激情"),
    ("29", "三级伦理"),
    ("35", "剧情动漫"),
    ("15", "SM调教"),
    ("70", "女同性恋"),
    ("71", "日韩无码"),
    ("72", "网曝吃瓜"),
    ("73", "约炮自拍"),
    ("74", "偷拍偷窥"),
    ("75", "日韩主播"),
    ("76", "中文字幕"),
    ("77", "主播诱惑"),
    ("79", "传媒剧情"),
    ("80", "抖阴短片"),
    ("81", "AV解说"),
    ("82", "换脸明星"),
    ("83", "VR视角"),
]

DL_CARD_RE = re.compile(
    r"<dl>[\s\S]*?<dt[^>]*>[\s\S]*?<a[^>]+href=[\"']/voddetail/(\d+)\.html[\"'][^>]*>"
    r"[\s\S]*?<img[^>]+data-original=[\"']([^\"']*)[\"'][^>]*>[\s\S]*?</a>[\s\S]*?</dt>"
    r"[\s\S]*?<dd>[\s\S]*?<a[^>]+href=[\"']/voddetail/\d+\.html[\"'][^>]*>([\s\S]*?)</a>"
    r"[\s\S]*?</dd>[\s\S]*?</dl>",
    re.I,
)
BUTTON_RE = re.compile(
    r"<div[^>]+class=[\"']item[\"'][^>]*>[\s\S]*?<a[^>]+href=[\"'](/vodplay/[0-9_\-]+\.html)[\"'][^>]*>([\s\S]*?)</a>",
    re.I,
)
ALT_BUTTON_RE = re.compile(
    r"href=[\"'](/vodplay/[0-9_\-]+\.html)[\"'][^>]*>([\s\S]*?)</a>",
    re.I,
)


def _encode_uri_component(s):
    return quote(str(s), safe="!*'()")


def _strip_html(s):
    if not s:
        return ""
    out = re.sub(r"<[^>]+>", "", str(s))

    def _dec(m):
        try:
            return chr(int(m.group(1), 10) % 65536)
        except Exception:
            return m.group(0)

    def _hex(m):
        try:
            return chr(int(m.group(1), 16) % 65536)
        except Exception:
            return m.group(0)

    out = re.sub(r"&#([0-9]{1,7});", _dec, out)
    out = re.sub(r"&#x([0-9a-fA-F]{1,6});", _hex, out)
    out = re.sub(r"&nbsp;", " ", out, flags=re.I)
    out = re.sub(r"&amp;", "&", out, flags=re.I)
    out = re.sub(r"&lt;", "<", out, flags=re.I)
    out = re.sub(r"&gt;", ">", out, flags=re.I)
    out = re.sub(r"&quot;", '"', out, flags=re.I)
    out = re.sub(r"&#39;", "'", out, flags=re.I)
    return re.sub(r"\s+", " ", out).strip()


def _format_poster(raw, host):
    pic = str(raw or "").strip()
    if not pic:
        return ""
    if not pic.startswith("http"):
        if pic.startswith("//"):
            pic = "https:" + pic
        else:
            pic = host + (pic if pic.startswith("/") else "/" + pic)
    pic = pic.replace("&amp;", "&")
    return pic + "@Referer=" + _encode_uri_component(host + "/") + "&User-Agent=" + _encode_uri_component(DEFAULT_UA)


def _clean_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


def _resp_text(resp):
    try:
        if resp is not None and resp.content:
            return resp.content.decode("utf-8", "ignore")
    except Exception:
        return ""
    return ""


class Spider(BaseSpider):
    def __init__(self):
        self.siteUrl = DEFAULT_HOST
        self._custom_host = ""
        self._active_host = ""
        self._active_host_ts = 0.0

    def init(self, extend=""):
        raw = ""
        if isinstance(extend, dict):
            raw = str(extend.get("host") or "")
        elif isinstance(extend, str) and extend.strip():
            try:
                parsed = json.loads(extend)
                if isinstance(parsed, dict):
                    raw = str(parsed.get("host") or "")
            except Exception:
                raw = ""
        custom = raw.strip()
        if custom and custom.startswith("http"):
            self._custom_host = custom.rstrip("/")
        return self.siteUrl

    def getName(self):
        return "2048核基地"

    def _resolve_host(self):
        base = self._custom_host if self._custom_host else DEFAULT_HOST
        if base != DEFAULT_HOST:
            return base
        if self._active_host and (time.time() - self._active_host_ts) < HOST_CACHE_TTL:
            return self._active_host
        for pub in PUBLISH_PAGES:
            try:
                r1 = requests.get(pub + "/", headers={"User-Agent": DEFAULT_UA}, timeout=PROBE_TIMEOUT)
                html1 = _resp_text(r1)
                cookie_str = ""
                mc = re.search(r"document\.cookie\s*=\s*\"([^\"]+)\"", html1)
                if mc and mc.group(1):
                    cookie_str = mc.group(1)
                ajax_headers = {
                    "User-Agent": DEFAULT_UA,
                    "Referer": pub + "/",
                    "X-Requested-With": "XMLHttpRequest",
                }
                if cookie_str:
                    ajax_headers["Cookie"] = cookie_str
                r2 = requests.get(pub + "/xuexi/data.php", headers=ajax_headers, timeout=PROBE_TIMEOUT)
                text2 = _resp_text(r2)
                candidate_urls = []
                try:
                    d2 = json.loads(text2)
                    if isinstance(d2, dict) and isinstance(d2.get("urls"), list):
                        candidate_urls = d2["urls"]
                except Exception:
                    m_urls = re.findall(r"https?://[a-z0-9]+\.luanlunba\d*\.\w+", text2, re.I)
                    if m_urls:
                        candidate_urls = m_urls
                for cand in candidate_urls:
                    u = str(cand).rstrip("/")
                    if u.startswith("http"):
                        try:
                            probe = requests.get(u + "/", headers={"User-Agent": DEFAULT_UA}, timeout=PROBE_TIMEOUT)
                            p_html = _resp_text(probe)
                            if ("vodtype" in p_html) or ("voddetail" in p_html):
                                self._active_host = u
                                self._active_host_ts = time.time()
                                return u
                        except Exception:
                            continue
            except Exception:
                continue
        return base

    def _request_text(self, url, host):
        headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            text = _resp_text(resp)
            if text:
                return text
        except Exception:
            if url.startswith("https://"):
                fallback_url = "http://" + url[len("https://"):]
                try:
                    resp2 = requests.get(fallback_url, headers=headers, timeout=TIMEOUT)
                    text2 = _resp_text(resp2)
                    if text2:
                        return text2
                except Exception:
                    pass
        return ""

    def _parse_cards(self, html, host):
        items = []
        if not html:
            return items
        seen = set()
        for m in DL_CARD_RE.finditer(str(html)):
            vid = (m.group(1) or "").strip()
            raw_img = (m.group(2) or "").strip()
            raw_title = (m.group(3) or "").strip()
            if not vid or vid in seen:
                continue
            seen.add(vid)
            title = _strip_html(raw_title)
            if not title:
                title = "片目 " + vid
            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": _format_poster(raw_img, host),
                "vod_remarks": BRAND_NAME + " | 超清",
            })
        return items

    def _extract_m3u8_list(self, html):
        urls = []
        if not html:
            return urls
        pm = re.search(r"var\s+player_aaaa\s*=\s*({[\s\S]*?});", str(html))
        if pm and pm.group(1):
            try:
                p_data = json.loads(pm.group(1))
                if isinstance(p_data, dict) and p_data.get("url"):
                    raw_dec = unquote(str(p_data["url"]))
                    if raw_dec.startswith("http"):
                        urls.append(raw_dec)
            except Exception:
                pass
        for dm in re.finditer(r"https?://[^\s\"'<>]+\.m3u8[^\s\"'<>]*", str(html), re.I):
            if dm and dm.group(0):
                urls.append(dm.group(0))
        for sm in re.finditer(r"<script[^>]*>([\s\S]*?)</script>", str(html), re.I):
            scr_body = sm.group(1) or ""
            for jm in re.finditer(r"[\"']url[\"']\s*:\s*[\"']([^\"']+\.m3u8[^\"']*)[\"']", scr_body, re.I):
                if jm and jm.group(1):
                    urls.append(jm.group(1))
        clean = []
        seen = set()
        for u in urls:
            if u and u.startswith("http") and u not in seen:
                seen.add(u)
                clean.append(u)
        return clean

    def _brand_block(self, host):
        return "\n".join([
            "🦋 2048核基地官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ])

    def _page_form(self, page, cards):
        n = len(cards)
        if n == 0:
            return {"page": page, "pagecount": page, "limit": 1, "total": 0, "list": []}
        return {"page": page, "pagecount": page + 1, "limit": n, "total": (page + 1) * n, "list": cards}

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES_DATA]
        return {"class": classes}

    def homeVideoContent(self):
        host = self._resolve_host()
        html = self._request_text(host + "/", host)
        items = self._parse_cards(html, host)
        if len(items) == 0:
            fallback_html = self._request_text(host + "/vodtype/1.html", host)
            items = self._parse_cards(fallback_html, host)
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        host = self._resolve_host()
        category_id = str(tid or "").strip() or "1"
        page = self._to_page(pg)
        if page > 1:
            target_url = host + "/vodtype/" + category_id + "-" + str(page) + ".html"
        else:
            target_url = host + "/vodtype/" + category_id + ".html"
        html = self._request_text(target_url, host)
        return self._page_form(page, self._parse_cards(html, host))

    def searchContent(self, key, quick, pg="1"):
        host = self._resolve_host()
        keyword = str(key or "").strip()
        page = self._to_page(pg)
        target_url = host + "/vodsearch/-------------.html?wd=" + _encode_uri_component(keyword) + "&page=" + str(page)
        html = self._request_text(target_url, host)
        return self._page_form(page, self._parse_cards(html, host))

    def detailContent(self, ids):
        if isinstance(ids, (list, tuple)):
            raw = str(ids[0]) if ids else ""
        else:
            raw = str(ids or "")
        vid = raw.strip()
        if not vid:
            return {"list": [], "msg": DETAIL_FAIL_TEXT}
        host = self._resolve_host()
        detail_url = host + "/voddetail/" + vid + ".html"
        html = self._request_text(detail_url, host)
        if not html:
            return {"list": [], "msg": DETAIL_FAIL_TEXT}
        title = ""
        h1m = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
        if h1m and h1m.group(1):
            title = _strip_html(h1m.group(1))
        if not title:
            tm = re.search(r"<title>([\s\S]*?)</title>", html, re.I)
            if tm and tm.group(1):
                title = _strip_html(tm.group(1))
        if not title:
            title = "影片 " + vid
        poster_raw = ""
        imgm = re.search(r"<img[^>]+data-original=[\"']([^\"']*)[\"'][^>]*>", html, re.I)
        if imgm and imgm.group(1):
            poster_raw = imgm.group(1).strip()
        if not poster_raw:
            ogm = re.search(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']", html, re.I)
            if ogm and ogm.group(1):
                poster_raw = ogm.group(1).strip()
        poster = _format_poster(poster_raw, host)
        buttons = []
        for bm in BUTTON_RE.finditer(html):
            href = (bm.group(1) or "").strip()
            b_name = _strip_html(bm.group(2) or "")
            if href:
                buttons.append((href, b_name))
        if len(buttons) == 0:
            for bm in ALT_BUTTON_RE.finditer(html):
                href = (bm.group(1) or "").strip()
                b_name = _strip_html(bm.group(2) or "")
                if href:
                    buttons.append((href, b_name))
        if len(buttons) == 0:
            buttons.append(("/vodplay/" + vid + "-1-1.html", "立即播放"))
        episodes = []
        for i, pair in enumerate(buttons):
            href, b_name = pair
            ep_name = b_name if b_name else ("第 " + str(i + 1) + " 集")
            if href.startswith("http"):
                ep_url = href
            else:
                ep_url = host + (href if href.startswith("/") else "/" + href)
            env = {"playUrl": ep_url, "itemId": vid}
            episodes.append(_clean_ep_name(ep_name) + "$" + json.dumps(env, ensure_ascii=False))
        content = self._brand_block(host) + "\n" + "【影片简介】" + title + "，极速专线直连，提供高清原生画质播放。"
        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": "🦋 蝴蝶影视",
            "vod_remarks": BRAND_NAME + " | 正片",
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
        play_page_url = str(ref.get("playUrl") or "")
        item_id = str(ref.get("itemId") or "")
        if not play_page_url:
            if raw.startswith("http"):
                play_page_url = raw
            else:
                host0 = self._resolve_host()
                play_page_url = host0 + "/vodplay/" + item_id + "-1-1.html"
        host = self._resolve_host()
        play_html = self._request_text(play_page_url, host)
        m3u8_list = self._extract_m3u8_list(play_html)
        target_media_url = ""
        if len(m3u8_list) > 0:
            target_media_url = m3u8_list[0]
        headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": host + "/",
        }
        if target_media_url and target_media_url.startswith("http"):
            return {"parse": 0, "jx": 0, "url": target_media_url, "header": headers}
        return {"parse": 1, "jx": 0, "url": play_page_url, "header": headers}

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249462753&sig=2d9423354536e9e6
