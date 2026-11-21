#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://www.xvideos.com"
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
BRAND = "蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
PAGE_SIZE = 27
POSTER_RATIO = 1.78
TIMEOUT = 8

CHANNELS = [
    ("new", "最新"),
    ("Fisting-165", "拳交"),
    ("Stockings-28", "丝袜"),
    ("Cam_Porn-58", "摄像头直播"),
    ("Oiled-22", "抹油"),
    ("Gapes-167", "扩张"),
    ("ASMR-229", "ASMR"),
    ("Indian-89", "印度"),
    ("Lingerie-83", "内衣"),
    ("Femdom-235", "女主调教"),
    ("Brunette-25", "褐发"),
    ("Arab-159", "阿拉伯"),
    ("Redhead-31", "红发"),
    ("Ass-14", "美臀"),
    ("Interracial-27", "跨种族"),
    ("Cumshot-18", "射精"),
    ("Solo_and_Masturbation-33", "单人自慰"),
    ("Bi_Sexual-62", "双性恋"),
    ("Blonde-20", "金发"),
    ("Squirting-56", "潮吹"),
    ("Blowjob-15", "口交"),
    ("Gangbang-69", "群交"),
    ("Latina-16", "拉丁裔"),
    ("Big_Cock-34", "大屌"),
    ("bbw-51", "丰满大码"),
    ("Creampie-40", "内射"),
    ("Mature-38", "熟女"),
    ("Cuckold-237", "绿帽"),
    ("Teen-13", "青春少女 (18+)"),
    ("Big_Ass-24", "大屁股"),
    ("Asian_Woman-32", "亚洲女优"),
    ("Milf-19", "熟妇"),
    ("Big_Tits-23", "大胸"),
    ("AI-239", "AI"),
    ("Anal-12", "肛交"),
    ("Black_Woman-30", "黑人"),
    ("Lesbian-26", "女同"),
    ("Amateur-65", "业余自拍"),
    ("Fucked_Up_Family-81", "家庭乱伦"),
]

NAMED_ENTITIES = {
    "eacute": "é", "egrave": "è", "ecirc": "ê", "euml": "ë",
    "agrave": "à", "aacute": "á", "acirc": "â", "atilde": "ã", "auml": "ä",
    "ccedil": "ç", "ntilde": "ñ",
    "oacute": "ó", "ograve": "ò", "ocirc": "ô", "otilde": "õ", "ouml": "ö",
    "uacute": "ú", "ugrave": "ù", "ucirc": "û", "uuml": "ü",
    "iacute": "í", "icirc": "î", "igrave": "ì", "iuml": "ï",
    "yacute": "ý", "yuml": "ÿ", "szlig": "ß",
    "hellip": "…", "rsquo": "’", "lsquo": "‘", "rdquo": "”", "ldquo": "“",
    "mdash": "—", "ndash": "–", "nbsp": " ", "copy": "©", "reg": "®", "trade": "™",
    "times": "×", "divide": "÷", "plusmn": "±", "deg": "°", "micro": "µ",
    "laquo": "«", "raquo": "»", "iexcl": "¡", "iquest": "¿",
    "cent": "¢", "pound": "£", "yen": "¥", "bull": "•", "dagger": "†", "Dagger": "‡",
    "permil": "‰", "oelig": "œ", "OElig": "Œ", "scaron": "š", "Scaron": "Š",
    "fnof": "ƒ", "circ": "ˆ", "tilde": "˜", "sup2": "²", "sup3": "³",
    "frac12": "½", "frac14": "¼", "frac34": "¾",
}


def _decode_entities(s):
    out = str(s or "")

    def _hex(m):
        try:
            v = int(m.group(1), 16)
            return chr(v) if v <= 0x10FFFF else m.group(0)
        except Exception:
            return m.group(0)

    def _dec(m):
        try:
            v = int(m.group(1), 10)
            return chr(v) if v <= 0x10FFFF else m.group(0)
        except Exception:
            return m.group(0)

    def _named(m):
        name = m.group(1)
        if name == "amp":
            return m.group(0)
        return NAMED_ENTITIES.get(name, m.group(0))

    out = re.sub(r"&#x([0-9a-fA-F]+);", _hex, out)
    out = re.sub(r"&#(\d+);", _dec, out)
    out = re.sub(r"&([a-zA-Z]+);", _named, out)
    out = out.replace("&amp;", "&")
    out = out.replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
    return out


def _json_unquote(raw):
    try:
        return json.loads('"' + raw + '"')
    except Exception:
        return raw


def _abs_url(raw, host):
    u = _decode_entities(str(raw or "").strip())
    if not u:
        return ""
    if u.startswith("//"):
        u = "https:" + u
    if u.startswith("/"):
        u = host + u
    if not u.startswith("http"):
        u = "https://" + u
    return u


def _abs_poster(raw, host):
    u = _decode_entities(str(raw or "").strip())
    if not u:
        return ""
    if u.startswith("http://"):
        u = "https://" + u[7:]
    return _abs_url(u, host)


def _divider(n):
    return "━" * n


def _title_page_mismatch(html, page):
    tm = re.search(r"<title>([^<]*)</title>", str(html or ""), re.I)
    if not tm or not tm.group(1):
        return False
    pm = re.search(r", page (\d+)", tm.group(1))
    if not pm or not pm.group(1):
        return False
    return int(pm.group(1)) != page


def _parse_iso_duration(s):
    m = re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", str(s or ""))
    if not m:
        return 0
    h = int(m.group(1)) if m.group(1) else 0
    mi = int(m.group(2)) if m.group(2) else 0
    sec = float(m.group(3)) if m.group(3) else 0
    return int(h * 3600 + mi * 60 + sec + 0.5)


def _fmt_duration(total):
    total = max(0, int(total or 0))
    h = total // 3600
    mi = (total % 3600) // 60
    sec = total % 60
    mm = str(h * 60 + mi) if h > 0 else str(mi)
    ss = ("0" + str(sec)) if sec < 10 else str(sec)
    return mm + ":" + ss


def _extract_ld_json(html):
    out = {"name": "", "duration": "", "thumbnailUrl": "", "uploadDate": "", "description": ""}
    m = re.search(r'<script[^>]*type="application/ld\+json"[^>]*>([\s\S]*?)</script>', str(html or ""))
    if not m or not m.group(1):
        return out
    block = m.group(1)
    nm = re.search(r'"name":\s*"((?:[^"\\]|\\.)*)"', block)
    if nm and nm.group(1):
        out["name"] = _json_unquote(nm.group(1))
    dm = re.search(r'"duration":\s*"([^"]+)"', block)
    if dm and dm.group(1):
        out["duration"] = dm.group(1)
    th = re.search(r'"thumbnailUrl":\s*"([^"]+)"', block)
    if th and th.group(1):
        out["thumbnailUrl"] = _json_unquote(th.group(1))
    um = re.search(r'"uploadDate":\s*"([^"]+)"', block)
    if um and um.group(1):
        out["uploadDate"] = um.group(1)
    ds = re.search(r'"description":\s*"((?:[^"\\]|\\.)*)"', block)
    if ds and ds.group(1):
        out["description"] = _json_unquote(ds.group(1))
    return out


def _extract_models(html):
    out = []
    for m in re.finditer(r'<li class="model">[\s\S]*?<span class="name">([^<]+)</span>', str(html or "")):
        name = _decode_entities(m.group(1)).strip()
        if name and name not in out:
            out.append(name)
    return out


def _extract_keywords(html):
    out = []
    for m in re.finditer(r'<a[^>]*class="[^"]*is-keyword[^"]*"[^>]*>([^<]+)</a>', str(html or "")):
        kw = _decode_entities(m.group(1)).strip()
        if kw and kw not in out:
            out.append(kw)
    return out


def _extract_related(html, host):
    text = str(html or "")
    idx = text.find("var video_related=[")
    if idx == -1:
        return []
    open_idx = text.find("[", idx)
    if open_idx == -1:
        return []
    depth = 0
    in_str = False
    esc = False
    i = open_idx
    closed = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    closed = True
                    break
        i += 1
    if not closed:
        return _extract_related_fallback(text, host)
    arr = None
    try:
        arr = json.loads(text[open_idx:i + 1])
    except Exception:
        arr = None
    if arr:
        out = []
        for a in arr:
            if not isinstance(a, dict) or not a.get("eid") or not a.get("u"):
                continue
            title = ""
            if a.get("tf"):
                title = str(a["tf"])
            elif a.get("t"):
                title = str(a["t"])
            title = _decode_entities(title).strip()
            if not title:
                title = str(a["eid"])
            out.append({
                "eid": str(a["eid"]),
                "url": _abs_url(str(a["u"]), host),
                "poster": _abs_poster(str(a["i"]), host) if a.get("i") else "",
                "title": title,
                "dur": str(a["d"]) if a.get("d") else "",
            })
        return out
    return _extract_related_fallback(text, host)


def _extract_related_fallback(text, host):
    out = []
    seen = set()
    for m in re.finditer(r'"eid":"([a-z0-9]+)"', text):
        eid = m.group(1)
        if eid in seen:
            continue
        chunk = text[m.start():m.start() + 2500]
        um = re.search(r'"u":"((?:[^"\\]|\\.)*)"', chunk)
        if not um or not um.group(1):
            continue
        title = ""
        fm = re.search(r'"tf":"((?:[^"\\]|\\.)*)"', chunk)
        if fm and fm.group(1):
            title = _json_unquote(fm.group(1))
        else:
            tm = re.search(r'"t":"((?:[^"\\]|\\.)*)"', chunk)
            if tm and tm.group(1):
                title = _json_unquote(tm.group(1))
        title = _decode_entities(title).strip() or eid
        dm = re.search(r'"d":"([^"]*)"', chunk)
        im = re.search(r'"i":"((?:[^"\\]|\\.)*)"', chunk)
        seen.add(eid)
        out.append({
            "eid": eid,
            "url": _abs_url(_json_unquote(um.group(1)), host),
            "poster": _abs_poster(_json_unquote(im.group(1)), host) if (im and im.group(1)) else "",
            "title": title,
            "dur": dm.group(1) if (dm and dm.group(1)) else "",
        })
    return out


def _parse_list_cards(html, host):
    items = []
    seen = set()
    opens = []
    for m in re.finditer(r'<div id="video_([a-z0-9]+)"[^>]*data-id="(\d+)"[^>]*>', str(html or "")):
        opens.append((m.group(1), m.group(2), m.start(), m.end()))
    for i in range(len(opens)):
        eid, num_id, start, end = opens[i]
        chunk_end = opens[i + 1][2] if i + 1 < len(opens) else min(len(html), end + 4000)
        chunk = html[end:chunk_end]
        if eid in seen:
            continue
        hm = re.search(r'<a href="(\/video\.[^"]+)"', chunk)
        if not hm or not hm.group(1):
            continue
        pm = re.search(r'data-src="([^"]+)"', chunk)
        if not pm or not pm.group(1):
            continue
        poster = _abs_poster(pm.group(1), host)
        if not poster:
            continue
        title = eid
        tm = re.search(r'<p class="title"><a[^>]*title="([^"]*)"', chunk)
        if tm and tm.group(1):
            title = _decode_entities(tm.group(1)).strip()
        if not title:
            title = eid
        dur = ""
        dm = re.search(r'<span class="duration">([^<]+)</span>', chunk)
        if dm and dm.group(1):
            dur = dm.group(1).strip()
        seen.add(eid)
        url = host + hm.group(1)
        items.append({
            "vod_id": "%s@@%s@@%s" % (num_id, quote(url, safe=""), eid),
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": (BRAND + " | " + dur) if dur else BRAND,
            "style": {"type": "rect", "ratio": POSTER_RATIO},
        })
    return items


def _clean_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        super(Spider, self).__init__()
        self.siteUrl = DEFAULT_HOST

    def init(self, extend=""):
        opts = {}
        if isinstance(extend, dict):
            opts = extend
        elif isinstance(extend, str) and extend.strip():
            try:
                parsed = json.loads(extend)
                if isinstance(parsed, dict):
                    opts = parsed
            except Exception:
                opts = {}
        host = opts.get("host")
        if isinstance(host, str) and host.strip().startswith("http"):
            self.siteUrl = host.strip().rstrip("/")
        return True

    def getName(self):
        return "XVideos"

    def _fetch(self, url, referer=""):
        headers = {"User-Agent": DEFAULT_UA, "Referer": referer or (self.siteUrl + "/")}
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        except requests.RequestException:
            return 0, ""
        try:
            text = resp.content.decode("utf-8", "ignore")
        except Exception:
            text = ""
        return resp.status_code, text

    def _brand_block(self):
        return "\n".join([
            "🦋 XVideos官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.siteUrl,
            _divider(28),
            _divider(7),
        ])

    def _page_result(self, cards, page):
        if not cards:
            return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": 0}
        return {"list": cards, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": name} for cid, name in CHANNELS]
        return {"class": classes}

    def homeVideoContent(self):
        status, html = self._fetch(self.siteUrl + "/", self.siteUrl + "/")
        if status != 200:
            return {"list": []}
        return {"list": _parse_list_cards(html, self.siteUrl)}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        cid = str(tid).strip() if tid is not None else ""
        if not cid:
            cid = "new"
        if cid == "new":
            url = (self.siteUrl + "/") if page == 1 else (self.siteUrl + "/new/" + str(page - 1))
        elif page == 1:
            url = self.siteUrl + "/c/" + cid
        else:
            url = self.siteUrl + "/c/" + cid + "/" + str(page - 1)
        status, html = self._fetch(url, self.siteUrl + "/")
        if status != 200:
            return self._page_result([], page)
        if _title_page_mismatch(html, page):
            return self._page_result([], page)
        return self._page_result(_parse_list_cards(html, self.siteUrl), page)

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_result([], page)
        url = self.siteUrl + "/?k=" + quote(keyword, safe="-_.!~*'()") + "&p=" + str(page)
        status, html = self._fetch(url, self.siteUrl + "/")
        if status != 200:
            return self._page_result([], page)
        if _title_page_mismatch(html, page):
            return self._page_result([], page)
        return self._page_result(_parse_list_cards(html, self.siteUrl), page)

    def _not_found(self, note):
        return {"list": [], "msg": note}

    def detailContent(self, ids):
        if isinstance(ids, (list, tuple)):
            raw = str(ids[0]) if ids else ""
        else:
            raw = str(ids or "")
        item_id = raw
        detail_url = ""
        eid_hint = ""
        if "@@" in raw:
            parts = raw.split("@@")
            item_id = parts[0]
            if len(parts) > 1:
                detail_url = unquote(parts[1])
            if len(parts) > 2:
                eid_hint = parts[2]
        if detail_url.startswith("/"):
            detail_url = self.siteUrl + detail_url
        if not detail_url:
            return self._not_found("未找到该影片")
        status, html = self._fetch(detail_url, self.siteUrl + "/")
        if status != 200 or not html:
            return self._not_found("未找到该影片")
        ld = _extract_ld_json(html)
        title = ld["name"] or ""
        if not title:
            om = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', html, re.I)
            if not om:
                om = re.search(r'<meta[^>]+content="([^"]*)"[^>]+property="og:title"', html, re.I)
            if om and om.group(1):
                title = _decode_entities(om.group(1))
        if not title:
            sm = re.search(r"html5player\.setVideoTitle\('((?:[^'\\]|\\.)*)'\)", html)
            if sm and sm.group(1):
                title = sm.group(1).replace("\\'", "'")
        if not title:
            title = item_id
        poster = ""
        im = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html, re.I)
        if not im:
            im = re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', html, re.I)
        if im and im.group(1):
            poster = _abs_poster(im.group(1), self.siteUrl)
        if not poster and ld["thumbnailUrl"]:
            poster = _abs_poster(ld["thumbnailUrl"], self.siteUrl)
        has_hls = re.search(r"html5player\.setVideoHLS\('([^']+)'\)", html) is not None
        has_high = re.search(r"html5player\.setVideoUrlHigh\('([^']+)'\)", html) is not None
        has_low = re.search(r"html5player\.setVideoUrlLow\('([^']+)'\)", html) is not None
        models = _extract_models(html)
        if models:
            actor = ", ".join(models + ["🦋 TG群: @tvshare23"])
        else:
            actor = "🦋 TG群: @tvshare23"
        tags = _extract_keywords(html)
        year = ld["uploadDate"][:4] if len(ld["uploadDate"]) >= 4 else ""
        dur_sec = _parse_iso_duration(ld["duration"])
        dur_text = _fmt_duration(dur_sec) if dur_sec > 0 else ""
        related = _extract_related(html, self.siteUrl)
        body = ld["description"] or ""
        if not body:
            rel_titles = [r["title"] for r in related[:6]]
            body = "\n".join([
                "标题：" + title,
                "分类：",
                "上传：" + (ld["uploadDate"][:10] if ld["uploadDate"] else "未知"),
                "时长：" + (dur_text if dur_text else "未知"),
                "片源：" + LINE_NAME,
                "编号：" + item_id,
                "标签：" + (" / ".join(tags[:8]) if tags else "无"),
                "相关推荐：" + (" / ".join(rel_titles) if rel_titles else "无"),
            ])
        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_year": year,
            "vod_class": ",".join(tags),
            "vod_actor": actor,
            "vod_director": "🦋 蝴蝶影视",
            "vod_remarks": (BRAND + " | " + dur_text) if dur_text else BRAND,
            "vod_play_from": LINE_NAME,
            "style": {"type": "rect", "ratio": POSTER_RATIO},
        }
        if not has_hls and not has_high and not has_low:
            if "XV PREMIUM" in html:
                note = "该视频为 Premium 付费内容，暂无免费播放直链"
            else:
                note = "未找到可播放片源"
            vod["vod_content"] = self._brand_block() + "\n" + body + "\n" + note
            notice_ref = {"notice": note}
            vod["vod_play_url"] = _clean_ep_name("暂无播放源") + "$" + json.dumps(notice_ref, ensure_ascii=False)
            return {"list": [vod]}
        eid = eid_hint
        if not eid:
            em = re.search(r"/video\.([a-z0-9]+)/", detail_url)
            if em and em.group(1):
                eid = em.group(1)
        episodes = []
        main_ref = {"eid": eid, "url": detail_url}
        episodes.append(_clean_ep_name("正片") + "$" + json.dumps(main_ref, ensure_ascii=False))
        for r in related:
            ref = {"eid": r["eid"], "url": r["url"]}
            episodes.append(_clean_ep_name(r["title"]) + "$" + json.dumps(ref, ensure_ascii=False))
        vod["vod_content"] = self._brand_block() + "\n" + body
        vod["vod_play_url"] = "#".join(episodes)
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        ref = {}
        try:
            parsed = json.loads(str(id))
            if isinstance(parsed, dict):
                ref = parsed
        except Exception:
            ref = {}
        if ref.get("notice"):
            return {"parse": 0, "msg": str(ref["notice"])}
        detail_url = ""
        if ref.get("url"):
            detail_url = str(ref["url"])
            if detail_url.startswith("/"):
                detail_url = self.siteUrl + detail_url
        if not detail_url:
            return {"parse": 0, "msg": "缺少播放标识"}
        status, html = self._fetch(detail_url, self.siteUrl + "/")
        if status != 200 or not html:
            if status:
                return {"parse": 0, "msg": "请求失败：HTTP %d" % status}
            return {"parse": 0, "msg": "请求失败"}
        header = {"User-Agent": DEFAULT_UA, "Referer": detail_url}
        hm = re.search(r"html5player\.setVideoHLS\('([^']+)'\)", html)
        if hm and hm.group(1):
            return {"parse": 0, "url": hm.group(1), "header": header}
        hi = re.search(r"html5player\.setVideoUrlHigh\('([^']+)'\)", html)
        if hi and hi.group(1):
            return {"parse": 0, "url": hi.group(1), "header": header}
        lo = re.search(r"html5player\.setVideoUrlLow\('([^']+)'\)", html)
        if lo and lo.group(1):
            return {"parse": 0, "url": lo.group(1), "header": header}
        return {"parse": 0, "msg": "未能提取到播放地址"}

    def liveContent(self, url=""):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250229245&sig=78738e73424de912
