# -*- coding: utf-8 -*-
# 51吃瓜 spider for FongMi / TVBox
import json
import random
import re
import urllib.error
import urllib.parse
import urllib.request

from base.spider import Spider as BaseSpider

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND_NAME = "51吃瓜"
DEFAULT_HOST = "https://51cg1.com"
DEFAULT_PIC_CDN = "https://pic.gyezbp.cn"
DEFAULT_WORKER = "https://chigua-img-proxy.yishengheqiu7679.workers.dev"
PAGE_SIZE = 25

CATEGORIES = [
    ("feed_stream", "🔥 沉浸连刷"),
    ("root_home", "全部最新"),
    ("wpcz", "今日吃瓜"),
    ("cbdj", "AI成人短剧"),
    ("mrds", "每日大赛"),
    ("whhj", "网黄合集"),
    ("mrdg", "吃瓜榜单"),
    ("qghj", "瓜友点播"),
    ("rdsj", "热门大瓜"),
    ("bkdg", "必看大瓜"),
    ("ysyl", "成人视频"),
    ("lldd", "伦理道德"),
    ("gcjq", "国产视频"),
    ("thjx", "探花精选"),
    ("xsxy", "学生校园"),
    ("whhl", "网红黑料"),
    ("snsn", "骚男骚女"),
    ("whmx", "明星爆料"),
    ("hwcg", "海外吃瓜"),
    ("rrcg", "人人吃瓜"),
    ("ldcg", "领导干部"),
    ("jpll", "软萌甜妹"),
    ("sjb", "竞技吃瓜"),
    ("qubk", "吃瓜看戏"),
    ("dcbq", "擦边撩骚"),
    ("zzs", "性爱技巧"),
    ("cgxw", "吃瓜新闻"),
    ("yczq", "原创博主"),
    ("51djc", "51剧场"),
]
AD_KEYWORDS = ["重金求稿", "变现", "高价收购", "商务合作", "吃瓜导航", "我要投稿", "关于我们"]
FEED_POOL_CATS = ["wpcz", "mrds", "rdsj", "bkdg", "thjx", "xsxy", "whhl", "root_home", "mrdg"]
PIC_ATTRS = ["z-bg-loader-url", "x-bg-loader-url", "z-image-loader-url", "data-banner", "data-src", "data-original", "data-bg", "data-thumb"]
COVER_ATTRS = ["z-bg-loader-url", "x-bg-loader-url", "z-image-loader-url", "data-banner", "data-src", "data-original"]

BANNER_RE = re.compile(r"loadBannerDirect\(['\"]([^'\"]+)['\"]\s*,\s*['\"][^'\"]*['\"]\s*,\s*document\.querySelector\(['\"]#post-card-(\d+)['\"]\)", re.I)
ASIDE_RE = re.compile(r"<aside[\s\S]*?</aside>", re.I)
WIDGET_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*(?:widget|sidebar)[^\"']*[\"'][^>]*>[\s\S]*?</div>", re.I)
ARTICLE_RE = re.compile(r"<article[^>]*>([\s\S]*?)</article>", re.I)
POSTCARD_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*post-card[^\"']*[\"'][^>]*>[\s\S]*?</div>\s*</div>", re.I)
CARD_ID_RE = re.compile(r"id=[\"']post-card-(\d+)[\"']", re.I)
ARCHIVES_ID_RE = re.compile(r"/archives/(\d+)/", re.I)
TITLE_CLASS_RE = re.compile(r"<h[234][^>]*class=[\"'][^\"']*post-card-title[^\"']*[\"'][^>]*>([\s\S]*?)</h[234]>", re.I)
TITLE_H_RE = re.compile(r"<h[234][^>]*>([\s\S]*?)</h[234]>", re.I)
DATE_META_RE = re.compile(r"itemprop=[\"']datePublished[\"'][^>]+content=[\"'](\d{4}-\d{2}-\d{2})", re.I)
DATE_CN_RE = re.compile(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)")
DATE_ANY_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
TITLE_SUFFIX_RE = re.compile(r"\s*(?:热搜\s*HOT|HOT|置顶|独家|NEW|吃瓜\s*HOT|爆料\s*HOT)\s*$", re.I)
POST_BODY_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*post-content[^\"']*[\"'][^>]*>([\s\S]*?)(?:<div[^>]+class=[\"'][^\"']*(?:post-footer|post-tags|comments)[\"'][^>]*>|</article>)", re.I)
SUB_LINK_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/archives/(\d+)/?[\"'][^>]*>([\s\S]*?)</a>", re.I)
SUB_LINK_ID_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/archives/(\d+)/?[\"']", re.I)
GALLERY_RE = re.compile(r"(?:z-image-loader-url|x-bg-loader-url|data-src|src)=[\"']([^\"']+)[\"']", re.I)


def strip_tags(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(text))).strip()


def clean_title(raw):
    if not raw:
        return ""
    t = strip_tags(raw)
    t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"').replace("&#039;", "'").replace("&nbsp;", " "))
    t = TITLE_SUFFIX_RE.sub("", t)
    return t.strip()


def clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw)
    clean = re.sub(r"\\u0068ttps", "https", clean)
    clean = re.sub(r"\\u0068ttp", "http", clean)
    clean = clean.replace("\\/", "/").replace('\\"', '"')
    clean = clean.replace("&quot;", "").replace("'", "").replace('"', "")
    clean = re.sub(r"[\s\]\}]+$", "", clean).strip()
    if clean.startswith("//"):
        clean = "https:" + clean
    return clean


def entity_decode(text):
    return (str(text).replace("&quot;", '"').replace("&amp;", "&")
            .replace("&#039;", "'").replace("&lt;", "<").replace("&gt;", ">"))


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST
        self.img_worker = DEFAULT_WORKER

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        self.img_worker = DEFAULT_WORKER
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
                        worker = str(data.get("imgWorker") or "").strip()
                        if worker.startswith("http"):
                            self.img_worker = worker.rstrip("/")
                except Exception:
                    pass

    def getName(self):
        return BRAND_NAME

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------------- fetch ----------------

    def _fetch_once(self, url):
        headers = {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
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
            return None

    def _fetch(self, url):
        if not url:
            return ""
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.host + url
        result = self._fetch_once(url)
        if result is None:
            if url.startswith("https://"):
                retry = self._fetch_once("http://" + url[8:])
                return retry if retry else ""
            return ""
        return result

    # ---------------- posters ----------------

    def _format_poster(self, raw_pic):
        if not raw_pic:
            return ""
        p = str(raw_pic).strip().strip("'\"").replace("&amp;", "&")
        if not p:
            return ""
        if p.startswith("//"):
            p = "https:" + p
        elif p.startswith("http://") or p.startswith("https://"):
            pass
        elif (p.startswith("/upload") or p.startswith("upload") or p.startswith("/image")
              or p.startswith("image") or p.startswith("/hc") or p.startswith("hc")):
            if not p.startswith("/"):
                p = "/" + p
            p = DEFAULT_PIC_CDN + p
        elif p.startswith("/"):
            p = self.host + p
        if self.img_worker:
            return self.img_worker + "/?url=" + urllib.parse.quote(p, safe="")
        return (p + "@Referer=" + urllib.parse.quote(self.host + "/", safe="")
                + "&User-Agent=" + urllib.parse.quote(UA, safe=""))

    def _extract_card_pic(self, block):
        for attr in PIC_ATTRS:
            m = re.search(attr + r"=[\"']([^\"']+)[\"']", block, re.I)
            if m and m.group(1):
                cand = m.group(1).strip()
                if cand and "img-placeholder" not in cand and "logo" not in cand.lower() and ".svg" not in cand.lower():
                    return cand
        m = re.search(r"[a-zA-Z0-9_-]*(?:bg-loader-url|image-loader-url)=[\"']([^\"']+)[\"']", block, re.I)
        if m and m.group(1):
            cand = m.group(1).strip()
            if cand and "img-placeholder" not in cand and "logo" not in cand.lower() and ".svg" not in cand.lower():
                return cand
        m = re.search(r"loadBannerDirect\s*\(\s*['\"]([^'\"]+)['\"]", block, re.I)
        if m and m.group(1):
            cand = m.group(1).strip()
            if cand and "img-placeholder" not in cand:
                return cand
        m = re.search(r"loadImage\s*\(\s*['\"]([^'\"]+)['\"]", block, re.I)
        if m and m.group(1):
            cand = m.group(1).strip()
            if cand and "img-placeholder" not in cand:
                return cand
        m = re.search(r"style=[\"'][^\"']*background(?:-image)?\s*:\s*url\(([\"']?)([^\"')]+)\1\)", block, re.I)
        if m and m.group(2):
            cand = m.group(2).strip()
            if cand and "img-placeholder" not in cand:
                return cand
        m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", block, re.I)
        if m and m.group(1):
            src = m.group(1).strip()
            if src and "logo" not in src.lower() and "img-placeholder" not in src and "avatar" not in src.lower() and ".svg" not in src.lower():
                return src
        return ""

    # ---------------- cards ----------------

    def _parse_cards(self, html_text, is_feed):
        if not html_text:
            return []
        items = []
        seen = set()
        banner_map = {}
        for bm in BANNER_RE.finditer(html_text):
            banner_map[bm.group(2)] = bm.group(1)
        clean = ASIDE_RE.sub("", html_text)
        clean = WIDGET_RE.sub("", clean)
        blocks = [m.group(1) for m in ARTICLE_RE.finditer(clean)]
        if not blocks:
            blocks = [m.group(0) for m in POSTCARD_RE.finditer(clean)]
        for inner in blocks:
            if "post-card-ads" in inner or "ad-card" in inner or "ad-item" in inner:
                continue
            idm = CARD_ID_RE.search(inner) or ARCHIVES_ID_RE.search(inner)
            if not idm:
                continue
            aid = idm.group(1).strip()
            if aid in seen or aid == "139553":
                continue
            tm = TITLE_CLASS_RE.search(inner) or TITLE_H_RE.search(inner)
            if tm:
                raw_extracted = re.split(r"<div|<span|<p", tm.group(1), flags=re.I)[0]
                name = clean_title(raw_extracted)
            else:
                raw_txt = strip_tags(inner)
                name = clean_title(raw_txt[:60]) if raw_txt else ("热点爆料 " + aid)
            if not name:
                continue
            has_ad = False
            for kw in AD_KEYWORDS:
                if kw in name:
                    has_ad = True
                    break
            if has_ad:
                continue
            seen.add(aid)
            post_date = ""
            dm = DATE_META_RE.search(inner)
            if dm:
                post_date = dm.group(1).strip()
            else:
                cm = DATE_CN_RE.search(inner)
                if cm:
                    post_date = re.sub(r"\s+", "", cm.group(1)).strip()
                else:
                    dm2 = DATE_ANY_RE.search(inner)
                    if dm2:
                        post_date = dm2.group(1).strip()
            raw_pic = self._extract_card_pic(inner)
            if not raw_pic and aid in banner_map:
                raw_pic = banner_map[aid]
            if is_feed:
                remarks = "蝴蝶影视 | 连刷起播"
                vid = "feed@@" + aid
            else:
                remarks = "蝴蝶影视 | " + (post_date if post_date else "现场实录")
                vid = aid
            items.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": self._format_poster(raw_pic),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.78},
            })
        return items

    # ---------------- video urls ----------------

    def _extract_video_urls(self, html_text):
        if not html_text:
            return []
        video_list = []
        m_container = (re.search(r"id=[\"']article-videos[\"'][^>]+data-url=([\"'])([\s\S]*?)\1", html_text, re.I)
                       or re.search(r"data-url=([\"'])([\s\S]*?)\1", html_text, re.I))
        if m_container and m_container.group(2):
            raw_val = entity_decode(m_container.group(2)).strip()
            if raw_val.startswith("["):
                try:
                    parsed = json.loads(raw_val)
                    if isinstance(parsed, list):
                        video_list = [v for v in parsed if isinstance(v, str)]
                except Exception:
                    video_list = re.findall(r"https?://[^\s\"'<>]+", raw_val)
            elif raw_val:
                video_list = [raw_val]
        if not video_list:
            for m_cfg in re.finditer(r"data-config=([\"'])([\s\S]*?)\1", html_text, re.I):
                raw_cfg = entity_decode(m_cfg.group(2))
                um = re.search(r"[\"']url[\"']\s*:\s*[\"']([^\"']+)[\"']", raw_cfg, re.I)
                if um and um.group(1):
                    video_list.append(um.group(1))
        if not video_list:
            for m_v in re.finditer(r"<video[^>]+>", html_text, re.I):
                sm = re.search(r"(?:data-hls-src|data-src|src)=[\"']([^\"']+)[\"']", m_v.group(0), re.I)
                if sm and sm.group(1):
                    video_list.append(sm.group(1))
        if not video_list:
            for m_s in re.finditer(r"[\"'](https?:[\\/]+[^\"'\s]+\.(?:m3u8|mp4)[^\"'\s]*)[\"']", html_text, re.I):
                video_list.append(m_s.group(1))
        seen = set()
        result = []
        for v in video_list:
            cleaned = clean_stream_url(v)
            if cleaned and cleaned not in seen and "logo" not in cleaned.lower():
                seen.add(cleaned)
                result.append(cleaned)
        return result

    def _extract_episodes(self, html_text, prefix):
        urls = self._extract_video_urls(html_text)
        episodes = []
        for i, url in enumerate(urls):
            num = i + 1
            name = prefix + " " + ("0" + str(num) if num < 10 else str(num))
            episodes.append((name, url))
        return episodes

    # ---------------- entries ----------------

    def homeContent(self, filter):
        return {"class": [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]}

    def homeVideoContent(self):
        html_text = self._fetch(self.host + "/")
        items = self._parse_cards(html_text, False)
        return {"list": items[:12]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        cid = str(tid or "").strip("/")
        is_feed = (cid == "feed_stream")
        if is_feed or cid in ("root_home", "index", "home", ""):
            urls = [self.host + "/page/" + str(page) + "/"] if page > 1 else [self.host + "/"]
        else:
            if page > 1:
                urls = [self.host + "/category/" + cid + "/" + str(page) + "/",
                        self.host + "/category/" + cid + "/?page=" + str(page)]
            else:
                urls = [self.host + "/category/" + cid + "/",
                        self.host + "/category/" + cid]
        items = []
        for url in urls:
            html_text = self._fetch(url)
            if html_text:
                items = self._parse_cards(html_text, is_feed)
                if items:
                    break
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
        enc = urllib.parse.quote(keyword, safe="")
        url = self.host + "/search/" + enc + "/" + str(page) + "/" if page > 1 else self.host + "/search/" + enc + "/"
        html_text = self._fetch(url)
        items = self._parse_cards(html_text, False) if html_text else []
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

    def detailContent(self, ids):
        raw_id = str(ids[0]) if ids else ""
        is_feed = False
        if raw_id.startswith("feed@@"):
            is_feed = True
            parts = raw_id.split("@@")
            start_aid = parts[1] if len(parts) > 1 else ""
        else:
            start_aid = raw_id
        start_aid = str(start_aid or "").strip("/")
        target_url = self.host + "/archives/" + start_aid + "/"
        html_text = self._fetch(target_url)
        title = "热点爆料 " + start_aid
        tm = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html_text, re.I)
        if tm:
            title = clean_title(tm.group(1))
        desc = ""
        dm = re.search(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']*)[\"']", html_text, re.I)
        if dm:
            desc = dm.group(1).strip()
        cover = ""
        for attr in COVER_ATTRS:
            m = re.search(attr + r"=[\"']([^\"']+)[\"']", html_text, re.I)
            if m and m.group(1) and "img-placeholder" not in m.group(1):
                cover = m.group(1).strip()
                break
        if not cover:
            bm = re.search(r"loadBannerDirect\s*\(\s*['\"]([^'\"]+)['\"]", html_text, re.I)
            if bm and bm.group(1) and "img-placeholder" not in bm.group(1):
                cover = bm.group(1).strip()
        if not cover:
            om = re.search(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']*)[\"']", html_text, re.I)
            if om and om.group(1) and "img-placeholder" not in om.group(1):
                cover = om.group(1).strip()
        resolved_cover = self._format_poster(cover) if cover else ""
        if is_feed:
            return {"list": [self._feed_detail(raw_id, start_aid, title, desc, resolved_cover)]}
        episodes = self._extract_episodes(html_text, "正片")
        if not episodes:
            pm = POST_BODY_RE.search(html_text)
            post_body = pm.group(1) if pm else html_text
            sub_tasks = []
            seen_sub = set()
            for sm in SUB_LINK_RE.finditer(post_body):
                sub_id = sm.group(1).strip()
                if sub_id == start_aid or sub_id in seen_sub or sub_id == "139553":
                    continue
                seen_sub.add(sub_id)
                sub_raw_title = strip_tags(sm.group(2))
                if sub_raw_title:
                    label = re.sub(r"[\$#\r\n\t]", "", sub_raw_title)[:22].strip()
                else:
                    n = len(sub_tasks) + 1
                    label = "TOP " + ("0" + str(n) if len(sub_tasks) < 9 else str(n))
                sub_tasks.append((sub_id, label))
                if len(sub_tasks) >= 12:
                    break
            for sub_id, label in sub_tasks:
                sub_html = self._fetch(self.host + "/archives/" + sub_id + "/")
                if sub_html:
                    sub_urls = self._extract_video_urls(sub_html)
                    for v_idx, v_url in enumerate(sub_urls):
                        ep_label = label if len(sub_urls) == 1 else (label + "·片段" + str(v_idx + 1))
                        episodes.append((ep_label, v_url))
        if not episodes:
            seen_gallery = set()
            for gm in GALLERY_RE.finditer(html_text):
                p_url = gm.group(1)
                low = p_url.lower()
                if "logo" in low or "avatar" in low or "icon" in low or "placeholder" in low or ".gif" in low:
                    continue
                if p_url in seen_gallery:
                    continue
                seen_gallery.add(p_url)
                full = p_url
                if full.startswith("//"):
                    full = "https:" + full
                elif full.startswith("/") and not full.startswith("/upload"):
                    full = self.host + full
                g_num = len(episodes) + 1
                episodes.append(("图集现场 " + ("0" + str(g_num) if g_num < 10 else str(g_num)), full))
                if len(episodes) >= 12:
                    break
        main_eps = []
        fb_eps = []
        for name, url in episodes:
            clean_name = name.replace("$", "_").replace("#", "_")
            main_eps.append(clean_name + "$" + json.dumps({"playUrl": url}, ensure_ascii=False))
            fb_eps.append(clean_name + "$" + json.dumps({"playUrl": re.sub(r"^https://", "http://", url, flags=re.I)}, ensure_ascii=False))
        summary = self._brand_block()
        if desc:
            summary += "\n" + desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：51吃瓜",
                "片源：🦋 蝴蝶专线、⚡ 备用线路 (HTTP)",
                "编号：" + start_aid,
            ])
        remarks = "蝴蝶影视 | 共" + str(len(episodes)) + "个切片" if len(episodes) > 1 else "蝴蝶影视 | 现场实录"
        vod = {
            "vod_id": raw_id,
            "vod_name": title,
            "vod_pic": resolved_cover,
            "vod_bg": resolved_cover,
            "vod_background": resolved_cover,
            "vod_banner": resolved_cover,
            "vod_remarks": remarks,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_content": summary,
            "vod_play_from": "🦋 蝴蝶专线$$$⚡ 备用线路 (HTTP)",
            "vod_play_url": "#".join(main_eps) + "$$$" + "#".join(fb_eps),
        }
        return {"list": [vod]}

    def _feed_detail(self, raw_id, start_aid, title, desc, cover):
        episodes = []
        first = ("01 · " + title).replace("$", "_").replace("#", "_")
        episodes.append(first + "$" + json.dumps({"aid": start_aid, "feed": True}, ensure_ascii=False))
        pool = list(FEED_POOL_CATS)
        random.shuffle(pool)
        sampled = pool[:3]
        targets = []
        seen = {start_aid}
        for sec in sampled:
            r_page = random.randint(1, 3)
            if sec == "root_home":
                url = self.host + "/page/" + str(r_page) + "/" if r_page > 1 else self.host + "/"
            else:
                url = self.host + "/category/" + sec + "/" + str(r_page) + "/" if r_page > 1 else self.host + "/category/" + sec + "/"
            s_html = self._fetch(url)
            if s_html:
                for card in self._parse_cards(s_html, False):
                    card_aid = card["vod_id"]
                    if card_aid not in seen and card_aid != "139553":
                        seen.add(card_aid)
                        targets.append((card_aid, card["vod_name"]))
            if len(targets) >= 70:
                break
        random.shuffle(targets)
        for t_aid, t_title in targets:
            seq = len(episodes) + 1
            seq_str = "0" + str(seq) if seq < 10 else str(seq)
            ep_name = (seq_str + " · " + t_title).replace("$", "_").replace("#", "_")
            episodes.append(ep_name + "$" + json.dumps({"aid": t_aid, "feed": True}, ensure_ascii=False))
        summary = self._brand_block()
        if desc:
            summary += "\n" + desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：51吃瓜",
                "片源：🦋 沉浸连刷专线",
                "编号：" + start_aid,
            ])
        return {
            "vod_id": raw_id,
            "vod_name": "🔥 沉浸连刷·" + title,
            "vod_pic": cover,
            "vod_bg": cover,
            "vod_background": cover,
            "vod_banner": cover,
            "vod_remarks": "蝴蝶影视 | 连刷流 " + str(len(episodes)) + " 条",
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_content": summary,
            "vod_play_from": "🦋 沉浸连刷专线",
            "vod_play_url": "#".join(episodes),
        }

    # ---------------- resolve ----------------

    def playerContent(self, flag, id, vipFlags):
        data = {}
        try:
            data = json.loads(id)
        except Exception:
            data = {}
        headers = {"User-Agent": UA, "Referer": self.host + "/", "Origin": self.host}
        play_url = str(data.get("playUrl") or "").strip()
        if data.get("feed") and data.get("aid"):
            aid = str(data["aid"])
            page_html = self._fetch(self.host + "/archives/" + aid + "/")
            urls = self._extract_video_urls(page_html)
            if urls:
                play_url = urls[0]
            else:
                for sm in SUB_LINK_ID_RE.finditer(page_html):
                    next_aid = sm.group(1)
                    if next_aid != aid and next_aid != "139553":
                        sub_html = self._fetch(self.host + "/archives/" + next_aid + "/")
                        sub_urls = self._extract_video_urls(sub_html)
                        if sub_urls:
                            play_url = sub_urls[0]
                            break
            if not play_url:
                return {"parse": 1, "url": self.host + "/archives/" + aid + "/", "header": headers}
        if not play_url:
            return {"parse": 1, "url": self.host + "/", "header": headers}
        return {"parse": 0, "url": play_url, "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249328799&sig=0f06380594f31e30
