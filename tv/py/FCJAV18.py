# -*- coding: utf-8 -*-
# FCJAV18 (com.butterfly.fcjav)

import base64
import json
import re

import requests
from urllib.parse import quote, unquote

from base.spider import Spider as BaseSpider

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
DEFAULT_HOST = "https://fcjav.com"
SITE_NAME = "FCJAV"
BRAND = "蝴蝶影视"
ACTOR_BRAND = "🦋 TG群: @tvshare23"
DIRECTOR_BRAND = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专属线路"
RELATED_LINE = "相关推荐"
PAGE_SIZE = 24
PIC_RATIO = 0.70

CATEGORIES = [
    ("movies?genre=censored", "有码 (Censored)"),
    ("movies?genre=uncensored", "无码 (Uncensored)"),
    ("movies", "最新/全部"),
    ("movies?genre=amateur", "业余"),
    ("movies?genre=reducing-mosaic", "减薄马赛克"),
    ("genre/uncensored-leaked", "无码流出"),
    ("label/s1-no-1-style", "S1 NO.1"),
    ("label/madonna", "Madonna"),
    ("label/moodyz-diva", "MOODYZ"),
    ("label/sod-star", "SOD star"),
    ("label/hhh-group", "HHH Group"),
    ("label/oppai", "OPPAI"),
    ("label/glory-quest", "GLORY QUEST"),
    ("label/tissue", "Tissue"),
    ("label/honnaka", "Honnaka"),
    ("label/fitch", "Fitch"),
    ("label/das", "Das"),
    ("genre/amateur", "素人"),
    ("genre/anal", "肛交"),
    ("genre/av-idol", "AV女优"),
    ("genre/beautiful-girl", "美少女"),
    ("genre/big-tits", "巨乳"),
    ("genre/blowjob", "口交"),
    ("genre/cosplay", "Cosplay"),
    ("genre/creampie", "中出"),
    ("genre/cumshot", "颜射"),
    ("genre/bondage", "束缚"),
]

SORT_ROW = {
    "key": "sort",
    "name": "排序",
    "init": "desc",
    "value": [
        {"n": "最新更新", "v": "desc"},
        {"n": "发布日期", "v": "release"},
        {"n": "最多观看", "v": "viewed"},
        {"n": "最受喜欢", "v": "liked"},
        {"n": "最多收藏", "v": "favorite"},
        {"n": "最早更新", "v": "asc"},
    ],
}
QUALITY_ROW = {
    "key": "quality",
    "name": "清晰度",
    "init": "all",
    "value": [
        {"n": "全部", "v": "all"},
        {"n": "高清(HD)", "v": "hd"},
        {"n": "普清(SD)", "v": "sd"},
    ],
}
YEAR_ROW = {
    "key": "year",
    "name": "年份",
    "init": "all",
    "value": [
        {"n": "全部", "v": "all"},
        {"n": "2026", "v": "2026"},
        {"n": "2025", "v": "2025"},
        {"n": "2024", "v": "2024"},
        {"n": "2023", "v": "2023"},
        {"n": "2022", "v": "2022"},
    ],
}
MOVIE_FILTER_ROWS = [SORT_ROW, QUALITY_ROW, YEAR_ROW]


def unescape_html(s):
    s = str(s or "")
    s = s.replace("&amp;", "&")
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&quot;", '"')
    s = re.sub(r"&#0?39;", "'", s)
    s = s.replace("&nbsp;", " ")
    s = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), s)
    return s


def clean_text(s):
    s = unescape_html(re.sub(r"<[^>]+>", " ", str(s or "")))
    return re.sub(r"\s+", " ", s).strip()


def sanitize_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def init(self, extend=""):
        self.host = DEFAULT_HOST
        host = ""
        if isinstance(extend, dict):
            host = str(extend.get("host") or "")
        elif extend:
            s = str(extend).strip()
            if s.startswith("http"):
                host = s
            else:
                try:
                    data = json.loads(s)
                    if isinstance(data, dict):
                        host = str(data.get("host") or "")
                except Exception:
                    host = ""
        if host.startswith("http"):
            self.host = host.rstrip("/")

    # ---------- fetch ----------

    def _fetch(self, target, referer=None, method="GET", data=None, extra_headers=None):
        url = str(target or "")
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.host + url
        headers = {
            "User-Agent": UA,
            "Referer": referer or (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }
        if extra_headers:
            headers.update(extra_headers)
        try:
            if method == "POST":
                resp = requests.post(url, data=data, headers=headers, timeout=8)
            else:
                resp = requests.get(url, headers=headers, timeout=8)
            return resp.text or ""
        except Exception:
            return ""

    # ---------- helpers ----------

    def _abs_url(self, u, host):
        u = str(u or "").strip().replace("\\/", "/")
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("http"):
            return u
        if u.startswith("/"):
            return (host or DEFAULT_HOST) + u
        return (host or DEFAULT_HOST) + "/" + u

    def _origin(self, u):
        m = re.match(r"^(https?://[^/]+)", str(u or ""), re.I)
        return m.group(1) if m else ""

    def _pick_pic(self, block, host):
        m = re.search(r"(?:data-original|data-src|data-lazy-src)\s*=\s*[\"']([^\"']+)[\"']", block, re.I)
        if not m:
            m = re.search(r"<img[^>]+src\s*=\s*[\"']([^\"']+)[\"']", block, re.I)
        return self._abs_url(m.group(1), host) if m else ""

    def _meta_content(self, html, prop):
        re1 = r"<meta[^>]+(?:property|name)=[\"']" + prop + r"[\"'][^>]+content=[\"']([^\"']*)[\"']"
        re2 = r"<meta[^>]+content=[\"']([^\"']*)[\"'][^>]+(?:property|name)=[\"']" + prop + r"[\"']"
        m = re.search(re1, html, re.I) or re.search(re2, html, re.I)
        return unescape_html(m.group(1)) if m else ""

    def _parse_list(self, html, host):
        items = []
        blocks = str(html or "").split('class="ml-item"')
        for block in blocks[1:]:
            scope = block[:1500]
            lm = re.search(r"href=[\"'](https?://[^\"']*/v/[^\"']+)[\"']", scope, re.I)
            if not lm:
                lm = re.search(r"href=[\"'](/v/[^\"']+)[\"']", scope, re.I)
            if not lm:
                continue
            link = lm.group(1)
            vid = link.rstrip("/").split("/v/")[-1]
            tm = re.search(r"data-title=[\"']([^\"']+)[\"']", scope, re.I)
            if not tm:
                tm = re.search(r"title=[\"']([^\"']+)[\"']", scope, re.I)
            if tm:
                name = clean_text(tm.group(1)) or vid
            else:
                name = vid.upper()
            pic = self._pick_pic(scope, host)
            rm = re.search(r"class=[\"'][^\"']*mli-runtimes[^\"']*[\"'][^>]*>([^<]+)<", scope, re.I)
            if not rm:
                rm = re.search(r"class=[\"'][^\"']*mli-quality[^\"']*[\"'][^>]*>([^<]+)<", scope, re.I)
            remarks = clean_text(rm.group(1)) if rm else ""
            vod_remarks = (BRAND + " | " + remarks) if remarks else (BRAND + " | 高清")
            items.append({
                "vod_id": vid + "@@" + quote(pic, safe=""),
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": vod_remarks,
                "style": {"type": "rect", "ratio": PIC_RATIO},
            })
        return items

    def _norm_id(self, v):
        t = str(v or "")
        for _ in range(3):
            if not re.search(r"%[0-9A-Fa-f]{2}", t):
                break
            try:
                d = unquote(t)
            except Exception:
                break
            if d == t:
                break
            t = d
        return t

    def _build_cat_url(self, tid, page, extend):
        clean = self._norm_id(str(tid or "movies")).strip("/")
        if clean.startswith("movies"):
            parts = clean.split("?")
            base = parts[0]
            q = {}
            if len(parts) > 1:
                for kv in parts[1].split("&"):
                    p = kv.split("=")
                    if p[0]:
                        q[p[0]] = unquote(p[1]) if len(p) > 1 else ""
            q["pg"] = str(page)
            if "type" not in q and "genre" not in q:
                q["type"] = "all"
            f = extend or {}
            if f.get("sort"):
                q["sort"] = str(f["sort"])
            if f.get("quality") and str(f["quality"]) != "all":
                q["quality"] = str(f["quality"])
            if f.get("year") and str(f["year"]) != "all":
                q["year"] = str(f["year"])
            qs = "&".join(k + "=" + quote(str(v), safe="") for k, v in q.items())
            return "/" + base + "?" + qs
        return "/" + clean + (("/pg-" + str(page)) if page > 1 else "")

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
            page = int(pg)
        except Exception:
            page = 1
        return page if page > 0 else 1

    def _brand_block(self):
        return "\n".join([
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ])

    def _build_episodes(self, html, slug):
        pairs = []
        seen = set()
        for m in re.finditer(r"data-source=\"(\d+)\"\s+data-id=\"(\d+)\"", html):
            key = m.group(1) + "|" + m.group(2)
            if key in seen:
                continue
            seen.add(key)
            pairs.append((m.group(1), m.group(2)))
        names = [m.group(1) for m in re.finditer(r"class=\"switch-source[^\"]*\"[^>]*>[\s\S]*?</i>\s*([A-Za-z0-9]+)\s*</button>", html)]
        eps = []
        for idx, pair in enumerate(pairs):
            nm = names[idx] if idx < len(names) else ("线路" + str(idx + 1))
            nm = sanitize_ep_name(nm)
            eps.append((nm, json.dumps({"filmId": pair[0], "eid": pair[1], "slug": slug})))
        f4 = [e for e in eps if e[0].upper() == "F4"]
        if f4:
            eps = f4
        if not eps:
            eps = [("正片", json.dumps({"filmId": "", "eid": "", "slug": slug}))]
        return eps

    def _extract_genres(self, html):
        genres = []
        gm = re.search(r"<p><strong>Genre\(s\):\s*</strong>([\s\S]*?)</p>", html, re.I)
        if gm:
            for am in re.finditer(r"<a[^>]*>([\s\S]*?)</a>", gm.group(1)):
                t = clean_text(am.group(1))
                if t:
                    genres.append(t)
        return genres

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, _cname in CATEGORIES:
                if cid.startswith("movies"):
                    filters[cid] = MOVIE_FILTER_ROWS
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        html = self._fetch("/movies")
        return {"list": self._parse_list(html, self.host)}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        url = self._build_cat_url(tid, page, extend or {})
        html = self._fetch(url)
        return self._page_form(self._parse_list(html, self.host), page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        kw = str(key or "").strip()
        if not kw:
            return self._page_form([], page)
        path = "/search/" + quote(kw, safe="") + (("/pg-" + str(page)) if page > 1 else "")
        html = self._fetch(path)
        return self._page_form(self._parse_list(html, self.host), page)

    # ---------- detail ----------

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        vid = raw
        ref_pic = ""
        if "@@" in raw:
            vid, pic_enc = raw.split("@@", 1)
            ref_pic = unquote(pic_enc)
        if vid.startswith("http"):
            durl = vid
            slug = vid.rstrip("/").split("/v/")[-1]
        else:
            durl = self.host + "/v/" + vid
            slug = vid
        html = self._fetch(durl)
        if not html:
            return {"list": []}

        name = ""
        hm = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
        if hm:
            name = clean_text(hm.group(1))
        if not name:
            tm = re.search(r"<title>([\s\S]*?)</title>", html, re.I)
            if tm:
                name = re.sub(r"\s*[-|]\s*FCJAV.*$", "", clean_text(tm.group(1)), flags=re.I)

        poster = ref_pic if ref_pic.startswith("http") else (self._meta_content(html, "og:image") or "")
        desc = self._meta_content(html, "description") or self._meta_content(html, "og:description") or ""
        genres = self._extract_genres(html)

        eps = self._build_episodes(html, slug)

        related_cards = []
        pos = html.find("You May Also Like")
        if pos >= 0:
            for card in self._parse_list(html[pos:], self.host):
                card_vid = card["vod_id"].split("@@", 1)[0]
                if card_vid == slug:
                    continue
                related_cards.append((card_vid, card["vod_name"]))
        related_eps = [(sanitize_ep_name(title), "rel:" + card_vid) for card_vid, title in related_cards]

        content_lines = [self._brand_block()]
        if desc:
            content_lines.append(desc)
        else:
            content_lines.append("标题：" + (name or slug))
            content_lines.append("分类：" + "、".join(genres))
            content_lines.append("片源：" + LINE_NAME)
            content_lines.append("编号：" + slug)
            if related_cards:
                content_lines.append("相关推荐：" + "、".join([t for _v, t in related_cards[:6]]))

        play_from_parts = [LINE_NAME]
        play_url_parts = ["#".join(nm + "$" + val for nm, val in eps)]
        if related_eps:
            play_from_parts.append(RELATED_LINE)
            play_url_parts.append("#".join(nm + "$" + val for nm, val in related_eps))

        vod = {
            "vod_id": vid,
            "vod_name": name or vid,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": ACTOR_BRAND,
            "vod_director": DIRECTOR_BRAND,
            "vod_remarks": BRAND + " | 超清正片",
            "vod_content": "\n".join(content_lines),
            "vod_play_from": "$$$".join(play_from_parts),
            "vod_play_url": "$$$".join(play_url_parts),
        }
        return {"list": [vod]}

    # ---------- resolve ----------

    def _b64_bytes(self, s):
        clean = re.sub(r"[^A-Za-z0-9+/=]", "", str(s or ""))
        clean += "=" * (-len(clean) % 4)
        try:
            return base64.b64decode(clean)
        except Exception:
            return b""

    def _b64_text(self, s):
        raw = self._b64_bytes(str(s or "").replace("-", "+").replace("_", "/"))
        try:
            return raw.decode("utf-8")
        except Exception:
            return raw.decode("latin-1")

    def _decode_player_enc(self, enc, pk):
        raw = self._b64_bytes(enc)
        pk_str = str(pk or "")
        if not pk_str:
            return ""
        key = bytes(bytearray([ord(c) & 255 for c in pk_str]))
        out = bytes(bytearray([b ^ key[i % len(key)] for i, b in enumerate(raw)]))
        try:
            return out.decode("utf-8")
        except Exception:
            return out.decode("latin-1")

    def _clean_wrap_f4(self, u):
        return "https://" + self._b64_text("Y2xlYW4uNTU2ODk5OS5jYy5jZA==") + "/clean?u=" + quote(u, safe="") + "&px=1&o=" + quote("https://f4scdn.com", safe="")

    def _extract_play_url(self, html):
        for pat in (r"var\s+urlPlay\s*=\s*'([^']+)'", r"var\s+urlPlay\s*=\s*\"([^\"]+)\"", r"\"file\"\s*:\s*\"([^\"]+)\"", r"'file'\s*:\s*'([^']+)'"):
            m = re.search(pat, str(html or ""))
            if m and m.group(1):
                return m.group(1).strip()
        return ""

    def _web_result(self, page_url):
        return {"parse": 1, "playUrl": "", "url": page_url, "header": {"User-Agent": UA, "Referer": page_url}}

    def _direct_result(self, url, referer):
        return {"parse": 0, "playUrl": "", "url": url, "header": {"User-Agent": UA, "Referer": referer}}

    def playerContent(self, flag, id, vipFlags):
        vid_id = str(id or "")
        if vid_id.startswith("rel:"):
            target = vid_id[4:]
            target_url = self.host + "/v/" + target
            target_html = self._fetch(target_url, referer=target_url)
            target_eps = self._build_episodes(target_html, target) if target_html else []
            if not target_eps:
                return self._web_result(target_url)
            vid_id = target_eps[0][1]

        ref = {}
        if vid_id.startswith("{"):
            try:
                parsed = json.loads(vid_id)
                if isinstance(parsed, dict):
                    ref = parsed
            except Exception:
                ref = {}
        slug = str(ref.get("slug") or "")
        if not slug and not vid_id.startswith("{"):
            slug = vid_id
        film_id = str(ref.get("filmId") or "")
        eid = str(ref.get("eid") or "")
        page_url = self.host + "/v/" + slug

        html = self._fetch(page_url, referer=page_url)
        ptm = re.search(r"__pt\s*=\s*\"([^\"]+)\"", html)
        pkm = re.search(r"__pk\s*=\s*\"([^\"]+)\"", html)
        if not film_id:
            dm = re.search(r"data-source=\"(\d+)\"\s+data-id=\"(\d+)\"", html)
            if dm:
                film_id = dm.group(1)
                if not eid:
                    eid = dm.group(2)
        if not film_id or not eid or not ptm or not pkm:
            return self._web_result(page_url)

        body = "episode=" + quote(eid, safe="") + "&filmId=" + quote(film_id, safe="") + "&pt=" + quote(ptm.group(1), safe="")
        resp_text = self._fetch(
            "/ajax/player",
            referer=page_url,
            method="POST",
            data=body,
            extra_headers={"X-Requested-With": "XMLHttpRequest", "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
        )
        try:
            j = json.loads(resp_text or "{}")
        except Exception:
            return self._web_result(page_url)
        if not isinstance(j, dict) or j.get("error"):
            return self._web_result(page_url)

        iframe_html = ""
        if j.get("player_enc"):
            iframe_html = self._decode_player_enc(j["player_enc"], pkm.group(1))
        elif j.get("player"):
            iframe_html = str(j["player"])
        sm = re.search(r"src=\"([^\"]+)\"", iframe_html or "")
        iframe_url = sm.group(1) if sm else ""
        if not iframe_url:
            return self._web_result(page_url)

        if re.search(r"f4scdn\.com/e/", iframe_url):
            ih = self._fetch(iframe_url, referer=page_url)
            am = re.search(r"data-api=\"([^\"]+)\"", ih)
            if am:
                api = am.group(1).replace("&amp;", "&")
                if api.startswith("/"):
                    api = self._origin(iframe_url) + api
                ar_text = self._fetch(
                    api + (("&" if "?" in api else "?") + "ab=0"),
                    referer=iframe_url,
                    extra_headers={"Accept": "application/json, text/javascript, */*; q=0.01", "X-Requested-With": "XMLHttpRequest"},
                )
                try:
                    aj = json.loads(ar_text or "{}")
                except Exception:
                    aj = {}
                if isinstance(aj, dict) and aj.get("src"):
                    return self._direct_result(self._clean_wrap_f4(str(aj["src"])), iframe_url)
                if isinstance(aj, dict) and aj.get("url"):
                    return self._direct_result(self._clean_wrap_f4(self._abs_url(str(aj["url"]), self._origin(iframe_url))), iframe_url)
            return self._web_result(page_url)

        ih2 = self._fetch(iframe_url, referer=self.host + "/")
        pu = self._extract_play_url(ih2)
        if pu:
            return self._direct_result(self._abs_url(pu, self.host), page_url)
        return self._web_result(page_url)

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250037307&sig=6be4b4b36088b8eb
