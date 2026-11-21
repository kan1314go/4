# -*- coding: utf-8 -*-
# 红果黄剧 蜘蛛（源自 Hamo 插件 com.butterfly.huangju 的接口逻辑移植）
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    SITE = "https://huangju.net"
    API = "https://api.huangju.net"
    PLAY_PROXY = "https://play.uou.qzz.io"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    PAGE_SIZE = 24
    MINOR_KEYS = ["萝莉", "幼女", "小学生", "中学生", "高三", "校园", "学生", "loli", "underage", "未成年", "女童", "师生"]

    def getName(self):
        return "红果黄剧"

    def init(self, extend=""):
        self.site = self.SITE
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.site = extend.strip().rstrip("/")
        self.cat_cache = None
        self.meta_cache = {}

    def _skip_minor(self, name):
        n = str(name or "").lower()
        for k in self.MINOR_KEYS:
            if k in n:
                return True
        return False

    def _fetch(self, url, site_ref=True):
        headers = {"User-Agent": self.UA, "Accept": "application/json", "Accept-Language": "zh-CN,zh;q=0.9"}
        if site_ref:
            headers["Referer"] = self.site + "/"
            headers["Origin"] = self.site
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    status = resp.status
                    resp_headers = resp.headers
                    raw = resp.read()
                text = raw.decode("utf-8", "replace") if raw else ""
                return status, text, resp_headers
            except urllib.error.HTTPError as e:
                try:
                    raw = e.read()
                    text = raw.decode("utf-8", "replace") if raw else ""
                except Exception:
                    text = ""
                return e.code, text, e.headers
            except Exception:
                pass
            time.sleep(0.5)
        return 0, "", None

    def _get_json(self, url):
        status, text, _ = self._fetch(url)
        if status != 200 or not text:
            return None
        try:
            return json.loads(text)
        except Exception:
            return None

    def _load_categories(self):
        if self.cat_cache is not None:
            return self.cat_cache
        cats = [("all", "全部")]
        data = self._get_json(self.API + "/categories")
        if isinstance(data, list):
            for c in data:
                if len(cats) >= 100:
                    break
                if not isinstance(c, dict):
                    continue
                name = str(c.get("name") or "")
                slug = str(c.get("slug") or "")
                if not slug or not name:
                    continue
                if self._skip_minor(name) or self._skip_minor(slug):
                    continue
                if len(slug) > 40 or len(name) > 20:
                    continue
                dc = c.get("dramaCount")
                if not (isinstance(dc, (int, float)) and dc > 0):
                    continue
                cats.append((slug, name))
        self.cat_cache = cats
        return cats

    def _card(self, it):
        if not isinstance(it, dict) or it.get("id") is None:
            return None
        title = str(it.get("title") or "")
        if self._skip_minor(title):
            return None
        slug = str(it.get("slug") or "")
        vid = (slug + "-" + str(it.get("id"))) if slug else str(it.get("id"))
        total = it.get("totalEpisodes")
        remarks = "蝴蝶影视 | 更新至" + str(total) + "集" if total else "蝴蝶影视"
        return {
            "vod_id": vid,
            "vod_name": title or vid,
            "vod_pic": str(it.get("coverUrl") or ""),
            "vod_remarks": remarks,
            "style": {"type": "rect", "ratio": 0.67},
        }

    def _list_page(self, query, page):
        parts = ["page=" + str(page), "pageSize=" + str(self.PAGE_SIZE)]
        for k, v in query.items():
            parts.append(urllib.parse.quote(str(k), safe="") + "=" + urllib.parse.quote(str(v), safe=""))
        data = self._get_json(self.API + "/dramas?" + "&".join(parts))
        arr = data.get("items") if isinstance(data, dict) and isinstance(data.get("items"), list) else []
        out = []
        seen = set()
        for it in arr:
            card = self._card(it)
            if card and card["vod_id"] not in seen:
                seen.add(card["vod_id"])
                out.append(card)
        return out

    def homeContent(self, filter=False):
        cats = self._load_categories()
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in cats]}

    def homeVideoContent(self):
        return {"list": self._list_page({}, 1)}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        q = {}
        if tid and str(tid) != "all":
            q["category"] = str(tid)
        items = self._list_page(q, page)
        return {"list": items, "page": page, "pagecount": page + 1 if len(items) >= self.PAGE_SIZE else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        items = self._list_page({"q": str(key)}, page)
        return {"list": items, "page": page, "pagecount": page + 1 if len(items) >= self.PAGE_SIZE else page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0] or "").strip()
        data = self._get_json(self.API + "/dramas/" + urllib.parse.quote(vid, safe=""))
        if not isinstance(data, dict) or not data.get("id"):
            return {"list": []}
        title = str(data.get("title") or vid)
        desc = str(data.get("description") or data.get("seoDescription") or "")
        if self._skip_minor(title) or self._skip_minor(desc):
            return {"list": []}
        raw_eps = data.get("episodes") if isinstance(data.get("episodes"), list) else []

        def ep_no(e):
            try:
                return float(e.get("epNo") or 0)
            except Exception:
                return 0

        episodes = []
        for e in sorted([e for e in raw_eps if isinstance(e, dict)], key=ep_no):
            if e.get("playable") is False or e.get("id") is None:
                continue
            name = str(e.get("title") or ("第" + str(e.get("epNo") or (len(episodes) + 1)) + "集"))
            val = json.dumps({"episodeId": str(e.get("id"))}, ensure_ascii=False)
            episodes.append(name + "$" + val)
        if not episodes:
            return {"list": []}
        total = data.get("totalEpisodes") or len(episodes)
        lines = [
            "🦋 红果黄剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.site,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        else:
            lines.append("标题：" + title)
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + vid)
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": str(data.get("coverUrl") or data.get("coverHUrl") or ""),
            "vod_remarks": "蝴蝶影视 | 共" + str(total) + "集",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.67},
        }
        return {"list": [vod]}

    def _pick_cookie(self, headers):
        if headers is None:
            return ""
        raw = None
        try:
            raw = headers.get("Set-Cookie")
        except Exception:
            raw = None
        if not raw:
            return ""
        values = []
        get_all = getattr(headers, "get_all", None)
        if get_all:
            try:
                values = get_all("Set-Cookie") or [raw]
            except Exception:
                values = [raw]
        else:
            values = [raw]
        parts = []
        for v in values:
            first = str(v).split(";")[0].strip()
            if "=" in first:
                parts.append(first)
        return "; ".join(parts)

    def _resolve_via_proxy(self, eid):
        url = self.PLAY_PROXY + "/?episodeId=" + urllib.parse.quote(eid, safe="")
        status, text, _ = self._fetch(url)
        if status != 200 or not text:
            return None
        try:
            data = json.loads(text)
        except Exception:
            return None
        if not isinstance(data, dict) or not data.get("ok") or not data.get("url"):
            return None
        signed = str(data["url"])
        qpos = signed.find("?")
        raw_url = signed[:qpos] if qpos >= 0 else signed
        kv = {}
        if qpos >= 0:
            for item in signed[qpos + 1:].split("&"):
                eq = item.find("=")
                if eq > 0:
                    kv[item[:eq]] = item[eq + 1:]
        headers = {"User-Agent": self.UA, "Referer": self.site + "/"}
        if kv.get("Policy") and kv.get("Signature") and kv.get("Key-Pair-Id"):
            headers["Cookie"] = ("CloudFront-Policy=" + kv["Policy"] +
                                 "; CloudFront-Signature=" + kv["Signature"] +
                                 "; CloudFront-Key-Pair-Id=" + kv["Key-Pair-Id"])
        return {"parse": 0, "playUrl": "", "url": raw_url, "header": headers}

    def _resolve_direct(self, eid):
        url = self.API + "/play/" + urllib.parse.quote(eid, safe="")
        status, text, resp_headers = self._fetch(url)
        if status != 200 or not text:
            return None
        try:
            data = json.loads(text)
        except Exception:
            return None
        play_url = str(data.get("url") or "") if isinstance(data, dict) else ""
        if not play_url:
            return None
        headers = {"User-Agent": self.UA, "Referer": self.site + "/"}
        cookie = self._pick_cookie(resp_headers)
        if cookie:
            headers["Cookie"] = cookie
        return {"parse": 0, "playUrl": "", "url": play_url, "header": headers}

    def playerContent(self, flag, id, vipFlags):
        eid = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                eid = str(data.get("episodeId") or "").strip()
        except Exception:
            pass
        headers = {"User-Agent": self.UA, "Referer": self.site + "/"}
        if not eid:
            return {"parse": 1, "playUrl": "", "url": "", "header": headers}
        result = self._resolve_via_proxy(eid)
        if result:
            return result
        for _ in range(2):
            result = self._resolve_direct(eid)
            if result:
                return result
        return {"parse": 1, "playUrl": "", "url": "", "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249681584&sig=6a617d6937827b97
