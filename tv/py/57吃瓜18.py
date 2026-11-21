# -*- coding: utf-8 -*-
# 57吃瓜 spider for FongMi / TVBox
import json
import random
import re
import urllib.error
import urllib.parse
import urllib.request

from base.spider import Spider as BaseSpider

UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND_NAME = "57吃瓜"
SITE_URL = "https://57duanju.org"
CG_URL = "https://57cg4.com"
IMG_REFERER = "https://57cg4.com/"
TG_GROUP = "https://t.me/tvshare23"
PAGE_SIZE = 20
CANNED_DESC = "暂无详细介绍"

CATEGORIES = [
    ("feed_stream", "🔥 沉浸连刷"),
    ("cat_aichengduanju", "成人AI短剧"),
    ("cat_hot", "热门精选"),
    ("cat_jrcg", "今日吃瓜"),
    ("cat_mrds", "每日大赛"),
    ("cat_wanghong", "网红黑料"),
    ("cat_video", "网黄合集"),
    ("cat_cheating", "出轨劈腿"),
    ("cat_live", "直播擦边"),
    ("cat_society", "社会事件"),
    ("cat_star", "明星八卦"),
    ("cat_all", "全部短剧"),
]
SORT_ROW = {
    "key": "sort", "name": "排序", "init": "",
    "value": [{"n": "最新发布", "v": ""}, {"n": "全站最热", "v": "hot"}, {"n": "飙升热榜", "v": "trending"}],
}
FEED_POOL_SLUGS = ["aichengduanju", "hot", "jrcg", "mrds", "wanghong", "video", "cheating", "live", "all"]

EVENT_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/events/(\d+)/?[\"'][^>]*>([\s\S]*?)</a>", re.I)
TITLE_H_RE = re.compile(r"<h[23][^>]*>([\s\S]*?)</h[23]>", re.I)
IMG_SRC_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.I)
VIDEO_TAG_RE = re.compile(r"<video([^>]+)>", re.I)
LD_JSON_RE = re.compile(r"<script\s+type=[\"']application/ld\+json[\"']>([\s\S]*?)</script>", re.I)
MEDIA_RE = re.compile(r"[\"'](https?://[^\"'\s]+\.(?:m3u8|mp4)[^\"'\s]*)[\"']", re.I)


def strip_tags(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", str(text)).strip()


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = SITE_URL

    def init(self, extend=""):
        self.host = SITE_URL
        if extend:
            text = str(extend).strip()
            if text.startswith("http"):
                self.host = text.rstrip("/")
            else:
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        host = str(data.get("host") or "").strip()
                        if host.startswith("http"):
                            self.host = host.rstrip("/")
                except Exception:
                    pass

    def getName(self):
        return BRAND_NAME

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------------- fetch ----------------

    def _fetch(self, url, referer=""):
        if not url:
            return ""
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.host + url
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else IMG_REFERER,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=4.5) as resp:
                status = resp.getcode() or 0
                body = resp.read().decode("utf-8", "ignore")
                if 200 <= status < 400 and body:
                    return body
                return ""
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "ignore")
            except Exception:
                body = ""
            if 200 <= e.code < 400 and body:
                return body
            return ""
        except Exception:
            return ""

    # ---------------- posters ----------------

    def _wrap_pic(self, raw_url):
        if not raw_url:
            return ""
        pic = str(raw_url).strip()
        if pic.startswith("//"):
            pic = "https:" + pic
        elif pic.startswith("/"):
            pic = self.host + pic
        if "s.chigua.media" in pic and "@Referer=" not in pic:
            return pic + "@Referer=" + urllib.parse.quote(IMG_REFERER, safe="")
        return pic

    # ---------------- cards ----------------

    def _parse_cards(self, html_text, is_feed):
        if not html_text:
            return []
        items = []
        seen = set()
        for m in EVENT_RE.finditer(html_text):
            event_id = m.group(1)
            inner = m.group(2)
            if not event_id or event_id in seen or len(event_id) < 2:
                continue
            seen.add(event_id)
            tm = TITLE_H_RE.search(inner)
            if tm:
                name = strip_tags(tm.group(1))
            else:
                raw_txt = re.sub(r"<[^>]+>", " ", inner).strip()
                name = raw_txt[:40] if raw_txt else ("短剧/热点 " + event_id)
            pic = ""
            for im in IMG_SRC_RE.finditer(inner):
                cand = (im.group(1) or "").strip()
                if ".svg" not in cand and "logo" not in cand:
                    pic = cand
                    break
            title_seg = urllib.parse.quote(name, safe="")
            if is_feed:
                vid = "feed@@" + event_id + "@@" + title_seg
                remarks = "🦋 连刷起播"
            else:
                vid = event_id + "@@" + title_seg
                remarks = "🦋 蝴蝶影视"
            items.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": self._wrap_pic(pic),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.78},
            })
        return items

    # ---------------- streams ----------------

    def _extract_streams(self, html_text):
        if not html_text:
            return []
        episodes = []
        seen = set()
        for m_v in VIDEO_TAG_RE.finditer(html_text):
            attr = m_v.group(1)
            hm = re.search(r"data-hls-src=[\"']([^\"']+)[\"']", attr, re.I)
            sm = re.search(r"src=[\"']([^\"']+)[\"']", attr, re.I)
            stream = hm.group(1).strip() if hm else (sm.group(1).strip() if sm else "")
            if stream and stream not in seen and "logo" not in stream:
                seen.add(stream)
                num = len(episodes) + 1
                episodes.append(("片段 " + ("0" + str(num) if num < 10 else str(num)), stream))
        if not episodes:
            for m_ld in LD_JSON_RE.finditer(html_text):
                block = m_ld.group(1)
                if '"VideoObject"' not in block:
                    continue
                try:
                    data = json.loads(block)
                except Exception:
                    continue
                if not isinstance(data, dict):
                    continue
                v_list = data.get("video") or []
                if not isinstance(v_list, list):
                    v_list = [v_list]
                for v in v_list:
                    c_url = ""
                    if isinstance(v, dict):
                        c_url = v.get("contentUrl") or ""
                    if c_url and c_url not in seen:
                        seen.add(c_url)
                        num = len(episodes) + 1
                        episodes.append(("第 " + ("0" + str(num) if num < 10 else str(num)) + " 集", c_url))
        if not episodes:
            for m_m in MEDIA_RE.finditer(html_text):
                m_url = m_m.group(1)
                if m_url and m_url not in seen and "logo" not in m_url:
                    seen.add(m_url)
                    num = len(episodes) + 1
                    episodes.append(("播放 " + ("0" + str(num) if num < 10 else str(num)), m_url))
        return episodes

    # ---------------- entries ----------------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        result = {"class": classes}
        if filter:
            result["filters"] = {cid: [dict(SORT_ROW)] for cid, cname in CATEGORIES}
        return result

    def homeVideoContent(self):
        res = self.categoryContent("cat_aichengduanju", "1", False, {})
        return {"list": res["list"][:12]}

    def _slug_url(self, slug, page):
        if slug in ("feed_stream", "all"):
            return self.host + "/page/" + str(page) + "/" if page > 1 else self.host + "/"
        if slug in ("aichengduanju", "hot"):
            return self.host + "/" + slug + "/" + str(page) + "/" if page > 1 else self.host + "/" + slug + "/"
        return CG_URL + "/" + slug + "/" + str(page) + "/" if page > 1 else CG_URL + "/" + slug + "/"

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        raw_slug = str(tid or "feed_stream").strip("/")
        is_feed = (raw_slug == "feed_stream")
        slug = raw_slug.replace("cat_", "")
        sort_val = ""
        if extend and isinstance(extend, dict):
            sort_val = str(extend.get("sort") or "")
        url = self._slug_url("feed_stream" if is_feed else slug, page)
        if sort_val:
            url += ("&" if "?" in url else "?") + "sort=" + urllib.parse.quote(sort_val, safe="")
        html_text = self._fetch(url)
        items = self._parse_cards(html_text, is_feed)[:PAGE_SIZE]
        if is_feed and items:
            random.shuffle(items)
        return {"list": items, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        if not keyword:
            return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": page * PAGE_SIZE}
        url = self.host + "/search/?q=" + urllib.parse.quote(keyword, safe="")
        if page > 1:
            url += "&page=" + str(page)
        html_text = self._fetch(url)
        items = self._parse_cards(html_text, False)[:PAGE_SIZE]
        return {"list": items, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}

    # ---------------- detail ----------------

    def _brand_block(self):
        lines = [
            "🦋 " + BRAND_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _fetch_detail_html(self, event_id):
        url = CG_URL + "/events/" + event_id + "/"
        html_text = self._fetch(url)
        if not html_text or len(html_text) < 500:
            url = self.host + "/events/" + event_id + "/"
            html_text = self._fetch(url)
        return html_text, url

    def _capsule_eps(self, event_id, target_url):
        tg_name = "💬 官方交流群 (@tvshare23)"
        origin_name = "🌐 查看源站网页 (" + event_id + ")"
        return [
            tg_name + "$" + json.dumps({"playUrl": TG_GROUP, "web": True}, ensure_ascii=False),
            origin_name + "$" + json.dumps({"playUrl": target_url, "web": True}, ensure_ascii=False),
        ]

    def detailContent(self, ids):
        raw_id = str(ids[0]) if ids else ""
        is_feed = False
        card_title = ""
        if raw_id.startswith("feed@@"):
            is_feed = True
            parts = raw_id.split("@@")
            event_id = parts[1] if len(parts) > 1 else ""
            if len(parts) > 2:
                card_title = urllib.parse.unquote(parts[2])
        else:
            parts = raw_id.split("@@")
            event_id = parts[0]
            if len(parts) > 1:
                card_title = urllib.parse.unquote(parts[1])
        event_id = str(event_id or "").strip("/")
        html_text, target_url = self._fetch_detail_html(event_id)
        title = card_title if card_title else ("AI短剧/热点 " + event_id)
        tm = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html_text, re.I)
        if tm:
            title = strip_tags(tm.group(1))
        desc = CANNED_DESC
        dm = re.search(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']*)[\"']", html_text, re.I)
        if dm:
            desc = dm.group(1).strip()
        cover = ""
        pm = re.search(r"poster=[\"']([^\"']+)[\"']", html_text, re.I) or re.search(r"<meta property=[\"']og:image[\"'] content=[\"']([^\"']+)[\"']", html_text, re.I)
        if pm:
            cover = pm.group(1).strip()
        final_cover = self._wrap_pic(cover)
        real_desc = desc if desc and desc != CANNED_DESC else ""
        if is_feed:
            return {"list": [self._feed_detail(raw_id, event_id, title, real_desc, final_cover, target_url)]}
        episodes = self._extract_streams(html_text)
        ep_values = []
        for name, url in episodes:
            clean_name = name.replace("$", "_").replace("#", "_")
            ep_values.append(clean_name + "$" + json.dumps({"streamUrl": url}, ensure_ascii=False))
        summary = self._brand_block()
        if real_desc:
            summary += "\n" + real_desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：短剧、热点",
                "片源：🦋 57吃瓜在线",
                "编号：" + event_id,
            ])
        remarks = "共 " + str(len(episodes)) + " 个片段" if len(episodes) > 1 else "🦋 蝴蝶影视"
        play_from = []
        play_url = []
        if ep_values:
            play_from.append("🦋 57吃瓜在线")
            play_url.append("#".join(ep_values))
        play_from.append("⚡ 快捷跳转胶囊")
        play_url.append("#".join(self._capsule_eps(event_id, target_url)))
        vod = {
            "vod_id": raw_id,
            "vod_name": title,
            "vod_pic": final_cover,
            "vod_bg": final_cover,
            "vod_background": final_cover,
            "vod_banner": final_cover,
            "vod_remarks": remarks,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_content": summary,
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url),
        }
        return {"list": [vod]}

    def _feed_detail(self, raw_id, event_id, title, real_desc, cover, target_url):
        episodes = []
        first = ("01 · " + title).replace("$", "_").replace("#", "_")
        episodes.append(first + "$" + json.dumps({"eventId": event_id, "feed": True}, ensure_ascii=False))
        pool = list(FEED_POOL_SLUGS)
        random.shuffle(pool)
        sampled = pool[:3]
        targets = []
        seen = {event_id}
        for slug in sampled:
            r_page = random.randint(1, 3)
            url = self._slug_url(slug, r_page)
            s_html = self._fetch(url)
            if s_html:
                for card in self._parse_cards(s_html, False):
                    card_id = card["vod_id"].split("@@")[0]
                    if card_id not in seen:
                        seen.add(card_id)
                        targets.append((card_id, card["vod_name"]))
            if len(targets) >= 60:
                break
        random.shuffle(targets)
        for t_id, t_title in targets:
            seq = len(episodes) + 1
            seq_str = "0" + str(seq) if seq < 10 else str(seq)
            ep_name = (seq_str + " · " + t_title).replace("$", "_").replace("#", "_")
            episodes.append(ep_name + "$" + json.dumps({"eventId": t_id, "feed": True}, ensure_ascii=False))
        summary = self._brand_block()
        if real_desc:
            summary += "\n" + real_desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：短剧、热点",
                "片源：🦋 沉浸连刷专线",
                "编号：" + event_id,
            ])
        return {
            "vod_id": raw_id,
            "vod_name": "🔥 沉浸连刷·" + title,
            "vod_pic": cover,
            "vod_bg": cover,
            "vod_background": cover,
            "vod_banner": cover,
            "vod_remarks": "🦋 蝴蝶影视 | 连刷流 " + str(len(episodes)) + " 条",
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_content": summary,
            "vod_play_from": "🦋 沉浸连刷专线$$$⚡ 快捷跳转胶囊",
            "vod_play_url": "#".join(episodes) + "$$$" + "#".join(self._capsule_eps(event_id, target_url)),
        }

    # ---------------- resolve ----------------

    def playerContent(self, flag, id, vipFlags):
        data = {}
        try:
            data = json.loads(id)
        except Exception:
            data = {}
        if data.get("web") and data.get("playUrl"):
            return {"parse": 1, "url": str(data["playUrl"]),
                    "header": {"User-Agent": UA, "Referer": IMG_REFERER}}
        play_url = str(data.get("streamUrl") or "").strip()
        if data.get("feed") and data.get("eventId"):
            event_id = str(data["eventId"])
            page_html, page_url = self._fetch_detail_html(event_id)
            eps = self._extract_streams(page_html)
            if eps:
                play_url = eps[0][1]
            if not play_url:
                return {"parse": 1, "url": page_url,
                        "header": {"User-Agent": UA, "Referer": IMG_REFERER, "Origin": CG_URL}}
        if not play_url or play_url.startswith("ep_"):
            return {"parse": 1, "url": CG_URL + "/",
                    "header": {"User-Agent": UA, "Referer": IMG_REFERER, "Origin": CG_URL}}
        return {"parse": 0, "url": play_url,
                "header": {"User-Agent": UA, "Referer": IMG_REFERER, "Origin": CG_URL}}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249329767&sig=83695621873f6e70
