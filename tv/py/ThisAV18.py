# ThisAV - FongMi Python Spider
# ThisAV完整版 (com.butterfly.thisav)
import base64
import json
import re

import requests
from urllib.parse import quote, unquote

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://jable01.com"
NAV_URLS = ["https://x99dh.cc", "https://x99dh.one"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
SITE_NAME = "ThisAV"
PAGE_SIZE = 12
PIC_RATIO = 1.78
FALLBACK_PIC_HOST = "https://spic2-147.71352.men"
VOD_ACTOR = "🦋 TG群: @tvshare23"
VOD_DIRECTOR = "🦋 蝴蝶影视"

VIDEO_SORT_OPTIONS = [
    ("default", "默认排序"),
    ("released_at", "发行日期"),
    ("published_at", "最近更新"),
    ("saved", "收藏最多"),
    ("today_views", "今日浏览"),
    ("weekly_views", "本周浏览"),
    ("monthly_views", "本月浏览"),
    ("views", "总浏览数"),
]

VIDEO_FILTER_OPTIONS = [
    ("all", "所有"),
    ("individual", "单人作品"),
    ("multiple", "多人作品"),
    ("chinese-subtitle", "中文字幕"),
]

FALLBACK_ACTRESS_OPTIONS = [
    ("", "全部女优 (默认最新)"),
    ("yua-mikami", "三上悠亚"),
    ("eimi-fukada", "深田咏美"),
    ("kanna-hashimoto", "桥本有菜"),
    ("saeko-matsushita", "松下纱荣子"),
    ("kana-momonogi", "桃乃木香奈"),
    ("minami-aizawa", "相泽南"),
    ("shoko-takahashi", "高桥圣子"),
    ("tsukasa-aoi", "葵司"),
    ("yuna-shiina", "椎名由奈"),
    ("airi-suzumura", "铃村爱里"),
    ("remu-suzumori", "凉森玲梦"),
    ("ichika-matsumoto", "松本一香"),
    ("mirei-uno", "宇野美玲"),
    ("saika-kawakita", "河北彩花"),
    ("miru-sakamichi", "坂道美琉"),
    ("mei-itsukaichi", "五日市芽依"),
    ("karen-kaede", "枫花恋"),
    ("tsubasa-amami", "天海翼"),
    ("julia", "JULIA"),
    ("hitomi", "Hitomi"),
]

FALLBACK_RANKING_OPTIONS = [("", "女优排行榜 (默认最新)")] + FALLBACK_ACTRESS_OPTIONS[1:]

FALLBACK_GENRE_OPTIONS = [
    ("", "全部题材 (默认最新)"),
    ("chinese-subtitle", "中文字幕"),
    ("VR", "VR专区"),
    ("uncensored-leak", "无码流出"),
    ("big-tits", "巨乳"),
    ("beautiful-girl", "美少女"),
    ("married-woman", "人妻"),
    ("mature-woman", "熟女"),
    ("uniform", "制服"),
    ("stockings", "丝袜"),
    ("ol", "OL"),
    ("female-teacher", "女教师"),
    ("nurse", "护士"),
    ("maid", "女仆"),
    ("sailor-suit", "水手服"),
    ("swimsuit", "泳装"),
    ("cosplay", "Cosplay"),
    ("creampie", "中出"),
    ("blowjob", "口交"),
    ("footjob", "足交"),
    ("paizuri", "乳交"),
    ("anal", "肛交"),
    ("3p", "3P"),
    ("group", "群交"),
    ("ntr", "NTR"),
    ("incest", "乱伦"),
    ("rape", "强奸"),
    ("bondage", "捆绑调教"),
    ("lesbian", "女同"),
    ("solo", "单体作品"),
]

FALLBACK_MAKER_OPTIONS = [
    ("", "全部发行商 (默认最新)"),
    ("S1", "S1 NO.1 STYLE"),
    ("MOODYZ", "MOODYZ"),
    ("IdeaPocket", "IDEA POCKET"),
    ("Prestige", "PRESTIGE"),
    ("Premium", "PREMIUM"),
    ("SOD", "SOD Create"),
    ("Madonna", "Madonna"),
    ("Attackers", "ATTACKERS"),
    ("Fitch", "Fitch"),
    ("E-Body", "E-BODY"),
    ("Kawaii", "kawaii*"),
    ("Faleno", "FALENO"),
    ("Dahlia", "DAHLIA"),
    ("Wan", "WANZ FACTORY"),
    ("OPPAI", "OPPAI"),
    ("Honnaka", "本中"),
    ("Das", "DAS"),
    ("Ro", "ROOKIE"),
    ("Tameike", "溜池ゴロー"),
    ("Muku", "无垢"),
]

CLASS_LIST = [
    ("/dm278/cn/chinese-subtitle", "中文字幕"),
    ("/dm539/cn/new", "最近更新"),
    ("/dm635/cn/release", "新作上市"),
    ("/dm817/cn/uncensored-leak", "无码流出"),
    ("filter@@actress", "女优一览"),
    ("filter@@actress_ranking", "女优排行"),
    ("filter@@genre", "全部类型"),
    ("filter@@maker", "全部发行商"),
    ("/cn/genres/VR", "VR专区"),
    ("/dm301/cn/today-hot", "今日热门"),
    ("/dm170/cn/weekly-hot", "本周热门"),
    ("/dm273/cn/monthly-hot", "本月热门"),
    ("/dm597/cn/fc2", "FC2"),
    ("/dm2208642/cn/heyzo", "HEYZO"),
    ("/dm42/cn/tokyohot", "东京热"),
    ("/dm5199603/cn/1pondo", "一本道"),
    ("/dm7704788/cn/caribbeancom", "加勒比"),
    ("/dm91887/cn/caribbeancompr", "加勒比PR"),
    ("/dm7208981/cn/10musume", "天然素人"),
    ("/dm3600557/cn/pacopacomama", "熟女俱乐部"),
    ("/dm150/cn/gachinco", "Gachinco"),
    ("/dm36/cn/siro", "SIRO"),
    ("/dm34/cn/luxu", "LUXU"),
    ("/dm34/cn/gana", "GANA"),
    ("/dm38/cn/scute", "S-CUTE"),
    ("/dm1004/cn/maan", "PRESTIGE"),
    ("/dm34/cn/ara", "ARA"),
    ("/dm33/cn/naughty4610", "顽皮4610"),
    ("/dm37/cn/naughty0930", "顽皮0930"),
    ("/dm63/cn/madou", "麻豆传媒"),
    ("/dm31/cn/twav", "TWAV"),
    ("/dm15/cn/furuke", "Furuke"),
    ("/dm37/cn/marriedslash", "人妻斩"),
    ("/dm42/cn/xxxav", "XXX-AV"),
]

BANNED_SLUGS = {
    "chinese-subtitle": True, "new": True, "release": True,
    "uncensored-leak": True, "today-hot": True, "weekly-hot": True,
    "monthly-hot": True, "genres": True, "actresses": True,
    "makers": True, "series": True, "tags": True, "vip": True,
    "saved": True, "playlists": True, "history": True, "login": True,
    "register": True, "siro": True, "luxu": True, "gana": True,
}

BLOCK_RE = re.compile(r"""<div[^>]+class=["'][^"']*(?:relative\s+group|thumbnail)[^"']*["'][^>]*>([\s\S]*?)(?=<div[^>]+class=["'][^"']*(?:relative\s+group|thumbnail)[^"']*["']|</section>|<footer|<nav\s+aria-label)""", re.I)
LINK_BLOCK_RE = re.compile(r"""<a[^>]+href=["']([^"']*\/(?:cn|dm\d+\/cn)\/([A-Za-z0-9_\-]+))["'][^>]*>([\s\S]*?)</a>""", re.I)
HREF_RE = re.compile(r"""href=["']([^"']*\/(?:cn|dm\d+\/cn)\/([A-Za-z0-9_\-]+))["']""", re.I)
NAME_DIV_RE = re.compile(r"""<div[^>]*class=["'][^"']*(?:title|my-2|font-semibold)[^"']*["'][^>]*>([\s\S]*?)</div>""", re.I)
ALT_RE = re.compile(r"""alt=["']([^"']+)["']""", re.I)
ANCHOR_RE = re.compile(r"<a[^>]*>([\s\S]*?)</a>", re.I)
PIC_RE = re.compile(r"""(?:data-src|data-original|src)=["']([^"']+\.(?:jpg|jpeg|png|webp)[^"']*)["']""", re.I)
DUR_RE = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)")
TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>", re.I)
OG_IMAGE_RE = re.compile(r"""<meta\s+property=["']og:image["']\s+content=["']([^"']+)["']""", re.I)
GENRE_A_RE = re.compile(r"""<a[^>]+href=["'][^"']*\/genres\/[^"']+["'][^>]*>([\s\S]*?)</a>""", re.I)
PACKER_RE = re.compile(r"""\}\s*\(\s*['"]([\s\S]*?)['"]\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*['"]([^'"]+)['"]\.split\(['"]\|['"]\)""")
SRC_1280_RE = re.compile(r"""source1280\s*=\s*['"]([^'"]+)['"]""")
SRC_842_RE = re.compile(r"""source842\s*=\s*['"]([^'"]+)['"]""")
SRC_AUTO_RE = re.compile(r"""source\s*=\s*['"]([^'"]+)['"]""")
DOMAIN_RE = re.compile(r"^https?://(([a-zA-Z0-9\-]+\.)+[a-zA-Z]{2,})/")
ORIGIN_RE = re.compile(r"^(https?://[^/]+)", re.I)
B64_BLOCK_RE = re.compile(r"""["']([A-Za-z0-9+/=]{100,})["']""")
PACKER_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _chr_safe(code):
    try:
        return chr(code)
    except Exception:
        return ""


def decode_entities(text):
    if not text:
        return ""
    t = str(text)
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    t = t.replace("&quot;", '"').replace("&#039;", "'").replace("&apos;", "'")
    t = re.sub(r"&#x([0-9a-fA-F]+);", lambda m: _chr_safe(int(m.group(1), 16)), t)
    t = re.sub(r"&#(\d+);", lambda m: _chr_safe(int(m.group(1))), t)
    return t


def strip_tags(html):
    if not html:
        return ""
    clean = re.sub(r"<[^>]+>", " ", str(html))
    clean = decode_entities(clean)
    return re.sub(r"[\r\n\t\s]+", " ", clean).strip()


def unwrap_html(raw):
    if not raw:
        return ""
    t = str(raw).strip()
    if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
        try:
            dec = json.loads(t)
            if isinstance(dec, str) and dec:
                return dec
        except Exception:
            t = t[1:-1]
    t = t.replace('\\"', '"').replace("\\/", "/")
    t = t.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", " ")
    return t


def resolve_full_url(raw_url, host):
    if not raw_url:
        return ""
    u = str(raw_url).strip().replace("&amp;", "&")
    if u.startswith("//"):
        return "https:" + u
    if u.startswith("/"):
        return host + u
    if not u.startswith("http"):
        return host + "/" + u
    return u


def extract_relative_path(full_url, host):
    u = str(full_url or "").strip()
    if u.startswith(host):
        rel = u[len(host):]
        return rel if rel else "/"
    m = re.match(r"^https?://[^/]+(/.*)$", u, re.I)
    if m and m.group(1):
        return m.group(1)
    return u if u.startswith("/") else ("/" + u)


def format_poster(raw_pic, host):
    if not raw_pic:
        return ""
    full = resolve_full_url(raw_pic, host)
    return full + "@Referer=" + quote(host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % ("蝴蝶影视", clean_meta)
    return "蝴蝶影视"


def _int2base(x, base):
    if x < 0:
        return "-" + _int2base(-x, base)
    res = []
    while x > 0:
        res.append(PACKER_CHARS[x % base])
        x //= base
    return "".join(reversed(res)) if res else "0"


def unpack_packer(p, a, c, k):
    table = {}
    idx = c
    while idx > 0:
        idx -= 1
        key = _int2base(idx, a)
        val = k[idx] if idx < len(k) and k[idx] else key
        table[key] = val
    return re.sub(r"\b\w+\b", lambda m: table.get(m.group(0), m.group(0)), str(p))


def rewrite_domain(url, host):
    return DOMAIN_RE.sub(lambda m: host + "/jmpres/" + m.group(1) + "/", url, count=1)


def _options(pairs):
    return [{"n": name, "v": value} for value, name in pairs]


def _standard_rows():
    return [
        {"key": "sort", "name": "排序", "init": "default", "value": _options(VIDEO_SORT_OPTIONS)},
        {"key": "filters", "name": "过滤", "init": "all", "value": _options(VIDEO_FILTER_OPTIONS)},
    ]


def _slug_rows(label, pairs):
    rows = [{"key": "slug", "name": label, "init": "", "value": _options(pairs)}]
    rows.extend(_standard_rows())
    return rows


def _build_filters():
    filters = {}
    for tid, _name in CLASS_LIST:
        if tid == "filter@@actress":
            filters[tid] = _slug_rows("选择女优", FALLBACK_ACTRESS_OPTIONS)
        elif tid == "filter@@actress_ranking":
            filters[tid] = _slug_rows("热门榜女优", FALLBACK_RANKING_OPTIONS)
        elif tid == "filter@@genre":
            filters[tid] = _slug_rows("选择类型", FALLBACK_GENRE_OPTIONS)
        elif tid == "filter@@maker":
            filters[tid] = _slug_rows("选择发行商", FALLBACK_MAKER_OPTIONS)
        else:
            filters[tid] = _standard_rows()
    return filters


FILTER_MAP = _build_filters()


class Spider(BaseSpider):
    def init(self, extend=""):
        self.host = DEFAULT_HOST
        self._custom_host = False
        self._live_host = ""
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "").strip()
        elif isinstance(extend, str):
            text = extend.strip()
            if text.startswith("{"):
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        custom = str(data.get("host") or "").strip()
                except Exception:
                    custom = ""
            elif text:
                custom = text
        if custom and custom.startswith("http"):
            self.host = custom.rstrip("/")
            self._custom_host = True

    # ---------- fetch layer ----------

    def _fetch_raw(self, url, referer):
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            text = resp.content.decode("utf-8", "ignore") if resp.content else ""
            if 200 <= resp.status_code < 300 and text:
                return resp.status_code, unwrap_html(text), resp.url or url
            return resp.status_code, (unwrap_html(text) if text else ""), url
        except Exception:
            if url.startswith("https://"):
                http_url = "http://" + url[len("https://"):]
                try:
                    resp = requests.get(http_url, headers=headers, timeout=8)
                    text = resp.content.decode("utf-8", "ignore") if resp.content else ""
                    if 200 <= resp.status_code < 300 and text:
                        return resp.status_code, unwrap_html(text), resp.url or http_url
                except Exception:
                    pass
        return 0, "", url

    def _discover_host(self):
        for nav in NAV_URLS:
            _status, text, _url = self._fetch_raw(nav, nav + "/")
            if not text:
                continue
            for m in B64_BLOCK_RE.finditer(text):
                try:
                    decoded = base64.b64decode(m.group(1)).decode("utf-8")
                    unquoted = unquote(decoded)
                except Exception:
                    continue
                if "MissAV" not in unquoted or "[" not in unquoted:
                    continue
                try:
                    site_list = json.loads(unquoted)
                except Exception:
                    continue
                if not isinstance(site_list, list):
                    continue
                for item in site_list:
                    if not isinstance(item, dict) or item.get("name") != "MissAV":
                        continue
                    candidates = []
                    if item.get("url"):
                        candidates.append(item["url"])
                    urls = item.get("urls")
                    if isinstance(urls, list):
                        for entry in urls:
                            if isinstance(entry, dict) and entry.get("url") and entry["url"] not in candidates:
                                candidates.append(entry["url"])
                    for cand in candidates:
                        om = ORIGIN_RE.match(str(cand))
                        if om and om.group(1):
                            base = om.group(1)
                            chk_status, chk_text, _u = self._fetch_raw(base + "/dm247/cn", base + "/")
                            if chk_status == 200 and chk_text:
                                return base
        return DEFAULT_HOST

    def _get_host(self, force=False):
        if self._custom_host:
            return self.host
        if not force and self._live_host:
            return self._live_host
        active = self._discover_host()
        self._live_host = active.rstrip("/")
        self.host = self._live_host
        return self._live_host

    def _fetch_safe(self, path_or_url, custom_referer=""):
        host = self._get_host()
        url = resolve_full_url(path_or_url, host)
        ref = custom_referer if custom_referer else (host + "/dm247/cn")
        status, text, final_url = self._fetch_raw(url, ref)
        if (status in (0, 404, 502, 503) or not text) and not self._custom_host:
            refreshed = self._get_host(force=True)
            if refreshed and refreshed != host:
                retry_url = ORIGIN_RE.sub(refreshed, url, count=1)
                _s, retry_text, retry_final = self._fetch_raw(retry_url, refreshed + "/dm247/cn")
                return retry_text, refreshed, retry_final
        return text, host, final_url

    # ---------- card parsing ----------

    def _parse_cards(self, html_text, host):
        items = []
        if not html_text:
            return items
        body = html_text
        if "</nav>" in body:
            body = body.split("</nav>", 1)[1]
        elif "</header>" in body:
            body = body.split("</header>", 1)[1]

        blocks = BLOCK_RE.findall(body)
        if not blocks:
            blocks = [m.group(0) for m in LINK_BLOCK_RE.finditer(body)]

        seen = {}
        for chunk in blocks:
            if not chunk:
                continue
            href_match = HREF_RE.search(chunk)
            if not href_match:
                continue
            raw_href = href_match.group(1).strip()
            dvd_id = href_match.group(2).strip()
            dvd_low = dvd_id.lower()
            if BANNED_SLUGS.get(dvd_low) or seen.get(dvd_low) or len(dvd_id) < 3:
                continue

            vod_name = ""
            name_match = NAME_DIV_RE.search(chunk)
            if name_match:
                cand = strip_tags(name_match.group(1))
                if cand and cand.lower() != dvd_low and len(cand) >= len(dvd_id):
                    vod_name = cand
            if not vod_name:
                alt_match = ALT_RE.search(chunk)
                if alt_match:
                    cand_alt = decode_entities(alt_match.group(1)).strip()
                    if cand_alt and cand_alt.lower() != dvd_low and len(cand_alt) >= len(dvd_id):
                        vod_name = cand_alt
            if not vod_name:
                for am in ANCHOR_RE.finditer(chunk):
                    t_str = strip_tags(am.group(1))
                    if t_str and t_str.lower() != dvd_low and len(t_str) > len(dvd_id):
                        if ("item." not in t_str and "HD" not in t_str and "FHD" not in t_str
                                and "4K" not in t_str and ":" not in t_str and "条影片" not in t_str):
                            vod_name = t_str
                            break
            if not vod_name:
                vod_name = dvd_id.upper()

            raw_pic = ""
            pic_match = PIC_RE.search(chunk)
            if pic_match and "item.dvd_id" not in pic_match.group(1):
                raw_pic = pic_match.group(1).strip()
            else:
                raw_pic = FALLBACK_PIC_HOST + "/" + dvd_low + "/cover-n.jpg"

            dur_match = DUR_RE.search(chunk)
            remarks = format_remarks(dur_match.group(1) if dur_match else "")

            full_url = resolve_full_url(raw_href, host)
            stable_path = extract_relative_path(full_url, host)

            seen[dvd_low] = True
            items.append({
                "vod_id": stable_path,
                "vod_name": vod_name,
                "vod_pic": format_poster(raw_pic, host),
                "vod_remarks": remarks,
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

    def _brand_block(self, host):
        return "\n".join([
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ])

    # ---------- FongMi entry points ----------

    def homeContent(self, filter):
        classes = [{"type_id": tid, "type_name": name} for tid, name in CLASS_LIST]
        result = {"class": classes}
        if filter:
            result["filters"] = FILTER_MAP
        return result

    def homeVideoContent(self):
        text, host, _f = self._fetch_safe("/dm539/cn/new")
        return {"list": self._parse_cards(text, host)}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        extend = extend or {}
        slug = str(extend.get("slug") or "").strip()
        sort = str(extend.get("sort") or "")
        filt = str(extend.get("filters") or "")

        if tid in ("filter@@actress", "filter@@actress_ranking"):
            target = ("/cn/actresses/" + quote(slug, safe="")) if slug else "/dm539/cn/new"
        elif tid == "filter@@genre":
            target = ("/cn/genres/" + quote(slug, safe="")) if slug else "/dm539/cn/new"
        elif tid == "filter@@maker":
            target = ("/cn/makers/" + quote(slug, safe="")) if slug else "/dm539/cn/new"
        else:
            target = str(tid or "").rstrip("/")
            if target and not target.startswith("/") and not target.startswith("http"):
                target = "/" + target
            if not target:
                target = "/dm539/cn/new"

        parts = []
        if page > 1:
            parts.append("page=" + str(page))
        if sort and sort != "default":
            parts.append("sort=" + quote(sort, safe=""))
        if filt and filt != "all":
            parts.append("filters=" + quote(filt, safe=""))
        if parts:
            sep = "&" if "?" in target else "?"
            target = target + sep + "&".join(parts)

        text, host, _f = self._fetch_safe(target)
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
        path = "/cn/search/" + quote(keyword, safe="")
        if page > 1:
            path = path + "?page=" + str(page)
        text, host, _f = self._fetch_safe(path)
        return self._page_form(self._parse_cards(text, host), page)

    def detailContent(self, ids):
        vod_id = str(ids[0]) if ids else ""
        target_path = vod_id.strip()
        if not target_path:
            return {"list": []}
        text, host, _f = self._fetch_safe(target_path)
        if not text:
            return {"list": []}
        detail_url = resolve_full_url(target_path, host)

        title_match = TITLE_RE.search(text)
        raw_title = strip_tags(title_match.group(1)) if title_match else "精彩视频"
        vod_name = raw_title.split(" - ")[0].split(" | ")[0].strip()
        if not vod_name:
            vod_name = "精彩视频"

        poster_match = OG_IMAGE_RE.search(text)
        raw_pic = poster_match.group(1).strip() if poster_match else ""
        poster = format_poster(raw_pic, host)

        genres = []
        for gm in GENRE_A_RE.finditer(text):
            g_name = strip_tags(gm.group(1))
            if g_name and "全部" not in g_name and g_name not in genres:
                genres.append(g_name)

        sources = []
        packer_match = PACKER_RE.search(text)
        if packer_match:
            try:
                a_val = int(packer_match.group(2))
                c_val = int(packer_match.group(3))
            except Exception:
                a_val = 0
                c_val = 0
            if a_val and c_val:
                unpacked = unpack_packer(packer_match.group(1), a_val, c_val, packer_match.group(4).split("|"))
                unpacked = unpacked.replace("\\'", "'")
                for src_re, line_name in (
                    (SRC_1280_RE, "🦋 1080P超清"),
                    (SRC_842_RE, "🦋 720P高清"),
                    (SRC_AUTO_RE, "🦋 自适应线路"),
                ):
                    sm = src_re.search(unpacked)
                    if sm and sm.group(1) and "sample" not in sm.group(1) and "preview" not in sm.group(1):
                        play_url = rewrite_domain(sm.group(1), host)
                        sources.append((line_name, {
                            "playUrl": play_url,
                            "detailUrl": detail_url,
                            "isDirect": True,
                        }))
        if not sources:
            sources.append(("🦋 官方原线", {
                "playUrl": detail_url,
                "detailUrl": detail_url,
                "isDirect": False,
            }))

        play_from = "$$$".join(name for name, _env in sources)
        play_url = "$$$".join(
            "正片$" + json.dumps(env, ensure_ascii=False) for _name, env in sources
        )

        dvd_id = target_path.rstrip("/").split("/")[-1]
        content_lines = [self._brand_block(host)]
        content_lines.append("标题：" + vod_name)
        content_lines.append("分类：" + "、".join(genres))
        content_lines.append("片源：" + sources[0][0])
        content_lines.append("编号：" + dvd_id)
        vod_content = "\n".join(content_lines)

        vod = {
            "vod_id": vod_id,
            "vod_name": vod_name,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": VOD_ACTOR,
            "vod_director": VOD_DIRECTOR,
            "vod_type": "、".join(genres),
            "vod_remarks": "蝴蝶影视",
            "vod_content": vod_content,
            "vod_play_from": play_from,
            "vod_play_url": play_url,
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        host = self._get_host()
        play_url = ""
        detail_url = ""
        is_direct_flag = False
        env = None
        if isinstance(id, str) and id.startswith("{"):
            try:
                parsed = json.loads(id)
                if isinstance(parsed, dict):
                    env = parsed
            except Exception:
                env = None
        if env is not None:
            play_url = str(env.get("playUrl") or "").strip()
            detail_url = str(env.get("detailUrl") or "").strip()
            is_direct_flag = bool(env.get("isDirect"))
        elif id:
            play_url = resolve_full_url(id, host)
        if not detail_url:
            detail_url = host + "/"
        if not play_url:
            return {
                "parse": 1,
                "url": detail_url,
                "header": {"User-Agent": UA, "Referer": host + "/"},
            }
        low = play_url.lower()
        is_direct = is_direct_flag or (".m3u8" in low) or (".mp4" in low)
        if is_direct:
            final_url = play_url
            if ".m3u8" not in low and ".mp4" not in low:
                sep = "&" if "?" in final_url else "?"
                final_url = final_url + sep + "format=.m3u8"
            return {
                "parse": 0,
                "url": final_url,
                "header": {"User-Agent": UA, "Referer": detail_url, "Origin": host},
            }
        return {
            "parse": 1,
            "url": play_url,
            "header": {"User-Agent": UA, "Referer": host + "/"},
        }

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250209462&sig=78b0f66c6e7c09d5
