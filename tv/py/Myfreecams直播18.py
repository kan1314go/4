# -*- coding: utf-8 -*-
# Myfreecams直播

import json
import re
import time
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://app.myfreecams.com"
API_BASE = "https://api-edge.myfreecams.com/"
UA = "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 Chrome/124 Mobile Safari/537.36"
BRAND = "蝴蝶影视"
PAGE_SIZE = 60
FEED_POOL_MAX = 100
TIMEOUT = 8
ROOMS_TTL = 45

CLASSES = [
    ("continuous_feed", "📺 连刷模式"),
    ("live", "在线直播"),
    ("all", "全部房间"),
]


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
    return "data:image/svg+xml;utf8," + quote(svg, safe="")


FEED_CHANNELS = [
    {
        "id": "feed_hot",
        "name": "🔥 人气榜单·高热主播连刷",
        "filterType": "hot",
        "path": "/",
        "fallbackPoster": _svg_cover("人气主播连刷", "MYFREECAMS · 高热切台", "#ff0844", "#ffb199"),
    },
    {
        "id": "feed_all",
        "name": "✨ 全员在线·极速切台连刷",
        "filterType": "all",
        "path": "/models",
        "fallbackPoster": _svg_cover("全员热门连刷", "MYFREECAMS · 精彩全聚合", "#6a11cb", "#2575fc"),
    },
    {
        "id": "feed_interactive",
        "name": "💬 话题畅聊·互动房间连刷",
        "filterType": "topic",
        "path": "/topics",
        "fallbackPoster": _svg_cover("互动房间连刷", "MYFREECAMS · 在线畅聊", "#f857a6", "#ff5858"),
    },
]
FEED_BY_ID = dict((c["id"], c) for c in FEED_CHANNELS)

SERVER_NUM_RE = re.compile(r"(\d+)$")


def _sanitize_ep_name(name):
    return str(name).replace("$", "_").replace("#", "_")


def _to_page(pg):
    try:
        p = int(pg)
    except Exception:
        p = 1
    return p if p > 0 else 1


def _avatar(rid):
    rid = str(rid or "")
    if not rid.isdigit():
        return ""
    return "https://img.mfcimg.com/photos2/" + rid[0:3] + "/" + rid + "/avatar.90x90.jpg"


def _cover(rid, snap, server):
    if snap:
        return snap
    m = SERVER_NUM_RE.search(str(server or ""))
    if str(rid).isdigit() and m:
        return "https://snap.mfcimg.com/snapimg/" + m.group(1) + "/853x480/mfc_a_" + str(100000000 + int(rid))
    return _avatar(rid)


def _enc_env(env):
    return json.dumps(env, ensure_ascii=False, separators=(",", ":"))


def _dec_env(raw):
    raw = str(raw or "").strip()
    if raw.startswith("{"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass
    if raw:
        return {"rid": raw}
    return {}


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST
        self._rooms = None
        self._rooms_at = 0.0

    def getName(self):
        return "Myfreecams直播"

    def init(self, extend=""):
        cfg = {}
        if isinstance(extend, dict):
            cfg = extend
        elif isinstance(extend, str) and extend:
            text = extend.strip()
            if text.startswith("http"):
                cfg = {"host": text}
            else:
                try:
                    cfg = json.loads(text)
                except Exception:
                    cfg = {}
        custom = ""
        if isinstance(cfg, dict):
            custom = str(cfg.get("host", "") or "").strip()
        if custom and custom.startswith("http"):
            self.host = custom.rstrip("/")

    def _online_rooms(self):
        now = time.time()
        if self._rooms is not None and now - self._rooms_at < ROOMS_TTL:
            return self._rooms
        resp = requests.get(
            API_BASE + "online_models",
            headers={
                "User-Agent": UA,
                "Accept": "application/json",
                "Referer": "https://app.myfreecams.com/",
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        obj = resp.json()
        rows = obj.get("result") if isinstance(obj, dict) else None
        out = []
        seen = set()
        for u in rows or []:
            if not isinstance(u, dict):
                continue
            rid = str(u.get("user_id") or "")
            name = str(u.get("username") or rid)
            if not rid or not name or rid in seen:
                continue
            seen.add(rid)
            try:
                viewers = int(u.get("room_count") or 0)
            except Exception:
                viewers = 0
            out.append({
                "id": rid,
                "name": name,
                "slug": name,
                "pic": _cover(rid, u.get("snap_url") or "", u.get("server_name") or ""),
                "topic": str(u.get("topic") or ""),
                "viewers": viewers,
                "server": str(u.get("server_name") or ""),
            })
        self._rooms = out
        self._rooms_at = now
        return out

    def _feed_pool(self, ch, rooms):
        if ch["filterType"] == "hot":
            return sorted(rooms, key=lambda r: -(r["viewers"] or 0))
        if ch["filterType"] == "topic":
            pool = [r for r in rooms if (r["topic"] or "").strip()]
            if len(pool) < 20:
                pool = rooms
            return pool
        return rooms

    def _room_card(self, r):
        topic = r["topic"] or ""
        if topic:
            remark = (topic + " · " + str(r["viewers"]) + "人") if r["viewers"] else topic
        else:
            remark = "在线直播"
        return {
            "vod_id": r["id"],
            "vod_name": r["name"],
            "vod_pic": r["pic"],
            "vod_remarks": BRAND + " | " + remark[0:80],
        }

    def _feed_card(self, ch, rooms):
        pool = self._feed_pool(ch, rooms)
        poster = pool[0]["pic"] if pool else ch["fallbackPoster"]
        return {
            "vod_id": ch["id"],
            "vod_name": ch["name"],
            "vod_pic": poster,
            "vod_remarks": BRAND + " | 自动切台",
        }

    def _summary(self, body):
        lines = [
            "🦋 Myfreecams直播官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        if body:
            lines.append(body)
        return "\n".join(lines)

    def _page(self, page, cards, limit, total):
        if total <= 0:
            return {"page": page, "pagecount": page, "limit": limit, "total": 0, "list": []}
        pagecount = (total + limit - 1) // limit
        return {"page": page, "pagecount": pagecount, "limit": limit, "total": total, "list": cards}

    def _empty_page(self, page):
        return {"page": page, "pagecount": page, "limit": PAGE_SIZE, "total": 0, "list": []}

    def homeContent(self, filter):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in CLASSES]}

    def homeVideoContent(self):
        try:
            rooms = self._online_rooms()
        except Exception:
            return {"list": []}
        return {"list": [self._room_card(r) for r in rooms[0:PAGE_SIZE]]}

    def categoryContent(self, tid, pg, filter, extend):
        page = _to_page(pg)
        cid = str(tid or "continuous_feed")
        if cid == "continuous_feed":
            if page > 1:
                return self._empty_page(page)
            try:
                rooms = self._online_rooms()
            except Exception:
                return self._empty_page(page)
            cards = [self._feed_card(ch, rooms) for ch in FEED_CHANNELS]
            return self._page(page, cards, len(cards), len(cards))
        try:
            rooms = self._online_rooms()
        except Exception:
            return self._empty_page(page)
        start = (page - 1) * PAGE_SIZE
        cards = [self._room_card(r) for r in rooms[start:start + PAGE_SIZE]]
        return self._page(page, cards, PAGE_SIZE, len(rooms))

    def searchContent(self, key, quick, pg="1"):
        page = _to_page(pg)
        kw = str(key or "").strip().lower()
        if not kw or page > 1:
            return self._empty_page(page)
        try:
            rooms = self._online_rooms()
        except Exception:
            return self._empty_page(page)
        matched = [r for r in rooms if kw in (r["name"] + " " + r["topic"]).lower()]
        cards = [self._room_card(r) for r in matched]
        return self._page(page, cards, len(cards) if cards else PAGE_SIZE, len(cards))

    def detailContent(self, ids):
        raw = ""
        if isinstance(ids, (list, tuple)) and ids:
            raw = str(ids[0])
        elif isinstance(ids, str):
            raw = ids
        if raw.startswith("feed_"):
            return self._detail_feed(raw)
        return self._detail_room(raw)

    def _detail_feed(self, raw):
        ch = FEED_BY_ID.get(raw) or FEED_CHANNELS[0]
        try:
            rooms = self._online_rooms()
        except Exception as e:
            return {"list": [], "msg": str(e) or "页面请求失败"}
        pool = self._feed_pool(ch, rooms)
        eps = []
        for i, r in enumerate(pool[0:FEED_POOL_MAX]):
            title = str(i + 1) + ". " + r["name"]
            if r["viewers"]:
                title += " (" + str(r["viewers"]) + "人)"
            eps.append({
                "name": _sanitize_ep_name(title),
                "value": _enc_env({"rid": r["id"], "slug": r["slug"], "server": r["server"]}),
                "still": r["pic"],
            })
        if not eps:
            eps.append({
                "name": "暂无在线主播",
                "value": _enc_env({"rid": ""}),
                "still": "",
            })
        poster = eps[0]["still"] or ch["fallbackPoster"]
        vod = {
            "vod_id": raw,
            "vod_name": ch["name"],
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_content": self._summary("【连刷功能提示】在播放器中开启“自动连播”或直接手势上下划动选集，即可秒速无缝切台！"),
            "vod_class": "📺 连刷直通车,🦋 蝴蝶专属,MyFreeCams热门",
            "vod_actor": "🦋 TG交流群,🌐 官方发布频道,🚀 官方自愈节点",
            "vod_remarks": BRAND + " | 共" + str(len(eps)) + "位在线",
            "vod_play_from": "🦋 连续刷流专线",
            "vod_play_url": "#".join(ep["name"] + "$" + ep["value"] for ep in eps),
        }
        return {"list": [vod]}

    def _detail_room(self, raw):
        rid = raw
        try:
            rooms = self._online_rooms()
        except Exception as e:
            return {"list": [], "msg": str(e) or "页面请求失败"}
        info = None
        for r in rooms:
            if r["id"] == rid:
                info = r
                break
        if info is None:
            info = {
                "id": rid,
                "name": rid,
                "slug": rid,
                "pic": _avatar(rid),
                "topic": "",
                "viewers": 0,
                "server": "",
            }
        body = "\n".join([
            "主播名: " + info["name"],
            "房间ID: " + rid,
            "房间话题: " + (info["topic"] or "在线直播中"),
            "在线观众: " + ((str(info["viewers"]) + " 人") if info["viewers"] else "多人群聊中"),
        ])
        ep_value = _enc_env({"rid": rid, "slug": info["slug"], "server": info["server"]})
        vod = {
            "vod_id": raw,
            "vod_name": info["name"],
            "vod_pic": info["pic"],
            "vod_bg": info["pic"],
            "vod_background": info["pic"],
            "vod_banner": info["pic"],
            "vod_content": self._summary(body),
            "vod_class": "MyFreeCams,在线直播,真人互动",
            "vod_actor": "🦋 TG交流群,🌐 官方发布频道,🚀 官方自愈节点",
            "vod_remarks": BRAND + " | 直播中",
            "vod_play_from": "🦋 蝴蝶超清专线",
            "vod_play_url": "进入直播$" + ep_value,
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        env = _dec_env(id)
        rid = str(env.get("rid") or "")
        slug = str(env.get("slug") or rid)
        server = str(env.get("server") or "")
        try:
            rooms = self._online_rooms()
        except Exception as e:
            return {"parse": 0, "msg": str(e) or "页面请求失败"}
        for r in rooms:
            if r["id"] == rid:
                slug = r["slug"]
                server = r["server"]
                break
        m = SERVER_NUM_RE.search(server or "")
        if m and rid.isdigit():
            stream = "mfc_a_" + str(100000000 + int(rid))
            url = ("https://edgevideo.myfreecams.com/llhls/NxServer/" + m.group(1)
                   + "/ngrp:" + stream + ".f4v_cmaf/playlist_sfm4s.m3u8")
            return {
                "parse": 0,
                "url": url,
                "header": {
                    "User-Agent": UA,
                    "Referer": "https://m.myfreecams.com/" + quote(slug, safe=""),
                },
            }
        return {"parse": 0, "msg": "主播已下线或分配服务器未就绪"}

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250135829&sig=830d65a3f7d9ecee
