#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import gzip
import zlib
import ssl
import http.cookiejar
import urllib.request
import urllib.parse

try:
    from base.spider import Spider as SpiderBase
except Exception:
    class SpiderBase(object):
        def getCache(self, key):
            return None

        def setCache(self, key, value):
            return "fail"

        def delCache(self, key):
            return "fail"


def _format_remarks(brand, meta):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


class Spider(SpiderBase):
    def __init__(self, *args, **kwargs):
        try:
            super(Spider, self).__init__(*args, **kwargs)
        except Exception:
            try:
                super(Spider, self).__init__()
            except Exception:
                pass

        self.siteName = "CHX站"
        self.hosts = ["https://chinaxmovie.com", "http://chinaxmovie.com"]
        self.hostIndex = 0
        self.customHost = ""
        self.cacheKeyHost = "butterfly_chx_host"
        self.tgGroup = "https://t.me/tvshare23"
        self.brandName = "蝴蝶影视"
        self.brandActor = "🦋 TG群: @tvshare23"
        self.brandDirector = "🦋 蝴蝶影视"
        self.lineName = "🦋 蝴蝶专属线路"
        self._ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        self.options = {}

        self.categories = [
            {"type_id": "domestic-media", "type_name": "国产传媒"},
            {"type_id": "japanese-av", "type_name": "日本AV"},
            {"type_id": "uncensored-videos", "type_name": "无码视频"},
            {"type_id": "chinese-subtitles", "type_name": "中文字幕"}
        ]

        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE

        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=self.ctx)
        )

    def init(self, extend=""):
        if isinstance(extend, dict):
            self.options = extend
        elif isinstance(extend, str) and extend.strip():
            ext_str = extend.strip()
            if ext_str.startswith("http"):
                self.customHost = ext_str.rstrip("/")
            else:
                try:
                    self.options = json.loads(ext_str)
                except Exception:
                    self.options = {}
        host = self.options.get("host", "") if isinstance(self.options, dict) else ""
        if isinstance(host, str) and host.strip().startswith("http"):
            self.customHost = host.strip().rstrip("/")
        if self.customHost and self.customHost not in self.hosts:
            self.hosts.insert(0, self.customHost)
        return True

    def getName(self):
        return self.siteName

    def isVideoFormat(self, url):
        if not url:
            return False
        low = str(url).lower()
        if any(bad in low for bad in ("preview.mp4", "sample.mp4", "trailer.mp4", "native-ad")):
            return False
        return any(ext in low for ext in (".m3u8", ".mp4", ".flv", ".mkv", ".ts", ".mpd"))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        self.options = {}

    def _current_host(self):
        if self.customHost:
            return self.customHost
        try:
            cached = self.getCache(self.cacheKeyHost)
            if isinstance(cached, str) and cached.startswith("http"):
                return cached.rstrip("/")
        except Exception:
            pass
        return self.hosts[self.hostIndex % len(self.hosts)]

    def _rotate_host(self):
        if self.customHost:
            return self.customHost
        self.hostIndex = (self.hostIndex + 1) % len(self.hosts)
        next_h = self.hosts[self.hostIndex]
        try:
            self.setCache(self.cacheKeyHost, next_h)
        except Exception:
            pass
        return next_h

    def _origin_of(self, url):
        m = re.match(r"^(https?://[^/]+)", str(url or ""), re.I)
        return m.group(1) if m else ""

    def _abs_url(self, u, host=""):
        s = str(u or "").strip()
        if not s:
            return ""
        base = host if host else self._current_host()
        if s.startswith("//"):
            return "https:" + s
        if s.startswith("/"):
            return "%s%s" % (base, s)
        if s.startswith("http"):
            return s
        return "%s/%s" % (base, s)

    def _unescape_html(self, s):
        text = str(s or "")
        text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        text = text.replace("&quot;", '"').replace("&#039;", "'").replace("&#39;", "'").replace("&nbsp;", " ")
        return text

    def _strip_tags(self, s):
        text = re.sub(r"<[^>]+>", "", str(s or ""))
        return re.sub(r"\s+", " ", self._unescape_html(text)).strip()

    def _format_poster(self, raw_pic, host=""):
        if not raw_pic:
            return ""
        base = host if host else self._current_host()
        full = self._abs_url(str(raw_pic).strip().replace("&amp;", "&"), base)
        if not full.startswith("http"):
            return ""
        ref = urllib.parse.quote("%s/" % base, safe="")
        ua = urllib.parse.quote(self._ua, safe="")
        return "%s@Referer=%s@User-Agent=%s" % (full, ref, ua)

    def _clean_title(self, title):
        t = re.sub(r"\s+", " ", str(title or "")).strip()
        t = re.sub(r"(高清)?在线(观看|播放)$", "", t)
        t = re.sub(r"[\u200b-\u200f\ufeff]", "", t).strip()
        return t

    def _clean_m3u8_url(self, raw_str):
        if not raw_str:
            return ""
        m = re.search(r'(https?://(?:(?!localhost|127\.0\.0\.1)[^\s"\'\$<>])+\.m3u8[^\s"\'\$<>]*)', str(raw_str), re.I)
        if m:
            return m.group(1).replace("\\u002F", "/").replace("\\/", "")
        return ""

    def _fetch_page(self, target, referer=""):
        host = self._current_host()
        candidates = [host]
        for h in self.hosts:
            if h not in candidates:
                candidates.append(h)

        for idx, cand_host in enumerate(candidates):
            full_url = str(target or "").strip()
            if full_url.startswith("//"):
                full_url = "https:" + full_url
            elif full_url.startswith("/"):
                full_url = "%s%s" % (cand_host, full_url)
            elif not full_url.startswith("http"):
                full_url = "%s/%s" % (cand_host, full_url)

            headers = {
                "User-Agent": self._ua,
                "Referer": referer if referer else ("%s/" % cand_host),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
                "X-Requested-With": "XMLHttpRequest",
                "Connection": "keep-alive"
            }

            try:
                req = urllib.request.Request(full_url, headers=headers)
                with self.opener.open(req, timeout=8) as resp:
                    code = resp.getcode()
                    final_url = resp.geturl()
                    raw = resp.read()
                    enc = getattr(resp, "headers", {}).get("Content-Encoding", "")
                    if raw.startswith(b"\x1f\x8b") or enc == "gzip":
                        raw = gzip.decompress(raw)
                    elif enc == "deflate":
                        try:
                            raw = zlib.decompress(raw)
                        except Exception:
                            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                    text = raw.decode("utf-8", errors="ignore")
                    if code >= 400 and len(text) < 200:
                        self._rotate_host()
                        continue
                    active_host = self._origin_of(final_url) or cand_host
                    if idx > 0:
                        try:
                            self.setCache(self.cacheKeyHost, active_host)
                        except Exception:
                            pass
                    return {"text": text, "host": active_host}
            except Exception:
                self._rotate_host()
                continue

        return {"text": "", "host": host}

    def _parse_cards(self, html, host):
        text = str(html or "")
        if not text:
            return []

        blocks = []
        if 'class="thumbnail' in text or "class='thumbnail" in text:
            parts = re.split(r'(?=<div[^>]*class=["\'][^"\']*thumbnail[^"\']*["\'])', text, flags=re.I)
            blocks = [p for p in parts if 'thumbnail' in p[:120].lower()]
        if not blocks:
            blocks = re.findall(r'<div[^>]*class=["\'][^"\']*thumbnail[^"\']*["\'][^>]*>[\s\S]*?</div>\s*</div>', text, re.I)

        items = []
        seen = set()
        for block in blocks:
            hm = re.search(r'href=["\'](/vodplay/[a-zA-Z0-9_\-]+)["\']', block, re.I)
            if not hm:
                continue
            href = hm.group(1).strip()
            if href in seen:
                continue

            pic = ""
            pm = re.search(r'<img[^>]+(?:data-src|src)=["\']([^"\']+)["\']', block, re.I)
            if pm:
                pic = pm.group(1).strip()

            title = ""
            am = re.search(r'<img[^>]+alt=["\']([^"\']+)["\']', block, re.I)
            if am:
                title = am.group(1).strip()
            if not title:
                xm = re.search(r'<a[^>]*class=["\'][^"\']*text-secondary[^"\']*["\'][^>]*>([\s\S]*?)</a>', block, re.I)
                if xm:
                    title = self._strip_tags(xm.group(1))

            title = self._clean_title(title)
            if not title or len(title) <= 1:
                continue

            seen.add(href)
            rm = re.search(r'<span[^>]*class=["\'][^"\']*(?:bottom-1|text-nord5|remarks|pic-text)[^"\']*["\'][^>]*>([\s\S]*?)</span>', block, re.I)
            raw_remark = self._strip_tags(rm.group(1)) if rm else ""
            meta = raw_remark if raw_remark else "高清"

            items.append({
                "vod_id": href,
                "vod_name": title,
                "vod_pic": self._format_poster(pic, host),
                "vod_remarks": _format_remarks(self.brandName, meta),
                "style": {"type": "rect", "ratio": 1.78}
            })
        return items

    def _extract_stream(self, html):
        text = str(html or "")
        s = ""
        m = re.search(r'player_aaaa\s*=\s*\{[\s\S]*?["\']url["\']\s*:\s*["\']([^"\']+)["\'][\s\S]*?\}', text, re.I)
        if m:
            s = m.group(1).replace("\\/", "/").strip()

        if not s or (".m3u8" not in s.lower() and ".mp4" not in s.lower()):
            m2 = re.search(r'["\']url["\']\s*:\s*["\'](https?:\\?/\\?/[^"\']+\.m3u8[^"\']*)["\']', text, re.I)
            if m2:
                s = m2.group(1).replace("\\/", "/").strip()

        if not s:
            bm = re.search(r'<div[^>]*class=["\'][^"\']*stui-player__video[^"\']*["\'][^>]*>([\s\S]*?)</div>', text, re.I)
            if bm:
                m3 = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', bm.group(1), re.I)
                if m3:
                    s = m3.group(1).strip()

        cleaned = self._clean_m3u8_url(s)
        return cleaned if cleaned else s

    def homeContent(self, filter):
        result = {"class": self.categories}
        if filter:
            result["filters"] = {}
        return result

    def homeVideoContent(self):
        r = self._fetch_page("/")
        items = self._parse_cards(r.get("text", ""), r.get("host", ""))[:24]
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1

        slug = str(tid or self.categories[0]["type_id"]).strip("/").replace("vodtype/", "")
        path = ("/vodtype/%s" % slug) if page <= 1 else ("/vodtype/%s/page/%d/" % (slug, page))
        r = self._fetch_page(path)
        items = self._parse_cards(r.get("text", ""), r.get("host", ""))

        if not items and page > 1:
            fallback_path = "/vodtype/%s-%d.html" % (slug, page)
            r2 = self._fetch_page(fallback_path)
            items = self._parse_cards(r2.get("text", ""), r2.get("host", ""))

        if not items:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        return {
            "list": items,
            "page": page,
            "pagecount": page + 1,
            "limit": len(items),
            "total": page * len(items) + 100
        }

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1

        kw = self._strip_tags(key)
        if not kw:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        enc_kw = urllib.parse.quote(kw)
        if page <= 1:
            path = "/vodsearch/-------------.html?wd=%s" % enc_kw
        else:
            path = "/vodsearch/%s----------%d---.html" % (enc_kw, page)

        r = self._fetch_page(path)
        items = self._parse_cards(r.get("text", ""), r.get("host", ""))
        if not items:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        return {
            "list": items,
            "page": page,
            "pagecount": page + 1,
            "limit": len(items),
            "total": page * len(items) + 100
        }

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, (list, tuple)) and ids else str(ids or "")
        path = str(raw_id).strip()
        if not path:
            return {"list": []}

        r = self._fetch_page(path)
        html = r.get("text", "")
        active_host = r.get("host", self._current_host())
        if not html:
            return {"list": []}

        tm = re.search(r"<h1[^>]*>([\s\S]*?)</h1>", html, re.I)
        title = self._clean_title(self._strip_tags(tm.group(1))) if tm else "精彩视频"
        if not title:
            title = "精彩视频"

        stream = self._extract_stream(html)
        pm = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html, re.I)
        if not pm:
            pm = re.search(r'<img[^>]+(?:data-original|data-src|src)=["\']([^"\']+\.(?:jpg|jpeg|png|webp)[^"\']*)["\']', html, re.I)
        pic = pm.group(1).strip() if pm else ""
        clean_bg = self._abs_url(pic.replace("&amp;", "&"), active_host) if pic else ""

        play_payload = ("stream@@%s" % stream) if stream else ("path@@%s" % path)
        content = (
            "🦋 蝴蝶影视专线直连 | %s | 官方交流群: @tvshare23\n"
            "当前节点：%s | CHX站专属超清线路，全网热播资源极速秒播"
        ) % (title, active_host)

        vod = {
            "vod_id": path,
            "vod_name": title,
            "vod_pic": clean_bg,
            "vod_bg": clean_bg,
            "vod_background": clean_bg,
            "vod_banner": clean_bg,
            "type_name": "CHX站",
            "vod_actor": self.brandActor,
            "vod_director": self.brandDirector,
            "vod_remarks": _format_remarks(self.brandName, "超清正片"),
            "vod_content": content,
            "vod_play_from": self.lineName,
            "vod_play_url": "正片$%s" % play_payload
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw_id = str(id or "").strip()
        host = self._current_host()
        target_url = ""

        if raw_id.startswith("stream@@"):
            target_url = self._abs_url(raw_id[len("stream@@"):].strip(), host)
        elif raw_id.startswith("path@@"):
            page_path = raw_id[len("path@@"):].strip()
            r = self._fetch_page(page_path)
            s = self._extract_stream(r.get("text", ""))
            if s:
                target_url = self._abs_url(s, r.get("host", host))
        else:
            if ".m3u8" in raw_id.lower() or ".mp4" in raw_id.lower():
                target_url = self._abs_url(raw_id, host)
            else:
                r = self._fetch_page(raw_id)
                s = self._extract_stream(r.get("text", ""))
                if s:
                    target_url = self._abs_url(s, r.get("host", host))

        headers = {
            "User-Agent": self._ua,
            "Referer": "%s/" % host,
            "Origin": host
        }

        if target_url:
            low = target_url.lower()
            if target_url.startswith("http") and ".m3u8" not in low and ".mp4" not in low:
                sep = "&" if "?" in target_url else "?"
                target_url = "%s%sformat=.m3u8" % (target_url, sep)
            return {
                "parse": 0,
                "jx": 0,
                "playUrl": "",
                "url": target_url,
                "header": headers
            }

        fallback_page = self._abs_url(raw_id.replace("path@@", ""), host)
        return {
            "parse": 1,
            "jx": 0,
            "playUrl": "",
            "url": fallback_page,
            "header": headers
        }

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]
# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250029864&sig=b303bd3a639acea7
