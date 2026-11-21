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

        self.siteName = "色播聚合"
        self.siteUrl = "http://api.hclyz.com:81/mf"
        self.tgGroup = "https://t.me/tvshare23"
        self.brandName = "蝴蝶影视"
        self.brandActor = "🦋 TG群: @tvshare23"
        self.brandDirector = "🦋 蝴蝶影视"
        self.lineName = "🦋 蝴蝶超清专线"
        self.feedLineName = "🦋 连续刷流专线"
        self.cacheKeyPlatforms = "lytvs_sebo_platforms_py_v1"
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

    def _abs_url(self, u):
        if not u:
            return ""
        s = str(u).strip().replace("\\/", "/")
        if s.startswith("http"):
            return s
        if s.startswith("//"):
            return "http:" + s
        if s.startswith("/"):
            return "%s%s" % (self.siteUrl, s)
        return "%s/%s" % (self.siteUrl, s)

    def _fetch_json(self, path):
        raw_p = str(path or "")
        if raw_p.startswith("http"):
            url = raw_p
        else:
            clean_p = raw_p if raw_p.startswith("/") else ("/%s" % raw_p)
            url = "%s%s" % (self.siteUrl, clean_p)

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

    def _platform_list(self):
        try:
            cached = self.getCache(self.cacheKeyPlatforms)
            if isinstance(cached, str) and cached:
                parsed = json.loads(cached)
                if isinstance(parsed, list) and parsed:
                    return parsed
        except Exception:
            pass

        data = self._fetch_json("/json.txt")
        raw_list = data.get("pingtai", []) if isinstance(data, dict) else []
        plats = []
        seen = set()

        if isinstance(raw_list, list):
            for item in raw_list:
                if not isinstance(item, dict):
                    continue
                raw_addr = str(item.get("address") or "").strip().lstrip("/")
                title = self._clean_text(item.get("title"))
                if not raw_addr or not title:
                    continue
                addr = "/%s" % raw_addr
                if addr in seen:
                    continue
                seen.add(addr)
                num_str = str(item.get("Number") or "0")
                try:
                    num_val = int(re.sub(r"\D+", "", num_str) or "0")
                except Exception:
                    num_val = 0
                plats.append({
                    "addr": addr,
                    "title": title,
                    "img": self._abs_url(item.get("xinimg") or item.get("img") or ""),
                    "num": num_val
                })

        plats.sort(key=lambda x: x.get("num", 0), reverse=True)

        if plats:
            try:
                self.setCache(self.cacheKeyPlatforms, json.dumps(plats, ensure_ascii=False))
            except Exception:
                pass
        return plats

    def _fetch_anchor_rooms(self, path):
        data = self._fetch_json(path)
        zhubo = data.get("zhubo", []) if isinstance(data, dict) else []
        rooms = []
        if isinstance(zhubo, list):
            for idx, v in enumerate(zhubo):
                if not isinstance(v, dict):
                    continue
                play_url = str(v.get("address") or "").strip()
                if not play_url or "rtmp" in play_url.lower():
                    continue
                title = self._clean_text(v.get("title")) or ("主播 %d" % (idx + 1))
                poster = self._abs_url(v.get("img") or "")
                rooms.append({
                    "title": title,
                    "playUrl": play_url,
                    "poster": poster
                })
        return rooms

    def _build_feed_items(self):
        plats = self._platform_list()
        feed_items = []
        for idx, ch in enumerate(self.feedChannels):
            cover = ""
            if plats:
                target_pt = plats[0] if idx == 0 else (plats[1] if len(plats) > 1 else plats[0])
                sample_rooms = self._fetch_anchor_rooms(target_pt["addr"])
                if sample_rooms and sample_rooms[0].get("poster"):
                    cover = sample_rooms[0]["poster"]
            feed_items.append({
                "vod_id": ch["id"],
                "vod_name": ch["name"],
                "vod_pic": cover if cover else ch["fallbackPoster"],
                "vod_remarks": _format_remarks(self.brandName, "自动切台"),
                "style": {"type": "rect", "ratio": 1.78}
            })
        return feed_items

    def homeContent(self, filter):
        categories = [{"type_id": "continuous_feed", "type_name": "📺 连刷模式"}]
        plats = self._platform_list()
        for pt in plats:
            if len(categories) >= 100:
                break
            categories.append({
                "type_id": pt["addr"],
                "type_name": pt["title"]
            })
        result = {"class": categories}
        if filter:
            result["filters"] = {}
        return result

    def homeVideoContent(self):
        items = self._build_feed_items()
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1

        cid = str(tid or "continuous_feed").strip()
        if page > 1:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        if cid == "continuous_feed":
            feed_cards = self._build_feed_items()
            return {
                "list": feed_cards,
                "page": 1,
                "pagecount": 1,
                "limit": len(feed_cards),
                "total": len(feed_cards)
            }

        rooms = self._fetch_anchor_rooms(cid)
        if not rooms:
            return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

        items = []
        for idx, rm in enumerate(rooms):
            raw_id = "%s#%d" % (cid, idx)
            items.append({
                "vod_id": raw_id,
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

        plats = self._platform_list()
        matched = []
        for pt in plats[:8]:
            rooms = self._fetch_anchor_rooms(pt["addr"])
            for idx, r in enumerate(rooms):
                if keyword in r["title"].lower():
                    matched.append({
                        "vod_id": "%s#%d" % (pt["addr"], idx),
                        "vod_name": r["title"],
                        "vod_pic": r["poster"],
                        "vod_remarks": _format_remarks(self.brandName, pt["title"]),
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

            plats = self._platform_list()
            target_pts = plats[:4] if item_id == "feed_hot" else plats[4:9]
            if not target_pts:
                target_pts = plats[:3]

            all_rooms = []
            for pt in target_pts:
                all_rooms.extend(self._fetch_anchor_rooms(pt["addr"]))

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
                "type_name": "色播聚合",
                "vod_actor": self.brandActor,
                "vod_director": self.brandDirector,
                "vod_remarks": _format_remarks(self.brandName, "共%d位在线" % len(episodes)),
                "vod_content": content,
                "vod_play_from": self.feedLineName,
                "vod_play_url": "#".join(episodes)
            }
            return {"list": [vod]}

        if "#" in item_id:
            apath, idx_str = item_id.split("#", 1)
            try:
                aidx = int(idx_str)
            except Exception:
                aidx = 0
        else:
            apath = item_id
            aidx = 0

        if not apath.startswith("/"):
            apath = "/%s" % apath

        rooms = self._fetch_anchor_rooms(apath)
        if not rooms:
            return {"list": []}

        start = aidx if (0 <= aidx < len(rooms)) else 0
        cur_room = rooms[start]
        title = cur_room.get("title") or "色播聚合"
        poster = cur_room.get("poster") or ""

        episodes_out = []
        for j in range(start, len(rooms)):
            rm = rooms[j]
            ep_name = (rm.get("title") or ("直播 %d" % (j + 1))).replace("$", "").replace("#", "")
            episodes_out.append("%s$%s" % (ep_name, rm["playUrl"]))

        if not episodes_out:
            return {"list": []}

        content = (
            "🦋 蝴蝶影视专线直连 | 主播名：%s | 官方交流群: @tvshare23\n"
            "当前节点：%s | 房间路径：%s | 直播状态：正在公开直播中，同台主播已挂载至选集列表支持连播"
        ) % (title, self.siteUrl, apath)

        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "type_name": "色播聚合",
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
        if not play_url.startswith("http") and "#" in play_url:
            apath, idx_str = play_url.split("#", 1)
            try:
                aidx = int(idx_str)
            except Exception:
                aidx = 0
            rooms = self._fetch_anchor_rooms(apath)
            if 0 <= aidx < len(rooms):
                play_url = rooms[aidx].get("playUrl", "")

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
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249876248&sig=f6608de62f813d62
