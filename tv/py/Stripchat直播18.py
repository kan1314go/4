# Stripchat直播
import base64
import gzip
import http.cookiejar
import json
import math
import ssl
import urllib.parse
import urllib.request
import zlib

try:
    from base.spider import Spider as BaseSpider
except Exception:
    class BaseSpider(object):
        def getCache(self, key):
            return None

        def setCache(self, key, value):
            return "fail"

        def delCache(self, key):
            return "fail"

HOST = "https://stripchat.com"
API_URL = "https://go.mavrtracktor.com/api/models"
WORKER_URL = "https://strip.5568999.cc.cd/mouflon/"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PAGE_SIZE = 60
TIMEOUT = 5
SEARCH_TAGS = ["girls", "couples", "men", "trans"]
BRAND_NAME = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
PLAY_FROM = "蝴蝶专线"

CLASSES = [
    {"type_id": "continuous_feed", "type_name": "📺 连刷模式"},
    {"type_id": "girls/chinese", "type_name": "🇨🇳中国女孩"},
    {"type_id": "girls/japanese", "type_name": "🇯🇵日本女孩"},
    {"type_id": "girls/korean", "type_name": "🇰🇷韩国女孩"},
    {"type_id": "girls/vietnamese", "type_name": "🇻🇳越南女孩"},
    {"type_id": "girls/ukrainian", "type_name": "🇺🇦乌克兰女孩"},
    {"type_id": "girls/russian", "type_name": "🇷🇺俄罗斯女孩"},
    {"type_id": "girls/american", "type_name": "🇺🇸美国女孩"},
    {"type_id": "girls/colombian", "type_name": "🇨🇴哥伦比亚女孩"},
    {"type_id": "girls/german", "type_name": "🇩🇪德国女孩"},
    {"type_id": "girls/french", "type_name": "🇫🇷法国女孩"},
    {"type_id": "girls/uk-models", "type_name": "🇬🇧英国女孩"},
    {"type_id": "girls/canadian", "type_name": "🇨🇦加拿大女孩"},
    {"type_id": "girls/mexican", "type_name": "🇲🇽墨西哥女孩"},
    {"type_id": "girls/indian", "type_name": "🇮🇳印度女孩"},
    {"type_id": "girls/venezuelan", "type_name": "🇻🇪委内瑞拉女孩"},
    {"type_id": "girls/romanian", "type_name": "🇷🇴罗马尼亚女孩"},
    {"type_id": "girls/african", "type_name": "🌍非洲女孩"},
    {"type_id": "girls/spanish-speaking", "type_name": "🇪🇸西班牙女孩"},
    {"type_id": "girls/arab", "type_name": "🇸🇦阿拉伯女孩"},
    {"type_id": "girls/kenyan", "type_name": "🇰🇪肯尼亚女孩"},
    {"type_id": "girls/south-african", "type_name": "🇿🇦南非女孩"},
    {"type_id": "girls/brazilian", "type_name": "🇧🇷巴西女孩"},
    {"type_id": "girls/thai", "type_name": "🇹🇭泰国女孩"},
    {"type_id": "girls/italian", "type_name": "🇮🇹意大利女孩"},
    {"type_id": "girls/teens", "type_name": "少女18+"},
    {"type_id": "girls/young", "type_name": "鲜嫩青年22+"},
    {"type_id": "girls/milfs", "type_name": "熟女"},
    {"type_id": "girls/mature", "type_name": "成熟"},
    {"type_id": "girls/grannies", "type_name": "老奶奶"},
    {"type_id": "girls/white", "type_name": "白人"},
    {"type_id": "girls/asian", "type_name": "亚洲人"},
    {"type_id": "girls/latin", "type_name": "拉丁人"},
    {"type_id": "girls/ebony", "type_name": "黑珍珠"},
    {"type_id": "girls/new", "type_name": "最新女主播"},
    {"type_id": "girls", "type_name": "全部女主播"},
    {"type_id": "couples/chinese", "type_name": "中国情侣"},
    {"type_id": "couples/popular", "type_name": "热门情侣"},
    {"type_id": "couples/new", "type_name": "最新情侣"},
    {"type_id": "couples", "type_name": "全部情侣"},
    {"type_id": "men/popular", "type_name": "最受欢迎"},
    {"type_id": "men/gay-couples", "type_name": "男同伴侣"},
    {"type_id": "men/gays", "type_name": "男同聊天"},
    {"type_id": "men/straight", "type_name": "直男"},
    {"type_id": "men", "type_name": "全部男主播"},
    {"type_id": "trans/popular", "type_name": "热门跨性别"},
    {"type_id": "trans/new", "type_name": "最新跨性别"},
    {"type_id": "trans", "type_name": "全部跨性别"},
]
CLASS_NAME = {}
for _c in CLASSES:
    CLASS_NAME[_c["type_id"]] = _c["type_name"]

FEED_CHANNELS = [
    {"id": "feed_chinese", "name": "🇨🇳 华语佳丽·中国女孩连刷", "tag": "girls/chinese", "path": "/girls/chinese", "svg_title": "华语精选连刷", "svg_sub": "STRIPCHAT · 中国女孩专区", "c1": "#ff0844", "c2": "#ffb199"},
    {"id": "feed_asian", "name": "🌸 东方风情·亚洲专区连刷", "tag": "girls/asian", "path": "/girls/asian", "svg_title": "亚洲专区连刷", "svg_sub": "STRIPCHAT · 东方佳丽精选", "c1": "#f857a6", "c2": "#ff5858"},
    {"id": "feed_girls", "name": "🔥 全员热门·女主播连刷", "tag": "girls", "path": "/girls", "svg_title": "热门女主播连刷", "svg_sub": "STRIPCHAT · 极速换台切台", "c1": "#f107a3", "c2": "#7b2ff7"},
    {"id": "feed_couples", "name": "👩‍❤️‍👨 激情互动·情侣连刷", "tag": "couples", "path": "/couples", "svg_title": "情侣双人连刷", "svg_sub": "STRIPCHAT · 真实激情互动", "c1": "#fa709a", "c2": "#fee140"},
    {"id": "feed_trans", "name": "🌈 特色风情·跨性别连刷", "tag": "trans", "path": "/trans", "svg_title": "特色跨性别连刷", "svg_sub": "STRIPCHAT · 异域风情精选", "c1": "#654ea3", "c2": "#eaafc8"},
    {"id": "feed_men", "name": "🕺 活力型男·男主播连刷", "tag": "men", "path": "/men", "svg_title": "男主播精选连刷", "svg_sub": "STRIPCHAT · 阳光型男推荐", "c1": "#13547a", "c2": "#80d0c7"},
]


def _svg_cover(title, sub, c1, c2):
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" viewBox="0 0 600 340">' + '<defs>' + '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">' + '<stop offset="0%" stop-color="' + c1 + '" />' + '<stop offset="100%" stop-color="' + c2 + '" />' + '</linearGradient>' + '</defs>' + '<rect width="100%" height="100%" fill="url(#g)" />' + '<circle cx="300" cy="130" r="46" fill="rgba(255,255,255,0.18)" />' + '<polygon points="288,110 322,130 288,150" fill="#ffffff" />' + '<text x="50%" y="225" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="28" font-weight="bold" fill="#ffffff" text-anchor="middle">' + title + '</text>' + '<text x="50%" y="265" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="16" fill="rgba(255,255,255,0.85)" text-anchor="middle">' + sub + '</text>' + '</svg>'
    return "data:image/svg+xml;utf8," + urllib.parse.quote(svg, safe="~()*!'")


def _b64e(text):
    raw = base64.urlsafe_b64encode(str(text).encode("utf-8")).decode("ascii")
    return raw.rstrip("=")


def _b64d(text):
    try:
        pad = "=" * (-len(str(text)) % 4)
        return base64.urlsafe_b64decode((str(text) + pad).encode("ascii")).decode("utf-8", "ignore")
    except Exception:
        return ""


def _clean_episode_name(name):
    return str(name or "").replace("$", "＄").replace("#", "＃").strip()


def _brand_content(lines):
    block = ["🦋 Stripchat官方交流群：@tvshare23", "导演：🦋 蝴蝶影视", "当前主站：" + HOST, "━" * 28, "━" * 7]
    block.extend(lines)
    return "\n".join(block)


def _empty_page(page):
    return {"list": [], "page": page, "pagecount": 1, "limit": PAGE_SIZE, "total": 0}


class Spider(BaseSpider):
    def __init__(self):
        super(Spider, self).__init__()
        self.siteUrl = HOST
        self.siteName = "Stripchat直播"
        self.extend = ""
        self._ua = UA
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=self.ctx)
        )

    def init(self, extend=""):
        self.extend = extend or ""
        return True

    def getName(self):
        return self.siteName

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        if any(bad in low for bad in ("preview.mp4", "sample.mp4", "trailer.mp4", "native-ad")):
            return False
        return any(k in low for k in (".m3u8", ".mp4", ".flv", ".ts", ".mpd"))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        return True

    def _fetch_json(self, url):
        headers = {
            "User-Agent": self._ua,
            "Referer": HOST + "/",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with self.opener.open(req, timeout=TIMEOUT) as resp:
                    raw = resp.read()
                    enc = (resp.headers.get("Content-Encoding") or "").lower()
                    if raw[:2] == b"\x1f\x8b" or "gzip" in enc:
                        try:
                            raw = gzip.decompress(raw)
                        except Exception:
                            raw = zlib.decompress(raw, 31)
                    elif "deflate" in enc:
                        try:
                            raw = zlib.decompress(raw)
                        except Exception:
                            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                    text = raw.decode("utf-8", "ignore")
                    data = json.loads(text)
                    if isinstance(data, dict):
                        return data
                    return {}
            except Exception as e:
                if attempt == 0:
                    continue
                return {}
        return {}

    def _models_url(self, tag, limit, offset):
        t = urllib.parse.quote(str(tag or "girls"), safe="/")
        return API_URL + "?tag=" + t + "&forceClient=1&stripcashR=0&limit=" + str(limit) + "&usePreroll&webp=1&type=popular&timezone=Asia/Shanghai&offset=" + str(offset)

    def _rooms(self, data):
        models = data.get("models") if isinstance(data, dict) else None
        rooms = []
        seen = set()
        for m in models or []:
            if not isinstance(m, dict):
                continue
            if str(m.get("status") or "") != "public":
                continue
            sid = str(m.get("id") or "").strip()
            if not sid or sid in seen:
                continue
            seen.add(sid)
            pic = str(m.get("snapshotUrl") or m.get("popularSnapshotUrl") or m.get("previewUrlThumbBig") or "")
            try:
                viewers = int(m.get("viewersCount") or 0)
            except Exception:
                viewers = 0
            rooms.append({"id": sid, "name": str(m.get("username") or sid), "pic": pic, "viewers": viewers, "hd": bool(m.get("broadcastHD"))})
        return rooms

    def _room_token(self, room, catname):
        payload = {"id": room["id"], "name": room["name"], "pic": room.get("pic") or "", "viewers": room.get("viewers") or 0, "cat": catname or "", "hd": 1 if room.get("hd") else 0}
        return "room@@" + _b64e(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))

    def _room_from_token(self, raw):
        if str(raw or "").startswith("room@@"):
            text = _b64d(str(raw)[6:])
            try:
                info = json.loads(text) if text else {}
            except Exception:
                info = {}
            if isinstance(info, dict) and str(info.get("id") or ""):
                return {"id": str(info.get("id")), "name": str(info.get("name") or info.get("id")), "pic": str(info.get("pic") or ""), "viewers": info.get("viewers") or 0, "cat": str(info.get("cat") or ""), "hd": bool(info.get("hd"))}
            return {}
        if str(raw or "").isdigit():
            return {"id": str(raw), "name": str(raw), "pic": "", "viewers": 0, "cat": "", "hd": False}
        return {}

    def _vod_item(self, room, catname):
        if room.get("viewers"):
            remarks = BRAND_NAME + " | 👤" + str(room["viewers"]) + "人"
        else:
            remarks = BRAND_NAME + " | 正在直播"
        return {"vod_id": self._room_token(room, catname), "vod_name": room["name"], "vod_pic": room.get("pic") or "", "vod_remarks": remarks, "style": {"type": "rect", "ratio": 0.75}}

    def _feed_cover(self, channel):
        key = "sc_cover_" + channel["id"]
        try:
            cached = self.getCache(key)
        except Exception:
            cached = None
        if cached:
            return str(cached)
        data = self._fetch_json(self._models_url(channel["tag"], 10, 0))
        rooms = self._rooms(data)
        for room in rooms:
            if room.get("pic"):
                try:
                    self.setCache(key, room["pic"])
                except Exception:
                    pass
                return room["pic"]
        return ""

    def homeContent(self, filter=False):
        result = {"class": CLASSES}
        if filter:
            result["filters"] = {}
        return result

    def homeVideoContent(self):
        data = self._fetch_json(self._models_url("girls", PAGE_SIZE, 0))
        rooms = self._rooms(data)
        return {"list": [self._vod_item(r, CLASS_NAME.get("girls", "")) for r in rooms]}

    def categoryContent(self, tid, pg, filter=False, extend=None):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        if str(tid or "") == "continuous_feed":
            if page > 1:
                return _empty_page(page)
            items = []
            for ch in FEED_CHANNELS:
                cover = self._feed_cover(ch)
                if not cover:
                    cover = _svg_cover(ch["svg_title"], ch["svg_sub"], ch["c1"], ch["c2"])
                items.append({"vod_id": "feed@@" + ch["id"], "vod_name": ch["name"], "vod_pic": cover, "vod_remarks": BRAND_NAME + " | 自动切台", "style": {"type": "rect", "ratio": 0.75}})
            return {"list": items, "page": 1, "pagecount": 1, "limit": PAGE_SIZE, "total": len(items)}
        data = self._fetch_json(self._models_url(tid, PAGE_SIZE, (page - 1) * PAGE_SIZE))
        rooms = self._rooms(data)
        catname = CLASS_NAME.get(str(tid or ""), "")
        total = data.get("total") if isinstance(data, dict) else None
        if not rooms:
            return _empty_page(page)
        if isinstance(total, int) and total > 0:
            pagecount = int(math.ceil(total / float(PAGE_SIZE)))
            total_out = total
        elif len(rooms) >= PAGE_SIZE:
            pagecount = page + 1
            total_out = page * len(rooms) + 100
        else:
            pagecount = page
            total_out = (page - 1) * PAGE_SIZE + len(rooms)
        return {"list": [self._vod_item(r, catname) for r in rooms], "page": page, "pagecount": pagecount, "limit": PAGE_SIZE, "total": total_out}

    def detailContent(self, ids):
        if not ids or not ids[0]:
            return {"list": [], "msg": "缺少直播间 ID"}
        raw = str(ids[0])
        if raw.startswith("feed@@"):
            feed_id = raw.split("@@", 1)[1] if "@@" in raw else ""
            channel = None
            for ch in FEED_CHANNELS:
                if ch["id"] == feed_id:
                    channel = ch
                    break
            if channel is None:
                channel = FEED_CHANNELS[0]
            seen = set()
            live = []
            for offset in (0, 60):
                data = self._fetch_json(self._models_url(channel["tag"], 60, offset))
                for room in self._rooms(data):
                    if room["id"] not in seen:
                        seen.add(room["id"])
                        live.append(room)
            episodes = []
            for idx, room in enumerate(live, 1):
                episodes.append("%d. %s$play@@%s@@720p" % (idx, _clean_episode_name(room["name"]), room["id"]))
            pic = live[0]["pic"] if live else ""
            if not pic:
                pic = _svg_cover(channel["svg_title"], channel["svg_sub"], channel["c1"], channel["c2"])
            if not episodes:
                episodes = ["暂无在线主播$play@@empty"]
                vod = {"vod_id": raw, "vod_name": channel["name"], "vod_pic": pic, "vod_bg": pic, "vod_background": pic, "vod_banner": pic, "type_name": "📺 连刷模式", "vod_remarks": BRAND_NAME + " | 暂无在线主播", "vod_actor": BRAND_ACTOR, "vod_director": BRAND_DIRECTOR, "vod_content": _brand_content(["标题：" + channel["name"], "分类：📺 连刷模式", "片源：" + PLAY_FROM, "编号：" + channel["id"], "暂无在线主播"]), "vod_play_from": PLAY_FROM, "vod_play_url": "#".join(episodes), "style": {"type": "rect", "ratio": 0.75}}
                return {"list": [vod]}
            vod = {"vod_id": raw, "vod_name": channel["name"], "vod_pic": pic, "vod_bg": pic, "vod_background": pic, "vod_banner": pic, "type_name": "📺 连刷模式", "vod_remarks": BRAND_NAME + " | 共" + str(len(episodes)) + "位在线", "vod_actor": BRAND_ACTOR, "vod_director": BRAND_DIRECTOR, "vod_content": _brand_content(["标题：" + channel["name"], "分类：📺 连刷模式", "片源：" + PLAY_FROM, "编号：" + channel["id"], "在播放器中开启“自动连播”或直接手势上下划动选集，即可秒速无缝切台！"]), "vod_play_from": PLAY_FROM, "vod_play_url": "#".join(episodes), "style": {"type": "rect", "ratio": 0.75}}
            return {"list": [vod]}
        room = self._room_from_token(raw)
        if not room or not room.get("id"):
            return {"list": [], "msg": "缺少直播间 ID"}
        sid = room["id"]
        name = room["name"]
        pic = room.get("pic") or ""
        catname = room.get("cat") or ""
        try:
            viewers = int(room.get("viewers") or 0)
        except Exception:
            viewers = 0
        episodes = ["720P超清正片 (推荐)$play@@%s@@720p" % sid, "1080P原画正片$play@@%s@@source" % sid]
        vod = {"vod_id": raw, "vod_name": name, "vod_pic": pic, "vod_bg": pic, "vod_background": pic, "vod_banner": pic, "type_name": catname, "vod_year": "", "vod_area": "", "vod_remarks": BRAND_NAME + " | 直播中", "vod_actor": BRAND_ACTOR, "vod_director": BRAND_DIRECTOR, "vod_content": _brand_content(["标题：" + name, "分类：" + catname, "片源：" + PLAY_FROM, "编号：" + sid, "观看人数：" + str(viewers) + "人", "直播状态：正在公开直播中", "如遇卡顿可在右上角切换主站节点。"]), "vod_play_from": PLAY_FROM, "vod_play_url": "#".join(episodes), "style": {"type": "rect", "ratio": 0.75}}
        return {"list": [vod]}

    def searchContent(self, key, quick=False, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        kw = str(key or "").strip().lower()
        if page > 1 or not kw:
            return _empty_page(page)
        found = []
        seen = set()
        for tag in SEARCH_TAGS:
            data = self._fetch_json(self._models_url(tag, 200, 0))
            for room in self._rooms(data):
                if kw in room["name"].lower() and room["id"] not in seen:
                    seen.add(room["id"])
                    found.append(self._vod_item(room, CLASS_NAME.get(tag, "")))
        found = found[:60]
        return {"list": found, "page": 1, "pagecount": 1, "limit": PAGE_SIZE, "total": len(found)}

    def playerContent(self, flag, id, vipFlags=None):
        pid = str(id or "").strip()
        if pid == "play@@empty":
            return {"parse": 0, "msg": "暂无在线主播"}
        if pid.startswith("play@@"):
            parts = pid.split("@@")
            if len(parts) != 3:
                return {"parse": 0, "msg": "直播间 ID 无效"}
            sid = parts[1]
            quality = parts[2]
            if not sid.isdigit():
                return {"parse": 0, "msg": "直播间 ID 无效"}
            if quality == "720p":
                url = WORKER_URL + sid + "/720p.m3u8"
            elif quality == "source":
                url = WORKER_URL + sid + "/source.m3u8"
            else:
                return {"parse": 0, "msg": "直播间 ID 无效"}
            return {"parse": 0, "url": url, "header": {"User-Agent": self._ua, "Referer": HOST + "/", "Origin": HOST}}
        return {"parse": 0, "msg": "直播间 ID 无效"}

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250177197&sig=7287743833cb31c8
