# -*- coding: utf-8 -*-
# 911爆料 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.baoliao911)
import json
import random
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://blw66.com"
DEFAULT_PIC_CDN = "https://pic.hdhwqx.cn"
DEFAULT_IMG_WORKER = "https://chigua-img-proxy.yishengheqiu7679.workers.dev"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND_NAME = "911爆料"
PAGE_SIZE = 15
AD_HASH = "8336b0b0b849e19984729790e6d2a7a0"

CATEGORIES = [
    ("feed_stream", "🔥 沉浸连刷"),
    ("root_home", "全部最新"),
    ("jrgb", "今日大瓜"),
    ("aidj", "AI短剧"),
    ("mrds", "每日大赛"),
    ("ssdbl", "热点吃瓜"),
    ("blqw", "猎奇吃瓜"),
    ("hjsq", "海角社区"),
    ("crfys", "午夜剧场"),
    ("thjx", "探花经典"),
    ("fljq", "福利视频"),
    ("dmhv", "动漫天堂"),
    ("crlz", "网黄专辑"),
    ("bgzq", "反差爆料"),
    ("tksm", "偷窥泄密"),
    ("rmgb", "独家爆料"),
    ("xyss", "校园吃瓜"),
    ("whbl", "网红黑料"),
    ("zksr", "SM专区"),
    ("slec", "影视床戏"),
    ("sgpjs", "水果派解说"),
    ("rlph", "黑料排行"),
    ("mxhl", "明星吃瓜"),
    ("kpzj", "看片专辑"),
    ("ntll", "男男女女"),
    ("mjmsjb", "世界杯黑料"),
    ("zqbb", "世界杯宝贝"),
]

FEED_POOL = ["jrgb", "mrds", "ssdbl", "blqw", "hjsq", "thjx", "rmgb", "whbl", "root_home"]

AD_KEYWORDS = [
    "重金求稿", "变现", "高价收购", "商务合作", "吃瓜导航", "我要投稿",
    "关于我们", "嫩模空降", "回家地址", "我要爆料", "赚钱福利", "加入我们",
    "使用帮助", "了解黑料", "用户协议", "隐私政策", "18 USC", "USC2257",
    "我要求瓜", "原创招募", "招募详情", "免责声明", "联系我们", "官方信息",
    "联系官方", "回家路", "常见问题", "现金红包", "APP下载", "发布页", "导航", "红包",
    "消息中心", "防走丢", "永久域名", "優先投放區", "优先投放",
]
TITLE_JUNK = ("loadBannerDirect", "post-card")

ASIDE_RE = re.compile(r"<aside[\s\S]*?</aside>", re.I)
FOOTER_RE = re.compile(r"<footer[\s\S]*?</footer>", re.I)
HEADER_RE = re.compile(r"<header[\s\S]*?</header>", re.I)
NAV_RE = re.compile(r"<nav[\s\S]*?</nav>", re.I)
BANNER_MAP_RE = re.compile(r"loadBannerDirect\(['\"]([^'\"]+)['\"]\s*,\s*['\"][^'\"]*['\"]\s*,\s*document\.querySelector\(['\"]#post-card-(\d+)['\"]\)")
CARD_START_RE = re.compile(r'<div[^>]+id=["\']post-card-(\d+)["\']', re.I)
H2_CARD_TITLE_RE = re.compile(r'<h2[^>]*class=["\'][^"\']*post-card-title[^"\']*["\'][^>]*>([\s\S]*?)</h2>', re.I)
H_HEADLINE_RE = re.compile(r'<h[1-6][^>]*itemprop=["\']headline["\'][^>]*>([\s\S]*?)</h[1-6]>', re.I)
H2_ANY_RE = re.compile(r"<h2[^>]*>([\s\S]*?)</h2>", re.I)
DIV_STRIP_RE = re.compile(r"<div[\s\S]*?</div>", re.I)
DATE_ITEMPROP_RE = re.compile(r'itemprop=["\']datePublished["\'][^>]+content=["\'](\d{4}-\d{2}-\d{2})', re.I)
DATE_MIX_RE = re.compile(r"(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})")
DATE_DASH_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
BANNER_FN_RE = re.compile(r"loadBannerDirect\s*\(\s*['\"]([^'\"]+)['\"]")
QUOTED_IMG_RE = re.compile(r'[\"\'](https?://[^"\'\s<>]+\.(?:jpe?g|png|webp)[^"\'\s<>]*)[\"\']', re.I)
BG_URL_RE = re.compile(r'background(?:-image)?\s*:\s*url\((["\']?)([^"\')]+)\1\)', re.I)
ARTICLE_VIDEOS_RE = re.compile(r'id=["\']article-videos["\'][^>]+data-url=(["\'])([\s\S]*?)\1', re.I)
DATA_URL_RE = re.compile(r'data-url=(["\'])([\s\S]*?)\1', re.I)
URL_SCAN_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
DATACONFIG_RE = re.compile(r"data-config=([\"'])([\s\S]*?)\1")
CFG_URL_RE = re.compile(r'["\']url["\']\s*:\s*["\']([^"\']+)["\']', re.I)
CFG_VIDEO_URL_RE = re.compile(r'["\']video["\']\s*:\s*\{[^}]*?["\']url["\']\s*:\s*["\']([^"\']+)["\']', re.I)
VIDEO_TAG_RE = re.compile(r"<video[^>]+>", re.I)
VIDEO_SRC_RE = re.compile(r'(?:data-hls-src|data-src|src)=["\']([^"\']+)["\']', re.I)
QUOTED_STREAM_RE = re.compile(r'[\"\'](https?:[\\/]+[^"\'\s]+\.(?:m3u8|mp4)[^"\'\s]*)[\"\']', re.I)
FINGERPRINT_RE = re.compile(r"(?:\.cn|\.cc|\.com|\.net|\.org|\.vip)(?::\d+)?(/[^?#]+)", re.I)
H1_POST_TITLE_RE = re.compile(r'<h1[^>]*class=["\'][^"\']*post-title[^"\']*["\'][^>]*>([\s\S]*?)</h1>', re.I)
H1_RE = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
OG_TITLE_RE = re.compile(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']*)["\']', re.I)
TITLE_TAG_RE = re.compile(r"<title>([\s\S]*?)(?:-|\||_)", re.I)
DESC_RE = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', re.I)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']*)["\']', re.I)
POST_BODY_RE = re.compile(r'<div[^>]+class=["\'][^"\']*(?:post-content|entry-content|article-content)[^"\']*["\'][^>]*>([\s\S]*?)(?:<div[^>]+class=["\'][^"\']*(?:post-footer|post-tags|comments)["\']|</article>)', re.I)
SUBLINK_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/(\d+)/?(?:\.html)?["\'][^>]*>([\s\S]*?)</a>', re.I)
SUBLINK_SIMPLE_RE = re.compile(r'<a[^>]+href=["\'](?:https?://[^/]+)?/archives/(\d+)/?(?:\.html)?["\'][^>]*>', re.I)
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
CRLF_TAB_RE = re.compile(r"[\r\n\t]+")
LEAD_JUNK_RE = re.compile(r"^[^<]*?>")
LEAD_CLASS_RE = re.compile(r'^class=["\'][^"\']*["\']\s*>?', re.I)
TRAILING_JUNK_RE = re.compile(r"[\s\]\}]+$")
NOISE_RES = [
    re.compile(r"热搜\s*HOT", re.I),
    re.compile(r"HOT", re.I),
    re.compile(r"置顶", re.I),
    re.compile(r"独家", re.I),
    re.compile(r"NEW", re.I),
    re.compile(r"吃瓜\s*HOT", re.I),
    re.compile(r"爆料\s*HOT", re.I),
    re.compile(r"^热\s*", re.I),
    re.compile(r"^置顶\s*", re.I),
]


# ---------- text helpers ----------

def clean_title(raw):
    if not raw:
        return ""
    t = TAG_RE.sub("", str(raw))
    t = t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    t = t.replace("&quot;", '"').replace("&#39;", "'")
    t = CRLF_TAB_RE.sub(" ", t)
    t = WS_RE.sub(" ", t).strip()
    for noise in NOISE_RES:
        t = noise.sub("", t)
    return t.strip()


def clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw)
    clean = clean.replace("\\u0068ttps", "https").replace("\\u0068ttp", "http")
    clean = clean.replace("\\/", "/")
    clean = clean.replace("&quot;", "").replace("'", "").replace('"', "")
    clean = clean.strip()
    clean = TRAILING_JUNK_RE.sub("", clean)
    if clean.startswith("//"):
        clean = "https:" + clean
    return clean


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

    def _fetch_once(self, url, referer=None):
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=8)
        if resp is not None and resp.text:
            return resp.text
        return ""

    def _fetch(self, url, referer=None):
        target = url
        if target.startswith("//"):
            target = "https:" + target
        elif target.startswith("/"):
            target = self.host + target
        try:
            body = self._fetch_once(target, referer)
            if body:
                return body
        except Exception:
            if target.startswith("https://"):
                try:
                    return self._fetch_once("http://" + target[8:], referer)
                except Exception:
                    return ""
        return ""

    def _fetch_archives(self, aid, referer=None):
        html = self._fetch(self.host + "/archives/" + aid + "/", referer)
        if not html:
            html = self._fetch(self.host + "/archives/" + aid + ".html", referer)
        return html

    # ---------- poster ----------

    def _format_img_url(self, raw_pic):
        if not raw_pic:
            return ""
        p = str(raw_pic).strip()
        if p[:1] in ("'", '"'):
            p = p[1:]
        if p[-1:] in ("'", '"'):
            p = p[:-1]
        if p.startswith("//"):
            clean = "https:" + p
        elif p.startswith("http://") or p.startswith("https://"):
            clean = p
        elif p.startswith("/upload") or p.startswith("upload") or p.startswith("/image") or p.startswith("image") or p.startswith("/hc") or p.startswith("hc"):
            if not p.startswith("/"):
                p = "/" + p
            clean = DEFAULT_PIC_CDN + p
        elif p.startswith("/"):
            clean = self.host + p
        else:
            clean = p
        return self.img_worker + "?url=" + quote(clean, safe="")

    def _card_pic(self, block, banner_map, aid):
        if aid and banner_map.get(aid):
            return banner_map[aid]
        m = BANNER_FN_RE.search(block)
        if m and m.group(1) and "home-cover-placeholder" not in m.group(1):
            return m.group(1).strip()
        for m_img in QUOTED_IMG_RE.finditer(block):
            cand = m_img.group(1).strip()
            low = cand.lower()
            if "logo" not in low and "avatar" not in low and "placeholder" not in low:
                return cand
        return ""

    # ---------- card list (post-card id driven) ----------

    def _parse_cards(self, html_text, is_feed):
        items = []
        seen = set()
        clean = ASIDE_RE.sub("", str(html_text or ""))
        clean = FOOTER_RE.sub("", clean)
        clean = HEADER_RE.sub("", clean)
        clean = NAV_RE.sub("", clean)
        banner_map = {}
        for m in BANNER_MAP_RE.finditer(clean):
            if "home-cover-placeholder" not in m.group(1):
                banner_map[m.group(2)] = m.group(1)
        for m in CARD_START_RE.finditer(clean):
            aid = m.group(1).strip()
            if aid in seen or aid == "139553":
                continue
            block = clean[m.start():m.start() + 3000]
            title = ""
            m_title = H2_CARD_TITLE_RE.search(block) or H_HEADLINE_RE.search(block) or H2_ANY_RE.search(block)
            if m_title:
                inner = DIV_STRIP_RE.sub("", m_title.group(1))
                title = clean_title(inner)
            if not title or len(title) < 4:
                continue
            if any(word in title for word in AD_KEYWORDS):
                continue
            if any(junk in title for junk in TITLE_JUNK):
                continue
            pic = self._card_pic(block, banner_map, aid)
            post_date = ""
            m_dt = DATE_ITEMPROP_RE.search(block)
            if m_dt:
                post_date = m_dt.group(1).strip()
            else:
                m_mix = DATE_MIX_RE.search(block)
                if m_mix:
                    post_date = m_mix.group(1).replace("年", "-").replace("月", "-")
                    if post_date.endswith("日"):
                        post_date = post_date[:-1]
                    post_date = post_date.strip()
            seen.add(aid)
            if is_feed:
                remarks = "蝴蝶影视 | 连刷起播"
                vod_id = "feed@@" + aid + "@@" + quote(title, safe="")
            else:
                remarks = "蝴蝶影视 | " + (post_date if post_date else "现场实录")
                vod_id = aid + "@@" + quote(title, safe="")
            items.append({
                "aid": aid,
                "title": title,
                "vod": {
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": self._format_img_url(pic),
                    "vod_remarks": remarks,
                    "style": {"type": "rect", "ratio": 1.78},
                },
            })
        return items

    # ---------- stream extraction ----------

    def _extract_streams(self, html_content):
        html_content = html_content or ""
        raw_candidates = []

        m_cont = ARTICLE_VIDEOS_RE.search(html_content) or DATA_URL_RE.search(html_content)
        if m_cont:
            raw_val = m_cont.group(2).strip().replace("&quot;", '"')
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

        if not raw_candidates:
            for m in DATACONFIG_RE.finditer(html_content):
                raw_cfg = m.group(2).replace("&quot;", '"')
                try:
                    cfg = json.loads(raw_cfg)
                    if isinstance(cfg, dict):
                        video = cfg.get("video")
                        if isinstance(video, dict) and video.get("url"):
                            raw_candidates.append(video.get("url"))
                except Exception:
                    m_url = CFG_VIDEO_URL_RE.search(raw_cfg)
                    if m_url:
                        raw_candidates.append(m_url.group(1))

        if not raw_candidates:
            for m in VIDEO_TAG_RE.finditer(html_content):
                m_src = VIDEO_SRC_RE.search(m.group(0))
                if m_src:
                    raw_candidates.append(m_src.group(1))

        if not raw_candidates:
            for m in QUOTED_STREAM_RE.finditer(html_content):
                raw_candidates.append(m.group(1))

        pool = []
        seen_fp = set()
        for cand in raw_candidates:
            c = clean_stream_url(cand)
            if not c or "logo" in c.lower() or len(c) > 300:
                continue
            if AD_HASH in c:
                continue
            low_c = c.lower()
            if "sample" in low_c or "preview" in low_c or "trailer" in low_c:
                continue
            m_fp = FINGERPRINT_RE.search(c)
            if m_fp:
                fingerprint = m_fp.group(1).lower()
            else:
                fingerprint = c.split("?")[0].lower()
            if fingerprint in seen_fp:
                continue
            seen_fp.add(fingerprint)
            pool.append(c)
        return pool

    def _extract_page_title(self, html, default_name):
        if not html:
            return default_name
        m = H1_POST_TITLE_RE.search(html) or H1_RE.search(html) or OG_TITLE_RE.search(html) or TITLE_TAG_RE.search(html)
        if m and m.group(1):
            t = clean_title(m.group(1))
            if t and len(t) >= 2 and "点击查看完整爆料" not in t:
                return t
        return default_name

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        html = self._fetch(self.host + "/")
        items = self._parse_cards(html, False)[:18]
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
        if is_feed or cid == "root_home":
            if page > 1:
                urls = [self.host + "/" + str(page) + "/",
                        self.host + "/page/" + str(page) + "/"]
            else:
                urls = [self.host + "/"]
        else:
            if page > 1:
                urls = [self.host + "/category/" + cid + "/" + str(page) + "/",
                        self.host + "/" + cid + "/" + str(page) + "/"]
            else:
                urls = [self.host + "/category/" + cid + "/",
                        self.host + "/" + cid + "/"]
        items = []
        for url in urls:
            html = self._fetch(url)
            if html:
                items = self._parse_cards(html, is_feed)
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
        enc = quote(keyword, safe="")
        url = (self.host + "/search/" + enc + "/" + str(page) + "/") if page > 1 else (self.host + "/search/" + enc + "/")
        html = self._fetch(url)
        items = self._parse_cards(html, False)
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
        if aid.lower().endswith(".html"):
            aid = aid[:-5]
        if not aid:
            return {"list": []}

        detail_url = self.host + "/archives/" + aid + "/"
        html = self._fetch(detail_url)
        if not html:
            detail_url = self.host + "/archives/" + aid + ".html"
            html = self._fetch(detail_url)

        title = ref_title
        if not title:
            title = self._extract_page_title(html, "热点爆料 " + aid)

        desc = ""
        m_desc = DESC_RE.search(html)
        if m_desc:
            desc = m_desc.group(1).strip()

        cover = ""
        banner_aid_re = re.compile(r"loadBannerDirect\(['\"]([^'\"]+)['\"]\s*,\s*['\"][^'\"]*['\"]\s*,\s*document\.querySelector\(['\"]#post-card-" + re.escape(aid) + r"['\"]\)")
        m_banner = banner_aid_re.search(html)
        if m_banner and "home-cover-placeholder" not in m_banner.group(1):
            cover = m_banner.group(1).strip()
        if not cover:
            m_dir = BANNER_FN_RE.search(html)
            if m_dir and "home-cover-placeholder" not in m_dir.group(1):
                cover = m_dir.group(1).strip()
        if not cover:
            m_pic = OG_IMAGE_RE.search(html)
            if m_pic and "placeholder" not in m_pic.group(1):
                cover = m_pic.group(1).strip()
        poster = self._format_img_url(cover) if cover else ""

        if is_feed:
            return {"list": [self._feed_detail(aid, title, desc, poster)]}
        return {"list": [self._normal_detail(aid, title, desc, poster, html, detail_url)]}

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
                url = (self.host + "/" + str(r_page) + "/") if r_page > 1 else (self.host + "/")
            else:
                url = (self.host + "/category/" + sec + "/" + str(r_page) + "/") if r_page > 1 else (self.host + "/category/" + sec + "/")
            sample_html = self._fetch(url)
            if sample_html:
                for card in self._parse_cards(sample_html, False):
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

    def _normal_detail(self, aid, title, desc, poster, html, detail_url):
        episodes = []
        streams = self._extract_streams(html)
        for i, u in enumerate(streams):
            num = i + 1
            name = "正片 " + (("0" + str(num)) if num <= 9 else str(num))
            name = name.replace("$", "_").replace("#", "_")
            episodes.append({"name": name, "value": json.dumps({"mediaUrl": u, "aid": aid}, ensure_ascii=False)})

        if not episodes:
            m_body = POST_BODY_RE.search(html)
            post_body = m_body.group(1) if m_body else html
            sub_tasks = []
            seen_sub = set()
            for m_sub in SUBLINK_RE.finditer(post_body):
                sub_id = m_sub.group(1).strip()
                if not sub_id or sub_id == aid or sub_id in seen_sub or sub_id == "139553":
                    continue
                seen_sub.add(sub_id)
                label = clean_title(m_sub.group(2))
                if not label or label == "点击查看完整爆料":
                    label = "瓜圈正片 " + sub_id
                sub_tasks.append({"id": sub_id, "label": label})
                if len(sub_tasks) >= 25:
                    break
            for task in sub_tasks:
                try:
                    sub_html = self._fetch_archives(task["id"], referer=detail_url)
                    if sub_html:
                        real_title = self._extract_page_title(sub_html, task["label"])
                        sub_streams = self._extract_streams(sub_html)
                        for si, su in enumerate(sub_streams):
                            ep_title = real_title
                            if len(sub_streams) > 1:
                                ep_title = ep_title + " P" + str(si + 1)
                            ep_title = ep_title.replace("$", "_").replace("#", "_")
                            episodes.append({"name": ep_title, "value": json.dumps({"mediaUrl": su, "aid": task["id"]}, ensure_ascii=False)})
                except Exception:
                    pass

        ep_strs = [ep["name"] + "$" + ep["value"] for ep in episodes]
        remarks = ("蝴蝶影视 | 共" + str(len(episodes)) + "段") if episodes else "蝴蝶影视 | 现场实录"
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
            "vod_play_from": "🦋 蝴蝶专线" if episodes else "",
            "vod_play_url": "#".join(ep_strs),
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

        if data is not None and data.get("feedFetch"):
            aid = str(data.get("aid") or "")
            page_html = self._fetch_archives(aid)
            if page_html:
                streams = self._extract_streams(page_html)
                if streams:
                    return {"parse": 0, "url": streams[0], "header": headers}
                for m_sub in SUBLINK_SIMPLE_RE.finditer(page_html):
                    next_aid = m_sub.group(1)
                    if next_aid != aid and next_aid != "139553":
                        sub_html = self._fetch(self.host + "/archives/" + next_aid + "/")
                        if sub_html:
                            sub_streams = self._extract_streams(sub_html)
                            if sub_streams:
                                return {"parse": 0, "url": sub_streams[0], "header": headers}
            return {"parse": 1, "url": self.host + "/archives/" + aid + "/", "header": headers}

        if data is not None and data.get("mediaUrl"):
            return {"parse": 0, "url": str(data["mediaUrl"]), "header": headers}

        if isinstance(pid, str) and pid.startswith("http"):
            return {"parse": 0, "url": pid, "header": headers}

        return {"parse": 1, "url": self.host + "/", "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249431877&sig=95b19aba1db76513
