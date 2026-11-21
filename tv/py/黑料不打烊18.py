# -*- coding: utf-8 -*-
# 黑料不打烊 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.hlbdy)
import json
import random
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://hl365.com"
DEFAULT_PIC_CDN = "https://pic.hdhwqx.cn"
DEFAULT_IMG_WORKER = "https://chigua-img-proxy.yishengheqiu7679.workers.dev"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND_NAME = "黑料不打烊"
PAGE_SIZE = 30
AD_HASH = "8336b0b0b849e19984729790e6d2a7a0"

CATEGORIES = [
    ("feed_stream", "🔥 沉浸连刷"),
    ("root_home", "全部最新"),
    ("24hcg", "今日看料"),
    ("mrds", "每日大赛"),
    ("swdj", "AI短剧"),
    ("mrrg", "每日热瓜"),
    ("hlda", "黑料大事"),
    ("rgtj", "热门吃瓜"),
    ("fcns", "反差女神"),
    ("xyrg", "学院热瓜"),
    ("whhl", "网红吃瓜"),
    ("lydt", "撸友看片"),
    ("llsq", "海角乱伦"),
    ("hlzt", "黑料杂谈"),
    ("thdq", "探花大全"),
    ("whzj", "网黄专辑"),
    ("mxbg", "明星吃瓜"),
    ("avjs", "av解说"),
    ("qgzq", "原创投稿"),
    ("wyxs", "性爱技巧"),
    ("chjlb", "偷拍盗摄"),
    ("gcmw", "官场秘闻"),
    ("mrst", "禁播动漫"),
    ("pmv", "PMV混剪"),
]

FEED_POOL = ["24hcg", "mrds", "swdj", "mrrg", "hlda", "rgtj", "fcns", "xyrg", "whhl", "root_home"]

STRICT_AD_KEYWORDS = [
    "重金求稿", "变现", "高价收购", "商务合作", "吃瓜导航", "我要投稿", "关于我们", "嫩模空降",
    "博业体育", "欧洲五大联赛", "澳门威尼斯", "威尼斯人", "官方指定投注", "约炮", "成人直播",
]
BLOCK_SKIP = ("post-card-ads", "ad-card", "ad-item", "tjtagmanager")
PIC_ATTRS = ("z-bg-loader-url", "x-bg-loader-url", "z-image-loader-url", "data-banner", "data-src", "data-original", "data-bg", "data-thumb")
DETAIL_PIC_ATTRS = ("z-bg-loader-url", "x-bg-loader-url", "z-image-loader-url", "data-banner", "data-src", "data-original")

BANNER_MAP_RE = re.compile(r"loadBannerDirect\(['\"]([^'\"]+)['\"]\s*,\s*['\"][^'\"]*['\"]\s*,\s*document\.querySelector\(['\"]#post-card-(\d+)['\"]\)", re.I)
ASIDE_RE = re.compile(r"<aside[\s\S]*?</aside>", re.I)
WIDGET_RE = re.compile(r'<div[^>]+class=["\'][^"\']*(?:widget|sidebar)[^"\']*["\'][\s\S]*?</div>', re.I)
POSTCARD_RE = re.compile(r'<div[^>]+class=["\'][^"\']*post-card[^"\']*["\'][^>]*>[\s\S]*?</div>\s*</div>', re.I)
ARTICLE_RE = re.compile(r"<article[^>]*>[\s\S]*?</article>", re.I)
ANCHOR_BLOCK_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/\d+(?:\.html|/?)["\'][^>]*>[\s\S]*?</a>', re.I)
AID_HTML_RE = re.compile(r"/archives/(\d+)\.html")
AID_CARD_RE = re.compile(r'id=["\']post-card-(\d+)["\']', re.I)
AID_PLAIN_RE = re.compile(r"/archives/(\d+)/?")
HEADLINE_RE = re.compile(r'itemprop=["\'](?:headline|name)["\'][^>]*>([\s\S]*?)</[^>]+>', re.I)
H_POST_TITLE_RE = re.compile(r'<h[234][^>]*class=["\'][^"\']*post-title[^"\']*["\'][^>]*>([\s\S]*?)</h[234]>', re.I)
H_CARD_TITLE_RE = re.compile(r'<h[234][^>]*class=["\'][^"\']*post-card-title[^"\']*["\'][^>]*>([\s\S]*?)</h[234]>', re.I)
H_ANY_RE = re.compile(r"<h[234][^>]*>([\s\S]*?)</h[234]>", re.I)
H_SPLIT_RE = re.compile(r"<div|<span|<p", re.I)
A_TITLE_TAG_RE = re.compile(r'<a[^>]+title=["\']([^"\']+)["\']', re.I)
TITLE_SUFFIX_RE = re.compile(r"\s*(?:热搜\s*HOT|HOT|置顶|独家|NEW|吃瓜\s*HOT|爆料\s*HOT)\s*$", re.I)
DATE_ITEMPROP_RE = re.compile(r'itemprop=["\']datePublished["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2})')
DATE_CN_RE = re.compile(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)")
DATE_DASH_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
BANNER_FN_RE = re.compile(r"loadBannerDirect\s*\(\s*['\"]([^'\"]+)['\"]")
LOADIMG_FN_RE = re.compile(r"loadImage\s*\(\s*['\"]([^'\"]+)['\"]")
BG_URL_RE = re.compile(r'style=["\'][^"\']*background(?:-image)?\s*:\s*url\((["\']?)([^"\')]+)\1\)', re.I)
IMG_TAG_RE = re.compile(r"<img[^>]+(?:src|data-src)=[\"']([^\"']+)[\"']", re.I)
IMG_VAL_RE = re.compile(r"(?:src|data-src)=[\"']([^\"']+)[\"']", re.I)
ARTICLE_VIDEOS_RE = re.compile(r'id=["\']article-videos["\'][^>]+data-url=(["\'])([\s\S]*?)\1', re.I)
DATA_URL_RE = re.compile(r'data-url=(["\'])([\s\S]*?)\1', re.I)
URL_SCAN_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
DATACONFIG_RE = re.compile(r"data-config=([\"'])([\s\S]*?)\1", re.I)
CFG_URL_RE = re.compile(r'["\']url["\']\s*:\s*["\']([^"\']+)["\']')
VIDEO_TAG_RE = re.compile(r"<video[^>]+>", re.I)
VIDEO_SRC_RE = re.compile(r'(?:data-hls-src|data-src|src)=["\']([^"\']+)["\']', re.I)
QUOTED_STREAM_RE = re.compile(r'[\"\'](https?:[\\/]+[^"\'\s]+\.(?:m3u8|mp4)[^"\'\s]*)[\"\']', re.I)
H1_POST_TITLE_RE = re.compile(r'<h1[^>]*class=["\'][^"\']*post-title[^"\']*["\'][^>]*>([\s\S]*?)</h1>', re.I)
H1_RE = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
TITLE_TAG_RE = re.compile(r"<title>([\s\S]*?)(?:-|\||_)</title>", re.I)
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']*)["\']', re.I)
POST_CONTENT_RE = re.compile(r'<div[^>]+class=["\'][^"\']*post-content[^"\']*["\'][^>]*>([\s\S]*?)(?:<div[^>]+class=["\'][^"\']*(?:post-footer|post-tags|comments)["\']|</article>)', re.I)
SUBLINK_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/(\d+)(?:\.html|/?)["\'][^>]*>([\s\S]*?)</a>', re.I)
SUBLINK_SIMPLE_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/(\d+)(?:\.html|/?)["\'][^>]*>', re.I)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
CRLF_TAB_RE = re.compile(r"[\r\n\t]+")
TRAILING_JUNK_RE = re.compile(r"[\s\]\}]+$")
LABEL_STRIP_RE = re.compile(r"[$#\r\n\t]")


# ---------- text helpers ----------

def strip_tags_bdy(html):
    if not html:
        return ""
    t = TAG_RE.sub("", str(html))
    t = re.sub(r"&nbsp;", " ", t, flags=re.I)
    return t.strip()


def clean_title_text(raw):
    if not raw:
        return ""
    t = strip_tags_bdy(raw)
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    t = t.replace("&quot;", '"').replace("&#039;", "'").replace("&#39;", "'")
    t = CRLF_TAB_RE.sub(" ", t)
    t = WS_RE.sub(" ", t).strip()
    t = TITLE_SUFFIX_RE.sub("", t)
    return t.strip()


def clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw)
    clean = re.sub(r"\\u0068ttps", "https", clean, flags=re.I)
    clean = re.sub(r"\\u0068ttp", "http", clean, flags=re.I)
    clean = clean.replace("\\/", "/").replace('\\"', '"').replace("\\u0026", "&")
    clean = clean.replace("&quot;", "").replace("'", "").replace('"', "")
    clean = TRAILING_JUNK_RE.sub("", clean)
    clean = clean.strip()
    if clean.startswith("//"):
        clean = "https:" + clean
    return clean


def title_valid(name):
    return bool(name) and len(name) >= 3 and name != "->" and name != "-> ->"


# ---------- spider ----------

class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST
        self.img_worker = DEFAULT_IMG_WORKER

    def getName(self):
        return BRAND_NAME

    def init(self, extend=""):
        host = ""
        worker = ""
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
                        worker = str(data.get("imgWorker") or "")
                except Exception:
                    pass
        elif isinstance(ext, dict):
            host = str(ext.get("host") or "")
            worker = str(ext.get("imgWorker") or "")
        if host.startswith("http"):
            self.host = host.rstrip("/")
        if worker.startswith("http"):
            self.img_worker = worker.rstrip("/")

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

    def _fetch_archives(self, aid):
        html = self._fetch(self.host + "/archives/" + aid + ".html")
        if not html:
            html = self._fetch(self.host + "/archives/" + aid + "/")
        return html

    # ---------- poster ----------

    def _normalize_pic(self, raw_pic):
        if not raw_pic:
            return ""
        p = str(raw_pic).strip()
        if p[:1] in ("'", '"'):
            p = p[1:]
        if p[-1:] in ("'", '"'):
            p = p[:-1]
        if p.startswith("//"):
            return "https:" + p
        if p.startswith("http://") or p.startswith("https://"):
            return p
        if p.startswith("/upload") or p.startswith("upload") or p.startswith("/image") or p.startswith("image") or p.startswith("/hc") or p.startswith("hc"):
            if not p.startswith("/"):
                p = "/" + p
            return DEFAULT_PIC_CDN + p
        if p.startswith("/"):
            return self.host + p
        return p

    def _wrap_pic(self, raw_pic):
        clean = self._normalize_pic(raw_pic)
        if not clean:
            return ""
        if self.img_worker:
            return self.img_worker + "/?url=" + quote(clean, safe="")
        return clean

    def _extract_card_pic(self, block, banner_map, aid):
        if aid and banner_map.get(aid):
            return banner_map[aid]
        m = BANNER_FN_RE.search(block)
        if m and m.group(1) and "img-placeholder" not in m.group(1):
            return m.group(1).strip()
        m = LOADIMG_FN_RE.search(block)
        if m and m.group(1) and "img-placeholder" not in m.group(1):
            return m.group(1).strip()
        for attr in PIC_ATTRS:
            m = re.search(attr + r'=["\']([^"\']+)["\']', block, re.I)
            if m and m.group(1):
                cand = m.group(1).strip()
                if cand and "img-placeholder" not in cand and "logo" not in cand.lower() and not cand.endswith(".svg"):
                    return cand
        m = BG_URL_RE.search(block)
        if m and m.group(2) and "img-placeholder" not in m.group(2):
            return m.group(2).strip()
        for tag_m in IMG_TAG_RE.finditer(block):
            vm = IMG_VAL_RE.search(tag_m.group(0))
            if vm and vm.group(1):
                c_img = vm.group(1).strip()
                low = c_img.lower()
                if not c_img.endswith(".svg") and "logo" not in low and "avatar" not in low and "placeholder" not in low:
                    return c_img
        return ""

    # ---------- card list ----------

    def _parse_card_list(self, html_text, is_feed):
        items = []
        seen = set()
        raw_html = str(html_text or "")
        banner_map = {}
        for m in BANNER_MAP_RE.finditer(raw_html):
            banner_map[m.group(2)] = m.group(1)
        clean = ASIDE_RE.sub("", raw_html)
        clean = WIDGET_RE.sub("", clean)
        blocks = [m.group(0) for m in POSTCARD_RE.finditer(clean)]
        if not blocks:
            blocks = [m.group(0) for m in ARTICLE_RE.finditer(clean)]
        if not blocks:
            blocks = [m.group(0) for m in ANCHOR_BLOCK_RE.finditer(clean)]
        for inner in blocks:
            if any(mark in inner for mark in BLOCK_SKIP):
                continue
            m_id = AID_HTML_RE.search(inner) or AID_CARD_RE.search(inner) or AID_PLAIN_RE.search(inner)
            if not m_id:
                continue
            aid = m_id.group(1).strip()
            if aid in seen or aid == "139553":
                continue
            name = ""
            m_head = HEADLINE_RE.search(inner)
            if m_head:
                name = clean_title_text(m_head.group(1))
            if not title_valid(name):
                m_h = H_POST_TITLE_RE.search(inner) or H_CARD_TITLE_RE.search(inner) or H_ANY_RE.search(inner)
                if m_h:
                    raw_part = H_SPLIT_RE.split(m_h.group(1))[0]
                    cand = clean_title_text(raw_part)
                    if title_valid(cand):
                        name = cand
            if not title_valid(name):
                for tag_m in A_TITLE_TAG_RE.finditer(inner):
                    cand_attr = clean_title_text(tag_m.group(1))
                    if title_valid(cand_attr):
                        name = cand_attr
                        break
            if not name or name == "->" or name == "-> ->":
                name = "热点爆料 " + aid
            if any(word in name for word in STRICT_AD_KEYWORDS):
                continue
            seen.add(aid)
            post_date = ""
            m_date = DATE_ITEMPROP_RE.search(inner) or DATE_CN_RE.search(inner) or DATE_DASH_RE.search(inner)
            if m_date:
                post_date = WS_RE.sub("", m_date.group(1)).strip()
            pic = self._wrap_pic(self._extract_card_pic(inner, banner_map, aid))
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

    # ---------- stream extraction (candidate pool model) ----------

    def _extract_video_urls(self, html_content):
        html_content = html_content or ""
        raw_candidates = []

        m_container = ARTICLE_VIDEOS_RE.search(html_content) or DATA_URL_RE.search(html_content)
        if m_container:
            raw_val = m_container.group(2).strip()
            if raw_val.startswith("["):
                try:
                    arr = json.loads(raw_val)
                    if isinstance(arr, list):
                        for el in arr:
                            if isinstance(el, str):
                                raw_candidates.append(el)
                            elif isinstance(el, (int, float)):
                                raw_candidates.append(str(el))
                except Exception:
                    raw_candidates.extend(URL_SCAN_RE.findall(raw_val))
            elif raw_val:
                raw_candidates.append(raw_val)

        for m in DATACONFIG_RE.finditer(html_content):
            raw_cfg = m.group(2)
            try:
                cfg = json.loads(raw_cfg)
                if isinstance(cfg, dict):
                    video = cfg.get("video")
                    if isinstance(video, dict) and video.get("url"):
                        raw_candidates.append(video.get("url"))
            except Exception:
                m_url = CFG_URL_RE.search(raw_cfg)
                if m_url:
                    raw_candidates.append(m_url.group(1))

        for m in VIDEO_TAG_RE.finditer(html_content):
            m_src = VIDEO_SRC_RE.search(m.group(0))
            if m_src:
                raw_candidates.append(m_src.group(1))

        for m in QUOTED_STREAM_RE.finditer(html_content):
            raw_candidates.append(m.group(1))

        valid_pool = []
        ad_pool = []
        for cand in raw_candidates:
            c = clean_stream_url(cand)
            if not c or "logo" in c.lower() or len(c) > 300:
                continue
            if AD_HASH in c:
                if c not in ad_pool:
                    ad_pool.append(c)
            else:
                if c not in valid_pool:
                    valid_pool.append(c)

        return valid_pool if valid_pool else ad_pool

    def _episodes_from_html(self, html_content, prefix, aid):
        episodes = []
        urls = self._extract_video_urls(html_content)
        for i, u in enumerate(urls):
            num = i + 1
            name = prefix + " " + (("0" + str(num)) if num < 10 else str(num))
            name = name.replace("$", "_").replace("#", "_")
            episodes.append({
                "name": name,
                "value": json.dumps({"playUrl": u, "aid": aid}, ensure_ascii=False),
            })
        return episodes

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        html = self._fetch(self.host + "/")
        items = self._parse_card_list(html, False)[:18]
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
            urls = [(self.host + "/page/" + str(page) + "/")] if page > 1 else [self.host + "/"]
        else:
            if page > 1:
                urls = [self.host + "/category/" + cid + "/" + str(page) + "/",
                        self.host + "/category/" + cid + "/?page=" + str(page)]
            else:
                urls = [self.host + "/category/" + cid + "/",
                        self.host + "/category/" + cid]
        items = []
        for url in urls:
            html = self._fetch(url)
            if html:
                items = self._parse_card_list(html, is_feed)
                if items:
                    break
        if is_feed and items:
            random.shuffle(items)
        return self._page_form([it["vod"] for it in items], page)

    def searchContent(self, key, quick, pg="1"):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        keyword = str(key or "").strip()
        if not keyword:
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
        if aid.endswith(".html"):
            aid = aid[:-5]

        html = self._fetch_archives(aid)

        title = ref_title if ref_title else ("热点爆料 " + aid)
        m_title = H1_POST_TITLE_RE.search(html) or H1_RE.search(html) or TITLE_TAG_RE.search(html)
        if m_title:
            title = clean_title_text(m_title.group(1))

        desc = ""
        m_desc = DESC_RE.search(html)
        if m_desc:
            desc = m_desc.group(1).strip()

        cover = ""
        for attr in DETAIL_PIC_ATTRS:
            m_a = re.search(attr + r'=["\']([^"\']+)["\']', html, re.I)
            if m_a and m_a.group(1) and "img-placeholder" not in m_a.group(1):
                cover = m_a.group(1).strip()
                break
        if not cover:
            m_b = BANNER_FN_RE.search(html)
            if m_b and m_b.group(1) and "img-placeholder" not in m_b.group(1):
                cover = m_b.group(1).strip()
        if not cover:
            m_og = OG_IMAGE_RE.search(html)
            if m_og and m_og.group(1) and "img-placeholder" not in m_og.group(1):
                cover = m_og.group(1).strip()
        poster = self._wrap_pic(cover) if cover else ""

        if is_feed:
            return {"list": [self._feed_detail(aid, title, desc, poster)]}
        return {"list": [self._normal_detail(aid, title, desc, poster, html)]}

    def _feed_detail(self, aid, title, desc, poster):
        episode_strs = []
        first_name = ("01 · " + title).replace("$", "_").replace("#", "_")
        episode_strs.append(first_name + "$" + json.dumps({"aid": aid, "feedFetch": 1}, ensure_ascii=False))

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
            seq = len(episode_strs) + 1
            seq_str = ("0" + str(seq)) if seq < 10 else str(seq)
            name = (seq_str + " · " + t["title"]).replace("$", "_").replace("#", "_")
            episode_strs.append(name + "$" + json.dumps({"aid": t["aid"], "feedFetch": 1}, ensure_ascii=False))

        vod = {
            "vod_id": "feed@@" + aid,
            "vod_name": "🔥 沉浸连刷·" + title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": "蝴蝶影视 | 连刷流 " + str(len(episode_strs)) + " 条",
            "vod_content": self._summary(desc, title, "🦋 沉浸连刷专线", aid),
            "vod_play_from": "🦋 沉浸连刷专线",
            "vod_play_url": "#".join(episode_strs),
        }
        return vod

    def _normal_detail(self, aid, title, desc, poster, html):
        episodes = self._episodes_from_html(html, "正片", aid)

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
                label = LABEL_STRIP_RE.sub("", strip_tags_bdy(m_sub.group(2)))[:22].strip()
                if not label:
                    label = "TOP " + str(len(sub_tasks) + 1)
                sub_tasks.append({"id": sub_id, "label": label})
                if len(sub_tasks) >= 6:
                    break
            for task in sub_tasks:
                sub_html = self._fetch_archives(task["id"])
                if sub_html:
                    sub_eps = self._episodes_from_html(sub_html, task["label"], task["id"])
                    for se in sub_eps:
                        if len(sub_eps) == 1:
                            ep_name = task["label"]
                        else:
                            ep_name = task["label"] + "·" + se["name"]
                        ep_name = ep_name.replace("$", "_").replace("#", "_")
                        episodes.append({"name": ep_name, "value": se["value"]})
                if len(episodes) >= 10:
                    break

        main_strs = []
        backup_strs = []
        for ep in episodes:
            main_strs.append(ep["name"] + "$" + ep["value"])
            data = json.loads(ep["value"])
            http_url = re.sub(r"^https://", "http://", str(data.get("playUrl") or ""), flags=re.I)
            backup_strs.append(ep["name"] + "$" + json.dumps({"playUrl": http_url, "aid": data.get("aid") or aid}, ensure_ascii=False))

        remarks = ("蝴蝶影视 | 共" + str(len(episodes)) + "个片段") if len(episodes) > 1 else "蝴蝶影视 | 现场实录"
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
        }
        data = None
        try:
            parsed = json.loads(pid)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = None

        if data is not None and data.get("feedFetch"):
            aid = str(data.get("aid") or "")
            page_html = self._fetch_archives(aid)
            urls = self._extract_video_urls(page_html)
            if urls:
                return {"parse": 0, "url": clean_stream_url(urls[0]), "header": headers}
            for m_sub in SUBLINK_SIMPLE_RE.finditer(page_html):
                next_aid = m_sub.group(1)
                if next_aid != aid and next_aid != "139553":
                    sub_html = self._fetch_archives(next_aid)
                    sub_urls = self._extract_video_urls(sub_html)
                    if sub_urls:
                        return {"parse": 0, "url": clean_stream_url(sub_urls[0]), "header": headers}
            return {"parse": 1, "url": self.host + "/archives/" + aid + ".html", "header": headers}

        if data is not None and data.get("playUrl"):
            return {"parse": 0, "url": clean_stream_url(str(data["playUrl"])), "header": headers}

        if isinstance(pid, str) and pid.startswith("http"):
            return {"parse": 0, "url": clean_stream_url(pid), "header": headers}

        return {"parse": 1, "url": self.host + "/", "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249640348&sig=e9ac6ffba7f8544d
