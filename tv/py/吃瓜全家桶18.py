# -*- coding: utf-8 -*-
# 吃瓜全家桶（八合一聚合） spider for FongMi / TVBox
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
BRAND_NAME = "吃瓜全家桶"
DEFAULT_IMG_WORKER = "https://chigua-img-proxy.yishengheqiu7679.workers.dev"
WORKER_1024 = "https://1024chigua.yishengheqiu7679.workers.dev"
WORKER_718 = "https://718haibao.peiqi192192.workers.dev/img"
PAGE_SIZE = 20
FEED_POOL = ["cgw", "cg1024", "cg51", "cg91", "cg718", "dycg", "ahl"]
SKIP_AIDS = {"139553", "14", "22245", "22877", "22747", "20261"}
STRICT_AD_KEYWORDS = [
    "重金求稿", "变现", "高价收购", "商务合作", "吃瓜导航", "我要投稿", "关于我们", "求瓜",
    "博业体育", "欧洲五大联赛", "澳门威尼斯", "威尼斯人", "89b.com", "7777.com", "bw55.co",
    "官方指定投注", "十年信誉", "1元起返", "约炮", "成人直播", "欲女的高潮", "欲女", "交友", "同城",
]

PLATFORMS = {
    "cgw": {
        "name": "🍉 吃瓜网", "host": "https://cgw666.com", "picCdn": "https://pic.gyezbp.cn",
        "worker": DEFAULT_IMG_WORKER, "type": "b2",
        "sections": [("全部最新", ""), ("今日吃瓜", "jrxw1"), ("吃瓜排行榜", "mrcg"), ("热搜吃瓜", "rsbl"), ("每日大赛", "ztds"), ("网红黑料", "dycg"), ("反差校花", "xyzt"), ("海角乱伦", "lljj"), ("必看大瓜", "bkrg"), ("激情偷拍", "meiritoupai"), ("网黄达人", "guochanwanghuang"), ("佳片有约", "hwcg"), ("独家爆料", "djbl"), ("AI剧场", "lpzq"), ("探花视频", "tanhuazhuanchang"), ("撸管精品", "lgjp"), ("动漫乐园", "chiyuan"), ("猎奇吃瓜", "lqds"), ("社会百科", "shehuiqiwen"), ("私密小说", "xiaoshuo"), ("体坛热闻", "worldcup")],
    },
    "cg1024": {
        "name": "🍉 1024吃瓜", "host": "https://1024cg.com", "picCdn": "https://pic.gyezbp.cn",
        "worker": WORKER_1024, "type": "b2",
        "sections": [("全部最新", ""), ("吃瓜日报", "cgkx"), ("每日大赛", "mrds"), ("AI短剧", "aidj"), ("海角乱伦", "hjll"), ("AV剧场", "crxs"), ("校园大瓜", "xsxy"), ("热门事件", "mrdg"), ("网红明星", "whmx"), ("反差黑料", "hwcg"), ("原创大神", "wyfl"), ("暗网资讯", "lqtj"), ("吃瓜精选", "jxdg"), ("成人动漫", "crdm"), ("看片精选", "kpjx")],
    },
    "cg51": {
        "name": "🍉 51吃瓜", "host": "https://51cg1.com", "picCdn": "https://pic.gyezbp.cn",
        "worker": DEFAULT_IMG_WORKER, "type": "b2",
        "sections": [("全部最新", ""), ("今日吃瓜", "wpcz"), ("AI成人短剧", "cbdj"), ("每日大赛", "mrds"), ("网黄合集", "whhj"), ("吃瓜榜单", "mrdg"), ("瓜友点播", "qghj"), ("热门大瓜", "rdsj"), ("必看大瓜", "bkdg"), ("成人视频", "ysyl"), ("伦理道德", "lldd"), ("国产视频", "gcjq"), ("探花精选", "thjx"), ("学生校园", "xsxy"), ("网红黑料", "whhl"), ("骚男骚女", "snsn"), ("明星爆料", "whmx"), ("海外吃瓜", "hwcg"), ("人人吃瓜", "rrcg"), ("领导干部", "ldcg"), ("软萌甜妹", "jpll"), ("竞技吃瓜", "sjb"), ("吃瓜看戏", "qubk"), ("擦边撩骚", "dcbq"), ("性爱技巧", "zzs"), ("吃瓜新闻", "cgxw"), ("原创博主", "yczq"), ("51剧场", "51djc")],
    },
    "cg91": {
        "name": "🍉 91吃瓜", "host": "https://www.91cg1.com", "picCdn": "https://pic.hdhwqx.cn",
        "worker": DEFAULT_IMG_WORKER, "type": "b2",
        "sections": [("全部最新", ""), ("今日吃瓜", "zxcghl"), ("AI短剧", "dydj"), ("ST精选", "stjx"), ("每日大赛", "mrds"), ("自拍偷拍", "zptp"), ("最高点击", "rsdg"), ("深夜撸片", "lpsd"), ("海角乱伦", "hjll"), ("91探花", "91th"), ("成人动漫", "crdm"), ("91周榜", "zdtop"), ("91月榜", "ydtop"), ("必吃大瓜", "bcdg"), ("网红黑料", "whhl"), ("明星黑料", "mxhl"), ("社会奇闻", "qwys"), ("师生专栏", "xsjlb"), ("反差靓女", "fclv"), ("投稿求瓜", "tgqg"), ("网黄合集", "gcwh"), ("明星AI", "aikj"), ("体育直播", "sports-live"), ("猎奇重口", "lqzk")],
    },
    "cg718": {
        "name": "🍉 718吃瓜", "host": "https://www.718yule.com", "picCdn": "",
        "worker": WORKER_718, "type": "b2_718",
        "sections": [("全部最新", ""), ("每日吃瓜", "daily-gossip"), ("热门吃瓜", "top-stories"), ("反差婊曝光", "contrast-reveal"), ("吃瓜TOP榜", "week-top"), ("网黄合集", "sexbook"), ("AI成人短剧", "AINSFW"), ("抖音网红瓜", "internet-celebrities"), ("社会热瓜", "trending-news"), ("微密圈", "model-photos"), ("福利姬", "fuli"), ("娱乐吃瓜", "celebrity-scandals"), ("娱乐圈爆料", "entertainment-news")],
    },
    "dycg": {
        "name": "🍉 抖音吃瓜", "host": "https://dychigua.com", "picCdn": "https://pic.gyezbp.cn",
        "worker": WORKER_1024, "type": "b2",
        "sections": [("全部最新", ""), ("今日推荐", "newUpdate"), ("混剪PMV", "rmdg"), ("主题大赛", "hwcg"), ("热搜吃瓜", "hjll"), ("网红黑料", "whmx"), ("校园学生", "xsxy"), ("每日大赛", "fcmg"), ("声控ASMR", "snsn"), ("网黄合集", "tqzj"), ("原创投稿", "shsj"), ("福利看片", "flkp"), ("cos写真", "qqbk")],
    },
    "ahl": {
        "name": "🍉 爱黑料", "host": "https://aiheiliao1.com", "picCdn": "",
        "worker": "", "type": "b2",
        "sections": [("全部最新", ""), ("今日吃瓜", "newUpdate"), ("热门大瓜", "rmdg"), ("黑料大事件", "hwcg"), ("网红明星", "whmx"), ("学生校园", "xsxy"), ("反差母狗", "fcmg"), ("偷情抓奸", "tqzj"), ("社会事件", "shsj"), ("福利看片", "flkp")],
    },
    "dj57": {
        "name": "🍉 57吃瓜", "host": "https://57duanju.org", "cgHost": "https://57cg4.com", "picCdn": "",
        "worker": "", "type": "dj57",
        "sections": [("全部最新", ""), ("成人AI短剧", "aichengduanju"), ("热门精选", "hot"), ("今日吃瓜", "jrcg"), ("每日大赛", "mrds"), ("网红黑料", "wanghong"), ("网黄合集", "video"), ("出轨劈腿", "cheating"), ("直播擦边", "live"), ("社会事件", "society"), ("明星八卦", "star"), ("全部短剧", "all")],
    },
}
PLATFORM_ORDER = ["cgw", "cg1024", "cg51", "cg91", "cg718", "dycg", "ahl", "dj57"]

TITLE_SUFFIX_RE = re.compile(r"\s*(?:热搜\s*HOT|HOT|置顶|独家|NEW|吃瓜\s*HOT|爆料\s*HOT|\|\s*吃瓜718)\s*$", re.I)
BANNER_RE = re.compile(r"loadBannerDirect\(['\"]([^'\"]+)['\"]\s*,\s*['\"][^'\"]*['\"]\s*,\s*document\.querySelector\(['\"]#post-card-(\d+)['\"]\)")
XQBJ_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*xqbj-recommand[^\"']*[\"'][\s\S]*?</div>\s*</div>\s*</div>", re.I)
ASIDE_RE = re.compile(r"<aside[\s\S]*?</aside>", re.I)
WIDGET_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*(?:widget|sidebar)[^\"']*[\"'][^>]*>[\s\S]*?</div>", re.I)
ARTICLE_RE = re.compile(r"<article[^>]*>([\s\S]*?)</article>", re.I)
POSTCARD_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*post-card[^\"']*[\"'][^>]*>[\s\S]*?</div>\s*</div>", re.I)
DJ57_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/events/(\d+)/?[\"'][^>]*>([\s\S]*?)</a>", re.I)
CARD_ID_RE = re.compile(r"id=[\"']post-card-(\d+)[\"']", re.I)
ARCHIVES_ID_RE = re.compile(r"/archives/(\d+)/", re.I)
TITLE_H_RE = re.compile(r"<h[234][^>]*class=[\"'][^\"']*post-card-title[^\"']*[\"'][^>]*>([\s\S]*?)</h[234]>", re.I)
TITLE_H_ANY_RE = re.compile(r"<h[234][^>]*>([\s\S]*?)</h[234]>", re.I)
DATE_META_RE = re.compile(r"itemprop=[\"'](?:datePublished|dateModified)[\"'][^>]+content=[\"'](\d{4}-\d{2}-\d{2})", re.I)
DATE_ANY_RE = re.compile(r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})")
SUB_LINK_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/(?:archives|events)/(\d+)/?[\"'][^>]*>([\s\S]*?)</a>", re.I)
SUB_LINK_ID_RE = re.compile(r"<a[^>]+href=[\"'](?:https?://[^/]+)?/(?:archives|events)/(\d+)/?[\"']", re.I)
POST_BODY_RE = re.compile(r"<div[^>]+class=[\"'][^\"']*post-content[^\"']*[\"'][^>]*>([\s\S]*?)(?:<div[^>]+class=[\"'][^\"']*(?:post-footer|post-tags|comments)[\"'][^>]*>|</article>)", re.I)


def strip_tags(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(text))).strip()


def clean_title(raw):
    if not raw:
        return ""
    t = strip_tags(raw)
    t = (t.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
         .replace("&quot;", '"').replace("&#039;", "'").replace("&#39;", "'").replace("&nbsp;", " "))
    t = TITLE_SUFFIX_RE.sub("", t)
    return t.strip()


def clean_stream_url(raw):
    if not raw:
        return ""
    clean = str(raw)
    clean = re.sub(r"\\u0068ttps", "https", clean, flags=re.I)
    clean = re.sub(r"\\u0068ttp", "http", clean, flags=re.I)
    clean = clean.replace("\\/", "/").replace('\\"', '"')
    clean = re.sub(r"\\u0026", "&", clean, flags=re.I)
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
        self.host = PLATFORMS["cgw"]["host"]
        self.img_worker = DEFAULT_IMG_WORKER

    def init(self, extend=""):
        self.img_worker = DEFAULT_IMG_WORKER
        if extend:
            try:
                data = json.loads(extend)
                if isinstance(data, dict):
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
            "Referer": referer if referer else (url + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
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

    def _fetch(self, url, referer=""):
        if not url:
            return ""
        result = self._fetch_once(url, referer)
        if result is None:
            if url.startswith("https://"):
                retry = self._fetch_once("http://" + url[8:], referer)
                return retry if retry else ""
            return ""
        return result

    # ---------------- posters ----------------

    def _format_poster(self, raw_pic, platform):
        if not raw_pic:
            return ""
        p = str(raw_pic).strip().strip("'\"").replace("&amp;", "&")
        if not p:
            return ""
        if platform["type"] == "b2_718":
            p = re.sub(r"^https?://[^/]+/", "", p).lstrip("/")
            worker = platform.get("worker") or WORKER_718
            return worker + "/" + p
        host = platform["host"]
        pic_cdn = platform.get("picCdn") or "https://pic.gyezbp.cn"
        if p.startswith("//"):
            p = "https:" + p
        elif p.startswith("http://") or p.startswith("https://"):
            pass
        elif (p.startswith("/upload") or p.startswith("upload") or p.startswith("/image")
              or p.startswith("image") or p.startswith("/hc") or p.startswith("hc")):
            if not p.startswith("/"):
                p = "/" + p
            p = pic_cdn + p
        elif p.startswith("/"):
            p = host + p
        worker_url = platform.get("worker") or self.img_worker
        pid = self._pid(platform)
        if worker_url and pid not in ("ahl", "dj57"):
            return worker_url + "/?url=" + urllib.parse.quote(p, safe="")
        if pid == "dj57":
            return (p + "@Referer=" + urllib.parse.quote(host + "/", safe="")
                    + "&User-Agent=" + urllib.parse.quote(UA, safe=""))
        return p

    # ---------------- cards ----------------

    def _extract_card_pic(self, inner):
        m = re.search(r"loadBannerDirect\s*\(\s*['\"]([^'\"]+)['\"]", inner, re.I)
        if m and "img-placeholder" not in m.group(1):
            return m.group(1).strip()
        m = re.search(r"loadImage\s*\(\s*['\"]([^'\"]+)['\"]", inner, re.I)
        if m and "img-placeholder" not in m.group(1):
            return m.group(1).strip()
        for attr in ["data-banner", "data-src", "data-original", "data-bg", "data-pic", "content"]:
            m = re.search(attr + r"=[\"']([^\"']+)[\"']", inner, re.I)
            if m and "img-placeholder" not in m.group(1) and "logo" not in m.group(1) and ".svg" not in m.group(1):
                return m.group(1).strip()
        m = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", inner, re.I)
        if m and "img-placeholder" not in m.group(1) and "logo" not in m.group(1) and "avatar" not in m.group(1):
            return m.group(1).strip()
        return ""

    def _short_name(self, platform):
        return platform["name"].replace("🍉 ", "")

    def _parse_cards(self, html_text, platform, is_feed):
        if not html_text:
            return []
        items = []
        seen = set()
        if platform["type"] == "dj57":
            for m in DJ57_RE.finditer(html_text):
                aid = m.group(1)
                inner = m.group(2)
                if not aid or aid in seen:
                    continue
                seen.add(aid)
                tm = re.search(r"<h[23][^>]*>([\s\S]*?)</h[23]>", inner, re.I)
                name = clean_title(tm.group(1)) if tm else clean_title(inner)
                if not name:
                    name = "短剧热点 " + aid
                im = re.search(r"<img[^>]+src=[\"']([^\"']+)[\"']", inner, re.I)
                pic = im.group(1).strip() if im else ""
                items.append({
                    "vod_id": self._pid(platform) + "@@" + aid,
                    "vod_name": name,
                    "vod_pic": self._format_poster(pic, platform),
                    "vod_remarks": self._short_name(platform) + " | 正片",
                    "style": {"type": "rect", "ratio": 1.78},
                })
            return items
        banner_map = {}
        for bm in BANNER_RE.finditer(html_text):
            banner_map[bm.group(2)] = bm.group(1)
        clean = XQBJ_RE.sub("", html_text)
        clean = ASIDE_RE.sub("", clean)
        clean = WIDGET_RE.sub("", clean)
        blocks = [m.group(1) for m in ARTICLE_RE.finditer(clean)]
        if not blocks:
            blocks = [m.group(0) for m in POSTCARD_RE.finditer(clean)]
        for inner in blocks:
            if ("post-card-ads" in inner or "ad-card" in inner or "ad-item" in inner
                    or 'itemprop="sponsor"' in inner or 'rel="sponsored nofollow"' in inner
                    or "_czc.push" in inner or "sticky" in inner or "post-sticky" in inner):
                continue
            idm = CARD_ID_RE.search(inner) or ARCHIVES_ID_RE.search(inner)
            if not idm:
                continue
            aid = idm.group(1).strip()
            if aid in seen or aid in SKIP_AIDS:
                continue
            tm = TITLE_H_RE.search(inner) or TITLE_H_ANY_RE.search(inner)
            raw_title = ""
            if tm:
                raw_title = tm.group(1)
                cut = re.search(r"<div|<span|<p", raw_title, re.I)
                if cut:
                    raw_title = raw_title[:cut.start()]
            name = clean_title(raw_title)
            if not name or "display-none" in name:
                continue
            has_ad = False
            for kw in STRICT_AD_KEYWORDS:
                if kw in name or kw in inner:
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
                dm2 = DATE_ANY_RE.search(inner)
                if dm2:
                    post_date = dm2.group(1).strip()
            pic = self._extract_card_pic(inner)
            if not pic and aid in banner_map:
                pic = banner_map[aid]
            if is_feed:
                remarks = "🍉 连刷起播"
                vid = "feed@@" + self._pid(platform) + "@@" + aid
            else:
                remarks = self._short_name(platform) + " | " + (post_date if post_date else "现场实录")
                vid = self._pid(platform) + "@@" + aid
            items.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": self._format_poster(pic, platform),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.78},
            })
        return items

    def _pid(self, platform):
        for key, plat in PLATFORMS.items():
            if plat is platform:
                return key
        return "cgw"

    # ---------------- video extraction ----------------

    def _extract_video_urls(self, html_text):
        if not html_text:
            return []
        seen = set()
        result = []

        def push(val):
            cval = clean_stream_url(val)
            if cval and cval not in seen and "logo" not in cval.lower():
                seen.add(cval)
                result.append(cval)

        m_container = (re.search(r"id=[\"']article-videos[\"'][^>]+data-url=([\"'])([\s\S]*?)\1", html_text, re.I)
                       or re.search(r"data-url=([\"'])([\s\S]*?)\1", html_text, re.I))
        if m_container and m_container.group(2):
            raw_val = entity_decode(m_container.group(2)).strip()
            video_list = []
            if raw_val.startswith("["):
                try:
                    parsed = json.loads(raw_val)
                    if isinstance(parsed, list):
                        video_list = parsed
                except Exception:
                    video_list = re.findall(r"https?://[^\s\"'<>]+", raw_val)
            elif raw_val:
                video_list = [raw_val]
            for v in video_list:
                if isinstance(v, str):
                    push(v)
        if not result:
            for m_cfg in re.finditer(r"data-config=([\"'])([\s\S]*?)\1", html_text, re.I):
                raw_cfg = entity_decode(m_cfg.group(2))
                v_url = ""
                try:
                    parsed = json.loads(raw_cfg)
                    if isinstance(parsed, dict):
                        video = parsed.get("video")
                        if isinstance(video, dict) and video.get("url"):
                            v_url = video["url"]
                        if not v_url and parsed.get("url"):
                            v_url = parsed["url"]
                        if not v_url and parsed.get("url2"):
                            v_url = parsed["url2"]
                except Exception:
                    um = re.search(r"[\"']url2?[\"']\s*:\s*[\"']([^\"']+)[\"']", raw_cfg, re.I)
                    if um:
                        v_url = um.group(1)
                if v_url:
                    push(v_url)
        if not result:
            for m_v in re.finditer(r"<video([^>]+)>", html_text, re.I):
                attr = m_v.group(1)
                hm = re.search(r"(?:data-hls-src|data-src|src)=[\"']([^\"']+)[\"']", attr, re.I)
                if hm:
                    cval = clean_stream_url(hm.group(1))
                    if cval and cval not in seen:
                        seen.add(cval)
                        result.append(cval)
        if not result:
            for m_s in re.finditer(r"[\"'](https?:[\\/]+[^\"'\s]+\.(?:m3u8|mp4)[^\"'\s]*)[\"']", html_text, re.I):
                push(m_s.group(1))
        return result

    # ---------------- entries ----------------

    def homeContent(self, filter):
        classes = [{"type_id": "feed_stream", "type_name": "🔥 全网连刷"}]
        filters = {}
        for pid in PLATFORM_ORDER:
            plat = PLATFORMS[pid]
            classes.append({"type_id": pid, "type_name": plat["name"]})
            filters[pid] = [{
                "key": "section", "name": "专区板块", "init": "",
                "value": [{"n": sec_name, "v": sec_val} for sec_name, sec_val in plat["sections"]],
            }]
        result = {"class": classes}
        if filter:
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        plat = PLATFORMS["cgw"]
        html_text = self._fetch(plat["host"] + "/", plat["host"])
        items = self._parse_cards(html_text, plat, False)
        return {"list": items[:12]}

    def categoryContent(self, tid, pg, filter, extend):
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        section = ""
        if extend and isinstance(extend, dict):
            section = str(extend.get("section") or "").strip()
        if tid == "feed_stream":
            pkey = FEED_POOL[(page - 1) % len(FEED_POOL)]
            plat = PLATFORMS[pkey]
            url = plat["host"] + "/page/" + str(page) + "/" if page > 1 else plat["host"] + "/"
            html_text = self._fetch(url, plat["host"])
            items = self._parse_cards(html_text, plat, True)
            random.shuffle(items)
            return {"list": items, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}
        plat = PLATFORMS.get(tid) or PLATFORMS["cgw"]
        if plat["type"] == "dj57":
            if section in ("", "aichengduanju", "hot"):
                phost = plat["host"]
            else:
                phost = plat["cgHost"]
            if section == "":
                url = phost + "/page/" + str(page) + "/" if page > 1 else phost + "/"
            else:
                url = phost + "/" + section + "/" + str(page) + "/" if page > 1 else phost + "/" + section + "/"
        else:
            if section == "":
                url = plat["host"] + "/page/" + str(page) + "/" if page > 1 else plat["host"] + "/"
            else:
                url = plat["host"] + "/category/" + section + "/" + str(page) + "/" if page > 1 else plat["host"] + "/category/" + section + "/"
        html_text = self._fetch(url, plat["host"])
        items = self._parse_cards(html_text, plat, False)
        return {"list": items, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}

    def searchContent(self, key, quick, pg="1"):
        keyword = str(key or "").strip()
        page = int(pg) if str(pg).isdigit() else 1
        if page < 1:
            page = 1
        if not keyword:
            return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": page * PAGE_SIZE}
        enc = urllib.parse.quote(keyword, safe="")
        all_items = []
        seen_titles = set()
        for pid in PLATFORM_ORDER:
            plat = PLATFORMS[pid]
            url = plat["host"] + "/search/" + enc + "/" + str(page) + "/" if page > 1 else plat["host"] + "/search/" + enc + "/"
            html_text = self._fetch(url, plat["host"])
            if html_text:
                for item in self._parse_cards(html_text, plat, False):
                    if item["vod_name"] not in seen_titles:
                        seen_titles.add(item["vod_name"])
                        all_items.append(item)
        return {"list": all_items, "page": page, "pagecount": page + 1, "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}

    # ---------------- detail ----------------

    def _brand_block(self, host):
        lines = [
            "🦋 " + BRAND_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _detail_url(self, plat, aid):
        if plat["type"] == "dj57":
            return plat["host"] + "/events/" + aid + "/"
        return plat["host"] + "/archives/" + aid + "/"

    def _fetch_detail_html(self, plat, aid):
        url = self._detail_url(plat, aid)
        html_text = self._fetch(url, plat["host"])
        if not html_text and plat["type"] == "dj57":
            url = plat["cgHost"] + "/events/" + aid + "/"
            html_text = self._fetch(url, plat["host"])
        return html_text, url

    def detailContent(self, ids):
        raw_id = str(ids[0]) if ids else ""
        is_feed = False
        if raw_id.startswith("feed@@"):
            is_feed = True
            segs = raw_id[6:].split("@@")
            pid = segs[0] if segs else "cgw"
            aid = segs[1] if len(segs) > 1 else ""
        else:
            segs = raw_id.split("@@")
            if len(segs) > 1:
                pid = segs[0]
                aid = segs[1]
            else:
                pid = "cgw"
                aid = segs[0]
        aid = aid.strip("/")
        plat = PLATFORMS.get(pid) or PLATFORMS["cgw"]
        pid = self._pid(plat)
        html_text, target_url = self._fetch_detail_html(plat, aid)
        title = self._short_name(plat) + " " + aid
        tm = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html_text, re.I)
        if tm and tm.group(1):
            title = clean_title(tm.group(1))
        desc = ""
        dm = re.search(r"<meta[^>]+name=[\"'](?:description|og:description)[\"'][^>]+content=[\"']([^\"']*)[\"']", html_text, re.I)
        if dm:
            desc = dm.group(1).strip()
        cover = self._format_poster(self._extract_card_pic(html_text), plat)
        if is_feed:
            return {"list": [self._feed_detail(raw_id, plat, pid, aid, title, desc, cover, target_url)]}
        video_urls = self._extract_video_urls(html_text)
        if not video_urls:
            pm = POST_BODY_RE.search(html_text)
            post_body = pm.group(1) if pm else html_text
            seen_sub = set()
            sub_ids = []
            for sm in SUB_LINK_RE.finditer(post_body):
                sid = sm.group(1).strip()
                if sid == aid or sid in seen_sub or sid == "139553":
                    continue
                seen_sub.add(sid)
                sub_ids.append(sid)
                if len(sub_ids) >= 6:
                    break
            for sid in sub_ids:
                s_html = self._fetch(plat["host"] + "/archives/" + sid + "/", plat["host"])
                for u in self._extract_video_urls(s_html):
                    video_urls.append(u)
                if len(video_urls) >= 10:
                    break
        main_eps = []
        fb_eps = []
        for idx, v_url in enumerate(video_urls):
            ep_num = idx + 1
            ep_name = "现场实录" if len(video_urls) == 1 else "片段 " + ("0" + str(ep_num) if ep_num < 10 else str(ep_num))
            ep_name = ep_name.replace("$", "_").replace("#", "_")
            main_eps.append(ep_name + "$" + json.dumps({"platformId": pid, "playUrl": v_url}, ensure_ascii=False))
            fb_eps.append(ep_name + "$" + json.dumps({"platformId": pid, "playUrl": v_url.replace("https://", "http://")}, ensure_ascii=False))
        summary = self._brand_block(plat["host"])
        if desc:
            summary += "\n" + desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：" + self._short_name(plat),
                "片源：🦋 蝴蝶专线、⚡ 备用线路 (HTTP)",
                "编号：" + aid,
            ])
        remarks = "蝴蝶影视 | 共" + str(len(video_urls)) + "个切片" if len(video_urls) > 1 else "蝴蝶影视 | 现场实录"
        vod = {
            "vod_id": raw_id,
            "vod_name": title,
            "vod_pic": cover,
            "vod_bg": cover,
            "vod_background": cover,
            "vod_banner": cover,
            "vod_remarks": remarks,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_content": summary,
            "vod_play_from": "🦋 蝴蝶专线$$$⚡ 备用线路 (HTTP)",
            "vod_play_url": "#".join(main_eps) + "$$$" + "#".join(fb_eps),
        }
        return {"list": [vod]}

    def _feed_detail(self, raw_id, plat, pid, aid, title, desc, cover, target_url):
        episodes = []
        first_name = ("01 · " + title).replace("$", "_").replace("#", "_")
        episodes.append(first_name + "$" + json.dumps({"platformId": pid, "aid": aid, "feed": True}, ensure_ascii=False))
        pool = list(FEED_POOL)
        random.shuffle(pool)
        sampled = pool[:3]
        targets = []
        seen_aids = {aid}
        for sp_key in sampled:
            sp = PLATFORMS[sp_key]
            r_page = random.randint(1, 3)
            s_url = sp["host"] + "/page/" + str(r_page) + "/" if r_page > 1 else sp["host"] + "/"
            s_html = self._fetch(s_url, sp["host"])
            if s_html:
                for card in self._parse_cards(s_html, sp, False):
                    c_aid = card["vod_id"].split("@@")[-1]
                    if c_aid and c_aid not in seen_aids:
                        seen_aids.add(c_aid)
                        targets.append({"platformId": sp_key, "aid": c_aid, "title": card["vod_name"]})
            if len(targets) >= 70:
                break
        random.shuffle(targets)
        for t in targets:
            seq = len(episodes) + 1
            seq_str = "0" + str(seq) if seq < 10 else str(seq)
            p_tag = self._short_name(PLATFORMS[t["platformId"]])
            ep_name = (seq_str + " · [" + p_tag + "] " + t["title"]).replace("$", "_").replace("#", "_")
            episodes.append(ep_name + "$" + json.dumps({"platformId": t["platformId"], "aid": t["aid"], "feed": True}, ensure_ascii=False))
        summary = self._brand_block(plat["host"])
        if desc:
            summary += "\n" + desc
        else:
            summary += "\n" + "\n".join([
                "标题：" + title,
                "分类：" + self._short_name(plat),
                "片源：🦋 沉浸连刷专线",
                "编号：" + aid,
            ])
        return {
            "vod_id": raw_id,
            "vod_name": "🔥 全网连刷·" + title,
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
        pid = str(data.get("platformId") or "cgw")
        plat = PLATFORMS.get(pid) or PLATFORMS["cgw"]
        play_url = str(data.get("playUrl") or "").strip()
        if data.get("feed") and data.get("aid"):
            aid = str(data["aid"])
            page_html, page_url = self._fetch_detail_html(plat, aid)
            urls = self._extract_video_urls(page_html)
            if urls:
                play_url = urls[0]
            else:
                for sm in SUB_LINK_ID_RE.finditer(page_html):
                    next_aid = sm.group(1)
                    if next_aid != aid and next_aid != "139553":
                        if plat["type"] == "dj57":
                            sub_url = plat["host"] + "/events/" + next_aid + "/"
                        else:
                            sub_url = plat["host"] + "/archives/" + next_aid + "/"
                        sub_html = self._fetch(sub_url, plat["host"])
                        sub_urls = self._extract_video_urls(sub_html)
                        if sub_urls:
                            play_url = sub_urls[0]
                            break
                if not play_url:
                    return {"parse": 1, "url": page_url, "header": {"User-Agent": UA, "Referer": plat["host"] + "/"}}
        play_url = clean_stream_url(play_url)
        if not play_url:
            return {"parse": 1, "url": plat["host"] + "/", "header": {"User-Agent": UA, "Referer": plat["host"] + "/"}}
        return {"parse": 0, "url": play_url, "header": {"User-Agent": UA, "Referer": plat["host"] + "/"}}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249523565&sig=ae689d97c2d9a656
