# -*- coding: utf-8 -*-
# 觅番社动漫 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.aniget)
import base64
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://aniget.org"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_NAME = "AniGet"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND = "蝴蝶影视"
PAGE_SIZE = 14

CATEGORIES = [
    ("update", "最新更新"),
    ("hot", "热门"),
    ("category/2d", "2D动画"),
    ("category/3d", "3D动画"),
    ("category/donjin", "同人作品"),
    ("category/anime", "里番"),
    ("category/real", "真人AI"),
]

ANCHOR_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', re.I)
PIC_RE = re.compile(r'data-bg=["\']([^"\']+)["\']', re.I)
DURATION_RE = re.compile(r"(\d+:\d{2}(?::\d{2})?)")
TITLE_RE = re.compile(r'card-text-line">([^<]+)')
OG_TITLE_RE = re.compile(r'property="og:title" content="([^"]+)"')
DATA_POSTER_RE = re.compile(r'data-poster="([^"]+)"')
OG_IMAGE_RE = re.compile(r'property="og:image" content="([^"]+)"')
ENCODED_SRC_RE = re.compile(r'data-encoded-src="([^"]+)"')
DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
TAG_STRIP_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def decode_entities(text):
    t = str(text or "")
    t = t.replace("&amp;", "&")
    t = t.replace("&lt;", "<")
    t = t.replace("&gt;", ">")
    t = t.replace("&quot;", '"')
    t = re.sub(r"&#0?39;", "'", t)
    t = t.replace("&nbsp;", " ")
    return t


def clean_text(text):
    return WS_RE.sub(" ", decode_entities(str(text or ""))).strip()


def strip_tags(html_text):
    return TAG_STRIP_RE.sub(" ", str(html_text or ""))


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = WS_RE.sub(" ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND, clean_meta)
    return BRAND


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST

    def getName(self):
        return BRAND_NAME

    def init(self, extend=""):
        host = ""
        ext = extend
        if isinstance(ext, str) and ext.strip():
            text = ext.strip()
            if text.startswith("http"):
                host = text
            else:
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        host = str(data.get("host") or "")
                except Exception:
                    pass
        elif isinstance(ext, dict):
            host = str(ext.get("host") or "")
        if host.startswith("http"):
            self.host = host.rstrip("/")

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- fetch ----------

    def _fetch(self, url, referer=None):
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer is not None else (self.host + "/"),
        }
        try:
            resp = requests.get(url, headers=headers, timeout=8)
            if resp is not None and 200 <= resp.status_code < 300:
                return resp.text or ""
        except Exception:
            return ""
        return ""

    # ---------- cards ----------

    def _parse_cards(self, html_text):
        items = []
        body = str(html_text or "")
        if not body:
            return items
        post_re = re.compile(r"^" + re.escape(self.host) + r"/\d+/$")
        seen = set()
        for m in ANCHOR_RE.finditer(body):
            url = decode_entities(m.group(1)).strip()
            if not post_re.match(url):
                continue
            if url in seen:
                continue
            inner = m.group(2) or ""
            if "card-text-line" not in inner:
                continue
            seen.add(url)
            pic = ""
            pm = PIC_RE.search(inner)
            if pm:
                pic = decode_entities(pm.group(1)).strip()
            duration = ""
            head_part = inner.split("card-body")[0]
            dm = DURATION_RE.search(head_part)
            if dm:
                duration = dm.group(1)
            title = ""
            tm = TITLE_RE.search(inner)
            if tm:
                title = clean_text(tm.group(1))
            if not title:
                title = url.rstrip("/").split("/")[-1]
            items.append({
                "vod_id": url,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": format_remarks(duration),
                "style": {"type": "rect", "ratio": 0.75},
            })
        return items

    def _page_url(self, path_id, page):
        url = self.host + "/" + str(path_id).strip("/") + "/"
        if page > 1:
            url = url + "page/" + str(page) + "/"
        return url

    def _fetch_listing(self, path_id, page):
        url = self._page_url(path_id, page)
        html_text = self._fetch(url, self.host + "/")
        items = self._parse_cards(html_text)
        if not items and html_text and page == 1:
            html_text = self._fetch(url, self.host + "/")
            items = self._parse_cards(html_text)
        return items

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        return {"list": self._fetch_listing("update", 1)}

    def _page_form(self, items, page):
        if items:
            return {
                "list": items,
                "page": page,
                "pagecount": page + 1,
                "limit": PAGE_SIZE,
                "total": (page + 1) * PAGE_SIZE,
            }
        return {
            "list": [],
            "page": page,
            "pagecount": page,
            "limit": PAGE_SIZE,
            "total": page * PAGE_SIZE,
        }

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        cid = str(tid or "").strip()
        if not cid:
            cid = "update"
        items = self._fetch_listing(cid, page)
        return self._page_form(items, page)

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        keyword = str(key or "")
        path_id = "search/" + quote(keyword, safe="")
        items = self._fetch_listing(path_id, page)
        return self._page_form(items, page)

    # ---------- detail ----------

    def _brand_block(self):
        lines = [
            "🦋 " + BRAND_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _summary(self, title, genres, source_name, aid):
        block = self._brand_block()
        fallback = [
            "标题：" + title,
            "分类：" + "、".join(genres),
            "片源：" + source_name,
            "编号：" + aid,
        ]
        return block + "\n" + "\n".join(fallback)

    def _extract_detail_date(self, html_text):
        idx = html_text.find("wp-plyr-player")
        if idx == -1:
            return ""
        seg = html_text[idx:idx + 7000]
        text = clean_text(strip_tags(seg))
        dm = DATE_RE.search(text)
        if dm:
            return dm.group(1)
        return ""

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        post_url = raw
        if post_url and not post_url.startswith("http"):
            post_url = self.host + "/" + post_url.lstrip("/")
        if not post_url:
            return {"list": []}
        html_text = self._fetch(post_url, self.host + "/")
        if not html_text:
            return {"list": [], "msg": "Detail page request failed"}

        title = post_url
        tm = OG_TITLE_RE.search(html_text)
        if tm:
            title = clean_text(tm.group(1))

        poster = ""
        pm = DATA_POSTER_RE.search(html_text)
        if pm:
            poster = decode_entities(pm.group(1)).strip()
        if not poster:
            om = OG_IMAGE_RE.search(html_text)
            if om:
                poster = decode_entities(om.group(1)).strip()

        genres = []
        seen_genre = set()
        tag_re = re.compile(r'<a[^>]+href=["\']' + re.escape(self.host) + r'/tag/[^"\']+["\'][^>]*>([^<]+)</a>', re.I)
        for gm in tag_re.finditer(html_text):
            tag_name = clean_text(gm.group(1))
            if tag_name and tag_name not in seen_genre:
                seen_genre.add(tag_name)
                genres.append(tag_name)

        date = self._extract_detail_date(html_text)

        episode_strs = []
        first_name = title.replace("$", "_").replace("#", "_")
        episode_strs.append(first_name + "$" + json.dumps({"url": post_url}, ensure_ascii=False))
        related = self._parse_cards(html_text)
        for card in related:
            if card["vod_id"] == post_url:
                continue
            ep_name = card["vod_name"].replace("$", "_").replace("#", "_")
            episode_strs.append(ep_name + "$" + json.dumps({"url": card["vod_id"]}, ensure_ascii=False))
            if len(episode_strs) >= 15:
                break

        aid = post_url.rstrip("/").split("/")[-1]
        vod = {
            "vod_id": post_url,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks(date),
            "vod_content": self._summary(title, genres, "🦋 蝴蝶专线", aid),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episode_strs),
        }
        if date:
            vod["vod_year"] = date[:4]
        return {"list": [vod]}

    # ---------- player ----------

    def _decode_base64_text(self, encoded):
        cleaned = WS_RE.sub("", str(encoded or ""))
        if not cleaned:
            return ""
        try:
            raw = base64.b64decode(cleaned + "=" * (-len(cleaned) % 4))
            return raw.decode("utf-8")
        except Exception:
            return ""

    def playerContent(self, flag, pid, vipFlags):
        headers = {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Origin": self.host,
        }
        post_url = ""
        data = None
        try:
            parsed = json.loads(pid)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = None
        if data is not None and data.get("url"):
            post_url = str(data.get("url") or "")
        elif isinstance(pid, str) and pid:
            post_url = pid
        if post_url and not post_url.startswith("http"):
            post_url = self.host + "/" + post_url.lstrip("/")
        if not post_url:
            return {"parse": 1, "url": self.host + "/", "header": headers}

        html_text = self._fetch(post_url, self.host + "/")
        mp4 = ""
        if html_text:
            sm = ENCODED_SRC_RE.search(html_text)
            if sm:
                decoded = self._decode_base64_text(sm.group(1))
                if decoded and decoded.startswith("http"):
                    mp4 = decoded.strip()
        if mp4:
            return {"parse": 0, "url": mp4, "header": headers}
        return {"parse": 1, "url": post_url, "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249839739&sig=fc0bb5e15b001262
