# -*- coding: utf-8 -*-
# 718吃瓜 spider for FongMi / TVBox
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
BRAND_NAME = "718吃瓜"
DEFAULT_HOST = "https://www.718yule.com"
DEFAULT_CDN = "https://718haibao.peiqi192192.workers.dev/img"
PAGE_SIZE = 43

CATEGORIES = [
    ("feed_stream", "🔥 沉浸连刷"),
    ("home_feed", "吃瓜首页"),
    ("daily-gossip", "每日吃瓜"),
    ("top-stories", "热门吃瓜"),
    ("contrast-reveal", "反差婊曝光"),
    ("week-top", "吃瓜TOP榜"),
    ("sexbook", "网黄合集"),
    ("AINSFW", "AI成人短剧"),
    ("internet-celebrities", "抖音网红瓜"),
    ("trending-news", "社会热瓜"),
    ("model-photos", "微密圈"),
    ("fuli", "福利姬"),
    ("celebrity-scandals", "娱乐吃瓜"),
    ("entertainment-news", "娱乐圈爆料"),
]
AD_ID_BLACKLIST = {"14", "22245", "22877", "22747", "20261"}
STRICT_AD_KEYWORDS = [
    "约炮", "成人直播", "欲女的高潮", "欲女", "交友", "同城",
    "兼职", "商务合作", "重金求稿", "变现", "高价收购", "吃瓜导航",
]
FEED_POOL_CATS = ["daily-gossip", "top-stories", "contrast-reveal", "week-top",
                  "trending-news", "home_feed", "internet-celebrities", "sexbook"]
RAW_TITLE_REJECT = ["HOT", "热搜", "置顶", "广告", "推广"]

ASIDE_RE = re.compile(r"<aside[\s\S]*?</aside>", re.I)
WIDGET_RE = re.compile(r"<div[^>]+class=['\"][^'\"]*(?:widget|sidebar)[^'\"]*['\"][\s\S]*?</div>", re.I)
ARTICLE_RE = re.compile(r"<article[^>]*>([\s\S]*?)</article>", re.I)
POSTCARD_DIV_RE = re.compile(r"<div[^>]+class=['\"][^'\"]*post-card[^'\"]*['\"][^>]*>([\s\S]*?</div>\s*</div>)", re.I)
ARCHIVES_ID_RE = re.compile(r"/archives/(\d+)/?")
TITLE_CLASS_RE = re.compile(r"<h[234][^>]*class=['\"][^'\"]*post-card-title[^'\"]*['\"][^>]*>([\s\S]*?)</h[234]>", re.I)
TITLE_H_RE = re.compile(r"<h[234][^>]*>([\s\S]*?)</h[234]>", re.I)
DATE_META_RE = re.compile(r"itemprop=['\"](?:dateModified|datePublished)['\"][^>]+content=['\"](\d{4}-\d{2}-\d{2})", re.I)
DATE_ANY_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
TITLE_SUFFIX_RE = re.compile(r"\s*(?:热搜\s*HOT|HOT|置顶|独家|NEW|吃瓜\s*HOT|爆料\s*HOT|\|\s*吃瓜718)\s*$", re.I)
PIC_PATH_RE = re.compile(r"['\"](/(?:5202|718yule|upload)/[^'\"]+\.(?:webp|jpg|png|jpeg)[^'\"]*)['\"]", re.I)
POST_BODY_RE = re.compile(r"<div[^>]+class=['\"][^'\"]*(?:post-content|content)[^'\"]*['\"][^>]*>([\s\S]*?)(?:<div[^>]+class=['\"][^'\"]*(?:post-footer|post-tags|comments)[^'\"]*['\"]|</article>)", re.I)
SUB_LINK_RE = re.compile(r"<a[^>]+href=['\"](?:https?://[^/]+)?/archives/(\d+)/?['\"][^>]*>([\s\S]*?)</a>", re.I)
SUB_LINK_ID_RE = re.compile(r"<a[^>]+href=['\"](?:https?://[^/]+)?/archives/(\d+)/?['\"]", re.I)


def decode_html(text):
    if not text:
        return ""
    return (str(text).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#039;", "'").replace("&#39;", "'"))


def clean_title_text(raw):
    if not raw:
        return ""
    t = re.sub(r"<[^>]+>", "", str(raw))
    t = decode_html(t)
    t = re.sub(r"[\r\n\t]+", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    t = TITLE_SUFFIX_RE.sub("", t)
    return t.strip()


def clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw)
    clean = re.sub(r"\\u0068ttps", "https", clean)
    clean = re.sub(r"\\u0068ttp", "http", clean)
    clean = clean.replace("\\/", "/")
    clean = re.sub(r"\\u0026", "&", clean)
    clean = clean.replace("&quot;", "").replace('"', "").replace("'", "")
    clean = re.sub(r"[\s\]\}]+$", "", clean).strip()
    if clean.startswith("//"):
        clean = "https:" + clean
    return clean


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST
        self.cdn = DEFAULT_CDN

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        self.cdn = DEFAULT_CDN
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
                        cdn = str(data.get("cdn") or "").strip()
                        if cdn.startswith("http"):
                            self.cdn = cdn.rstrip("/")
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

    def _resolve_pic(self, rel_pic):
        if not rel_pic:
            return ""
        clean = str(rel_pic).strip().strip("'\"")
        clean = re.sub(r"^https?://[^/]+/", "", clean).lstrip("/")
        return self.cdn + "/" + clean

    def _extract_card_pic(self, block):
        m = re.search(r"class=['\"][^'\"]*blog-background[^'\"]*['\"][^>]+data-pic=['\"]([^'\"]+)['\"]", block, re.I)
        if not m:
            m = re.search(r"data-pic=['\"]([^'\"]+)['\"]", block, re.I)
        if m:
            cand = m.group(1).strip()
            if "listzw" not in cand and "placeholder" not in cand:
                return cand
        m = re.search(r"<meta[^>]+itemprop=['\"]image['\"][^>]+content=['\"]([^'\"]+)['\"]", block, re.I)
        if m:
            cand = m.group(1).strip()
            if "listzw" not in cand and "placeholder" not in cand:
                return cand
        m = PIC_PATH_RE.search(block)
        if m:
            cand = m.group(1).strip()
            if "listzw" not in cand and "placeholder" not in cand:
                return cand
        return ""

    # ---------------- cards ----------------

    def _parse_cards(self, html_text, is_feed):
        raw = str(html_text or "")
        clean = ASIDE_RE.sub("", raw)
        clean = WIDGET_RE.sub("", clean)
        items = []
        seen = set()
        blocks = [m.group(1) for m in ARTICLE_RE.finditer(clean)]
        if not blocks:
            blocks = [m.group(1) for m in POSTCARD_DIV_RE.finditer(clean)]
        for block in blocks:
            if ('rel="sponsored nofollow"' in block or 'itemprop="sponsor"' in block
                    or "_czc.push" in block or "sticky" in block or "post-sticky" in block):
                continue
            idm = ARCHIVES_ID_RE.search(block)
            if not idm:
                continue
            aid = idm.group(1).strip()
            if aid in seen or aid in AD_ID_BLACKLIST:
                continue
            tm = TITLE_CLASS_RE.search(block) or TITLE_H_RE.search(block)
            raw_title = ""
            if tm:
                raw_title = tm.group(1)
                cut = re.search(r"<div|<span|<p", raw_title, re.I)
                if cut:
                    raw_title = raw_title[:cut.start()]
            rejected = False
            for marker in RAW_TITLE_REJECT:
                if marker in raw_title:
                    rejected = True
                    break
            if rejected:
                continue
            name = clean_title_text(raw_title) if raw_title else ""
            if not name:
                plain = re.sub(r"<[^>]+>", " ", block).strip()
                name = clean_title_text(plain[:60]) if plain else ("热点爆料 " + aid)
            has_ad = False
            for kw in STRICT_AD_KEYWORDS:
                if kw in name:
                    has_ad = True
                    break
            if has_ad or not name:
                continue
            seen.add(aid)
            post_date = ""
            dm = DATE_META_RE.search(block)
            if dm:
                post_date = dm.group(1).strip()
            else:
                dm2 = DATE_ANY_RE.search(block)
                if dm2:
                    post_date = dm2.group(1).strip()
            pic = self._extract_card_pic(block)
            resolved = self._resolve_pic(pic) if pic else ""
            if is_feed:
                remarks = "蝴蝶影视 | 连刷起播"
                vid = "feed@@" + aid
            else:
                remarks = "蝴蝶影视 | " + (post_date if post_date else "现场实录")
                vid = aid
            items.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": resolved,
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.78},
            })
        return items

    # ---------------- video urls ----------------

    def _extract_video_urls(self, html_text):
        if not html_text:
            return []
        video_list = []
        for m_cfg in re.finditer(r"data-config=(['\"])([\s\S]*?)\1", html_text, re.I):
            raw_cfg = decode_html(m_cfg.group(2))
            u2 = re.search(r"['\"]url2['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw_cfg)
            if u2 and u2.group(1):
                video_list.append(u2.group(1))
            u1 = re.search(r"['\"]url['\"]\s*:\s*['\"]([^'\"]+)['\"]", raw_cfg)
            if u1 and u1.group(1) and u1.group(1) != "null":
                video_list.append(u1.group(1))
        if not video_list:
            m_container = (re.search(r"id=['\"]article-videos['\"][^>]+data-url=(['\"])([\s\S]*?)\1", html_text, re.I)
                           or re.search(r"data-url=(['\"])([\s\S]*?)\1", html_text, re.I))
            if m_container:
                raw_val = decode_html(m_container.group(2)).strip()
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
            for m_v in re.finditer(r"<video[^>]+>", html_text, re.I):
                sm = re.search(r"(?:data-hls-src|data-src|src)=['\"]([^'\"]+)['\"]", m_v.group(0), re.I)
                if sm and sm.group(1):
                    video_list.append(sm.group(1))
        if not video_list:
            for m_s in re.finditer(r"['\"](https?:[/\\]+[^'\"\s]+\.(?:m3u8|mp4)[^'\"\s]*)['\"]", html_text, re.I):
                video_list.append(m_s.group(1))
        seen = set()
        result = []
        for v in video_list:
            cleaned = clean_stream_url(v)
            if cleaned and cleaned not in seen and "logo" not in cleaned:
                seen.add(cleaned)
                result.append(cleaned)
        return result

    # ---------------- entries ----------------

    def homeContent(self, filter):
        return {"class": [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]}

    def homeVideoContent(self):
        html_text = self._fetch(self.host + "/")
        if not html_text:
            html_text = self._fetch(self.host)
        items = self._parse_cards(html_text, False)
        return {"list": items[:12]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        cid = str(tid or "").strip("/")
        is_feed = (cid == "feed_stream")
        if is_feed or cid in ("home_feed", "index", "home", ""):
            if page > 1:
                urls = [self.host + "/page/" + str(page) + "/",
                        self.host + "/index.php/page/" + str(page) + "/",
                        self.host + "/?page=" + str(page)]
            else:
                urls = [self.host + "/", self.host]
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
        items = self._parse_cards(html_text, False)
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
            title = clean_title_text(tm.group(1))
        desc = ""
        dm = re.search(r"<meta[^>]+name=['\"]description['\"][^>]+content=['\"]([^'\"]*)['\"]", html_text, re.I)
        if not dm:
            dm = re.search(r"<meta[^>]+property=['\"]og:description['\"][^>]+content=['\"]([^'\"]*)['\"]", html_text, re.I)
        if dm:
            desc = dm.group(1).strip()
        cover = ""
        cm = PIC_PATH_RE.search(html_text)
        if cm and "listzw" not in cm.group(1) and "placeholder" not in cm.group(1):
            cover = cm.group(1).strip()
        if not cover:
            mm = re.search(r"content=['\"]([^'\"]+\.(?:webp|jpg|png|jpeg)[^'\"]*)['\"]", html_text, re.I)
            if mm and "listzw" not in mm.group(1) and "placeholder" not in mm.group(1):
                cover = mm.group(1).strip()
        resolved_cover = self._resolve_pic(cover) if cover else ""
        if is_feed:
            return {"list": [self._feed_detail(raw_id, start_aid, title, desc, resolved_cover)]}
        video_urls = self._extract_video_urls(html_text)
        if not video_urls:
            pm = POST_BODY_RE.search(html_text)
            post_body = pm.group(1) if pm else html_text
            sub_targets = []
            seen_sub = set()
            for sm in SUB_LINK_RE.finditer(post_body):
                sub_id = sm.group(1)
                if sub_id == start_aid or sub_id in seen_sub or sub_id in AD_ID_BLACKLIST:
                    continue
                seen_sub.add(sub_id)
                sub_title = re.sub(r"[\$#\r\n\t]", "", re.sub(r"<[^>]+>", "", sm.group(2))).strip()
                label = sub_title[:20] if sub_title else ("TOP " + str(len(sub_targets)))
                sub_targets.append((sub_id, label))
                if len(sub_targets) >= 6:
                    break
            for sub_id, label in sub_targets:
                sub_html = self._fetch(self.host + "/archives/" + sub_id + "/")
                for u in self._extract_video_urls(sub_html):
                    video_urls.append(u)
        main_eps = []
        fb_eps = []
        for idx, url in enumerate(video_urls):
            ep_name = "现场实录" if len(video_urls) == 1 else "片段 " + ("0" + str(idx + 1) if idx + 1 < 10 else str(idx + 1))
            ep_name = ep_name.replace("$", "_").replace("#", "_")
            main_eps.append(ep_name + "$" + json.dumps({"playUrl": url, "aid": start_aid}, ensure_ascii=False))
            fb_eps.append(ep_name + "$" + json.dumps({"playUrl": url.replace("https://", "http://"), "aid": start_aid}, ensure_ascii=False))
        summary = self._brand_block()
        if desc:
            summary += "\n" + desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：718吃瓜",
                "片源：🦋 蝴蝶专线、🦋 备用直链",
                "编号：" + start_aid,
            ])
        remarks = "蝴蝶影视 | 共" + str(len(video_urls)) + "个片段" if len(video_urls) > 1 else "蝴蝶影视 | 现场实录"
        play_from = ""
        play_url = ""
        if main_eps:
            play_from = "🦋 蝴蝶专线$$$🦋 备用直链"
            play_url = "#".join(main_eps) + "$$$" + "#".join(fb_eps)
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
            "vod_play_from": play_from,
            "vod_play_url": play_url,
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
            if sec == "home_feed":
                url = self.host + "/page/" + str(r_page) + "/" if r_page > 1 else self.host + "/"
            else:
                url = self.host + "/category/" + sec + "/" + str(r_page) + "/" if r_page > 1 else self.host + "/category/" + sec + "/"
            s_html = self._fetch(url)
            if s_html:
                for card in self._parse_cards(s_html, False):
                    card_aid = card["vod_id"]
                    if card_aid not in seen and card_aid not in AD_ID_BLACKLIST:
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
                "分类：718吃瓜",
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
        headers = {"User-Agent": UA, "Referer": self.host + "/"}
        play_url = str(data.get("playUrl") or "")
        if data.get("feed") and data.get("aid"):
            aid = str(data["aid"])
            page_html = self._fetch(self.host + "/archives/" + aid + "/")
            urls = self._extract_video_urls(page_html)
            if urls:
                play_url = urls[0]
            if not play_url:
                return {"parse": 1, "url": self.host + "/archives/" + aid + "/", "header": headers}
        if not play_url:
            return {"parse": 1, "url": self.host + "/", "header": headers}
        return {"parse": 0, "url": play_url, "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249430001&sig=2d5d50d9f0bd86ad
