# rouAV spider for FongMi / TVBox
# com.butterfly.rouav
import base64
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
DEFAULT_HOST = "https://rou123.ws"
NAV_URLS = ["https://x99dh.net", "https://x99dh.lat"]
TARGET_SITE_NAME = "rouav"
SITE_NAME = "rouAV"
BRAND = "蝴蝶影视"
PAGE_SIZE = 20
PIC_RATIO = 1.78
LINE_NAME = "🦋 肉视频自愈线"
RELATED_NAME = "相关推荐"
TG_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"

CATEGORIES = [
    ("7", "国产AV"),
    ("3", "日本"),
    ("6", "自拍流出"),
    ("5", "探花"),
    ("4", "OnlyFans"),
    ("1", "其他"),
]
CAT_NAME_SET = set(name for _cid, name in CATEGORIES)

CARD_RE = re.compile(
    r'<div[^>]+class=["\'][^"\']*(?:col-|myui-vodlist__box|item)[^"\']*["\'][^>]*>([\s\S]*?)'
    r'(?=<div[^>]+class=["\'][^"\']*(?:col-|myui-vodlist__box|item)[^"\']*["\']|</ul>|</section>|<footer|<div[^>]+class=["\'][^"\']*page)',
    re.I,
)
LINK_FALLBACK_RE = re.compile(r'<a[^>]+href=["\'](/vodplay/\d+-[\d\-]+?\.html)["\'][^>]*>([\s\S]*?)</a>', re.I)
LINK_RE = re.compile(r'<a[^>]+href=["\'](/vodplay/\d+-[\d\-]+?\.html)["\'][^>]*>([\s\S]*?)</a>', re.I)
PIC_RE = re.compile(r'(?:data-original|data-src|src)=["\']([^"\']+)["\']', re.I)
TITLE_ATTR_RE = re.compile(r'(?:title|alt)=["\']([^"\']+)["\']', re.I)
HEADING_RE = re.compile(
    r'<(?:h[2-6]|p|div)[^>]+class=["\'][^"\']*(?:title|name)[^"\']*["\'][^>]*>([\s\S]*?)</(?:h[2-6]|p|div)>',
    re.I,
)
DURATION_FULL_RE = re.compile(r'^\d+:\d+$')
DURATION_LINE_RE = re.compile(r'^\d+:\d+(?::\d+)?$')
DATE_TEXT_RE = re.compile(r'\d+月\d+日')
PLAYER_RE = re.compile(r'<script[^>]*>\s*var\s+player_aaaa\s*=\s*(\{[\s\S]*?\})\s*</script>', re.I)
API_ROUTE_RE = re.compile(r'["\'](/api/v/[a-zA-Z0-9_\-]+)["\']')
OG_IMAGE_RE = re.compile(r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', re.I)
DATA_ORIGINAL_RE = re.compile(r'data-original=["\']([^"\']+)["\']', re.I)
H1_RE = re.compile(r'<h1[^>]*>([\s\S]*?)</h1>', re.I)
TITLE_TAG_RE = re.compile(r'<title>([\s\S]*?)</title>', re.I)
B64_BLOB_RE = re.compile(r'["\']([A-Za-z0-9+/=]{100,})["\']')
ORIGIN_RE = re.compile(r'^(https?://[^/]+)', re.I)
TYPE_META_RE = re.compile(r'类型：([^<]+)')
VOD_NUM_RE = re.compile(r'/vodplay/(\d+)')
HEX_ENTITY_RE = re.compile(r'&#x([0-9a-fA-F]+);')
DEC_ENTITY_RE = re.compile(r'&#(\d+);')


def decode_entities(text):
    if not text:
        return ""
    out = str(text)
    out = out.replace("&amp;", "&")
    out = out.replace("&lt;", "<")
    out = out.replace("&gt;", ">")
    out = out.replace("&quot;", '"')
    out = out.replace("&#039;", "'")
    out = out.replace("&apos;", "'")
    out = HEX_ENTITY_RE.sub(lambda m: chr(int(m.group(1), 16)), out)
    out = DEC_ENTITY_RE.sub(lambda m: chr(int(m.group(1), 10)), out)
    return out


def strip_tags(html_text):
    if not html_text:
        return ""
    clean = re.sub(r"<[^>]+>", " ", str(html_text))
    clean = decode_entities(clean)
    return re.sub(r"[\r\n\t\s]+", " ", clean).strip()


def unwrap_html(raw_text):
    if not raw_text:
        return ""
    text = str(raw_text).strip()
    if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
        try:
            dec = json.loads(text)
            if isinstance(dec, str) and dec:
                return dec
        except Exception:
            text = text[1:-1]
    text = text.replace('\\"', '"')
    text = text.replace("\\/", "/")
    text = text.replace("\\r\\n", "\n")
    text = text.replace("\\n", "\n")
    text = text.replace("\\t", " ")
    return text


def resolve_full_url(raw_url, host):
    if not raw_url:
        return ""
    url = str(raw_url).strip().replace("&amp;", "&")
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("/"):
        return host + url
    if not url.startswith("http"):
        return host + "/" + url
    return url


def format_poster(raw_pic, host):
    if not raw_pic:
        return ""
    full = resolve_full_url(raw_pic, host)
    if full.startswith("data:image"):
        return ""
    return full + "@Referer=" + quote(host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND, clean_meta)
    return BRAND


def sanitize_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST
        self.custom_host = ""
        self.live_host = ""

    # ---------- lifecycle ----------

    def init(self, extend=""):
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "").strip()
        elif isinstance(extend, str) and extend.strip():
            text = extend.strip()
            if text.startswith("{"):
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        custom = str(data.get("host") or "").strip()
                except Exception:
                    custom = ""
            else:
                custom = text
        if custom and custom.startswith("http"):
            self.custom_host = custom.rstrip("/")

    def destroy(self):
        pass

    # ---------- host discovery (JS getHost / discoverActiveHost) ----------

    def _effective_host(self, force=False):
        if self.custom_host:
            return self.custom_host
        if not force and self.live_host:
            return self.live_host
        host = self._discover_host()
        self.live_host = host.rstrip("/")
        return self.live_host

    def _discover_host(self):
        for nav in NAV_URLS:
            res = self._fetch_raw(nav, nav + "/")
            html_text = res.get("text") or ""
            if not html_text:
                continue
            for match in B64_BLOB_RE.finditer(html_text):
                origin = self._origin_from_blob(match.group(1))
                if origin:
                    return origin
        return DEFAULT_HOST

    def _origin_from_blob(self, blob):
        try:
            decoded = base64.b64decode(blob).decode("utf-8")
            unquoted = unquote(decoded)
        except Exception:
            return ""
        lowered = unquoted.lower()
        if "[" not in unquoted or "{" not in unquoted or TARGET_SITE_NAME not in lowered:
            return ""
        try:
            site_list = json.loads(unquoted)
        except Exception:
            return ""
        if not isinstance(site_list, list):
            return ""
        for item in site_list:
            if not isinstance(item, dict):
                continue
            if str(item.get("name") or "").strip().lower() == TARGET_SITE_NAME and item.get("url"):
                m = ORIGIN_RE.match(str(item.get("url")).strip())
                if m:
                    return m.group(1)
        return ""

    # ---------- http (JS fetchRawUrl / fetchSafeHtml) ----------

    def _fetch_raw(self, target_url, referer):
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else target_url,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        result = self._fetch_once(target_url, headers)
        if result is not None:
            return result
        if target_url.startswith("https://"):
            http_url = "http://" + target_url[8:]
            result = self._fetch_once(http_url, headers)
            if result is not None:
                return result
        return {"status": 0, "text": "", "url": target_url}

    def _fetch_once(self, target_url, headers):
        try:
            resp = requests.get(target_url, headers=headers, timeout=8)
        except Exception:
            return None
        body = resp.text if resp is not None else ""
        return {
            "status": resp.status_code if resp is not None else 0,
            "text": unwrap_html(body) if body else "",
            "url": resp.url if resp is not None and resp.url else target_url,
        }

    def _fetch_safe(self, path_or_url, referer=""):
        host = self._effective_host()
        target_url = resolve_full_url(path_or_url, host)
        ref = referer if referer else host + "/"
        res = self._fetch_raw(target_url, ref)
        bad = res.get("status") in (0, 404, 451, 502, 503) or not res.get("text")
        if bad and not self.custom_host:
            refreshed = self._effective_host(force=True)
            if refreshed and refreshed != host:
                retry_url = ORIGIN_RE.sub(refreshed, target_url, count=1)
                retry = self._fetch_raw(retry_url, refreshed + "/")
                return retry.get("text") or "", refreshed
        return res.get("text") or "", host

    # ---------- card parsing (JS parseVodCards / parseCardTitle) ----------

    def _card_title(self, inner_html, chunk):
        attr = TITLE_ATTR_RE.search(inner_html or "")
        if attr and attr.group(1):
            val = decode_entities(attr.group(1)).strip()
            if len(val) > 2 and not DURATION_FULL_RE.match(val) and not DATE_TEXT_RE.search(val):
                return val
        heading = HEADING_RE.search(chunk or "")
        if heading and heading.group(1):
            val2 = strip_tags(heading.group(1))
            if val2 and not DATE_TEXT_RE.search(val2):
                return val2
        raw = re.sub(r"<[^>]+>", "\n", str(chunk or inner_html or ""))
        raw = decode_entities(raw)
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            if DURATION_LINE_RE.match(line):
                continue
            if DATE_TEXT_RE.search(line) or " | " in line:
                continue
            if line in CAT_NAME_SET or line == "HD" or line == "高清":
                continue
            return line
        return "肉视频"

    def _parse_card_items(self, html_text, host):
        items = []
        if not html_text:
            return items
        blocks = [m.group(1) for m in CARD_RE.finditer(html_text)]
        if not blocks:
            blocks = [m.group(0) for m in LINK_FALLBACK_RE.finditer(html_text)]
        seen = set()
        for chunk in blocks:
            if not chunk:
                continue
            link = LINK_RE.search(chunk)
            if not link:
                continue
            href = link.group(1).strip()
            if not href or href in seen:
                continue
            pic = PIC_RE.search(chunk)
            if not pic or not pic.group(1):
                continue
            raw_pic = pic.group(1).strip()
            title = self._card_title(link.group(2) or "", chunk)
            seen.add(href)
            items.append({"path": href, "title": title, "raw_pic": raw_pic})
        return items

    def _parse_cards(self, html_text, host):
        cards = []
        for item in self._parse_card_items(html_text, host):
            vod_id = "%s@@%s@@%s" % (item["path"], quote(item["title"], safe=""), quote(item["raw_pic"], safe=""))
            cards.append({
                "vod_id": vod_id,
                "vod_name": item["title"],
                "vod_pic": format_poster(item["raw_pic"], host),
                "vod_remarks": format_remarks(),
                "style": {"type": "rect", "ratio": PIC_RATIO},
            })
        return cards

    # ---------- shared page form ----------

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
        if page < 1:
            page = 1
        return page

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": name} for cid, name in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        text, host = self._fetch_safe("/vodtype/7.html")
        return {"list": self._parse_cards(text, host)}

    def categoryContent(self, tid, pg, filter, extend):
        cid = str(tid or "").strip("/")
        if not cid:
            cid = "7"
        page = self._to_page(pg)
        if page > 1:
            path = "/vodtype/%s-%d.html" % (cid, page)
        else:
            path = "/vodtype/%s.html" % cid
        text, host = self._fetch_safe(path)
        return self._page_form(self._parse_cards(text, host), page)

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = self._to_page(pg)
        if not keyword:
            return self._page_form([], page)
        encoded = quote(keyword, safe="")
        if page > 1:
            path = "/vodsearch/" + encoded + "-" * 10 + str(page) + "-" * 3 + ".html"
        else:
            path = "/vodsearch/" + "-" * 13 + ".html?wd=" + encoded
        text, host = self._fetch_safe(path)
        return self._page_form(self._parse_cards(text, host), page)

    # ---------- detail ----------

    def _brand_block(self, host):
        lines = [
            "🦋 %s官方交流群：@tvshare23" % SITE_NAME,
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _fetch_api_hls(self, dispatch_url, detail_url, host):
        res = self._fetch_raw(dispatch_url, detail_url)
        text = res.get("text") or ""
        if not text:
            return ""
        try:
            data = json.loads(text)
        except Exception:
            return ""
        video = data.get("video") if isinstance(data, dict) else None
        v_url = str(video.get("videoUrl") or "").strip() if isinstance(video, dict) else ""
        if v_url:
            return resolve_full_url(v_url, host)
        return ""

    def _detail_vod(self, raw_path, ref_title, ref_pic):
        play_path = raw_path if raw_path.startswith("/") else "/" + raw_path
        text, host = self._fetch_safe(play_path)
        if not text:
            return None
        detail_url = resolve_full_url(play_path, host)

        vod_name = str(ref_title or "").strip()
        h1 = H1_RE.search(text)
        if h1 and h1.group(1):
            clean_h1 = strip_tags(h1.group(1))
            if clean_h1:
                vod_name = clean_h1
        if not vod_name:
            tag = TITLE_TAG_RE.search(text)
            if tag and tag.group(1):
                vod_name = strip_tags(tag.group(1)).split("-")[0].strip()
        if not vod_name:
            vod_name = "肉视频"
        vod_name = decode_entities(vod_name)

        raw_pic = str(ref_pic or "").strip()
        if not raw_pic:
            og = OG_IMAGE_RE.search(text) or DATA_ORIGINAL_RE.search(text)
            if og and og.group(1):
                raw_pic = og.group(1).strip()
        poster = format_poster(raw_pic, host)

        api_route = ""
        player = PLAYER_RE.search(text)
        if player and player.group(1):
            try:
                p_info = json.loads(player.group(1))
                b64_url = str(p_info.get("url") or "").strip() if isinstance(p_info, dict) else ""
                if b64_url:
                    decoded = base64.b64decode(b64_url).decode("utf-8")
                    url_json = json.loads(decoded)
                    ss = url_json.get("ss") if isinstance(url_json, dict) else None
                    if isinstance(ss, list) and ss and isinstance(ss[0], list) and len(ss[0]) > 1:
                        api_route = str(ss[0][1]).strip()
            except Exception:
                api_route = ""
        if not api_route:
            api_match = API_ROUTE_RE.search(text)
            if api_match and api_match.group(1):
                api_route = api_match.group(1).strip()

        dispatch_url = resolve_full_url(api_route, host) if api_route else detail_url
        pre_hls = ""
        if "/api/v/" in dispatch_url:
            pre_hls = self._fetch_api_hls(dispatch_url, detail_url, host)

        type_match = TYPE_META_RE.search(text)
        type_text = type_match.group(1).strip() if type_match else ""
        num_match = VOD_NUM_RE.search(play_path)
        vod_num = num_match.group(1) if num_match else play_path

        rel_eps = []
        rel_titles = []
        marker = text.find("相关推荐")
        if marker >= 0:
            for item in self._parse_card_items(text[marker:], host):
                if item["path"] == play_path:
                    continue
                rel_eps.append("%s$rel:%s" % (sanitize_ep_name(item["title"]), item["path"]))
                rel_titles.append(item["title"])

        envelope = json.dumps(
            {"hls": pre_hls, "dispatch": dispatch_url, "detail": detail_url},
            ensure_ascii=False,
        )
        play_from_parts = [LINE_NAME]
        play_url_parts = ["正片$" + envelope]
        if rel_eps:
            play_from_parts.append(RELATED_NAME)
            play_url_parts.append("#".join(rel_eps))

        summary_lines = [self._brand_block(host)]
        summary_lines.append("标题：" + vod_name)
        summary_lines.append("分类：" + type_text)
        summary_lines.append("片源：" + LINE_NAME)
        summary_lines.append("编号：" + vod_num)
        if rel_titles:
            summary_lines.append("相关推荐：" + "、".join(rel_titles[:6]))

        return {
            "vod_id": play_path,
            "vod_name": vod_name,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": TG_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks(),
            "vod_content": "\n".join(summary_lines),
            "vod_play_from": "$$$".join(play_from_parts),
            "vod_play_url": "$$$".join(play_url_parts),
            "style": {"type": "rect", "ratio": PIC_RATIO},
        }

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        raw = str(ids[0] or "")
        parts = raw.split("@@")
        path = parts[0]
        ref_title = unquote(parts[1]) if len(parts) > 1 else ""
        ref_pic = unquote(parts[2]) if len(parts) > 2 else ""
        if not path:
            return {"list": []}
        vod = self._detail_vod(path, ref_title, ref_pic)
        if vod is None:
            return {"list": []}
        return {"list": [vod]}

    # ---------- player ----------

    def _resolve_envelope(self, env):
        host = self._effective_host()
        final = str(env.get("hls") or "").strip()
        dispatch = str(env.get("dispatch") or "").strip()
        detail = str(env.get("detail") or "").strip() or host + "/"
        if not final and dispatch and "/api/v/" in dispatch:
            final = self._fetch_api_hls(dispatch, detail, host)
        if not final:
            final = dispatch
        headers = {"User-Agent": UA, "Referer": host + "/"}
        return {"parse": 0, "url": final, "header": headers}

    def playerContent(self, flag, id, vipFlags):
        host = self._effective_host()
        vid = str(id or "")
        if vid.startswith("rel:"):
            target = vid[4:]
            vod = self._detail_vod(target, "", "")
            if vod is not None:
                first_line = str(vod.get("vod_play_url") or "").split("$$$")[0]
                first_ep = first_line.split("#")[0]
                if "$" in first_ep:
                    payload = first_ep.split("$", 1)[1]
                    try:
                        env = json.loads(payload)
                        if isinstance(env, dict):
                            return self._resolve_envelope(env)
                    except Exception:
                        pass
            return {"parse": 1, "url": resolve_full_url(target, host), "header": {"User-Agent": UA, "Referer": host + "/"}}
        if vid.startswith("{"):
            try:
                env = json.loads(vid)
                if isinstance(env, dict):
                    return self._resolve_envelope(env)
            except Exception:
                pass
        final = resolve_full_url(vid, host) if vid else host + "/"
        return {"parse": 0, "url": final, "header": {"User-Agent": UA, "Referer": host + "/"}}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250164625&sig=1e7aeba355e13e1f
