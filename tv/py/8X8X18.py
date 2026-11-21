#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import json
import base64
import html as html_lib
import urllib.request
import urllib.parse
from urllib.parse import urlparse, quote, unquote
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
    t = str(text).replace("$", "").replace("#", "").strip()
    t = re.sub(r"\s+", " ", t)
    return t[:24]

ALL_TAG_FILTERS = [
    {
        "key": "age",
        "name": "年龄",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "AI短剧", "v": "/tags/AI%e7%9f%ad%e5%89%a7/"},
            {"n": "年轻萝莉", "v": "/tags/%e5%b9%b4%e8%bd%bb%e8%90%9d%e8%8e%89/"},
            {"n": "人妻熟女", "v": "/tags/%e4%ba%ba%e5%a6%bb%e7%86%9f%e5%a5%b3/"},
            {"n": "初夜开苞", "v": "/tags/%e5%88%9d%e5%a4%9c%e5%bc%80%e8%8b%9e/"}
        ]
    },
    {
        "key": "career",
        "name": "职业",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "教师学生", "v": "/tags/%e6%95%99%e5%b8%88%e5%ad%a6%e7%94%9f/"},
            {"n": "名模空姐", "v": "/tags/%e5%90%8d%e6%a8%a1%e7%a9%ba%e5%a7%90/"},
            {"n": "医生护士", "v": "/tags/%e5%8c%bb%e7%94%9f%e6%8a%a4%e5%a3%ab/"},
            {"n": "角色扮演", "v": "/tags/%e8%a7%92%e8%89%b2%e6%89%ae%e6%bc%94/"}
        ]
    },
    {
        "key": "plot",
        "name": "剧情",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "家庭乱伦", "v": "/tags/%e5%ae%b6%e5%ba%ad%e4%b9%b1%e4%bc%a6/"},
            {"n": "奸夫淫妇", "v": "/tags/%e5%a5%b8%e5%a4%ab%e6%b7%ab%e5%a6%87/"}
        ]
    },
    {
        "key": "gossip",
        "name": "吃瓜",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "网红主播", "v": "/tags/%e7%bd%91%e7%ba%a2%e4%b8%bb%e6%92%ad/"},
            {"n": "自拍偷拍", "v": "/tags/%e8%87%aa%e6%8b%8d%e5%81%b7%e6%8b%8d/"}
        ]
    },
    {
        "key": "body",
        "name": "身材",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "明星女优", "v": "/tags/%e6%98%8e%e6%98%9f%e5%a5%b3%e4%bc%98/"},
            {"n": "巨乳肥臀", "v": "/tags/%e5%b7%a8%e4%b9%b3%e8%82%a5%e8%87%80/"},
            {"n": "极品女神", "v": "/tags/%e6%9e%81%e5%93%81%e5%a5%b3%e7%a5%9e/"},
            {"n": "美穴白虎", "v": "/tags/%e7%be%8e%e7%a9%b4%e7%99%bd%e8%99%8e/"}
        ]
    },
    {
        "key": "multi",
        "name": "多人",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "两女一男", "v": "/tags/%e4%b8%a4%e5%a5%b3%e4%b8%80%e7%94%b7/"},
            {"n": "多人群P", "v": "/tags/%e5%a4%9a%e4%ba%ba%e7%be%a4P/"},
            {"n": "两男一女", "v": "/tags/%e4%b8%a4%e7%94%b7%e4%b8%80%e5%a5%b3/"}
        ]
    },
    {
        "key": "pose",
        "name": "姿势",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "老汉推车", "v": "/tags/%e8%80%81%e6%b1%89%e6%8e%a8%e8%bd%a6/"},
            {"n": "自慰喷水", "v": "/tags/%e8%87%aa%e6%85%b0%e5%96%b7%e6%b0%b4/"},
            {"n": "女上男下", "v": "/tags/%e5%a5%b3%e4%b8%8a%e7%94%b7%e4%b8%8b/"},
            {"n": "推油乳交", "v": "/tags/%e6%8e%a8%e6%b2%b9%e4%b9%b3%e4%ba%a4/"},
            {"n": "打打飞机", "v": "/tags/%e6%89%93%e6%89%93%e9%a3%9e%e6%9c%ba/"},
            {"n": "口交深喉", "v": "/tags/%e5%8f%a3%e4%ba%a4%e6%b7%b1%e5%96%89/"},
            {"n": "舔逼品玉", "v": "/tags/%e8%88%94%e9%80%bc%e5%93%81%e7%8e%89/"},
            {"n": "颜射吞精", "v": "/tags/%e9%a2%9c%e5%b0%84%e5%90%9e%e7%b2%be/"},
            {"n": "69互舔", "v": "/tags/69%e4%ba%92%e8%88%94/"}
        ]
    },
    {
        "key": "reaction",
        "name": "反应",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "抽插特写", "v": "/tags/%e6%8a%bd%e6%8f%92%e7%89%b9%e5%86%99/"},
            {"n": "强奸迷奸", "v": "/tags/%e5%bc%ba%e5%a5%b8%e8%bf%b7%e5%a5%b8/"}
        ]
    },
    {
        "key": "dress",
        "name": "服装",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "情趣内衣", "v": "/tags/%e6%83%85%e8%b6%a3%e5%86%85%e8%a1%a3/"},
            {"n": "情趣丝袜", "v": "/tags/%e6%83%85%e8%b6%a3%e4%b8%9d%e8%a2%9c/"},
            {"n": "制服诱惑", "v": "/tags/%e5%88%b6%e6%9c%8d%e8%af%b1%e6%83%91/"}
        ]
    },
    {
        "key": "foot",
        "name": "足控",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "足交恋足", "v": "/tags/%e8%b6%b3%e4%ba%a4%e6%81%8b%e8%b6%b3/"}
        ]
    },
    {
        "key": "scene",
        "name": "场景",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "户外啪啪", "v": "/tags/%e6%88%b7%e5%a4%96%e5%95%aa%e5%95%aa/"},
            {"n": "刺激车震", "v": "/tags/%e5%88%ba%e6%bf%80%e8%bd%a6%e9%9c%87/"},
            {"n": "成人玩具", "v": "/tags/%e6%88%90%e4%ba%ba%e7%8e%a9%e5%85%b7/"},
            {"n": "大庭广众", "v": "/tags/%e5%a4%a7%e5%ba%ad%e5%b9%bf%e4%bc%97/"},
            {"n": "厕所偷拍", "v": "/tags/%e5%8e%95%e6%89%80%e5%81%b7%e6%8b%8d/"}
        ]
    },
    {
        "key": "special",
        "name": "特殊",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "百合拉拉", "v": "/tags/%e7%99%be%e5%90%88%e6%8b%89%e6%8b%89/"},
            {"n": "奇葩怪癖", "v": "/tags/%e5%a5%87%e8%91%a9%e6%80%aa%e7%99%96/"}
        ]
    }
]

class Spider(SpiderBase):
    def __init__(self):
        super(Spider, self).__init__()
        self.siteName = "8x8x"
        self.entryUrl = "https://www.7xb38c.com"
        self.siteUrl = "https://462555.yjbvzqq3.com"
        self.bodyPrefix = "/tym4"
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
        self._auto_heal_route()
        return True

    def getName(self):
        return self.siteName

    def isVideoFormat(self, url):
        if not url:
            return False
        low = url.lower()
        if any(bad in low for bad in ("preview.mp4", "sample.mp4", "trailer.mp4", "native-ad", "domain.gif")):
            return False
        return any(k in low for k in (".m3u8", ".mp4", ".flv", ".ts", "format=.m3u8"))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        self.options = {}

    def _clean_m3u8_url(self, raw_str):
        if not raw_str:
            return ""
        m = re.search(r'(https?://(?:(?!localhost|127\.0\.0\.1)[^\s"\'\$<>])+\.m3u8[^\s"\'\$<>]*)', raw_str)
        if m:
            return m.group(1).replace("\\u002F", "/").replace("\\/", "")
        return ""

    def _fetch(self, target_url, referer=""):
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

        last_err = ""
        for attempt in range(2):
            try:
                req = urllib.request.Request(target_url, headers=headers)
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
                    try:
                        text = raw.decode("utf-8")
                    except Exception:
                        text = raw.decode("latin1", errors="ignore")
                    return {"code": code, "text": text, "bytes": raw, "err": "", "final_url": final_url}
            except urllib.error.HTTPError as e:
                last_err = "HTTP %s" % e.code
                if e.code in (451, 403, 429) and attempt == 0:
                    continue
                err_raw = ""
                try:
                    err_raw = e.read().decode("utf-8", errors="ignore")
                except Exception:
                    pass
                return {"code": e.code, "text": err_raw, "bytes": b"", "err": str(e), "final_url": target_url}
            except Exception as e:
                last_err = str(e)
                if attempt == 0:
                    continue
                return {"code": -1, "text": "", "bytes": b"", "err": str(e), "final_url": target_url}

        return {"code": -1, "text": "", "bytes": b"", "err": last_err, "final_url": target_url}

    def _auto_heal_route(self):
        try:
            entry_res = self._fetch(self.entryUrl)
            final_url = entry_res.get("final_url", "")
            if final_url and final_url.startswith("http"):
                parsed = urllib.parse.urlparse(final_url)
                self.siteUrl = "%s://%s" % (parsed.scheme, parsed.netloc)

            root_res = self._fetch(self.siteUrl + "/")
            root_html = root_res.get("text", "")

            m_body = re.search(r'data-body-url=["\']?(/[^"\'\s>]+)', root_html)
            if m_body:
                self.bodyPrefix = "/" + m_body.group(1).strip("/")
                return

            m_app = re.search(r'src=["\']?/assets/(app\.[a-f0-9]+\.js)["\']?', root_html)
            if m_app:
                js_url = self.siteUrl + "/assets/" + m_app.group(1)
                js_res = self._fetch(js_url, referer=self.siteUrl + "/")
                js_text = js_res.get("text", "")
                m_b64 = re.search(r'atob\(["\']([A-Za-z0-9+/=]+)["\']\)', js_text)
                if m_b64:
                    dec = base64.b64decode(m_b64.group(1)).decode("utf-8", errors="ignore")
                    self.bodyPrefix = "/" + dec.strip("/")
        except Exception:
            pass

    def _extract_cards(self, html):
        cards = []
        if not html:
            return cards
        pattern = r'<a\s+href=([^\s>]+)\s+class=["\']?card group["\']?>([\s\S]*?)</a>'
        for m in re.finditer(pattern, html, re.I):
            href = m.group(1).strip('"\'').strip()
            inner = m.group(2)
            tm = re.search(r'class=card-title>([^<]+)<', inner, re.I)
            if not tm:
                tm = re.search(r'class=["\']?card-title["\']?>([^<]+)<', inner, re.I)
            im = re.search(r'data-src=([^\s>]+)', inner, re.I)
            name = tm.group(1).strip() if tm else "精彩视频"
            pic = im.group(1).strip('"\'') if im else ""
            cards.append({
                "vod_id": href,
                "vod_name": name,
                "vod_pic": pic,
                "vod_remarks": format_remarks("蝴蝶影视", "超清"),
                "style": {"type": "rect", "ratio": 1.78}
            })
        return cards

    def homeContent(self, filter):
        classes = [
            {"type_id": "1", "type_name": "🇨🇳 国产精品"},
            {"type_id": "2", "type_name": "🇯🇵 日韩精选"},
            {"type_id": "3", "type_name": "🇺🇸 欧美高清"},
            {"type_id": "4", "type_name": "🎌 动漫二次元"},
            {"type_id": "5", "type_name": "🔞 三级伦理"},
            {"type_id": "all_tags", "type_name": "🏷️ 热门标签"}
        ]
        result = {"class": classes}
        if filter:
            result["filters"] = {
                "all_tags": ALL_TAG_FILTERS
            }
        return result

    def homeVideoContent(self):
        home_url = self.siteUrl + self.bodyPrefix + "/"
        res = self._fetch(home_url)
        cards = self._extract_cards(res.get("text", ""))
        if not cards:
            self._auto_heal_route()
            home_url = self.siteUrl + self.bodyPrefix + "/"
            res = self._fetch(home_url)
            cards = self._extract_cards(res.get("text", ""))
        return {"list": cards[:30]}

    def categoryContent(self, tid, pg, filter, extend):
        page = 1
        try:
            page = max(int(str(pg).strip()), 1)
        except Exception:
            page = 1

        tid_str = str(tid).strip()
        extend_dict = extend if isinstance(extend, dict) else {}

        selected_tag_url = ""
        if tid_str == "all_tags":
            for flt in ALL_TAG_FILTERS:
                val = extend_dict.get(flt["key"], "")
                if val:
                    selected_tag_url = val
                    break

        if selected_tag_url:
            base_path = selected_tag_url.rstrip("/")
        elif tid_str.startswith("/tags/"):
            base_path = tid_str.rstrip("/")
        elif tid_str == "all_tags":
            base_path = "/category/1"
        else:
            base_path = "/category/%s" % tid_str.strip("/")

        target_url = self.siteUrl + self.bodyPrefix + base_path + "/page/%s/" % page
        res = self._fetch(target_url)
        html = res.get("text", "")
        cards = self._extract_cards(html)

        if not cards and page == 1:
            self._auto_heal_route()
            target_url = self.siteUrl + self.bodyPrefix + base_path + "/page/%s/" % page
            res = self._fetch(target_url)
            html = res.get("text", "")
            cards = self._extract_cards(html)

        if not cards:
            return {
                "list": [],
                "page": int(page),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }

        max_p = page
        mp = re.search(r'data-max=["\']?(\d+)', html, re.I)
        if mp:
            try:
                max_p = int(mp.group(1))
            except Exception:
                max_p = page + 10
        else:
            max_p = page + 1 if len(cards) >= 10 else page

        return {
            "list": cards,
            "page": int(page),
            "pagecount": int(max_p),
            "limit": int(len(cards)),
            "total": int(max_p * len(cards))
        }

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, (list, tuple)) else str(ids)
        vid = str(raw_id).strip()

        if not vid.startswith("/vd/"):
            clean_vid = vid.strip("/")
            vid = "/vd/%s/" % clean_vid

        detail_url = self.siteUrl + self.bodyPrefix + vid
        res = self._fetch(detail_url)
        html = res.get("text", "")

        if not html:
            self._auto_heal_route()
            detail_url = self.siteUrl + self.bodyPrefix + vid
            res = self._fetch(detail_url)
            html = res.get("text", "")

        tm = re.search(r'<title>([^<]+)</title>', html, re.I)
        title = tm.group(1).replace(" - 8x8x", "").strip() if tm else "蝴蝶专线视频"

        pm = re.search(r'data-poster=([^\s>]+)', html, re.I)
        pic = pm.group(1).strip('"\'') if pm else ""

        mm = re.search(r'data-m3u8=([^\s>]+)', html, re.I)
        m3u8_path = mm.group(1).strip('"\'') if mm else ""

        play_routes = []
        play_urls = []

        route_keys = [("data-route1", "专线1"), ("data-route2", "专线2"), ("data-route3", "专线3")]
        for r_attr, r_label in route_keys:
            rm = re.search(r'%s=([^\s>]+)' % r_attr, html, re.I)
            if rm and m3u8_path:
                r_base = rm.group(1).strip('"\'')
                full_stream = r_base.rstrip("/") + "/" + m3u8_path.lstrip("/")
                clean_stream = self._clean_m3u8_url(full_stream) or full_stream
                play_routes.append(r_label)
                play_urls.append("正片$%s" % clean_stream)

        if not play_routes and m3u8_path:
            clean_m = self._clean_m3u8_url(m3u8_path) or m3u8_path
            play_routes.append("蝴蝶专线")
            play_urls.append("正片$%s" % clean_m)
        elif not play_routes:
            play_routes.append("蝴蝶专线")
            play_urls.append("正片$%s/placeholder.m3u8" % self.siteUrl)

        rec_episodes = []
        rec_matches = re.finditer(r'<a\s+href=([^\s>]+)\s+class=["\']?card group["\']?>([\s\S]*?)</a>', html, re.I)
        seen_rec = set([vid])
        rec_idx = 1

        for rm in rec_matches:
            r_href = rm.group(1).strip('"\'').strip()
            if r_href in seen_rec:
                continue
            r_inner = rm.group(2)
            r_tm = re.search(r'class=card-title>([^<]+)<', r_inner, re.I)
            if not r_tm:
                r_tm = re.search(r'class=["\']?card-title["\']?>([^<]+)<', r_inner, re.I)
            r_title = r_tm.group(1).strip() if r_tm else ""
            if not r_title:
                continue

            seen_rec.add(r_href)
            clean_t = clean_label(r_title)
            rec_episodes.append("%02d·%s$%s@@@%s" % (rec_idx, clean_t, r_href, quote(r_title)))
            rec_idx += 1
            if rec_idx > 24:
                break

        final_from = []
        final_urls = []
        for i in range(len(play_routes)):
            rf = play_routes[i]
            ru = play_urls[i]
            if rec_episodes:
                combined_episodes = ru + "#" + "#".join(rec_episodes)
            else:
                combined_episodes = ru
            final_from.append(rf)
            final_urls.append(combined_episodes)

        desc = "🦋 蝴蝶影视专线直连 | 高清极速画质 | 官方交流群: @tvshare23"

        vod = {
            "vod_id": raw_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_bg": pic,
            "vod_background": pic,
            "vod_banner": pic,
            "vod_actor": self.brandActor,
            "vod_director": self.brandDirector,
            "vod_remarks": format_remarks("蝴蝶影视", "全%s部连播" % (len(rec_episodes) + 1)),
            "vod_content": desc,
            "vod_play_from": "$$$".join(final_from),
            "vod_play_url": "$$$".join(final_urls)
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw_val = str(id).strip()
        desc_title = ""

        if "@@@" in raw_val:
            target_href, raw_title = raw_val.split("@@@", 1)
            desc_title = unquote(raw_title)
        else:
            target_href = raw_val

        real_stream = ""
        if target_href.startswith("http") and (".m3u8" in target_href.lower() or ".mp4" in target_href.lower()):
            real_stream = target_href
        else:
            sub_vid = target_href
            if not sub_vid.startswith("/vd/"):
                sub_vid = "/vd/%s/" % sub_vid.strip("/")
            sub_url = self.siteUrl + self.bodyPrefix + sub_vid
            res = self._fetch(sub_url)
            sub_html = res.get("text", "")
            mm = re.search(r'data-m3u8=([^\s>]+)', sub_html, re.I)
            if mm:
                m3u8_path = mm.group(1).strip('"\'')
                rm = re.search(r'data-route1=([^\s>]+)', sub_html, re.I)
                if not rm:
                    rm = re.search(r'data-route2=([^\s>]+)', sub_html, re.I)
                if not rm:
                    rm = re.search(r'data-route3=([^\s>]+)', sub_html, re.I)
                if rm:
                    real_stream = rm.group(1).strip('"\'').rstrip("/") + "/" + m3u8_path.lstrip("/")
                else:
                    real_stream = m3u8_path

        clean_play_stream = self._clean_m3u8_url(real_stream) or real_stream
        if clean_play_stream and ".m3u8" not in clean_play_stream.lower() and ".mp4" not in clean_play_stream.lower():
            sep = "&" if "?" in clean_play_stream else "?"
            clean_play_stream = clean_play_stream + sep + "format=.m3u8"

        headers = {
            "User-Agent": self._ua,
            "Referer": self.siteUrl + "/"
        }

        result = {
            "parse": 0 if clean_play_stream and clean_play_stream.startswith("http") else 1,
            "playUrl": "",
            "url": clean_play_stream,
            "header": headers
        }
        if desc_title:
            result["desc"] = desc_title
        return result

    def searchContent(self, key, quick, pg="1"):
        page = 1
        try:
            page = max(int(str(pg).strip()), 1)
        except Exception:
            page = 1

        api_url = "%s/api/search/video?keyword=%s&page=%s" % (self.siteUrl, quote(str(key).strip()), page)
        res = self._fetch(api_url)
        raw_text = res.get("text", "")

        try:
            data = json.loads(raw_text)
        except Exception:
            data = {}

        if data.get("code") != 0:
            return {
                "list": [],
                "page": int(page),
                "pagecount": 1,
                "limit": 20,
                "total": 0
            }

        dl = data.get("data", {})
        items = dl.get("list", [])
        videos = []
        for item in items:
            vid_val = item.get("id")
            title_val = item.get("title", "")
            pic_val = item.get("litpic", "")
            type_val = item.get("typename", "")
            if vid_val:
                videos.append({
                    "vod_id": "/vd/%s/" % vid_val,
                    "vod_name": title_val,
                    "vod_pic": pic_val,
                    "vod_remarks": format_remarks("蝴蝶影视", type_val),
                    "style": {"type": "rect", "ratio": 1.78}
                })

        total_pages = dl.get("total_pages", page)
        total_items = dl.get("total", len(videos))

        return {
            "list": videos,
            "page": int(page),
            "pagecount": int(total_pages) if total_pages else int(page),
            "limit": int(len(videos)),
            "total": int(total_items) if total_items else int(len(videos))
        }

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249321361&sig=a4259edb62d13655
