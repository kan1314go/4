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
import urllib.error
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
        def getProxyUrl(self): return "http://127.0.0.1:9978/proxy?do=py"


class Spider(SpiderBase):
    def __init__(self):
        super(Spider, self).__init__()
        self.navUrls = ["https://x99dh.net", "https://x99dh.lat", "https://x99dh.cc", "https://x99dh.one"]
        self.targetSiteName = "三级片资源, 稀缺资源"
        self.cacheKey = "ptt01_direct_auto_heal_host"
        self.defaultHost = "https://ptt01.com"
        self.siteUrl = self.defaultHost
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
        
        self._refresh_site_url_from_nav()
        return True

    def getName(self):
        return "蝴蝶影院·动态直跳自愈版"

    def isVideoFormat(self, url):
        low = (url or "").lower()
        return any(k in low for k in (".m3u8", ".mp4", ".flv", ".mkv", ".ts", ".mpd"))

    def manualVideoCheck(self):
        return False

    def _decompress(self, raw, enc=""):
        if not raw:
            return b""
        if raw.startswith(b"\x1f\x8b") or enc == "gzip":
            try:
                return gzip.decompress(raw)
            except Exception:
                pass
        elif enc == "deflate":
            try:
                return zlib.decompress(raw)
            except Exception:
                try:
                    return zlib.decompress(raw, -zlib.MAX_WBITS)
                except Exception:
                    pass
        return raw

    def _refresh_site_url_from_nav(self):
        headers = {
            "User-Agent": self._ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Cache-Control": "max-age=0",
            "Connection": "close",
            "Sec-Ch-Ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

        for nav in self.navUrls:
            raw = b""
            enc = ""
            try:
                req = urllib.request.Request(nav, headers=headers)
                with self.opener.open(req, timeout=8) as resp:
                    raw = resp.read()
                    enc = getattr(resp, "headers", {}).get("Content-Encoding", "")
            except urllib.error.HTTPError as e:
                try:
                    raw = e.read()
                    enc = getattr(e, "headers", {}).get("Content-Encoding", "")
                except Exception:
                    raw = b""
            except Exception:
                continue

            if not raw:
                continue

            decomp = self._decompress(raw, enc)
            try:
                html_text = decomp.decode("utf-8")
            except Exception:
                html_text = decomp.decode("latin1", errors="ignore")

            if not html_text:
                continue

            b64_blocks = re.findall(r'["\']([A-Za-z0-9+/=]{100,})["\']', html_text)
            for b in b64_blocks:
                try:
                    dec = base64.b64decode(b).decode("utf-8", errors="ignore")
                    unq = urllib.parse.unquote(dec)
                    if "[" in unq and "{" in unq and ("三级片资源" in unq or "稀缺资源" in unq):
                        site_list = json.loads(unq)
                        if isinstance(site_list, list):
                            for item in site_list:
                                item_name = str(item.get("name", "")).strip()
                                if item_name == self.targetSiteName or "三级片资源" in item_name or "稀缺资源" in item_name:
                                    direct_target_url = item.get("url", "").strip()
                                    if direct_target_url:
                                        parsed = urllib.parse.urlparse(direct_target_url)
                                        base_host = "%s://%s" % (parsed.scheme, parsed.netloc)
                                        self.siteUrl = base_host
                                        self.setCache(self.cacheKey, base_host)
                                        return True
                except Exception:
                    continue

        cached_host = self.getCache(self.cacheKey)
        if cached_host and str(cached_host).startswith("http"):
            self.siteUrl = str(cached_host).strip().rstrip("/")
            return True

        self.siteUrl = self.defaultHost
        return False

    def _fetch(self, target_url, referer="", retry_on_fail=True):
        if not target_url:
            return {"code": 0, "text": "", "err": "", "final_url": ""}
        if target_url.startswith("//"):
            target_url = "https:" + target_url
        elif target_url.startswith("/"):
            target_url = self.siteUrl + target_url

        headers = {
            "User-Agent": self._ua,
            "Referer": referer if referer else (self.siteUrl + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

        try:
            req = urllib.request.Request(target_url, headers=headers)
            with self.opener.open(req, timeout=10) as resp:
                code = resp.getcode()
                final_url = resp.geturl()
                raw = resp.read()
                enc = getattr(resp, "headers", {}).get("Content-Encoding", "")
                decomp = self._decompress(raw, enc)
                try:
                    text = decomp.decode("utf-8")
                except Exception:
                    text = decomp.decode("latin1", errors="ignore")
                return {"code": code, "text": text, "err": "", "final_url": final_url}
        except urllib.error.HTTPError as e:
            if retry_on_fail and e.code in (404, 451, 502, 503):
                if self._refresh_site_url_from_nav():
                    parsed = urllib.parse.urlparse(target_url)
                    new_target = "%s%s" % (self.siteUrl, parsed.path)
                    if parsed.query:
                        new_target += "?" + parsed.query
                    return self._fetch(new_target, referer=referer, retry_on_fail=False)
            return {"code": e.code, "text": "", "err": str(e), "final_url": target_url}
        except Exception as e:
            if retry_on_fail:
                if self._refresh_site_url_from_nav():
                    parsed = urllib.parse.urlparse(target_url)
                    new_target = "%s%s" % (self.siteUrl, parsed.path)
                    if parsed.query:
                        new_target += "?" + parsed.query
                    return self._fetch(new_target, referer=referer, retry_on_fail=False)
            return {"code": -1, "text": "", "err": str(e), "final_url": target_url}

    def homeContent(self, filter):
        classes = [
            {"type_name": "🎬 电影", "type_id": "1"},
            {"type_name": "📺 电视剧", "type_id": "3"},
            {"type_name": "🌸 动漫", "type_id": "4"},
            {"type_name": "🎤 综艺", "type_id": "2"},
            {"type_name": "⚡ 短剧", "type_id": "66"},
            {"type_name": "⚽ 体育", "type_id": "53"}
        ]

        year_list = [
            {"n": "全部", "v": ""},
            {"n": "2026", "v": "2026"},
            {"n": "2025", "v": "2025"},
            {"n": "2024", "v": "2024"},
            {"n": "2023", "v": "2023"},
            {"n": "2022", "v": "2022"},
            {"n": "2021", "v": "2021"},
            {"n": "2020", "v": "2020"},
            {"n": "2019", "v": "2019"},
            {"n": "2018", "v": "2018"},
            {"n": "2017", "v": "2017"},
            {"n": "2016", "v": "2016"}
        ]

        filters = {
            "1": [
                {
                    "key": "c",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "伦理", "v": "33"},
                        {"n": "动作", "v": "5"},
                        {"n": "喜剧", "v": "6"},
                        {"n": "爱情", "v": "7"},
                        {"n": "科幻", "v": "8"},
                        {"n": "恐怖", "v": "9"},
                        {"n": "犯罪", "v": "10"},
                        {"n": "战争", "v": "11"},
                        {"n": "动漫", "v": "12"},
                        {"n": "剧情", "v": "13"},
                        {"n": "纪录", "v": "30"},
                        {"n": "悬疑", "v": "34"},
                        {"n": "动画", "v": "35"},
                        {"n": "解说", "v": "32"},
                        {"n": "其他", "v": "48"}
                    ]
                },
                {
                    "key": "area_id",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "2"},
                        {"n": "香港", "v": "5"},
                        {"n": "台湾", "v": "4"},
                        {"n": "韩国", "v": "17"},
                        {"n": "日本", "v": "18"},
                        {"n": "欧美", "v": "6"},
                        {"n": "泰国", "v": "10"},
                        {"n": "印度", "v": "14"},
                        {"n": "其他", "v": "3"}
                    ]
                },
                {
                    "key": "year",
                    "name": "年代",
                    "value": year_list
                }
            ],
            "3": [
                {
                    "key": "c",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "19"},
                        {"n": "香港", "v": "20"},
                        {"n": "台湾", "v": "81"},
                        {"n": "日本", "v": "83"},
                        {"n": "韩国", "v": "82"},
                        {"n": "欧美", "v": "22"},
                        {"n": "泰国", "v": "92"},
                        {"n": "其他", "v": "23"}
                    ]
                },
                {
                    "key": "year",
                    "name": "年代",
                    "value": year_list
                }
            ],
            "4": [
                {
                    "key": "c",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "26"},
                        {"n": "日本", "v": "86"},
                        {"n": "韩国", "v": "87"},
                        {"n": "欧美", "v": "27"},
                        {"n": "其他", "v": "28"}
                    ]
                },
                {
                    "key": "year",
                    "name": "年代",
                    "value": year_list
                }
            ],
            "2": [
                {
                    "key": "c",
                    "name": "地区",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "大陆", "v": "15"},
                        {"n": "台湾", "v": "89"},
                        {"n": "香港", "v": "88"},
                        {"n": "日本", "v": "90"},
                        {"n": "韩国", "v": "91"},
                        {"n": "欧美", "v": "18"},
                        {"n": "其他", "v": "16"}
                    ]
                },
                {
                    "key": "year",
                    "name": "年代",
                    "value": year_list
                }
            ],
            "66": [
                {
                    "key": "c",
                    "name": "类型",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "爽剧", "v": "67"},
                        {"n": "言情", "v": "68"},
                        {"n": "穿越", "v": "70"},
                        {"n": "悬疑", "v": "71"},
                        {"n": "古装", "v": "73"},
                        {"n": "都市", "v": "80"},
                        {"n": "甜宠", "v": "84"},
                        {"n": "恋爱", "v": "85"},
                        {"n": "其他", "v": "74"}
                    ]
                },
                {
                    "key": "year",
                    "name": "年代",
                    "value": year_list
                }
            ],
            "53": [
                {
                    "key": "c",
                    "name": "项目",
                    "value": [
                        {"n": "全部", "v": ""},
                        {"n": "足球", "v": "54"},
                        {"n": "篮球", "v": "55"},
                        {"n": "游戏", "v": "59"},
                        {"n": "撞球", "v": "63"},
                        {"n": "网球", "v": "64"},
                        {"n": "其他", "v": "93"}
                    ]
                },
                {
                    "key": "year",
                    "name": "年代",
                    "value": year_list
                }
            ]
        }

        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        return {"list": []}

    def _parse_card_list(self, html_text):
        cards = []
        seen = set()
        item_blocks = re.findall(r'(<div[^>]+class=["\'][^"\']*item[^"\']*["\'][\s\S]*?</div>\s*</div>\s*</div>)', html_text, re.I)
        if not item_blocks:
            item_blocks = re.findall(r'(<div[^>]+class=["\'][^"\']*card[^"\']*["\'][\s\S]*?</div>\s*</div>)', html_text, re.I)

        for block in item_blocks:
            m_href = re.search(r'href=["\'](/(\d+))["\']', block)
            if not m_href:
                continue
            path = m_href.group(1)
            if path in seen:
                continue

            title = ""
            m_alt = re.search(r'<img[^>]+alt=["\']([^"\']+)["\']', block, re.I)
            if m_alt and m_alt.group(1).strip():
                title = m_alt.group(1).strip()

            if not title:
                m_title = re.search(r'title=["\']([^"\']+)["\']', block)
                if m_title and m_title.group(1).strip():
                    title = m_title.group(1).strip()

            if not title:
                m_text_link = re.search(r'<a[^>]+href=["\']/%s["\'][^>]*>([\s\S]*?)</a>' % m_href.group(2), block, re.I)
                if m_text_link:
                    cand_t = re.sub(r'<[^>]+>', '', m_text_link.group(1)).strip()
                    if cand_t:
                        title = cand_t

            if not title:
                title = "视频 %s" % m_href.group(2)

            img_src = ""
            m_img = re.search(r'(?:src|data-original|data-src)=["\']([^"\']+)["\']', block, re.I)
            if m_img:
                cand = m_img.group(1).strip()
                if not any(bad in cand.lower() for bad in ("logo", "avatar", "icon", ".svg", "data:image")):
                    img_src = ("https:" + cand) if cand.startswith("//") else ((self.siteUrl + cand) if cand.startswith("/") else cand)

            badge_parts = []
            m_left = re.search(r'class=["\'][^"\']*imagelabel-bottom-left[^"\']*["\'][^>]*>([\s\S]*?)</div>', block, re.I)
            if m_left:
                c_left = re.sub(r'<[^>]+>', '', m_left.group(1)).strip()
                if c_left:
                    badge_parts.append(c_left)

            m_right = re.search(r'class=["\'][^"\']*imagelabel-bottom-right[^"\']*["\'][^>]*>([\s\S]*?)</div>', block, re.I)
            if m_right:
                c_right = re.sub(r'<[^>]+>', '', m_right.group(1)).strip()
                if c_right:
                    badge_parts.append(c_right)

            if not badge_parts:
                badges = re.findall(r'<span[^>]+class=["\'][^"\']*badge[^"\']*["\'][^>]*>([^<]+)</span>', block, re.I)
                for bg in badges:
                    cl_b = bg.strip()
                    if cl_b and cl_b not in badge_parts and not cl_b.startswith("fa-"):
                        badge_parts.append(cl_b)

            source_remark = " ".join(badge_parts).strip()
            remarks = ("蝴蝶影视 | %s" % source_remark) if source_remark else "蝴蝶影视"

            seen.add(path)
            cards.append({
                "vod_id": path,
                "vod_name": html_lib.unescape(title),
                "vod_pic": img_src,
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 0.75}
            })
        return cards

    def categoryContent(self, tid, pg, filter, extend):
        clean_tid = str(tid).replace("/p/", "").strip("/")
        ext_dict = extend if isinstance(extend, dict) else {}

        c_val = str(ext_dict.get("c", "")).strip()
        area_id_val = str(ext_dict.get("area_id", "")).strip()
        year_val = str(ext_dict.get("year", "")).strip()
        page_val = str(pg) if str(pg).isdigit() else "1"

        if c_val:
            base_path = "/p/%s/c/%s" % (clean_tid, c_val)
        else:
            base_path = "/p/%s" % clean_tid

        query_params = []
        if area_id_val:
            query_params.append("area_id=%s" % area_id_val)
        if year_val:
            query_params.append("year=%s" % year_val)
        if int(page_val) > 1:
            query_params.append("page=%s" % page_val)

        if query_params:
            req_path = "%s?%s" % (base_path, "&".join(query_params))
        else:
            req_path = base_path

        res = self._fetch(req_path)
        cards = self._parse_card_list(res.get("text", ""))

        return {"page": int(page_val), "pagecount": 99, "limit": len(cards), "total": 9999, "list": cards}

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, (list, tuple)) else str(ids)
        vid_m = re.search(r'(\d+)', raw_id)
        if not vid_m:
            return {"list": []}
        vid = vid_m.group(1)

        play_home_path = "/%s" % vid
        detail_path = "/v/%s" % vid

        res_play = self._fetch(play_home_path)
        play_html = res_play.get("text", "")

        res_detail = self._fetch(detail_path)
        detail_html = res_detail.get("text", "")

        title_m = re.search(r'<title>(.*?)</title>', detail_html if detail_html else play_html, re.I)
        vod_name = title_m.group(1).split("-")[0].strip() if title_m else ("视频 %s" % vid)

        vod_pic = ""
        m_og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', play_html, re.I)
        if not m_og_img:
            m_og_img = re.search(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', detail_html, re.I)
        if m_og_img:
            vod_pic = m_og_img.group(1).strip()
        if not vod_pic:
            m_img = re.search(r'<img[^>]+src=["\']([^"\']+/images/node/[^"\']+)["\']', detail_html if detail_html else play_html, re.I)
            if m_img:
                vod_pic = m_img.group(1).strip()

        if vod_pic.startswith("//"):
            vod_pic = "https:" + vod_pic
        elif vod_pic.startswith("/"):
            vod_pic = self.siteUrl + vod_pic

        vod_year = ""
        m_yr = re.search(r'<th>年代</th>\s*<td>([^<]+)</td>', detail_html, re.I)
        if m_yr:
            vod_year = m_yr.group(1).strip()

        vod_remarks = "蝴蝶影视"
        m_st = re.search(r'<th>状态</th>\s*<td>([^<]+)</td>', detail_html, re.I)
        if m_st:
            st_text = m_st.group(1).strip()
            vod_remarks = ("蝴蝶影视 | %s %s" % (vod_year, st_text)).strip()
        elif vod_year:
            vod_remarks = "蝴蝶影视 | %s" % vod_year

        actor_list = re.findall(r'<a[^>]+href=["\']/q/actors/[^"\']*["\'][^>]*>([^<]+)</a>', detail_html, re.I)
        vod_actor = (", ".join(actor_list)) if actor_list else self.brandActor

        dir_list = re.findall(r'<a[^>]+href=["\']/q/director/[^"\']*["\'][^>]*>([^<]+)</a>', detail_html, re.I)
        vod_director = (", ".join(dir_list)) if dir_list else self.brandDirector

        ep_numbers = []
        raw_seq_links = re.findall(r'<a[^>]+class=["\'][^"\']*seq[^"\']*["\'][^>]+href=["\'](/%s/(\d+)(?:/(\d+))?)["\'][^>]*>([^<]+)</a>' % vid, play_html + detail_html, re.I)
        for full_h, ep_num, line_cd, text_num in raw_seq_links:
            num = int(ep_num)
            if num not in ep_numbers:
                ep_numbers.append(num)

        if not ep_numbers:
            m_total = re.search(r'"total":\s*(\d+)', play_html + detail_html)
            if m_total:
                total_cnt = int(m_total.group(1))
                ep_numbers = list(range(1, total_cnt + 1))
            else:
                ep_numbers = [1]
        else:
            ep_numbers.sort()

        lines = []
        tab_list_match = re.search(r'<ul[^>]+class=["\'][^"\']*nav-tabs[^"\']*["\'][^>]*>([\s\S]*?)</ul>', play_html, re.I)
        if tab_list_match:
            raw_tab_links = re.findall(r'<a[^>]+href=["\'](/%s/\d+/(\d+))["\'][^>]*>([\s\S]*?)</a>' % vid, tab_list_match.group(1), re.I)
            for href, line_code, tab_name_raw in raw_tab_links:
                line_name = re.sub(r'<[^>]+>', '', tab_name_raw).strip()
                if line_name and not any(bad in line_name for bad in ("排序", "选集", "快捷键")):
                    lines.append({"name": line_name, "code": line_code})

        if not lines:
            line_pattern = re.findall(r'href=["\']/%s/1/(\d+)["\'][^>]*>([^<]+)</a>' % vid, play_html, re.I)
            for l_code, l_name in line_pattern:
                clean_n = l_name.strip()
                if clean_n:
                    lines.append({"name": clean_n, "code": l_code})

        rec_part = ""
        m_block = re.search(r'(?:热门推荐|猜你喜欢|同分类热门推荐|相关推荐)[\s\S]*?(<div[^>]+id=["\']videos["\'][\s\S]*)', play_html, re.I)
        if m_block:
            rec_part = m_block.group(1)
        elif 'id="videos"' in play_html:
            m_v = re.search(r'(<div[^>]+id=["\']videos["\'][\s\S]*)', play_html, re.I)
            if m_v:
                rec_part = m_v.group(1)

        rec_episodes = []
        if rec_part:
            m_foot = re.search(r'<(?:footer|div[^>]+class=["\'][^"\']*footer)', rec_part, re.I)
            if m_foot:
                rec_part = rec_part[:m_foot.start()]

            rec_cards = self._parse_card_list(rec_part)
            if rec_cards:
                for c in rec_cards[:24]:
                    c_title = re.sub(r'[\$#]', '', c["vod_name"]).strip()
                    c_vid = c["vod_id"].strip("/")
                    if c_vid == str(vid):
                        continue
                    rec_label = "%02d·%s" % (len(rec_episodes) + 1, c_title[:16])
                    rec_payload = "REC@@@%s@@@%s" % (c_vid, urllib.parse.quote(c_title))
                    rec_episodes.append("%s$%s" % (rec_label, rec_payload))

        play_from_items = []
        play_url_items = []

        is_single_ep = (len(ep_numbers) <= 1)

        if lines:
            for line_obj in lines:
                l_name = line_obj["name"]
                l_code = line_obj["code"]
                ep_list = []
                for ep in ep_numbers:
                    ep_url = "/%s/%d/%s" % (vid, ep, l_code)
                    ep_title = "正片" if is_single_ep else ("第%d集" % ep)
                    ep_list.append("%s$%s" % (ep_title, ep_url))
                
                if is_single_ep and rec_episodes:
                    ep_list.extend(rec_episodes)
                
                play_from_items.append("🦋 %s" % l_name)
                play_url_items.append("#".join(ep_list))
        else:
            ep_list = []
            for ep in ep_numbers:
                ep_url = "/%s/%d" % (vid, ep)
                ep_title = "正片" if is_single_ep else ("第%d集" % ep)
                ep_list.append("%s$%s" % (ep_title, ep_url))
            
            if is_single_ep and rec_episodes:
                ep_list.extend(rec_episodes)
                
            play_from_items.append("🦋 蝴蝶专线")
            play_url_items.append("#".join(ep_list))

        if (not is_single_ep) and rec_episodes:
            play_from_items.append("🦋 猜你喜欢")
            play_url_items.append("#".join(rec_episodes))

        active_domain = urllib.parse.urlparse(self.siteUrl).netloc or self.siteUrl
        content_desc = "🦋 蝴蝶影视专线直连 | 当前采用域名: %s | 官方交流群: @tvshare23" % active_domain

        return {
            "list": [{
                "vod_id": raw_id,
                "vod_name": vod_name,
                "vod_pic": vod_pic,
                "vod_bg": vod_pic,
                "vod_background": vod_pic,
                "vod_banner": vod_pic,
                "vod_actor": vod_actor,
                "vod_director": vod_director,
                "vod_remarks": vod_remarks,
                "vod_content": content_desc,
                "vod_play_from": "$$$".join(play_from_items),
                "vod_play_url": "$$$".join(play_url_items)
            }]
        }

    def playerContent(self, flag, id, vipFlags):
        raw_play_path = str(id).strip()
        target_m3u8 = ""
        desc_title = ""

        if raw_play_path.startswith("REC@@@"):
            parts = raw_play_path.split("@@@")
            rec_vid = parts[1]
            if len(parts) > 2:
                desc_title = urllib.parse.unquote(parts[2])
            fetch_url = "/%s" % rec_vid
        else:
            fetch_url = raw_play_path

        if fetch_url.startswith("http") and ".m3u8" in fetch_url:
            target_m3u8 = fetch_url
        else:
            res = self._fetch(fetch_url)
            html_text = res.get("text", "")

            m_src = re.search(r'<source[^>]+src=["\']([^"\']+\.m3u8[^"\']*)["\']', html_text, re.I)
            if m_src:
                target_m3u8 = m_src.group(1).strip()

            if not target_m3u8:
                m_content_url = re.search(r'"contentUrl":\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html_text, re.I)
                if m_content_url:
                    target_m3u8 = m_content_url.group(1).replace("\\/", "/")

            if not target_m3u8:
                m_direct = re.search(r'https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*', html_text)
                if m_direct:
                    target_m3u8 = m_direct.group(0).replace("\\/", "/")

            if not target_m3u8:
                m_iframe = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html_text, re.I)
                if m_iframe:
                    sub_url = m_iframe.group(1).strip()
                    if sub_url.startswith("//"):
                        sub_url = "https:" + sub_url
                    elif sub_url.startswith("/"):
                        sub_url = self.siteUrl + sub_url
                    res_ifr = self._fetch(sub_url, referer=self.siteUrl + fetch_url)
                    ifr_text = res_ifr.get("text", "")
                    m_ifr_m3u8 = re.search(r'https?://[^"\'\s<>]+\.m3u8[^"\'\s<>]*', ifr_text)
                    if m_ifr_m3u8:
                        target_m3u8 = m_ifr_m3u8.group(0).replace("\\/", "/")

        final_play_url = target_m3u8 if target_m3u8 else fetch_url

        if ".m3u8" in final_play_url.lower():
            if not final_play_url.lower().endswith(".m3u8"):
                sep = "&" if "?" in final_play_url else "?"
                final_play_url = final_play_url + sep + "format=.m3u8"

        result = {
            "parse": 0,
            "jx": 0,
            "url": final_play_url,
            "header": {
                "User-Agent": self._ua,
                "Referer": self.siteUrl + "/"
            },
            "contentType": "application/vnd.apple.mpegurl" if ".m3u8" in final_play_url.lower() else "video/mp4",
            "format": "hls" if ".m3u8" in final_play_url.lower() else "mp4"
        }
        if desc_title:
            result["desc"] = desc_title

        return result

    def searchContent(self, key, quick, pg="1"):
        search_kw = str(key).strip()
        page_val = int(pg) if str(pg).isdigit() else 1

        encoded_kw = urllib.parse.quote(search_kw)
        search_path = "/search/%s" % encoded_kw
        if page_val > 1:
            search_path = "%s?page=%d" % (search_path, page_val)

        res = self._fetch(search_path)
        cards = self._parse_card_list(res.get("text", ""))

        return {
            "page": page_val,
            "pagecount": 99,
            "limit": len(cards),
            "total": 9999,
            "list": cards
        }

    def localProxy(self, params):
        return [404, "text/plain", "Direct playback only"]

    def action(self, action): return {"msg": "ok"}
    def liveContent(self): return ""
    def destroy(self): pass
# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249684570&sig=a0488f323abdc74a
