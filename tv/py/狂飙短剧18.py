# -*- coding: utf-8 -*-
# 狂飙短剧 蜘蛛（源自 Hamo 插件 com.butterfly.kuangbiaoduanju 的接口逻辑移植）
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://ai.dramarush.tv"
    UA = "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"
    CLASSES = [("成人短剧", "adult_short"), ("正规短剧", "normal_short"), ("短剧", "t-5jxcit")]
    FALLBACK = [
        {"vod_id": "cms5gkpmm08ic016polf4lbnq", "vod_name": "鸭王争霸", "vod_pic": "https://raw.shorttv.online/images/2026-08-08/aa93208f-c3db-46f9-8a1b-8ac55fcc6298.jpg", "vod_remarks": "8集", "trailerUrl": "https://raw.shorttv.online/uploads/direct/cms5gkpmr08id016p43cfqk20/video.mp4", "vod_content": "", "firstEpisodeId": ""},
        {"vod_id": "cmsgx8rgr00lj010fi6lttg9c", "vod_name": "斗破苍穹", "vod_pic": "https://cdn.shorttv.online/images/2026-08-06/fca26c04-5a77-492c-a505-fa7440886090.jpg", "vod_remarks": "7集", "trailerUrl": "/api/media/centaurus/hls/cmsgx8rgu00lk010fjy2kas6p/h264/master.m3u8?tok=69dc75cf2fa24f54fe841a45a7768db4&ep=cmsgx8rgu00lk010fjy2kas6p", "vod_content": "", "firstEpisodeId": ""},
        {"vod_id": "cmse0xyci0d300130psgoy5c5", "vod_name": "魔毒圣缘", "vod_pic": "https://cdn.shorttv.online/images/2026-08-04/2a3f6dc2-7491-4d88c092d0f.png", "vod_remarks": "4集", "trailerUrl": "https://raw.shorttv.online/uploads/direct/cmse0xycl0d310130rev3nav1/video.mp4", "vod_content": "", "firstEpisodeId": ""},
    ]
    PLACEHOLDER_PIC = "dc/img/828ed491f008e85d9caef01a.jpg"

    def getName(self):
        return "狂飙短剧"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.cursors = {}
        self.meta = {}

    def _fetch(self, url, referer="", extra_headers=None, timeout=20):
        headers = {
            "User-Agent": self.UA,
            "Referer": referer or (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        if extra_headers:
            headers.update(extra_headers)
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = resp.status
                    raw = resp.read()
                return status, (raw.decode("utf-8", "replace") if raw else "")
            except urllib.error.HTTPError as e:
                try:
                    raw = e.read()
                    text = raw.decode("utf-8", "replace") if raw else ""
                except Exception:
                    text = ""
                return e.code, text
            except Exception:
                pass
            time.sleep(0.5)
        return 0, ""

    def _api(self, name, data=None):
        url = self.host + "/api/trpc/" + name
        if data is not None:
            enc = urllib.parse.quote(json.dumps({"json": data}, separators=(",", ":"), ensure_ascii=False), safe="-_.!~*'()")
            url += "?input=" + enc
        status, text = self._fetch(url, referer=self.host + "/zh/", extra_headers={"Accept": "application/json,text/plain,*/*"})
        try:
            obj = json.loads(text or "")
            d = obj.get("result", {}).get("data", {}).get("json") if isinstance(obj, dict) else None
            if d is None:
                return {} if data is not None else []
            return d
        except Exception:
            return {} if data is not None else []

    def _fix_url(self, u):
        if u and str(u).startswith("/"):
            return self.host + u
        return u or ""

    def _img_min(self, u):
        if not u or "_minimize." in u:
            return u or ""
        p, q = u, ""
        qi = u.find("?")
        if qi >= 0:
            p, q = u[:qi], u[qi:]
        i = p.rfind(".")
        if i > p.rfind("/"):
            return p[:i] + "_minimize.webp" + q
        return u

    def _pic_of(self, v, x):
        for u in [v.get("cover"), v.get("poster"), x.get("vod_pic")]:
            if not u or self.PLACEHOLDER_PIC in str(u):
                continue
            u = str(u)
            if "cdn.shorttv.online/lsj/" in u:
                u = u.replace("https://cdn.shorttv.online/lsj/", "https://raw.shorttv.online/lsj/")
            return self._img_min(u)
        return ""

    def _norm_item(self, x):
        if not isinstance(x, dict):
            return None
        v = x.get("drama") if isinstance(x.get("drama"), dict) else x
        vid = str(v.get("id") or x.get("id") or "")
        if not vid:
            return None
        tags = []
        if isinstance(v.get("tags"), list):
            for t in v["tags"]:
                tags.append(str(t.get("name") or "") if isinstance(t, dict) else str(t or ""))
        adult = any(t.startswith("adult-") or "不伦" in t or "偷情" in t for t in tags)
        total = v.get("totalEpisodes")
        return {
            "vod_id": vid,
            "vod_name": v.get("title") or x.get("vod_name") or vid,
            "vod_pic": self._pic_of(v, x),
            "vod_remarks": (str(total).strip() + "集") if total else (x.get("vod_remarks") or ""),
            "vod_content": v.get("description") or x.get("vod_content") or "",
            "trailerUrl": self._fix_url(x.get("trailerUrl") or ""),
            "firstEpisodeId": x.get("firstEpisodeId") or "",
            "_adult": adult,
        }

    def _items_of(self, d, mode, need_pic):
        arr = d if isinstance(d, list) else (d.get("items") if isinstance(d, dict) and isinstance(d.get("items"), list) else [])
        out = []
        seen = set()
        for raw in arr:
            it = self._norm_item(raw)
            if not it:
                continue
            if mode == "adult" and not it["_adult"]:
                continue
            if mode == "normal" and it["_adult"]:
                continue
            if need_pic and not it["vod_pic"]:
                continue
            name_key = re.sub(r"\s+", "", str(it["vod_name"]))
            if it["vod_id"] in seen or ("n:" + name_key) in seen:
                continue
            seen.add(it["vod_id"])
            seen.add("n:" + name_key)
            out.append(it)
        return out

    def _list_page(self, tid, pg):
        mp = {
            "t-5jxcit": {"categorySlug": "t-5jxcit"},
            "adult_short": {"tagSlug": "adult"},
            "normal_short": {"contentKind": "SHORT_DRAMA"},
            "short_kind": {"contentKind": "SHORT_DRAMA"},
        }
        cursor = ""
        if pg > 1:
            cursor = self.cursors.get((tid, pg), "")
            if not cursor:
                return []
        mode = "normal" if tid == "normal_short" else "all"
        out = []
        nxt = ""
        if tid in ("recommend", "all", ""):
            d = self._api("feed.recommend", {"limit": 12})
            nxt = d.get("nextCursor") if isinstance(d, dict) and d.get("nextCursor") else ""
            out = self._items_of(d, mode, False)
        else:
            data = {"limit": 12}
            data.update(mp.get(tid, {"categorySlug": tid}))
            if cursor:
                data["cursor"] = cursor
            loops = 8 if tid in ("adult_short", "normal_short") else 1
            for _ in range(loops):
                d_browse = self._api("feed.browse", data)
                nxt = d_browse.get("nextCursor") if isinstance(d_browse, dict) and d_browse.get("nextCursor") else ""
                sub = self._items_of(d_browse, mode, tid == "normal_short")
                for it in sub:
                    out.append(it)
                    if len(out) >= 12:
                        break
                if len(out) >= 12 or not nxt:
                    break
                data["cursor"] = nxt
        seen = set()
        deduped = []
        for it in out:
            if it["vod_id"] in seen:
                continue
            seen.add(it["vod_id"])
            deduped.append(it)
        for it in deduped:
            self.meta[it["vod_id"]] = it
        if nxt:
            self.cursors[(tid, pg + 1)] = nxt
        return deduped

    def _card(self, it):
        return {
            "vod_id": it["vod_id"],
            "vod_name": it["vod_name"],
            "vod_pic": it["vod_pic"] or "",
            "vod_remarks": "蝴蝶影视 | " + (it["vod_remarks"] or "正片"),
            "style": {"type": "rect", "ratio": 0.75},
        }

    def _get_drama(self, vid):
        if vid in self.meta:
            return self.meta[vid]
        for fb in self.FALLBACK:
            if fb["vod_id"] == vid:
                return dict(fb)
        return None

    def homeContent(self, filter=False):
        return {"class": [{"type_id": cid, "type_name": name} for name, cid in self.CLASSES]}

    def homeVideoContent(self):
        items = self._list_page("recommend", 1)
        if not items:
            items = self._list_page("t-5jxcit", 1)
        if not items:
            items = [dict(fb) for fb in self.FALLBACK]
        return {"list": [self._card(it) for it in items]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        items = self._list_page(str(tid or "t-5jxcit"), page)
        return {"list": [self._card(it) for it in items], "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        keyword = str(key or "").strip()
        if not keyword or page > 1:
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        pool = {}
        for it in self._list_page("recommend", 1):
            pool[it["vod_id"]] = it
        for p in range(1, 6):
            li = self._list_page("t-5jxcit", p)
            if not li:
                break
            for it in li:
                pool[it["vod_id"]] = it
            if len(pool) >= 72:
                break
        hits = [it for it in pool.values() if keyword in str(it["vod_name"])]
        return {"list": [self._card(it) for it in hits], "page": page, "pagecount": page, "limit": len(hits), "total": len(hits)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0] or "")
        it = self._get_drama(vid)
        if not it:
            self._list_page("t-5jxcit", 1)
            it = self._get_drama(vid)
        if not it:
            it = {"vod_id": vid, "vod_name": vid, "vod_pic": "", "vod_remarks": "12集", "vod_content": "", "trailerUrl": "", "firstEpisodeId": ""}
        m = re.search(r"(\d+)", str(it.get("vod_remarks") or ""))
        total = int(m.group(1)) if m else 12
        total = max(1, min(total, 80))
        eps_arr = []
        d = self._api("episode.watch", {"dramaId": vid, "episodeNumber": 1})
        if isinstance(d, dict) and isinstance(d.get("episodes"), list):
            eps_arr = d["episodes"]
        episodes = []
        if eps_arr:
            for i in range(1, total + 1):
                eid = ""
                if i - 1 < len(eps_arr) and isinstance(eps_arr[i - 1], dict) and eps_arr[i - 1].get("id"):
                    eid = str(eps_arr[i - 1]["id"])
                val = json.dumps({"vid": vid, "ep": i, "eid": eid}, ensure_ascii=False)
                episodes.append("第" + str(i) + "集$" + val)
        else:
            val = json.dumps({"vid": vid, "ep": 1, "eid": it.get("firstEpisodeId") or ""}, ensure_ascii=False)
            episodes.append("第1集$" + val)
        title = str(it.get("vod_name") or vid)
        desc = str(it.get("vod_content") or "")
        lines = [
            "🦋 狂飙短剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        else:
            lines.append("标题：" + title)
            lines.append("片源：🦋 蝴蝶狂飙专线")
            lines.append("编号：" + vid)
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": it.get("vod_pic") or "",
            "vod_remarks": "蝴蝶影视 | " + (it.get("vod_remarks") or ("共" + str(len(episodes)) + "集")),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶狂飙专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.75},
        }
        return {"list": [vod]}

    def _unesc(self, s):
        return str(s or "").replace("\\u0026", "&").replace("\\/", "/")

    def _media_from_html(self, h):
        h = self._unesc(h)
        m = re.search(r'<video[^>]+src="([^"]+)"', h)
        if not m:
            m = re.search(r'"(?:hlsUrl|playUrl|videoUrl|sourceUrl|mediaUrl|trailerUrl)"\s*:\s*"([^"]+?\.(?:m3u8|mp4)[^"]*)"', h)
        if not m:
            m = re.search(r'https?://[^\s"<>]+?\.(?:mp4|m3u8)[^\s"<>]*', h)
            if m:
                return self._fix_url(m.group(0))
            return ""
        return self._fix_url(m.group(1))

    def _eid_from_html(self, h):
        h = self._unesc(h)
        m = re.search(r'"episode"\s*:\s*\{[^{}]*"id"\s*:\s*"([^"]+)"', h)
        if not m:
            m = re.search(r'"(?:episodeId|id)"\s*:\s*"(cms[a-z0-9]{10,})"', h)
        return m.group(1) if m else ""

    def _alive(self, u):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": self.UA, "Range": "bytes=0-0", "Referer": self.host + "/", "Origin": self.host})
            with urllib.request.urlopen(req, timeout=4) as resp:
                return resp.status in (200, 206)
        except urllib.error.HTTPError as e:
            return e.code in (200, 206)
        except Exception:
            return False

    def playerContent(self, flag, id, vipFlags):
        headers = {"User-Agent": self.UA, "Referer": self.host + "/zh/", "Origin": self.host}
        vid, ep, eid = "", 1, ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                vid = str(data.get("vid") or "")
                ep = data.get("ep") or 1
                eid = str(data.get("eid") or "")
        except Exception:
            pass
        url = ""
        if eid:
            url = "https://raw.shorttv.online/uploads/direct/" + eid + "/video.mp4"
        html = ""
        if not url:
            status, text = self._fetch(self.host + "/zh/watch/" + vid + "/" + str(ep))
            html = text or ""
            url = self._media_from_html(html)
        if not url:
            found_eid = self._eid_from_html(html)
            if found_eid:
                cands = [
                    "https://raw.shorttv.online/uploads/direct/" + found_eid + "/video.mp4",
                    "https://cdn.shorttv.online/uploads/direct/" + found_eid + "/video.mp4",
                    "https://cdn.shorttv.online/uploads/hls/" + found_eid + "/master.m3u8",
                    "https://cdn.shorttv.online/lsj/hls/" + found_eid + "/master.m3u8",
                    "https://cdn.shorttv.online/dc/hls/" + found_eid + "/master.m3u8",
                ]
                for cand in cands:
                    if self._alive(cand):
                        url = cand
                        break
        if not url:
            it = self._get_drama(vid)
            if it and it.get("trailerUrl"):
                url = self._fix_url(it["trailerUrl"])
        if not url:
            return {"parse": 1, "playUrl": "", "url": self.host + "/zh/watch/" + vid + "/" + str(ep), "header": headers}
        url = self._unesc(url)
        return {"parse": 0, "playUrl": "", "url": url, "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249812268&sig=f7cde31e80c30517
