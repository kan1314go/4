# -*- coding: utf-8 -*-
# Madou Club - com.butterfly.madou
import re
import json
import html as html_lib
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://madou.club"
DEFAULT_DASH_HOST = "https://dash.madou.club"
SITE_NAME = "麻豆社"
BRAND = "蝴蝶影视"
TG_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
HOT_LINE_NAME = "🔥 大家在看"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
PAGE_SIZE = 20
CARD_RATIO = 1.33

CLASSES = [
    {"type_id": "home", "type_name": "最新推荐"},
    {"type_id": "hot_rank", "type_name": "热门排行"},
    {"type_id": "hot_tags", "type_name": "热门标签"},
    {"type_id": "madou_uni", "type_name": "麻豆宇宙"},
    {"type_id": "top_studios", "type_name": "主流大厂"},
    {"type_id": "indie_studios", "type_name": "独立厂牌"},
    {"type_id": "creator_series", "type_name": "网红企划"},
]

FILTERS = {
    "hot_rank": [
        {
            "key": "rank",
            "name": "榜单类型",
            "init": "likes",
            "value": [
                {"n": "点赞排行", "v": "likes"},
                {"n": "7天热门", "v": "week"},
                {"n": "30天热门", "v": "month"},
            ],
        }
    ],
    "hot_tags": [
        {
            "key": "tag",
            "name": "标签筛选",
            "init": "%e7%99%bd%e8%99%8e",
            "value": [
                {"n": "白虎", "v": "%e7%99%bd%e8%99%8e"},
                {"n": "后入", "v": "%e5%90%8e%e5%85%a5"},
                {"n": "少妇", "v": "%e5%b0%91%e5%a6%87"},
                {"n": "无套", "v": "%e6%97%a0%e5%a5%97"},
                {"n": "口交", "v": "%e5%8f%a3%e4%ba%a4"},
                {"n": "乱伦", "v": "%e4%b9%b1%e4%bc%a6"},
                {"n": "黑丝", "v": "%e9%bb%91%e4%b8%9d"},
                {"n": "痴女", "v": "%e7%97%b4%e5%a5%b3"},
                {"n": "爆乳", "v": "%e7%88%86%e4%b9%b3"},
                {"n": "巨乳", "v": "%e5%b7%a8%e4%b9%b3"},
                {"n": "骑乘位", "v": "%e9%aa%91%e4%b9%98%e4%bd%8d"},
                {"n": "人妻", "v": "%e4%ba%ba%e5%a6%bb"},
                {"n": "美臀", "v": "%e7%be%8e%e8%87%80"},
                {"n": "日本", "v": "%e6%97%a5%e6%9c%ac"},
                {"n": "内射", "v": "%e5%86%85%e5%b0%84"},
                {"n": "制服", "v": "%e5%88%b6%e6%9c%8d"},
                {"n": "丝袜", "v": "%e4%b8%9d%e8%a2%9c"},
                {"n": "御姐", "v": "%e5%be%a1%e5%a7%90"},
                {"n": "美乳", "v": "%e7%be%8e%e4%b9%b3"},
                {"n": "开裆", "v": "%e5%bc%80%e8%a3%86"},
                {"n": "NTR", "v": "ntr"},
                {"n": "约炮", "v": "%e7%ba%a6%e7%82%ae"},
                {"n": "贫乳", "v": "%e8%b4%ab%e4%b9%b3"},
                {"n": "自慰", "v": "%e8%87%aa%e6%85%b0"},
                {"n": "女优", "v": "%e5%a5%b3%e4%bc%98"},
                {"n": "高潮", "v": "%e9%ab%98%e6%bd%ae"},
                {"n": "调教", "v": "%e8%b0%83%e6%95%99"},
                {"n": "企划", "v": "%e4%bc%81%e5%88%92"},
                {"n": "熟女", "v": "%e7%86%9f%e5%a5%b3"},
                {"n": "兄妹", "v": "%e5%85%84%e5%a6%b9"},
                {"n": "反差婊", "v": "%e5%8f%8d%e5%b7%ae%e5%a9%8a"},
                {"n": "创意", "v": "%e5%88%9b%e6%84%8f"},
                {"n": "清纯", "v": "%e6%b8%85%e7%ba%af"},
                {"n": "近亲", "v": "%e8%bf%91%e4%ba%b2"},
                {"n": "美少女", "v": "%e7%be%8e%e5%b0%91%e5%a5%b3"},
                {"n": "OL", "v": "ol"},
                {"n": "3P", "v": "3p"},
                {"n": "白丝", "v": "%e7%99%bd%e4%b8%9d"},
                {"n": "女教师", "v": "%e5%a5%b3%e6%95%99%e5%b8%88"},
                {"n": "姐弟", "v": "%e5%a7%90%e5%bc%9f"},
                {"n": "强奸", "v": "%e5%bc%ba%e5%a5%b8"},
                {"n": "足交", "v": "%e8%b6%b3%e4%ba%a4"},
                {"n": "斑斑", "v": "%e6%96%91%e6%96%91"},
                {"n": "女友", "v": "%e5%a5%b3%e5%8f%8b"},
                {"n": "新人", "v": "%e6%96%b0%e4%ba%ba"},
                {"n": "师生", "v": "%e5%b8%88%e7%94%9f"},
                {"n": "中出", "v": "%e4%b8%ad%e5%87%ba"},
                {"n": "69", "v": "69"},
                {"n": "迷奸", "v": "%e8%bf%b7%e5%a5%b8"},
                {"n": "双马尾", "v": "%e5%8f%8c%e9%a9%ac%e5%b0%be"},
            ],
        }
    ],
    "madou_uni": [
        {
            "key": "sub",
            "name": "系列厂牌",
            "init": "%e9%ba%bb%e8%b1%86%e4%bc%a0%e5%aa%92",
            "value": [
                {"n": "麻豆传媒", "v": "%e9%ba%bb%e8%b1%86%e4%bc%a0%e5%aa%92"},
                {"n": "麻豆番外篇", "v": "%e9%ba%bb%e8%b1%86%e7%95%aa%e5%a4%96%e7%af%87"},
                {"n": "麻豆花絮", "v": "%e9%ba%bb%e8%b1%86%e8%8a%b1%e7%b5%ae"},
                {"n": "麻豆导演系列", "v": "%e9%ba%bb%e8%b1%86%e5%af%bc%e6%bc%94%e7%b3%bb%e5%88%97"},
                {"n": "女优淫娃培训营", "v": "%e5%a5%b3%e4%bc%98%e6%b7%ab%e5%a8%83%e5%9f%b9%e8%ae%ad%e8%90%a5"},
                {"n": "淫欲游戏王", "v": "%e6%b7%ab%e6%ac%b2%e6%b8%b8%e6%88%8f%e7%8e%8b"},
                {"n": "女神羞羞研究所", "v": "%e5%a5%b3%e7%a5%9e%e7%be%9e%e7%be%9e%e7%a0%94%e7%a9%b6%e6%89%80"},
                {"n": "突袭女优家", "v": "%e7%aa%81%e8%a2%ad%e5%a5%b3%e4%bc%98%e5%ae%b6"},
                {"n": "情趣K歌房", "v": "%e6%83%85%e8%b6%a3k%e6%ad%8c%e6%88%bf"},
                {"n": "KISS糖果屋", "v": "kiss%e7%b3%96%e6%9e%9c%e5%b1%8b"},
            ],
        }
    ],
    "top_studios": [
        {
            "key": "sub",
            "name": "系列厂牌",
            "init": "91%e5%88%b6%e7%89%87%e5%8e%82",
            "value": [
                {"n": "91制片厂", "v": "91%e5%88%b6%e7%89%87%e5%8e%82"},
                {"n": "果冻传媒", "v": "%e6%9e%9c%e5%86%bb%e4%bc%a0%e5%aa%92"},
                {"n": "蜜桃影像", "v": "%e8%9c%9c%e6%a1%83%e5%bd%b1%e5%83%8f"},
                {"n": "天美传媒", "v": "%e5%a4%a9%e7%be%8e%e4%bc%a0%e5%aa%92"},
                {"n": "皇家华人", "v": "%e7%9a%87%e5%ae%b6%e5%8d%8e%e4%ba%ba"},
                {"n": "星空无限传媒", "v": "%e6%98%9f%e7%a9%ba%e6%97%a0%e9%99%90%e4%bc%a0%e5%aa%92"},
                {"n": "精东影业", "v": "%e7%b2%be%e4%b8%9c%e5%bd%b1%e4%b8%9a"},
                {"n": "兔子先生", "v": "%e5%85%94%e5%ad%90%e5%85%88%e7%94%9f"},
            ],
        }
    ],
    "indie_studios": [
        {
            "key": "sub",
            "name": "系列厂牌",
            "init": "%e5%a4%a7%e8%b1%a1%e4%bc%a0%e5%aa%92",
            "value": [
                {"n": "大象传媒", "v": "%e5%a4%a7%e8%b1%a1%e4%bc%a0%e5%aa%92"},
                {"n": "杏吧", "v": "%e6%9d%8f%e5%90%a7"},
                {"n": "抖阴", "v": "%e6%8a%96%e9%98%b4"},
                {"n": "爱豆", "v": "%e7%88%b1%e8%b1%86"},
                {"n": "猫爪影像", "v": "%e7%8c%ab%e7%88%aa%e5%bd%b1%e5%83%8f"},
                {"n": "乐播传媒", "v": "%e4%b9%90%e6%92%ad%e4%bc%a0%e5%aa%92"},
                {"n": "草莓", "v": "%e8%8d%89%e8%8e%93"},
                {"n": "SA国际传媒", "v": "sa%e5%9b%bd%e9%99%85%e4%bc%a0%e5%aa%92"},
                {"n": "起点传媒/性视界传媒", "v": "%e8%b5%b7%e7%82%b9%e4%bc%a0%e5%aa%92-%e6%80%a7%e8%a7%86%e7%95%8c%e4%bc%a0%e5%aa%92"},
            ],
        }
    ],
    "creator_series": [
        {
            "key": "sub",
            "name": "系列厂牌",
            "init": "hongkongdoll",
            "value": [
                {"n": "HongKongDoll", "v": "hongkongdoll"},
                {"n": "PsychopornTW", "v": "psychoporntw"},
                {"n": "大鸟十八", "v": "%e5%a4%a7%e9%b8%9f%e5%8d%81%e5%85%ab"},
                {"n": "小鹏奇啪行", "v": "%e5%b0%8f%e9%b9%8f%e5%a5%87%e5%95%aa%e8%a1%8c"},
            ],
        }
    ],
}

ARTICLE_RE = re.compile(r"<article\b[^>]*>([\s\S]*?)</article>", re.I)
HREF_RE = re.compile(r"<a[^>]+href=[\"']([^\"']+\.html)[\"']", re.I)
TITLE_H2_RE = re.compile(r"<h2[^>]*>[\s\S]*?<a[^>]*>([\s\S]*?)</a>", re.I)
TITLE_ATTR_RE = re.compile(r"<a[^>]+title=[\"']([^\"']+)[\"']", re.I)
PIC_DATA_SRC_RE = re.compile(r"<img[^>]+data-src=[\"']([^\"']+)[\"']", re.I)
PIC_DATA_ORIGINAL_RE = re.compile(r"<img[^>]+data-original=[\"']([^\"']+)[\"']", re.I)
PIC_SRC_RE = re.compile(r"<img[^>]+src=[\"']([^\"']+)[\"']", re.I)
TIME_RE = re.compile(r"<time[^>]*>([\s\S]*?)</time>", re.I)
VIEWS_RE = re.compile(r"观看\(([^)]+)\)")
UL_ITEM_RE = re.compile(r"<li>\s*<a[^>]+href=[\"']([^\"']+\.html)[\"'][^>]*>([\s\S]*?)</a>\s*</li>", re.I)
H1_TITLE_RE = re.compile(r"<h1[^>]*class=[\"']article-title[\"'][^>]*>([\s\S]*?)</h1>", re.I)
DOC_TITLE_RE = re.compile(r"<title>([\s\S]*?)</title>", re.I)
SHAREIMAGE_RE = re.compile(r"shareimage\s*:\s*[\"']([^\"']+)[\"']", re.I)
OG_IMAGE_RE = re.compile(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']", re.I)
CATE_RE = re.compile(r"分类：\s*<a[^>]*>([\s\S]*?)</a>", re.I)
TAG_BLOCK_RE = re.compile(r"<div[^>]+class=[\"']article-tags[\"'][^>]*>([\s\S]*?)</div>", re.I)
TAG_A_RE = re.compile(r"<a[^>]*>([\s\S]*?)</a>", re.I)
IFRAME_RE = re.compile(r"<iframe[^>]+src=[\"']?([^\"'\s>]+)", re.I)
REL_BLOCK_RE = re.compile(r"<div[^>]+class=[\"']postitems[\"'][^>]*>([\s\S]*?)</div>", re.I)
HOT_BLOCK_RE = re.compile(r"<div[^>]+class=[\"']widget widget-postlist[\"'][^>]*>([\s\S]*?)</div>", re.I)
TOKEN_RE = re.compile(r"var\s+token\s*=\s*[\"']([^\"']*)[\"']", re.I)
M3U8_RE = re.compile(r"var\s+m3u8\s*=\s*[\"']([^\"']+\.m3u8[^\"']*)[\"']", re.I)
SIZE_SUFFIX_RE = re.compile(r"-\d+x\d+(?=\.(?:jpg|jpeg|png|webp)(?:[?#]|$))", re.I)
ORIGIN_RE = re.compile(r"^(https?://[^/]+)", re.I)


def strip_tags(value):
    if not value:
        return ""
    clean = re.sub(r"<[^>]+>", " ", str(value))
    clean = html_lib.unescape(clean)
    return re.sub(r"[\r\n\t\s]+", " ", clean).strip()


def clean_ep_label(text):
    cleaned = strip_tags(text)
    cleaned = re.sub(r"[$#@]+", "-", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned.strip("-")


def format_remarks(meta):
    clean_meta = re.sub(r"[\r\n\t]+", " ", str(meta or "")).strip()
    if clean_meta:
        return "%s | %s" % (BRAND, clean_meta)
    return BRAND


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or extend.get("site") or "").strip()
        elif isinstance(extend, str) and extend.strip():
            text = extend.strip()
            if text.startswith("{"):
                try:
                    obj = json.loads(text)
                    if isinstance(obj, dict):
                        custom = str(obj.get("host") or obj.get("site") or "").strip()
                except Exception:
                    custom = ""
            else:
                custom = text
        if custom and custom.startswith("http"):
            self.host = custom.rstrip("/")

    def get_dash_host(self):
        if not self.host or self.host == DEFAULT_HOST:
            return DEFAULT_DASH_HOST
        clean = re.sub(r"^https?://", "", self.host, flags=re.I)
        clean = re.sub(r"^www\.", "", clean, flags=re.I)
        return "https://dash." + clean

    # ---------- text / url helpers ----------

    def unwrap_html(self, raw):
        if not raw:
            return ""
        t = str(raw).strip()
        if len(t) >= 2 and t[0] == '"' and t[-1] == '"':
            try:
                dec = json.loads(t)
                if isinstance(dec, str) and dec:
                    return dec
            except Exception:
                t = t[1:-1]
        t = t.replace('\\"', '"').replace("\\/", "/")
        t = t.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", " ")
        return t

    def resolve_full_url(self, raw_url, host=None):
        if not raw_url:
            return ""
        base = host or self.host
        u = str(raw_url).strip().replace("&amp;", "&")
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return base + u
        if not u.startswith("http"):
            return base + "/" + u
        return u

    def format_poster(self, pic_url):
        if not pic_url:
            return ""
        full = self.resolve_full_url(pic_url)
        return full + "@Referer=" + quote(self.host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def upgrade_hd_pic(self, pic_url):
        if not pic_url:
            return ""
        full = self.resolve_full_url(pic_url)
        full = SIZE_SUFFIX_RE.sub("", full)
        return full + "@Referer=" + quote(self.host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def extract_relative_path(self, full_url):
        u = str(full_url or "").strip()
        if u.startswith(self.host):
            rel = u[len(self.host):]
            return rel if rel else "/"
        m = ORIGIN_RE.match(u)
        if m:
            rest = u[m.end():]
            return rest if rest else "/"
        return u if u.startswith("/") else ("/" + u)

    # ---------- network ----------

    def _fetch_once(self, url, headers):
        try:
            resp = requests.get(url, headers=headers, timeout=8)
        except Exception:
            return None, ""
        body = ""
        if resp is not None and resp.status_code >= 200 and resp.status_code < 300 and resp.text:
            body = resp.text
        return resp, body

    def fetch_html(self, target_url, referer=""):
        if not target_url:
            return ""
        req_url = self.resolve_full_url(target_url)
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        for attempt in range(2):
            resp, body = self._fetch_once(req_url, headers)
            if body:
                return self.unwrap_html(body)
            if resp is not None and resp.status_code in (451, 403, 429) and attempt == 0:
                continue
            if resp is None and req_url.startswith("https://"):
                http_url = "http://" + req_url[8:]
                resp2, body2 = self._fetch_once(http_url, headers)
                if body2:
                    return self.unwrap_html(body2)
        return ""

    # ---------- cards ----------

    def parse_cards(self, html_text):
        items = []
        if not html_text:
            return items
        seen = {}
        for m in ARTICLE_RE.finditer(html_text):
            block = m.group(1)
            if not block:
                continue
            href_m = HREF_RE.search(block)
            raw_href = href_m.group(1).strip() if href_m else ""
            if not raw_href:
                continue
            full_href = self.resolve_full_url(raw_href)
            stable_id = self.extract_relative_path(full_href)
            if not stable_id or stable_id in seen:
                continue
            title_m = TITLE_H2_RE.search(block) or TITLE_ATTR_RE.search(block)
            vod_name = strip_tags(title_m.group(1)) if title_m else ""
            if not vod_name:
                continue
            pic_m = PIC_DATA_SRC_RE.search(block) or PIC_DATA_ORIGINAL_RE.search(block) or PIC_SRC_RE.search(block)
            raw_pic = pic_m.group(1).strip() if pic_m else ""
            meta_m = TIME_RE.search(block) or VIEWS_RE.search(block)
            meta_text = strip_tags(meta_m.group(1)) if meta_m else ""
            seen[stable_id] = True
            items.append({
                "vod_id": stable_id + "@@" + quote(vod_name, safe=""),
                "vod_name": vod_name,
                "vod_pic": self.format_poster(raw_pic),
                "vod_remarks": format_remarks(meta_text),
                "style": {"type": "rect", "ratio": CARD_RATIO},
            })
        return items

    def parse_ul_items(self, section_html):
        results = []
        if not section_html:
            return results
        for m in UL_ITEM_RE.finditer(section_html):
            raw_href = m.group(1).strip() if m.group(1) else ""
            title = strip_tags(m.group(2)) if m.group(2) else ""
            if raw_href and title:
                full_href = self.resolve_full_url(raw_href).split("#")[0]
                results.append({"url": full_href, "title": title})
        return results

    def _page_form(self, items, page):
        if items:
            return {
                "list": items,
                "page": page,
                "pagecount": page + 1,
                "limit": PAGE_SIZE,
                "total": (page + 1) * PAGE_SIZE,
            }
        return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": 0}

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        result = {"class": CLASSES}
        if filter:
            result["filters"] = FILTERS
        return result

    def homeVideoContent(self):
        html_text = self.fetch_html(self.host + "/")
        return {"list": self.parse_cards(html_text)}

    def _category_base_url(self, tid, extend):
        ext = extend if isinstance(extend, dict) else {}
        if tid == "home":
            return self.host
        if tid == "hot_rank":
            rank = str(ext.get("rank") or "likes").strip().strip("/")
            if rank not in ("likes", "week", "month"):
                rank = "likes"
            return self.host + "/" + rank
        if tid == "hot_tags":
            tag = str(ext.get("tag") or "%e7%99%bd%e8%99%8e").strip().strip("/")
            return self.host + "/tag/" + tag
        if tid in ("madou_uni", "top_studios", "indie_studios", "creator_series"):
            defaults = {
                "madou_uni": "%e9%ba%bb%e8%b1%86%e4%bc%a0%e5%aa%92",
                "top_studios": "91%e5%88%b6%e7%89%87%e5%8e%82",
                "indie_studios": "%e5%a4%a7%e8%b1%a1%e4%bc%a0%e5%aa%92",
                "creator_series": "hongkongdoll",
            }
            sub = str(ext.get("sub") or defaults[tid]).strip().strip("/")
            return self.host + "/category/" + sub
        if tid in ("likes", "week", "month"):
            return self.host + "/" + tid
        if tid.startswith("http"):
            return tid.rstrip("/")
        return self.host + "/category/" + tid

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        tid = str(tid or "home").strip("/")
        base_url = self._category_base_url(tid, extend)
        target_url = (base_url + "/") if page <= 1 else (base_url + "/page/" + str(page))
        html_text = self.fetch_html(target_url)
        items = self.parse_cards(html_text)
        return self._page_form(items, page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_form([], page)
        encoded = quote(keyword, safe="")
        if page <= 1:
            target_url = self.host + "/?s=" + encoded
        else:
            target_url = self.host + "/page/" + str(page) + "?s=" + encoded
        html_text = self.fetch_html(target_url)
        items = self.parse_cards(html_text)
        return self._page_form(items, page)

    # ---------- detail ----------

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return lines

    def _episode_value(self, play_page, detail_url, ep_title):
        payload = {"playPage": play_page, "detailUrl": detail_url, "epTitle": ep_title}
        return json.dumps(payload, ensure_ascii=False)

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        raw_id = str(ids[0] or "")
        parts = raw_id.split("@@")
        target_path = parts[0].strip()
        carried_title = unquote(parts[1]).strip() if len(parts) > 1 else ""
        if not target_path:
            return {"list": []}
        detail_url = self.resolve_full_url(target_path)
        html_text = self.fetch_html(detail_url)
        if not html_text:
            return {"list": []}

        title_m = H1_TITLE_RE.search(html_text)
        vod_name = strip_tags(title_m.group(1)) if title_m else ""
        if not vod_name:
            doc_m = DOC_TITLE_RE.search(html_text)
            if doc_m:
                vod_name = strip_tags(doc_m.group(1)).split("-")[0].strip()
        if not vod_name:
            vod_name = carried_title if carried_title else "超清正片"

        pic_m = SHAREIMAGE_RE.search(html_text) or OG_IMAGE_RE.search(html_text) or PIC_DATA_SRC_RE.search(html_text) or PIC_SRC_RE.search(html_text)
        raw_pic = pic_m.group(1).strip() if pic_m else ""
        hd_poster = self.upgrade_hd_pic(raw_pic)

        cate_m = CATE_RE.search(html_text)
        cate_name = strip_tags(cate_m.group(1)) if cate_m else ""
        views_m = VIEWS_RE.search(html_text)
        views_text = strip_tags(views_m.group(1)) if views_m else ""

        genres = []
        if cate_name:
            genres.append(cate_name)
        tag_block_m = TAG_BLOCK_RE.search(html_text)
        if tag_block_m and tag_block_m.group(1):
            for tm in TAG_A_RE.finditer(tag_block_m.group(1)):
                t_val = strip_tags(tm.group(1))
                if t_val and t_val not in genres:
                    genres.append(t_val)

        iframe_m = IFRAME_RE.search(html_text)
        iframe_src = iframe_m.group(1).strip() if iframe_m else ""
        play_target = self.resolve_full_url(iframe_src) if iframe_src else detail_url

        full_title = vod_name if vod_name else "超清正片"
        main_label = clean_ep_label(full_title) or "超清正片"

        main_episodes = []
        main_episodes.append(main_label + "$" + self._episode_value(play_target, detail_url, full_title))

        seen_urls = {}
        seen_urls[detail_url.rstrip("/")] = True

        rel_titles = []
        rel_block_m = REL_BLOCK_RE.search(html_text)
        if rel_block_m and rel_block_m.group(1):
            rel_list = self.parse_ul_items(rel_block_m.group(1))
            for i, rel in enumerate(rel_list):
                norm = rel["url"].rstrip("/")
                if norm in seen_urls:
                    continue
                seen_urls[norm] = True
                rel_titles.append(rel["title"])
                rel_label = clean_ep_label(rel["title"]) or ("推荐" + str(i + 1))
                main_episodes.append(rel_label + "$" + self._episode_value(rel["url"], detail_url, rel["title"]))

        hot_episodes = []
        hot_block_m = HOT_BLOCK_RE.search(html_text)
        if hot_block_m and hot_block_m.group(1):
            hot_list = self.parse_ul_items(hot_block_m.group(1))
            for j, hot in enumerate(hot_list):
                norm = hot["url"].rstrip("/")
                if norm in seen_urls:
                    continue
                seen_urls[norm] = True
                hot_label = clean_ep_label(hot["title"]) or ("热门" + str(j + 1))
                hot_episodes.append(hot_label + "$" + self._episode_value(hot["url"], detail_url, hot["title"]))

        play_from_parts = [LINE_NAME]
        play_url_parts = ["#".join(main_episodes)]
        if hot_episodes:
            play_from_parts.append(HOT_LINE_NAME)
            play_url_parts.append("#".join(hot_episodes))

        summary_lines = self._brand_block()
        summary_lines.append("标题：" + full_title)
        summary_lines.append("分类：" + "、".join(genres))
        summary_lines.append("片源：" + LINE_NAME)
        summary_lines.append("编号：" + target_path)
        if rel_titles:
            summary_lines.append("相关推荐：" + "、".join(rel_titles[:6]))

        vod = {
            "vod_id": raw_id,
            "vod_name": full_title,
            "vod_pic": hd_poster,
            "vod_bg": hd_poster,
            "vod_background": hd_poster,
            "vod_banner": hd_poster,
            "vod_actor": TG_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks(views_text),
            "vod_content": "\n".join(summary_lines),
            "vod_play_from": "$$$".join(play_from_parts),
            "vod_play_url": "$$$".join(play_url_parts),
        }
        return {"list": [vod]}

    # ---------- player ----------

    def playerContent(self, flag, id, vipFlags):
        play_page = ""
        detail_url = self.host + "/"
        ep_title = ""
        raw = str(id or "").strip()
        if raw:
            try:
                payload = json.loads(raw)
                if isinstance(payload, dict):
                    play_page = str(payload.get("playPage") or "").strip()
                    detail_url = str(payload.get("detailUrl") or "").strip() or detail_url
                    ep_title = str(payload.get("epTitle") or "").strip()
            except Exception:
                play_page = ""
            if not play_page and not raw.startswith("{"):
                play_page = self.resolve_full_url(raw)
        if not play_page:
            return {"parse": 1, "url": detail_url, "header": {"User-Agent": UA, "Referer": detail_url}}

        if "/share/" not in play_page:
            det_html = self.fetch_html(play_page, detail_url)
            iframe_m = IFRAME_RE.search(det_html)
            if iframe_m and iframe_m.group(1):
                play_page = self.resolve_full_url(iframe_m.group(1).strip())

        share_html = self.fetch_html(play_page, detail_url)
        token_m = TOKEN_RE.search(share_html)
        m3u8_m = M3U8_RE.search(share_html)
        token = token_m.group(1).strip() if token_m else ""
        m3u8_path = m3u8_m.group(1).strip() if m3u8_m else ""

        if m3u8_path:
            if m3u8_path.startswith("http"):
                stream_url = m3u8_path
            elif m3u8_path.startswith("//"):
                stream_url = "https:" + m3u8_path
            else:
                origin_m = ORIGIN_RE.match(play_page)
                share_origin = origin_m.group(1) if origin_m else self.get_dash_host()
                stream_url = self.resolve_full_url(m3u8_path, share_origin)
            if token and "token=" not in stream_url:
                sep = "&" if "?" in stream_url else "?"
                stream_url = stream_url + sep + "token=" + quote(token, safe="")
            if ".m3u8" not in stream_url.lower():
                sep = "&" if "?" in stream_url else "?"
                stream_url = stream_url + sep + "format=.m3u8"
            stream_origin_m = ORIGIN_RE.match(stream_url)
            stream_origin = stream_origin_m.group(1) if stream_origin_m else self.get_dash_host()
            return {
                "parse": 0,
                "url": stream_url,
                "header": {
                    "User-Agent": UA,
                    "Referer": play_page,
                    "Origin": stream_origin,
                },
            }

        return {"parse": 1, "url": play_page, "header": {"User-Agent": UA, "Referer": detail_url}}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249835069&sig=9ad0518e778fb578
