#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import gzip
import zlib
import ssl
import http.cookiejar
import urllib.request
import urllib.parse

try:
    from base.spider import Spider as SpiderBase
except Exception:
    class SpiderBase(object):
        def getCache(self, key):
            return None

        def setCache(self, key, value):
            return "fail"

        def delCache(self, key):
            return "fail"


def _format_remarks(brand, meta):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


class Spider(SpiderBase):
    def __init__(self, *args, **kwargs):
        try:
            super(Spider, self).__init__(*args, **kwargs)
        except Exception:
            try:
                super(Spider, self).__init__()
            except Exception:
                pass

        self.siteName = "百年直播"
        self.siteUrl = "http://api.vipmisss.com:81/xcdsw"
        self.tgGroup = "https://t.me/tvshare23"
        self.brandName = "蝴蝶影视"
        self.brandActor = "🦋 TG群: @tvshare23"
        self.brandDirector = "🦋 蝴蝶影视"
        self.lineName = "🦋 蝴蝶超清专线"
        self.feedLineName = "🦋 连续刷流专线"
        self.cacheKeyPlatforms = "lytvs_bainian_platforms_py_v1"
        self._ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        self.options = {}

        self.feedChannels = [
            {
                "id": "feed_hot",
                "name": "🔥 全网聚合·热门直播连刷",
                "fallbackPoster": "https://dummyimage.com/600x340/ff0844/ffffff.png&text=HOT_LIVE_FEED"
            },
            {
                "id": "feed_top_platforms",
                "name": "✨ 精选大台·多平台全连刷",
                "fallbackPoster": "https://dummyimage.com/600x340/6a11cb/ffffff.png&text=TOP_PLATFORMS_FEED"
            }
        ]

        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=self.ctx)
        )

    def init(self, extend=""):
        if isinstance(extend, dict):
            self.options = extend
        elif isinstance(extend, str) and extend.strip():
            ext_str = extend.strip()
            if ext_str.startswith("http"):
                self.siteUrl = ext_str.rstrip("/")
            else:
                try:
                    self.options = json.loads(ext_str)
                except Exception:
                    self.options = {}
        host = self.options.get("host", "") if isinstance(self.options, dict) else ""
        if isinstance(host, str) and host.strip().startswith("http"):
            self.siteUrl = host.strip().rstrip("/")
        return True

    def getName(self):
        return self.siteName

    def isVideoFormat(self, url):
        if not url:
            return False
        low = str(url).lower()
        return any(ext in low for ext in (".m3u8", ".mp4", ".flv", ".mkv", ".ts", ".mpd"))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        self.options = {}

    def _clean_text(self, val):
        if val is None:
            return ""
        s = re.sub(r"<[^>]+>", "", str(val))
        s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        s = s.replace("&quot;", '"').replace("&#039;", "'").replace("&#39;", "'").replace("&nbsp;", " ")
        s = re.sub(r"[\$#\r\n\t]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    def _abs_img(self, img):
        if not img:
            return ""
        u = str(img).strip().replace("\\/", "/")
        if u.startswith("http"):
            return u
        if u.startswith("//"):
            return "http:" + u
        if u.startswith("/"):
            return "%s%s" % (self.siteUrl, u)
        return "%s/%s" % (self.siteUrl, u)

    def _api_json(self, path):
        clean_path = path if str(path).startswith("/") else ("/%s" % str(path))
        url = "%s%s" % (self.siteUrl, clean_path)
        headers = {
            "User-Agent": self._ua,
            "Referer": "%s/" % self.siteUrl,
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with self.opener.open(req, timeout=8) as resp:
                    if resp.getcode() >= 400:
                        continue
                    raw = resp.read()
                    enc = getattr(resp, "headers", {}).get("Content-Encoding", "")
                    if raw.startswith(b"\x1f\x8b") or enc == "gzip":
                        raw = gzip.decompress(raw)
                    elif enc == "deflate":
                        try:
                            raw = zlib.decompress(raw)
                        except Exception:
                            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                    text = raw.decode("utf-8", errors="ignore")
                    data = json.loads(text)
                    if isinstance(data, dict):
                        return data
            except Exception:
                if attempt == 0:
                    continue
                break
        return {}

    def _get_platforms(self):
        try:
            cached = self.getCache(self.cacheKeyPlatforms)
            if isinstance(cached, str) and cached:
                parsed = json.loads(cached)
                if isinstance(parsed, list) and parsed:
                    return parsed
        except Exception:
            pass

        d = self._api_json("/json.txt")
        pts = d.get("pingtai", []) if isinstance(d, dict) else []
        out = []
        seen = set()
        if isinstance(pts, list):
            for pt in pts:
                if not isinstance(pt, dict):
                    continue
                raw_addr = str(pt.get("address") or "").strip().lstrip("/")
                name = self._clean_text(pt.get("title"))
                if not raw_addr or not name or raw_addr in seen:
                    continue
                seen.add(raw_addr)
                out.append({
                    "id": raw_addr,
                    "name": name,
                    "icon": self._abs_img(pt.get("xinimg") or pt.get("img") or "")
                })

        if out:
            try:
                self.setCache(self.cacheKeyPlatforms, json.dumps(out, ensure_ascii=False))
            except Exception:
                pass
        return out

    def _fetch_platform_rooms(self, platform_id):
        d = self._api_json("/%s" % str(platform_id).lstrip("/"))
        raw_list = d.get("zhubo", []) if isinstance(d, dict) else []
        rooms = []
        if isinstance(raw_list, list):
            for idx, zb in enumerate(raw_list):
                if not isinstance(zb, dict):
                    continue
                addr = str(zb.get("address") or "").strip()
                if not addr or "rtmp" in addr.lower():
                    continue
                title = self._clean_text(zb.get("title")) or ("主播 %d" % (idx + 1))
                img = self._abs_img(zb.get("img") or "")
                rooms.append({
                    "title": title,
                    "playUrl": addr,
                    "poster": img
                })
        return rooms

    def _encode_room_id(self, title, play_url, poster, platform_id=""):
        payload = "%s|%s|%s|%s" % (title, play_url, poster, platform_id)
        return "room@@%s" % urllib.parse.quote(payload, safe="")

    def _decode_room_id(self, raw_id):
        s = str(raw_id or "")
        if s.startswith("room@@"):
            s = s[len("room@@"):]
        try:
            dec = urllib.parse.unquote(s)
            parts = dec.split("|")
            if len(parts) >= 2:
                return {
                    "title": parts[0],
                    "addr": parts[1],
                    "img": parts[2] if len(parts) >= 3 else "",
                    "platformId": parts[3] if len(parts) >= 4 else ""
                }
        except Exception:
            pass
        return {"title": "", "addr": s, "img": "", "platformId": ""}

    def homeContent(self, filter):
        categories = [{"type_id": "continuous_feed", "type_name": "📺 连刷模式"}]
        platforms = self._get_platforms()
        for pt in platforms:
            if len(categories) >= 100:
                break
            categories.append({
                "type_id": pt["id"],
                "type_name": pt["name"]
            })
        result = {"class": categories}
        if filter:
            result["filters"] = {}
        return result

    def homeVideoContent(self):
        platforms = self._get_platforms()
        if not platforms:
            return {"list": []}
        rooms = self._fetch_platform_rooms(platforms[0]["id"])
        items = []
        for r in rooms[:20]:
            items.append({
                "vod_id": self._encode_room_id(r["title"], r["playUrl"], r["poster"], platforms[0]["id"]),
                "vod_name": r["title"],
                "vod_pic": r["poster"],
                "vod_remarks": _format_remarks(self.brandName, "正在直播"),
                "style": {"type": "rect", "ratio": 1.78}
            })
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1

        clean_tid = str(tid or "continuous_feed").strip()
        if page > 1:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        if clean_tid == "continuous_feed":
            platforms = self._get_platforms()
            feed_items = []
            for idx, ch in enumerate(self.feedChannels):
                cover = ""
                if platforms:
                    target_pt = platforms[0] if idx == 0 else (platforms[1] if len(platforms) > 1 else platforms[0])
                    sample_rooms = self._fetch_platform_rooms(target_pt["id"])
                    if sample_rooms and sample_rooms[0].get("poster"):
                        cover = sample_rooms[0]["poster"]
                feed_items.append({
                    "vod_id": ch["id"],
                    "vod_name": ch["name"],
                    "vod_pic": cover if cover else ch["fallbackPoster"],
                    "vod_remarks": _format_remarks(self.brandName, "自动切台"),
                    "style": {"type": "rect", "ratio": 1.78}
                })
            return {
                "list": feed_items,
                "page": 1,
                "pagecount": 1,
                "limit": len(feed_items),
                "total": len(feed_items)
            }

        rooms = self._fetch_platform_rooms(clean_tid)
        if not rooms:
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

        items = []
        for rm in rooms:
            items.append({
                "vod_id": self._encode_room_id(rm["title"], rm["playUrl"], rm["poster"], clean_tid),
                "vod_name": rm["title"],
                "vod_pic": rm["poster"],
                "vod_remarks": _format_remarks(self.brandName, "直播中"),
                "style": {"type": "rect", "ratio": 1.78}
            })

        return {
            "list": items,
            "page": 1,
            "pagecount": 1,
            "limit": len(items),
            "total": len(items)
        }

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        keyword = self._clean_text(key).lower()
        if not keyword or page > 1:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        platforms = self._get_platforms()
        matched = []
        for pt in platforms[:8]:
            rooms = self._fetch_platform_rooms(pt["id"])
            for r in rooms:
                if keyword in r["title"].lower():
                    matched.append({
                        "vod_id": self._encode_room_id(r["title"], r["playUrl"], r["poster"], pt["id"]),
                        "vod_name": r["title"],
                        "vod_pic": r["poster"],
                        "vod_remarks": _format_remarks(self.brandName, pt["name"]),
                        "style": {"type": "rect", "ratio": 1.78}
                    })

        return {
            "list": matched,
            "page": 1,
            "pagecount": 1,
            "limit": len(matched),
            "total": len(matched)
        }

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, (list, tuple)) and ids else str(ids or "")
        item_id = str(raw_id).strip()
        if not item_id:
            return {"list": []}

        if item_id.startswith("feed_"):
            ch = self.feedChannels[0]
            for c in self.feedChannels:
                if c["id"] == item_id:
                    ch = c
                    break

            platforms = self._get_platforms()
            target_pts = platforms[:3] if item_id == "feed_hot" else platforms[2:6]
            if not target_pts:
                target_pts = platforms[:2]

            all_rooms = []
            for pt in target_pts:
                all_rooms.extend(self._fetch_platform_rooms(pt["id"]))

            episodes = []
            seen_urls = set()
            first_poster = ""
            idx = 1
            for room in all_rooms:
                p_url = room.get("playUrl", "")
                if not p_url or p_url in seen_urls:
                    continue
                seen_urls.add(p_url)
                if not first_poster and room.get("poster"):
                    first_poster = room["poster"]
                ep_name = ("%d. %s" % (idx, room["title"])).replace("$", "").replace("#", "")
                episodes.append("%s$%s" % (ep_name, p_url))
                idx += 1

            if not episodes:
                return {"list": []}

            cover_img = first_poster if first_poster else ch["fallbackPoster"]
            content = (
                "🦋 蝴蝶影视专线加速播放 | 官方TG交流群：@tvshare23 | "
                "当前节点：%s | 本频道已汇聚 %d 位高热度在线主播，开启自动连播或手势切集即可秒速无缝切台"
            ) % (self.siteUrl, len(episodes))

            vod = {
                "vod_id": item_id,
                "vod_name": ch["name"],
                "vod_pic": cover_img,
                "vod_bg": cover_img,
                "vod_background": cover_img,
                "vod_banner": cover_img,
                "type_name": "百年直播",
                "vod_actor": self.brandActor,
                "vod_director": self.brandDirector,
                "vod_remarks": _format_remarks(self.brandName, "共%d位在线" % len(episodes)),
                "vod_content": content,
                "vod_play_from": self.feedLineName,
                "vod_play_url": "#".join(episodes)
            }
            return {"list": [vod]}

        info = self._decode_room_id(item_id)
        title = info.get("title") or "在线直播"
        addr = info.get("addr") or ""
        img = info.get("img") or ""
        platform_id = info.get("platformId") or ""

        if not addr or not addr.startswith("http"):
            return {"list": []}

        episodes_out = []
        ep_first_name = title.replace("$", "").replace("#", "") or "直播房间 1"
        episodes_out.append("%s$%s" % (ep_first_name, addr))

        if platform_id:
            sibling_rooms = self._fetch_platform_rooms(platform_id)
            seen_addrs = {addr}
            for s_idx, s_rm in enumerate(sibling_rooms):
                s_url = s_rm.get("playUrl", "")
                if not s_url or s_url in seen_addrs:
                    continue
                seen_addrs.add(s_url)
                s_name = (s_rm.get("title") or ("直播房间 %d" % (s_idx + 2))).replace("$", "").replace("#", "")
                episodes_out.append("%s$%s" % (s_name, s_url))

        content = (
            "🦋 蝴蝶影视专线直连 | 主播名：%s | 官方交流群: @tvshare23\n"
            "当前节点：%s | 房间状态：正在公开直播中，同台主播已挂载至选集列表支持连播"
        ) % (title, self.siteUrl)

        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": img,
            "vod_bg": img,
            "vod_background": img,
            "vod_banner": img,
            "type_name": "百年直播",
            "vod_actor": self.brandActor,
            "vod_director": self.brandDirector,
            "vod_remarks": _format_remarks(self.brandName, "直播中"),
            "vod_content": content,
            "vod_play_from": self.lineName,
            "vod_play_url": "#".join(episodes_out)
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = str(id or "").strip()
        if play_url.startswith("room@@"):
            info = self._decode_room_id(play_url)
            play_url = info.get("addr", "")

        headers = {
            "User-Agent": self._ua,
            "Referer": "%s/" % self.siteUrl,
            "Origin": self.siteUrl
        }
        return {
            "parse": 0,
            "jx": 0,
            "playUrl": "",
            "url": play_url,
            "header": headers
        }

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]
# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249502182&sig=77357017555126dd
