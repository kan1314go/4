#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://moguds.cc"
DEFAULT_CDN_BASE = "https://dfdf.tjacq.com"
DEFAULT_CDN_FALLBACK = "https://d1uy7itup9paqh.cloudfront.net"
DEFAULT_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
BRAND = "蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
PAGE_SIZE = 20
POSTER_RATIO = 1.78
TIMEOUT = 8
NO_SOURCE_REASON = "未找到可播放片源"

ZONES = [
    ("zone_home", "🔥今日精选", "route_home", [
        ("今日推荐", "route_home"),
    ]),
    ("zone_media", "🎬传媒原创", "cate14", [
        ("素人自摄", "cate14"),
        ("麻豆热剧", "cate15"),
        ("糖心系列", "cate16"),
        ("果冻精选", "cate17"),
        ("天使映画", "cate18"),
        ("天美热作", "cate19"),
        ("星空夜欲", "cate20"),
        ("蜜桃诱惑", "cate21"),
    ]),
    ("zone_creator", "💃网黄达人", "cate24", [
        ("桥本香菜", "cate24"),
        ("小水水", "cate25"),
        ("刘玥", "cate26"),
        ("Ellie", "cate27"),
        ("米菲兔", "cate28"),
        ("辛尤里", "cate29"),
        ("唐伯虎", "cate30"),
        ("饼干姐姐", "cate31"),
        ("吴梦梦", "cate32"),
        ("台北娜娜", "cate33"),
        ("玩偶姐姐", "cate34"),
        ("柚子猫", "cate35"),
    ]),
    ("zone_asia", "🌸日韩精选", "cate38", [
        ("FC2 无码", "cate38"),
        ("淫妻母狗", "cate39"),
        ("中文字幕", "cate40"),
        ("素人AV", "cate41"),
        ("JK制服", "cate42"),
        ("口爆内射", "cate43"),
        ("师生乱欲", "cate44"),
        ("御姐足交", "cate45"),
        ("家庭禁忌", "cate46"),
    ]),
    ("zone_west", "🗽欧美洋马", "cate49", [
        ("欧美辣妹", "cate49"),
        ("欧美巨乳", "cate50"),
        ("欧美熟女", "cate51"),
        ("欧美SM", "cate52"),
        ("欧美足控", "cate53"),
        ("捷克木屋", "cate54"),
    ]),
    ("zone_anime", "🎀综合动漫", "cate57", [
        ("MMD-热舞系列", "cate57"),
        ("MMD-纯爱3D", "cate58"),
    ]),
    ("zone_sex_edu", "🎭性爱教学", "cate60", [
        ("王竹子SM教学", "cate60"),
        ("中指通一下", "cate61"),
        ("Misa米砂", "cate62"),
        ("小哥哥艾理", "cate63"),
        ("verzz 异物梗色", "cate64"),
        ("薇傲的性趣", "cate65"),
        ("一三蜜桃说", "cate66"),
        ("Carrie雨千", "cate67"),
    ]),
]

ZONE_MAP = dict((z[0], z) for z in ZONES)

_CARD_RE = re.compile(r"<a[^>]+href=[\"'](/video/\d+/?)[\"'][^>]*>([\s\S]*?)</a>", re.I)
_TITLE_RE = re.compile(r"(?:title=[\"']([^\"']+)[\"']|alt=[\"']([^\"']+)[\"']|<h\d[^>]*>([\s\S]*?)</h\d>)", re.I)
_DUR_RE = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)")
_M3U8_RE = re.compile(r"([^\s\"'>=]*?\.m3u8[^\s\"'<]*)", re.I)


def _encode_uri_component(s):
    return quote(str(s), safe="-_.!~*'()")


def _clean_text(s):
    if not s:
        return ""
    t = re.sub(r"<[^>]+>", "", str(s))
    t = t.replace("&amp;", "&")
    t = t.replace("&lt;", "<")
    t = t.replace("&gt;", ">")
    t = t.replace("&quot;", '"')
    t = re.sub(r"&#0?39;", "'", t)
    t = t.replace("&nbsp;", " ")
    t = re.sub(r"[\$#\r\n\t]+", " ", t)
    return t.strip()


def _format_remarks(meta):
    clean_meta = _clean_text(meta)
    if clean_meta:
        return BRAND + " | " + clean_meta
    return BRAND


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
    return t.replace('\\"', '"').replace("\\/", "/").replace("\\r\\n", "\n").replace("\\n", "\n")


def _normalize_url(u, host):
    if not u:
        return ""
    clean = str(u).strip().replace("\\u002F", "/").replace("\\/", "/")
    clean = re.sub(r"^(https?:)\/([^\/])", r"\1//\2", clean)
    if clean.startswith("//"):
        return "https:" + clean
    if clean.startswith("/"):
        return host + clean
    if clean.startswith("http"):
        return clean
    return host + "/" + clean


def _format_poster(raw_pic, host):
    if not raw_pic:
        return ""
    p = _normalize_url(raw_pic, host)
    if not p.startswith("http"):
        return p
    return p + "@Referer=" + _encode_uri_component(host + "/") + "&User-Agent=" + _encode_uri_component(DEFAULT_UA)


def _clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw).replace("\\u002F", "/").replace("\\/", "/").strip()
    m = re.search(r"https?:\/\/[^\s\"'$<>]+\.m3u8[^\s\"'$<>]*", clean, re.I)
    if m:
        return m.group(0)
    m = re.search(r"https?:\/\/[^\s\"'$<>]+\.mp4[^\s\"'$<>]*", clean, re.I)
    if m:
        return m.group(0)
    return clean


def _extract_clean_pic(inner):
    for attr in ("data-src", "data-original", "data-cover", "src"):
        m = re.search(attr + r"=[\"']([^\"']+)[\"']", inner, re.I)
        if m:
            cand = m.group(1).strip()
            low = cand.lower()
            bad = False
            for b in ("loading.jpg", "loading.png", "placeholder", "default"):
                if b in low:
                    bad = True
                    break
            if cand and not bad:
                if cand.startswith("/"):
                    return DEFAULT_CDN_BASE + cand
                return cand
    return ""


def _parse_cards(html, host):
    items = []
    seen = set()
    for m in _CARD_RE.finditer(str(html or "")):
        v_url = m.group(1).strip()
        inner = m.group(2)
        if v_url in seen:
            continue
        pic = _extract_clean_pic(inner)
        title = ""
        tm = _TITLE_RE.search(inner)
        if tm:
            title = _clean_text(tm.group(1) or tm.group(2) or tm.group(3) or "")
        if not title:
            for line in _clean_text(inner).split():
                if len(line) > 3:
                    title = line
                    break
        dur_m = _DUR_RE.search(inner)
        duration = dur_m.group(1) if dur_m else ""
        if v_url and (pic or title):
            seen.add(v_url)
            items.append({
                "vod_id": v_url,
                "vod_name": title or "蘑菇精彩视频",
                "vod_pic": _format_poster(pic, host) if pic else "",
                "vod_remarks": _format_remarks(duration),
                "style": {"type": "rect", "ratio": POSTER_RATIO},
            })
    return items


def _parse_cdn_lines(html):
    bases = []
    m = re.search(r"cdn_lines\s*=\s*'([^']+)'", str(html or ""), re.I)
    if not m:
        m = re.search(r"cdn_lines\s*=\s*(\[[^\]]+\])", str(html or ""), re.I)
    if m:
        try:
            arr = json.loads(m.group(1).replace("\\/", "/"))
            for it in arr:
                b = str((it or {}).get("cdnLine", "")).strip().rstrip("/")
                b = re.sub(r"^(https?:)\/([^\/])", r"\1//\2", b)
                if b.startswith("http") and b not in bases:
                    bases.append(b)
        except Exception:
            pass
    if DEFAULT_CDN_BASE not in bases:
        bases.append(DEFAULT_CDN_BASE)
    if DEFAULT_CDN_FALLBACK not in bases:
        bases.append(DEFAULT_CDN_FALLBACK)
    return bases


def _extract_play_stream(html):
    if not html:
        return ""
    primary_cdn = _parse_cdn_lines(html)[0]
    m_data = re.search(r"id=[\"']article-videos[\"'][^>]*data-url=[\"']([^\"']+)[\"']", html, re.I)
    if not m_data:
        m_data = re.search(r"data-url=[\"']([^\"']+)[\"'][^>]*id=[\"']article-videos[\"']", html, re.I)
    if m_data:
        cand = m_data.group(1).strip()
        if cand:
            cand = cand.replace("\\u002F", "/").replace("\\/", "/")
            if cand.startswith("http"):
                return cand
            if cand.startswith("/"):
                return primary_cdn + cand
            return primary_cdn + "/" + cand
    for mm in _M3U8_RE.finditer(html):
        hit = mm.group(1).replace("\\u002F", "/").replace("\\/", "/").strip()
        if "sample" in hit or "test" in hit:
            continue
        if hit.startswith("http"):
            return hit
        if hit.startswith("/"):
            return primary_cdn + hit
        return primary_cdn + "/" + hit
    pats = [
        r"(?:var\s+raw\s*=\s*|video_url\s*:\s*|url\s*:\s*)[\"'](https?:\/\/[^\s\"'$<>]+\.m3u8[^\s\"'$<>]*)[\"']",
        r"(https?:\/\/(?:(?!localhost|127\.0\.0\.1)[^\s\"'$<>])+\.mp4[^\s\"'$<>]*)",
    ]
    for p in pats:
        sm = re.search(p, html, re.I)
        if sm:
            found = _clean_stream_url(sm.group(1))
            if found:
                return found
    return ""


def _divider(n):
    return "━" * n


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
        return "蘑菇视频"

    def _fetch(self, path, referer=""):
        if path.startswith("//"):
            full = "https:" + path
        elif path.startswith("/"):
            full = self.siteUrl + path
        elif path.startswith("http"):
            full = path
        else:
            full = self.siteUrl + "/" + path
        headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": referer or (self.siteUrl + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(full, headers=headers, timeout=TIMEOUT)
        except requests.RequestException:
            resp = None
            if full.startswith("https://"):
                try:
                    resp = requests.get("http://" + full[8:], headers=headers, timeout=TIMEOUT)
                except requests.RequestException:
                    resp = None
        if resp is None:
            return 0, ""
        try:
            text = resp.content.decode("utf-8", "ignore")
        except Exception:
            text = ""
        return resp.status_code, _unwrap_html(text)

    def _brand_block(self):
        return "\n".join([
            "🦋 蘑菇视频官方交流群：@tvshare23",
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
        classes = [{"type_id": z[0], "type_name": z[1]} for z in ZONES]
        result = {"class": classes}
        if filter:
            filters = {}
            for z in ZONES:
                if len(z[3]) > 1:
                    filters[z[0]] = [{
                        "key": "sub",
                        "name": "细分分类",
                        "init": z[2],
                        "value": [{"n": n, "v": v} for n, v in z[3]],
                    }]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        status, html = self._fetch("/")
        if status != 200:
            return {"list": []}
        return {"list": _parse_cards(html, self.siteUrl)[:20]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        zone_id = str(tid or "").replace("/", "")
        ext = extend if isinstance(extend, dict) else {}
        target = ""
        if ext.get("sub"):
            target = str(ext.get("sub")).strip()
        else:
            zone = ZONE_MAP.get(zone_id)
            if zone:
                target = zone[2]
        if not target:
            target = zone_id
        if target == "route_home":
            path = "/" if page == 1 else ("/page/" + str(page) + "/")
        elif page == 1:
            path = "/category/" + target + "/"
        else:
            path = "/category/" + target + "/" + str(page) + "/"
        status, html = self._fetch(path)
        if status != 200:
            return self._page_result([], page)
        return self._page_result(_parse_cards(html, self.siteUrl), page)

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_result([], page)
        enc = _encode_uri_component(keyword)
        if page == 1:
            path = "/search/" + enc + "/"
        else:
            path = "/search/" + enc + "/" + str(page) + "/"
        status, html = self._fetch(path)
        if status != 200:
            return self._page_result([], page)
        return self._page_result(_parse_cards(html, self.siteUrl), page)

    def detailContent(self, ids):
        if isinstance(ids, (list, tuple)):
            raw = str(ids[0]) if ids else ""
        else:
            raw = str(ids or "")
        raw_id = raw.strip()
        if not raw_id:
            return {"list": [], "msg": "缺少作品 ID"}
        status, html = self._fetch(raw_id)
        if status != 200 or not html:
            return {"list": [], "msg": "未找到该影片"}
        host = self.siteUrl
        title_m = re.search(r"<title>(.*?)</title>", html, re.I)
        raw_title = title_m.group(1).strip() if title_m else "蝴蝶专线高清视频"
        main_title = re.sub(r"[-_].*$", "", raw_title).strip()
        if not main_title:
            main_title = "蘑菇精彩视频"
        real_stream = _extract_play_stream(html)
        detail_url = raw_id if raw_id.startswith("http") else (host + raw_id)

        rec_cards = _parse_cards(html, host)
        poster_raw = ""
        poster_ready = ""
        dfdf_m = re.findall(r"dfdf\.tjacq\.com/image/[^\s\"']+", html, re.I)
        if dfdf_m:
            poster_raw = "https://" + dfdf_m[0]
        if not poster_raw:
            og_m = re.search(r"property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']", html, re.I)
            if og_m:
                poster_raw = re.sub(r"^(https?:)\/([^\/])", r"\1//\2", og_m.group(1).strip())

        episodes = [{
            "name": "超清正片",
            "value": json.dumps({"page": raw_id, "stream": real_stream}, ensure_ascii=False),
        }]
        seen = {raw_id, detail_url}
        rec_titles = []
        rec_idx = 1
        for card in rec_cards:
            if not poster_raw and not poster_ready and card["vod_pic"]:
                poster_ready = card["vod_pic"]
            rec_id = card["vod_id"]
            if rec_id in seen:
                continue
            seen.add(rec_id)
            rec_title = card["vod_name"]
            rec_titles.append(rec_title)
            display_t = (rec_title[:20] + "...") if len(rec_title) > 20 else rec_title
            label = ("0" + str(rec_idx)) if rec_idx < 10 else str(rec_idx)
            episodes.append({
                "name": label + "·" + display_t,
                "value": json.dumps({"page": rec_id, "stream": ""}, ensure_ascii=False),
            })
            rec_idx += 1
            if rec_idx > 24:
                break

        poster = _format_poster(poster_raw, host) if poster_raw else poster_ready
        num_m = re.search(r"/video/(\d+)/", raw_id)
        summary_lines = [
            "标题：" + main_title,
            "分类：传媒影视",
            "片源：" + LINE_NAME,
            "编号：" + (num_m.group(1) if num_m else raw_id),
            "相关推荐：" + (" / ".join(rec_titles[:6]) if rec_titles else "无"),
        ]
        if real_stream:
            play_url = "#".join(
                _clean_ep_name(ep["name"]) + "$" + ep["value"] for ep in episodes
            )
            remarks_text = "全" + str(len(episodes)) + "部连播"
        else:
            summary_lines.append(NO_SOURCE_REASON)
            play_url = "暂无播放源$" + json.dumps({"notice": NO_SOURCE_REASON}, ensure_ascii=False)
            remarks_text = NO_SOURCE_REASON
        vod = {
            "vod_id": raw,
            "vod_name": main_title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "type_name": "传媒影视",
            "vod_class": "传媒影视",
            "vod_year": "",
            "vod_area": "",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "",
            "vod_remarks": _format_remarks(remarks_text),
            "vod_content": self._brand_block() + "\n" + "\n".join(summary_lines),
            "vod_play_from": LINE_NAME,
            "vod_play_url": play_url,
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        headers = {
            "User-Agent": DEFAULT_UA,
            "Referer": self.siteUrl + "/",
            "Origin": self.siteUrl,
        }
        raw = str(id or "").strip()
        ref = {}
        if raw.startswith("{"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    ref = parsed
            except Exception:
                ref = {}
        if not ref:
            ref = {"page": raw}
        if ref.get("notice"):
            return {"parse": 0, "msg": str(ref.get("notice"))}
        stream_url = str(ref.get("stream") or "").strip()
        video_page = str(ref.get("page") or "").strip()
        target = ""
        if stream_url and (".m3u8" in stream_url or ".mp4" in stream_url or ".ts" in stream_url):
            target = stream_url
        elif video_page:
            status, html = self._fetch(video_page)
            if status == 200 and html:
                found = _extract_play_stream(html)
                if found:
                    target = found
        if target:
            return {"parse": 0, "url": target, "header": headers}
        page_url = video_page if video_page.startswith("http") else (self.siteUrl + video_page if video_page else self.siteUrl)
        return {"parse": 1, "url": page_url, "header": headers}

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249842011&sig=8bccd84006117257
