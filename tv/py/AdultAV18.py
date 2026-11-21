# AdultAV - FongMi Python Spider
# com.butterfly.adultpornaav

import base64
import json
import re
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
DEFAULT_HOST = "https://www.adultporna-av107.com"
SITE_NAME = "AdultAV"
PAGE_SIZE = 50
CARD_RATIO = 1.78
BRAND = "蝴蝶影视"
VOD_ACTOR = "🦋 TG群: @tvshare23"
VOD_DIRECTOR = "🦋 蝴蝶影视"
WASH_HOST = base64.b64decode("Y2xlYW4uNTU2ODk5OS5jYy5jZA==").decode("ascii")

CLASSES = [
    ("每日最新", "/topic/"),
    ("国产视频", "/t/163/"),
    ("网曝黑料", "/t/232/"),
    ("主播大秀", "/t/236/"),
    ("AV解说", "/t/233/"),
    ("国产自拍", "/t/48/"),
    ("抖阴视频", "/t/231/"),
    ("空姐模特", "/t/67/"),
    ("91制片厂", "/t/131/"),
    ("糖心VLOG", "/t/128/"),
]

CARD_RE = re.compile(r"""<a\s+href=["']/voddetail/(\d+)/?["']\s+title=["']([^"']*)["']\s+class=["']img-box[^"']*["'][^>]*>([\s\S]*?)</a>""", re.I)
IMG_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.I)
SMALL_RE = re.compile(r"""<small[^>]*>([\s\S]*?)</small>""", re.I)
H1_RE = re.compile(r"""<h1[^>]*>([\s\S]*?)</h1>""", re.I)
DETAIL_PIC_RE = re.compile(r"""detail-image-wrapper[^>]*>\s*<img[^>]+src=["']([^"']+)["']""", re.I)
CRUMB_RE = re.compile(r"""当前位置[\s\S]{0,600}?<a\s+href=["']/t/\d+/["'][^>]*>([^<]+)</a>""", re.I)
PLAYER_JSON_RE = re.compile(r"""player_aaaa\s*=\s*(\{[\s\S]*?\})\s*<""", re.I)
PLAYER_JSON_RE2 = re.compile(r"""player_aaaa\s*=\s*(\{[\s\S]*?\})""", re.I)
PLAYER_URL_RE = re.compile(r"""["']url["']\s*:\s*["']([^"']+)["']""")
MEDIA_SCAN_RE = re.compile(r"""https?://[^\s"'<>]+\.(?:m3u8|mp4)(?:\?[^\s"'<>]*)?""", re.I)
MEDIA_FULL_RE = re.compile(r"""\.(?:m3u8|mp4|flv|mkv|mov)(?:\?|$)""", re.I)
M3U8_RE = re.compile(r"""\.m3u8(?:\?|$)""", re.I)
NUM_ENTITY_RE = re.compile(r"""&#(\d+);""")


def _unescape_html(s):
    s = str(s or "")
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#39;", "'").replace("&#039;", "'")
    s = s.replace("&nbsp;", " ")

    def _num(m):
        try:
            return chr(int(m.group(1)))
        except Exception:
            return m.group(0)

    return NUM_ENTITY_RE.sub(_num, s)


def _clean_text(s):
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    s = _unescape_html(s)
    return re.sub(r"\s+", " ", s).strip()


def _origin_of(u):
    m = re.match(r"^(https?://[^/]+)", str(u or ""), re.I)
    return m.group(1) if m else ""


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND, clean_meta)
    return BRAND


class Spider(BaseSpider):
    def init(self, extend=""):
        self.host = DEFAULT_HOST
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "").strip()
        elif extend:
            text = str(extend).strip()
            if text.startswith("{"):
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        custom = str(data.get("host") or "").strip()
                except Exception:
                    custom = ""
            elif text.startswith("http"):
                custom = text
        if custom.startswith("http"):
            self.host = custom.rstrip("/")

    # ---------- network ----------

    def _fetch(self, target, referer=""):
        full = str(target or "")
        if full.startswith("//"):
            full = "https:" + full
        elif full.startswith("/"):
            full = self.host + full
        headers = {
            "User-Agent": UA,
            "Referer": referer or (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(full, headers=headers, timeout=8)
            text = resp.content.decode("utf-8", "replace") if resp.content else ""
            final_host = _origin_of(resp.url) or self.host
            return text, final_host
        except Exception:
            return "", self.host

    def _abs_url(self, u, host):
        u = str(u or "").strip().replace("\\/", "/")
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("http"):
            return u
        base = host or self.host
        if u.startswith("/"):
            return base + u
        return base + "/" + u

    def _is_media(self, u):
        return bool(MEDIA_FULL_RE.search(str(u or "")))

    def _first_media(self, html):
        m = MEDIA_SCAN_RE.search(str(html or "").replace("\\/", "/"))
        return m.group(0) if m else ""

    # ---------- cards ----------

    def _parse_list(self, html, host):
        items = []
        seen = set()
        for m in CARD_RE.finditer(str(html or "")):
            vid = m.group(1)
            if vid in seen:
                continue
            seen.add(vid)
            block = m.group(3)
            im = IMG_RE.search(block)
            sm = SMALL_RE.search(block)
            poster = self._abs_url(im.group(1), host) if im else ""
            title = _clean_text(m.group(2)) or vid
            meta = _clean_text(sm.group(1)) if sm else ""
            items.append(self._card(vid, title, poster, meta))
        return items

    def _card(self, vid, title, poster, meta):
        vod_id = vid
        if poster:
            vod_id = "%s@@%s" % (vid, quote(poster, safe=""))
        return {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": format_remarks(meta if meta else "高清"),
            "style": {"type": "rect", "ratio": CARD_RATIO},
        }

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
        return page if page >= 1 else 1

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": tid, "type_name": name} for name, tid in CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        text, host = self._fetch("/zzzz")
        items = self._parse_list(text, host)
        if not items:
            text, host = self._fetch("/topic/")
            items = self._parse_list(text, host)
        return {"list": items}

    def _norm_tid(self, s):
        t = str(s or "")
        for _ in range(3):
            try:
                d = unquote(t)
            except Exception:
                break
            if d == t:
                break
            t = d
        return t

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        t = self._norm_tid(tid or "/topic/")
        if not t.startswith("/"):
            t = "/t/" + t.strip("/") + "/"
        if t == "/topic/" and page > 1:
            return self._page_form([], page)
        path = t
        if page > 1:
            path = path.rstrip("/") + "/page/" + str(page) + "/"
        text, host = self._fetch(path)
        return self._page_form(self._parse_list(text, host), page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        kw = str(key or "").strip()
        if not kw:
            return self._page_form([], page)
        if page > 1:
            path = "/s/page/" + str(page) + "/?wd=" + quote(kw, safe="")
        else:
            path = "/s/?wd=" + quote(kw, safe="")
        text, host = self._fetch(path)
        return self._page_form(self._parse_list(text, host), page)

    # ---------- detail ----------

    def _related_cards(self, html, self_vid):
        idx = str(html or "").find("info-xg-box")
        if idx < 0:
            return []
        start = str(html).rfind("<div", 0, idx)
        if start < 0:
            return []
        depth = 0
        seg = str(html)[start:]
        end = len(seg)
        for m in re.finditer(r"<div\b|</div>", seg):
            if m.group(0) == "</div>":
                depth -= 1
                if depth == 0:
                    end = m.end()
                    break
            else:
                depth += 1
        cards = self._parse_list(seg[:end], self.host)
        out = []
        for c in cards:
            cid = str(c.get("vod_id") or "").split("@@")[0]
            if cid and cid != self_vid:
                out.append(c)
        return out

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return lines

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        parts = raw.split("@@")
        vid = parts[0].strip().strip("/").split("/")[-1]
        ref_poster = unquote(parts[1]) if len(parts) > 1 else ""
        if not vid:
            return {"list": []}
        text, host = self._fetch("/voddetail/" + vid + "/")
        h = text or ""

        name = ""
        hm = H1_RE.search(h)
        if hm:
            name = re.sub(r"-cd\d+$", "", _clean_text(hm.group(1)), flags=re.I)
        if not name:
            name = vid

        poster = ""
        pm = DETAIL_PIC_RE.search(h)
        if pm:
            poster = self._abs_url(pm.group(1), host)
        if not poster:
            poster = ref_poster

        cat_name = ""
        cm = CRUMB_RE.search(h)
        if cm:
            cat_name = _clean_text(cm.group(1))

        ep_re = re.compile(
            r"""class=["']vod-episode-link[^"']*["'][^>]*href=["'](/v/"""
            + re.escape(vid)
            + r"""-(\d+)-(\d+)/?)["']""",
            re.I,
        )
        by_line = {}
        order = []
        for m in ep_re.finditer(h):
            sid = m.group(2)
            nid = m.group(3)
            if sid not in by_line:
                by_line[sid] = []
                order.append(sid)
            if not any(e[0] == nid for e in by_line[sid]):
                by_line[sid].append((nid, m.group(1)))
        if not order:
            by_line["1"] = [("1", "/v/" + vid + "/")]
            order = ["1"]

        play_from = []
        play_url = []
        for sid in order:
            eps = sorted(by_line[sid], key=lambda e: int(e[0]))
            multi = len(eps) > 1
            ep_strs = []
            for nid, path in eps:
                ep_name = ("第" + nid + "集") if multi else "正片"
                ep_name = ep_name.replace("$", "_").replace("#", "_")
                env = json.dumps({"pageUrl": self._abs_url(path, host)})
                ep_strs.append("%s$%s" % (ep_name, env))
            play_from.append("🦋 蝴蝶专线 " + sid)
            play_url.append("#".join(ep_strs))

        related = self._related_cards(h, vid)
        if related:
            rel_eps = []
            for c in related:
                rid = str(c.get("vod_id") or "").split("@@")[0]
                rname = str(c.get("vod_name") or rid).replace("$", "_").replace("#", "_")
                rel_eps.append("%s$rel:%s" % (rname, rid))
            play_from.append("相关推荐")
            play_url.append("#".join(rel_eps))

        content_lines = self._brand_block()
        content_lines.append("标题：" + name)
        content_lines.append("分类：" + cat_name)
        content_lines.append("片源：" + (play_from[0] if play_from else ""))
        content_lines.append("编号：" + vid)
        if related:
            titles = [str(c.get("vod_name") or "") for c in related[:6]]
            content_lines.append("相关推荐：" + "、".join(titles))

        vod = {
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": VOD_ACTOR,
            "vod_director": VOD_DIRECTOR,
            "vod_remarks": format_remarks("超清正片"),
            "vod_content": "\n".join(content_lines),
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
        }
        return {"list": [vod]}

    # ---------- player ----------

    def _play_headers(self, referer):
        return {"User-Agent": UA, "Referer": referer or (self.host + "/")}

    def _clean_wrap(self, u, r):
        ref = r or ""
        if not ref:
            o = _origin_of(u)
            ref = (o + "/") if o else ""
        w = "https://" + WASH_HOST + "/clean?u=" + quote(u, safe="")
        if ref:
            w += "&r=" + quote(ref, safe="")
        return w

    def _direct_result(self, url, referer):
        out = url
        if M3U8_RE.search(url or ""):
            out = self._clean_wrap(url, referer)
        return {"parse": 0, "url": out, "header": self._play_headers(referer)}

    def _resolve_page(self, page_url):
        if self._is_media(page_url):
            return self._direct_result(page_url, page_url)
        text, host = self._fetch(page_url, referer=page_url)
        h = text or ""
        play = ""
        m = PLAYER_JSON_RE.search(h) or PLAYER_JSON_RE2.search(h)
        if m:
            raw = m.group(1)
            try:
                data = json.loads(raw.replace("\\/", "/"))
                play = str(data.get("url") or "")
            except Exception:
                mm = PLAYER_URL_RE.search(raw)
                play = mm.group(1).replace("\\/", "/") if mm else ""
        if not play:
            play = self._first_media(h)
        if play and self._is_media(play):
            return self._direct_result(self._abs_url(play, host), page_url)
        return {"parse": 1, "url": page_url, "header": self._play_headers(page_url)}

    def playerContent(self, flag, id, vipFlags):
        pid = str(id or "")
        if pid.startswith("rel:"):
            rid = pid[4:].strip()
            detail = self.detailContent([rid])
            lst = detail.get("list") or []
            if not lst:
                return {"parse": 1, "url": self.host + "/", "header": self._play_headers("")}
            vod = lst[0]
            urls = str(vod.get("vod_play_url") or "").split("$$$")
            first_eps = urls[0].split("#")[0] if urls and urls[0] else ""
            first_val = first_eps.split("$", 1)[1] if "$" in first_eps else ""
            if not first_val or first_val.startswith("rel:"):
                page = "%s/voddetail/%s/" % (self.host, rid)
                return {"parse": 1, "url": page, "header": self._play_headers(page)}
            pid = first_val
        page_url = ""
        if pid.startswith("{"):
            try:
                data = json.loads(pid)
                page_url = str(data.get("pageUrl") or "")
            except Exception:
                page_url = ""
        elif pid.startswith("http"):
            page_url = pid
        if not page_url:
            return {"parse": 1, "url": self.host + "/", "header": self._play_headers("")}
        return self._resolve_page(page_url)

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249957004&sig=8e16e78402bd6de1
