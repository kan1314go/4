# -*- coding: utf-8 -*-
# 午夜影院

import re
import json
import requests
from urllib.parse import quote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://leaves-fall-gracefully.777hub129.xyz"
    BASE_PATH = "/label/sort999"
    DEFAULT_UA = "Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 Chrome/120 Mobile Safari/537.36"
    BRAND = "蝴蝶影视"
    LINE_NAME = "🦋 蝴蝶专属线路"
    RELATED_LINE = "相关推荐"
    POSTER_RATIO = 1.78
    PAGE_SIZE = 16
    HOME_SIZE = 24
    TIMEOUT = 8

    CLASSES = [
        ("20", "国产自拍"), ("21", "网红主播"), ("22", "国产传媒"), ("23", "人妻熟女"),
        ("24", "探花系列"), ("25", "日本无码"), ("26", "美乳巨乳"), ("27", "强制侵犯"),
        ("28", "制服诱惑"), ("29", "绝色佳人"), ("30", "风俗泡泡浴"), ("31", "家庭乱伦"),
        ("32", "AV解说"), ("33", "A V 解说"), ("34", "三级电影"), ("35", "少女萝莉"),
        ("36", "SM调教"), ("37", "绝顶潮吹"), ("38", "魔镜系列"), ("39", "时间停止"),
        ("40", "催眠洗脑"), ("41", "漫改系列"), ("42", "电车痴汉"), ("43", "淫欲痴女"),
        ("44", "AI换脸"), ("45", "网曝门"), ("46", "TS专区"), ("47", "女性向系列"),
        ("48", "女同性恋"), ("49", "男同性恋"), ("50", "欧美精品"), ("51", "日本动漫"),
        ("52", "3D动漫"), ("53", "韩国主播"), ("54", "泰国风情"), ("55", "OnlyFans"),
    ]

    def __init__(self):
        self.host = self.DEFAULT_HOST

    def init(self, extend=""):
        cfg = {}
        if isinstance(extend, dict):
            cfg = extend
        elif isinstance(extend, str) and extend:
            try:
                cfg = json.loads(extend)
            except Exception:
                cfg = {}
        custom = ""
        if isinstance(cfg, dict):
            custom = str(cfg.get("host", "") or "").strip()
        if custom and custom.startswith("http"):
            self.host = custom.rstrip("/")
        else:
            self.host = self.DEFAULT_HOST
        return True

    def getName(self):
        return "午夜影院"

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        return (".m3u8" in low) or (".mp4" in low) or (".flv" in low) or (".mpd" in low)

    def manualVideoCheck(self):
        return False

    def _referer(self):
        return self.host + self.BASE_PATH + "/"

    def _fetch(self, url, referer=None):
        headers = {"User-Agent": self.DEFAULT_UA, "Referer": referer or self._referer()}
        try:
            resp = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            return resp.status_code, resp.text or ""
        except Exception:
            return -1, ""

    def _unesc(self, s):
        out = str(s or "")
        out = out.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        out = out.replace("&quot;", '"')
        out = re.sub(r"&#0?39;", "'", out)
        out = out.replace("&nbsp;", " ")
        return out

    def _clean(self, s):
        out = re.sub(r"777午夜精品在线影院|777成人网|午夜影院", "", str(s or ""))
        out = self._unesc(out)
        out = re.sub(r"<[^>]+>", " ", out)
        out = re.sub(r"\s+", " ", out)
        return out.strip()

    def _first(self, text, pattern):
        m = re.search(pattern, str(text or ""), re.I | re.S)
        return self._clean(m.group(1)) if m else ""

    def _abs_url(self, v):
        v = self._unesc(str(v or "").strip())
        if not v:
            return ""
        if re.match(r"https?://", v, re.I):
            return v
        if v.startswith(self.BASE_PATH + "/"):
            return self.host + v
        return self.host + self.BASE_PATH + "/" + v.lstrip("/")

    def _parse_cards(self, html):
        out = []
        if not html:
            return out
        seen = set()
        for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']*\/vod\/detail\/id\/(\d+)\.html)["\'][^>]*>', html, re.I):
            url = self._abs_url(m.group(1))
            if url in seen:
                continue
            seen.add(url)
            block = html[max(0, m.start() - 300):min(len(html), m.end() + 1800)]
            title = self._first(block, r'(?:alt|title)=["\']([^"\']+)')
            if not title:
                title = m.group(2)
            pic = self._first(block, r'(?:data-src|data-original|src)=["\']([^"\']+)')
            pic = self._abs_url(pic) if pic else ""
            remark = self._first(block, r'<span[^>]+class=["\'][^"\']*type[^"\']*["\'][^>]*>(.*?)</span>')
            status_text = (self.BRAND + " | " + remark) if remark else (self.BRAND + " | 超清")
            out.append({
                "vod_id": url,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": status_text,
                "style": {"type": "rect", "ratio": self.POSTER_RATIO},
            })
        return out

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        status, doc = self._fetch(self.host + self.BASE_PATH + "/")
        if status != 200:
            return {"list": []}
        return {"list": self._parse_cards(doc)[:self.HOME_SIZE]}

    def _page_result(self, page, items):
        if items:
            return {"page": page, "pagecount": page + 1, "limit": self.PAGE_SIZE, "total": 999, "list": items}
        return {"page": page, "pagecount": page, "limit": self.PAGE_SIZE, "total": 0, "list": []}

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        category_id = str(tid or "").strip() or "20"
        if page > 1:
            path = "/index.php/vod/type/id/" + category_id + "/page/" + str(page) + ".html"
        else:
            path = "/index.php/vod/type/id/" + category_id + ".html"
        status, doc = self._fetch(self._abs_url(path))
        items = self._parse_cards(doc) if status == 200 else []
        return self._page_result(page, items)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_result(page, [])
        url = (self.host + self.BASE_PATH + "/index.php/vod/search.html?wd="
               + quote(keyword, safe="-_.!~*'()") + "&page=" + str(page))
        status, doc = self._fetch(url)
        items = self._parse_cards(doc) if status == 200 else []
        return self._page_result(page, items)

    def _brand_block(self):
        lines = [
            "🦋 午夜影院官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _episode_name(self, name):
        return str(name).replace("$", "_").replace("#", "_")

    def _detail_episodes(self, doc, target):
        episodes = []
        seen = set()
        for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']*vod/play[^"\']+)["\'][^>]*>(.*?)</a>', doc, re.I | re.S):
            pu = self._abs_url(m.group(1))
            if pu in seen:
                continue
            seen.add(pu)
            label = self._clean(m.group(2)) or "播放"
            episodes.append((label, pu))
        if not episodes:
            idm = re.search(r"/id/(\d+)", target)
            nid = idm.group(1) if idm else ""
            episodes.append(("正片", self.host + self.BASE_PATH + "/index.php/vod/play/id/" + nid + "/sid/1/nid/1.html"))
        return episodes

    def detailContent(self, ids):
        raw = ""
        if isinstance(ids, (list, tuple)) and ids:
            raw = str(ids[0])
        elif ids:
            raw = str(ids)
        if not raw:
            return {"list": [], "msg": "未找到该影片"}
        target = self._abs_url(raw)
        status, doc = self._fetch(target)
        if status != 200 or not doc:
            return {"list": [], "msg": "未找到该影片"}
        title = self._first(doc, r"<h1[^>]*>(.*?)</h1>") or self._first(doc, r"<title[^>]*>(.*?)</title>")
        pic = self._first(doc, r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)')
        poster = self._abs_url(pic) if pic else ""
        desc = self._first(doc, r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\'][^>]+content=["\']([^"\']+)')
        episodes = self._detail_episodes(doc, target)
        body = "【影片信息】" + (desc if desc else "午夜影院专属超清直连线路，秒播流畅。")
        content = self._brand_block() + "\n" + body
        flags = [self.LINE_NAME]
        ep_lines = []
        main_eps = []
        for name, pu in episodes:
            main_eps.append(self._episode_name(name) + "$" + json.dumps({"playUrl": pu}, ensure_ascii=False))
        ep_lines.append("#".join(main_eps))
        related = []
        ridx = doc.find("猜你喜欢")
        if ridx >= 0:
            for card in self._parse_cards(doc[ridx:]):
                if card["vod_id"] != raw and card["vod_id"] != target:
                    related.append(card)
        if related:
            flags.append(self.RELATED_LINE)
            rel_eps = []
            for card in related:
                rel_eps.append(self._episode_name(card["vod_name"]) + "$" + "rel:" + card["vod_id"])
            ep_lines.append("#".join(rel_eps))
        vod = {
            "vod_id": raw,
            "vod_name": title if title else "视频详情",
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_remarks": self.BRAND + " | 超清正片",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_content": content,
            "vod_play_from": "$$$".join(flags),
            "vod_play_url": "$$$".join(ep_lines),
        }
        return {"list": [vod]}

    def _resolve_play(self, value):
        headers = {"User-Agent": self.DEFAULT_UA, "Referer": self._referer()}
        if re.search(r"\.m3u8(\?|$)", value, re.I):
            return {"parse": 0, "jx": 0, "url": value, "header": headers}
        if re.search(r"\.(mp4|ts)(\?|$)", value, re.I):
            return {"parse": 0, "jx": 0, "url": value, "header": headers}
        status, page = self._fetch(value)
        if status == 200 and page:
            m = re.search(r'url:\s*["\']\s*([^"\']+\.m3u8[^"\']*)', page, re.I)
            if not m:
                m = re.search(r'(?:hlsUrl|playurl|src|file)\s*[:=]\s*["\']\s*([^"\']+\.m3u8[^"\']*)', page, re.I)
            if m:
                u = m.group(1).strip()
                if u.startswith("//"):
                    u = "https:" + u
                if u.startswith("http"):
                    return {"parse": 0, "jx": 0, "url": u,
                            "header": {"User-Agent": self.DEFAULT_UA, "Referer": value}}
        return {"parse": 0, "jx": 0, "url": "", "msg": "未提取到播放地址"}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("rel:"):
            target = raw[4:].strip()
            if not target:
                return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
            target = self._abs_url(target)
            status, doc = self._fetch(target)
            if status != 200 or not doc:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未提取到播放地址"}
            episodes = self._detail_episodes(doc, target)
            if not episodes:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未提取到播放地址"}
            return self._resolve_play(episodes[0][1])
        env = None
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if isinstance(obj, dict):
                if obj.get("notice"):
                    return {"parse": 0, "msg": str(obj["notice"])}
                env = obj
        if env is None:
            if raw.startswith("http"):
                return self._resolve_play(raw)
            return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
        play_url = str(env.get("playUrl") or "")
        if not play_url:
            return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
        return self._resolve_play(play_url)

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Not Found"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249882396&sig=fbecd3822329e5d9
