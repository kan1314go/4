# -*- coding: utf-8 -*-
# Cam4直播 - com.butterfly.cam4
import json
import re
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

SITE_NAME = "Cam4直播"
BRAND_NAME = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
DEFAULT_HOST = "https://zh.cam4.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PAGE_SIZE = 60
PIC_RATIO = 1.78
ROOM_LINE = "🦋 蝴蝶超清专线"
FEED_LINE = "🦋 连续刷流专线"

CLASSES = [
    ("continuous_feed", "📺 连刷模式"),
    ("all", "全部"),
    ("female", "女性"),
    ("male", "男性"),
    ("couples", "情侣"),
    ("shemale", "变性"),
]

CLASS_EXTRA = {
    "female": "&gender=female",
    "male": "&gender=male",
    "couples": "&broadcastType=male_female_group",
    "shemale": "&gender=shemale",
}

FEED_CHANNELS = [
    {"id": "feed_all", "name": "🔥 热门在线·全员连刷", "extra": "", "path": "/directoryCams",
     "cover": ("全员热门连刷", "CAM4 · 全天候自动切台", "#ff0844", "#ffb199")},
    {"id": "feed_female", "name": "💃 热门精选·女主播连刷", "extra": "&gender=female", "path": "/female",
     "cover": ("女主播连刷", "CAM4 · 绝美佳丽推荐", "#f107a3", "#7b2ff7")},
    {"id": "feed_couples", "name": "👩‍❤️‍👨 激情互动·情侣连刷", "extra": "&broadcastType=male_female_group", "path": "/couples",
     "cover": ("情侣双人连刷", "CAM4 · 浪漫在线互动", "#fa709a", "#fee140")},
    {"id": "feed_shemale", "name": "✨ 特色精选·伪娘变性连刷", "extra": "&gender=shemale", "path": "/shemale",
     "cover": ("特色风情连刷", "CAM4 · 伪娘变性专属", "#654ea3", "#eaafc8")},
    {"id": "feed_male", "name": "🕺 活力型男·男主播连刷", "extra": "&gender=male", "path": "/male",
     "cover": ("活力男主播连刷", "CAM4 · 阳刚型男精选", "#13547a", "#80d0c7")},
]


def format_remarks(brand, meta):
    clean_meta = re.sub(r"[\r\n\t]+", " ", str(meta or "")).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


def make_svg_cover(title, sub, c1, c2):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" viewBox="0 0 600 340">'
           '<defs>'
           '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
           '<stop offset="0%" stop-color="' + c1 + '" />'
           '<stop offset="100%" stop-color="' + c2 + '" />'
           '</linearGradient>'
           '</defs>'
           '<rect width="100%" height="100%" fill="url(#g)" />'
           '<circle cx="300" cy="130" r="46" fill="rgba(255,255,255,0.18)" />'
           '<polygon points="288,110 322,130 288,150" fill="#ffffff" />'
           '<text x="50%" y="225" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="28" font-weight="bold" fill="#ffffff" text-anchor="middle">' + title + '</text>'
           '<text x="50%" y="265" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="16" fill="rgba(255,255,255,0.85)" text-anchor="middle">' + sub + '</text>'
           '</svg>')
    return "data:image/svg+xml;utf8," + quote(svg, safe="-_.!~*'()")


def clean_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def init(self, extend=""):
        self.host = DEFAULT_HOST
        self._feed_cover_cache = {}
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "").strip()
        elif isinstance(extend, str) and extend.strip():
            text = extend.strip()
            if text.startswith("{"):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        custom = str(parsed.get("host") or "").strip()
                except Exception:
                    custom = ""
            else:
                custom = text
        if custom.startswith("http"):
            self.host = custom.rstrip("/")

    def _headers(self, accept=None):
        return {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Accept": accept or "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _fetch_users(self, extra, page):
        url = (self.host + "/directoryCams?directoryJson=true&online=true&url=true&page="
               + str(page) + (extra or ""))
        try:
            resp = requests.get(url, headers=self._headers("application/json, text/plain, */*"), timeout=8)
            data = json.loads(resp.text or "")
        except Exception:
            return []
        if isinstance(data, dict) and isinstance(data.get("users"), list):
            return data["users"]
        return []

    def _page_num(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        return page if page >= 1 else 1

    def _page_form(self, cards, page):
        if cards:
            return {"list": cards, "page": page, "pagecount": page + 1,
                    "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}
        return {"list": [], "page": page, "pagecount": page,
                "limit": PAGE_SIZE, "total": 0}

    def _user_card(self, u, with_age):
        uname = str(u.get("username") or "")
        title = uname + " (" + str(u.get("countryCode") or "") + ")"
        age = u.get("age")
        if with_age and age is not None:
            title += " - " + str(age) + "岁"
        resolution = u.get("resolution")
        if resolution:
            title += " [HD:" + str(resolution).split(":")[-1] + "]"
        status_msg = u.get("statusMessage")
        if status_msg:
            remarks = format_remarks(BRAND_NAME, status_msg)
        else:
            remarks = format_remarks(BRAND_NAME, "正在直播")
        pic = str(u.get("snapshotImageLink") or "")
        ref = {"playUrl": str(u.get("hlsPreviewUrl") or ""), "uname": uname, "pic": pic}
        return {
            "vod_id": json.dumps(ref, ensure_ascii=False),
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": remarks,
            "style": {"type": "rect", "ratio": PIC_RATIO},
        }

    def _summary(self, title, category, line_name, code):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
            "标题：" + str(title or ""),
            "分类：" + str(category or ""),
            "片源：" + line_name,
            "编号：" + str(code or ""),
        ]
        return "\n".join(lines)

    def homeContent(self, filter):
        classes = [{"type_id": tid, "type_name": name} for tid, name in CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        users = self._fetch_users("", 1)
        cards = [self._user_card(u, True) for u in users if u.get("hlsPreviewUrl")]
        return {"list": cards[:18]}

    def _feed_cover(self, ch):
        cached = self._feed_cover_cache.get(ch["id"])
        if cached:
            return cached
        users = self._fetch_users(ch["extra"], 1)
        for u in users:
            pic = str(u.get("snapshotImageLink") or "")
            if pic:
                self._feed_cover_cache[ch["id"]] = pic
                return pic
        return ""

    def categoryContent(self, tid, pg, filter, extend):
        page = self._page_num(pg)
        if tid == "continuous_feed":
            if page > 1:
                return self._page_form([], page)
            items = []
            for ch in FEED_CHANNELS:
                cover = self._feed_cover(ch)
                if not cover:
                    cover = make_svg_cover(*ch["cover"])
                items.append({
                    "vod_id": ch["id"],
                    "vod_name": ch["name"],
                    "vod_pic": cover,
                    "vod_remarks": format_remarks(BRAND_NAME, "自动切台"),
                    "style": {"type": "rect", "ratio": PIC_RATIO},
                })
            return {"list": items, "page": page, "pagecount": page,
                    "limit": PAGE_SIZE, "total": len(items)}
        extra = CLASS_EXTRA.get(tid, "")
        users = self._fetch_users(extra, page)
        cards = [self._user_card(u, True) for u in users if u.get("hlsPreviewUrl")]
        return self._page_form(cards, page)

    def searchContent(self, key, quick, pg="1"):
        page = self._page_num(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_form([], page)
        users = self._fetch_users("&tags=" + quote(keyword, safe=""), page)
        cards = [self._user_card(u, False) for u in users if u.get("hlsPreviewUrl")]
        return self._page_form(cards, page)

    def _parse_ref(self, raw):
        ref = {}
        text = str(raw or "")
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    ref = parsed
            except Exception:
                ref = {}
        play_url = str(ref.get("playUrl") or "")
        uname = str(ref.get("uname") or "")
        pic = str(ref.get("pic") or "")
        if not ref:
            if "://" in text:
                play_url = text
            elif text:
                uname = text
        if not uname and play_url:
            m = re.search(r"cam4-origin-live/([A-Za-z0-9_]+)-", play_url)
            if m:
                uname = m.group(1)
        return play_url, uname, pic

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        if raw.startswith("feed_"):
            return {"list": [self._feed_detail(raw)]}
        play_url, uname, pic = self._parse_ref(raw)
        if not uname and not play_url:
            return {"list": []}
        poster = pic
        if not poster and uname:
            poster = "https://snapshots.xcdnpro.com/thumbnails/" + uname
        ep_value = json.dumps({"playUrl": play_url, "uname": uname}, ensure_ascii=False)
        vod = {
            "vod_id": raw,
            "vod_name": uname or SITE_NAME,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_type": "Cam4直播,美女直播,高清秒播",
            "vod_remarks": format_remarks(BRAND_NAME, "直播中"),
            "vod_content": self._summary(uname, "Cam4直播", ROOM_LINE, uname),
            "vod_play_from": ROOM_LINE,
            "vod_play_url": "直连播放$" + ep_value,
        }
        return {"list": [vod]}

    def _feed_detail(self, feed_id):
        ch = None
        for cand in FEED_CHANNELS:
            if cand["id"] == feed_id:
                ch = cand
                break
        if ch is None:
            ch = FEED_CHANNELS[0]
        users = self._fetch_users(ch["extra"], 1) + self._fetch_users(ch["extra"], 2)
        live_users = [u for u in users if u.get("hlsPreviewUrl")]
        episodes = []
        seen = set()
        idx = 1
        for u in live_users:
            uname = str(u.get("username") or "")
            if not uname or uname in seen:
                continue
            seen.add(uname)
            ep_name = str(idx) + ". " + uname
            if u.get("countryCode"):
                ep_name += " (" + str(u.get("countryCode")) + ")"
            if u.get("age"):
                ep_name += " · " + str(u.get("age")) + "岁"
            ep_value = json.dumps(
                {"playUrl": str(u.get("hlsPreviewUrl") or ""), "uname": uname,
                 "pic": str(u.get("snapshotImageLink") or "")},
                ensure_ascii=False)
            episodes.append(clean_ep_name(ep_name) + "$" + ep_value)
            idx += 1
        if not episodes:
            placeholder = json.dumps({"playUrl": "", "uname": "None"}, ensure_ascii=False)
            episodes.append("暂无在线主播$" + placeholder)
        poster = ""
        if live_users:
            poster = str(live_users[0].get("snapshotImageLink") or "")
        if not poster:
            poster = make_svg_cover(*ch["cover"])
        content = self._summary(ch["name"], "连刷模式", FEED_LINE, ch["id"])
        content += "\n【连刷功能提示】在播放器中开启“自动连播”或直接手势上下划动选集，即可秒速无缝切台！"
        vod = {
            "vod_id": feed_id,
            "vod_name": ch["name"],
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_type": "📺 连刷直通车,🦋 蝴蝶专属,Cam4热门",
            "vod_remarks": BRAND_NAME + " | 共" + str(len(episodes)) + "位在线",
            "vod_content": content,
            "vod_play_from": FEED_LINE,
            "vod_play_url": "#".join(episodes),
        }
        return vod

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "")
        play_url, uname, _pic = self._parse_ref(raw)
        if not play_url:
            lookup = ""
            if uname and uname != "None":
                lookup = uname
            elif raw and "://" not in raw and not raw.startswith("feed_") and not raw.startswith("{"):
                lookup = raw
            if lookup:
                users = self._fetch_users("&username=" + quote(lookup, safe=""), 1)
                if users and users[0].get("hlsPreviewUrl"):
                    play_url = str(users[0].get("hlsPreviewUrl"))
        if play_url:
            return {"parse": 0, "url": play_url,
                    "header": {"User-Agent": UA, "Referer": self.host + "/"}}
        if uname and uname != "None":
            return {"parse": 1, "url": self.host + "/" + quote(uname, safe="")}
        return {"parse": 1, "url": self.host + "/"}

    def liveContent(self):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249989662&sig=31f04f0608de50a3
