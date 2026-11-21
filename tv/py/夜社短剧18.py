# -*- coding: utf-8 -*-
# 夜社短剧 蜘蛛（源自 Hamo 插件 com.butterfly.yeshe 的页面逻辑移植）
import base64
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://yeshe.tv"
    SHORT_URL = "https://ysurl.win/755WwN"
    PROBE_PATH = "/type/13.html"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    CLASSES = [
        ("2", "视频"), ("13", "AI短剧"), ("36", "擦边短剧"), ("11", "国产视频"), ("12", "日本AV"),
        ("14", "欧美无码"), ("35", "韩国BJ"), ("1", "动漫"), ("7", "同人作品"), ("8", "动画卡通"),
        ("10", "3D动漫"), ("9", "中文动漫"), ("32", "里番"), ("33", "泡面番"), ("3", "有声"),
        ("15", "有声小说"), ("16", "淫词艳曲"), ("17", "激情骚麦"), ("5", "写真"), ("20", "秀人系列"),
        ("22", "网红COS"), ("21", "机构套图"), ("23", "内购私拍"), ("34", "AI绘图"), ("24", "各国套图"),
    ]
    CARD_RE = re.compile(r'<a\s+href="/play/(\d+)/\d+/\d+\.html"\s*title="([^"]*)"[^>]*>([\s\S]*?)</a>')
    PIC_RE1 = re.compile(r'src="(https:\\?/\\?/[^"]*\.(?:webp|avif|png|jpg|jpeg))"')
    PIC_RE2 = re.compile(r'src="(https:[^"]*\.(?:webp|avif|png|jpe?g))"')
    TIME_RE = re.compile(r'<div class="time">([^<]+)</div>')
    B64_RE = re.compile(r'var\s+a\s*=\s*"([A-Za-z0-9+/=]+)"')

    def getName(self):
        return "夜社短剧"

    def init(self, extend=""):
        self.custom_host = ""
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.custom_host = extend.strip().rstrip("/")
        self.host = None

    def _raw_get(self, url, referer=""):
        headers = {
            "User-Agent": self.UA,
            "Referer": referer,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    status = resp.status
                    final_url = resp.geturl()
                    raw = resp.read()
                return status, (raw.decode("utf-8", "replace") if raw else ""), final_url
            except urllib.error.HTTPError as e:
                try:
                    raw = e.read()
                    text = raw.decode("utf-8", "replace") if raw else ""
                except Exception:
                    text = ""
                return e.code, text, url
            except Exception:
                pass
            time.sleep(0.5)
        return 0, "", url

    def _origin_of(self, u):
        m = re.match(r"^(https?://[^/]+)", str(u or ""), re.I)
        return m.group(1) if m else ""

    def _decode_page(self, text):
        m = self.B64_RE.search(text or "")
        if m:
            try:
                dec = base64.b64decode(m.group(1)).decode("utf-8", "replace")
                if dec and len(dec) > len(text or "") * 0.3:
                    return dec
            except Exception:
                pass
        return text or ""

    def _ensure_host(self):
        if self.host:
            return self.host
        if self.custom_host:
            self.host = self.custom_host
            return self.host
        host = self.DEFAULT_HOST
        try:
            status, text, final_url = self._raw_get(self.SHORT_URL)
            origin = self._origin_of(final_url)
            if origin and origin != self._origin_of(self.SHORT_URL):
                pstatus, ptext, _ = self._raw_get(origin + self.PROBE_PATH, origin + "/")
                if 200 <= pstatus < 400 and len(ptext or "") > 100 and "/play/" in self._decode_page(ptext):
                    host = origin
        except Exception:
            pass
        self.host = host
        return host

    def _fetch_decoded(self, path):
        host = self._ensure_host()
        url = path
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = host + url
        status, text, final_url = self._raw_get(url, host + "/")
        return self._decode_page(text), host

    def _parse_cards(self, html):
        items = []
        seen = set()
        for m in self.CARD_RE.finditer(html or ""):
            vid = m.group(1)
            if vid in seen:
                continue
            seen.add(vid)
            block = m.group(3)
            cm = self.PIC_RE1.search(block) or self.PIC_RE2.search(block)
            pic = cm.group(1).replace("\\/", "/") if cm else ""
            tm = self.TIME_RE.search(block)
            meta = tm.group(1).strip() if tm else "高清"
            items.append({
                "vod_id": vid,
                "vod_name": m.group(2).strip(),
                "vod_pic": pic,
                "vod_remarks": "蝴蝶影视 | " + meta,
                "style": {"type": "rect", "ratio": 0.75},
            })
        return items

    def homeContent(self, filter=False):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]}

    def homeVideoContent(self):
        text, host = self._fetch_decoded("/type/13.html")
        return {"list": self._parse_cards(text)[:30]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        text, host = self._fetch_decoded("/filter/" + str(tid) + "/page/" + str(page) + ".html")
        items = self._parse_cards(text)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        kw = urllib.parse.quote(str(key), safe="")
        if page > 1:
            path = "/vod/search/wd/" + kw + "/page/" + str(page) + ".html"
        else:
            path = "/vod/search/wd/" + kw + ".html"
        text, host = self._fetch_decoded(path)
        items = self._parse_cards(text)[:30]
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def _extract_json(self, text, key):
        idx = (text or "").find(key)
        if idx < 0:
            return None
        start = text.find("{", idx)
        if start < 0:
            return None
        depth = 0
        for i in range(start, len(text)):
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        return None
        return None

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = re.sub(r"\D", "", str(ids[0] or ""))
        if not vid:
            return {"list": []}
        detail_path = "/play/" + vid + "/1/1.html"
        html, host = self._fetch_decoded(detail_path)
        if not html:
            return {"list": []}
        config = self._extract_json(html, "player_aaaa")
        if not isinstance(config, dict):
            return {"list": []}
        vd = config.get("vod_data") if isinstance(config.get("vod_data"), dict) else {}
        ep_count = 1
        em = re.search(r"vod_play_all\s*=\s*(\d+)", html)
        if em:
            ep_count = int(em.group(1))
        else:
            found = set(re.findall(r"/play/" + vid + r"/1/(\d+)\.html", html))
            ep_count = len(found) or 1
        cfg_url = str(config.get("url") or "").replace("\\/", "/")
        tpl = re.match(r"^(.*\/)\d+\/(play\.m3u8.*)$", cfg_url)
        episodes = []
        for i in range(1, ep_count + 1):
            if tpl:
                val = json.dumps({"directUrl": tpl.group(1) + str(i) + "/" + tpl.group(2)}, ensure_ascii=False)
            elif i == 1 and cfg_url:
                val = json.dumps({"directUrl": cfg_url}, ensure_ascii=False)
            else:
                val = json.dumps({"pagePath": "/play/" + vid + "/1/" + str(i) + ".html"}, ensure_ascii=False)
            episodes.append("第" + str(i) + "集$" + val)
        pic = str(vd.get("vod_pic") or "")
        if pic.startswith("//"):
            pic = "https:" + pic
        elif pic and not pic.startswith("http"):
            pic = host + (pic if pic.startswith("/") else "/" + pic)
        title = str(vd.get("vod_name") or vid)
        lines = [
            "🦋 夜社短剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
            "标题：" + title,
        ]
        if vd.get("vod_class"):
            lines.append("分类：" + str(vd.get("vod_class")))
        lines.append("片源：🦋 蝴蝶夜社专线")
        lines.append("编号：" + vid)
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": "蝴蝶影视 | 共" + str(ep_count) + "集",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶夜社专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.75},
        }
        if vd.get("vod_class"):
            vod["vod_class"] = str(vd.get("vod_class"))
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        host = self._ensure_host()
        headers = {"User-Agent": self.UA, "Referer": host + "/"}
        direct = ""
        page_path = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                direct = str(data.get("directUrl") or "")
                page_path = str(data.get("pagePath") or "")
        except Exception:
            pass
        if direct:
            return {"parse": 0, "playUrl": "", "url": direct, "header": headers}
        if page_path:
            text, host2 = self._fetch_decoded(page_path)
            config = self._extract_json(text, "player_aaaa")
            if isinstance(config, dict) and config.get("url"):
                return {"parse": 0, "playUrl": "", "url": str(config["url"]), "header": headers}
            return {"parse": 1, "playUrl": "", "url": host + page_path, "header": headers}
        return {"parse": 1, "playUrl": "", "url": "", "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249897517&sig=094174bfa05bb63b
