# -*- coding: utf-8 -*-
# Chaturbate直播 - com.butterfly.chaturbate
import re
import json
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

SITE_NAME = "Chaturbate直播"
BRAND_NAME = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
DEFAULT_HOST = "https://chaturbate.com"
UA = "Mozilla/5.0 (Linux; Android 10) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
PAGE_SIZE = 90
PIC_RATIO = 1.33
THUMB_BASE = "https://thumb.live.mmcdn.com/ri/"
ROOM_GENRES = ["Chaturbate直播", "欧美直播", "在线互动"]
FEED_LINE_NAME = "🦋 连续刷流专线"
ROOM_LINE_NAME = "🦋 蝴蝶超清专线"

CLASSES = [
    ("continuous_feed", "📺 连刷模式"),
    ("female-cams", "女性"),
    ("couple-cams", "情侣"),
    ("male-cams", "男性"),
    ("trans-cams", "变性"),
    ("new-cams", "新人"),
    ("gaming-cams", "游戏"),
    ("mature-cams", "熟女"),
    ("north-american-cams", "北美"),
    ("south-american-cams", "南美"),
    ("asian-cams", "亚洲"),
    ("euro-russian-cams", "欧洲/俄罗斯"),
    ("other-region-cams", "其他地区"),
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

FEED_CHANNELS = [
    {"id": "feed_female", "name": "🔥 热门精选·女主播连刷", "extra": "&genders=f", "path": "/female-cams/", "svg_title": "热门女主播连刷", "svg_sub": "CHATURBATE · 极速换台", "c1": "#ff0844", "c2": "#ffb199"},
    {"id": "feed_all", "name": "✨ 全员在线·极速切台连刷", "extra": "", "path": "/", "svg_title": "全员热门连刷", "svg_sub": "CHATURBATE · 精彩全聚合", "c1": "#6a11cb", "c2": "#2575fc"},
    {"id": "feed_couple", "name": "👩‍❤️‍👨 激情互动·情侣连刷", "extra": "&genders=c", "path": "/couple-cams/", "svg_title": "情侣双人连刷", "svg_sub": "CHATURBATE · 真实激情互动", "c1": "#fa709a", "c2": "#fee140"},
    {"id": "feed_asian", "name": "🌸 东方佳丽·亚洲专区连刷", "extra": "&regions=AS", "path": "/asian-cams/", "svg_title": "亚洲专区连刷", "svg_sub": "CHATURBATE · 东方佳丽精选", "c1": "#f857a6", "c2": "#ff5858"},
    {"id": "feed_trans", "name": "🌈 特色风情·变性连刷", "extra": "&genders=t", "path": "/trans-cams/", "svg_title": "变性特色连刷", "svg_sub": "CHATURBATE · 异域风情精选", "c1": "#654ea3", "c2": "#eaafc8"},
    {"id": "feed_male", "name": "🕺 活力型男·男主播连刷", "extra": "&genders=m", "path": "/male-cams/", "svg_title": "男主播精选连刷", "svg_sub": "CHATURBATE · 阳光型男推荐", "c1": "#13547a", "c2": "#80d0c7"},
]

OG_TITLE_RE = re.compile(r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"', re.I)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', re.I)
DESC_RE = re.compile(r'<meta[^>]+name="description"[^>]+content="([^"]*)"', re.I)
PIC_SEG_RE = re.compile(r"/(?:riw|r|thumb)/")
HLS_SOURCE_RE = re.compile(r'hls_source\\u0022:\s*\\u0022(.*?)\\u0022', re.S)
QUOTED_M3U8_RE = re.compile(r'"(https?://[^"]+\.m3u8[^"]*)"')
NUM_ENTITY_RE = re.compile(r"&#(\d+);")


def make_svg_cover(title, sub, c1, c2):
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" viewBox="0 0 600 340">' + \
        '<defs>' + \
        '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">' + \
        '<stop offset="0%" stop-color="' + c1 + '" />' + \
        '<stop offset="100%" stop-color="' + c2 + '" />' + \
        '</linearGradient>' + \
        '</defs>' + \
        '<rect width="100%" height="100%" fill="url(#g)" />' + \
        '<circle cx="300" cy="130" r="46" fill="rgba(255,255,255,0.18)" />' + \
        '<polygon points="288,110 322,130 288,150" fill="#ffffff" />' + \
        '<text x="50%" y="225" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="28" font-weight="bold" fill="#ffffff" text-anchor="middle">' + title + '</text>' + \
        '<text x="50%" y="265" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="16" fill="rgba(255,255,255,0.85)" text-anchor="middle">' + sub + '</text>' + \
        '</svg>'
    return "data:image/svg+xml;utf8," + quote(svg, safe="-_.!~*'()")


def unescape_html(s):
    t = str(s or "")
    t = t.replace("&amp;", "&")
    t = t.replace("&lt;", "<")
    t = t.replace("&gt;", ">")
    t = t.replace("&quot;", '"')
    t = re.sub(r"&#0?39;", "'", t)
    t = t.replace("&nbsp;", " ")
    t = NUM_ENTITY_RE.sub(lambda m: chr(int(m.group(1))), t)
    return t


def strip_tags(s):
    return re.sub(r"<[^>]+>", "", str(s or ""))


def clean_text(s):
    t = unescape_html(strip_tags(str(s or "")))
    t = re.sub(r"[\r\n\t]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def sanitize_ep_name(name):
    t = str(name or "").replace("$", "_").replace("#", "_")
    return re.sub(r"\s+", " ", t).strip()


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND_NAME, clean_meta)
    return BRAND_NAME


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST
        self._feed_covers = {}

    def getName(self):
        return SITE_NAME

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "").strip()
        elif extend:
            text = str(extend).strip()
            if text.startswith("{"):
                try:
                    obj = json.loads(text)
                    if isinstance(obj, dict):
                        custom = str(obj.get("host") or "").strip()
                except Exception:
                    custom = ""
            else:
                custom = text
        if custom.startswith("http"):
            self.host = custom.rstrip("/")

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def liveContent(self):
        return ""

    # ---------- network ----------

    def _headers(self, json_accept=False, referer=None):
        return {
            "User-Agent": UA,
            "Referer": referer if referer else (self.host + "/"),
            "Accept": "application/json, text/plain, */*" if json_accept else "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _fetch_json(self, path):
        for _attempt in range(2):
            try:
                resp = requests.get(self.host + path, headers=self._headers(json_accept=True), timeout=8)
                if resp is not None and isinstance(resp.text, str) and resp.text:
                    try:
                        data = json.loads(resp.text)
                        if isinstance(data, dict):
                            return data
                    except Exception:
                        pass
            except Exception:
                pass
        return None

    def _fetch_text(self, path):
        target = path
        if target.startswith("//"):
            target = "https:" + target
        elif target.startswith("/"):
            target = self.host + target
        for _attempt in range(2):
            try:
                resp = requests.get(target, headers=self._headers(), timeout=8)
                if resp is not None and isinstance(resp.text, str) and resp.text:
                    return resp.text
            except Exception:
                pass
        return ""

    def _room_list_path(self, limit, offset, extra):
        return "/api/ts/roomlist/room-list/?limit=" + str(limit) + "&offset=" + str(offset) + "&require_fingerprint=false" + (extra or "")

    # ---------- cards ----------

    def _room_card(self, room):
        if not isinstance(room, dict):
            return None
        name = str(room.get("username") or "")
        if not name:
            return None
        num = room.get("num_users")
        if num is not None:
            num_text = "%s 人在看" % num
        else:
            num_text = "正在直播"
        return {
            "vod_id": name,
            "vod_name": name,
            "vod_pic": THUMB_BASE + name + ".jpg",
            "vod_remarks": format_remarks(num_text),
            "style": {"type": "rect", "ratio": PIC_RATIO},
        }

    def _rooms_to_cards(self, rooms):
        cards = []
        seen = set()
        for room in rooms or []:
            card = self._room_card(room)
            if card is None:
                continue
            if card["vod_id"] in seen:
                continue
            seen.add(card["vod_id"])
            cards.append(card)
        return cards

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

    # ---------- entries ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        data = self._fetch_json(self._room_list_path(20, 0, "&genders=f"))
        rooms = data.get("rooms") if isinstance(data, dict) else None
        return {"list": self._rooms_to_cards(rooms)}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        tid = str(tid or "continuous_feed")
        if tid == "continuous_feed":
            if page > 1:
                return self._page_form([], page)
            return self._page_form(self._feed_cards(), page)
        offset = (page - 1) * PAGE_SIZE
        data = self._fetch_json(self._room_list_path(PAGE_SIZE, offset, CAT_PARAMS.get(tid, "")))
        rooms = data.get("rooms") if isinstance(data, dict) else None
        return self._page_form(self._rooms_to_cards(rooms), page)

    def _feed_cards(self):
        cards = []
        for ch in FEED_CHANNELS:
            cover = self._feed_covers.get(ch["id"]) or ""
            if not cover:
                data = self._fetch_json(self._room_list_path(1, 0, ch["extra"]))
                rooms = data.get("rooms") if isinstance(data, dict) else None
                if rooms and isinstance(rooms[0], dict) and rooms[0].get("username"):
                    cover = THUMB_BASE + str(rooms[0].get("username")) + ".jpg"
                    self._feed_covers[ch["id"]] = cover
            cards.append({
                "vod_id": ch["id"],
                "vod_name": ch["name"],
                "vod_pic": cover or make_svg_cover(ch["svg_title"], ch["svg_sub"], ch["c1"], ch["c2"]),
                "vod_remarks": format_remarks("自动切台"),
                "style": {"type": "rect", "ratio": PIC_RATIO},
            })
        return cards

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip().lower()
        if not keyword or page > 1:
            return self._page_form([], page)
        found = []
        offset = 0
        while offset < 270 and len(found) < 90:
            data = self._fetch_json(self._room_list_path(PAGE_SIZE, offset, ""))
            rooms = data.get("rooms") if isinstance(data, dict) else None
            if not rooms:
                break
            for room in rooms:
                if not isinstance(room, dict):
                    continue
                subj = room.get("subject") or room.get("room_subject") or ""
                tags = room.get("tags")
                tag_text = " ".join([str(t) for t in tags]) if isinstance(tags, list) else ""
                hay = (str(room.get("username") or "") + " " + str(subj) + " " + tag_text).lower()
                if keyword in hay:
                    found.append(room)
            offset += PAGE_SIZE
        cards = []
        seen = set()
        for room in found[:90]:
            card = self._room_card(room)
            if card is None:
                continue
            if card["vod_id"] in seen:
                continue
            seen.add(card["vod_id"])
            cards.append(card)
        return self._page_form(cards, page)

    # ---------- detail ----------

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return lines

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0] or "")
        if vid.startswith("feed_"):
            return {"list": [self._feed_detail(vid)]}
        detail = self._room_detail(vid)
        if detail is None:
            return {"list": []}
        return {"list": [detail]}

    def _feed_detail(self, feed_id):
        ch = None
        for item in FEED_CHANNELS:
            if item["id"] == feed_id:
                ch = item
                break
        if ch is None:
            ch = FEED_CHANNELS[0]
        rooms = []
        for offset in (0, 60):
            data = self._fetch_json(self._room_list_path(60, offset, ch["extra"]))
            part = data.get("rooms") if isinstance(data, dict) else None
            if isinstance(part, list):
                rooms.extend(part)
        episodes = []
        seen = set()
        idx = 1
        first_still = ""
        for room in rooms:
            if not isinstance(room, dict):
                continue
            uname = str(room.get("username") or "")
            if not uname or uname in seen:
                continue
            seen.add(uname)
            ep_title = str(idx) + ". " + uname
            num = room.get("num_users")
            if num is not None:
                ep_title += " (" + str(num) + "人)"
            value = json.dumps({"username": uname, "pic": THUMB_BASE + uname + ".jpg"}, ensure_ascii=False)
            episodes.append(sanitize_ep_name(ep_title) + "$" + value)
            if not first_still:
                first_still = THUMB_BASE + uname + ".jpg"
            idx += 1
        if not episodes:
            episodes.append("暂无在线房间$" + json.dumps({"username": ""}, ensure_ascii=False))
        poster = first_still or make_svg_cover(ch["svg_title"], ch["svg_sub"], ch["c1"], ch["c2"])
        tip = "【连刷功能提示】本频道已汇聚 " + str(len(episodes)) + " 位高热度在线主播。在播放器中开启“自动连播”或直接手势上下划动选集，即可秒速无缝切台！"
        content_lines = self._brand_block()
        content_lines.append(tip)
        return {
            "vod_id": feed_id,
            "vod_name": ch["name"],
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks("共" + str(len(episodes)) + "位在线"),
            "vod_content": "\n".join(content_lines),
            "vod_play_from": FEED_LINE_NAME,
            "vod_play_url": "#".join(episodes),
        }

    def _room_detail(self, vid):
        username = re.sub(r"^/+|/+$", "", str(vid or ""))
        if not username:
            return None
        title = username
        pic = THUMB_BASE + username + ".jpg"
        desc = ""
        html = self._fetch_text("/" + quote(username, safe="") + "/")
        if html:
            m = OG_TITLE_RE.search(html)
            if m:
                t = clean_text(m.group(1))
                if t:
                    title = t
            m = OG_IMAGE_RE.search(html)
            if m:
                pic = PIC_SEG_RE.sub("/ri/", m.group(1), count=1)
            m = DESC_RE.search(html)
            if m:
                desc = unescape_html(m.group(1))
        poster = pic
        if poster.startswith("//"):
            poster = "https:" + poster
        elif poster.startswith("/"):
            poster = self.host + poster
        content_lines = self._brand_block()
        if desc:
            content_lines.append(desc)
        else:
            content_lines.append("标题：" + title)
            content_lines.append("分类：" + "、".join(ROOM_GENRES))
            content_lines.append("片源：" + ROOM_LINE_NAME)
            content_lines.append("编号：" + username)
        episode_value = json.dumps({"username": username}, ensure_ascii=False)
        return {
            "vod_id": username,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks("正在直播"),
            "vod_content": "\n".join(content_lines),
            "vod_play_from": ROOM_LINE_NAME,
            "vod_play_url": "进入直播间$" + episode_value,
        }

    # ---------- play ----------

    def _hls_from_html(self, html):
        m = HLS_SOURCE_RE.search(html or "")
        if not m:
            return ""
        s = m.group(1)
        s = re.sub(r"\\u002d", "-", s, flags=re.I)
        s = re.sub(r"\\u003d", "=", s, flags=re.I)
        s = re.sub(r"\\u0026", "&", s, flags=re.I)
        s = s.replace("\\/", "/")
        return s

    def _get_stream(self, username):
        ctx = self._fetch_json("/api/chatvideocontext/" + quote(username, safe="") + "/")
        if isinstance(ctx, dict) and ctx.get("hls_source"):
            return str(ctx.get("hls_source")).replace("\\/", "/")
        html = self._fetch_text("/" + quote(username, safe="") + "/")
        if html:
            stream = self._hls_from_html(html)
            if stream:
                return stream
            m = QUOTED_M3U8_RE.search(html)
            if m:
                return m.group(1).replace("\\/", "/")
        return ""

    def playerContent(self, flag, id, vipFlags):
        headers = {"User-Agent": UA, "Referer": self.host + "/", "Origin": self.host}
        raw = str(id or "")
        username = ""
        direct = ""
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
                if isinstance(obj, dict):
                    direct = str(obj.get("directUrl") or "")
                    username = str(obj.get("username") or "")
            except Exception:
                username = ""
        if direct:
            return {"parse": 0, "url": direct, "header": headers}
        if not username:
            username = re.sub(r"^/+|/+$", "", raw).split("|")[0]
        if not username:
            return {"parse": 1, "url": self.host + "/", "header": headers}
        stream = self._get_stream(username)
        if stream:
            return {"parse": 0, "url": stream, "header": headers}
        return {"parse": 1, "url": self.host + "/" + quote(username, safe="") + "/", "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250009821&sig=60794ad83437cc27
