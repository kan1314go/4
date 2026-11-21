# -*- coding: utf-8 -*-
# 肉视频 蜘蛛（源自 Hamo 插件 com.butterfly.rouvideo 的逻辑移植）
import base64
import html as html_lib
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://rou66.net"
    NAV_URLS = ["https://x99dh.net", "https://x99dh.lat"]
    TARGET_NAME = "肉视频"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    CATEGORIES = [
        ("/v?order=createdAt", "🔥 最新发布"), ("/v?order=viewCount", "👑 最多播放"), ("/v?order=likeCount", "❤️ 最受喜爱"),
        ("/t/AI短劇", "🤖 AI成人短剧"), ("/t/自拍流出", "📱 自拍流出"), ("/t/探花", "🕵️ 探花精选"),
        ("/t/國產AV", "🇨🇳 国产AV"), ("/t/日本", "🇯🇵 日本精选"), ("/t/中文字幕", "🀄 中文字幕"),
        ("/t/麻豆傳媒", "麻豆传媒"), ("/t/糖心Vlog", "糖心Vlog"), ("/t/蜜桃影像傳媒", "蜜桃传媒"),
        ("/t/香蕉視頻傳媒", "香蕉视频"), ("/t/星空無限傳媒", "星空无限"), ("/t/天美傳媒", "天美传媒"),
        ("/t/OnlyFans", "OnlyFans"), ("/t/巨乳", "巨乳"), ("/t/人妻", "人妻"), ("/t/絲襪", "丝袜"),
        ("/t/熟女", "熟女"), ("/t/美少女", "美少女"), ("/t/中出", "中出"), ("/t/口交", "口交"),
        ("/t/痴女", "痴女"), ("/t/多人運動", "多人运动"), ("/t/NTR", "NTR"),
    ]
    NEXT_RE = re.compile(r'<script\s+id=["\']__NEXT_DATA__["\'][^>]*>([\s\S]*?)</script>', re.I)
    CARD_RE = re.compile(r'<a[^>]+href=["\'](/v/[a-zA-Z0-9_\-]+)["\'][^>]*>([\s\S]*?)</a>', re.I)
    B64_RE = re.compile(r"""["']([A-Za-z0-9+/=]{100,})["']""")

    def getName(self):
        return "肉视频"

    def init(self, extend=""):
        self.custom_host = ""
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.custom_host = extend.strip().rstrip("/")
        self.host = None
        self.meta = {}

    # ---------- transport ----------
    def _unwrap(self, raw):
        t = (raw or "").strip()
        if t.startswith('"') and t.endswith('"') and len(t) >= 2:
            try:
                dec = json.loads(t)
                if isinstance(dec, str) and dec:
                    return dec
            except Exception:
                t = t[1:-1]
        return (t.replace('\\"', '"').replace("\\/", "/")
                 .replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", " "))

    def _fetch(self, url, referer=""):
        headers = {
            "User-Agent": self.UA,
            "Referer": referer or url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        status, text, final = 0, "", url
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as resp:
                status = resp.status
                final = resp.geturl()
                raw = resp.read()
            text = self._unwrap(raw.decode("utf-8", "replace") if raw else "")
            return status, text, final
        except urllib.error.HTTPError as e:
            try:
                raw = e.read()
                text = self._unwrap(raw.decode("utf-8", "replace") if raw else "")
            except Exception:
                text = ""
            return e.code, text, url
        except Exception:
            pass
        if url.startswith("https://"):
            http_url = "http://" + url[8:]
            try:
                req = urllib.request.Request(http_url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    status = resp.status
                    final = resp.geturl()
                    raw = resp.read()
                text = self._unwrap(raw.decode("utf-8", "replace") if raw else "")
                return status, text, final
            except Exception:
                pass
        return 0, "", url

    # ---------- host discovery ----------
    def _discover_host(self):
        for nav in self.NAV_URLS:
            status, text, final = self._fetch(nav, nav + "/")
            if not text:
                continue
            for m in self.B64_RE.finditer(text):
                try:
                    decoded = base64.b64decode(m.group(1)).decode("utf-8", "replace")
                    unq = urllib.parse.unquote(decoded)
                    if "[" not in unq or "{" not in unq or self.TARGET_NAME not in unq:
                        continue
                    sites = json.loads(unq)
                    if not isinstance(sites, list):
                        continue
                    for item in sites:
                        if isinstance(item, dict) and str(item.get("name") or "").strip() == self.TARGET_NAME and item.get("url"):
                            om = re.match(r"^(https?://[^/]+)", str(item["url"]).strip(), re.I)
                            if om:
                                return om.group(1)
                except Exception:
                    continue
        return self.DEFAULT_HOST

    def _ensure_host(self, force=False):
        if self.custom_host:
            self.host = self.custom_host
            return self.host
        if self.host and not force:
            return self.host
        self.host = self._discover_host().rstrip("/")
        return self.host

    def _fetch_page(self, path_or_url, referer=""):
        host = self._ensure_host()
        url = self._resolve_url(path_or_url, host)
        ref = referer or (host + "/v")
        status, text, final = self._fetch(url, ref)
        if (status in (0, 404, 451, 502, 503) or not text) and not self.custom_host:
            new_host = self._ensure_host(force=True)
            if new_host and new_host != host:
                retry_url = re.sub(r"^https?://[^/]+", new_host, url, flags=re.I)
                status, text, final = self._fetch(retry_url, new_host + "/v")
                return text, new_host
        return text, host

    # ---------- helpers ----------
    def _resolve_url(self, raw, host):
        if not raw:
            return ""
        u = str(raw).strip().replace("&amp;", "&")
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return host + u
        if not u.startswith("http"):
            return host + "/" + u
        return u

    def _poster(self, raw_pic, host):
        if not raw_pic:
            return ""
        full = self._resolve_url(raw_pic, host)
        if full.startswith("data:image"):
            return ""
        return full

    def _format_duration(self, sec_val):
        try:
            total = int(float(sec_val))
        except Exception:
            return "HD"
        if total <= 0:
            return "HD"
        m_total, s = divmod(total, 60)
        h, m = divmod(m_total, 60)
        if h > 0:
            return str(h) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)
        return str(m).zfill(2) + ":" + str(s).zfill(2)

    def _status(self, meta):
        clean = re.sub(r"[\r\n\t]+", " ", str(meta or "")).strip()
        return "蝴蝶影视 | " + clean if clean else "蝴蝶影视"

    def _encode_category_path(self, raw_path):
        p = str(raw_path or "").strip()
        q_idx = p.find("?")
        path_part = p[:q_idx] if q_idx >= 0 else p
        query_part = p[q_idx:] if q_idx >= 0 else ""
        segs = []
        for seg in path_part.split("/"):
            if seg:
                try:
                    seg = urllib.parse.quote(urllib.parse.unquote(seg), safe="")
                except Exception:
                    seg = urllib.parse.quote(seg, safe="")
            segs.append(seg)
        return "/".join(segs) + query_part

    # ---------- list parsing ----------
    def _parse_list(self, html_text, host):
        items = []
        if not html_text:
            return items
        nm = self.NEXT_RE.search(html_text)
        if nm:
            try:
                data = json.loads(nm.group(1).strip())
                videos = data.get("props", {}).get("pageProps", {}).get("videos")
                if isinstance(videos, list) and videos:
                    seen = set()
                    for v in videos:
                        if not isinstance(v, dict):
                            continue
                        vid = str(v.get("id") or "").strip()
                        if not vid or vid in seen:
                            continue
                        seen.add(vid)
                        title = html_lib.unescape(str(v.get("nameZh") or v.get("name") or self.TARGET_NAME)).strip()
                        raw_pic = v.get("coverImageUrl") or ""
                        self.meta[vid] = {"title": title, "pic": raw_pic}
                        items.append({
                            "vod_id": vid,
                            "vod_name": title,
                            "vod_pic": self._poster(raw_pic, host),
                            "vod_remarks": self._status(self._format_duration(v.get("duration"))),
                            "style": {"type": "rect", "ratio": 1.49},
                        })
                    if items:
                        return items
            except Exception:
                pass
        seen = set()
        for m in self.CARD_RE.finditer(html_text):
            href, block = m.group(1), m.group(2) or ""
            slug = href.replace("/v/", "").rstrip("/")
            if not slug or slug in seen:
                continue
            seen.add(slug)
            pic = ""
            pm = (re.search(r'data-src=["\']([^"\']+)["\']', block, re.I) or
                  re.search(r'data-original=["\']([^"\']+)["\']', block, re.I) or
                  re.search(r'src=["\']([^"\']+)["\']', block, re.I))
            if pm and ".svg" not in pm.group(1) and "data:image" not in pm.group(1):
                pic = pm.group(1).strip()
            tm = re.search(r'(?:title|alt)=["\']([^"\']+)["\']', block, re.I)
            title = html_lib.unescape(tm.group(1)).strip() if tm else ""
            if not title:
                stripped = re.sub(r"<[^>]+>", " ", block)
                title = re.sub(r"\s+", " ", html_lib.unescape(stripped)).strip() or self.TARGET_NAME
            dm = re.search(r'(\d{1,2}:\d{2}(?::\d{2})?)', block)
            dur = dm.group(1) if dm else "HD"
            self.meta[slug] = {"title": title, "pic": pic}
            items.append({
                "vod_id": slug,
                "vod_name": title,
                "vod_pic": self._poster(pic, host),
                "vod_remarks": self._status(dur),
                "style": {"type": "rect", "ratio": 1.49},
            })
        return items

    # ---------- entries ----------
    def homeContent(self, filter=False):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in self.CATEGORIES]}

    def homeVideoContent(self):
        text, host = self._fetch_page("/v?order=createdAt&page=1")
        return {"list": self._parse_list(text, host)}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        encoded = self._encode_category_path(str(tid or "/v?order=createdAt"))
        sep = "&" if "?" in encoded else "?"
        text, host = self._fetch_page(encoded + sep + "page=" + str(page))
        items = self._parse_list(text, host)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        path = "/search?q=" + urllib.parse.quote(str(key), safe="") + "&page=" + str(page)
        text, host = self._fetch_page(path)
        items = self._parse_list(text, host)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0] or "").strip().replace("/v/", "").rstrip("/")
        if not vid:
            return {"list": []}
        cached = self.meta.get(vid) or {}
        vod_name = cached.get("title") or ""
        raw_pic = cached.get("pic") or ""
        genres = []
        desc = ""
        text, host = self._fetch_page("/v/" + vid)
        if text:
            nm = self.NEXT_RE.search(text)
            if nm:
                try:
                    data = json.loads(nm.group(1).strip())
                    vo = data.get("props", {}).get("pageProps", {}).get("video")
                    if isinstance(vo, dict):
                        if not vod_name:
                            vod_name = str(vo.get("nameZh") or vo.get("name") or self.TARGET_NAME)
                        if vo.get("coverImageUrl"):
                            raw_pic = vo.get("coverImageUrl")
                        tags = vo.get("tagsZh") or vo.get("tags") or []
                        if isinstance(tags, list):
                            for t in tags:
                                t = str(t or "").strip()
                                if t and t not in genres:
                                    genres.append(t)
                        if vo.get("description"):
                            desc = str(vo.get("description")).strip()
                except Exception:
                    pass
            if not raw_pic:
                og = re.search(r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', text, re.I)
                if og:
                    raw_pic = og.group(1).strip()
        if not vod_name:
            vod_name = self.TARGET_NAME
        vod_name = html_lib.unescape(vod_name)
        poster = self._poster(raw_pic, host)
        lines = [
            "🦋 肉视频官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        else:
            lines.append("标题：" + vod_name)
            if genres:
                lines.append("分类：" + " · ".join(genres))
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + vid)
        val = json.dumps({"vid": vid}, ensure_ascii=False)
        vod = {
            "vod_id": vid,
            "vod_name": vod_name,
            "vod_pic": poster,
            "vod_remarks": self._status("正片"),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "正片完整版$" + val,
            "style": {"type": "rect", "ratio": 1.49},
        }
        if genres:
            vod["vod_class"] = ",".join(genres)
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        host = self._ensure_host()
        headers = {"User-Agent": self.UA, "Referer": host + "/"}
        vid = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                vid = str(data.get("vid") or "").strip()
        except Exception:
            pass
        if not vid:
            vid = str(id or "").replace("/v/", "").rstrip("/")
        if not vid:
            return {"parse": 1, "playUrl": "", "url": "", "header": headers}
        play_api = host + "/api/hls/" + vid
        detail_url = host + "/v/" + vid
        status, text, final = self._fetch(play_api, detail_url)
        url = final if final and final != play_api else play_api
        return {"parse": 0, "playUrl": "", "url": url, "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249851602&sig=474b93c58941cf0e
