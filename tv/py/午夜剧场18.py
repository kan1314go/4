# -*- coding: utf-8 -*-
# 午夜剧场

import re
import json
import base64
import requests
from urllib.parse import quote, unquote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://due.wyjc9.xyz"
    FALLBACK_HOSTS = ["https://bra.wyjc7.quest"]
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    BRAND = "蝴蝶影视"
    LINE_NAME = "🦋 蝴蝶专属线路"
    RELATED_LINE = "相关推荐"
    CARD_REMARKS = "蝴蝶影视 | 高清"
    DETAIL_REMARKS = "蝴蝶影视 | 高清正片"
    ACTOR = "🦋 TG群: @tvshare23"
    SUMMARY_BODY = "【影片信息】午夜剧场专属高清线路，秒播流畅观看。"
    DETAIL_EMPTY_MSG = "详情页面为空"
    PLAY_FAIL_MSG = "未能定位有效播放资源"
    POSTER_RATIO = 1.78
    PAGE_SIZE = 84
    HOME_SIZE = 24
    TIMEOUT = 8

    CLASSES = [
        ("/vodtype/21.html", "国产精品"),
        ("/vodtype/22.html", "无码专区"),
        ("/vodtype/23.html", "中文字幕"),
        ("/vodtype/20.html", "美女写真"),
        ("/vodtype/26.html", "亚洲情色"),
        ("/vodtype/25.html", "人妻熟女"),
        ("/vodtype/27.html", "制服丝袜"),
        ("/vodtype/28.html", "SM捆绑"),
        ("/vodtype/30.html", "三级伦理"),
        ("/vodtype/24.html", "强奸乱伦"),
        ("/vodtype/29.html", "自淫系列"),
    ]

    IMG_OK = re.compile(r"\.(?:jpe?g|png|webp|gif)(?:[?#]|$)", re.I)
    CARD_RE = re.compile(r"<a[^>]+href=['\"](/\d+\.html)['\"][^>]*>([\s\S]*?)</a>", re.I)
    STREAM_RE = re.compile(r"\.(?:m3u8|mp4)(?:[?#]|$)", re.I)

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
        return "午夜剧场"

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        return (".m3u8" in low) or (".mp4" in low) or (".flv" in low) or (".mpd" in low)

    def manualVideoCheck(self):
        return False

    def _enc(self, s):
        return quote(str(s or ""), safe="!*'()")

    def _unescape(self, s):
        out = str(s or "")
        out = out.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        out = out.replace("&quot;", '"')
        out = re.sub(r"&#0?39;", "'", out)
        out = out.replace("&nbsp;", " ")
        return out

    def _abs_url(self, u, host):
        s = str(u or "").strip().replace("\\/", "/")
        if not s:
            return ""
        if s.startswith("//"):
            return "https:" + s
        if s.startswith("http"):
            return s
        if s.startswith("/"):
            return host + s
        return host + "/" + s

    def _format_poster(self, raw, host):
        if not raw:
            return ""
        pic = self._abs_url(str(raw).strip().replace("&amp;", "&"), host)
        if not pic:
            return ""
        return pic + "@Referer=" + self._enc(host + "/") + "&User-Agent=" + self._enc(self.DEFAULT_UA)

    def _fetch(self, url, referer=None):
        headers = {
            "User-Agent": self.DEFAULT_UA,
            "Referer": referer or (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "X-Requested-With": "XMLHttpRequest",
        }
        bases = [self.host]
        for fb in self.FALLBACK_HOSTS:
            if fb != self.host:
                bases.append(fb)
        for base in bases:
            target = url
            if base != self.host and url.startswith(self.host):
                target = base + url[len(self.host):]
            try:
                resp = requests.get(target, headers=headers, timeout=self.TIMEOUT)
            except Exception:
                continue
            if base != self.host:
                self.host = base
            return resp.status_code, resp.text or "", base
        return -1, "", self.host

    def _parse_cards(self, html, host):
        items = []
        if not html:
            return items
        seen = set()
        for m in self.CARD_RE.finditer(html):
            href = m.group(1)
            whole = m.group(0)
            open_tag = whole[:whole.index(">") + 1]
            inner = m.group(2)
            title = ""
            tm = re.search(r"title=['\"]([^'\"]+)['\"]", open_tag, re.I)
            if tm:
                title = tm.group(1)
            pic = ""
            im = re.search(r"<img[^>]+>", inner, re.I)
            if im:
                alt = re.search(r"alt=['\"]([^'\"]+)['\"]", im.group(0), re.I)
                if not title and alt:
                    title = alt.group(1)
                sm = re.search(r"src=['\"]([^'\"]+)['\"]", im.group(0), re.I)
                if sm and self.IMG_OK.search(sm.group(1).strip()):
                    pic = sm.group(1).strip()
            clean_href = self._abs_url(href, host)
            if clean_href in seen:
                continue
            if not title:
                continue
            title = self._unescape(title.strip())
            if not title or title == "午夜剧场":
                continue
            seen.add(clean_href)
            pic_abs = self._abs_url(pic, host) if pic else ""
            vod_id = clean_href + "@@" + pic_abs if pic_abs else clean_href
            items.append({
                "vod_id": vod_id,
                "vod_name": title,
                "vod_pic": self._format_poster(pic_abs, host) if pic_abs else "",
                "vod_remarks": self.CARD_REMARKS,
                "style": {"type": "rect", "ratio": self.POSTER_RATIO},
            })
        return items

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        status, doc, host = self._fetch(self.host + self.CLASSES[0][0], self.host + "/")
        if status != 200:
            return {"list": []}
        return {"list": self._parse_cards(doc, host)[:self.HOME_SIZE]}

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
        category_id = str(tid or "").strip() or self.CLASSES[0][0]
        path = category_id if category_id.startswith("/") else ("/" + category_id)
        if page > 1:
            path = path.replace(".html", "-" + str(page) + ".html", 1)
        status, doc, host = self._fetch(self.host + path, self.host + "/")
        items = self._parse_cards(doc, host) if status == 200 else []
        return self._page_result(page, items)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_result(page, [])
        enc = self._enc(keyword)
        if page > 1:
            path = "/s/" + enc + "/page/" + str(page) + ".html"
        else:
            path = "/s/" + enc + ".html"
        status, doc, host = self._fetch(self.host + path, self.host + "/")
        items = self._parse_cards(doc, host) if status == 200 else []
        return self._page_result(page, items)

    def _detail_title(self, html):
        m = re.search(r"<title>([\s\S]*?)</title>", html, re.I)
        if not m:
            return ""
        t = self._unescape(m.group(1).strip())
        t = re.sub(r"^正在播放\s*[:：]\s*", "", t)
        t = re.sub(r"\s*[-–—]\s*午夜剧场\s*$", "", t)
        return t.strip()

    def _brand_block(self, host):
        lines = [
            "🦋 午夜剧场官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _episode_name(self, name):
        return str(name).replace("$", "_").replace("#", "_")

    def detailContent(self, ids):
        raw = ""
        if isinstance(ids, (list, tuple)) and ids:
            raw = str(ids[0])
        elif ids:
            raw = str(ids)
        if not raw:
            return {"list": [], "msg": self.DETAIL_EMPTY_MSG}
        page_part = raw.split("@@")[0]
        card_poster = raw.split("@@", 1)[1] if "@@" in raw else ""
        target = page_part if page_part.startswith("http") else self._abs_url(page_part, self.host)
        status, doc, host = self._fetch(target, self.host + "/")
        if status != 200 or not doc:
            return {"list": [], "msg": self.DETAIL_EMPTY_MSG}
        title = self._detail_title(doc) or "精彩正片"
        vod_pic_raw = ""
        if card_poster and self.IMG_OK.search(card_poster):
            vod_pic_raw = card_poster
        if not vod_pic_raw:
            for im in re.finditer(r"<img[^>]+>", doc, re.I):
                alt = re.search(r"alt=['\"]([^'\"]+)['\"]", im.group(0), re.I)
                if alt and self._unescape(alt.group(1).strip()) == title:
                    sm = re.search(r"src=['\"]([^'\"]+)['\"]", im.group(0), re.I)
                    if sm and self.IMG_OK.search(sm.group(1).strip()):
                        vod_pic_raw = self._abs_url(sm.group(1).strip(), host)
                        break
        genres = []
        gm = re.search(r"类型：[\s\S]{0,120}?>([^<>]{2,20})<", doc, re.I)
        if gm:
            genres.append(self._unescape(gm.group(1).strip()))
        year = ""
        ym = re.search(r"时间：[\s\S]{0,120}?(\d{4})-\d{2}-\d{2}", doc, re.I)
        if ym:
            year = ym.group(1)
        page_url = self._abs_url(page_part, host)
        poster = self._format_poster(vod_pic_raw, host) if vod_pic_raw else ""
        content = self._brand_block(host) + "\n" + self.SUMMARY_BODY
        flags = [self.LINE_NAME]
        main_eps = [self._episode_name("正片") + "$" + json.dumps({"playUrl": page_url}, ensure_ascii=False)]
        ep_lines = ["#".join(main_eps)]
        ridx = doc.find(self.RELATED_LINE)
        if ridx >= 0:
            related = []
            for card in self._parse_cards(doc[ridx:], host):
                if card["vod_id"].split("@@")[0] != page_url:
                    related.append(card)
            if related:
                flags.append(self.RELATED_LINE)
                rel_eps = []
                for card in related:
                    rel_eps.append(self._episode_name(card["vod_name"]) + "$" + "rel:" + card["vod_id"])
                ep_lines.append("#".join(rel_eps))
        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_year": year,
            "vod_remarks": self.DETAIL_REMARKS,
            "vod_actor": self.ACTOR,
            "vod_content": content,
            "vod_play_from": "$$$".join(flags),
            "vod_play_url": "$$$".join(ep_lines),
        }
        if genres:
            vod["vod_class"] = ",".join(genres)
        return {"list": [vod]}

    def _b64_decode_utf8(self, s):
        try:
            raw = str(s or "")
            raw += "=" * (-len(raw) % 4)
            return base64.b64decode(raw).decode("utf-8", "replace")
        except Exception:
            return ""

    def _decode_play_url(self, u, enc):
        out = str(u or "")
        try:
            if str(enc) == "1":
                out = unquote(out)
            elif str(enc) == "2":
                d = self._b64_decode_utf8(out)
                if d:
                    out = unquote(d)
        except Exception:
            pass
        return out.replace("\\/", "/")

    def _extract_player_url(self, html):
        s = str(html or "")
        rm = re.search(r"const\s+rawUrl\s*=\s*['\"]([^'\"]+)['\"]", s, re.I)
        if rm:
            return rm.group(1).strip()
        pm = re.search(r"(?:player_data|player_aaaa|mac_player_data)[\s\S]*?['\"]url['\"]\s*:\s*['\"]([^'\"]+)['\"]", s, re.I)
        if pm:
            em = re.search(r"(?:player_data|player_aaaa|mac_player_data)[\s\S]*?['\"]encrypt['\"]\s*:\s*(\d+)", s, re.I)
            return self._decode_play_url(pm.group(1), em.group(1) if em else "0")
        vm = re.search(r"<video[^>]+src=['\"]([^'\"]+)['\"]", s, re.I)
        if vm:
            return vm.group(1).strip()
        mm = re.search(r"['\"](https?://[^'\"]+\.m3u8[^'\"]*)['\"]", s, re.I)
        if mm:
            return mm.group(1).strip()
        mp = re.search(r"['\"](https?://[^'\"]+\.mp4[^'\"]*)['\"]", s, re.I)
        if mp:
            return mp.group(1).strip()
        return ""

    def _play_headers(self):
        return {"User-Agent": self.DEFAULT_UA, "Referer": self.host + "/"}

    def _resolve_page(self, page_url):
        fail = {"parse": 0, "jx": 0, "url": "", "msg": self.PLAY_FAIL_MSG}
        if not page_url or not str(page_url).startswith("http"):
            return fail
        page_url = str(page_url)
        if self.STREAM_RE.search(page_url):
            return {"parse": 0, "jx": 0, "url": page_url, "header": self._play_headers()}
        status, doc, host = self._fetch(page_url, self.host + "/")
        if status == -1:
            return fail
        u = self._extract_player_url(doc)
        if u and u.startswith("http"):
            target = self._abs_url(u, host)
            return {"parse": 0, "jx": 0, "url": target, "header": self._play_headers()}
        return {"parse": 1, "jx": 0, "url": page_url, "header": self._play_headers()}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("rel:"):
            target = raw[4:].strip()
            if not target:
                return {"parse": 0, "jx": 0, "url": "", "msg": self.PLAY_FAIL_MSG}
            page = target.split("@@")[0]
            if not page.startswith("http"):
                page = self._abs_url(page, self.host)
            return self._resolve_page(page)
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if isinstance(obj, dict):
                if obj.get("notice"):
                    return {"parse": 0, "msg": str(obj["notice"])}
                page = str(obj.get("playUrl") or obj.get("url") or "")
                return self._resolve_page(page)
            return {"parse": 0, "jx": 0, "url": "", "msg": self.PLAY_FAIL_MSG}
        if raw.startswith("http"):
            return self._resolve_page(raw)
        return {"parse": 0, "jx": 0, "url": "", "msg": self.PLAY_FAIL_MSG}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Not Found"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249881086&sig=d68159c0fee46ef7
