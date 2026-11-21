# -*- coding: utf-8 -*-
# Chaturbate2直播 - com.butterfly.chaturbate2
import re
import json
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

SITE_NAME = "Chaturbate2直播"
BRAND_NAME = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专属直播线路"
DEFAULT_HOST = "https://chaturbate.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
PAGE_SIZE = 60
HOME_CAP = 24
PIC_RATIO = 1.78

CATEGORIES = [
    ("女性", "female-cams"),
    ("男性", "male-cams"),
    ("情侣", "couple-cams"),
    ("变性", "trans-cams"),
    ("新人", "new-cams"),
    ("游戏", "gaming-cams"),
    ("熟女", "mature-cams"),
    ("北美", "north-american-cams"),
    ("南美", "south-american-cams"),
    ("亚洲", "asian-cams"),
    ("欧洲/俄罗斯", "euro-russian-cams"),
    ("其他地区", "other-region-cams"),
]

CAT_PARAMS = {
    "female-cams": "&genders=f",
    "male-cams": "&genders=m",
    "couple-cams": "&genders=c",
    "trans-cams": "&genders=t",
    "new-cams": "&new_cams=true",
    "gaming-cams": "&gaming=true",
    "mature-cams": "&from_age=50&to_age=100",
    "north-american-cams": "&regions=NA",
    "south-american-cams": "&regions=SA",
    "asian-cams": "&regions=AS",
    "euro-russian-cams": "&regions=ER",
    "other-region-cams": "&regions=O",
}

QUALITIES = [
    ("1080P (蓝光超清)", "4"),
    ("720P (高清原画)", "3"),
    ("480P (流畅画质)", "2"),
    ("360P (标清画质)", "1"),
    ("自动 (Auto自适应)", "all"),
]

ROOMLIST_PATH = "/api/ts/roomlist/room-list/?enable_recommendations=false&limit=60&offset="


def format_remarks(brand="蝴蝶影视", meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


def sanitize_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        super(Spider, self).__init__()
        self.siteName = SITE_NAME
        self.host = DEFAULT_HOST
        self.options = {}

    def init(self, extend=""):
        if isinstance(extend, dict):
            self.options = extend
        elif extend:
            text = str(extend).strip()
            if text.startswith("http"):
                self.options = {"host": text}
            else:
                try:
                    parsed = json.loads(text)
                    self.options = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    self.options = {}
        host = str(self.options.get("host") or "").strip()
        if host.startswith("http"):
            self.host = host.rstrip("/")
        return True

    def getName(self):
        return self.siteName

    def isVideoFormat(self, url):
        path = str(url or "").split("?")[0].lower()
        return path.endswith((".m3u8", ".mpd", ".mp4", ".mkv", ".flv", ".mp3", ".m4a", ".aac"))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        self.options = {}

    def _page_num(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def _empty(self, page):
        return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": 0}

    def _page_form(self, cards, page):
        if not cards:
            return self._empty(page)
        return {"list": cards, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}

    def _fetch_json(self, path):
        full_url = path if path.startswith("http") else (self.host + path)
        headers = {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Accept": "application/json, text/plain, */*",
            "X-Requested-With": "XMLHttpRequest",
        }
        try:
            resp = requests.get(full_url, headers=headers, timeout=8)
            if resp.status_code >= 400:
                return None
            data = resp.json()
            return data if isinstance(data, dict) else None
        except Exception:
            return None

    def _abs_url(self, u):
        s = str(u or "").strip()
        if not s:
            return ""
        if s.startswith("//"):
            return "https:" + s
        if s.startswith("/"):
            return self.host + s
        if not re.match(r"https?://", s, re.I):
            return self.host + "/" + s
        return s

    def _format_poster(self, raw_pic):
        if not raw_pic:
            return ""
        full = self._abs_url(str(raw_pic).strip().replace("&amp;", "&"))
        return full + "@Referer=" + quote(self.host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def _rooms(self, path):
        data = self._fetch_json(path)
        if not isinstance(data, dict):
            return []
        rooms = data.get("rooms")
        return rooms if isinstance(rooms, list) else []

    def _room_card(self, r):
        if not isinstance(r, dict):
            r = {}
        username = str(r.get("username") or "")
        raw_pic = r.get("img") or ("https://thumb.live.mmcdn.com/ri/" + username + ".jpg")
        num_users = r.get("num_users")
        if num_users is not None:
            remarks = format_remarks(BRAND_NAME, "%s人在线" % num_users)
        else:
            remarks = format_remarks(BRAND_NAME, "直播中")
        return {
            "vod_id": username,
            "vod_name": username,
            "vod_pic": self._format_poster(raw_pic),
            "vod_remarks": remarks,
            "style": {"type": "rect", "ratio": PIC_RATIO},
        }

    def homeContent(self, filter):
        classes = [{"type_id": slug, "type_name": name} for name, slug in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        rooms = self._rooms(ROOMLIST_PATH + "0" + CAT_PARAMS["female-cams"])
        cards = [self._room_card(r) for r in rooms]
        return {"list": cards[:HOME_CAP]}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._page_num(pg)
        tid = str(tid or "female-cams")
        extra = CAT_PARAMS.get(tid, CAT_PARAMS["female-cams"])
        offset = (page - 1) * PAGE_SIZE
        rooms = self._rooms(ROOMLIST_PATH + str(offset) + extra)
        cards = [self._room_card(r) for r in rooms]
        return self._page_form(cards, page)

    def searchContent(self, key, quick, pg="1"):
        page = self._page_num(pg)
        keyword = str(key or "").strip()
        if not keyword or page > 1:
            return self._empty(page)
        kw = keyword.lower()
        found = []
        seen = set()
        for off in range(0, 300, PAGE_SIZE):
            rooms = self._rooms(ROOMLIST_PATH + str(off))
            if not rooms:
                break
            for r in rooms:
                if not isinstance(r, dict):
                    continue
                uname = str(r.get("username") or "")
                if uname in seen:
                    continue
                seen.add(uname)
                tags = r.get("tags")
                tag_str = " ".join(str(t) for t in tags) if isinstance(tags, list) else ""
                hay = (uname + " " + tag_str + " " + str(r.get("room_subject") or "")).lower()
                if kw in hay:
                    found.append(self._room_card(r))
        return {"list": found, "page": 1, "pagecount": 1, "limit": PAGE_SIZE, "total": len(found)}

    def _brand_block(self):
        return [
            "🦋 %s官方交流群：@tvshare23" % self.siteName,
            "导演：🦋 蝴蝶影视",
            "当前主站：%s" % self.host,
            "━" * 28,
            "━" * 7,
        ]

    def detailContent(self, ids):
        raw = ids[0] if isinstance(ids, (list, tuple)) and ids else ids
        username = str(raw or "").strip()
        if not username:
            return {"list": []}
        poster = self._format_poster("https://thumb.live.mmcdn.com/ri/" + username + ".jpg")
        eps = []
        for qname, q in QUALITIES:
            eps.append("%s$%s___%s" % (sanitize_ep_name(qname), username, q))
        content_lines = self._brand_block()
        content_lines.append("标题：%s" % username)
        content_lines.append("分类：%s" % "")
        content_lines.append("片源：%s" % LINE_NAME)
        content_lines.append("编号：%s" % username)
        vod = {
            "vod_id": username,
            "vod_name": username,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": "%s、%s" % (username, BRAND_ACTOR),
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks(BRAND_NAME, "正在直播"),
            "vod_content": "\n".join(content_lines),
            "vod_play_from": LINE_NAME,
            "vod_play_url": "#".join(eps),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw_id = str(id or "")
        username = raw_id.split("___")[0].strip()
        if not username:
            return {"parse": 0, "jx": 0, "url": ""}
        data = self._fetch_json("/api/chatvideocontext/" + quote(username, safe="") + "/")
        play_url = ""
        if isinstance(data, dict):
            play_url = str(data.get("hls_source") or "")
        if play_url:
            return {"parse": 0, "jx": 0, "url": play_url, "header": {"User-Agent": UA, "Referer": self.host + "/"}}
        return {"parse": 1, "jx": 0, "url": self.host + "/" + username}

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249993220&sig=c7e9f7167948b4e1
