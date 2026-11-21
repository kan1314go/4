# -*- coding: utf-8 -*-
# 橙果短剧 蜘蛛（源自 Hamo 插件 com.butterfly.chengguodj 的解析逻辑移植）
import base64
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    HOST = "https://chengguodj.com"
    UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6.1 Mobile/15E148 Safari/604.1"
    PLAY_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    PLACEHOLDER = "https://dummyimage.com/600x800/1e293b/ffffff.png&text=NO_COVER"
    CLASSES = [
        ("yuanchuang", "原创短剧"), ("mogai", "魔改短剧"), ("manju", "漫剧"),
        ("zhenren", "真人短剧"), ("aiduanju", "AI短剧"), ("browse", "片库索引"),
    ]

    def getName(self):
        return "橙果短剧"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.home_cache = None
        self.meta_cache = {}

    def _fetch(self, url):
        urls = [url]
        if url.startswith("https://"):
            urls.append("http://" + url[8:])
        headers = {
            "User-Agent": self.UA,
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        for u in urls:
            for _ in range(2):
                try:
                    req = urllib.request.Request(u, headers=headers)
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

    def _strip_tags(self, text):
        if not text:
            return ""
        s = str(text)
        s = re.sub(r"<[^>]+>", "", s)
        s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
        s = s.replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")
        return re.sub(r"\s+", " ", s).strip()

    def _remarks(self, meta):
        clean = self._strip_tags(meta)
        clean = re.sub(r"[\r\n\t]+", " ", clean).strip()
        if clean:
            return "蝴蝶影视 | " + clean
        return "蝴蝶影视"

    def _pic(self, raw_url):
        if not raw_url:
            return self.PLACEHOLDER
        u = str(raw_url).replace("\\u002F", "/").replace("\\/", "/").strip().strip("'\"")
        if u.startswith("//"):
            u = "https:" + u
        elif u.startswith("/"):
            u = self.host + u
        elif not u.startswith("http"):
            u = self.host + "/" + u
        try:
            b64 = base64.b64encode(u.encode("utf-8")).decode("utf-8")
            b64 = b64.replace("+", "-").replace("/", "_").rstrip("=")
            return self.host + "/_img/" + b64
        except Exception:
            return u

    def _nuxt_arr(self, html):
        if not html:
            return None
        m = re.search(r'<script[^>]+id=["\']__NUXT_DATA__["\'][^>]*>([\s\S]*?)</script>', html, re.I)
        if not m:
            return None
        try:
            arr = json.loads(m.group(1).strip())
            return arr if isinstance(arr, list) else None
        except Exception:
            return None

    def _idx(self, arr, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)) and int(v) < len(arr):
            return arr[int(v)]
        return v

    def _parse_list(self, html):
        items = []
        arr = self._nuxt_arr(html)
        if not arr:
            return items
        seen = set()
        for item in arr:
            if not isinstance(item, dict):
                continue
            if "title" not in item or ("slug" not in item and "detail_route" not in item):
                continue
            title = self._idx(arr, item.get("title"))
            if not title or not isinstance(title, str):
                continue
            drama_path = self._idx(arr, item.get("detail_route"))
            if not drama_path:
                slug = self._idx(arr, item.get("slug"))
                if slug:
                    drama_path = "/drama/" + str(slug)
            if not drama_path or not isinstance(drama_path, str) or drama_path in seen:
                continue
            cover_obj = self._idx(arr, item.get("cover"))
            final_pic = ""
            if isinstance(cover_obj, dict):
                raw_u = self._idx(arr, cover_obj.get("url"))
                if raw_u and isinstance(raw_u, str):
                    final_pic = self._pic(raw_u)
            eps_val = item.get("total_episode_count")
            if eps_val is None:
                eps_val = item.get("published_episode_count")
            if eps_val is None:
                eps_val = item.get("latest_episode_number")
            eps_num = ""
            if isinstance(eps_val, (int, float)) and not isinstance(eps_val, bool) and int(eps_val) < len(arr) and not isinstance(arr[int(eps_val)], (dict, list)):
                eps_num = str(arr[int(eps_val)])
            elif eps_val is not None:
                eps_num = str(eps_val)
            remarks = self._remarks(eps_num + "集") if eps_num else "蝴蝶影视"
            seen.add(drama_path)
            card = {
                "vod_id": drama_path,
                "vod_name": self._strip_tags(title),
                "vod_pic": final_pic or self.PLACEHOLDER,
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 0.56},
            }
            items.append(card)
            existing = self.meta_cache.get(drama_path)
            if not existing or existing.get("pic") == self.PLACEHOLDER or card["vod_pic"] != self.PLACEHOLDER:
                self.meta_cache[drama_path] = {"title": card["vod_name"], "pic": card["vod_pic"]}
        return items

    def homeContent(self, filter=False):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]}

    def homeVideoContent(self):
        if self.home_cache is not None:
            return {"list": self.home_cache}
        html = self._fetch(self.host + "/yuanchuang")
        self.home_cache = self._parse_list(html)
        return {"list": self.home_cache}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        t = str(tid or "yuanchuang").strip("/")
        if page <= 1:
            url = self.host + "/" + t
        else:
            url = self.host + "/" + t + "/page-" + str(page)
        items = self._parse_list(self._fetch(url))
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        url = self.host + "/search?keyword=" + urllib.parse.quote(str(key), safe="")
        if page > 1:
            url += "&page=" + str(page)
        items = self._parse_list(self._fetch(url))
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        drama_path = str(ids[0] or "").strip()
        if drama_path.startswith("http"):
            detail_url = drama_path
        else:
            detail_url = self.host + "/" + drama_path.lstrip("/")
        html = self._fetch(detail_url)
        vod_name = ""
        m = re.search(r"<title>([^<]+)</title>", html, re.I)
        if m:
            vod_name = m.group(1).split("-")[0].replace("在线观看", "").strip()
        pic = ""
        wm = re.search(r'["\'](https?://[^"\']*wlwvch\.cn[^"\']+)["\']', html, re.I)
        if wm:
            pic = self._pic(wm.group(1))
        if not pic:
            cached = self.meta_cache.get(drama_path) or {}
            pic = cached.get("pic") or ""
        desc = ""
        dm = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html, re.I)
        if dm:
            desc = self._strip_tags(dm.group(1))
        slug = drama_path.strip("/").split("/")[-1]
        episodes = []
        arr = self._nuxt_arr(html)
        if arr:
            for item in arr:
                if isinstance(item, dict) and "total_episode_count" in item:
                    tot = self._idx(arr, item.get("total_episode_count"))
                    if isinstance(tot, (int, float)) and not isinstance(tot, bool) and tot > 0:
                        for i in range(1, int(tot) + 1):
                            val = json.dumps({"playPath": "/play/" + slug + "/" + str(i)}, ensure_ascii=False)
                            episodes.append("第" + str(i) + "集$" + val)
                        break
        if not episodes:
            links = []
            seen_links = set()
            for lm in re.finditer(r'href=["\'](/play/[^"\']+)["\']', html, re.I):
                p_link = lm.group(1).strip()
                if p_link not in seen_links:
                    seen_links.add(p_link)
                    links.append(p_link)
            for link in links:
                tail = link.split("/")[-1]
                name = ("第" + tail + "集") if re.match(r"^\d+$", tail) else tail
                val = json.dumps({"playPath": link}, ensure_ascii=False)
                episodes.append(name + "$" + val)
        if not episodes:
            tm = re.search(r"(\d+)\s*(?:集|话|部)", html)
            max_ep = int(tm.group(1)) if tm else 1
            for i in range(1, max_ep + 1):
                val = json.dumps({"playPath": "/play/" + slug + "/" + str(i)}, ensure_ascii=False)
                episodes.append("第" + str(i) + "集$" + val)
        title = vod_name or "短剧详情"
        lines = [
            "🦋 橙果短剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        else:
            lines.append("标题：" + title)
            lines.append("片源：🦋 橙果专线")
            lines.append("编号：" + slug)
        vod = {
            "vod_id": drama_path,
            "vod_name": title,
            "vod_pic": pic or self.PLACEHOLDER,
            "vod_remarks": self._remarks(str(len(episodes)) + "集"),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 橙果专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.56},
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_path = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                play_path = str(data.get("playPath") or "")
        except Exception:
            play_path = str(id or "")
        if play_path and not play_path.startswith("/") and not play_path.startswith("http"):
            play_path = "/" + play_path
        play_url = play_path if play_path.startswith("http") else (self.host + play_path)
        html = self._fetch(play_url)
        video_url = ""
        arr = self._nuxt_arr(html)
        if arr:
            for item in arr:
                if isinstance(item, str) and ".m3u8" in item and item.startswith("http"):
                    video_url = item
                    break
        if not video_url:
            mm = re.search(r'["\'](https?://[^"\'\s<>\\]+\.m3u8[^"\'\s<>\\]*)["\']', html, re.I)
            if mm:
                video_url = mm.group(1).replace("\\u002F", "/").replace("\\/", "/")
        headers = {"User-Agent": self.PLAY_UA, "Referer": self.host + "/"}
        if video_url.startswith("http"):
            return {"parse": 0, "playUrl": "", "url": video_url, "header": headers}
        return {"parse": 1, "playUrl": "", "url": play_url, "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249519946&sig=9af8fed8ffcff71a
