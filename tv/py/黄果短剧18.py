# -*- coding: utf-8 -*-
# 黄果短剧 蜘蛛（源自 Hamo 插件 com.butterfly.huangguo 的接口逻辑移植）
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://huangguo-parser.yishengheqiu7679.workers.dev"
    SITE_HOST = "https://huangguoai.io"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    HG_KEY = "88f1f4f88de7eaf666233b1f4779dbab"
    PAGE_SIZE = 50
    SORT_FILTER = [
        {"key": "sort", "name": "排序", "value": [
            {"n": "最新更新", "v": "latest"},
            {"n": "当前热播", "v": "hot"},
            {"n": "独家原创", "v": "original"},
            {"n": "随机推荐", "v": "random"},
        ]},
    ]
    BASE_CLASSES = [
        ("ai-duanju", "AI短剧"), ("ai-manju", "AI漫剧"),
        ("rank:hot", "热播榜"), ("rank:recommend", "推荐榜"), ("rank:potential", "潜力榜"),
        ("chigua", "吃瓜·全部"), ("chigua:remen", "吃瓜·热门"), ("chigua:yuanchuang", "吃瓜·AI原创"),
    ]

    def getName(self):
        return "黄果短剧"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.classes_cache = None
        self.home_cache = None
        self.meta_cache = {}

    def _headers(self):
        return {
            "User-Agent": self.UA,
            "Referer": self.host + "/",
            "Accept": "application/json",
            "X-HG-Key": self.HG_KEY,
        }

    def _fetch(self, url, method="GET", body=None):
        for _ in range(3):
            try:
                data = None
                if method == "POST":
                    data = json.dumps(body or {}).encode("utf-8")
                req = urllib.request.Request(url, headers=self._headers(), data=data, method=method)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    if resp.status != 200:
                        return ""
                    raw = resp.read()
                if raw:
                    text = raw.decode("utf-8", "replace")
                    if text.strip():
                        return text
            except Exception:
                pass
            time.sleep(0.5)
        return ""

    def _api(self, path, method="GET", body=None):
        text = self._fetch(self.host + path, method=method, body=body)
        if not text:
            return {}
        try:
            data = json.loads(text)
        except Exception:
            return {}
        if not isinstance(data, dict) or data.get("error"):
            return {}
        return data

    def _clean(self, s):
        if s is None:
            return ""
        out = re.sub(r"<[^>]+>", "", str(s))
        out = out.replace("&amp;", "&").replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">")
        return re.sub(r"\s+", " ", out).strip()

    def _remarks(self, meta):
        clean = self._clean(meta)
        if clean:
            return "蝴蝶影视 | " + clean
        return "蝴蝶影视"

    def _pic(self, u):
        u = str(u or "")
        if not u:
            return ""
        if re.match(r"^https?://", u, re.I):
            return self.host + "/media?url=" + urllib.parse.quote(u, safe="")
        if u.startswith("/"):
            return self.host + u
        return self.host + "/" + u

    def _tags(self, x, key):
        out = []
        val = x.get(key)
        if isinstance(val, list):
            for t in val:
                if isinstance(t, str) and t:
                    out.append(t)
        return out

    def _vod_card(self, x, cat_name):
        if not isinstance(x, dict):
            return None
        vid = str(x.get("vod_id") or x.get("id") or "")
        title = self._clean(x.get("vod_name") or x.get("title") or "")
        if not vid or not title:
            return None
        poster = self._pic(x.get("vod_pic") or x.get("cover") or "")
        self.meta_cache[vid] = {"pic": poster, "cat": cat_name or ""}
        return {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": self._remarks(x.get("vod_remarks") or ""),
            "style": {"type": "rect", "ratio": 0.75},
        }

    def _site_card(self, x):
        if not isinstance(x, dict):
            return None
        vid = str(x.get("id") or "")
        title = self._clean(x.get("title") or "")
        if not vid or not title:
            return None
        poster = self._pic(x.get("cover") or "")
        try:
            eps = int(x.get("episode_count") or 0)
        except Exception:
            eps = 0
        remarks = ""
        if eps > 0:
            remarks = ("全" + str(eps) + "集") if x.get("is_finished") else ("更新至" + str(eps) + "集")
        if x.get("score"):
            remarks = (remarks + " · " + str(x.get("score")) + "分") if remarks else (str(x.get("score")) + "分")
        self.meta_cache[vid] = {"pic": poster, "cat": ""}
        return {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": self._remarks(remarks),
            "style": {"type": "rect", "ratio": 0.75},
        }

    def _post_card(self, x):
        if not isinstance(x, dict):
            return None
        pid = str(x.get("id") or "")
        title = self._clean(x.get("title") or "")
        if not pid or not title:
            return None
        poster = self._pic(x.get("cover") or "")
        created = self._clean(x.get("created_at") or "")
        self.meta_cache["archives_" + pid] = {"pic": poster, "created": created}
        return {
            "vod_id": "archives_" + pid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": self._remarks(created) if created else "蝴蝶影视 | 吃瓜",
            "style": {"type": "rect", "ratio": 2.03},
        }

    def _topic_short(self, title):
        t = str(title or "")
        for suf in ("AI成人短剧专辑", "AI短剧专辑", "AI成人漫剧专辑", "AI漫剧专辑", "专辑", "专题"):
            if t.endswith(suf):
                t = t[: -len(suf)]
                break
        t = t.replace("AI", "").replace("成人", "")
        t = re.sub(r"短剧|漫剧", "", t)
        if not t:
            t = str(title or "").replace("AI", "")
        return t[:10]

    def _classes(self):
        if self.classes_cache is not None:
            return self.classes_cache
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.BASE_CLASSES]
        filters = {"ai-duanju": self.SORT_FILTER, "ai-manju": self.SORT_FILTER}
        data = self._api("/api/topics")
        topics = data.get("list") if isinstance(data.get("list"), list) else []
        for it in topics:
            if not isinstance(it, dict) or not it.get("vod_id"):
                continue
            vid = str(it["vod_id"])
            if not vid.startswith("topic_"):
                continue
            slug = vid[6:]
            if not slug:
                continue
            tid = "topic:" + slug
            classes.append({"type_id": tid, "type_name": "专题·" + self._topic_short(it.get("vod_name") or "")})
        self.classes_cache = (classes, filters)
        return self.classes_cache

    def homeContent(self, filter=False):
        classes, filters = self._classes()
        result = {"class": classes}
        if filter:
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        if self.home_cache is not None:
            return {"list": self.home_cache}
        cards = []
        data = self._api("/api/all")
        secs = data.get("sections") if isinstance(data.get("sections"), dict) else {}
        rec = secs.get("recommend") if isinstance(secs.get("recommend"), dict) else {}
        if isinstance(rec.get("list"), list):
            cards = rec["list"]
        if not cards:
            f = self._api("/api/category/ai-duanju?page=1&size=" + str(self.PAGE_SIZE) + "&sort=latest")
            if isinstance(f.get("list"), list):
                cards = f["list"]
        items = []
        seen = set()
        for raw in cards:
            card = self._vod_card(raw, "")
            if card and card["vod_id"] not in seen:
                seen.add(card["vod_id"])
                items.append(card)
        self.home_cache = items
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        cid = str(tid or "")
        items = []
        if cid in ("ai-duanju", "ai-manju"):
            sort = "latest"
            if isinstance(extend, dict):
                raw = str(extend.get("sort") or "")
                if raw in ("latest", "hot", "original", "random"):
                    sort = raw
            cat_name = "AI短剧" if cid == "ai-duanju" else "AI漫剧"
            d = self._api("/api/category/" + cid + "?page=" + str(page) + "&size=" + str(self.PAGE_SIZE) + "&sort=" + sort)
            for raw in d.get("list") or []:
                card = self._vod_card(raw, cat_name)
                if card:
                    items.append(card)
        elif cid.startswith("rank:"):
            kind = cid[5:]
            if kind in ("hot", "recommend", "potential") and page <= 1:
                r = self._api("/api/ranks/" + kind + "?page=1&size=" + str(self.PAGE_SIZE))
                for raw in r.get("list") or []:
                    card = self._vod_card(raw, "")
                    if card:
                        items.append(card)
        elif cid.startswith("topic:"):
            slug = cid[6:]
            if slug and page <= 1:
                t = self._api("/api/topics?slug=" + urllib.parse.quote(slug, safe="") + "&page=1&size=" + str(self.PAGE_SIZE))
                for raw in t.get("list") or []:
                    card = self._vod_card(raw, "")
                    if card:
                        items.append(card)
        elif cid.startswith("chigua"):
            cate = "all"
            if cid == "chigua:remen":
                cate = "remen"
            elif cid == "chigua:yuanchuang":
                cate = "yuanchuang"
            elif cid != "chigua":
                cate = ""
            if cate:
                p = self._api("/api/site/posts?cate=" + cate + "&page=" + str(page) + "&size=" + str(self.PAGE_SIZE))
                pdata = p.get("data") if isinstance(p.get("data"), dict) else {}
                for raw in pdata.get("items") or []:
                    card = self._post_card(raw)
                    if card:
                        items.append(card)
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        keyword = self._clean(key or "")
        if not keyword:
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        items = []
        s = self._api("/api/site/search?q=" + urllib.parse.quote(keyword, safe="") + "&page=" + str(page) + "&size=" + str(self.PAGE_SIZE))
        sdata = s.get("data") if isinstance(s.get("data"), dict) else {}
        for raw in sdata.get("items") or []:
            card = self._site_card(raw)
            if card:
                items.append(card)
        if not items and page == 1:
            w = self._api("/api/search/" + urllib.parse.quote(keyword, safe="") + "?page=1&size=" + str(self.PAGE_SIZE))
            for raw in w.get("list") or []:
                card = self._vod_card(raw, "")
                if card:
                    items.append(card)
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def _content(self, title, cat_name, vid, desc):
        lines = [
            "🦋 黄果短剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        intro = self._clean(desc)
        if intro:
            lines.append(intro)
        else:
            lines.append("标题：" + str(title or ""))
            if cat_name:
                lines.append("分类：" + str(cat_name))
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + str(vid))
        return "\n".join(lines)

    def _post_videos(self, pid):
        d = self._api("/api/site/posts/" + urllib.parse.quote(str(pid), safe="") + "/playback", method="POST", body={})
        data = d.get("data") if isinstance(d.get("data"), dict) else {}
        out = []
        vids = data.get("videos") if isinstance(data.get("videos"), list) else []
        for i, v in enumerate(vids):
            if not isinstance(v, dict) or not v.get("url"):
                continue
            try:
                idx = int(v.get("index")) if v.get("index") is not None else i
            except Exception:
                idx = i
            out.append({"index": idx, "url": str(v["url"])})
        return out

    def _post_detail(self, pid):
        d = self._api("/api/site/posts/" + urllib.parse.quote(str(pid), safe=""))
        data = d.get("data")
        return data if isinstance(data, dict) else None

    def _detail_post(self, item_id):
        pid = item_id[9:]
        data = self._api("/api/detail/" + urllib.parse.quote(item_id, safe=""))
        lst = data.get("list") if isinstance(data.get("list"), list) else []
        x = lst[0] if lst else None
        if not isinstance(x, dict):
            return {"list": []}
        title = self._clean(x.get("vod_name") or "")
        if not title:
            return {"list": []}
        meta = self.meta_cache.get(item_id) or {}
        poster = self._pic(x.get("vod_pic") or "") or meta.get("pic") or ""
        episodes = []
        vids = self._post_videos(pid)
        for i, v in enumerate(vids):
            val = json.dumps({"pid": pid, "idx": v["index"]}, ensure_ascii=False)
            episodes.append("视频" + str(i + 1) + "$" + val)
        if not episodes:
            pd = self._post_detail(pid)
            if pd:
                own = str(pd.get("video_url") or "")
                if re.match(r"^https?:", own, re.I):
                    val = json.dumps({"pid": pid, "idx": 0, "via": "video_url"}, ensure_ascii=False)
                    episodes.append("第1集$" + val)
                else:
                    m = re.search(r"/video/(\d+)/", str(pd.get("content") or ""))
                    if m:
                        val = json.dumps({"vid": m.group(1), "ep": "1", "via": "bridge"}, ensure_ascii=False)
                        episodes.append("第1集$" + val)
        if not episodes:
            return {"list": []}
        created = meta.get("created") or ""
        status_text = created or self._clean(x.get("vod_remarks") or "") or "吃瓜"
        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": self._remarks(status_text),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": self._content(title, "吃瓜", item_id, ""),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 2.03},
        }
        return {"list": [vod]}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        item_id = str(ids[0] or "")
        if item_id.startswith("archives_"):
            return self._detail_post(item_id)
        data = self._api("/api/detail/" + urllib.parse.quote(item_id, safe=""))
        lst = data.get("list") if isinstance(data.get("list"), list) else []
        x = lst[0] if lst else None
        if not isinstance(x, dict):
            return {"list": []}
        title = self._clean(x.get("vod_name") or "")
        if not title:
            return {"list": []}
        meta = self.meta_cache.get(item_id) or {}
        poster = self._pic(x.get("vod_pic") or "") or meta.get("pic") or ""
        if title == item_id and not poster:
            return {"list": []}
        remarks = self._clean(x.get("vod_remarks") or "")
        desc = x.get("vod_desc") or x.get("description") or ""
        cat_name = meta.get("cat") or ""
        genres = self._tags(x, "vod_tags")
        episodes = []
        eps = x.get("episodes") if isinstance(x.get("episodes"), list) else []
        for i, ep in enumerate(eps):
            if not isinstance(ep, dict):
                continue
            num = str(ep.get("ep") or (i + 1))
            name = self._clean(ep.get("title") or ("第" + num + "集"))
            val = json.dumps({"vid": item_id, "ep": num}, ensure_ascii=False)
            episodes.append(name + "$" + val)
        if not episodes:
            return {"list": []}
        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": self._remarks(remarks),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": self._content(title, cat_name, item_id, desc),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.75},
        }
        if genres:
            vod["vod_class"] = ",".join(genres)
        if x.get("vod_year"):
            vod["vod_year"] = str(x["vod_year"])
        return {"list": [vod]}

    def _resolve_post(self, pid, idx):
        vids = self._post_videos(pid)
        picked = None
        for v in vids:
            if v["index"] == idx:
                picked = v
                break
        if picked is None and vids:
            picked = vids[idx] if 0 <= idx < len(vids) else vids[0]
        if picked and picked.get("url"):
            return picked["url"]
        pd = self._post_detail(pid)
        if pd:
            own = str(pd.get("video_url") or "")
            if re.match(r"^https?:", own, re.I):
                return own
            m = re.search(r"/video/(\d+)/", str(pd.get("content") or ""))
            if m:
                d = self._api("/api/play?url=" + urllib.parse.quote(m.group(1), safe="") + "&ep=1")
                if d.get("url"):
                    return str(d["url"])
        return ""

    def playerContent(self, flag, id, vipFlags):
        vid = ""
        ep = ""
        pid = ""
        idx = 0
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                vid = str(data.get("vid") or "")
                ep = str(data.get("ep") or "")
                pid = str(data.get("pid") or "")
                try:
                    idx = int(data.get("idx") or 0)
                except Exception:
                    idx = 0
        except Exception:
            pass
        headers = {"User-Agent": self.UA, "Referer": self.SITE_HOST + "/"}
        url = ""
        if vid and ep:
            d = self._api("/api/play?url=" + urllib.parse.quote(vid, safe="") + "&ep=" + urllib.parse.quote(ep, safe=""))
            url = str(d.get("url") or "")
        elif pid:
            url = self._resolve_post(pid, idx)
        if url.startswith("http"):
            return {"parse": 0, "playUrl": "", "url": url, "header": headers}
        return {"parse": 1, "playUrl": "", "url": "", "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249701041&sig=5c55a4e7b32bbc5f
