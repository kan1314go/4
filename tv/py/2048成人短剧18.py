# -*- coding: utf-8 -*-
# 2048成人短剧 蜘蛛（源自 Hamo 插件 com.butterfly.madou.drama 的接口逻辑移植）
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://mdcmai4.xyz"
    DRAMA_TID = "short_drama_ai"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    DRAMA_FILTERS = [
        {"key": "sort", "name": "排序", "value": [
            {"n": "热门短剧", "v": "heat"},
            {"n": "最新短剧", "v": "latest"},
        ]},
    ]
    VIDEO_FILTERS = [
        {"key": "sort", "name": "排序", "value": [
            {"n": "热门推荐", "v": "heat"},
            {"n": "最新发布", "v": "latest"},
            {"n": "最多播放", "v": "views"},
            {"n": "最高评分", "v": "rating"},
        ]},
    ]

    def getName(self):
        return "2048成人短剧"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.classes_cache = None
        self.home_cache = []
        self.meta_cache = {}

    def _headers(self):
        return {
            "User-Agent": self.UA,
            "Referer": self.host + "/",
            "Origin": self.host,
            "Accept": "application/json, text/plain, */*",
        }

    def _fetch(self, url):
        last = None
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=self._headers())
                with urllib.request.urlopen(req, timeout=20) as resp:
                    body = resp.read()
                if body:
                    try:
                        text = body.decode("utf-8")
                    except Exception:
                        text = body.decode("utf-8", "replace")
                    if text.strip():
                        return text
                last = "empty"
            except Exception as e:
                last = e
            time.sleep(0.6)
        return ""

    def _get_json(self, url):
        text = self._fetch(url)
        if not text:
            return {}
        try:
            data = json.loads(text)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _remarks(self, meta):
        clean = re.sub(r"[\r\n\t]+", " ", str(meta or "")).strip()
        if clean:
            return "蝴蝶影视 | " + clean
        return "蝴蝶影视"

    def _cover(self, cover):
        pic = str(cover or "").strip()
        if not pic:
            return ""
        if pic.startswith("http"):
            return pic.split("@")[0]
        if pic.startswith("/uploads/") or pic.startswith("/api/"):
            return self.host + pic
        return self.host + "/api/v1/image/proxy?path=" + urllib.parse.quote(pic, safe="")

    def _play_url(self, video):
        v = str(video or "").strip()
        if not v:
            return ""
        if v.startswith("http"):
            return v
        if v.startswith("/api/v1/m3u8/proxy"):
            return self.host + v
        return self.host + "/api/v1/m3u8/proxy?path=" + urllib.parse.quote(v, safe="")

    def _duration(self, seconds):
        try:
            sec = int(float(seconds))
        except Exception:
            return ""
        if not sec:
            return ""
        m = sec // 60
        s = sec % 60
        h = m // 60
        rem_m = m % 60
        if h > 0:
            return "%02d:%02d:%02d" % (h, rem_m, s)
        return "%02d:%02d" % (rem_m, s)

    def _classes(self):
        if self.classes_cache is not None:
            return self.classes_cache
        classes = [{"type_id": self.DRAMA_TID, "type_name": "🔥 AI短剧"}]
        filters = {self.DRAMA_TID: self.DRAMA_FILTERS}
        res = self._get_json(self.host + "/api/v1/categories")
        data = res.get("data") if res.get("code") == 200 else None
        if isinstance(data, list):
            for cat in data:
                if not isinstance(cat, dict):
                    continue
                name = str(cat.get("name") or "").strip()
                if "交友闲谈" in name:
                    continue
                if cat.get("enabled") is False:
                    continue
                cid = str(cat.get("id") or "")
                if not cid:
                    continue
                classes.append({"type_id": cid, "type_name": name or "未知分类"})
                filters[cid] = self.VIDEO_FILTERS
        self.classes_cache = (classes, filters)
        return self.classes_cache

    def _drama_card(self, it):
        if not isinstance(it, dict):
            return None
        did = str(it.get("id") or "")
        if not did:
            return None
        try:
            eps = int(it.get("episodeCount") or 1)
        except Exception:
            eps = 1
        return {
            "vod_id": "drama@@" + did,
            "vod_name": str(it.get("title") or "").strip(),
            "vod_pic": self._cover(it.get("coverUrl")),
            "vod_remarks": self._remarks("全" + str(eps) + "集"),
            "style": {"type": "rect", "ratio": 0.67},
        }

    def _video_card(self, it):
        if not isinstance(it, dict):
            return None
        vid = str(it.get("id") or "")
        if not vid:
            return None
        meta = self._duration(it.get("durationSec")) or str(it.get("categoryName") or "")
        self.meta_cache[vid] = {
            "videoUrl": it.get("videoUrl") or "",
            "title": it.get("title") or "",
            "cover": it.get("coverUrl") or "",
            "desc": it.get("description") or "",
            "catName": it.get("categoryName") or "",
        }
        return {
            "vod_id": "video@@" + vid,
            "vod_name": str(it.get("title") or "").strip(),
            "vod_pic": self._cover(it.get("coverUrl")),
            "vod_remarks": self._remarks(meta),
            "style": {"type": "rect", "ratio": 1.51},
        }

    def homeContent(self, filter=False):
        classes, filters = self._classes()
        result = {"class": classes}
        if filter:
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        if self.home_cache:
            return {"list": self.home_cache}
        res = self._get_json(self.host + "/api/v1/short-dramas?productId=1&sortBy=heat&page=1&size=12")
        items = []
        data = res.get("data") if res.get("code") == 200 else None
        if isinstance(data, dict):
            for it in data.get("items") or []:
                card = self._drama_card(it)
                if card:
                    items.append(card)
        self.home_cache = items
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        sort_val = ""
        if isinstance(extend, dict):
            sort_val = str(extend.get("sort") or "").strip()
        items = []
        pagecount = page
        if str(tid) == self.DRAMA_TID:
            sort = "latest" if sort_val == "latest" else "heat"
            url = self.host + "/api/v1/short-dramas?productId=1&sortBy=" + sort + "&page=" + str(page) + "&size=12"
            res = self._get_json(url)
            data = res.get("data") if res.get("code") == 200 else None
            if isinstance(data, dict):
                for it in data.get("items") or []:
                    card = self._drama_card(it)
                    if card:
                        items.append(card)
                if data.get("totalPages"):
                    pagecount = int(data["totalPages"])
        else:
            sort = sort_val if sort_val in ("heat", "latest", "views", "rating") else "heat"
            url = (self.host + "/api/v1/videos?page=" + str(page) + "&size=24&categoryId="
                   + urllib.parse.quote(str(tid), safe="") + "&sortBy=" + sort)
            res = self._get_json(url)
            data = res.get("data") if res.get("code") == 200 else None
            if isinstance(data, dict):
                for it in data.get("items") or []:
                    card = self._video_card(it)
                    if card:
                        items.append(card)
                if data.get("totalPages"):
                    pagecount = int(data["totalPages"])
        return {"list": items, "page": page, "pagecount": pagecount, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        url = (self.host + "/api/v1/videos/search?page=" + str(page) + "&size=24&q="
               + urllib.parse.quote(str(key), safe=""))
        res = self._get_json(url)
        items = []
        pagecount = page
        data = res.get("data") if res.get("code") == 200 else None
        if isinstance(data, dict):
            for it in data.get("items") or []:
                card = self._video_card(it)
                if card:
                    items.append(card)
            if data.get("totalPages"):
                pagecount = int(data["totalPages"])
        return {"list": items, "page": page, "pagecount": pagecount, "limit": len(items), "total": len(items)}

    def _content(self, site_name, title, cat_name, source_name, raw_id, desc):
        lines = [
            "🦋 " + site_name + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        intro = str(desc or "").strip()
        if intro and intro != str(title or "").strip():
            lines.append(intro)
        else:
            lines.append("标题：" + str(title or ""))
            if cat_name:
                lines.append("分类：" + str(cat_name))
            lines.append("片源：" + source_name)
            lines.append("编号：" + str(raw_id))
        return "\n".join(lines)

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        item_id = str(ids[0] or "")
        vtype = ""
        raw_id = ""
        if "@@" in item_id:
            parts = item_id.split("@@", 1)
            vtype = parts[0]
            raw_id = parts[1]
        title = "在线播放"
        cover = ""
        desc = ""
        cat_name = ""
        episodes = []
        if vtype == "drama":
            source_name = "🦋 AI短剧专线"
            res = self._get_json(self.host + "/api/v1/short-dramas/" + urllib.parse.quote(raw_id, safe="") + "?productId=1")
            data = res.get("data") if res.get("code") == 200 else None
            remarks = self._remarks("")
            if isinstance(data, dict):
                title = data.get("title") or title
                cover = data.get("coverUrl") or cover
                desc = data.get("description") or ""
                cat_name = "AI短剧"
                if data.get("episodeCount"):
                    remarks = self._remarks("全" + str(data.get("episodeCount")) + "集")
                for i, ep in enumerate(data.get("episodes") or []):
                    if not isinstance(ep, dict) or not ep.get("videoUrl"):
                        continue
                    ep_no = ep.get("episodeNo") or (i + 1)
                    play = self._play_url(ep.get("videoUrl"))
                    episodes.append("第" + str(ep_no) + "集$" + json.dumps({"u": play}, ensure_ascii=False))
            vod = {
                "vod_id": item_id,
                "vod_name": str(title).strip(),
                "vod_pic": self._cover(cover),
                "vod_year": "2026",
                "vod_remarks": remarks,
                "vod_actor": "🦋 TG群: @tvshare23",
                "vod_director": "🦋 蝴蝶影视",
                "vod_content": self._content("2048成人短剧", title, cat_name, source_name, raw_id, desc),
                "vod_play_from": source_name,
                "vod_play_url": "#".join(episodes),
                "style": {"type": "rect", "ratio": 0.67},
            }
            return {"list": [vod]}
        source_name = "🦋 蝴蝶专线"
        meta = self.meta_cache.get(raw_id) or {}
        title = meta.get("title") or title
        cover = meta.get("cover") or ""
        desc = meta.get("desc") or ""
        cat_name = meta.get("catName") or ""
        play = self._play_url(meta.get("videoUrl"))
        if play:
            episodes.append("超清正片$" + json.dumps({"u": play}, ensure_ascii=False))
        else:
            episodes.append("暂无播放地址$" + json.dumps({"u": ""}, ensure_ascii=False))
        vod = {
            "vod_id": item_id,
            "vod_name": str(title).strip(),
            "vod_pic": self._cover(cover),
            "vod_year": "2026",
            "vod_remarks": self._remarks("高清正片"),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": self._content("2048成人短剧", title, cat_name, source_name, raw_id, desc),
            "vod_play_from": source_name,
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 1.51},
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        url = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                url = str(data.get("u") or "")
        except Exception:
            url = str(id or "")
        return {
            "parse": 0,
            "playUrl": "",
            "url": url,
            "header": {
                "User-Agent": self.UA,
                "Referer": self.host + "/",
                "Origin": self.host,
            },
        }

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249460865&sig=412bcac2a95dc53c
