# -*- coding: utf-8 -*-
# 七猫短剧（成人版）蜘蛛（源自 Hamo 插件 com.butterfly.qimaoduanju 的接口逻辑移植）
import json
import re
import time
import uuid
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://7maoduanju.com"
    API_PATH = "/api/toc/v1"
    UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    PAGE_SIZE = 12
    LINES = [
        ("10000000-0000-4000-8000-0000000000c0", "热门短剧"),
        ("10000000-0000-4000-8000-000000000002", "原创短剧"),
        ("10000000-0000-4000-8000-0000000000b0", "真人短剧"),
        ("10000000-0000-4000-8000-000000000005", "擦边短剧"),
        ("10000000-0000-4000-8000-0000000000b3", "AI短剧"),
        ("10000000-0000-4000-8000-000000000003", "AI漫剧"),
        ("10000000-0000-4000-8000-0000000000b1", "AI魔改"),
        ("10000000-0000-4000-8000-0000000000b2", "AI换脸"),
        ("10000000-0000-4000-8000-0000000000b4", "影视综艺"),
    ]
    LINE_FILTERS = [
        {"key": "sort", "name": "排序", "value": [
            {"n": "默认", "v": "default"},
            {"n": "最新", "v": "latest"},
            {"n": "最热", "v": "hot"},
        ]},
        {"key": "status", "name": "状态", "value": [
            {"n": "全部", "v": "all"},
            {"n": "连载中", "v": "ongoing"},
            {"n": "已完结", "v": "completed"},
        ]},
    ]

    def getName(self):
        return "七猫短剧"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.home_cache = None
        self.token = ""
        self.token_ts = 0

    def _headers(self, token=""):
        h = {
            "User-Agent": self.UA,
            "Accept": "application/json, text/plain, */*",
            "Referer": self.host + "/",
            "Origin": self.host,
        }
        if token:
            h["Authorization"] = "Bearer " + token
        return h

    def _fetch(self, url, method="GET", body=None, token=""):
        urls = [url]
        if url.startswith("https://"):
            urls.append("http://" + url[8:])
        for u in urls:
            for _ in range(2):
                try:
                    data = None
                    headers = self._headers(token)
                    if body is not None:
                        data = json.dumps(body).encode("utf-8")
                        headers["Content-Type"] = "application/json"
                    req = urllib.request.Request(u, headers=headers, data=data, method=method)
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        raw = resp.read()
                    if raw:
                        text = raw.decode("utf-8", "replace")
                        if text.strip():
                            return text
                except Exception:
                    pass
                time.sleep(0.5)
        return ""

    def _api(self, path, params=None, method="GET", body=None, token=""):
        url = self.host + self.API_PATH + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        text = self._fetch(url, method=method, body=body, token=token)
        if not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    def _device_token(self):
        now = time.time()
        if self.token and now - self.token_ts < 1800:
            return self.token
        res = self._api("/auth/device", method="POST", body={"deviceId": str(uuid.uuid4())})
        tok = ""
        if isinstance(res, dict) and res.get("token"):
            tok = str(res["token"]).strip()
        if tok:
            self.token = tok
            self.token_ts = now
        return tok

    def _clean_pic(self, url):
        if not url:
            return ""
        u = str(url).strip()
        if u.startswith("//"):
            return "https:" + u
        return u.split("@Referer")[0].split("@User-Agent")[0].strip()

    def _remarks(self, info):
        i = str(info or "").strip()
        if not i:
            return "蝴蝶影视"
        return "蝴蝶影视 | " + i

    def _num(self, v):
        try:
            return int(float(v))
        except Exception:
            return 0

    def _card(self, item):
        if not isinstance(item, dict):
            return None
        did = str(item.get("id") or "")
        title = str(item.get("title") or "").strip()
        if not did or not title:
            return None
        eps = self._num(item.get("episodeCount"))
        free = self._num(item.get("freeEpisodeCount"))
        pay = str(item.get("payMode") or "")
        vip = bool(item.get("isVipBadge"))
        notes = []
        if eps > 0:
            notes.append(str(eps) + "集")
        if vip or pay == "vip_only":
            if 0 < free < 9000:
                notes.append("免" + str(free) + "·VIP")
            else:
                notes.append("VIP")
        elif 0 < free < 9000 and eps > 0:
            notes.append("免" + str(free) + "集")
        return {
            "vod_id": did,
            "vod_name": title,
            "vod_pic": self._clean_pic(item.get("coverUrl")),
            "vod_remarks": self._remarks(" · ".join(notes)),
            "style": {"type": "rect", "ratio": 0.75},
        }

    def _card_list(self, items):
        out = []
        if isinstance(items, list):
            for it in items:
                card = self._card(it)
                if card:
                    out.append(card)
        return out

    def _build_seo(self, prefix, index):
        if not prefix or not index or index <= 0:
            return ""
        ep = ("0" + str(index)) if index < 10 else str(index)
        return prefix + "/hls/ep" + ep + "/ep" + ep + ".m3u8"

    def _fetch_detail(self, did):
        res = self._api("/dramas/" + urllib.parse.quote(str(did), safe=""))
        if not isinstance(res, dict):
            return None, "", []
        raw_eps = res.get("episodes") if isinstance(res.get("episodes"), list) else []
        episodes = []
        for e in raw_eps:
            if not isinstance(e, dict):
                continue
            episodes.append({
                "id": str(e.get("id") or ""),
                "index": self._num(e.get("indexNo")),
                "title": str(e.get("title") or ""),
                "locked": bool(e.get("locked")),
                "seo": str(e.get("seoContentUrl") or ""),
            })
        episodes.sort(key=lambda x: x["index"])
        prefix = ""
        for ep in episodes:
            m = re.match(r"(https?://[^/\s]+/7cat/[^/\s]+)/hls/", ep["seo"], re.I)
            if m:
                prefix = m.group(1)
                break
        return res, prefix, episodes

    def homeContent(self, filter=False):
        classes = [{"type_id": lid, "type_name": name} for lid, name in self.LINES]
        result = {"class": classes}
        if filter:
            result["filters"] = dict((lid, self.LINE_FILTERS) for lid, _ in self.LINES)
        return result

    def homeVideoContent(self):
        if self.home_cache is not None:
            return {"list": self.home_cache}
        items = []
        seen = set()
        res = self._api("/home")
        if isinstance(res, dict) and isinstance(res.get("blocks"), list):
            for blk in res["blocks"]:
                if isinstance(blk, dict):
                    for card in self._card_list(blk.get("items")):
                        if card["vod_id"] not in seen:
                            seen.add(card["vod_id"])
                            items.append(card)
        if not items:
            res2 = self._api("/browse", {"line": self.LINES[0][0], "offset": 0})
            if isinstance(res2, dict):
                items = self._card_list(res2.get("items"))
        self.home_cache = items
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        params = {"line": str(tid), "offset": (page - 1) * self.PAGE_SIZE}
        if isinstance(extend, dict):
            so = str(extend.get("sort") or "").strip()
            st = str(extend.get("status") or "").strip()
            if so and so != "sort" and so != "default":
                params["sort"] = so
            if st and st != "all":
                params["status"] = st
        res = self._api("/browse", params)
        items = []
        pagecount = page
        if isinstance(res, dict):
            items = self._card_list(res.get("items"))
            total = self._num(res.get("total"))
            if total > 0:
                pagecount = (total + self.PAGE_SIZE - 1) // self.PAGE_SIZE
            elif res.get("hasMore"):
                pagecount = page + 1
        return {"list": items, "page": page, "pagecount": pagecount, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        res = self._api("/search", {"q": str(key)})
        items = []
        if isinstance(res, list):
            items = self._card_list(res)
        elif isinstance(res, dict):
            items = self._card_list(res.get("items"))
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        did = str(ids[0] or "")
        if "|" in did:
            did = did.split("|")[0].strip()
        drama, prefix, raw_eps = self._fetch_detail(did)
        title = did
        cover = ""
        desc = ""
        tags = []
        if isinstance(drama, dict):
            title = str(drama.get("title") or did).strip()
            cover = drama.get("coverUrl") or ""
            desc = str(drama.get("description") or "").strip()
            if isinstance(drama.get("tags"), list):
                tags = [str(t) for t in drama["tags"]]
        episodes = []
        for ep in raw_eps:
            idx = ep["index"]
            name = ep["title"] or ("第" + str(idx) + "集")
            candidate = ep["seo"] or self._build_seo(prefix, idx)
            val = json.dumps({"did": did, "epId": ep["id"], "idx": idx, "seo": candidate}, ensure_ascii=False)
            episodes.append(name + "$" + val)
        notes = []
        eps_n = self._num(drama.get("episodeCount")) if isinstance(drama, dict) else len(raw_eps)
        free_n = self._num(drama.get("freeEpisodeCount")) if isinstance(drama, dict) else 0
        if eps_n > 0:
            notes.append(str(eps_n) + "集")
        if 0 < free_n < 9000:
            notes.append("免" + str(free_n) + "集")
        if tags:
            notes.append("/".join(tags[:3]))
        lines = [
            "🦋 七猫短剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        else:
            lines.append("标题：" + title)
            if tags:
                lines.append("分类：" + "/".join(tags[:3]))
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + did)
        play_url = "#".join(episodes)
        vod = {
            "vod_id": did,
            "vod_name": title,
            "vod_pic": self._clean_pic(cover),
            "vod_remarks": self._remarks(" · ".join(notes)),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶专线$$$⚡ 全集秒播",
            "vod_play_url": play_url + "$$$" + play_url,
            "style": {"type": "rect", "ratio": 0.75},
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        did = ""
        ep_id = ""
        idx = 0
        seo = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                did = str(data.get("did") or "")
                ep_id = str(data.get("epId") or "")
                idx = self._num(data.get("idx"))
                seo = str(data.get("seo") or "")
        except Exception:
            pass
        target = ""
        if seo.startswith("http"):
            target = seo
        if not target and did:
            drama, prefix, eps = self._fetch_detail(did)
            for ep in eps:
                if (ep_id and ep["id"] == ep_id) or (idx > 0 and ep["index"] == idx):
                    target = ep["seo"] or self._build_seo(prefix, ep["index"])
                    break
            if not target and prefix and idx > 0:
                target = self._build_seo(prefix, idx)
        if not target and did and ep_id:
            tok = self._device_token()
            if tok:
                res = self._api("/dramas/" + urllib.parse.quote(did, safe="") + "/episodes/" + urllib.parse.quote(ep_id, safe="") + "/play", token=tok)
                if isinstance(res, dict) and res.get("playUrl"):
                    target = str(res["playUrl"]).strip()
        headers = {"User-Agent": self.UA, "Referer": self.host + "/"}
        if target.startswith("http"):
            low = target.lower()
            if ".m3u8" not in low and ".mp4" not in low and ".flv" not in low and ".ts" not in low:
                sep = "&" if "?" in target else "?"
                target = target + sep + "format=.m3u8"
            return {"parse": 0, "playUrl": "", "url": target, "header": headers}
        return {"parse": 1, "playUrl": "", "url": self.host + "/drama/" + did, "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249844462&sig=d5a902a061dc685d
