# -*- coding: utf-8 -*-
# 韩国Pandalive直播18

import json
import re
import time
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://5721004.xyz"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
BRAND = "蝴蝶影视"
TIMEOUT = 8
PAGE_SIZE = 30
SEARCH_LIMIT = 50
FEED_LIMIT = 100
LIST_TTL = 120
PLAY_HEADERS = {
    "User-Agent": UA,
    "Referer": "https://www.pandalive.co.kr/",
    "Origin": "https://www.pandalive.co.kr",
}
DETAIL_ACTORS = "🦋 TG交流群,🌐 官方发布频道,🚀 官方自愈节点"
ROOM_GENRES = "PandaLive,韩国女主播,高清秒播"
FEED_GENRES = "📺 连刷直通车,🦋 蝴蝶专属,韩国直播"
ROOM_FROM = "🦋 蝴蝶超清专线"
FEED_FROM = "🦋 连续刷流专线"
OFFLINE_MSG = "直播信号已离线或房间不存在"
STREAM_DEAD_MSG = "直播流已失效或主播已下播"

CLASSES = [
    {"type_id": "continuous_feed", "type_name": "📺 连刷模式"},
    {"type_id": "pandalive", "type_name": "🐼 PandaTV"},
]

TYPE_OPTS = [
    ("全部", "all"),
    ("🔞 19+", "adult"),
    ("🔐 密碼房", "pw"),
    ("💎 粉絲房", "fan"),
    ("📼 錄播", "recorded"),
]

SORT_OPTS = [
    ("觀眾量 ↓", "user-desc"),
    ("實時熱度 ↓", "totalScoreCnt-desc"),
    ("關注量 ↓", "bookmarkCnt-desc"),
    ("默認排序", "default"),
]

FILTERS = {
    "pandalive": [
        {"key": "type", "name": "類型", "init": "all",
         "value": [{"n": n, "v": v} for n, v in TYPE_OPTS]},
        {"key": "sort", "name": "排序", "init": "default",
         "value": [{"n": n, "v": v} for n, v in SORT_OPTS]},
    ]
}

FEED_CHANNELS = [
    {"id": "feed_hot", "name": "🔥 人气榜单·高热主播连刷", "filterType": "hot",
     "svg": ("人气主播连刷", "PandaLive · 观众热度切台", "#ff0844", "#ffb199")},
    {"id": "feed_adult", "name": "🔞 限制专属·19+专区连刷", "filterType": "adult",
     "svg": ("19+激情连刷", "PandaLive · 专属限制级切台", "#f107a3", "#7b2ff7")},
    {"id": "feed_all", "name": "✨ 全员在线·极速切台连刷", "filterType": "all",
     "svg": ("全员热门连刷", "PandaLive · 精彩全聚合", "#6a11cb", "#2575fc")},
]
FEED_BY_ID = {c["id"]: c for c in FEED_CHANNELS}


def _svg_cover(title, sub, c1, c2):
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


def _sanitize_ep_name(name):
    return str(name).replace("$", "_").replace("#", "_")


def _to_page(pg):
    try:
        p = int(pg)
    except Exception:
        p = 1
    return p if p > 0 else 1


def _page_form(page, cards, limit, total):
    pagecount = (total + limit - 1) // limit if total > 0 else page
    return {"page": page, "pagecount": pagecount, "limit": limit, "total": total, "list": cards}


def _empty_page(page, limit):
    return {"page": page, "pagecount": page, "limit": limit, "total": 0, "list": []}


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST
        self._list_cache = None
        self._list_at = 0.0

    def getName(self):
        return "韩国Pandalive直播"

    def init(self, extend=""):
        host = ""
        if extend:
            s = str(extend).strip()
            if s.startswith("{"):
                try:
                    obj = json.loads(s)
                    if isinstance(obj, dict):
                        host = str(obj.get("host") or "").strip()
                except Exception:
                    host = ""
            elif s.startswith("http"):
                host = s
        if host.startswith("http"):
            self.host = host.rstrip("/")

    def _fetch_text(self, url):
        r = requests.get(url, headers={"User-Agent": UA, "Referer": self.host + "/"}, timeout=TIMEOUT)
        return r.text or ""

    def _fetch_list(self):
        text = self._fetch_text(self.host + "/player/list.m3u")
        meta = {}
        lines = str(text or "").split("\n")
        for i, line in enumerate(lines):
            if line.startswith("#EXTINF") and i + 1 < len(lines):
                parts = line.split(",")
                if len(parts) >= 2:
                    uid = parts[1].strip()
                    nick_meta = ",".join(parts[2:]).strip() if len(parts) > 2 else ""
                    tags = re.findall(r"\[([^\]]+)\]", nick_meta)
                    nick = re.sub(r"\[[^\]]*\]", "", nick_meta).strip() or uid
                    meta[uid] = {
                        "url": lines[i + 1].strip(),
                        "tags": tags,
                        "nick": nick,
                        "isRecorded": "录" in tags,
                        "isFan": "粉" in tags,
                    }
        raw = []
        try:
            obj = json.loads(self._fetch_text(self.host + "/player/list.json") or "")
            if isinstance(obj, dict) and isinstance(obj.get("list"), list):
                raw = obj["list"]
        except Exception:
            raw = []
        by_uid = {}
        for it in raw:
            if isinstance(it, dict):
                by_uid[str(it.get("userId"))] = it
        out = []
        for uid, mm in meta.items():
            m = by_uid.get(uid)
            if not m:
                continue
            nick = m.get("userNick") or mm["nick"] or uid
            tags = list(mm["tags"])
            if m.get("isAdult"):
                tags.append("19+")
            status = BRAND + " | 👤 " + str(m.get("user") or 0)
            if tags:
                status += " " + " ".join("[" + t + "]" for t in tags)
            out.append({
                "id": "live_" + uid,
                "uid": uid,
                "nick": nick,
                "title": "📺 " + nick,
                "poster": m.get("thumbUrl") or "",
                "status": status,
                "summary": m.get("title") or (nick + " 的直播"),
                "isAdult": bool(m.get("isAdult")),
                "isPw": bool(m.get("isPw")),
                "type": m.get("type") or "",
                "isRecorded": mm["isRecorded"],
                "isFan": mm["isFan"],
                "userCount": int(m.get("user") or 0),
                "score": int(m.get("totalScoreCnt") or 0),
                "bookmark": int(m.get("bookmarkCnt") or 0),
                "streamUrl": mm["url"],
            })
        return out

    def _load_list(self):
        now = time.time()
        if self._list_cache is not None and now - self._list_at < LIST_TTL:
            return self._list_cache
        items = self._fetch_list()
        if items:
            self._list_cache = items
            self._list_at = now
        return items

    def _summary(self, body):
        lines = [
            "🦋 韩国Pandalive直播官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        if body:
            lines.append(body)
        return "\n".join(lines)

    def _card(self, v):
        return {
            "vod_id": v["id"],
            "vod_name": v["title"],
            "vod_pic": v["poster"],
            "vod_remarks": v["status"],
        }

    def _feed_pool(self, ch, lst):
        if ch["filterType"] == "hot":
            return sorted(lst, key=lambda v: -v["userCount"])
        if ch["filterType"] == "adult":
            return [v for v in lst if v["isAdult"]]
        return list(lst)

    def _feed_cards(self):
        try:
            lst = self._load_list()
        except Exception:
            lst = []
        cards = []
        for ch in FEED_CHANNELS:
            pool = self._feed_pool(ch, lst)
            top = pool[0] if pool else (lst[0] if lst else None)
            poster = (top["poster"] if top else "") or _svg_cover(*ch["svg"])
            cards.append({
                "vod_id": ch["id"],
                "vod_name": ch["name"],
                "vod_pic": poster,
                "vod_remarks": BRAND + " | 自动切台",
            })
        return cards

    def homeContent(self, filter):
        result = {"class": [dict(c) for c in CLASSES]}
        if filter:
            result["filters"] = FILTERS
        return result

    def homeVideoContent(self):
        return {"list": self._feed_cards()}

    def categoryContent(self, tid, pg, filter, extend):
        page = _to_page(pg)
        cid = str(tid or "")
        if cid == "continuous_feed":
            if page > 1:
                return _empty_page(page, 3)
            cards = self._feed_cards()
            return _page_form(page, cards, len(cards), len(cards))
        if cid != "pandalive":
            return _empty_page(page, PAGE_SIZE)
        try:
            lst = list(self._load_list())
        except Exception:
            lst = []
        ext = extend if isinstance(extend, dict) else {}
        ft = str(ext.get("type") or "all")
        if ft == "adult":
            lst = [v for v in lst if v["isAdult"]]
        elif ft == "pw":
            lst = [v for v in lst if v["isPw"]]
        elif ft == "fan":
            lst = [v for v in lst if v["type"] == "fan" or v["isFan"]]
        elif ft == "recorded":
            lst = [v for v in lst if v["isRecorded"]]
        st = str(ext.get("sort") or "default")
        if st == "user-desc":
            lst.sort(key=lambda v: -v["userCount"])
        elif st == "totalScoreCnt-desc":
            lst.sort(key=lambda v: -v["score"])
        elif st == "bookmarkCnt-desc":
            lst.sort(key=lambda v: -v["bookmark"])
        total = len(lst)
        start = (page - 1) * PAGE_SIZE
        cards = [self._card(v) for v in lst[start:start + PAGE_SIZE]]
        return _page_form(page, cards, PAGE_SIZE, total)

    def searchContent(self, key, quick, pg="1"):
        page = _to_page(pg)
        kw = str(key or "").strip().lower()
        if not kw or page > 1:
            return _empty_page(page, SEARCH_LIMIT)
        try:
            lst = self._load_list()
        except Exception:
            lst = []
        matched = [v for v in lst
                   if kw in v["title"].lower() or kw in v["uid"].lower()][:SEARCH_LIMIT]
        if not matched:
            return _empty_page(page, SEARCH_LIMIT)
        cards = [self._card(v) for v in matched]
        return {"page": page, "pagecount": 1,
                "limit": len(cards), "total": len(cards), "list": cards}

    def _envelope(self, v):
        return json.dumps({"playUrl": v["streamUrl"], "vid": v["id"], "uid": v["uid"]},
                          ensure_ascii=False)

    def detailContent(self, ids):
        raw = ""
        if isinstance(ids, (list, tuple)) and ids:
            raw = str(ids[0])
        elif isinstance(ids, str):
            raw = ids
        if raw in FEED_BY_ID or raw.startswith("feed_"):
            return self._detail_feed(raw)
        return self._detail_room(raw)

    def _detail_feed(self, raw):
        ch = FEED_BY_ID.get(raw) or FEED_CHANNELS[0]
        lst = self._load_list()
        pool = self._feed_pool(ch, lst)
        if ch["filterType"] == "adult" and not pool:
            pool = list(lst)
        eps = []
        seen = set()
        for v in pool[:FEED_LIMIT]:
            if not v["streamUrl"] or v["streamUrl"] in seen:
                continue
            seen.add(v["streamUrl"])
            name = str(len(eps) + 1) + ". " + (v["nick"] or re.sub(r"^📺\s*", "", v["title"]))
            eps.append({"name": _sanitize_ep_name(name), "value": self._envelope(v),
                        "still": v["poster"]})
        if not eps:
            eps.append({"name": "暂无在线房间",
                        "value": json.dumps({"playUrl": "", "vid": ""}, ensure_ascii=False),
                        "still": ""})
        count = len(eps)
        body = "【连刷功能提示】在播放器中开启“自动连播”或直接手势上下划动选集，即可秒速无缝切台！"
        poster = eps[0]["still"] or _svg_cover(*ch["svg"])
        vod = {
            "vod_id": raw,
            "vod_name": ch["name"],
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_content": self._summary(body),
            "vod_remarks": BRAND + " | 共" + str(count) + "位在线",
            "vod_actor": DETAIL_ACTORS,
            "vod_class": FEED_GENRES,
            "vod_play_from": FEED_FROM,
            "vod_play_url": "#".join(e["name"] + "$" + e["value"] for e in eps),
        }
        return {"list": [vod]}

    def _detail_room(self, raw):
        lst = self._load_list()
        idx = -1
        for i, x in enumerate(lst):
            if x["id"] == raw:
                idx = i
                break
        if idx < 0 or not lst[idx]["streamUrl"]:
            return {"list": [], "msg": OFFLINE_MSG}
        v = lst[idx]
        eps = []
        for x in lst[idx:]:
            if not x["streamUrl"]:
                continue
            eps.append({"name": _sanitize_ep_name(x["title"]), "value": self._envelope(x)})
        body = ("主播名: " + v["title"] + "\n房间ID: " + v["uid"] +
                "\n房间简介: " + (v["summary"] or "无特别说明") +
                "\n如遇卡顿可在右上角切换主站节点。")
        vod = {
            "vod_id": raw,
            "vod_name": v["title"],
            "vod_pic": v["poster"],
            "vod_bg": v["poster"],
            "vod_background": v["poster"],
            "vod_banner": v["poster"],
            "vod_content": self._summary(body),
            "vod_remarks": v["status"],
            "vod_actor": DETAIL_ACTORS,
            "vod_class": ROOM_GENRES,
            "vod_play_from": ROOM_FROM,
            "vod_play_url": "#".join(e["name"] + "$" + e["value"] for e in eps),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        env = {}
        if raw.startswith("{"):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    env = parsed
            except Exception:
                env = {}
        play_url = str(env.get("playUrl") or "")
        if not play_url:
            vid = str(env.get("vid") or raw)
            try:
                lst = self._load_list()
            except Exception:
                lst = []
            for x in lst:
                if x["id"] == vid and x["streamUrl"]:
                    play_url = x["streamUrl"]
                    break
        if not play_url:
            return {"parse": 0, "msg": STREAM_DEAD_MSG}
        return {"parse": 0, "url": play_url, "header": dict(PLAY_HEADERS)}

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249612356&sig=4c397bee927831e3
