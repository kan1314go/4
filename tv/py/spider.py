# -*- coding: utf-8 -*-
"""黄桃短剧 aihuangdou.com CatVod/TVBox Python Spider.

仅使用站点公开页面、公开分类/搜索页面和播放页提供的公开播放接口。
不绕过登录、验证码、付费内容或 robots.txt 禁止的管理/API 区域。
依赖 Python 3.8+ 标准库，兼容 CatVod 的 homeContent 等接口命名。
"""
import gzip
import html
import json
import logging
import re
import threading
import time
from collections import OrderedDict
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urljoin, urlparse
from urllib.request import HTTPRedirectHandler, HTTPCookieProcessor, Request, build_opener

CONFIG = {
    "name": "黄桃短剧",
    "version": "1.0.0",
    "base_url": "https://aihuangdou.com",
    "timeout": 15,
    "max_retries": 3,
    "cache_ttl": 300,
    "cache_size": 128,
    "page_size": 20,
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(CONFIG["name"])


class TTLCache:
    def __init__(self, maxsize=128, ttl=300):
        self.maxsize, self.ttl = maxsize, ttl
        self.items = OrderedDict()
        self.lock = threading.RLock()

    def get(self, key):
        with self.lock:
            item = self.items.get(key)
            if not item:
                return None
            if item[0] <= time.monotonic():
                self.items.pop(key, None)
                return None
            self.items.move_to_end(key)
            return item[1]

    def set(self, key, value, ttl=None):
        with self.lock:
            self.items[key] = (time.monotonic() + (self.ttl if ttl is None else ttl), value)
            self.items.move_to_end(key)
            while len(self.items) > self.maxsize:
                self.items.popitem(last=False)


class Parser:
    CARD_RE = re.compile(r'<article[^>]+class="drama-card"[^>]*>(.*?)</article>', re.I | re.S)
    HREF_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>', re.I)
    IMG_RE = re.compile(r'<img[^>]+(?:data-src|src)=["\']([^"\']+)["\'][^>]*>', re.I)
    H3_RE = re.compile(r'<h3[^>]*>(.*?)</h3>', re.I | re.S)
    TEXT_RE = re.compile(r'<[^>]+>')

    @classmethod
    def clean(cls, value):
        return re.sub(r"\s+", " ", cls.TEXT_RE.sub(" ", html.unescape(value or ""))).strip()

    @classmethod
    def cards(cls, body, base):
        out, seen = [], set()
        for raw in cls.CARD_RE.findall(body):
            href = next((x for x in cls.HREF_RE.findall(raw) if re.search(r"/drama/\d+/?$", x)), "")
            if not href:
                continue
            url = urljoin(base, href)
            if url in seen:
                continue
            seen.add(url)
            title_match = cls.H3_RE.search(raw)
            title = cls.clean(title_match.group(1)) if title_match else ""
            if not title:
                aria = re.search(r'alt="《([^"】]+)', raw)
                title = cls.clean(aria.group(1)) if aria else "未命名"
            image = re.search(r'<img[^>]+data-src=["\']([^"\']+)["\'][^>]*>', raw, re.I)
            if not image:
                image = re.search(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', raw, re.I)
            pic = urljoin(base, image.group(1)) if image else ""
            ep = re.search(r"(?:更新至|共|全)\s*(\d+)\s*集", cls.clean(raw))
            out.append({"vod_id": url, "vod_name": title, "vod_pic": pic,
                        "vod_remarks": ("至%s集" % ep.group(1)) if ep else ""})
        return out

    @staticmethod
    def play_data(body):
        match = re.search(r'<script[^>]+id=["\']ninePlayData["\'][^>]*>(.*?)</script>', body, re.I | re.S)
        if not match:
            return {}
        try:
            return json.loads(html.unescape(match.group(1).strip()))
        except (TypeError, ValueError):
            return {}

    @classmethod
    def episode_urls(cls, body, base, drama_id=None):
        result, seen = [], set()
        for href, label in re.findall(r'<a[^>]+href=["\']([^"\']*/video/\d+(?:/\d+)?/?)["\'][^>]*[^>]*>(.*?)</a>', body, re.I | re.S):
            url = urljoin(base, href)
            if drama_id and not re.search(r"/video/%s(?:/|$)" % re.escape(str(drama_id)), url):
                continue
            if url in seen:
                continue
            seen.add(url)
            match = re.search(r"/video/\d+/(\d+)/?$", url)
            number = int(match.group(1)) if match else 1
            result.append((number, "第%d集" % number, url))
        result.sort(key=lambda x: x[0])
        return result


class Spider:
    def __init__(self):
        self.session = None
        self.cache = TTLCache(CONFIG["cache_size"], CONFIG["cache_ttl"])
        self.lock = threading.RLock()
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Linux; Android 12) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
            "Accept-Encoding": "gzip",
            "Connection": "close",
        }

    def init(self, kwargs=None):
        if isinstance(kwargs, str):
            try:
                kwargs = json.loads(kwargs)
            except ValueError:
                kwargs = {}
        if isinstance(kwargs, dict):
            for key in ("timeout", "max_retries", "cache_ttl"):
                try:
                    if key in kwargs:
                        CONFIG[key] = max(1, int(kwargs[key]))
                except (TypeError, ValueError):
                    pass
        self._ensure_session()
        return dict(CONFIG)

    def _ensure_session(self):
        with self.lock:
            if self.session is None:
                self.session = build_opener(HTTPCookieProcessor(CookieJar()), HTTPRedirectHandler())
        return self.session

    def _request(self, url, method="GET", data=None, headers=None, use_cache=True):
        key = method + ":" + url + (":" + str(data) if data else "")
        if use_cache:
            cached = self.cache.get(key)
            if cached is not None:
                return cached
        request_headers = dict(self.headers)
        if headers:
            request_headers.update(headers)
        if data is not None and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"
        last_error = None
        for attempt in range(CONFIG["max_retries"]):
            try:
                request = Request(url, data=data, headers=request_headers, method=method)
                with self._ensure_session().open(request, timeout=CONFIG["timeout"]) as response:
                    raw = response.read()
                    if response.headers.get("Content-Encoding", "").lower() == "gzip":
                        raw = gzip.decompress(raw)
                    text = raw.decode(response.headers.get_content_charset() or "utf-8", "replace")
                    if use_cache:
                        self.cache.set(key, text)
                    return text
            except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
                last_error = exc
                if isinstance(exc, HTTPError) and exc.code in (401, 403, 404):
                    break
                if attempt + 1 < CONFIG["max_retries"]:
                    time.sleep(min(2 ** attempt, 4))
        logger.warning("请求失败 %s: %s", url, last_error)
        return ""

    def _json_post(self, path, payload, referer):
        body = self._request(urljoin(CONFIG["base_url"], path), method="POST",
                             data=json.dumps(payload).encode("utf-8"), use_cache=False,
                             headers={"Accept": "application/json", "Content-Type": "application/json",
                                      "Origin": CONFIG["base_url"], "Referer": referer})
        try:
            return json.loads(body)
        except (TypeError, ValueError):
            return {}

    def _page(self, path):
        return self._request(urljoin(CONFIG["base_url"], path))

    def home(self, filter=None):
        return {"class": [
            {"type_id": "duanju", "type_name": "AI短剧"},
            {"type_id": "manju", "type_name": "AI漫剧"},
            {"type_id": "mogai", "type_name": "AI魔改"},
            {"type_id": "meinv", "type_name": "AI美女"},
        ]}

    def category(self, tid, pg=1, filter=None, extend=None):
        try:
            page = max(1, int(pg))
        except (TypeError, ValueError):
            page = 1
        slug = str(tid or "duanju").strip().strip("/")
        if slug in ("all", "duanju"):
            path = "/ai-duanju/"
        elif slug in ("manju", "ai-manju"):
            path = "/ai-manju/"
        elif slug in ("mogai", "ai-mogai"):
            path = "/ai-mogai/"
        elif slug in ("meinv", "ai-meinv"):
            path = "/ai-meinv/"
        else:
            path = "/%s/" % quote(slug, safe="-")
        if page > 1:
            path = path.rstrip("/") + "/%d/" % page
        body = self._page(path)
        items = Parser.cards(body, CONFIG["base_url"])
        clean_body = Parser.clean(body)
        total_match = re.search(r"共\s*([\d,]+)\s*部作品", clean_body, re.I)
        total = int(total_match.group(1).replace(",", "")) if total_match else 0
        page_match = re.search(r"第\s*(\d+)\s*页，共\s*(\d+)\s*页", clean_body, re.I)
        pagecount = int(page_match.group(2)) if page_match else page
        return {"page": page, "pagecount": pagecount, "limit": CONFIG["page_size"], "total": total, "list": items}

    def detail(self, id):
        target = str(id or "").strip()
        if not target.startswith("http"):
            target = urljoin(CONFIG["base_url"] + "/", target.lstrip("/"))
        path = urlparse(target).path
        if "/video/" in path:
            video_url = target
            drama_url = urljoin(CONFIG["base_url"], re.sub(r"/video/\d+(?:/\d+)?/?", "/drama/%s/" % re.search(r"/video/(\d+)", path).group(1), path))
            body = self._page(path)
        else:
            drama_url = target
            body = self._page(path)
            video_url = ""
        data = Parser.play_data(body)
        title = Parser.clean(re.search(r'<h1[^>]*>(.*?)</h1>', body, re.I | re.S).group(1)) if re.search(r'<h1[^>]*>(.*?)</h1>', body, re.I | re.S) else str(data.get("title", "未命名"))
        desc = Parser.clean(data.get("description", ""))
        poster = str(data.get("poster", ""))
        image_candidates = re.findall(r'<img[^>]+(?:data-src|src)=["\']([^"\']+)["\'][^>]*>', body, re.I)
        if not poster or "mc.yandex.ru" in poster:
            poster = next((x for x in image_candidates if "pic.qnlycc.cn" in x or "/upload_" in x), "")
        if not poster or "mc.yandex.ru" in poster:
            og = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', body, re.I)
            poster = og.group(1) if og else ""
        if not poster:
            poster = str(data.get("poster", ""))
        drama_match = re.search(r"/drama/(\d+)", drama_url)
        current_drama_id = drama_match.group(1) if drama_match else data.get("id", "")
        episodes = Parser.episode_urls(body, CONFIG["base_url"], current_drama_id)
        if not episodes and data.get("eps"):
            for ep in data["eps"]:
                n = int(ep.get("n", 1))
                episode_url = "/video/%s/%s/" % (data.get("id", ""), n) if n > 1 else "/video/%s/" % data.get("id", "")
                episodes.append((n, "第%d集" % n, urljoin(CONFIG["base_url"], episode_url)))
        if not episodes and video_url:
            episodes = [(1, "第1集", video_url)]
        play_urls = "#".join(label + "$" + url for _, label, url in episodes)
        return {"list": [{"vod_id": drama_url, "vod_name": title, "vod_pic": poster,
                          "vod_content": desc, "vod_remarks": "%d集" % len(episodes) if episodes else "",
                          "vod_play_from": "黄桃短剧", "vod_play_url": play_urls}]}

    def search(self, wd, quick=False):
        keyword = str(wd or "").strip()
        if not keyword:
            return {"list": []}
        body = self._page("/search/video/%s/" % quote(keyword, safe=""))
        return {"list": Parser.cards(body, CONFIG["base_url"])}

    def play(self, flag, id, flags=None, url="", sub=None):
        target = str(url or id or "").strip()
        if not target.startswith("http"):
            target = urljoin(CONFIG["base_url"] + "/", target.lstrip("/"))
        path = urlparse(target).path
        match = re.search(r"/video/(\d+)(?:/(\d+))?/?$", path)
        if not match:
            return {"parse": 0, "url": target}
        drama_id, ep = match.group(1), int(match.group(2) or 1)
        page = self._page(path)
        data = Parser.play_data(page)
        endpoint = str(data.get("playbackEndpoint", "/api/videos/%s/episodes/__EP__/playback" % drama_id)).replace("__EP__", str(ep))
        result = self._json_post(endpoint, {}, target)
        payload = result.get("data", result) if isinstance(result, dict) else {}
        streams = payload.get("streams", {}) if isinstance(payload, dict) else {}
        media = streams.get("main") or payload.get("src") or payload.get("url") or ""
        headers = {"Referer": target, "Origin": CONFIG["base_url"], "User-Agent": self.headers["User-Agent"]}
        cdn = payload.get("cdn", {}) if isinstance(payload, dict) else {}
        if cdn.get("authKey") and cdn.get("authValue"):
            headers[cdn["authKey"]] = cdn["authValue"]
        if cdn.get("app"):
            headers["x-cdn-app"] = str(cdn["app"])
        return {"parse": 0, "url": str(media), "header": headers}

    def proxy(self, segment, headers=None, url="", data=None):
        return str(url or "")

    # CatVod standard compatibility names.
    def homeContent(self, filter=None): return self.home(filter)
    def categoryContent(self, tid, pg=1, filter=None, extend=None): return self.category(tid, pg, filter, extend)
    def detailContent(self, ids): return self.detail(ids[0] if isinstance(ids, (list, tuple)) and ids else ids)
    def searchContent(self, wd, quick=False, pg=1): return self.search(wd, quick)
    def playerContent(self, flag, id, vipFlags=None): return self.play(flag, id, vipFlags, id, None)
    def localProxy(self, params): return self.proxy(params.get("segment", ""), params.get("headers", {}), params.get("url", ""), params.get("data")) if isinstance(params, dict) else ""
    def __close__(self): self.session = None
    async def __async_init__(self): self.init({}); return True


def main():
    spider = Spider()
    spider.init({})
    return spider
