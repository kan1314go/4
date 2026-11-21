# -*- coding: utf-8 -*-
# 爱黑料 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.aiheiliao)
import json
import random
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://aiheiliao1.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND_NAME = "爱黑料"
PAGE_SIZE = 36

CATEGORIES = [
    ("feed_stream", "🔥 沉浸连刷"),
    ("root_home", "全部最新"),
    ("newUpdate", "今日吃瓜"),
    ("rmdg", "热门大瓜"),
    ("hwcg", "黑料大事件"),
    ("whmx", "网红明星"),
    ("xsxy", "学生校园"),
    ("fcmg", "反差母狗"),
    ("tqzj", "偷情抓奸"),
    ("shsj", "社会事件"),
    ("flkp", "福利看片"),
]

FEED_POOL = ["newUpdate", "rmdg", "hwcg", "whmx", "xsxy", "fcmg", "tqzj", "shsj", "root_home"]

AD_KEYWORDS = ["重金求稿", "变现", "高价收购", "商务合作", "吃瓜导航", "我要投稿", "关于我们", "求瓜"]
BLOCK_SKIP = ("xqbj-recommand", "swiper-slide", "post-card-ads", "ad-card")
PIC_ATTRS = ("data-original", "data-src", "data-bg", "data-thumb")

XQBJ_RE = re.compile(r'<div[^>]+class=["\'][^"\']*xqbj-recommand[^"\']*["\'][\s\S]*?</div>\s*</div>\s*</div>', re.I)
ASIDE_RE = re.compile(r"<aside[\s\S]*?</aside>", re.I)
WIDGET_RE = re.compile(r'<div[^>]+class=["\'][^"\']*(?:widget|sidebar)[^"\']*["\'][\s\S]*?</div>', re.I)
POSTCARD_RE = re.compile(r'<div[^>]+class=["\'][^"\']*post-card[^"\']*["\'][^>]*>[\s\S]*?</div>\s*</div>', re.I)
ANCHOR_BLOCK_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/(\d+)/?["\'][^>]*>([\s\S]*?)</a>', re.I)
CARD_ID_RE = re.compile(r'id=["\']post-card-(\d+)["\']', re.I)
ARCHIVES_ID_RE = re.compile(r"/archives/(\d+)/", re.I)
TITLE_H_RE = re.compile(r"<h[234][^>]*>([\s\S]*?)</h[234]>", re.I)
TITLE_SUFFIX_RE = re.compile(r"\s*(?:热搜\s*HOT|HOT|置顶|独家|NEW|吃瓜\s*HOT|爆料\s*HOT)\s*$", re.I)
DATE_ITEMPROP_RE = re.compile(r'itemprop=["\']datePublished["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2})', re.I)
DATE_CN_RE = re.compile(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)")
DATE_DASH_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
BANNER_FN_RE = re.compile(r"loadBannerDirect\s*\(\s*['\"]([^'\"]+)['\"]", re.I)
LOADIMG_FN_RE = re.compile(r"loadImage\s*\(\s*['\"]([^'\"]+)['\"]", re.I)
BG_URL_RE = re.compile(r'style=["\'][^"\']*background(?:-image)?\s*:\s*url\((["\']?)([^"\')]+)\1\)', re.I)
IMG_SRC_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)
ARTICLE_VIDEOS_RE = re.compile(r'id=["\']article-videos["\'][^>]+data-url=(["\'])([\s\S]*?)\1', re.I)
DATA_URL_RE = re.compile(r'data-url=(["\'])([\s\S]*?)\1', re.I)
URL_SCAN_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
TRAILING_JUNK_RE = re.compile(r"[\s\]\}]+$")
DATA_BANNER_RE = re.compile(r'data-banner=["\']([^"\']+)["\']', re.I)
DATACONFIG_RE = re.compile(r"data-config=([\"'])([\s\S]*?)\1", re.I)
CFG_URL_RE = re.compile(r'["\']url["\']\s*:\s*["\']([^"\']+)["\']', re.I)
VIDEO_TAG_RE = re.compile(r"<video[^>]+>", re.I)
VIDEO_SRC_RE = re.compile(r'(?:data-hls-src|data-src|src)=["\']([^"\']+)["\']', re.I)
QUOTED_STREAM_RE = re.compile(r'[\"\'](https?:[\\/]+[^"\'\s]+\.(?:m3u8|mp4)[^"\'\s]*)[\"\']', re.I)
H1_RE = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']*)["\']', re.I)
POST_CONTENT_RE = re.compile(r'<div[^>]+class=["\'][^"\']*post-content[^"\']*["\'][^>]*>([\s\S]*?)(?:<div[^>]+class=["\'][^"\']*(?:post-footer|post-tags|comments)["\']|</article>)', re.I)
SUBLINK_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/(\d+)/?["\'][^>]*>([\s\S]*?)</a>', re.I)
SUBLINK_SIMPLE_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/(\d+)/?["\'][^>]*>', re.I)
LABEL_STRIP_RE = re.compile(r"[$#\r\n\t]")
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


# ---------- text helpers ----------

def strip_tags(text):
    if not text:
        return ""
    return WS_RE.sub(" ", TAG_RE.sub("", str(text))).strip()


def clean_title(raw):
    if not raw:
        return ""
    t = strip_tags(raw)
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    t = t.replace("&quot;", '"').replace("&#039;", "'").replace("&nbsp;", " ")
    t = TITLE_SUFFIX_RE.sub("", t)
    return t.strip()


def clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw)
    clean = clean.replace("\\u0068ttps", "https").replace("\\u0068ttp", "http")
    clean = clean.replace("\\/", "/").replace('\\"', '"')
    clean = clean.replace("&quot;", "").replace("'", "").replace('"', "")
    clean = TRAILING_JUNK_RE.sub("", clean)
    clean = clean.strip()
    if clean.startswith("//"):
        clean = "https:" + clean
    return clean


# ---------- spider ----------

class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST

    def getName(self):
        return BRAND_NAME

    def init(self, extend=""):
        host = ""
        ext = extend
        if isinstance(ext, str) and ext.strip():
            text = ext.strip()
            if text.startswith("http"):
                host = text
            else:
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        host = str(data.get("host") or "")
                except Exception:
                    pass
        elif isinstance(ext, dict):
            host = str(ext.get("host") or "")
        if host.startswith("http"):
            self.host = host.rstrip("/")

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- fetch ----------

    def _headers(self):
        return {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _fetch_once(self, url):
        resp = requests.get(url, headers=self._headers(), timeout=8)
        if resp is not None and 200 <= resp.status_code < 400 and resp.text:
            return resp.text
        return ""

    def _fetch(self, url):
        target = url
        if target.startswith("//"):
            target = "https:" + target
        elif target.startswith("/"):
            target = self.host + target
        try:
            body = self._fetch_once(target)
            if body:
                return body
        except Exception:
            if target.startswith("https://"):
                try:
                    return self._fetch_once("http://" + target[8:])
                except Exception:
                    return ""
        return ""

    # ---------- poster ----------

    def _format_poster(self, raw_pic):
        if not raw_pic:
            return ""
        p = str(raw_pic).strip().strip("'\"").replace("&amp;", "&")
        if p.startswith("//"):
            p = "https:" + p
        elif p.startswith("http://") or p.startswith("https://"):
            pass
        elif p.startswith("/") and not p.startswith("/upload"):
            p = self.host + p
        suffix = "@Referer=" + quote(self.host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")
        return p + suffix

    def _extract_card_pic(self, block):
        m = DATA_BANNER_RE.search(block)
        if m and m.group(1):
            c1 = m.group(1).strip()
            if c1 and "img-placeholder" not in c1:
                return c1
        m = BANNER_FN_RE.search(block)
        if m and m.group(1):
            c2 = m.group(1).strip()
            if c2 and "img-placeholder" not in c2:
                return c2
        m = LOADIMG_FN_RE.search(block)
        if m and m.group(1):
            c3 = m.group(1).strip()
            if c3 and "img-placeholder" not in c3:
                return c3
        for attr in PIC_ATTRS:
            m = re.search(attr + r'=["\']([^"\']+)["\']', block, re.I)
            if m and m.group(1):
                val = m.group(1).strip()
                low = val.lower()
                if val and "logo" not in low and "img-placeholder" not in val and ".svg" not in low:
                    return val
        m = BG_URL_RE.search(block)
        if m and m.group(2):
            c4 = m.group(2).strip()
            if c4 and "img-placeholder" not in c4:
                return c4
        m = IMG_SRC_RE.search(block)
        if m and m.group(1):
            src = m.group(1).strip()
            low = src.lower()
            if src and "logo" not in low and "img-placeholder" not in src and "avatar" not in low and ".svg" not in low:
                return src
        return ""

    # ---------- card list ----------

    def _parse_card_list(self, html_text, is_feed):
        items = []
        seen = set()
        clean = XQBJ_RE.sub("", str(html_text or ""))
        clean = ASIDE_RE.sub("", clean)
        clean = WIDGET_RE.sub("", clean)
        blocks = [m.group(0) for m in POSTCARD_RE.finditer(clean)]
        if not blocks:
            blocks = [m.group(0) for m in ANCHOR_BLOCK_RE.finditer(clean)]
        for inner in blocks:
            if any(mark in inner for mark in BLOCK_SKIP):
                continue
            m_id = CARD_ID_RE.search(inner) or ARCHIVES_ID_RE.search(inner)
            if not m_id:
                continue
            aid = m_id.group(1).strip()
            if aid in seen or aid == "139553":
                continue
            m_title = TITLE_H_RE.search(inner)
            if m_title:
                name = clean_title(m_title.group(1))
            else:
                raw_txt = strip_tags(inner)
                name = clean_title(raw_txt[:60]) if raw_txt else ("热点爆料 " + aid)
            if not name:
                continue
            if any(word in name for word in AD_KEYWORDS):
                continue
            seen.add(aid)
            post_date = ""
            m_dt = DATE_ITEMPROP_RE.search(inner)
            if m_dt:
                post_date = m_dt.group(1).strip()
            else:
                m_cn = DATE_CN_RE.search(inner)
                if m_cn:
                    post_date = WS_RE.sub("", m_cn.group(1)).strip()
                else:
                    m_dash = DATE_DASH_RE.search(inner)
                    if m_dash:
                        post_date = m_dash.group(1).strip()
            pic = self._format_poster(self._extract_card_pic(inner))
            if is_feed:
                remarks = "蝴蝶影视 | 连刷起播"
                vod_id = "feed@@" + aid + "@@" + quote(name, safe="")
            else:
                remarks = "蝴蝶影视 | " + (post_date if post_date else "现场实录")
                vod_id = aid + "@@" + quote(name, safe="")
            items.append({
                "aid": aid,
                "title": name,
                "vod": {
                    "vod_id": vod_id,
                    "vod_name": name,
                    "vod_pic": pic,
                    "vod_remarks": remarks,
                    "style": {"type": "rect", "ratio": 1.78},
                },
            })
        return items

    # ---------- stream extraction ----------

    def _extract_video_urls(self, html_content):
        html_content = html_content or ""
        video_list = []

        m_container = ARTICLE_VIDEOS_RE.search(html_content) or DATA_URL_RE.search(html_content)
        if m_container and m_container.group(2):
            raw_val = m_container.group(2)
            raw_val = raw_val.replace("&quot;", '"').replace("&amp;", "&")
            raw_val = raw_val.replace("&#039;", "'").replace("&lt;", "<").replace("&gt;", ">")
            raw_val = raw_val.strip()
            if raw_val.startswith("["):
                try:
                    parsed_list = json.loads(raw_val)
                    if isinstance(parsed_list, list):
                        video_list = parsed_list
                except Exception:
                    video_list = URL_SCAN_RE.findall(raw_val)
            elif raw_val:
                video_list = [raw_val]

        if not video_list:
            for m in DATACONFIG_RE.finditer(html_content):
                raw_cfg = m.group(2)
                raw_cfg = raw_cfg.replace("&quot;", '"').replace("&amp;", "&")
                raw_cfg = raw_cfg.replace("&#039;", "'").replace("&lt;", "<").replace("&gt;", ">")
                m_url = CFG_URL_RE.search(raw_cfg)
                if m_url and m_url.group(1):
                    video_list.append(m_url.group(1))

        if not video_list:
            for m in VIDEO_TAG_RE.finditer(html_content):
                m_src = VIDEO_SRC_RE.search(m.group(0))
                if m_src and m_src.group(1):
                    video_list.append(m_src.group(1))

        if not video_list:
            for m in QUOTED_STREAM_RE.finditer(html_content):
                video_list.append(m.group(1))

        seen = set()
        result = []
        for v in video_list:
            v_clean = clean_stream_url(v)
            if v_clean and v_clean not in seen and "logo" not in v_clean.lower():
                seen.add(v_clean)
                result.append(v_clean)
        return result

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        html = self._fetch(self.host + "/")
        items = self._parse_card_list(html, False)[:12]
        return {"list": [it["vod"] for it in items]}

    def _page_form(self, items, page):
        return {
            "list": items,
            "page": page,
            "pagecount": page + 1,
            "limit": PAGE_SIZE,
            "total": (page + 1) * PAGE_SIZE,
        }

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        cid = str(tid or "").strip("/")
        if not cid:
            cid = "feed_stream"
        is_feed = cid == "feed_stream"
        if is_feed or cid in ("root_home", "index", "home"):
            url = (self.host + "/page/" + str(page) + "/") if page > 1 else (self.host + "/")
        else:
            url = (self.host + "/category/" + cid + "/" + str(page) + "/") if page > 1 else (self.host + "/category/" + cid + "/")
        html = self._fetch(url)
        items = self._parse_card_list(html, is_feed)
        if is_feed and items:
            random.shuffle(items)
        return self._page_form([it["vod"] for it in items], page)

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        keyword = str(key or "").strip()
        if not keyword or any(word in keyword for word in AD_KEYWORDS):
            return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": page * PAGE_SIZE}
        enc = quote(keyword, safe="")
        url = (self.host + "/search/" + enc + "/" + str(page) + "/") if page > 1 else (self.host + "/search/" + enc + "/")
        html = self._fetch(url)
        items = self._parse_card_list(html, False)
        return self._page_form([it["vod"] for it in items], page)

    # ---------- detail ----------

    def _brand_block(self):
        lines = [
            "🦋 " + BRAND_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _summary(self, desc, title, source_name, aid):
        block = self._brand_block()
        if desc:
            return block + "\n" + desc
        fallback = [
            "标题：" + title,
            "分类：",
            "片源：" + source_name,
            "编号：" + aid,
        ]
        return block + "\n" + "\n".join(fallback)

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        is_feed = raw.startswith("feed@@")
        parts = raw.split("@@")
        ref_title = ""
        if is_feed:
            aid = parts[1] if len(parts) > 1 else ""
            if len(parts) > 2:
                ref_title = unquote(parts[2])
        elif len(parts) > 1:
            aid = parts[0]
            ref_title = unquote(parts[1])
        else:
            aid = raw
        aid = aid.strip("/")

        target_url = self.host + "/archives/" + aid + "/"
        html = self._fetch(target_url)

        title = ref_title if ref_title else ("热点爆料 " + aid)
        m_h1 = H1_RE.search(html)
        if m_h1:
            title = clean_title(m_h1.group(1))

        desc = ""
        m_desc = DESC_RE.search(html)
        if m_desc:
            desc = m_desc.group(1).strip()

        cover = ""
        m_cover = DATA_BANNER_RE.search(html)
        if m_cover and m_cover.group(1) and "img-placeholder" not in m_cover.group(1):
            cover = m_cover.group(1).strip()
        if not cover:
            m_cover = BANNER_FN_RE.search(html)
            if m_cover and m_cover.group(1) and "img-placeholder" not in m_cover.group(1):
                cover = m_cover.group(1).strip()
        if not cover:
            m_cover = OG_IMAGE_RE.search(html)
            if m_cover and m_cover.group(1) and "img-placeholder" not in m_cover.group(1):
                cover = m_cover.group(1).strip()
        poster = self._format_poster(cover) if cover else ""

        if is_feed:
            return {"list": [self._feed_detail(aid, title, desc, poster)]}
        return {"list": [self._normal_detail(aid, title, desc, poster, html)]}

    def _feed_detail(self, aid, title, desc, poster):
        episodes = []
        first_name = ("01 · " + title).replace("$", "_").replace("#", "_")
        episodes.append(first_name + "$" + json.dumps({"aid": aid, "feedFetch": 1}, ensure_ascii=False))

        pool = FEED_POOL[:]
        random.shuffle(pool)
        targets = []
        seen = {aid}
        for sec in pool[:3]:
            r_page = random.randint(1, 3)
            if sec == "root_home":
                url = (self.host + "/page/" + str(r_page) + "/") if r_page > 1 else (self.host + "/")
            else:
                url = (self.host + "/category/" + sec + "/" + str(r_page) + "/") if r_page > 1 else (self.host + "/category/" + sec + "/")
            sample_html = self._fetch(url)
            if sample_html:
                for card in self._parse_card_list(sample_html, False):
                    card_aid = card["aid"]
                    if card_aid not in seen and card_aid != "139553":
                        seen.add(card_aid)
                        targets.append({"aid": card_aid, "title": card["title"]})
            if len(targets) >= 70:
                break

        random.shuffle(targets)
        for t in targets:
            seq = len(episodes) + 1
            seq_str = ("0" + str(seq)) if seq < 10 else str(seq)
            name = (seq_str + " · " + t["title"]).replace("$", "_").replace("#", "_")
            episodes.append(name + "$" + json.dumps({"aid": t["aid"], "feedFetch": 1}, ensure_ascii=False))

        vod = {
            "vod_id": "feed@@" + aid,
            "vod_name": "🔥 沉浸连刷·" + title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": "蝴蝶影视 | 连刷流 " + str(len(episodes)) + " 条",
            "vod_content": self._summary(desc, title, "🦋 沉浸连刷专线", aid),
            "vod_play_from": "🦋 沉浸连刷专线",
            "vod_play_url": "#".join(episodes),
        }
        return vod

    def _normal_detail(self, aid, title, desc, poster, html):
        episodes = []
        urls = self._extract_video_urls(html)
        for i, u in enumerate(urls):
            num = i + 1
            name = "片段 " + (("0" + str(num)) if num < 10 else str(num))
            episodes.append({"name": name, "value": json.dumps({"playUrl": u, "aid": aid}, ensure_ascii=False)})

        if not episodes:
            m_content = POST_CONTENT_RE.search(html)
            post_body = m_content.group(1) if m_content else html
            sub_tasks = []
            seen_sub = set()
            for m_sub in SUBLINK_RE.finditer(post_body):
                sub_id = m_sub.group(1).strip()
                if sub_id == aid or sub_id in seen_sub or sub_id == "139553":
                    continue
                seen_sub.add(sub_id)
                sub_raw = strip_tags(m_sub.group(2))
                if sub_raw:
                    label = LABEL_STRIP_RE.sub("", sub_raw)[:22].strip()
                else:
                    nxt = len(sub_tasks) + 1
                    label = "TOP " + (("0" + str(nxt)) if len(sub_tasks) < 9 else str(nxt))
                sub_tasks.append({"id": sub_id, "label": label})
                if len(sub_tasks) >= 12:
                    break
            for task in sub_tasks:
                sub_html = self._fetch(self.host + "/archives/" + task["id"] + "/")
                if sub_html:
                    sub_urls = self._extract_video_urls(sub_html)
                    for vi, su in enumerate(sub_urls):
                        if len(sub_urls) == 1:
                            ep_label = task["label"]
                        else:
                            ep_label = task["label"] + "·片段" + str(vi + 1)
                        episodes.append({"name": ep_label, "value": json.dumps({"playUrl": su, "aid": task["id"]}, ensure_ascii=False)})

        main_strs = []
        backup_strs = []
        for ep in episodes:
            ep_name = ep["name"].replace("$", "_").replace("#", "_")
            main_strs.append(ep_name + "$" + ep["value"])
            data = json.loads(ep["value"])
            http_url = re.sub(r"^https://", "http://", str(data.get("playUrl") or ""), flags=re.I)
            backup_strs.append(ep_name + "$" + json.dumps({"playUrl": http_url, "aid": data.get("aid") or aid}, ensure_ascii=False))

        remarks = ("蝴蝶影视 | 共" + str(len(episodes)) + "个片段") if len(episodes) > 1 else "蝴蝶影视 | 正片实录"
        vod = {
            "vod_id": aid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": remarks,
            "vod_content": self._summary(desc, title, "🦋 蝴蝶专线", aid),
            "vod_play_from": "🦋 蝴蝶专线$$$⚡ 备用线路 (HTTP)" if episodes else "",
            "vod_play_url": "#".join(main_strs) + "$$$" + "#".join(backup_strs) if episodes else "",
        }
        return vod

    # ---------- player ----------

    def playerContent(self, flag, pid, vipFlags):
        headers = {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Origin": self.host,
        }
        data = None
        try:
            parsed = json.loads(pid)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = None

        if data is not None and data.get("playUrl"):
            return {"parse": 0, "url": str(data["playUrl"]), "header": headers}

        if data is not None and data.get("feedFetch"):
            aid = str(data.get("aid") or "")
            page_html = self._fetch(self.host + "/archives/" + aid + "/")
            urls = self._extract_video_urls(page_html)
            if urls:
                return {"parse": 0, "url": urls[0], "header": headers}
            for m_sub in SUBLINK_SIMPLE_RE.finditer(page_html):
                next_aid = m_sub.group(1)
                if next_aid != aid and next_aid != "139553":
                    sub_html = self._fetch(self.host + "/archives/" + next_aid + "/")
                    sub_urls = self._extract_video_urls(sub_html)
                    if sub_urls:
                        return {"parse": 0, "url": sub_urls[0], "header": headers}
            return {"parse": 1, "url": self.host + "/archives/" + aid + "/", "header": headers}

        if isinstance(pid, str) and pid.startswith("http"):
            return {"parse": 0, "url": pid, "header": headers}

        return {"parse": 1, "url": self.host + "/", "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249475856&sig=cff0353dc1519d41
