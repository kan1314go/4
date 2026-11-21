# -*- coding: utf-8 -*-
# BB影速播18.py - FongMi/TVBox python spider, converted from Hamo JS plugin com.butterfly.bbysb (BB影速播.js)

import json
import re
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://evs.bbysb.pics"
DEFAULT_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
BRAND = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
LINE_NAME = "🦋 蝴蝶专线"
RELATED_LINE = "相关推荐"
TIMEOUT = 8
PAGE_SIZE = 24
DETAIL_FAIL_TEXT = "缺少作品 ID"

STATIC_CLASSES = [
    ("20", "国产一区"), ("21", "学生少女"), ("22", "技师风采"), ("23", "熟女少妇"),
    ("24", "国产热播"), ("25", "反差母狗"), ("26", "美脚丝足"), ("27", "情侣自拍"),
    ("28", "偷情约炮"), ("29", "真实偷拍"), ("30", "高潮喷水"), ("31", "国产二区"),
    ("32", "强奸迷奸"), ("33", "户外露出"), ("34", "SM调教"), ("35", "情趣内衣"),
    ("36", "精选探花"), ("37", "黑料曝光"), ("38", "网曝门事件"), ("39", "校园猛料"),
    ("40", "网红流出"), ("41", "明星黑料"), ("42", "裸贷肉偿"), ("43", "婚闹恶俗"),
    ("44", "抓奸名场面"), ("45", "男同女同"), ("46", "制服诱惑"), ("47", "JK少女"),
    ("48", "黑丝白丝"), ("49", "女仆"), ("50", "cosplay"), ("51", "OL制服"),
    ("52", "旗袍"), ("53", "空姐制服"), ("54", "护士医生"), ("55", "伦理之爱"),
    ("56", "禁忌母子"), ("57", "兄弟姐妹"), ("58", "爱上嫂子"), ("59", "狂操阿姨"),
    ("60", "换夫换妻"), ("61", "淫荡儿媳"), ("62", "爷爷奶奶"), ("63", "直播"),
    ("64", "啪啪直播"), ("65", "学生直播"), ("66", "自慰诱惑"), ("67", "乱伦直播"),
    ("68", "户外勾搭"), ("69", "车震直播"), ("70", "国产AV"), ("71", "欧美"),
    ("72", "欧美精选"), ("73", "户外搭讪"), ("74", "美女自慰"), ("75", "成人剧情"),
    ("76", "黑人大屌"), ("77", "群P大作战"), ("78", "欧美重口"), ("79", "重口猎奇"),
    ("80", "人兽性交"), ("81", "SM性虐"), ("82", "人妖伪娘"), ("83", "孕妇内射"),
    ("84", "吃屎喝尿"), ("85", "扩阴拳交"), ("86", "阳具巨物"), ("87", "动漫"),
    ("88", "3D动漫"), ("89", "同人动漫"), ("90", "日本"), ("91", "日本中文"),
    ("92", "无码流出"), ("93", "FC2"), ("94", "HEYZO"), ("95", "东京热"),
    ("96", "一本道"), ("97", "人妻斩"), ("98", "网红主播"), ("99", "乱伦精选"),
    ("100", "剧情故事"), ("101", "韩国"), ("102", "主播网黄"), ("103", "色情综艺"),
    ("104", "情色AV"), ("105", "伦理精选"), ("106", "私房俱乐部"), ("107", "国产动漫"),
    ("108", "日韩动漫"), ("109", "欧美动漫"), ("110", "港台动漫"), ("111", "海外动漫"),
]

SORT_ROW = {
    "key": "by",
    "name": "排序",
    "init": "",
    "value": [
        {"n": "默认", "v": ""},
        {"n": "按时间", "v": "time"},
        {"n": "按观看", "v": "time_hits"},
        {"n": "按点赞", "v": "up"},
        {"n": "按热度", "v": "hits"},
    ],
}

_CARD_PAT = re.compile(r'href=["\'](/index\.php/vod/play/id/([0-9]+)/sid/[0-9]+/nid/[0-9]+\.html)["\']', re.I)
_CARD_IMG_PAT = re.compile(r'<img[^>]+(?:src|data-src|data-original)=["\']([^"\']+)["\']', re.I)
_CARD_TITLE_PAT = re.compile(r'title=["\']([^"\']+)["\']', re.I)
_CARD_DUR_PAT = re.compile(r'<span[^>]*class=["\'][^"\']*duration[^"\']*["\'][^>]*>([^<]+)</span>', re.I)
_CARD_QUAL_PAT = re.compile(r'<span[^>]*class=["\'][^"\']*quality[^"\']*["\'][^>]*>([^<]+)</span>', re.I)
_CARD_GLOBAL_PAT = re.compile(r'<a[^>]+href=["\'](/index\.php/vod/(?:play/id/([0-9]+)/sid/[0-9]+/nid/[0-9]+|detail/id/([0-9]+))\.html)["\'][^>]*>([\s\S]*?)</a>', re.I)
_M3U8_PAT = re.compile(r'https?://[^\s"\'<>\\`]+?\.m3u8(?:[^\s"\'<>\\`]*)?', re.I)
_SNIFF_VARS = ("player_aaaa", "player_data", "MacPlayer", "urlplay")


def _clean_text(value):
    if not value:
        return ""
    s = str(value)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("&amp;", "&")
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&quot;", '"')
    s = s.replace("&#39;", "'")
    s = s.replace("&nbsp;", " ")
    s = re.sub(r"[\r\n\t]+", " ", s)
    return s.strip()


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


def _format_poster(raw_url, host):
    if not raw_url:
        return ""
    u = str(raw_url).strip().replace("&amp;", "&")
    if u.startswith("//"):
        u = "https:" + u
    elif u.startswith("/"):
        u = host + u
    elif not u.startswith("http"):
        u = host + "/" + u
    return u


def _format_remarks(brand, meta):
    clean_meta = _clean_text(meta)
    if clean_meta:
        return brand + " | " + clean_meta
    return brand


def _sniff_media(html):
    if not html:
        return ""
    for var_name in _SNIFF_VARS:
        reg = re.compile(r"(?:var|let|const)?[ ]*" + var_name + r"[ ]*=[ ]*(\{[\s\S]*?\});", re.I)
        m = reg.search(html)
        if m and m.group(1):
            try:
                clean_json = m.group(1).replace("\\/", "/")
                clean_json = re.sub(r",[ ]*([\}\]])", r"\1", clean_json)
                obj = json.loads(clean_json)
            except Exception:
                obj = None
            if obj:
                target = obj.get("url") or obj.get("src") or obj.get("link") or obj.get("play_url")
                if target and isinstance(target, str):
                    return target.replace("\\/", "/").replace("&amp;", "&").strip()
    m3u8_match = _M3U8_PAT.search(html)
    if m3u8_match:
        return m3u8_match.group(0).replace("\\/", "/").replace("&amp;", "&").strip()
    return ""


def _episode_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.siteUrl = DEFAULT_HOST

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
        return "BB影速播"

    def _fetch(self, url):
        if not url:
            return ""
        headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": self.siteUrl + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            text = resp.content.decode("utf-8", "replace") if resp.content else ""
            if text:
                return _unwrap_html(text)
        except Exception:
            if url.startswith("https://"):
                fallback_url = "http://" + url[8:]
                try:
                    resp2 = requests.get(fallback_url, headers=headers, timeout=TIMEOUT)
                    text2 = resp2.content.decode("utf-8", "replace") if resp2.content else ""
                    if text2:
                        return _unwrap_html(text2)
                except Exception:
                    pass
        return ""

    def _parse_cards(self, html):
        cards = []
        seen = set()
        if not html:
            return cards
        blocks = html.split('class="thumb_block')
        if len(blocks) <= 1:
            blocks = html.split('class="item')
        if len(blocks) > 1:
            for block in blocks[1:]:
                m = _CARD_PAT.search(block)
                if not m:
                    continue
                vid = (m.group(2) or "").strip()
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                name = ""
                tm = _CARD_TITLE_PAT.search(block)
                if tm:
                    name = _clean_text(tm.group(1))
                if not name:
                    name = "视频 " + vid
                pic = ""
                im = _CARD_IMG_PAT.search(block)
                if im:
                    pic = im.group(1).strip()
                remarks_meta = ""
                dm = _CARD_DUR_PAT.search(block)
                if dm:
                    remarks_meta = _clean_text(dm.group(1))
                if not remarks_meta:
                    qm = _CARD_QUAL_PAT.search(block)
                    if qm:
                        remarks_meta = _clean_text(qm.group(1))
                cards.append({
                    "vod_id": vid,
                    "vod_name": name,
                    "vod_pic": _format_poster(pic, self.siteUrl),
                    "vod_remarks": _format_remarks(BRAND, remarks_meta),
                })
        if not cards:
            for gm in _CARD_GLOBAL_PAT.finditer(html):
                gvid = gm.group(2) or gm.group(3)
                if not gvid or gvid in seen:
                    continue
                seen.add(gvid)
                chunk = gm.group(0)
                gtitle = ""
                gtm = _CARD_TITLE_PAT.search(chunk)
                if gtm:
                    gtitle = _clean_text(gtm.group(1))
                else:
                    ginner = _clean_text(gm.group(4))
                    if ginner and len(ginner) > 1:
                        gtitle = ginner
                if not gtitle:
                    gtitle = "视频 " + gvid
                gpic = ""
                gim = _CARD_IMG_PAT.search(chunk)
                if gim:
                    gpic = gim.group(1).strip()
                cards.append({
                    "vod_id": gvid,
                    "vod_name": gtitle,
                    "vod_pic": _format_poster(gpic, self.siteUrl),
                    "vod_remarks": BRAND,
                })
        return cards

    def _page_form(self, page, cards):
        n = len(cards)
        if n == 0:
            return {"page": page, "pagecount": page, "limit": 1, "total": 0, "list": []}
        return {"page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE, "list": cards}

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
        first_tid = STATIC_CLASSES[0][0] if STATIC_CLASSES else "20"
        html = self._fetch(self.siteUrl + "/index.php/vod/type/id/" + first_tid + ".html")
        items = self._parse_cards(html)
        if not items:
            raw_home = self._fetch(self.siteUrl + "/")
            items = self._parse_cards(raw_home)
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        category_id = str(tid or "").strip() or "20"
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        extend = extend or {}
        by = str(extend.get("by") or "").strip()
        if by:
            if page <= 1:
                target_url = self.siteUrl + "/index.php/vod/show/by/" + quote(by, safe="!*'()") + "/id/" + category_id + ".html"
            else:
                target_url = self.siteUrl + "/index.php/vod/show/by/" + quote(by, safe="!*'()") + "/id/" + category_id + "/page/" + str(page) + ".html"
        else:
            if page <= 1:
                target_url = self.siteUrl + "/index.php/vod/type/id/" + category_id + ".html"
            else:
                target_url = self.siteUrl + "/index.php/vod/type/id/" + category_id + "/page/" + str(page) + ".html"
        html = self._fetch(target_url)
        result = self._page_form(page, self._parse_cards(html))
        result["type_id"] = category_id
        return result

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        if not keyword:
            return {"page": page, "pagecount": page, "limit": 1, "total": 0, "list": []}
        search_url = self.siteUrl + "/index.php/vod/search.html?wd=" + quote(keyword, safe="!*'()")
        html = self._fetch(search_url)
        cards = self._parse_cards(html)
        if not cards:
            return {"page": page, "pagecount": page, "limit": 1, "total": 0, "list": []}
        return {"page": page, "pagecount": page, "limit": PAGE_SIZE, "total": len(cards), "list": cards}

    def _brand_block(self):
        lines = [
            "🦋 BB影速播官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.siteUrl,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _play_url(self, vid):
        return self.siteUrl + "/index.php/vod/play/id/" + vid + "/sid/1/nid/1.html"

    def detailContent(self, ids):
        if isinstance(ids, (list, tuple)):
            raw = str(ids[0]) if ids else ""
        else:
            raw = str(ids or "")
        vid = raw.strip()
        if not vid:
            return {"list": [], "msg": DETAIL_FAIL_TEXT}
        detail_urls = [
            self.siteUrl + "/index.php/vod/detail/id/" + vid + ".html",
            self._play_url(vid),
        ]
        html = ""
        for u in detail_urls:
            h = self._fetch(u)
            if h and len(h) > 500:
                html = h
                break
        title = ""
        pic = ""
        raw_desc = ""
        if html:
            t_match = (
                re.search(r'<h1[^>]*class=["\'][^"\']*(?:title|video-title)[^"\']*["\'][^>]*>([\s\S]*?)</h1>', html, re.I)
                or re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
                or re.search(r"<title>([^<]+)</title>", html, re.I)
            )
            if t_match:
                title = re.sub(r" - .+$", "", _clean_text(t_match.group(1))).strip()
            p_match = (
                re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
                or re.search(r'<img[^>]+class=["\'][^"\']*img_thumb[^"\']*["\'][^>]+src=["\']([^"\']+)["\']', html, re.I)
                or re.search(r'(?:data-original|data-src)=["\']([^"\']+)["\']', html, re.I)
            )
            if p_match:
                pic = _format_poster(p_match.group(1).strip(), self.siteUrl)
            d_match = (
                re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html, re.I)
                or re.search(r'<div[^>]*class=["\'][^"\']*(?:desc|content|intro)[^"\']*["\'][^>]*>([\s\S]*?)</div>', html, re.I)
            )
            if d_match:
                raw_desc = _clean_text(d_match.group(1))
        if not title:
            title = "BB影速播 · 视频 " + vid
        if raw_desc:
            body = "【影片简介】" + raw_desc
        else:
            body = "【极速高清播放】4K高清原生极速画质，蝴蝶专线加速支持。"
        content = self._brand_block() + "\n" + body
        direct = _sniff_media(html)
        playback_target = direct if direct else self._play_url(vid)
        main_episode = _episode_name("超清正片") + "$" + json.dumps({"playUrl": playback_target, "vodId": vid}, ensure_ascii=False)
        play_from = [LINE_NAME]
        play_url_lines = [main_episode]
        related = []
        for card in self._parse_cards(html):
            if card["vod_id"] != vid:
                related.append(card)
        if related:
            play_from.append(RELATED_LINE)
            rel_eps = []
            for card in related:
                rel_eps.append(_episode_name(card["vod_name"]) + "$" + "rel:" + card["vod_id"])
            play_url_lines.append("#".join(rel_eps))
        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": pic,
            "vod_bg": pic,
            "vod_background": pic,
            "vod_banner": pic,
            "vod_actor": BRAND_ACTOR,
            "vod_director": "🦋 蝴蝶影视",
            "vod_remarks": _format_remarks(BRAND, "正片"),
            "vod_content": content,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url_lines),
        }
        return {"list": [vod]}

    def _resolve_chain(self, target_url, vid):
        if not target_url and vid:
            target_url = self._play_url(vid)
        headers = {"User-Agent": DEFAULT_UA, "Referer": self.siteUrl + "/"}
        if ".m3u8" in target_url:
            return {"parse": 0, "jx": 0, "url": target_url, "header": headers}
        if ".mp4" in target_url:
            return {"parse": 0, "jx": 0, "url": target_url, "header": headers}
        play_html = self._fetch(target_url)
        direct = _sniff_media(play_html)
        if direct:
            return {"parse": 0, "jx": 0, "url": direct, "header": headers}
        return {"parse": 1, "jx": 0, "url": target_url, "header": headers}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("rel:"):
            target_vid = raw[4:].strip()
            if not target_vid:
                return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
            return self._resolve_chain("", target_vid)
        target_url = ""
        vid = ""
        if raw.startswith("{"):
            obj = None
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if isinstance(obj, dict):
                target_url = str(obj.get("playUrl") or "").strip()
                vid = str(obj.get("vodId") or "").strip()
            else:
                target_url = raw
        elif raw:
            target_url = raw
        return self._resolve_chain(target_url, vid)

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249984101&sig=8ff68bb41af84639
