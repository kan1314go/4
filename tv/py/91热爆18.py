# -*- coding: utf-8 -*-
# 91热爆 - com.butterfly.91rebao
import base64
import json
import re

import requests
from urllib.parse import quote, unquote

from base.spider import Spider as BaseSpider

SITE_NAME = "91热爆"
BRAND_NAME = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
DEFAULT_SITE = "https://rb.jnyk08.icu"
DEFAULT_API = "https://api.vuecloudrb.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
WASH_HOST_B64 = "Y2xlYW4uNTU2ODk5OS5jYy5jZA=="
PAGE_SIZE = 24
PIC_RATIO = 1.78

STATIC_CATEGORIES = [
    ("all", "推荐"),
    ("new", "最新"),
    ("hot", "热门"),
]

SNAPSHOT_CATEGORIES = [
    ("31", "韩国主播"),
    ("28", "FC2視頻"),
    ("21", "日韩自拍"),
    ("36", "探花约炮"),
    ("12", "厕所偷拍"),
    ("8", "日本有码"),
    ("7", "日本无码"),
    ("29", "亞洲SM"),
    ("24", "印度视频"),
    ("14", "国模私拍"),
    ("32", "男同性恋"),
    ("23", "华语AV"),
    ("11", "人妖视频"),
    ("3", "偷拍视频"),
    ("2", "中文字幕"),
    ("26", "街拍抄底"),
    ("33", "摄像头偷拍"),
    ("17", "短视频"),
    ("10", "网红主播"),
    ("22", "SM重口味"),
    ("1", "国产自拍"),
    ("5", "欧美自拍"),
    ("15", "日本高清"),
    ("4", "动漫视频"),
    ("20", "91视频"),
    ("13", "韩国BJ"),
    ("16", "JVID视频"),
    ("18", "欧美小视频"),
    ("30", "SWAG"),
    ("9", "日韩三级"),
    ("6", "港台三级"),
    ("19", "无码短片"),
    ("27", "OnlyFans"),
    ("25", "街头扒衣"),
    ("34", "AV解说"),
    ("35", "国产吃瓜"),
    ("37", "AI短剧"),
]

CATEGORIES = STATIC_CATEGORIES + SNAPSHOT_CATEGORIES


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND_NAME, clean_meta)
    return BRAND_NAME


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_SITE
        self._custom_host = ""
        self._host_ready = False

    # ---------- host / http ----------

    def init(self, extend=""):
        custom = ""
        ext = extend
        if isinstance(ext, dict):
            custom = str(ext.get("host") or "").strip()
        elif isinstance(ext, str) and ext.strip():
            text = ext.strip()
            if text.startswith("{"):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        custom = str(parsed.get("host") or "").strip()
                except Exception:
                    custom = ""
            if not custom:
                custom = text
        if custom.startswith("http"):
            self._custom_host = custom.rstrip("/")
            self.host = self._custom_host
        self._host_ready = False

    def _probe_host(self, host):
        try:
            resp = requests.get(
                host + "/",
                headers={"User-Agent": UA},
                timeout=6,
            )
            if 200 <= resp.status_code < 500:
                return host
        except Exception:
            pass
        return None

    def _get_host(self):
        if self._custom_host:
            self.host = self._custom_host
            return self.host
        if self._host_ready:
            return self.host
        winner = self._probe_host(DEFAULT_SITE)
        self.host = winner if winner else DEFAULT_SITE
        self._host_ready = True
        return self.host

    def _api_get(self, path, params):
        host = self._get_host()
        try:
            resp = requests.get(
                DEFAULT_API + path,
                params=params,
                headers={
                    "User-Agent": UA,
                    "Referer": host + "/",
                    "Origin": host,
                },
                timeout=8,
            )
            if resp.status_code >= 400:
                return {}
            data = resp.json()
            if isinstance(data, dict):
                return data
            return {}
        except Exception:
            return {}

    # ---------- data shaping ----------

    def _fmt_time(self, value):
        try:
            total = int(float(value)) if isinstance(value, str) and "." in value else int(value)
        except Exception:
            try:
                total = int(str(value).strip())
            except Exception:
                total = 0
        if total < 0:
            total = 0
        h = total // 3600
        m = (total % 3600) // 60
        s = total % 60
        if h:
            return "%02d:%02d:%02d" % (h, m, s)
        return "%02d:%02d" % (m, s)

    def _extract_rows(self, data):
        arr = data
        if isinstance(arr, dict):
            rows = arr.get("data")
            if not isinstance(rows, list):
                rows = None
                sub_new = arr.get("list_new")
                if isinstance(sub_new, dict) and isinstance(sub_new.get("data"), list):
                    rows = sub_new.get("data")
                if rows is None:
                    sub_hot = arr.get("list_hot")
                    if isinstance(sub_hot, dict) and isinstance(sub_hot.get("data"), list):
                        rows = sub_hot.get("data")
                if rows is None:
                    rows = []
            return rows
        if isinstance(arr, list):
            return arr
        return []

    def _to_items(self, data):
        out = []
        for item in self._extract_rows(data):
            if not isinstance(item, dict):
                continue
            vid = item.get("video_id") or item.get("id") or ""
            if not vid:
                continue
            vid = str(vid)
            title = item.get("title") or item.get("name") or vid
            title = str(title)
            poster = item.get("video_img") or item.get("screenshot1") or ""
            poster = str(poster)
            duration = self._fmt_time(item.get("duration") or 0)
            vod_id = "@@".join([
                vid,
                quote(title, safe=""),
                quote(poster, safe=""),
                quote(duration, safe=""),
            ])
            out.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": poster,
                "vod_remarks": format_remarks(duration),
                "style": {"type": "rect", "ratio": PIC_RATIO},
            })
        return out

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
            "total": 0,
        }

    def _page_num(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        data = self._api_get("/videos/index_byall", [
            ("page", 1),
            ("size", 24),
            ("categories", 0),
            ("sort", "post_date"),
        ])
        content = data.get("content") or {}
        rows = content.get("list_new") or {}
        return {"list": self._to_items(rows)}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._page_num(pg)
        tid = str(tid or "all")
        if (tid == "new" or tid == "hot") and page > 1:
            return self._page_form([], page)
        data = {}
        if tid == "all":
            res = self._api_get("/videos/index", [
                ("page", page),
                ("size", 24),
            ])
            data = res.get("content") or {}
        elif tid == "new":
            res = self._api_get("/videos/index_byall", [
                ("page", page),
                ("size", 24),
                ("categories", 0),
                ("sort", "post_date"),
            ])
            data = (res.get("content") or {}).get("list_new") or {}
        elif tid == "hot":
            res = self._api_get("/videos/index_byall", [
                ("page", page),
                ("size", 24),
                ("categories", 0),
                ("sort", "video_viewed"),
            ])
            data = (res.get("content") or {}).get("list_hot") or {}
        elif tid.startswith("tag_"):
            res = self._api_get("/videos/list_bytags", [
                ("page", page),
                ("size", 24),
                ("categories", 0),
                ("sort", "post_date"),
                ("tags", tid[4:]),
            ])
            data = res.get("content") or {}
        else:
            res = self._api_get("/videos/index", [
                ("page", page),
                ("size", 24),
                ("categories", tid),
                ("sort", "post_date"),
            ])
            data = res.get("content") or {}
        return self._page_form(self._to_items(data), page)

    def searchContent(self, key, quick, pg="1"):
        page = self._page_num(pg)
        kw = str(key or "").strip()
        if not kw:
            return self._page_form([], page)
        res = self._api_get("/videos/search", [
            ("keyword", kw),
            ("page", page),
            ("limit", 20),
        ])
        data = res.get("content") or {}
        return self._page_form(self._to_items(data), page)

    # ---------- detail ----------

    def _brand_block(self):
        host = self._get_host()
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ]
        return lines

    def _summary(self, name, cat_list, vid):
        lines = self._brand_block()
        lines.append("标题：" + name)
        lines.append("分类：" + "、".join(cat_list))
        lines.append("片源：" + LINE_NAME)
        lines.append("编号：" + vid)
        return "\n".join(lines)

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        raw_id = str(ids[0] or "")
        parts = raw_id.split("@@")
        vid = parts[0]
        ref_title = unquote(parts[1]) if len(parts) > 1 else ""
        ref_poster = unquote(parts[2]) if len(parts) > 2 else ""
        ref_duration = unquote(parts[3]) if len(parts) > 3 else ""
        if not vid:
            return {"list": []}

        res = self._api_get("/videos/detail", [("id", vid)])
        c = res.get("content") or {}
        if not isinstance(c, dict):
            c = {}

        name = str(c.get("title") or ref_title or vid)
        poster = str(c.get("video_img") or ref_poster or "")

        tag_list = []
        tags = c.get("tags")
        if isinstance(tags, list):
            for t in tags:
                if isinstance(t, dict) and t.get("tag"):
                    tag_list.append(str(t.get("tag")).strip())

        cat_list = []
        cats = c.get("categories")
        if isinstance(cats, list):
            for cat in cats:
                if isinstance(cat, dict) and cat.get("title"):
                    cat_list.append(str(cat.get("title")).strip())

        if c.get("duration"):
            duration = self._fmt_time(c.get("duration"))
        else:
            duration = ref_duration

        year = ""
        if c.get("post_date"):
            year = str(c.get("post_date"))[:4]

        vod = {
            "vod_id": vid,
            "vod_name": name,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_remarks": format_remarks(duration),
            "vod_year": year,
            "vod_type": ",".join(cat_list),
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_content": self._summary(name, cat_list, vid),
            "vod_play_from": LINE_NAME,
            "vod_play_url": "正片$" + vid,
        }
        return {"list": [vod]}

    # ---------- play ----------

    def _parse_int_prefix(self, text):
        m = re.match(r"\s*([+-]?\d+)", str(text or ""))
        if not m:
            return None
        try:
            return int(m.group(1))
        except Exception:
            return None

    def _raw_m3u8(self, vid):
        n = self._parse_int_prefix(vid)
        if n is None:
            base = (vid[:len(vid) - 3] if len(vid) > 3 else "") + "000"
        else:
            base = str((n // 1000) * 1000)
        return "https://delivery.douyinpaly.com/hls/contents/videos/" + base + "/" + vid + "/" + vid + ".mp4/index.m3u8"

    def _clean_wrap(self, raw_url, host):
        wash = base64.b64decode(WASH_HOST_B64).decode("utf-8", "ignore")
        out = "https://" + wash + "/clean?u=" + quote(raw_url, safe="")
        out += "&r=" + quote(host + "/", safe="")
        out += "&px=1&ct=video%2FMP2T"
        return out

    def playerContent(self, flag, id, vipFlags):
        vid = str(id or "").strip()
        host = self._get_host()
        raw = self._raw_m3u8(vid)
        return {
            "parse": 0,
            "url": self._clean_wrap(raw, host),
            "header": {
                "User-Agent": UA,
                "Referer": host + "/",
                "Origin": host,
            },
        }

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249364149&sig=3d2a977f3e7ffaa3
