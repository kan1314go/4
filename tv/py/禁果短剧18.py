# -*- coding: utf-8 -*-
# 禁果短剧 蜘蛛（源自 Hamo 插件 com.butterfly.jinguo 的接口逻辑移植）
import base64
import gzip
import json
import re
import secrets
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://jinguoduanju.app"
    UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    PAGE_SIZE = 24
    WASH_HOST_B64 = "Y2xlYW4uNTU2ODk5OS5jYy5jZA=="
    CLASSES = [
        ("latest", "最新上线"), ("heat", "热度排行"), ("landing", "精选推荐"), ("nav_2", "全部短剧"),
        ("nav_7", "原创精品"), ("nav_3", "单体作品"), ("nav_6", "动漫改编"), ("nav_5", "影视改编"),
    ]
    CLASS_FILTERS = [
        {"key": "sort", "name": "排序", "value": [
            {"n": "最新", "v": "latest"}, {"n": "最热", "v": "heat"},
        ]},
        {"key": "length", "name": "集数", "value": [
            {"n": "全部", "v": ""}, {"n": "多集", "v": "multi"}, {"n": "单集", "v": "single"},
        ]},
        {"key": "tag", "name": "题材标签", "value": [
            {"n": "全部", "v": ""}, {"n": "魔改", "v": "魔改"}, {"n": "都市", "v": "都市"},
            {"n": "职场", "v": "职场"}, {"n": "奇幻", "v": "奇幻"}, {"n": "古装", "v": "古装"}, {"n": "动漫", "v": "动漫"},
        ]},
    ]

    def getName(self):
        return "禁果短剧"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.token = ""
        self.token_ts = 0
        self.device = secrets.token_hex(16)
        self.landing_cache = None

    def _fetch(self, url, method="GET", body=None, token=""):
        headers = {
            "User-Agent": self.UA,
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip",
        }
        if token:
            headers["Authorization"] = "Bearer " + token
        data = None
        if method == "POST":
            data = json.dumps(body or {}).encode("utf-8")
            headers["Content-Type"] = "application/json;charset=UTF-8"
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers, data=data, method=method)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    status = resp.status
                    raw = resp.read()
                    enc = resp.headers.get("Content-Encoding") or ""
                if raw and (enc.lower() == "gzip" or raw[:2] == b"\x1f\x8b"):
                    try:
                        raw = gzip.decompress(raw)
                    except Exception:
                        pass
                text = raw.decode("utf-8", "replace") if raw else ""
                return status, text
            except urllib.error.HTTPError as e:
                try:
                    raw = e.read()
                    if raw and raw[:2] == b"\x1f\x8b":
                        try:
                            raw = gzip.decompress(raw)
                        except Exception:
                            pass
                    text = raw.decode("utf-8", "replace") if raw else ""
                except Exception:
                    text = ""
                return e.code, text
            except Exception:
                pass
            time.sleep(0.5)
        return 0, ""

    def _ensure_token(self):
        now = time.time()
        if self.token and now - self.token_ts < 3600:
            return self.token
        status, text = self._fetch(self.host + "/api/v1/auth/device", method="POST",
                                   body={"deviceId": "h5:" + self.device, "channelCode": "", "attributionToken": ""})
        tok = ""
        if text:
            try:
                d = json.loads(text)
                if isinstance(d, dict) and d.get("token"):
                    tok = str(d["token"]).strip()
            except Exception:
                pass
        if tok:
            self.token = tok
            self.token_ts = now
        return tok

    def _api_get(self, path, query=None, retry=False):
        tok = self._ensure_token()
        parts = []
        if query:
            for k, v in query.items():
                if v is not None and str(v) != "":
                    parts.append(urllib.parse.quote(str(k), safe="") + "=" + urllib.parse.quote(str(v), safe=""))
        url = self.host + "/api/v1" + path + (("?" + "&".join(parts)) if parts else "")
        status, text = self._fetch(url, token=tok)
        if status == 401 and not retry:
            self.token = ""
            self.token_ts = 0
            return self._api_get(path, query, retry=True)
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    def _fix_cover(self, u):
        raw = str(u or "").strip()
        if not raw:
            return ""
        if re.match(r"^https?://", raw, re.I):
            return raw
        if raw.startswith("//"):
            return "https:" + raw
        return self.host + "/" + raw.lstrip("/")

    def _card(self, it):
        if not isinstance(it, dict):
            return None
        vid = str(it.get("id") or "").strip()
        if not vid:
            return None
        title = str(it.get("title") or vid).strip()
        cover = self._fix_cover(it.get("coverUrl") or it.get("cover"))
        parts = []
        if it.get("episodeCount"):
            parts.append("全" + str(it.get("episodeCount")) + "集")
        tags = it.get("tags") if isinstance(it.get("tags"), list) else []
        if tags:
            parts.append(" · ".join(str(t) for t in tags[:2]))
        meta = " · ".join(parts) if parts else "连载中"
        return {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": cover,
            "vod_remarks": "蝴蝶影视 | " + meta,
            "style": {"type": "rect", "ratio": 0.56},
        }

    def _card_list(self, arr):
        out = []
        if isinstance(arr, list):
            for it in arr:
                card = self._card(it)
                if card:
                    out.append(card)
        return out

    def _landing_all(self):
        if self.landing_cache is not None:
            return self.landing_cache
        data = self._api_get("/landing")
        all_items = []
        if isinstance(data, dict):
            if isinstance(data.get("dramas"), list):
                all_items = data["dramas"]
        elif isinstance(data, list):
            all_items = data
        self.landing_cache = all_items
        return all_items

    def _landing_items(self, page):
        all_items = self._landing_all()
        start = (page - 1) * self.PAGE_SIZE
        return self._card_list(all_items[start:start + self.PAGE_SIZE])

    def homeContent(self, filter=False):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]
        result = {"class": classes}
        if filter:
            result["filters"] = dict((cid, self.CLASS_FILTERS) for cid, _ in self.CLASSES)
        return result

    def homeVideoContent(self):
        return {"list": self._landing_items(1)[:24]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        slug = str(tid or "latest").strip()
        if slug == "landing":
            items = self._landing_items(page)
            return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}
        ext = extend if isinstance(extend, dict) else {}
        q = {"sort": str(ext.get("sort") or ("heat" if slug == "heat" else "latest"))}
        if slug.startswith("nav_"):
            q["navigationId"] = slug.split("_")[1]
        if ext.get("length"):
            q["length"] = str(ext["length"])
        data = self._api_get("/dramas", q)
        all_items = data if isinstance(data, list) else []
        tag_filter = str(ext.get("tag") or "").strip()
        if tag_filter:
            filtered = []
            for it in all_items:
                tags = it.get("tags") if isinstance(it, dict) and isinstance(it.get("tags"), list) else []
                if tag_filter in [str(t) for t in tags]:
                    filtered.append(it)
            all_items = filtered
        start = (page - 1) * self.PAGE_SIZE
        items = self._card_list(all_items[start:start + self.PAGE_SIZE])
        pagecount = (len(all_items) + self.PAGE_SIZE - 1) // self.PAGE_SIZE if all_items else page
        return {"list": items, "page": page, "pagecount": pagecount, "limit": len(items), "total": len(all_items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        data = self._api_get("/dramas", {"sort": "latest", "q": str(key)})
        all_items = data if isinstance(data, list) else []
        start = (page - 1) * self.PAGE_SIZE
        items = self._card_list(all_items[start:start + self.PAGE_SIZE])
        pagecount = (len(all_items) + self.PAGE_SIZE - 1) // self.PAGE_SIZE if all_items else page
        return {"list": items, "page": page, "pagecount": pagecount, "limit": len(items), "total": len(all_items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0] or "").strip()
        data = self._api_get("/dramas/" + urllib.parse.quote(vid, safe=""))
        drama = data.get("drama") if isinstance(data, dict) and isinstance(data.get("drama"), dict) else {}
        eps = data.get("episodes") if isinstance(data, dict) and isinstance(data.get("episodes"), list) else []
        title = str(drama.get("title") or vid).strip()
        cover = self._fix_cover(drama.get("coverUrl") or drama.get("cover"))
        tags = [str(t) for t in drama.get("tags")] if isinstance(drama.get("tags"), list) else []
        desc = str(drama.get("description") or "").strip()
        episodes = []
        if eps:
            for i, ep in enumerate(eps):
                if not isinstance(ep, dict):
                    continue
                n = str(ep.get("number") or (i + 1)).strip()
                ep_id = str(ep.get("id") or "").strip()
                t_name = str(ep.get("title") or ("第" + n + "集")).strip().replace("$", "").replace("#", "")
                val = json.dumps({"dramaId": vid, "epNum": n, "epId": ep_id}, ensure_ascii=False)
                episodes.append(t_name + "$" + val)
        else:
            val = json.dumps({"dramaId": vid, "epNum": "1", "epId": ""}, ensure_ascii=False)
            episodes.append("第1集$" + val)
        lines = [
            "🦋 禁果短剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        elif tags:
            lines.append(" · ".join(tags))
        else:
            lines.append("标题：" + title)
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + vid)
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": cover,
            "vod_remarks": "蝴蝶影视 | 全" + str(len(episodes)) + "集",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.56},
        }
        if tags:
            vod["vod_class"] = ",".join(tags)
        return {"list": [vod]}

    def _clean_wrap(self, u, referer):
        ref = referer or ""
        if not ref:
            m = re.match(r"^(https?://[^/]+)", str(u or ""), re.I)
            ref = (m.group(1) + "/") if m else ""
        wash_host = base64.b64decode(self.WASH_HOST_B64).decode("utf-8", "replace")
        w = "https://" + wash_host + "/clean?u=" + urllib.parse.quote(str(u), safe="")
        if ref:
            w += "&r=" + urllib.parse.quote(ref, safe="")
        w += "&px=1"
        return w

    def playerContent(self, flag, id, vipFlags):
        drama_id = ""
        ep_num = "1"
        ep_id = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                drama_id = str(data.get("dramaId") or "").split(":")[0]
                ep_num = str(data.get("epNum") or "1")
                ep_id = str(data.get("epId") or "")
        except Exception:
            pass
        headers = {"User-Agent": self.UA, "Referer": self.host + "/", "Origin": self.host}
        if not drama_id:
            return {"parse": 1, "playUrl": "", "url": "", "header": headers}
        if not ep_id:
            data = self._api_get("/dramas/" + urllib.parse.quote(drama_id, safe=""))
            eps = data.get("episodes") if isinstance(data, dict) and isinstance(data.get("episodes"), list) else []
            for ep in eps:
                if isinstance(ep, dict) and (str(ep.get("number") or "") == ep_num or str(ep.get("id") or "") == ep_num):
                    ep_id = str(ep.get("id") or "")
                    break
            if not ep_id and eps and isinstance(eps[0], dict):
                ep_id = str(eps[0].get("id") or "")
        video_url = ""
        if ep_id:
            play = self._api_get("/episodes/" + urllib.parse.quote(ep_id, safe="") + "/play")
            if isinstance(play, dict):
                video_url = str(play.get("videoUrl") or "").strip()
        if not video_url:
            return {"parse": 1, "playUrl": "", "url": "", "header": headers}
        if re.search(r"\.mp4($|\?)", video_url, re.I):
            return {"parse": 0, "playUrl": "", "url": video_url, "header": headers}
        return {"parse": 0, "playUrl": "", "url": self._clean_wrap(video_url, self.host + "/"), "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249772435&sig=a90e434c93d64c5a
