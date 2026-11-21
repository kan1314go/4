#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
import json
import base64
import html as html_lib
import urllib.request
import urllib.parse
from urllib.parse import quote, unquote
import http.cookiejar
import gzip
import zlib
import ssl

try:
    from base.spider import Spider as SpiderBase
except ImportError:
    class SpiderBase(object):
        def getCache(self, key): return None
        def setCache(self, key, value): return "fail"
        def delCache(self, key): return "fail"

def format_remarks(brand="蝴蝶影视", meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand

def clean_label(text):
    if not text:
        return ""
    t = re.sub(r'<[^>]+>', '', str(text))
    t = re.sub(r'[\r\n\t\$\#]+', ' ', t).strip()
    return t[:24]

class Spider(SpiderBase):
    def __init__(self):
        super(Spider, self).__init__()
        self.siteName = "萝莉社"
        self.siteUrl = "https://app-1.xx16x.shop"
        self.tgGroup = "https://t.me/tvshare23"
        self.brandActor = "🦋 TG群: @tvshare23"
        self.brandDirector = "🦋 蝴蝶影视"
        self._ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        self.options = {}

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
        elif extend:
            try:
                self.options = json.loads(extend)
            except Exception:
                self.options = {}
        return True

    def getName(self):
        return self.siteName

    def isVideoFormat(self, url):
        low = (url or "").lower()
        return any(k in low for k in (".m3u8", ".mp4", ".flv", ".mkv", ".ts"))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        self.options = {}

    def _fetch(self, target_url, data=None, referer="", headers_custom=None):
        if not target_url:
            return {"code": 0, "text": "", "bytes": b"", "err": "", "final_url": ""}
        if target_url.startswith("//"):
            target_url = "https:" + target_url
        elif target_url.startswith("/"):
            target_url = self.siteUrl + target_url

        headers = {
            "User-Agent": self._ua,
            "Referer": referer if referer else (self.siteUrl + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        if headers_custom:
            headers.update(headers_custom)

        req_data = None
        if data is not None:
            if isinstance(data, dict):
                req_data = urllib.parse.urlencode(data).encode("utf-8")
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                headers["X-Requested-With"] = "XMLHttpRequest"
            elif isinstance(data, (bytes, str)):
                req_data = data.encode("utf-8") if isinstance(data, str) else data

        for attempt in range(2):
            try:
                req = urllib.request.Request(target_url, data=req_data, headers=headers)
                with self.opener.open(req, timeout=8) as resp:
                    raw = resp.read()
                    enc = getattr(resp, "headers", {}).get("Content-Encoding", "")
                    if raw.startswith(b"\x1f\x8b") or enc == "gzip":
                        raw = gzip.decompress(raw)
                    elif enc == "deflate":
                        try:
                            raw = zlib.decompress(raw)
                        except Exception:
                            raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                    try:
                        text = raw.decode("utf-8")
                    except Exception:
                        text = raw.decode("latin1", errors="ignore")
                    return {"code": resp.getcode(), "text": text, "bytes": raw, "err": "", "final_url": resp.geturl()}
            except Exception as e:
                if attempt == 0:
                    continue
                return {"code": -1, "text": "", "bytes": b"", "err": str(e), "final_url": target_url}

        return {"code": -1, "text": "", "bytes": b"", "err": "timeout", "final_url": target_url}

    def _clean_m3u8_url(self, raw_str):
        if not raw_str:
            return ""
        m = re.search(r'(https?://(?:(?!localhost|127\.0\.0\.1)[^\s"\'\$<>])+\.m3u8[^\s"\'\$<>]*)', raw_str)
        if m:
            clean = m.group(1).replace("\\u002F", "/").replace("\\/", "")
            if ".m3u8" not in clean.lower():
                sep = "&" if "?" in clean else "?"
                clean = clean + sep + "format=.m3u8"
            return clean
        return ""

    def _extract_stream_from_html(self, html, page_url):
        prev_m = re.search(r'data-preview=["\']([^"\']+\.m3u8[^"\']*)["\']', html, re.I)
        if prev_m:
            return self._clean_m3u8_url(prev_m.group(1))

        src_m = re.search(r'<(?:source|video)[^>]+src=["\']([^"\']+\.m3u8[^"\']*)["\']', html, re.I)
        if src_m:
            return self._clean_m3u8_url(src_m.group(1))

        var_m = re.search(r'(?:videoUrl|playUrl|hlsUrl|url|source|path)\s*[:=]\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html, re.I)
        if var_m:
            return self._clean_m3u8_url(var_m.group(1))

        all_m3u8 = re.findall(r'https?://[^\s"\'\$<>]+\.m3u8[^\s"\'\$<>]*', html)
        for cand in all_m3u8:
            clean = self._clean_m3u8_url(cand)
            if clean:
                return clean
        return ""

    def _parse_card_list(self, html):
        cards = []
        raw_blocks = re.findall(r'(<a[^>]+href=["\'](?:/|\./)?\?play-\d+-\d+-\.html["\'][\s\S]*?</a>)', html, re.I)
        seen_ids = set()

        for block in raw_blocks:
            href_m = re.search(r'href=["\']([^"\']*\?play-(\d+)-\d+-\.html)["\']', block, re.I)
            if not href_m:
                continue
            vod_id = href_m.group(2).strip()

            if vod_id in seen_ids:
                continue
            seen_ids.add(vod_id)

            img_m = re.search(r'(?:data-original|data-src|data-echo|src)=["\']([^"\']+)["\']', block, re.I)
            pic = img_m.group(1).strip() if img_m else ""
            if pic.startswith("//"):
                pic = "https:" + pic
            elif pic.startswith("/"):
                pic = self.siteUrl + pic

            title_m = re.search(r'(?:alt|title)=["\']([^"\']+)["\']', block, re.I)
            name = ""
            if title_m:
                name = title_m.group(1).strip()
            if not name:
                text_clean = re.sub(r'<[^>]+>', '', block).strip()
                lines = [l.strip() for l in text_clean.split("\n") if l.strip()]
                name = lines[0] if lines else "视频"

            remarks_m = re.search(r'<span[^>]+class=["\'][^"\']*(?:duration|remarks|time|hd|tag)[^"\']*["\'][^>]*>([\s\S]*?)</span>', block, re.I)
            raw_remarks = re.sub(r'<[^>]+>', '', remarks_m.group(1)).strip() if remarks_m else ""

            cards.append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": format_remarks("蝴蝶影视", raw_remarks),
                "style": {"type": "rect", "ratio": 1.78}
            })

        return cards

    def homeContent(self, filter):
        classes = [
            {"type_id": "抖音", "type_name": "抖音"},
            {"type_id": "吃瓜", "type_name": "吃瓜"},
            {"type_id": "国产", "type_name": "国产"},
            {"type_id": "情色", "type_name": "情色"},
            {"type_id": "师生", "type_name": "师生"},
            {"type_id": "美腿", "type_name": "美腿"},
            {"type_id": "硬核", "type_name": "硬核"},
            {"type_id": "字幕", "type_name": "字幕"},
            {"type_id": "有码", "type_name": "有码"},
            {"type_id": "制服", "type_name": "制服"},
            {"type_id": "写真", "type_name": "写真"},
            {"type_id": "捆绑", "type_name": "捆绑"},
            {"type_id": "自淫", "type_name": "自淫"},
            {"type_id": "亚洲", "type_name": "亚洲"},
            {"type_id": "人妖", "type_name": "人妖"},
            {"type_id": "无码", "type_name": "无码"},
            {"type_id": "传媒", "type_name": "传媒"},
            {"type_id": "私拍", "type_name": "私拍"},
            {"type_id": "中文", "type_name": "中文"},
            {"type_id": "日本", "type_name": "日本"},
            {"type_id": "欧美", "type_name": "欧美"},
            {"type_id": "乱伦", "type_name": "乱伦"},
            {"type_id": "动漫", "type_name": "动漫"},
            {"type_id": "伦理", "type_name": "伦理"},
            {"type_id": "萝莉", "type_name": "萝莉"},
            {"type_id": "重口", "type_name": "重口"},
            {"type_id": "偷拍", "type_name": "偷拍"},
            {"type_id": "情侣", "type_name": "情侣"},
            {"type_id": "幼齿", "type_name": "幼齿"},
            {"type_id": "三级", "type_name": "三级"},
            {"type_id": "主播", "type_name": "主播"},
            {"type_id": "明星", "type_name": "明星"},
            {"type_id": "女优", "type_name": "女优"},
            {"type_id": "网红", "type_name": "网红"},
            {"type_id": "自拍", "type_name": "自拍"},
            {"type_id": "精品", "type_name": "精品"},
            {"type_id": "网曝", "type_name": "网曝"},
            {"type_id": "卡通", "type_name": "卡通"},
            {"type_id": "素人", "type_name": "素人"},
            {"type_id": "颜射", "type_name": "颜射"},
            {"type_id": "同性", "type_name": "同性"},
            {"type_id": "丝袜", "type_name": "丝袜"},
            {"type_id": "群交", "type_name": "群交"},
            {"type_id": "人妻", "type_name": "人妻"},
            {"type_id": "新人", "type_name": "新人"},
            {"type_id": "熟女", "type_name": "熟女"},
            {"type_id": "巨乳", "type_name": "巨乳"},
            {"type_id": "换脸", "type_name": "换脸"},
            {"type_id": "探花", "type_name": "探花"},
            {"type_id": "少女", "type_name": "少女"},
            {"type_id": "独家", "type_name": "独家"},
            {"type_id": "美女", "type_name": "美女"},
            {"type_id": "黑料", "type_name": "黑料"},
            {"type_id": "直播", "type_name": "直播"},
            {"type_id": "韩国", "type_name": "韩国"},
            {"type_id": "专区", "type_name": "专区"},
            {"type_id": "暗网", "type_name": "暗网"},
            {"type_id": "解说", "type_name": "解说"},
            {"type_id": "VR", "type_name": "VR"},
            {"type_id": "sm", "type_name": "sm"}
        ]

        sort_values = [
            {"n": "默认排序", "v": ""},
            {"n": "最新点播", "v": "db"},
            {"n": "最多点击", "v": "h"},
            {"n": "最多弹幕", "v": "d"},
            {"n": "最新弹幕", "v": "dt"},
            {"n": "最多评论", "v": "p"},
            {"n": "最新评论", "v": "pt"},
            {"n": "最多收藏", "v": "s"},
            {"n": "最新收藏", "v": "st"},
            {"n": "最多点赞", "v": "z"},
            {"n": "最新点赞", "v": "zt"}
        ]

        filters = {}
        for c in classes:
            filters[c["type_id"]] = [
                {
                    "key": "rq",
                    "name": "排序",
                    "init": "",
                    "value": sort_values
                }
            ]

        result = {"class": classes}
        if filter:
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        res = self._fetch(self.siteUrl + "/")
        cards = self._parse_card_list(res.get("text", ""))
        return {"list": cards[:16]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1

        sort_key = ""
        if isinstance(extend, dict):
            sort_key = extend.get("rq", "")

        cat_encoded = quote(str(tid).strip())
        if page == 1:
            req_url = "%s/?fenlei=%s" % (self.siteUrl, cat_encoded)
        else:
            req_url = "%s/?fenlei=%s-%d.html" % (self.siteUrl, cat_encoded, page)

        if sort_key:
            req_url += ("&rq=%s" % sort_key)

        res = self._fetch(req_url)
        cards = self._parse_card_list(res.get("text", ""))

        if not cards:
            return {
                "list": [],
                "page": page,
                "pagecount": page,
                "limit": 20,
                "total": 0
            }

        total_est = page * len(cards) + 120
        return {
            "list": cards,
            "page": page,
            "pagecount": page + 1,
            "limit": len(cards),
            "total": total_est
        }

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, (list, tuple)) else str(ids)
        target_id = str(raw_id).strip()
        detail_url = "%s/?play-%s-1-.html" % (self.siteUrl, target_id)

        res = self._fetch(detail_url)
        html = res.get("text", "")

        title_m = re.search(r'<title>(.*?)</title>', html, re.I)
        raw_title = title_m.group(1).split("-在线播放")[0].strip() if title_m else "超清正片"

        desc = ""
        desc_m = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html, re.I)
        if desc_m:
            desc = desc_m.group(1).strip()
        clean_content = "🦋 蝴蝶影视专线直连 | %s | 官方交流群: @tvshare23" % desc if desc else "🦋 蝴蝶影视专线加速播放 | 官方TG交流群：@tvshare23 | 4K高清原生极速画质"

        main_stream = self._extract_stream_from_html(html, detail_url)
        first_payload = "%s@@@%s" % (main_stream if main_stream else target_id, quote(raw_title))
        episodes = ["正片$%s" % first_payload]

        rec_matches = re.findall(r'<a[^>]+href=["\'](?:/|\./)?\?play-(\d+)-\d+-\.html["\'][^>]*>([\s\S]*?)</a>', html, re.I)
        seen_rec = set([target_id])
        rec_idx = 1

        for rec_id, inner in rec_matches:
            if rec_id in seen_rec:
                continue
            seen_rec.add(rec_id)

            t_m = re.search(r'(?:alt|title)=["\']([^"\']+)["\']', inner)
            rec_title = t_m.group(1) if t_m else re.sub(r'<[^>]+>', '', inner).strip()
            rec_title = clean_label(rec_title)

            if not rec_title or len(rec_title) < 2:
                continue

            ep_payload = "%s@@@%s" % (rec_id, quote(rec_title))
            episodes.append("%02d·%s$%s" % (rec_idx, rec_title, ep_payload))
            rec_idx += 1
            if rec_idx > 24:
                break

        vod = {
            "vod_id": target_id,
            "vod_name": raw_title,
            "vod_pic": "",
            "vod_bg": "",
            "vod_background": "",
            "vod_banner": "",
            "vod_actor": self.brandActor,
            "vod_director": self.brandDirector,
            "vod_remarks": format_remarks("蝴蝶影视", "全%s集" % len(episodes)),
            "vod_content": clean_content,
            "vod_play_from": "蝴蝶专线",
            "vod_play_url": "#".join(episodes)
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw_val = str(id).strip()
        target = raw_val
        desc_title = ""

        if "@@@" in raw_val:
            parts = raw_val.split("@@@", 1)
            target = parts[0]
            desc_title = unquote(parts[1])

        real_stream = ""
        if ".m3u8" in target.lower() or ".mp4" in target.lower():
            real_stream = target
        else:
            detail_url = "%s/?play-%s-1-.html" % (self.siteUrl, target)
            res = self._fetch(detail_url)
            html = res.get("text", "")
            real_stream = self._extract_stream_from_html(html, detail_url)

        headers = {
            "User-Agent": self._ua,
            "Referer": self.siteUrl + "/",
            "Origin": self.siteUrl
        }

        result = {
            "parse": 0,
            "playUrl": "",
            "url": real_stream,
            "header": headers
        }
        if desc_title:
            result["desc"] = desc_title
        return result

    def searchContent(self, key, quick, pg="1"):
        return {"list": [], "page": 1, "pagecount": 1, "limit": 20, "total": 0}

    def liveContent(self):
        return ""

    def action(self, action):
        return {"msg": "ok"}

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]
# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249834388&sig=f1031f1a2c946a40
