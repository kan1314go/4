#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import gzip
import zlib
import ssl
import random
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

        self.siteName = "Twitter精选"
        self.siteUrl = "https://pektino.com"
        self.tgGroup = "https://t.me/tvshare23"
        self.brandName = "蝴蝶影视"
        self.brandActor = "🦋 TG群: @tvshare23"
        self.brandDirector = "🦋 蝴蝶影视"
        self.lineName = "🦋 蝴蝶专线"
        self._ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        self.options = {}

        self.categories = [
            {"type_id": "feed_stream", "type_name": "🔥 沉浸连刷"},
            {"type_id": "daily", "type_name": "每日精选"},
            {"type_id": "weekly", "type_name": "每周热门"},
            {"type_id": "monthly", "type_name": "每月排行"},
            {"type_id": "all", "type_name": "历史最佳"}
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
                self.siteUrl = ext_str.rstrip("/")
            else:
                try:
                    self.options = json.loads(ext_str)
                except Exception:
                    self.options = {}
        host = self.options.get("host", "") if isinstance(self.options, dict) else ""
        if isinstance(host, str) and host.strip().startswith("http"):
            self.siteUrl = host.strip().rstrip("/")
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

    def _clean_text(self, val):
        if val is None:
            return ""
        s = re.sub(r"<[^>]+>", "", str(val))
        s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        s = s.replace("&quot;", '"').replace("&#039;", "'").replace("&#39;", "'").replace("&nbsp;", " ")
        s = re.sub(r"[\$#\r\n\t]+", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    def _convert_pic_proxy(self, pic_url):
        if not pic_url:
            return ""
        pic = str(pic_url).strip()
        if pic.startswith("//"):
            pic = "https:" + pic
        elif pic.startswith("/"):
            pic = "%s%s" % (self.siteUrl, pic)
        if "twimg.com" in pic:
            return "https://wsrv.nl/?url=%s" % urllib.parse.quote(pic, safe="")
        return pic

    def _fetch_html(self, target_url, referer="", timeout=7):
        if not target_url:
            return {"code": 0, "text": "", "url": ""}
        full_url = target_url
        if full_url.startswith("//"):
            full_url = "https:" + full_url
        elif full_url.startswith("/"):
            full_url = "%s%s" % (self.siteUrl, full_url)
        elif not full_url.startswith("http"):
            full_url = "%s/%s" % (self.siteUrl, full_url)

        headers = {
            "User-Agent": self._ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Referer": referer if referer else ("%s/zh-CN" % self.siteUrl),
            "Connection": "keep-alive"
        }

        for attempt in range(2):
            try:
                req = urllib.request.Request(full_url, headers=headers)
                with self.opener.open(req, timeout=timeout) as resp:
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
                    return {"code": code, "text": text, "url": final_url}
            except urllib.error.HTTPError as e:
                if e.code in (451, 403, 429) and attempt == 0:
                    continue
                return {"code": e.code, "text": "", "url": full_url}
            except Exception:
                if attempt == 0:
                    continue
                return {"code": 0, "text": "", "url": full_url}
        return {"code": 0, "text": "", "url": full_url}

    def _parse_cards_raw(self, html_text):
        cards = []
        if not html_text:
            return cards

        seen_ids = set()
        for m in re.finditer(r'<a[^>]+href="[^"]*(?:/zh-CN)?/(?:movies?|shorts)/[^"]+"[^>]*>[\s\S]*?</a>', html_text, re.I):
            block = m.group(0)
            href_m = re.search(r'href="([^"]*(?:/zh-CN)?/(?:movies?|shorts)/([^"/]+)/?)"', block, re.I)
            if not href_m:
                continue

            vid = href_m.group(2).strip()
            if not vid or vid in seen_ids:
                continue
            seen_ids.add(vid)

            img_m = re.search(r'(?:src|data-src|poster)="([^"]+)"', block, re.I)
            pic = self._convert_pic_proxy(img_m.group(1)) if img_m else ""

            dur_m = re.search(r'(\d+:\d+(?::\d+)?)', block)
            dur = dur_m.group(1) if dur_m else ""

            title = vid
            alt_m = re.search(r'alt="([^"]+)"', block, re.I)
            if alt_m:
                clean_alt = re.sub(r'X\s*\(Twitter\)\s*adult\s*video\s*', '', alt_m.group(1), flags=re.I)
                clean_alt = self._clean_text(clean_alt)
                if clean_alt:
                    title = clean_alt
            if title == vid:
                title = "精选影片 %s" % vid

            cards.append({
                "vid": vid,
                "title": title,
                "pic": pic,
                "dur": dur
            })
        return cards

    def _extract_stream_from_html(self, html_text, vid=""):
        if not html_text:
            return ""
        clean_text = html_text.replace("\\/", "/").replace('\\"', '"').replace("\\\\", "\\")
        raw_mp4s = re.findall(r'https?://video\.twimg\.com/[^"\'\s<>\\]+\.mp4(?:\?[^"\'\s<>\\]*)?', clean_text, re.I)

        valid = []
        for u in raw_mp4s:
            cu = u.replace("\\", "").strip()
            if cu.startswith("http") and "localhost" not in cu and "127.0.0.1" not in cu and cu not in valid:
                valid.append(cu)

        if vid:
            for u in valid:
                if vid in u:
                    return u
        return valid[0] if valid else ""

    def _fetch_movie_html(self, vid, timeout=7):
        if str(vid).startswith("http"):
            return self._fetch_html(vid, timeout=timeout)
        res = self._fetch_html("%s/zh-CN/movies/%s" % (self.siteUrl, vid), timeout=timeout)
        if not res.get("text") or res.get("code") == 404:
            res = self._fetch_html("%s/zh-CN/movie/%s" % (self.siteUrl, vid), timeout=timeout)
        return res

    def homeContent(self, filter):
        result = {"class": self.categories}
        if filter:
            result["filters"] = {}
        return result

    def homeVideoContent(self):
        res = self._fetch_html("%s/zh-CN" % self.siteUrl)
        raw_cards = self._parse_cards_raw(res.get("text", ""))[:12]
        items = []
        for c in raw_cards:
            items.append({
                "vod_id": c["vid"],
                "vod_name": c["title"],
                "vod_pic": c["pic"],
                "vod_remarks": _format_remarks(self.brandName, c["dur"]),
                "style": {"type": "rect", "ratio": 1.78}
            })
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1

        clean_tid = str(tid or "daily").strip("/")

        if clean_tid == "feed_stream":
            pool_sections = ["weekly", "monthly", "all", "daily"]
            random.shuffle(pool_sections)
            raw_cards = []

            for sec in pool_sections:
                base_p = random.randint(1, 5)
                target_url = ("%s/zh-CN" % self.siteUrl) if sec == "daily" else ("%s/zh-CN/%s" % (self.siteUrl, sec))
                if base_p > 1:
                    target_url = "%s?page=%d" % (target_url, base_p)
                res = self._fetch_html(target_url)
                cards = self._parse_cards_raw(res.get("text", ""))
                if cards:
                    raw_cards = cards
                    break

            if not raw_cards:
                fallback_res = self._fetch_html("%s/zh-CN" % self.siteUrl)
                raw_cards = self._parse_cards_raw(fallback_res.get("text", ""))

            if not raw_cards:
                return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

            random.shuffle(raw_cards)
            items = []
            for c in raw_cards:
                items.append({
                    "vod_id": "feed@@%s" % c["vid"],
                    "vod_name": c["title"],
                    "vod_pic": c["pic"],
                    "vod_remarks": _format_remarks(self.brandName, "连刷起播"),
                    "style": {"type": "rect", "ratio": 1.78}
                })
            return {
                "list": items,
                "page": page,
                "pagecount": page + 1,
                "limit": len(items),
                "total": page * len(items) + 100
            }

        target_url = ("%s/zh-CN" % self.siteUrl) if clean_tid == "daily" else ("%s/zh-CN/%s" % (self.siteUrl, clean_tid))
        if page > 1:
            target_url = "%s?page=%d" % (target_url, page)

        res = self._fetch_html(target_url)
        raw_cards = self._parse_cards_raw(res.get("text", ""))
        if not raw_cards:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        items = []
        for c in raw_cards:
            items.append({
                "vod_id": c["vid"],
                "vod_name": c["title"],
                "vod_pic": c["pic"],
                "vod_remarks": _format_remarks(self.brandName, c["dur"]),
                "style": {"type": "rect", "ratio": 1.78}
            })

        return {
            "list": items,
            "page": page,
            "pagecount": page + 1,
            "limit": len(items),
            "total": page * len(items) + 100
        }

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, (list, tuple)) and ids else str(ids or "")
        vid_raw = str(raw_id).strip()
        if not vid_raw:
            return {"list": []}

        if vid_raw.startswith("feed@@"):
            start_vid = vid_raw.split("@@", 1)[1].strip()
            first_resp = self._fetch_movie_html(start_vid, timeout=6)
            first_html = first_resp.get("text", "")
            first_stream = self._extract_stream_from_html(first_html, start_vid)

            pic = ""
            pic_m = re.search(r'property="og:image"\s+content="([^"]+)"', first_html, re.I)
            if pic_m:
                pic = self._convert_pic_proxy(pic_m.group(1))

            random_pool = []
            seen_pool_ids = {start_vid}

            rec_cards = self._parse_cards_raw(first_html)
            for rc in rec_cards:
                if rc["vid"] not in seen_pool_ids:
                    seen_pool_ids.add(rc["vid"])
                    random_pool.append(rc["vid"])

            sections = ["weekly", "monthly", "all", "daily"]
            random.shuffle(sections)
            for sec in sections[:2]:
                pg_num = random.randint(1, 5)
                t_url = ("%s/zh-CN" % self.siteUrl) if sec == "daily" else ("%s/zh-CN/%s" % (self.siteUrl, sec))
                if pg_num > 1:
                    t_url = "%s?page=%d" % (t_url, pg_num)
                page_res = self._fetch_html(t_url, timeout=5)
                for pc in self._parse_cards_raw(page_res.get("text", "")):
                    if pc["vid"] not in seen_pool_ids:
                        seen_pool_ids.add(pc["vid"])
                        random_pool.append(pc["vid"])
                if len(random_pool) >= 60:
                    break

            random.shuffle(random_pool)
            start_payload = "stream@@%s" % first_stream if first_stream else ("vid@@%s" % start_vid)
            episodes = ["🔥 沉浸首发$%s" % start_payload]

            for idx, r_vid in enumerate(random_pool[:60]):
                ep_num = ("0%d" % (idx + 1)) if (idx + 1) < 10 else str(idx + 1)
                episodes.append("连刷 %s$vid@@%s" % (ep_num, r_vid))

            content = (
                "🦋 蝴蝶影视专线加速播放 | 官方TG交流群：@tvshare23 | "
                "沉浸式短视频连刷模式，遥控器按下键或自动无缝切集"
            )

            vod = {
                "vod_id": vid_raw,
                "vod_name": "🔥 沉浸连刷·全屏自适应",
                "vod_pic": pic,
                "vod_bg": pic,
                "vod_background": pic,
                "vod_banner": pic,
                "type_name": "连刷精选",
                "vod_actor": self.brandActor,
                "vod_director": self.brandDirector,
                "vod_remarks": _format_remarks(self.brandName, "连刷%d集" % len(episodes)),
                "vod_content": content,
                "vod_play_from": self.lineName,
                "vod_play_url": "#".join(episodes)
            }
            return {"list": [vod]}

        vid = vid_raw
        res = self._fetch_movie_html(vid, timeout=7)
        html_text = res.get("text", "")
        if not html_text:
            return {"list": []}

        title = "精选影片"
        title_m = re.search(r"<title>([^<]+)</title>", html_text, re.I)
        if title_m:
            parsed_t = self._clean_text(title_m.group(1).split(" - ")[0])
            if parsed_t:
                title = parsed_t

        pic = ""
        pic_m = re.search(r'property="og:image"\s+content="([^"]+)"', html_text, re.I)
        if pic_m:
            pic = self._convert_pic_proxy(pic_m.group(1))

        rec_cards = self._parse_cards_raw(html_text)
        main_stream = self._extract_stream_from_html(html_text, vid)
        main_payload = "stream@@%s" % main_stream if main_stream else ("vid@@%s" % vid)
        episodes = ["正片$%s" % main_payload]

        rec_idx = 1
        for rc in rec_cards:
            if rc["vid"] != vid:
                ep_prefix = ("0%d" % rec_idx) if rec_idx < 10 else str(rec_idx)
                clean_rec_t = self._clean_text(rc["title"])[:14]
                episodes.append("%s·%s$vid@@%s" % (ep_prefix, clean_rec_t, rc["vid"]))
                rec_idx += 1
                if rec_idx > 30:
                    break

        rec_count = len(episodes) - 1
        content = (
            "🦋 蝴蝶影视专线直连 | %s | 官方交流群: @tvshare23\n"
            "本片已智能挂载【%d】部关联推荐影片，切集即可直接连播！"
        ) % (title, rec_count)

        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": pic,
            "vod_bg": pic,
            "vod_background": pic,
            "vod_banner": pic,
            "type_name": "Twitter精选",
            "vod_actor": self.brandActor,
            "vod_director": self.brandDirector,
            "vod_remarks": _format_remarks(self.brandName, "推荐%d部" % rec_count),
            "vod_content": content,
            "vod_play_from": self.lineName,
            "vod_play_url": "#".join(episodes)
        }
        return {"list": [vod]}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1

        keyword = self._clean_text(key)
        if not keyword:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        search_url = "%s/zh-CN/search?tag=%s" % (self.siteUrl, urllib.parse.quote(keyword))
        if page > 1:
            search_url = "%s&page=%d" % (search_url, page)

        res = self._fetch_html(search_url)
        raw_cards = self._parse_cards_raw(res.get("text", ""))
        if not raw_cards:
            return {"list": [], "page": page, "pagecount": 1, "limit": 20, "total": 0}

        items = []
        for c in raw_cards:
            items.append({
                "vod_id": c["vid"],
                "vod_name": c["title"],
                "vod_pic": c["pic"],
                "vod_remarks": _format_remarks(self.brandName, c["dur"]),
                "style": {"type": "rect", "ratio": 1.78}
            })

        return {
            "list": items,
            "page": page,
            "pagecount": page + 1,
            "limit": len(items),
            "total": page * len(items) + 100
        }

    def playerContent(self, flag, id, vipFlags):
        raw_id = str(id or "").strip()
        stream_url = ""
        target_vid = ""

        if raw_id.startswith("stream@@"):
            stream_url = raw_id[len("stream@@"):].strip()
        elif raw_id.startswith("vid@@"):
            target_vid = raw_id[len("vid@@"):].strip()
        else:
            if raw_id.startswith("http"):
                stream_url = raw_id
            else:
                target_vid = raw_id

        if not stream_url and target_vid:
            page_res = self._fetch_movie_html(target_vid, timeout=6)
            stream_url = self._extract_stream_from_html(page_res.get("text", ""), target_vid)

        if not stream_url:
            fallback_page = "%s/zh-CN/movies/%s" % (self.siteUrl, target_vid) if target_vid else self.siteUrl
            return {
                "parse": 1,
                "jx": 0,
                "playUrl": "",
                "url": fallback_page,
                "header": {"User-Agent": self._ua, "Referer": "%s/zh-CN" % self.siteUrl}
            }

        final_url = stream_url
        low = final_url.lower()
        if ".m3u8" not in low and ".mp4" not in low:
            sep = "&" if "?" in final_url else "?"
            final_url = "%s%sformat=.mp4" % (final_url, sep)

        return {
            "parse": 0,
            "jx": 0,
            "playUrl": "",
            "url": final_url,
            "header": {
                "User-Agent": self._ua
            }
        }

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]
# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250218506&sig=b7baf1c4468bec4d
