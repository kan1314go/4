# -*- coding: utf-8 -*-
# RedTube18.py - FongMi/TVBox python spider, converted from Hamo JS plugin com.butterfly.redtube (redtube.js)

import re
import json
import math
import requests
from urllib.parse import quote
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://www.redtube.com"
DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
BRAND = "蝴蝶影视"
POSTER_RATIO = 1.78
PAGE_SIZE = 36
SEARCH_PAGE_SIZE = 32
TIMEOUT = 8

CATEGORIES = [
    ("home", "推荐"),
    ("newest", "最新视频"),
    ("hot", "热门趋势"),
    ("top", "评分最高"),
    ("mostfavored", "最多收藏"),
    ("amateur", "业余"),
    ("anal", "肛交"),
    ("arab", "阿拉伯"),
    ("asian", "亚洲"),
    ("bbw", "丰满大码"),
    ("bigass", "大屁股"),
    ("bigdick", "大屌"),
    ("bigtits", "大胸"),
    ("blonde", "金发"),
    ("blowjob", "口交"),
    ("bondage", "捆绑"),
    ("brazilian", "巴西"),
    ("brunette", "褐发"),
    ("bukkake", "颜射"),
    ("cartoon", "卡通"),
    ("casting", "试镜"),
    ("celebrity", "名人"),
    ("college", "大学"),
    ("compilation", "合集"),
    ("cosplay", "角色扮演"),
    ("creampie", "内射"),
    ("cuckold", "绿帽"),
    ("cumshot", "射精"),
    ("doublepenetration", "双插"),
    ("ebony", "黑人"),
    ("european", "欧洲"),
    ("facials", "颜面射精"),
    ("feet", "恋足"),
    ("femaleorgasm", "女性高潮"),
    ("fetish", "恋物"),
    ("fingering", "指交"),
    ("fisting", "拳交"),
    ("french", "法国"),
    ("funny", "搞笑"),
    ("gangbang", "轮奸"),
    ("german", "德国"),
    ("group", "群交"),
    ("handjob", "手交"),
    ("hd", "高清"),
    ("hentai", "动漫色情"),
    ("indian", "印度"),
    ("interracial", "跨种族"),
    ("japanese", "日本"),
    ("latina", "拉丁"),
    ("lesbian", "女同"),
    ("lingerie", "内衣"),
    ("massage", "按摩"),
    ("masturbation", "自慰"),
    ("mature", "熟女"),
    ("milf", "熟妇"),
    ("orgy", "淫乱派对"),
    ("parody", "恶搞"),
    ("party", "派对"),
    ("pissing", "撒尿"),
    ("popular-with-women", "女性喜爱"),
    ("pov", "第一视角"),
    ("public", "公共场所"),
    ("pussy-licking", "舔阴"),
    ("reality", "真实"),
    ("redhead", "红发"),
    ("romantic", "浪漫"),
    ("rough", "粗暴"),
    ("small-tits", "小胸"),
    ("solomale", "单男"),
    ("squirting", "潮吹"),
    ("stepfantasy", "继亲幻想"),
    ("striptease", "脱衣舞"),
    ("teens", "青春少女 (18+)"),
    ("threesome", "三人行"),
    ("toys", "玩具"),
    ("transgender", "变性人"),
    ("verifiedamateurs", "认证业余"),
    ("vintage", "复古"),
    ("virtualreality", "虚拟现实"),
    ("webcam", "摄像头"),
    ("youngandold", "忘年恋")
]

CAT_NAME_BY_ID = {}
for _cid, _cname in CATEGORIES:
    CAT_NAME_BY_ID[_cid] = _cname

SLUG_IDS = set()
for _cid, _cname in CATEGORIES[5:]:
    SLUG_IDS.add(_cid)

SORTING_MAP = {
    "rating": "sorting=rating",
    "rating-monthly": "sorting=rating&period=monthly",
    "rating-alltime": "sorting=rating&period=alltime",
    "mostfavored": "sorting=mostfavored",
    "mostviewed": "sorting=mostviewed",
    "mostviewed-monthly": "sorting=mostviewed&period=monthly",
    "mostviewed-alltime": "sorting=mostviewed&period=alltime",
    "longest": "sorting=longest",
    "longest-alltime": "sorting=longest&period=alltime"
}

SORT_OPTIONS = [
    ("", "默认推荐"),
    ("rating", "评分最高·本周"),
    ("rating-monthly", "评分最高·本月"),
    ("rating-alltime", "评分最高·全部"),
    ("mostfavored", "最多收藏"),
    ("mostviewed", "最多观看·本周"),
    ("mostviewed-monthly", "最多观看·本月"),
    ("mostviewed-alltime", "最多观看·全部"),
    ("longest", "最长·本周"),
    ("longest-alltime", "最长·全部")
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
    "frac12": "½", "frac14": "¼", "frac34": "¾"
}


def _decode_entities(s):
    out = str(s or "")
    out = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: chr(int(m.group(1), 16)), out)
    out = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1), 10)), out)

    def _named(m):
        name = m.group(1)
        if name == "amp":
            return m.group(0)
        return NAMED_ENTITIES.get(name, m.group(0))

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


def _js_round(x):
    return int(math.floor(float(x) + 0.5))


def _parse_int_js(s):
    m = re.match(r"\s*[+-]?\d+", str(s or ""))
    if not m:
        return None
    try:
        return int(m.group(0))
    except ValueError:
        return None


def _clean_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        super(Spider, self).__init__()
        self.siteUrl = DEFAULT_HOST
        self.options = {}

    def init(self, extend=""):
        opts = {}
        if isinstance(extend, dict):
            opts = extend
        elif extend:
            try:
                parsed = json.loads(extend)
                if isinstance(parsed, dict):
                    opts = parsed
            except Exception:
                opts = {}
        self.options = opts
        custom = str(opts.get("host") or "").strip()
        if custom.startswith("http"):
            self.siteUrl = custom.rstrip("/")
        else:
            self.siteUrl = DEFAULT_HOST
        return True

    def getName(self):
        return "RedTube"

    def destroy(self):
        self.options = {}

    def _fetch(self, url, referer=None):
        headers = {"User-Agent": DEFAULT_UA, "Referer": referer or (self.siteUrl + "/")}
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            return resp.status_code, resp.content.decode("utf-8", "ignore")
        except Exception:
            return -1, ""

    def _slice_grid(self, html):
        text = str(html or "")
        m = re.search(r"<ul[^>]*videos_grid[^>]*>", text)
        if not m:
            return ""
        start = m.end()
        end = text.find("</ul>", start)
        if end == -1:
            return text[start:]
        return text[start:end]

    def _parse_cards(self, grid_html):
        html = str(grid_html or "")
        items = []
        seen = {}
        opens = []
        for om in re.finditer(r"<li[^>]*thumbnail-card[^>]*>", html):
            opens.append((om.start(), om.end(), om.group(0)))
        for i in range(len(opens)):
            o_start, o_end, o_tag = opens[i]
            idm = re.search(r'data-video-id="(\d+)"', o_tag)
            if not idm or not idm.group(1):
                continue
            vid = idm.group(1)
            if seen.get(vid):
                continue
            if i + 1 < len(opens):
                chunk_end = opens[i + 1][0]
            else:
                chunk_end = min(len(html), o_end + 6000)
            chunk = html[o_end:chunk_end]
            poster = ""
            pm = re.search(r'data-src="([^"]+)"', chunk)
            if pm and pm.group(1):
                poster = pm.group(1)
            poster = _abs_poster(poster, self.siteUrl)
            if not poster:
                continue
            title = ""
            am = re.search(r'alt="([^"]*)"', chunk)
            if am and am.group(1):
                title = _decode_entities(am.group(1)).strip()
            if not title:
                tm = re.search(r'class="video-title-text[^"]*"[^>]*>([\s\S]*?)</a>', chunk)
                if tm and tm.group(1):
                    title = re.sub(r"\s+", " ", _decode_entities(tm.group(1))).strip()
            if not title:
                continue
            dur = ""
            dum = re.search(r'class="video-properties tm_video_duration">([^<]+)<', chunk)
            if dum and dum.group(1):
                dur = dum.group(1).strip()
            status = BRAND
            if dur:
                status += " | " + dur
            seen[vid] = True
            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": poster,
                "vod_remarks": status,
                "style": {"type": "rect", "ratio": POSTER_RATIO}
            })
        return items

    def _sort_filter_row(self):
        return {
            "key": "sorting",
            "name": "排序",
            "init": "",
            "value": [{"n": name, "v": value} for value, name in SORT_OPTIONS]
        }

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, cname in CATEGORIES:
                if cid in SLUG_IDS:
                    filters[cid] = [self._sort_filter_row()]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        status, html = self._fetch(self.siteUrl + "/", self.siteUrl + "/")
        if status != 200:
            return {"list": []}
        return {"list": self._parse_cards(self._slice_grid(html))}

    def _category_path(self, category_id):
        if category_id == "home":
            return "/"
        if category_id == "newest":
            return "/newest"
        if category_id == "hot":
            return "/hot?cc=us"
        if category_id == "top":
            return "/top"
        if category_id == "mostfavored":
            return "/mostfavored"
        if category_id in SLUG_IDS:
            return "/redtube/" + category_id
        return ""

    def _page_form(self, page, cards, page_size):
        if not cards:
            return {"page": page, "pagecount": page, "limit": page_size, "total": 0, "list": []}
        pagecount = page + 1 if len(cards) >= page_size else page
        return {"page": page, "pagecount": pagecount, "limit": page_size, "total": pagecount * page_size, "list": cards}

    def _to_page(self, pg):
        try:
            page = int(str(pg))
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def categoryContent(self, tid, pg, filter, extend):
        category_id = str(tid)
        page = self._to_page(pg)
        base = self._category_path(category_id)
        if not base:
            return self._page_form(page, [], PAGE_SIZE)
        q = []
        if page > 1:
            q.append("page=" + str(page))
        if category_id in SLUG_IDS and isinstance(extend, dict):
            sv = str(extend.get("sorting") or "").strip()
            if sv in SORTING_MAP:
                q.append(SORTING_MAP[sv])
        url = self.siteUrl + base
        if q:
            url += ("&" if "?" in base else "?") + "&".join(q)
        status, html = self._fetch(url, self.siteUrl + "/")
        if status != 200:
            return self._page_form(page, [], PAGE_SIZE)
        cards = self._parse_cards(self._slice_grid(html))
        return self._page_form(page, cards, PAGE_SIZE)

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = self._to_page(pg)
        if not keyword:
            return self._page_form(page, [], SEARCH_PAGE_SIZE)
        url = self.siteUrl + "/?search=" + quote(keyword)
        if page > 1:
            url += "&page=" + str(page)
        status, html = self._fetch(url, self.siteUrl + "/")
        if status != 200:
            return self._page_form(page, [], SEARCH_PAGE_SIZE)
        cards = self._parse_cards(self._slice_grid(html))
        return self._page_form(page, cards, SEARCH_PAGE_SIZE)

    def _parse_iso_duration(self, s):
        m = re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?", str(s or ""))
        if not m:
            return 0
        h = int(m.group(1)) if m.group(1) else 0
        mi = int(m.group(2)) if m.group(2) else 0
        sec = float(m.group(3)) if m.group(3) else 0
        return _js_round(h * 3600 + mi * 60 + sec)

    def _fmt_duration(self, total):
        total = max(0, _js_round(total or 0))
        h = total // 3600
        mi = (total % 3600) // 60
        s = total % 60
        mm = str(h * 60 + mi) if h > 0 else str(mi)
        ss = ("0" + str(s)) if s < 10 else str(s)
        return mm + ":" + ss

    def _extract_ld(self, html):
        out = {"name": "", "duration": "", "thumbnailUrl": "", "uploadDate": "", "description": "", "interactionCount": ""}
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
        ic = re.search(r'"interactionCount":\s*(\d+)', block)
        if ic and ic.group(1):
            out["interactionCount"] = ic.group(1)
        return out

    def _extract_actors(self, html):
        out = []
        text = str(html or "")
        md = re.search(r'<meta name="description" content="([^"]*)"', text)
        if md and md.group(1):
            desc = _decode_entities(md.group(1))
            sm = re.search(r"Starring Pornstars?(?:\(s\))?:\s*([^.]*)", desc)
            if sm and sm.group(1):
                for part in sm.group(1).split(","):
                    nm = part.strip()
                    if nm and nm not in out:
                        out.append(nm)
        for m in re.finditer(r'data-pornstar="([^"]*)"', text):
            nm = _decode_entities(m.group(1)).strip()
            if nm and nm not in out:
                out.append(nm)
        return out

    def _extract_uploader(self, html):
        md = re.search(r'<meta name="description" content="([^"]*)"', str(html or ""))
        if md and md.group(1):
            desc = _decode_entities(md.group(1))
            um = re.search(r"Uploaded by ([^-]+?)(?:\s*-|\s*$)", desc)
            if um and um.group(1):
                return um.group(1).strip()
        return ""

    def _extract_genres(self, html):
        out = []
        for m in re.finditer(r'video_carousel_category" href="/redtube/([a-z0-9\-]+)">([^<]+)<', str(html or "")):
            slug = m.group(1)
            nm = CAT_NAME_BY_ID.get(slug) or _decode_entities(m.group(2)).strip()
            if nm and nm not in out:
                out.append(nm)
        return out

    def _brand_block(self):
        return ("🦋 RedTube官方交流群：@tvshare23" + "\n"
                + "导演：🦋 蝴蝶影视" + "\n"
                + "当前主站：" + self.siteUrl + "\n"
                + "━" * 28 + "\n"
                + "━" * 7)

    def detailContent(self, ids):
        if isinstance(ids, (list, tuple)):
            vid = str(ids[0]) if ids else ""
        else:
            vid = str(ids or "")
        detail_url = self.siteUrl + "/" + vid
        status, html = self._fetch(detail_url, self.siteUrl + "/")
        if status != 200 or not html:
            return {"list": [], "msg": "未找到该影片"}
        ld = self._extract_ld(html)
        title = ld["name"] or ""
        if not title:
            om = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', html, re.I)
            if not om:
                om = re.search(r'<meta[^>]+content="([^"]*)"[^>]+property="og:title"', html, re.I)
            if om and om.group(1):
                title = _decode_entities(om.group(1))
        if not title:
            return {"list": [], "msg": "未找到该影片"}
        has_source = "mediaDefinition" in html
        poster = ""
        im = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', html, re.I)
        if not im:
            im = re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', html, re.I)
        if im and im.group(1):
            poster = _abs_poster(im.group(1), self.siteUrl)
        if not poster and ld["thumbnailUrl"]:
            poster = _abs_poster(ld["thumbnailUrl"], self.siteUrl)
        actors = self._extract_actors(html)
        genres = self._extract_genres(html)
        uploader = self._extract_uploader(html)
        year = ""
        if ld["uploadDate"] and len(ld["uploadDate"]) >= 4:
            year = ld["uploadDate"][:4]
        dur_sec = self._parse_iso_duration(ld["duration"])
        dur_text = self._fmt_duration(dur_sec) if dur_sec > 0 else ""
        views = ld["interactionCount"] or ""
        related = self._parse_cards(self._slice_grid(html))
        rel_names = []
        for card in related[:6]:
            rel_names.append(card["vod_name"])
        body = ("标题：" + title + "\n"
                + "分类：" + (" / ".join(genres) if genres else "无") + "\n"
                + "上传者：" + (uploader or "未知") + "\n"
                + "时长：" + (dur_text or "未知") + "\n"
                + "播放量：" + (views or "未知") + "\n"
                + "片源：🦋 蝴蝶专线" + "\n"
                + "编号：" + vid + "\n"
                + "相关推荐：" + (" / ".join(rel_names) if rel_names else "无"))
        content = self._brand_block() + "\n" + body
        if has_source:
            episodes = ["正片$" + vid]
        else:
            content += "\n" + "未找到可播放片源"
            notice_ref = {"notice": "未找到可播放片源"}
            episodes = ["暂无播放源$" + json.dumps(notice_ref, ensure_ascii=False)]
        for card in related:
            episodes.append(_clean_ep_name(card["vod_name"]) + "$" + card["vod_id"])
        status_text = BRAND
        if dur_text:
            status_text += " | " + dur_text
        if actors:
            actor_text = ",".join(actors) + ",🦋 TG群: @tvshare23"
        else:
            actor_text = "🦋 TG群: @tvshare23"
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_year": year,
            "vod_class": ",".join(genres),
            "vod_actor": actor_text,
            "vod_director": "🦋 蝴蝶影视",
            "vod_remarks": status_text,
            "vod_content": content,
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes)
        }
        return {"list": [vod]}

    def _extract_token(self, html):
        m = re.search(r"\\?/media\\?/hls\?s=([A-Za-z0-9_\-]+)", str(html or ""))
        if m and m.group(1):
            return m.group(1)
        return ""

    def _pick_tier(self, tiers):
        if not isinstance(tiers, list) or not tiers:
            return ""
        def_url = ""
        best_url = ""
        best_num = -1
        for t in tiers:
            if not isinstance(t, dict) or not t.get("videoUrl"):
                continue
            if t.get("defaultQuality") is True:
                def_url = str(t["videoUrl"])
            q = _parse_int_js(t.get("quality") or "")
            if q is not None and q > best_num:
                best_num = q
                best_url = str(t["videoUrl"])
        if def_url:
            return def_url
        if best_url:
            return best_url
        first = tiers[0]
        if isinstance(first, dict):
            return str(first.get("videoUrl") or "")
        return ""

    def _fetch_media(self, path, referer):
        headers = {"User-Agent": DEFAULT_UA, "Referer": referer}
        try:
            resp = requests.get(self.siteUrl + path, headers=headers, timeout=TIMEOUT)
        except Exception:
            return ""
        if resp.status_code != 200:
            return ""
        text = resp.content.decode("utf-8", "ignore")
        if not text:
            return ""
        try:
            tiers = json.loads(text)
        except Exception:
            return ""
        return self._pick_tier(tiers)

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "")
        if raw.startswith("{"):
            ref = {}
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    ref = parsed
            except Exception:
                ref = {}
            if ref.get("notice"):
                return {"parse": 0, "msg": str(ref["notice"])}
        vid = raw
        detail_url = self.siteUrl + "/" + vid
        status, html = self._fetch(detail_url, self.siteUrl + "/")
        if status != 200 or not html:
            if status == -1:
                msg = "请求失败：网络异常"
            else:
                msg = "请求失败：HTTP " + str(status)
            return {"parse": 0, "jx": 0, "url": "", "msg": msg}
        token = self._extract_token(html)
        if not token:
            return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放标识"}
        hls_url = self._fetch_media("/media/hls?s=" + token, detail_url)
        if hls_url:
            return {"parse": 0, "jx": 0, "url": hls_url,
                    "header": {"User-Agent": DEFAULT_UA, "Referer": detail_url}}
        mp4_url = self._fetch_media("/media/mp4?s=" + token, detail_url)
        if mp4_url:
            return {"parse": 0, "jx": 0, "url": mp4_url,
                    "header": {"User-Agent": DEFAULT_UA, "Referer": detail_url}}
        return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放地址"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Not Found"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250163254&sig=94704c536b5a36de
