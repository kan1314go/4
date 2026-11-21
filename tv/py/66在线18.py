# -*- coding: utf-8 -*-
# 66在线18.py - FongMi/TVBox python spider, converted from Hamo JS plugin com.butterfly.zaixian66 (66在线.js)

import re
import json
import base64
import requests
from urllib.parse import quote, unquote
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://442855.66sp025.top"
SUB = "liuliu"
DEFAULT_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
BRAND = "蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
RELATED_LINE = "相关推荐"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
SUMMARY_BODY = "【极速高清播放】66在线原生专线已就绪，欢迎加入交流群。"
DETAIL_REMARKS = "蝴蝶影视 | 正片"
TIMEOUT = 8
PAGE_SIZE = 18
SEARCH_SIZE = 16
POSTER_RATIO = 1.78

CATEGORIES = [
    ("66", "素人自拍"), ("29", "日本有码"), ("28", "国产传媒"), ("27", "中文字幕"),
    ("26", "国产视频"), ("59", "多人多P"), ("60", "野外露出"), ("61", "瑜伽裤"),
    ("62", "台湾辣妹"), ("63", "巨乳美乳"), ("64", "Cosplay"), ("65", "精品推荐"),
    ("30", "日本无码"), ("67", "兽耳系列"), ("68", "恋腿狂魔"), ("69", "自拍偷拍"),
    ("72", "剧情介绍"), ("73", "古装扮演"), ("74", "欺辱凌辱"), ("75", "风情旗袍"),
    ("76", "人妻熟女"), ("77", "口交颜射"), ("78", "男同性恋"), ("47", "人妖系列"),
    ("49", "VR视角"), ("55", "东南亚AV"), ("56", "91探花"), ("57", "唯美港姐"),
    ("58", "闷骚护士"), ("41", "AV解说"), ("42", "SM调教"), ("43", "萝莉少女"),
    ("45", "女同性恋"), ("46", "网红头条"), ("48", "韩国主播"), ("37", "抖阴视频"),
    ("38", "女优明星"), ("39", "网曝黑料"), ("40", "伦理三级"), ("33", "制服诱惑"),
    ("34", "国产主播"), ("35", "激情动漫"), ("36", "明星换脸"), ("32", "强奸乱伦"),
    ("31", "欧美无码"),
]

_CARD_LINK_RE = re.compile(r"href=[\"'](/" + SUB + r"/index\.php/vod/(?:play|detail)/id/(\d+)[^\"']*)[\"']", re.I)
_PLAY_ANCHOR_RE = re.compile(r"href=[\"'](/" + SUB + r"/index\.php/vod/play/id/\d+/sid/\d+/nid/\d+\.html)[\"'][^>]*>([^<]{1,15})</a>", re.I)
_STREAM_RE = re.compile(r"\.(?:m3u8|mp4)(\?|$)", re.I)
_VALIDATOR_RE = re.compile(r"document\.cookie\s*=\s*\"([A-Za-z0-9_]+=[^\";]+)")


def _unescape_html(s):
    out = str(s or "")
    out = out.replace("&amp;", "&")
    out = out.replace("&lt;", "<")
    out = out.replace("&gt;", ">")
    out = out.replace("&quot;", '"')
    out = re.sub(r"&#0?39;", "'", out)
    out = out.replace("&nbsp;", " ")

    def _num(m):
        try:
            return chr(int(m.group(1)) % 65536)
        except Exception:
            return m.group(0)

    out = re.sub(r"&#(\d+);", _num, out)
    return out


def _clean_text(s):
    out = re.sub(r"<[^>]+>", "", str(s or ""))
    return re.sub(r"\s+", " ", _unescape_html(out)).strip()


def _unwrap_html(raw):
    if not raw:
        return ""
    t = str(raw).strip()
    if t.startswith('"') and t.endswith('"') and len(t) >= 2:
        try:
            dec = json.loads(t)
            if isinstance(dec, str) and dec:
                return dec
        except Exception:
            t = t[1:-1]
    t = t.replace('\\"', '"')
    t = t.replace("\\/", "/")
    t = t.replace("\\r\\n", "\n")
    t = t.replace("\\n", "\n")
    t = t.replace("\\t", " ")
    return t


def _abs_url(u, host):
    u = str(u or "").strip().replace("&amp;", "&")
    if not u:
        return ""
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return host + u
    if u.startswith("http"):
        return u
    return host + "/" + u


def _base_abs(u, host):
    u = str(u or "").strip().replace("&amp;", "&")
    if not u:
        return ""
    if u.startswith("http"):
        return u
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return host + u
    return host + "/" + SUB + "/" + u


def _pick_pic(block, host):
    for attr in ("data-original", "data-src", "src"):
        m = re.search(r"<img[^>]*?\b" + attr + r"=[\"']([^\"']+)[\"']", block, re.I)
        if m:
            u = m.group(1).strip()
            if not u or "data:image" in u:
                continue
            low = u.lower()
            if "loading" in low or "load.svg" in low or "placeholder" in low or "blank" in low:
                continue
            return _abs_url(_base_abs(u, host), host)
    return ""


def _encode_id(vid, pic):
    if pic:
        return vid + "@@" + quote(pic, safe="")
    return vid


def _parse_cards(h, host):
    items = []
    seen = set()
    if not h:
        return items
    for lm in re.finditer(r"<li>([\s\S]*?)</li>", str(h), re.I):
        block = lm.group(1)
        um = _CARD_LINK_RE.search(block)
        if not um:
            continue
        vid = um.group(2)
        if vid in seen:
            continue
        seen.add(vid)
        nm = re.search(r"<h5><a[^>]*>([^<]+)</a></h5>", block, re.I)
        name = _clean_text(nm.group(1)) if nm else ""
        if not name:
            name = "视频 " + vid
        dm = re.search(r"<span[^>]*class=[\"'][^\"']*(?:duration|time|tag)[^\"']*[\"'][^>]*>([^<]+)</span>", block, re.I)
        meta = _clean_text(dm.group(1)) if dm and dm.group(1).strip() else "高清"
        pic = _pick_pic(block, host)
        items.append({
            "_vid": vid,
            "vod_id": _encode_id(vid, pic),
            "vod_name": name,
            "vod_pic": pic,
            "vod_remarks": BRAND + " | " + meta,
            "style": {"type": "rect", "ratio": POSTER_RATIO},
        })
    return items


def _public_card(card):
    return {
        "vod_id": card["vod_id"],
        "vod_name": card["vod_name"],
        "vod_pic": card["vod_pic"],
        "vod_remarks": card["vod_remarks"],
        "style": card["style"],
    }


def _parse_player_json(h, varname):
    idx = h.find("var " + varname + "=")
    if idx < 0:
        return None
    seg = h[idx:idx + 12000]
    start = seg.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(seg)):
        c = seg[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(seg[start:i + 1])
                except Exception:
                    return None
    return None


def _b64_decode(s):
    try:
        t = str(s or "")
        t += "=" * (-len(t) % 4)
        return base64.b64decode(t).decode("utf-8", "replace")
    except Exception:
        return ""


def _decode_player_url(url, encrypt):
    if not url:
        return ""
    try:
        if encrypt == 1:
            return unquote(url)
        if encrypt == 2:
            raw = _b64_decode(unquote(url))
            try:
                return unquote(raw)
            except Exception:
                return raw
    except Exception:
        pass
    return url


def _extract_mac_play_url(h):
    if not h:
        return ""
    for varname in ("player_aaaa", "player_data"):
        data = _parse_player_json(h, varname)
        if data and data.get("url"):
            u = _decode_player_url(str(data["url"]), data.get("encrypt") or 0)
            if u:
                return u
    m = re.search(r"MacPlayer\.PlayUrl\s*=\s*[\"']([^\"']+)[\"']", h, re.I)
    if m and m.group(1).strip():
        return m.group(1).strip()
    m = re.search(r"var\s+dp_video_url\s*=\s*['\"]([^'\"]+)['\"]", h, re.I)
    if m:
        d = _b64_decode(m.group(1))
        if d:
            return d
    m = re.search(r"<iframe[^>]+src=[\"']([^\"']+)[\"']", h, re.I)
    if m:
        return m.group(1)
    for mm in re.finditer(r"\"url\"\s*:\s*\"([^\"]+)\"", h, re.I):
        raw_url = mm.group(1).replace("\\/", "/").replace("\\", "")
        if _STREAM_RE.search(raw_url) and raw_url.startswith("http"):
            return raw_url
    return ""


def _episode_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.siteUrl = DEFAULT_HOST
        self._validator_cookie = ""

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
        host = host.strip()
        if host and host.startswith("http"):
            self.siteUrl = host.rstrip("/")
        return self.siteUrl

    def getName(self):
        return "66在线"

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        return (".m3u8" in low) or (".mp4" in low) or (".flv" in low) or (".mpd" in low)

    def manualVideoCheck(self):
        return False

    def _base(self):
        return self.siteUrl + "/" + SUB

    def _fetch_once(self, url, headers):
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        if resp is not None and resp.content:
            return resp.content.decode("utf-8", "replace")
        return ""

    def _fetch(self, url, referer=None, accept_all=False):
        if not url:
            return ""
        headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": referer or (self.siteUrl + "/"),
            "Accept": "*/*" if accept_all else "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if self._validator_cookie:
            headers["Cookie"] = self._validator_cookie
        text = ""
        try:
            text = self._fetch_once(url, headers)
        except Exception:
            if url.startswith("https://"):
                fallback_url = "http://" + url[len("https://"):]
                try:
                    text = self._fetch_once(fallback_url, headers)
                except Exception:
                    text = ""
        if text and "location.reload" in text:
            vm = _VALIDATOR_RE.search(text)
            if vm:
                pair = vm.group(1).strip()
                if pair and pair != self._validator_cookie:
                    self._validator_cookie = pair
                    retry_headers = dict(headers)
                    retry_headers["Cookie"] = pair
                    try:
                        text2 = self._fetch_once(url, retry_headers)
                        if text2:
                            text = text2
                    except Exception:
                        pass
        return _unwrap_html(text) if text else ""

    def _page_form(self, page, cards, limit):
        n = len(cards)
        if n == 0:
            return {"page": page, "pagecount": page, "limit": 1, "total": 0, "list": []}
        return {"page": page, "pagecount": page + 1, "limit": limit, "total": (page + 1) * limit, "list": cards}

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        first_tid = CATEGORIES[0][0] if CATEGORIES else "1"
        html = self._fetch(self._base() + "/index.php/vod/type/id/" + first_tid + ".html", self.siteUrl + "/")
        return {"list": [_public_card(c) for c in _parse_cards(html, self.siteUrl)]}

    def categoryContent(self, tid, pg, filter, extend):
        category_id = str(tid or "").strip() or "1"
        page = self._to_page(pg)
        if page <= 1:
            target_url = self._base() + "/index.php/vod/type/id/" + category_id + ".html"
        else:
            target_url = self._base() + "/index.php/vod/type/id/" + category_id + "/page/" + str(page) + ".html"
        html = self._fetch(target_url, self.siteUrl + "/")
        result = self._page_form(page, [_public_card(c) for c in _parse_cards(html, self.siteUrl)], PAGE_SIZE)
        result["type_id"] = category_id
        return result

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = self._to_page(pg)
        if not keyword:
            return {"page": page, "pagecount": page, "limit": 1, "total": 0, "list": []}
        kw = quote(keyword, safe="!*'()")
        if page <= 1:
            target_url = self._base() + "/index.php/vod/search/wd/" + kw + ".html"
        else:
            target_url = self._base() + "/index.php/vod/search/wd/" + kw + "/page/" + str(page) + ".html"
        html = self._fetch(target_url, self.siteUrl + "/")
        return self._page_form(page, [_public_card(c) for c in _parse_cards(html, self.siteUrl)], SEARCH_SIZE)

    def _brand_block(self):
        lines = [
            "🦋 66在线官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.siteUrl,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _play_entry(self, vid):
        return self._base() + "/index.php/vod/play/id/" + vid + "/sid/1/nid/1.html"

    def detailContent(self, ids):
        if isinstance(ids, (list, tuple)):
            raw = str(ids[0]) if ids else ""
        else:
            raw = str(ids or "")
        raw = raw.strip()
        parts = raw.split("@@")
        vid = parts[0].strip()
        pic = unquote(parts[1]) if len(parts) > 1 else ""
        if not vid:
            return {"list": [], "msg": "缺少作品 ID"}
        play_entry = self._play_entry(vid)
        h = self._fetch(play_entry, self.siteUrl + "/")
        name = ""
        tm = re.search(r"<title>([^<]+)</title>", h, re.I)
        if tm:
            seg = tm.group(1).split("在线播放")[0].split("-")[0].split("_")[0].strip()
            name = _unescape_html(seg)
        if not name:
            name = "视频 " + vid
        episodes = []
        seen_url = set()
        for pm in _PLAY_ANCHOR_RE.finditer(h):
            n = _unescape_html(pm.group(2).strip())
            full = _base_abs(pm.group(1), self.siteUrl)
            if not n or full in seen_url:
                continue
            pos = h.find(pm.group(1))
            if pos >= 0 and "thumbnail" in h[max(0, pos - 200):pos]:
                continue
            seen_url.add(full)
            episodes.append((n, full))
        if not episodes:
            episodes = [("超清正片", play_entry)]
        main_eps = []
        for ep_name, ep_url in episodes:
            env = {"playUrl": ep_url}
            main_eps.append(_episode_name(ep_name) + "$" + json.dumps(env, ensure_ascii=False))
        play_from = [LINE_NAME]
        play_url_lines = ["#".join(main_eps)]
        rel_idx = h.find("猜你喜欢")
        if rel_idx >= 0:
            related = []
            for card in _parse_cards(h[rel_idx:], self.siteUrl):
                if card["_vid"] != vid:
                    related.append(card)
            if related:
                play_from.append(RELATED_LINE)
                rel_eps = []
                for card in related:
                    rel_eps.append(_episode_name(card["vod_name"]) + "$" + "rel:" + card["_vid"])
                play_url_lines.append("#".join(rel_eps))
        vod = {
            "vod_id": raw,
            "vod_name": name,
            "vod_pic": pic,
            "vod_bg": pic,
            "vod_background": pic,
            "vod_banner": pic,
            "vod_actor": BRAND_ACTOR,
            "vod_remarks": DETAIL_REMARKS,
            "vod_content": self._brand_block() + "\n" + SUMMARY_BODY,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url_lines),
        }
        return {"list": [vod]}

    def _resolve_mac(self, page_url):
        headers = {"User-Agent": DEFAULT_UA, "Referer": page_url}
        html = self._fetch(page_url, page_url)
        url = _extract_mac_play_url(html)
        if url:
            if url.startswith("/"):
                url = _abs_url(url, self.siteUrl)
            if not _STREAM_RE.search(url):
                share_text = self._fetch(url, page_url, accept_all=True)
                dm = re.search(r"url\s*:\s*[\"']([^\"']+\.m3u8[^\"']*)[\"']", share_text, re.I) or re.search(r"[\"'](https?://[^\"']+\.m3u8[^\"']*)[\"']", share_text, re.I)
                if dm:
                    url = dm.group(1).replace("\\/", "/")
            if _STREAM_RE.search(url):
                return {"parse": 0, "jx": 0, "url": url, "header": headers}
            return {"parse": 1, "jx": 0, "url": url, "header": headers}
        return {"parse": 1, "jx": 0, "url": page_url, "header": headers}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("rel:"):
            target_vid = raw[len("rel:"):].strip()
            if not target_vid:
                return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
            return self._resolve_mac(self._play_entry(target_vid))
        page_url = ""
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if isinstance(obj, dict):
                page_url = str(obj.get("playUrl") or "").strip()
        elif raw.startswith("http"):
            page_url = raw
        if not page_url:
            return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放地址"}
        return self._resolve_mac(page_url)

    def liveContent(self, url):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Not Found"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249332083&sig=505c8ea913d000a3
