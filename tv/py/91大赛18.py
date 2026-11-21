# -*- coding: utf-8 -*-
# 91大赛

import re
import json
import requests
from urllib.parse import quote, unquote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://alone.emmkaawz.cc"
    IMG_WORKER = "https://dasai-img-proxy.yishengheqiu7679.workers.dev"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    BRAND = "蝴蝶影视"
    LINE_NAME = "🦋 蝴蝶专线"
    PAGE_SIZE = 20
    TIMEOUT = 8

    CLASSES = [
        ("jrds", "今日大赛"),
        ("rsds", "热搜大赛"),
        ("mrds", "每日大赛"),
        ("aidj", "AI短剧"),
        ("nsds", "女神大赛"),
        ("llds", "乱伦大赛"),
        ("xyds", "学院大赛"),
        ("whds", "网红大赛"),
        ("lyds", "撸友看片"),
        ("sjbzq", "优选投放区"),
        ("qwds", "奇闻大赛"),
        ("mxds", "明星吃瓜"),
        ("ntds", "女同大赛"),
        ("wmds", "污漫大赛"),
    ]

    TAGS = [
        ("tag/91大赛", "🔥 91大赛"),
        ("tag/吃瓜", "🍉 吃瓜"),
        ("tag/反差", "😈 反差"),
        ("tag/自慰", "💧 自慰"),
        ("tag/口交", "👄 口交"),
        ("tag/巨乳", "🍈 巨乳"),
        ("tag/后入", "🐕 后入"),
        ("tag/母狗", "🐶 母狗"),
        ("tag/反差婊", "💋 反差婊"),
        ("tag/高颜值", "✨ 高颜值"),
        ("tag/美乳", "🍒 美乳"),
        ("tag/黑丝", "🖤 黑丝"),
    ]

    def __init__(self):
        self.host = self.DEFAULT_HOST

    def init(self, extend=""):
        cfg = {}
        if isinstance(extend, dict):
            cfg = extend
        elif isinstance(extend, str) and extend:
            try:
                cfg = json.loads(extend)
            except Exception:
                cfg = {}
        custom = ""
        if isinstance(cfg, dict):
            custom = str(cfg.get("host", "") or "").strip()
        if custom and custom.startswith("http"):
            self.host = custom.rstrip("/")
        else:
            self.host = self.DEFAULT_HOST
        return True

    def getName(self):
        return "91大赛"

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        return (".m3u8" in low) or (".mp4" in low) or (".flv" in low) or (".mpd" in low)

    def manualVideoCheck(self):
        return False

    def _fetch(self, url):
        headers = {
            "User-Agent": self.DEFAULT_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": self.host + "/",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            if resp.status_code >= 400 or not resp.text:
                return ""
            return resp.text
        except Exception:
            return ""

    def _strip(self, s):
        return re.sub(r"<[^>]+>", "", str(s or "")).strip()

    def _fix_img(self, u):
        if not u:
            return ""
        u = str(u)
        if u.startswith("data:"):
            return u
        if u.startswith("//"):
            out = "https:" + u
        elif u.startswith("http"):
            out = u
        elif u.startswith("/"):
            out = self.host + u
        else:
            out = self.host + "/" + u
        if re.match(r"https?://", out, re.I) and self.IMG_WORKER not in out:
            return self.IMG_WORKER + "/?url=" + quote(out, safe="")
        return out

    def _extract_list_image(self, block):
        m = re.search(r'data-xkrkllgl=["\']([^"\']+)["\']', block, re.I)
        if m:
            return self._fix_img(m.group(1))
        m = re.search(r'data-src=["\']([^"\']+)["\']', block, re.I)
        if m:
            return self._fix_img(m.group(1))
        m = re.search(r'<img[^>]*src=["\']([^"\']+)["\']', block, re.I)
        if m and "zw.png" not in m.group(1) and "lazyload" not in m.group(1):
            return self._fix_img(m.group(1))
        return ""

    def _parse_list(self, html):
        videos = []
        seen = set()
        blocks = re.findall(
            r'<li\s+class=["\'](?:Xc_home_article-si|Xc_archive-si)[^"\']*["\'][^>]*>([\s\S]*?)</li>',
            html or "", re.I)
        if not blocks:
            blocks = re.findall(
                r'<(?:article|div)\s[^>]*class=["\'][^"\']*(?:post|article|card)[^"\']*["\'][^>]*>([\s\S]*?)</(?:article|div)>',
                html or "", re.I)
        if not blocks:
            for m in re.finditer(r'<a\s[^>]*href=["\']([^"\']*)["\'][^>]*>([\s\S]*?)</a>', html or "", re.I):
                href = m.group(1)
                block = m.group(0)
                tm = re.search(r'title=["\']([^"\']*)["\']', block, re.I) or re.search(r'alt=["\']([^"\']*)["\']', block, re.I)
                title = tm.group(1).strip() if tm else ""
                if not title:
                    continue
                vm = re.search(r'/archives/(\d+)/', href)
                vid = vm.group(1) if vm else href
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                rm = re.search(r'<time[^>]*>([\s\S]*?)</time>', block, re.I)
                remark = self._strip(rm.group(1)) if rm else ""
                videos.append({
                    "vod_id": vid,
                    "vod_name": title,
                    "vod_pic": self._extract_list_image(block),
                    "vod_remarks": (self.BRAND + " | " + remark) if remark else self.BRAND,
                })
            return videos
        for item in blocks:
            aM = re.search(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*title=["\']([^"\']*)["\']', item, re.I)
            if aM:
                href, title = aM.group(1), aM.group(2).strip()
            else:
                a2 = re.search(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>[\s\S]*?<img[^>]*alt=["\']([^"\']*)["\']', item, re.I)
                if a2:
                    href, title = a2.group(1), a2.group(2).strip()
                else:
                    a3 = re.search(r'<a\s[^>]*href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', item, re.I)
                    if not a3:
                        continue
                    href, title = a3.group(1), self._strip(a3.group(2))
                    if not title:
                        continue
            if not title:
                im = re.search(r'<img[^>]*alt=["\']([^"\']*)["\']', item, re.I)
                title = im.group(1).strip() if im else ""
            vm = re.search(r'/archives/(\d+)/', href)
            vid = vm.group(1) if vm else href
            if not vid or vid in seen:
                continue
            seen.add(vid)
            rM = re.search(r'<div class=["\']last["\']>([\s\S]*?)</div>', item, re.I) or re.search(r'<time[^>]*>([\s\S]*?)</time>', item, re.I)
            remark = self._strip(rM.group(1)) if rM else ""
            videos.append({
                "vod_id": vid,
                "vod_name": title if title else vid,
                "vod_pic": self._extract_list_image(item),
                "vod_remarks": (self.BRAND + " | " + remark) if remark else self.BRAND,
            })
        return videos

    def _extract_from_config(self, html):
        purl, pic = "", ""
        for pat in (r'data-config=["\']([^"\']*)["\']', r'data-config=\s*["\']([^"\']*?)["\']'):
            m = re.search(pat, html or "", re.I)
            if m:
                try:
                    clean = m.group(1).replace("&quot;", '"').replace("\\/", "/")
                    cfg = json.loads(clean)
                    v = cfg.get("video", {}) if isinstance(cfg, dict) else {}
                    purl = v.get("url", "") or ""
                    pic = v.get("pic", "") or ""
                    if purl:
                        break
                except Exception:
                    pass
        return purl, pic

    def _extract_video(self, html):
        html = html or ""
        purl, _pic = self._extract_from_config(html)
        if purl:
            return purl
        m = re.search(r'new\s+DPlayer\s*\(\s*\{[^}]*url\s*:\s*["\']([^"\']+)', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'var player_[^=]+=\s*(\{[\s\S]*?\})', html, re.I)
        if m:
            try:
                d = json.loads(m.group(1))
                if d.get("url"):
                    return d["url"]
            except Exception:
                pass
        m = re.search(r'["\'],\s*["\']url["\']\s*:\s*["\']([^"\']+)["\']', html, re.I) or re.search(r'"","url":"(.*?)"', html)
        if m:
            return m.group(1).replace("\\", "")
        m = re.search(r'<video[^>]+src=["\']([^"\']+)["\']', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'<source[^>]+src=["\']([^"\']+)["\']', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'(https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*)', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'(https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*)', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html, re.I)
        if m:
            return m.group(1)
        m = re.search(r'data-url=["\']([^"\']+)["\']', html, re.I)
        if m:
            return m.group(1)
        allm = re.findall(r'https?://[^\s"\'<>]+\.(?:m3u8|mp4)[^\s"\'<>]*', html, re.I)
        return allm[0] if allm else ""

    def homeContent(self, filter):
        classes = []
        filters = {}
        tag_value = [{"n": "本分类", "v": ""}]
        for tv, tn in self.TAGS:
            tag_value.append({"n": tn, "v": tv})
        for tid, name in self.CLASSES:
            classes.append({"type_id": tid, "type_name": name})
            filters[tid] = [{"key": "sub", "name": "热门标签", "init": "", "value": tag_value}]
        return {"class": classes, "filters": filters}

    def homeVideoContent(self):
        html = self._fetch(self.host + "/")
        items = self._parse_list(html) if html else []
        return {"list": items[:30]}

    def categoryContent(self, tid, pg, filter, extend):
        pg = int(pg) if str(pg).isdigit() else 1
        sub = ""
        if filter and isinstance(extend, dict):
            sub = str(extend.get("sub", "") or "")
        cid = sub if sub else str(tid)
        for _ in range(2):
            d = unquote(cid)
            if d == cid:
                break
            cid = d
        if cid.startswith("tag/"):
            path = "/tag/" + cid[4:].strip("/") + "/"
        elif cid.startswith("/category/"):
            path = cid if cid.endswith("/") else cid + "/"
        else:
            path = "/category/" + cid.strip("/") + "/"
        base = self.host + path
        if pg == 1:
            urls = [base]
        else:
            urls = [
                base.rstrip("/") + "/" + str(pg) + "/",
                base.rstrip("/") + "/page/" + str(pg) + "/",
                base + ("&" if "?" in base else "?") + "page=" + str(pg),
            ]
        html = ""
        for u in urls:
            html = self._fetch(u)
            if html:
                break
        items = self._parse_list(html) if html else []
        return {"list": items, "page": pg, "pagecount": 9999, "limit": self.PAGE_SIZE, "total": 999999}

    def searchContent(self, key, quick, pg=1):
        kw = str(key or "").strip()
        pg = int(pg) if str(pg).isdigit() else 1
        if not kw:
            return {"list": [], "page": pg, "pagecount": 1, "limit": self.PAGE_SIZE, "total": 0}
        if pg == 1:
            url = self.host + "/search/" + quote(kw, safe="") + "/"
        else:
            url = self.host + "/search/" + quote(kw, safe="") + "/page/" + str(pg) + "/"
        html = self._fetch(url)
        items = self._parse_list(html) if html else []
        return {"list": items, "page": pg, "pagecount": 9999, "limit": self.PAGE_SIZE, "total": 999999}

    def detailContent(self, ids):
        raw = ""
        if isinstance(ids, (list, tuple)) and ids:
            raw = str(ids[0])
        elif ids:
            raw = str(ids)
        if not raw:
            return {"list": []}
        did = raw.strip()
        vid = did
        if re.match(r"^\d+$", did):
            detail_url = self.host + "/archives/" + did + "/"
        elif did.startswith("/archives/"):
            detail_url = self.host + did
            vm = re.search(r'/archives/(\d+)/', did)
            if vm:
                vid = vm.group(1)
        else:
            detail_url = self.host + did
        html = self._fetch(detail_url)
        if not html:
            return {"list": []}
        title = ""
        for pat in (r'<h1[^>]*class=["\'][^"\']*title[^"\']*["\'][^>]*>([\s\S]*?)</h1>',
                    r'<meta[^>]*property=["\']og:title["\'][^>]*content=["\']([^"\']*)["\']',
                    r'<title>([\s\S]*?)</title>'):
            m = re.search(pat, html, re.I)
            if m:
                title = self._strip(m.group(1))
                break
        purl, pic = self._extract_from_config(html)
        if not purl:
            purl = self._extract_video(html)
        if not pic:
            pm = re.search(r'<meta[^>]*property=["\']og:image["\'][^>]*content=["\']([^"\']*)["\']', html, re.I)
            if pm:
                pic = self._fix_img(pm.group(1))
        if not pic:
            im = re.search(r'<img[^>]*data-xkrkllgl=["\']([^"\']+)["\']', html, re.I)
            if im:
                pic = self._fix_img(im.group(1))
        else:
            pic = self._fix_img(pic)
        if purl:
            play_value = purl
        else:
            play_value = "page:" + detail_url
        content = (
            "🦋 蝴蝶影视官方交流群: @tvshare23\n"
            "导演: 🦋 蝴蝶影视\n"
            "当前主站: " + self.host + "\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "【影片名称】" + (title if title else "91大赛精品视频") + "\n"
            "【视频编号】" + vid
        )
        vod = {
            "vod_id": raw,
            "vod_name": title if title else vid,
            "vod_pic": pic,
            "vod_bg": pic,
            "vod_background": pic,
            "vod_banner": pic,
            "vod_remarks": self.BRAND + " | 正片",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_content": content,
            "vod_play_from": self.LINE_NAME,
            "vod_play_url": "正片$" + play_value,
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        headers = {
            "User-Agent": self.DEFAULT_UA,
            "Referer": self.host + "/",
            "Origin": self.host,
        }
        raw = str(id or "")
        if not raw:
            return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放引用参数 (ref)", "header": headers}
        if raw.startswith("page:"):
            html = self._fetch(raw[5:])
            extracted = self._extract_video(html) if html else ""
            if not extracted:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到有效媒体播放地址", "header": headers}
            url = extracted if extracted.startswith("http") else self.host + "/" + extracted.lstrip("/")
            return {"parse": 0, "jx": 0, "url": url, "header": headers}
        url = raw if raw.startswith("http") else self.host + "/" + raw.lstrip("/")
        return {"parse": 0, "jx": 0, "url": url, "header": headers}

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249359515&sig=c24ad87081ff3b74
