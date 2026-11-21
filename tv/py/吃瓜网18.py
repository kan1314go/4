# -*- coding: utf-8 -*-
# 吃瓜网 spider for FongMi / TVBox
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
BRAND_NAME = "吃瓜网"
DEFAULT_HOST = "https://cgw666.com"
DEFAULT_PIC_CDN = "https://pic.gyezbp.cn"
DEFAULT_WORKER = "https://chigua-img-proxy.yishengheqiu7679.workers.dev"
PAGE_SIZE = 20

CATEGORIES = [
    ("feed_stream", "🔥 沉浸连刷"),
    ("root_home", "全部最新"),
    ("jrxw1", "今日吃瓜"),
    ("mrcg", "吃瓜排行榜"),
    ("rsbl", "热搜吃瓜"),
    ("ztds", "每日大赛"),
    ("dycg", "网红黑料"),
    ("xyzt", "反差校花"),
    ("lljj", "海角乱伦"),
    ("bkrg", "必看大瓜"),
    ("meiritoupai", "激情偷拍"),
    ("guochanwanghuang", "网黄达人"),
    ("hwcg", "佳片有约"),
    ("djbl", "独家爆料"),
    ("lpzq", "AI剧场"),
    ("tanhuazhuanchang", "探花视频"),
    ("lgjp", "撸管精品"),
    ("chiyuan", "动漫乐园"),
    ("lqds", "猎奇吃瓜"),
    ("shehuiqiwen", "社会百科"),
    ("xiaoshuo", "私密小说"),
    ("worldcup", "体坛热闻"),
]
AD_KEYWORDS = ["重金求稿", "变现", "高价收购", "商务合作", "吃瓜导航", "我要投稿", "关于我们", "求瓜"]
FEED_POOL_CATS = ["jrxw1", "mrcg", "rsbl", "ztds", "dycg", "bkrg", "meiritoupai", "root_home", "djbl"]

BANNER_RE = re.compile(r"loadBannerDirect\(['\"]([^'\"]+)['\"]\s*,\s*['\"][^'\"]*['\"]\s*,\s*document\.querySelector\(['\"]#post-card-(\d+)['\"]\)", re.I)
XQBJ_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*xqbj-recommand[^\"']*[\"'][\s\S]*?</div>\s*</div>\s*</div>", re.I)
ASIDE_RE = re.compile(r"<aside[\s\S]*?</aside>", re.I)
WIDGET_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*(?:widget|sidebar)[^\"']*[\"'][^>]*>[\s\S]*?</div>", re.I)
POSTCARD_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*post-card[^\"']*[\"'][^>]*>[\s\S]*?</div>\s*</div>", re.I)
ANCHOR_CARD_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/archives/(\d+)/?[\"'][^>]*>([\s\S]*?)</a>", re.I)
CARD_ID_RE = re.compile(r"id=[\"']post-card-(\d+)[\"']", re.I)
ARCHIVES_ID_RE = re.compile(r"/archives/(\d+)/", re.I)
TITLE_H_RE = re.compile(r"<h[234][^>]*>([\s\S]*?)</h[234]>", re.I)
DATE_META_RE = re.compile(r"itemprop=[\"']datePublished[\"'][^>]+content=[\"'](\d{4}-\d{2}-\d{2})", re.I)
DATE_CN_RE = re.compile(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)")
DATE_ANY_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
TITLE_SUFFIX_RE = re.compile(r"\s*(?:热搜\s*HOT|HOT|置顶|独家|NEW|吃瓜\s*HOT|爆料\s*HOT)\s*$", re.I)
POST_BODY_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*post-content[^\"']*[\"'][^>]*>([\s\S]*?)(?:<div[^>]+class=[\"'][^\"']*(?:post-footer|post-tags|comments)[\"'][^>]*>|</article>)", re.I)
SUB_LINK_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/archives/(\d+)/?[\"'][^>]*>([\s\S]*?)</a>", re.I)
SUB_LINK_ID_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/archives/(\d+)/?[\"']", re.I)


def strip_tags(text):
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", str(text)).strip()


def clean_entities(raw):
    if not raw:
        return ""
    return (str(raw).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            .replace("&quot;", '"').replace("&#39;", "'"))


def clean_title(raw):
    if not raw:
        return ""
    t = clean_entities(strip_tags(raw))
    t = TITLE_SUFFIX_RE.sub("", t)
    return t.strip()


def clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw)
    clean = re.sub(r"\\u0068ttps", "https", clean)
    clean = re.sub(r"\\u0068ttp", "http", clean)
    clean = clean.replace("\\/", "/").strip()
    if clean.startswith("//"):
        clean = "https:" + clean
    return clean


def is_ad(text):
    if not text:
        return False
    s = str(text)
    for kw in AD_KEYWORDS:
        if kw in s:
            return True
    return False


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

    def _fetch_once(self, url, referer):
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = resp.read().decode("utf-8", "ignore")
                return body if body else ""
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "ignore")
            except Exception:
                body = ""
            return body if body else ""
        except Exception:
            return None

    def _fetch_path(self, path, referer=""):
        if path.startswith("//"):
            url = "https:" + path
        elif path.startswith("/"):
            url = self.host + path
        else:
            url = path
        result = self._fetch_once(url, referer)
        if result is None:
            if url.startswith("https://"):
                retry = self._fetch_once("http://" + url[8:], referer)
                return retry if retry else ""
            return ""
        return result

    # ---------------- posters ----------------

    def _normalize_pic(self, raw_pic):
        if not raw_pic:
            return ""
        p = clean_entities(raw_pic).strip().strip("'\"")
        if not p:
            return ""
        if ".svg" in p or p.startswith("data:image"):
            return ""
        if p.startswith("//"):
            return "https:" + p
        if p.startswith("http://") or p.startswith("https://"):
            return p
        if p.startswith("/upload") or p.startswith("upload"):
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
            return self.img_worker + "/?url=" + urllib.parse.quote(clean, safe="")
        return (clean + "@Referer=" + urllib.parse.quote(self.host + "/", safe="")
                + "&User-Agent=" + urllib.parse.quote(UA, safe=""))

    # ---------------- cards ----------------

    def _parse_cards(self, html_text, is_feed):
        html = str(html_text or "")
        items = []
        seen = set()
        banner_map = {}
        for bm in BANNER_RE.finditer(html):
            b_url = bm.group(1).strip()
            b_aid = bm.group(2).strip()
            if b_url and b_aid:
                banner_map[b_aid] = b_url
        clean = XQBJ_RE.sub("", html)
        clean = ASIDE_RE.sub("", clean)
        clean = WIDGET_RE.sub("", clean)
        blocks = [m.group(0) for m in POSTCARD_RE.finditer(clean)]
        if not blocks:
            blocks = [m.group(0) for m in ANCHOR_CARD_RE.finditer(clean)]
        for inner in blocks:
            if "xqbj-recommand" in inner or "swiper-slide" in inner:
                continue
            idm = CARD_ID_RE.search(inner) or ARCHIVES_ID_RE.search(inner)
            if not idm:
                continue
            aid = idm.group(1).strip()
            if aid in seen or aid == "139553":
                continue
            tm = TITLE_H_RE.search(inner)
            if tm and tm.group(1):
                title = clean_title(tm.group(1))
            else:
                raw_txt = strip_tags(inner)
                title = clean_title(raw_txt[:50]) if raw_txt else ("瓜圈热点 " + aid)
            if is_ad(title):
                continue
            seen.add(aid)
            post_date = ""
            dm = DATE_META_RE.search(inner)
            if dm and dm.group(1):
                post_date = dm.group(1).strip()
            else:
                cm = DATE_CN_RE.search(inner)
                if cm and cm.group(1):
                    post_date = re.sub(r"\s+", "", cm.group(1)).strip()
                else:
                    dm2 = DATE_ANY_RE.search(inner)
                    if dm2 and dm2.group(1):
                        post_date = dm2.group(1).strip()
            pic = banner_map.get(aid) or ""
            if not pic:
                m1 = re.search(r"loadBannerDirect\(['\"]([^'\"]+)['\"]", inner, re.I)
                if m1 and m1.group(1):
                    pic = m1.group(1).strip()
            if not pic:
                m2 = re.search(r"loadImage\(['\"]([^'\"]+)['\"]", inner, re.I)
                if m2 and m2.group(1):
                    pic = m2.group(1).strip()
            if not pic:
                m3 = re.search(r"data-src=[\"']([^\"']+)[\"']", inner, re.I)
                if m3 and m3.group(1) and "logo" not in m3.group(1):
                    pic = m3.group(1).strip()
            if not pic:
                m4 = re.search(r"(?:data-banner|data-bg|data-original)=[\"']([^\"']+)[\"']", inner, re.I)
                if m4 and m4.group(1):
                    pic = m4.group(1).strip()
            if not pic:
                m5 = re.search(r"url\([\"']?([^\"')]+)[\"']?\)", inner, re.I)
                if m5 and m5.group(1):
                    pic = m5.group(1).strip()
            if not pic:
                for m6 in re.finditer(r"src=[\"']([^\"']+)[\"']", inner, re.I):
                    cand = m6.group(1).strip() if m6.group(1) else ""
                    if cand and ".svg" not in cand and "logo" not in cand and "avatar" not in cand:
                        pic = cand
                        break
            if is_feed:
                remarks = "蝴蝶影视 | 连刷起播"
                vid = "feed@@" + aid
            else:
                remarks = "蝴蝶影视 | " + (post_date if post_date else "现场实录")
                vid = aid
            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._wrap_pic(pic),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.78},
            })
        return items

    # ---------------- episodes ----------------

    def _extract_episodes(self, html_text, prefix):
        html = str(html_text or "")
        episodes = []
        seen = set()

        def push(url):
            name = prefix + " " + ("0" + str(len(episodes) + 1) if len(episodes) + 1 < 10 else str(len(episodes) + 1))
            episodes.append((name, url))

        for m_cfg in re.finditer(r"data-config=([\"'])([\s\S]*?)\1", html, re.I):
            raw_cfg = clean_entities(m_cfg.group(2))
            v_url = ""
            try:
                cfg = json.loads(raw_cfg)
                if isinstance(cfg, dict):
                    video = cfg.get("video")
                    if isinstance(video, dict) and video.get("url"):
                        v_url = video["url"]
            except Exception:
                um = re.search(r"[\"']url[\"']\s*:\s*[\"']([^\"']+)[\"']", raw_cfg, re.I)
                if um and um.group(1):
                    v_url = um.group(1)
            v_url = clean_stream_url(v_url)
            if v_url and v_url not in seen and "logo" not in v_url:
                seen.add(v_url)
                push(v_url)
        if not episodes:
            for m_v in re.finditer(r"<video[^>]+>", html, re.I):
                tag = m_v.group(0)
                sm = re.search(r"(?:data-hls-src|data-src|src)=[\"']([^\"']+)[\"']", tag, re.I)
                if sm and sm.group(1):
                    s_url = clean_stream_url(sm.group(1))
                    if s_url and s_url not in seen:
                        seen.add(s_url)
                        push(s_url)
        if not episodes:
            for m_s in re.finditer(r"[\"'](https?:[\\/]+[^\"'\s]+\.(?:m3u8|mp4)[^\"'\s]*)[\"']", html, re.I):
                c_url = clean_stream_url(m_s.group(1))
                if c_url and c_url not in seen and "logo" not in c_url:
                    seen.add(c_url)
                    push(c_url)
        return episodes

    # ---------------- entries ----------------

    def homeContent(self, filter):
        return {"class": [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]}

    def homeVideoContent(self):
        html_text = self._fetch_path("/", "")
        items = self._parse_cards(html_text, False)
        return {"list": items[:12]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        is_feed = (tid == "feed_stream")
        if is_feed or tid == "root_home":
            path = "/page/" + str(page) + "/" if page > 1 else "/"
        else:
            path = "/category/" + str(tid) + "/" + str(page) + "/" if page > 1 else "/category/" + str(tid) + "/"
        html_text = self._fetch_path(path, "")
        items = self._parse_cards(html_text, is_feed)
        if is_feed and items:
            random.shuffle(items)
        return {"list": items, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        if not keyword or is_ad(keyword):
            return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": page * PAGE_SIZE}
        enc = urllib.parse.quote(keyword, safe="")
        path = "/search/" + enc + "/" + str(page) + "/" if page > 1 else "/search/" + enc + "/"
        html_text = self._fetch_path(path, "")
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
        if not start_aid:
            return {"list": [], "msg": "详情页加载失败，请稍后重试"}
        target_path = "/archives/" + start_aid + "/"
        html_text = self._fetch_path(target_path, self.host + "/")
        if not html_text:
            return {"list": [], "msg": "详情页加载失败，请稍后重试"}
        title = "瓜圈爆料 " + start_aid
        tm = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html_text, re.I)
        if tm and tm.group(1):
            title = clean_title(tm.group(1))
        desc = ""
        dm = re.search(r"<meta[^>]+name=[\"']description[\"'][^>]+content=[\"']([^\"']*)[\"']", html_text, re.I)
        if dm and dm.group(1):
            desc = dm.group(1).strip()
        cover = ""
        cm = re.search(r"loadBannerDirect\(['\"]([^'\"]+)['\"]", html_text, re.I)
        if cm and cm.group(1):
            cover = cm.group(1).strip()
        if not cover:
            cm2 = re.search(r"loadImage\(['\"]([^'\"]+)['\"]", html_text, re.I)
            if cm2 and cm2.group(1):
                cover = cm2.group(1).strip()
        if not cover:
            cm3 = re.search(r"<meta[^>]+property=[\"']og:image[\"'][^>]+content=[\"']([^\"']*)[\"']", html_text, re.I)
            if cm3 and cm3.group(1):
                cover = cm3.group(1).strip()
        resolved_cover = self._wrap_pic(cover) if cover else ""
        if is_feed:
            return {"list": [self._feed_detail(raw_id, start_aid, title, desc, resolved_cover)]}
        episodes = self._extract_episodes(html_text, "片段")
        if not episodes:
            pm = POST_BODY_RE.search(html_text)
            post_body = pm.group(1) if pm and pm.group(1) else html_text
            sub_tasks = []
            seen_sub = set()
            for sm in SUB_LINK_RE.finditer(post_body):
                sub_id = sm.group(1).strip() if sm.group(1) else ""
                sub_inner = sm.group(2) if sm.group(2) else ""
                if not sub_id or sub_id == start_aid or sub_id in seen_sub or sub_id == "139553":
                    continue
                seen_sub.add(sub_id)
                sub_title_raw = re.sub(r"[\$#\r\n\t]+", " ", strip_tags(sub_inner)).strip()
                count = len(seen_sub)
                label = sub_title_raw[:18] if sub_title_raw else ("TOP " + ("0" + str(count) if count < 10 else str(count)))
                sub_tasks.append((sub_id, label))
                if len(sub_tasks) >= 8:
                    break
            for sub_id, label in sub_tasks:
                sub_html = self._fetch_path("/archives/" + sub_id + "/", self.host + target_path)
                if sub_html:
                    for ep in self._extract_episodes(sub_html, label):
                        episodes.append(ep)
        if not episodes:
            episodes = [("现场图文/网页播放", self.host + target_path)]
            ep_values = [episodes[0][0].replace("$", "_").replace("#", "_") + "$" + json.dumps({"playUrl": episodes[0][1], "web": True}, ensure_ascii=False)]
        else:
            ep_values = [(name.replace("$", "_").replace("#", "_") + "$" + json.dumps({"playUrl": url}, ensure_ascii=False)) for name, url in episodes]
        summary = self._brand_block()
        if desc:
            summary += "\n" + desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：热搜爆料",
                "片源：🦋 蝴蝶专线",
                "编号：" + start_aid,
            ])
        remarks = "蝴蝶影视 | 共" + str(len(episodes)) + "个片段" if len(episodes) > 1 else "蝴蝶影视 | 正片实录"
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
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(ep_values),
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
                path = "/page/" + str(r_page) + "/" if r_page > 1 else "/"
            else:
                path = "/category/" + sec + "/" + str(r_page) + "/" if r_page > 1 else "/category/" + sec + "/"
            s_html = self._fetch_path(path, self.host + "/")
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
                "分类：热搜爆料",
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
            page_html = self._fetch_path("/archives/" + aid + "/", self.host + "/")
            if page_html:
                eps = self._extract_episodes(page_html, "正片")
                if eps:
                    play_url = eps[0][1]
                else:
                    for sm in SUB_LINK_ID_RE.finditer(page_html):
                        next_aid = sm.group(1)
                        if next_aid != aid and next_aid != "139553":
                            sub_html = self._fetch_path("/archives/" + next_aid + "/", self.host + "/")
                            if sub_html:
                                sub_eps = self._extract_episodes(sub_html, "正片")
                                if sub_eps:
                                    play_url = sub_eps[0][1]
                                    break
            if not play_url:
                return {"parse": 1, "url": self.host + "/archives/" + aid + "/", "header": headers}
        if data.get("web") or not play_url or not play_url.startswith("http"):
            fallback = play_url if (data.get("web") and play_url.startswith("http")) else self.host + "/"
            return {"parse": 1, "url": fallback, "header": headers}
        return {"parse": 0, "url": play_url, "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249543575&sig=7b1c6f32688a4576
