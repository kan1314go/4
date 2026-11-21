# -*- coding: utf-8 -*-
# TikTok FongMi spider (converted from Hamo plugin tiktok.js, PornTok)
# Site: PornTok (porntok.io) vertical short videos, continuous-play pool detail

import json
import re
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://porntok.io"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
TIMEOUT = 8
SOURCE_NAME = "🦋 蝴蝶专线"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
HOME_PAGE_SIZE = 38

CLASSES = [
    ("all", "🔥 热门推荐"),
    ("teen-18plus", "📱 Teen 18+"),
    ("big-tits", "🍑 巨乳大翘臀"),
    ("amateur", "🎀 业余自拍"),
    ("asian", "🌸 亚洲精选"),
    ("milf", "💄 熟女人妻"),
    ("anal", "🍑 极品后庭"),
    ("hentai-animated", "✨ 动漫二次元"),
    ("latina", "💃 拉丁热舞"),
    ("ebony", "🖤 黑人珍珠"),
    ("indian", "👳 印度风情"),
]

VIDEO_RE = re.compile(r"(https?://(?:media\.porntok\.io|[^\s\"'<>]+\.r2\.dev)/videos/[^\s\"'<>]+\.mp4)", re.I)
TAG_RE = re.compile(r"/videos/([^/]+)/", re.I)
FILE_RE = re.compile(r"/([^/]+)\.mp4", re.I)


def _page_num(pg):
    try:
        n = int(pg)
    except (TypeError, ValueError):
        n = 1
    return n if n > 0 else 1


def _extract_videos(text):
    if not text:
        return []
    clean = text.replace('\\"', '"').replace('\\/', '/').replace('\\\\', '')
    videos = []
    seen = set()
    for raw in VIDEO_RE.findall(clean):
        path = raw.strip().replace("\\", "").replace("'", "").replace('"', "")
        if path in seen:
            continue
        seen.add(path)
        base = path[:path.rfind(".")]
        m = FILE_RE.search(path)
        vid = m.group(1) if m else str(len(seen))
        videos.append({"id": vid, "path": path, "thumb": base + "_thumb.webp"})
    return videos


def _tag_display(path):
    m = TAG_RE.search(path)
    if m:
        return "#" + m.group(1).replace("_", " ")
    return ""


def _card_title(tag, idx):
    head = tag if tag else "PornTok"
    return head + " 短视频 " + str(idx + 1).zfill(2)


class Spider(BaseSpider):
    host = DEFAULT_HOST

    def getName(self):
        return "TikTok"

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "")
        elif extend:
            s = str(extend).strip()
            if s.startswith("{"):
                try:
                    obj = json.loads(s)
                except ValueError:
                    obj = None
                if isinstance(obj, dict):
                    custom = str(obj.get("host") or "")
            else:
                custom = s
        custom = custom.strip()
        if custom.startswith("http"):
            self.host = custom.rstrip("/")

    def _fetch(self, url):
        headers = {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=TIMEOUT)
            if 200 <= resp.status_code < 400:
                return resp.text or ""
        except Exception:
            pass
        return ""

    def _cat_url(self, tid):
        if not tid or tid == "all":
            return self.host + "/"
        return self.host + "/category/" + quote(str(tid), safe="")

    def _card(self, video, tid, idx):
        tag = _tag_display(video["path"])
        title = _card_title(tag, idx)
        remarks = "🦋 蝴蝶影视 | " + (tag if tag else "高清秒开")
        vod_id = (video["id"] + "@@" + quote(video["path"], safe="") + "@@"
                  + str(tid) + "@@" + quote(title, safe=""))
        return {
            "vod_id": vod_id,
            "vod_name": title,
            "vod_pic": video["thumb"],
            "vod_remarks": remarks,
        }

    def _list_page(self, tid, page):
        videos = _extract_videos(self._fetch(self._cat_url(tid)))
        items = [self._card(v, tid, i) for i, v in enumerate(videos)]
        if not items:
            return {"list": [], "page": page, "pagecount": page,
                    "limit": HOME_PAGE_SIZE, "total": 0}
        return {"list": items, "page": page, "pagecount": 1,
                "limit": len(items), "total": len(items)}

    def homeContent(self, filter=False):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in CLASSES]}

    def homeVideoContent(self):
        videos = _extract_videos(self._fetch(self.host + "/"))
        items = [self._card(v, "all", i) for i, v in enumerate(videos[:20])]
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        page = _page_num(pg)
        raw_tid = str(tid or "all").strip() or "all"
        return self._list_page(raw_tid, page)

    def searchContent(self, key, quick, pg="1"):
        page = _page_num(pg)
        return {"list": [], "page": page, "pagecount": page,
                "limit": HOME_PAGE_SIZE, "total": 0}

    def detailContent(self, ids):
        raw_id = str(ids[0]) if ids else ""
        parts = raw_id.split("@@")
        link = unquote(parts[1]) if len(parts) > 1 else ""
        tid = parts[2] if len(parts) > 2 and parts[2] else "all"
        title = unquote(parts[3]) if len(parts) > 3 and parts[3] else "PornTok 短视频"
        screen = ""
        if link:
            screen = link[:link.rfind(".")] + "_thumb.webp"

        videos = _extract_videos(self._fetch(self._cat_url(tid)))
        stream = []
        seen = set()
        if link:
            stream.append({"name": title, "url": link, "still": screen})
            seen.add(link)
        for i, v in enumerate(videos):
            p = v["path"]
            if p in seen:
                continue
            seen.add(p)
            tag = _tag_display(p)
            tag_name = tag[1:] if tag else "推荐"
            stream.append({
                "name": "#" + tag_name + " 短视频 " + str(i + 1).zfill(2),
                "url": p,
                "still": v["thumb"],
            })

        ep_strs = []
        for i, item in enumerate(stream):
            prefix = "▶ 当前播放 " if i == 0 else str(i).zfill(2) + ". "
            name = (prefix + item["name"]).replace("$", "").replace("#", "")
            ep_strs.append(name + "$" + item["url"])

        lines = [
            "🦋 PornTok官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
            "【💡 温馨提示：PornTok 竖屏流媒体短视频，支持全屏连刷自适应。】",
            "🦋 蝴蝶影视专线直连 | 4K高清原生极速画质",
        ]
        vod = {
            "vod_id": raw_id,
            "vod_name": title,
            "vod_pic": screen,
            "vod_bg": screen,
            "vod_background": screen,
            "vod_banner": screen,
            "vod_actor": BRAND_ACTOR,
            "vod_class": "短视频,TikTok",
            "vod_remarks": "🦋 蝴蝶影视 | 直链秒开",
            "vod_content": "\n".join(lines),
            "vod_play_from": SOURCE_NAME,
            "vod_play_url": "#".join(ep_strs),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = str(id or "").strip()
        if not play_url or play_url.startswith("ep_"):
            return {"parse": 0, "msg": "未获取到有效的短视频媒体直链"}
        return {"parse": 0, "url": play_url,
                "header": {"User-Agent": UA, "Referer": self.host + "/"}}

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250218196&sig=42091224670e430d
