# -*- coding: utf-8 -*-
# [618视频¹⁸ 更新于:2026-11-20 20:40]
import json
import random
import re
import time
import threading
import base64
import ssl
import gzip
import zlib
import urllib.request
import urllib.error
import socket
import http.client
import http.cookiejar
from urllib.parse import quote, unquote

try:
    from base.spider import Spider as BaseSpider
except Exception:
    class BaseSpider:
        def proxy(self, params):
            return [404, "text/plain", ""]
        def localProxy(self, params):
            return [404, "text/plain", ""]

NAME = "618视频"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
PAGE_SIZE = 20
CACHE_TTL = 30
DEBUG = False
VOD_ID_PREFIX = "vod/"

ZONE_NAMES = ["一区", "二区", "三区", "四区", "五区", "六区", "七区", "八区", "九区", "漫画"]
ZONE_PATH = ["vod", "vod", "vod", "art", "vod", "vod", "art", "vod", "vod", "art"]
ZONE_TID = [13, 1, 1, 5, 2, 43, 30, 66, 35, 27]
ZONE_DOMAIN = [["https://618940.xyz", "https://618218.xyz", "https://618932.xyz", "https://618626.xyz", "https://618782.xyz"],
               ["https://618977.xyz", "https://618319.xyz", "https://618979.xyz", "https://618415.xyz", "https://618744.xyz", "https://618285.xyz"],
               ["https://6181013.xyz", "https://6181022.xyz", "https://618353.xyz", "https://618703.xyz"],
               ["https://618155.xyz", "https://618139.xyz", "https://618371.xyz"],
               ["https://618409.xyz", "https://618410.xyz", "https://618415.xyz", "https://618744.xyz"],
               ["https://618290.xyz", "https://618279.xyz", "https://618285.xyz", "https://618979.xyz"],
               ["https://618620.xyz", "https://618621.xyz", "https://618626.xyz", "https://618932.xyz", "https://618782.xyz"],
               ["https://618706.xyz", "https://618698.xyz", "https://618703.xyz", "https://618353.xyz"],
               ["https://618727.xyz", "https://618739.xyz", "https://618744.xyz", "https://618415.xyz"],
               ["https://618767.xyz", "https://618771.xyz", "https://618782.xyz"]]
BOOT_JS = "https://donk666.duokkq.com/center_upload/2026/1012/2fadb9de2065421fae88574de05b7016.js"
DISC_TTL = 6 * 3600

SPLIT_HOSTS = ["6180011", "6180012", "6180013", "6180014", "6180015", "6180016", "6180017",
               "6180018", "6180019", "6180020", "6180021", "6180022", "6180023", "6180024",
               "6180025", "6180026", "6180027", "6180028", "6180029", "6180030", "6180031",
               "6180032", "6180033", "6180034", "6180035", "6180036", "6180037", "6180038", "6180039"]
COVER_AES_KEY = "f5d965df75336270"
COVER_AES_IV = "97b60394abc2fbe1"

COMIC_IMG_API = "https://b5.xn--ruqv1b57ck8l04i31ecvcfzs0tovoonv4bff6a.xn--fiqs8s/content/comic"

STYLE_NONE = {"type": "rect", "ratio": 1.33}
PLACEHOLDER_PIC = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIxMDAiIGhlaWdodDoiMTQwIiB2aWV3Qm94PSIwIDAgMTAwIDE0MCI+PHJlY3Qgd2lkdGg9IjEwMCIgaGVpZ2h0PSIxNDAiIGZpbGw9IiMzYTMzYTMiLz48dGV4dCB4PSIxMCIgeT0iNzQiIGZvbnQtc2l6ZT0iOCIgZmlsbD0iI2ZmZiI+6L+Z55qE5a2X5YWs6rev5Zu2PC90ZXh0Pjwvc3ZnPg=="


class Spider(BaseSpider):

    def __init__(self):
        super().__init__()
        self.name = NAME
        self.options = {}
        self._lock = threading.Lock()
        self._cache = {}
        self._cache_time = {}
        self._good = {}
        self._aes_kv = None
        self._disc = {}
        try:
            raw = self.local.get("618_domains")
            if raw:
                rows = json.loads(raw)
                if isinstance(rows, list):
                    self._disc["__rows"] = rows
                    self._disc["__ts"] = time.time()
        except Exception:
            pass
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self._cj = http.cookiejar.CookieJar()
            self._opener = urllib.request.build_opener(
                urllib.request.HTTPCookieProcessor(self._cj),
                urllib.request.HTTPSHandler(context=ctx))
        except Exception:
            self._opener = None

    def init(self, extend=""):
        if isinstance(extend, dict):
            self.options = extend
        elif extend:
            try:
                cfg = json.loads(extend)
                if isinstance(cfg, dict):
                    self.options = cfg
            except Exception:
                pass

    def getDependence(self):
        return []

    def destroy(self):
        with self._lock:
            self._cache.clear()
            self._cache_time.clear()
        self.options = {}

    def isVideoFormat(self, url):
        return bool(re.search(r"\.(m3u8|mp4|flv|mkv|ts)(\?|$)", str(url)))

    def manualVideoCheck(self):
        return False

    def action(self, action):
        return {"msg": ""}

    def _dec(self, t):
        if not t:
            return ""
        try:
            return "".join(chr(128 ^ ord(c)) for c in t)
        except Exception:
            return t

    def _zone_idx(self, tid):
        try:
            i = int(tid)
            if 1 <= i <= 10:
                return i - 1
        except Exception:
            pass
        return 0

    def _zone_base(self, zi):
        good = self._good.get(zi)
        if good:
            return good
        c = self._cand(zi)
        return c[0] if c else ZONE_DOMAIN[zi][0].rstrip("/")

    def _cand(self, zi):
        out = []
        for u in ZONE_DOMAIN[zi]:
            u = u.rstrip("/")
            if u not in out:
                out.append(u)
        rows = self._disc.get("__rows") or []
        if len(rows) > zi:
            for v in rows[zi]:
                u = "https://618%s.xyz" % v
                if u not in out:
                    out.append(u)
        return out

    def _discover_domains(self, force=False):
        ts = self._disc.get("__ts") or 0
        if not force and ts and time.time() - ts < DISC_TTL and self._disc.get("__rows"):
            return
        js = ""
        try:
            js = self._get_html(BOOT_JS, timeout=8000)
        except Exception:
            js = ""
        if (not js or "zuArr=" not in js) and ZONE_DOMAIN:
            try:
                h = self._get_html(ZONE_DOMAIN[0][0].rstrip("/") + "/", timeout=6000)
                m = re.search(r'src="(https://donk666[^"]+\.js)"', h or "")
                if m:
                    js = self._get_html(m.group(1), timeout=6000)
            except Exception:
                pass
        rows = []
        if js and "zuArr=" in js:
            i = js.find("zuArr=")
            j = js.find("];for", i)
            body = js[i + 6:(j + 1 if j > 0 else len(js))]
            for r in re.findall(r"\[([^\[\]]+)\]", body):
                vals = [v.strip().strip("'\"") for v in r.split(",")]
                vals = [v for v in vals if v]
                if len(vals) > 5:
                    rows.append(vals)
        if rows:
            self._disc["__rows"] = rows
            self._disc["__ts"] = time.time()
            try:
                self.local.set("618_domains", json.dumps(rows))
            except Exception:
                pass

    def _ensure_zone(self, zi):
        if self._good.get(zi):
            return self._good[zi]
        self._discover_domains()
        probe = "/index.php/%s/type/id/%s.html" % (self._zone_path(zi), self._zone_tid(zi))
        cands = self._cand(zi)
        for base in cands[:6]:
            html = self._get_html(base + probe, timeout=4000)
            if html and len(html) > 2000:
                self._good[zi] = base
                return base
        for base in cands[6:14]:
            html = self._get_html(base + probe, timeout=2000)
            if html and len(html) > 2000:
                self._good[zi] = base
                return base
        self._good[zi] = cands[0] if cands else ZONE_DOMAIN[zi][0].rstrip("/")
        return self._good[zi]

    def _zone_path(self, zi):
        return ZONE_PATH[zi]

    def _zone_tid(self, zi):
        return ZONE_TID[zi]

    def _classes(self):
        arr = []
        for i, nm in enumerate(ZONE_NAMES):
            arr.append({"type_id": str(i + 1), "type_name": nm})
        return arr

    def _filters(self, classes):
        return {c["type_id"]: [] for c in classes}

    def homeContent(self, filter):
        result = {"class": self._classes()}
        result["list"] = []
        return result

    def homeVideoContent(self):
        return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        pg = self._int(pg, 1)
        tid = str(tid or "")
        if tid.startswith("folder/"):
            parts = tid.split("/", 2)
            if len(parts) == 3:
                try:
                    zi = int(parts[1]) - 1
                except Exception:
                    zi = 0
                val = unquote(parts[2])
                if val in ("", "_"):
                    items = self._folder_entries(zi)
                    return {"list": items, "page": 1, "pagecount": 1, "limit": 20, "total": len(items)}
                else:
                    items = self._fetch_list(zi, val, pg)
                    pc = self._pagecount(pg, items)
                    return {"list": [self._vod(x) for x in items], "page": pg,
                            "pagecount": pc, "limit": PAGE_SIZE, "total": 999999}
        zi = self._zone_idx(tid)
        items = self._folder_entries(zi)
        return {"list": items, "page": 1, "pagecount": 1, "limit": 20, "total": len(items)}

    def _int(self, x, d=0):
        try:
            return int(x)
        except Exception:
            return d

    def _parse_tp(self, html):
        m = re.search(r"totalPages\s*=\s*(?:parseInt\(\s*)?'(\d*)'", html or "")
        if m:
            try:
                return int(m.group(1) or 0)
            except Exception:
                return 0
        return 0

    def _pagecount(self, pg, items):
        tp = getattr(self, "_last_tp", 0) or 0
        if tp > 0:
            return tp
        return pg if len(items) < PAGE_SIZE else 9999

    def _fetch_folder_entries(self, type_):
        return self._folder_entries(self._int(type_, 0))

    def _folder_entries(self, zi, _retry=0):
        ck = "fe:%d" % zi
        hit = self._cache.get(ck)
        if hit and time.time() - self._cache_time.get(ck, 0) < 600:
            return hit
        base = self._zone_base(zi)
        path = self._zone_path(zi)
        self._ensure_zone(zi)
        out = []
        if zi == 6:
            html = self._get_html(base + "/index.php/art/type/id/30.html")
            for cid, cname in self._parse_comic_nav(html):
                out.append(self._folder_card(zi, cid, cname))
        elif zi == 3:
            html = self._get_html(base + "/index.php/art/type/id/5.html")
            out.append(self._folder_card(zi, "44", "欧美视频"))
            out.append(self._folder_card(zi, "40", "中文字幕2"))
            out.append(self._folder_card(zi, "17", "中文字幕"))
            out.append(self._folder_card(zi, "18", "无码破解"))
            for aid, aname in self._parse_actor_nav(html):
                out.append(self._folder_card(zi, aid, aname))
        else:
            if path == "art" and zi == 9:
                html = self._get_html(base + "/index.php/art/type/id/27.html")
                cats = self._parse_comic_nav(html)
            else:
                html = self._get_html(base + "/index.php/vod/type/id/%s.html" % self._zone_tid(zi))
                cats = self._parse_vod_nav(html)
            for cid, cname in cats:
                out.append(self._folder_card(zi, cid, cname))
        if not out and _retry < 1:
            self._good.pop(zi, None)
            self._discover_domains(True)
            return self._folder_entries(zi, _retry + 1)
        self._cache[ck] = out
        self._cache_time[ck] = time.time()
        return out

    def _fill_folder_covers_unused(self, zi, out, budget=5.0, cap=10):
        todo = []
        for card in out:
            pic = card.get("vod_pic") or ""
            if pic and not pic.startswith("data:"):
                continue
            try:
                cid = str(card.get("vod_id") or "").split("/", 2)[2]
            except Exception:
                cid = ""
            if cid:
                todo.append((card, cid))
        if not todo:
            return
        if len(todo) > cap:
            todo = todo[:cap]

        def work(pair):
            card, cid = pair
            try:
                return card, self._fetch_list(zi, cid, 1)
            except Exception:
                return card, []

        def apply(card, items):
            if items and items[0].get("pic"):
                pic = self._pic_proxy(items[0]["pic"], zi)
                if pic:
                    card["vod_pic"] = pic

        try:
            from concurrent.futures import ThreadPoolExecutor, as_completed
            ex = ThreadPoolExecutor(max_workers=10)
            futs = [ex.submit(work, pair) for pair in todo]
            deadline = time.time() + budget
            try:
                for f in as_completed(futs, timeout=budget + 4):
                    try:
                        card, items = f.result()
                    except Exception:
                        continue
                    apply(card, items)
                    if time.time() > deadline:
                        break
            except Exception:
                pass
            ex.shutdown(wait=False)
        except Exception:
            for pair in todo:
                card, items = work(pair)
                apply(card, items)

    def _parse_actor_nav(self, html):
        cats = []
        seen = set()
        for m in re.finditer(r'<a class="actor_name" href="([^"]+)"[^>]*>([^<]*)</a>', html):
            href, name = m.group(1), m.group(2).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            cats.append((quote(name, safe=""), name))
        return cats

    def _folder_card(self, zi, cid, cname):
        vid = "folder/%d/%s" % (zi + 1, cid)
        return {
            "vod_id": vid,
            "vod_name": str(cname or cid),
            "vod_pic": PLACEHOLDER_PIC,
            "vod_remarks": "",
            "vod_tag": "folder",
        }

    def _parse_vod_nav(self, html):
        cats = []
        seen = set()
        for m in re.finditer(r'href="/index\.php/vod/type/id/(\d+)\.html"[^>]*>([^<]*)</a>', html):
            cid, raw = m.group(1), m.group(2)
            name = self._dec(raw).strip()
            if not name or (cid, name) in seen:
                continue
            seen.add((cid, name))
            cats.append((cid, name))
        return cats

    def _parse_comic_nav(self, html):
        cats = []
        seen = set()
        for m in re.finditer(r'href="/index\.php/art/type/id/(\d+)\.html"[^>]*>([^<]*)</a>', html):
            cid, raw = m.group(1), m.group(2)
            if cid in seen:
                continue
            name = raw.strip()
            if not name:
                continue
            seen.add(cid)
            cats.append((cid, name))
        return cats

    def _fetch_list(self, zi, cid, pg):
        base = self._zone_base(zi)
        path = self._zone_path(zi)
        if zi == 3:
            if cid in ("44", "40"):
                url = base + "/index.php/vod/type/id/%s/page/%d.html" % (cid, pg)
                html = self._get_html(url)
                self._last_tp = self._parse_tp(html)
                return self._parse_vod_list(html, zi, cid)
            elif cid in ("5", "17", "18"):
                url = base + "/index.php/art/type/id/%s/page/%d.html" % (cid, pg)
            else:
                name = unquote(cid or "")
                url = base + "/index.php/art/type/id/5/wd/%s/page/%d.html" % (quote(name, safe=""), pg)
            html = self._get_html(url)
            self._last_tp = self._parse_tp(html)
            return self._parse_kvkv_list(html, zi, cid)
        if zi == 6:
            url = base + "/index.php/art/type/id/%s/page/%d.html" % (cid, pg)
            html = self._get_html(url)
            self._last_tp = self._parse_tp(html)
            return self._parse_tailwind_list(html, zi, cid)
        if zi == 9:
            url = base + "/index.php/art/type/id/%s/page/%d.html" % (cid, pg)
            html = self._get_html(url)
            self._last_tp = self._parse_tp(html)
            return self._parse_comic_list(html, zi, cid)
        url = base + "/index.php/vod/type/id/%s/page/%d.html" % (cid, pg)
        html = self._get_html(url)
        self._last_tp = self._parse_tp(html)
        return self._parse_vod_list(html, zi, cid)

    def _parse_vod_list(self, html, zi, cid):
        items = []
        if not html:
            return items
        for m in re.finditer(r'<a class="vodbox" href="([^"]+)"[^>]*>(.*?)</a>', html, re.S):
            href, inner = m.group(1), m.group(2)
            pic = self._first(r'data-original="([^"]+)"', inner)
            title = self._title_from_href(href)
            if not title:
                title = self._first(r'<p class="km-script">([^<]*)</p>', inner)
                title = self._dec(title).strip()
            if not title:
                title = self._first(r'<div class="title">([^<]*)</div>', inner).strip()
            if not title:
                continue
            play = self._play_from_href(href)
            items.append({
                "id": href,
                "name": title,
                "pic": pic,
                "remarks": "",
                "zone": zi,
                "cid": cid,
                "play": play,
            })
        if not items:
            items = self._parse_figure_list(html, zi, cid)
        if not items:
            items = self._parse_kvkv_list(html, zi, cid)
        return items

    def _parse_figure_list(self, html, zi, cid):
        items = []
        if not html:
            return items
        for m in re.finditer(r'<a[^>]+href="(/html/[^"]+)"[^>]*>(.*?)</a>', html, re.S):
            href, inner = m.group(1), m.group(2)
            title = self._title_from_href(href)
            if not title:
                raw = self._first(r'class="km-script"[^>]*>([^<]*)<', inner)
                title = self._dec(raw).strip()
            if not title:
                continue
            items.append({
                "id": href,
                "name": title,
                "pic": self._first(r'data-original="([^"]+)"', inner),
                "remarks": "",
                "zone": zi,
                "cid": cid,
            })
        return items

    def _parse_kvkv_list(self, html, zi, cid):
        items = []
        for m in re.finditer(r'<a href="(/html/kvkv/[^"]+)"[^>]*>(.*?)</a>', html, re.S):
            href, inner = m.group(1), m.group(2)
            pic = self._first(r'data-cover="([^"]+)"', inner)
            play = self._kvkv_play(href)
            title = self._title_from_href(href)
            items.append({
                "id": href,
                "name": title,
                "pic": pic,
                "remarks": "",
                "zone": zi,
                "cid": cid,
                "play": play,
                "kvkv": True,
            })
        return items

    def _parse_tailwind_list(self, html, zi, cid):
        items = []
        if not html:
            return items
        self._pick_kv(html)
        for m in re.finditer(r'<a href="(/index\.php/art/detail/id/\d+\.html)"[^>]*>(.*?)</a>', html, re.S):
            href, inner = m.group(1), m.group(2)
            title = self._first(r'<h3[^>]*>(.*?)</h3>', inner).strip()
            if not title:
                continue
            items.append({
                "id": href,
                "name": title,
                "pic": self._first(r'data-original="([^"]+)"', inner),
                "remarks": "",
                "zone": zi,
                "cid": cid,
                "play": self._play_from_href(href),
            })
        return items

    def _parse_comic_list(self, html, zi, cid):
        items = []
        if not html:
            return items
        for m in re.finditer(r'<li><a href="(/index\.php/art/detail/id/\d+\.html)"[^>]*>(.*?)</a></li>', html, re.S):
            href, inner = m.group(1), m.group(2)
            pic = self._first(r'data-original="([^"]+)"', inner)
            title = self._first(r'<div class="title">([^<]*)</div>', inner).strip()
            if not title:
                continue
            items.append({
                "id": href,
                "name": title,
                "pic": pic,
                "remarks": "",
                "zone": zi,
                "cid": cid,
                "comic": True,
            })
        return items

    def _play_from_href(self, href):
        m = re.search(r'\?(?:v|id|kd|m)=([^&"]+)', href)
        if not m:
            return ""
        return self._real_play(m.group(1))

    def _real_play(self, u):
        if not u:
            return u
        if "cloudfront.net" in u and "/m3u8/" in u:
            i = u.index("/m3u8/")
            return "https://%s.xyz%s" % (random.choice(SPLIT_HOSTS), u[i:])
        return u

    def _kvkv_play(self, href):
        m = re.search(r'\?m=([^&"]+)', href)
        return m.group(1) if m else ""

    def _first(self, pat, s):
        m = re.search(pat, s or "", re.S)
        return m.group(1) if m else ""

    def _vod(self, item):
        item = item or {}
        vid = item.get("id") or ""
        if item.get("comic"):
            return self._comic_vod(item)
        return {
            "vod_id": self._vod_id(vid, item.get("zone"), item.get("pic") or ""),
            "vod_name": item.get("name") or vid,
            "vod_pic": self._pic_proxy(item.get("pic") or "", item.get("zone")),
            "vod_remarks": item.get("remarks") or "",
        }

    def _pic_proxy(self, url, zi=None):
        if not url:
            return ""
        if "yimg.yidi.la" in url:
            return self._proxy_url({"type": "img", "url": quote(url, safe="")})
        if "2thewash.com" in url:
            return self._proxy_url({"type": "img", "url": quote(url, safe=""), "b64": "1"})
        if "lkkwip.cn" in url:
            return self._proxy_url({"type": "img", "url": quote(url, safe=""),
                                    "k": "xor:100:2019ysapp7527"})
        if "drleao.cn" in url:
            return PLACEHOLDER_PIC
        return url

    def _comic_vod(self, item):
        return {
            "vod_id": self._vod_id(item.get("id") or "", item.get("zone")),
            "vod_name": item.get("name") or "",
            "vod_pic": self._pic_proxy(item.get("pic") or ""),
            "vod_remarks": "漫画",
        }

    def _pic(self, item):
        return item.get("pic") or ""

    def _vod_id(self, site_id, zi=None, pic=""):
        s = str(site_id or "")
        if zi is None:
            return s
        head = "%d|%s" % (zi + 1, s)
        if pic:
            head += "|" + quote(str(pic), safe="")
        return head

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        results = []
        for vid in ids:
            vid = str(vid)
            if vid.startswith("folder/"):
                continue
            zi = None
            href = vid
            pic = ""
            parts = vid.split("|", 2)
            if len(parts) >= 2 and parts[0].isdigit():
                zi = int(parts[0]) - 1
                href = parts[1]
                if len(parts) > 2:
                    pic = unquote(parts[2])
            if zi == 6:
                results.extend(self._tailwind_detail(href, pic).get("list") or [])
            elif zi == 9 or href.startswith("/index.php/art/detail/"):
                results.extend(self._comic_detail(href).get("list") or [])
            else:
                results.extend(self._vod_detail(href).get("list") or [])
        return {"list": results}

    def _vod_detail(self, vid):
        title = self._title_from_href(vid)
        play_url = ""
        m = re.search(r'\?(?:v|id|kd|m)=([^&"\']+)', vid)
        if m:
            play_url = m.group(1)
            if play_url.isdigit():
                play_url = "https://h5.xxoo475.org/api/v2/vod/reqplay/" + play_url
                play_url += "||" + self._zone_base(0) + vid
            else:
                play_url = self._real_play(play_url)
        if not play_url:
            html = self._get_html(vid)
            play_url = self._extract_play_from_html(html)
        if play_url and play_url.startswith("/"):
            play_url = self._kvkv_abs(play_url)
        if play_url and play_url.startswith("http") and "618791.xyz" in play_url:
            pass
        vod = {
            "vod_id": self._vod_id(vid),
            "vod_name": title or "视频",
            "vod_pic": "",
            "vod_remarks": "",
            "vod_content": "",
            "vod_play_from": "正片",
            "vod_play_url": "正片$" + play_url if play_url else "",
        }
        return {"list": [vod]}

    def _title_from_href(self, href):
        m = re.search(r'/html/[a-z]+/([^?"]+)\.html', href)
        if not m:
            return ""
        return self._dec(m.group(1)).strip()

    def _extract_play_from_html(self, html):
        if not html:
            return ""
        patterns = [
            r'const\s+mk\s*=\s*[^;]*?\'([^\']*m3u8[^\']*)\'',
            r'const\s+mk\s*=\s*"([^"]*m3u8[^"]*)"',
            r'const\s+mk\s*=\s*\'([^\']*m3u8[^\']*)\'',
            r'url\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
            r'(https?://[^\s"\']+\.m3u8[^\s"\']*)',
        ]
        for p in patterns:
            m = re.search(p, html)
            if m:
                v = m.group(1)
                return v
        return ""

    def _kvkv_abs(self, mpath):
        if mpath.startswith("http"):
            return mpath
        return "https://618791.xyz/web" + mpath if mpath.startswith("/") else mpath

    def _pick_kv(self, html):
        if not html:
            return
        m = re.search(r'media_key\s*=\s*CryptoJS\.enc\.Utf8\.parse\("([^"]+)"', html)
        n = re.search(r'media_iv\s*=\s*CryptoJS\.enc\.Utf8\.parse\("([^"]+)"', html)
        try:
            k = "".join(chr(int(x)) for x in m.group(1).split("_") if x) if m else ""
            v = "".join(chr(int(x)) for x in n.group(1).split("_") if x) if n else ""
        except Exception:
            k = v = ""
        if k and v:
            self._aes_kv = (k, v)

    def _tailwind_detail(self, vid, pic=""):
        html = self._get_html(self._zone_base(6) + vid)
        self._pick_kv(html)
        title = ""
        m = re.search(r"<title>([^<]*)</title>", html or "")
        if m:
            title = m.group(1).strip()
        if not title:
            m = re.search(r"const episod = '([^']*)'", html or "")
            if m:
                title = m.group(1).strip()
        lines = []
        em = re.search(r"const episodes = (\[.*?\]);", html or "", re.S)
        if em:
            try:
                for ep in json.loads(re.sub(r",\s*]", "]", em.group(1))):
                    num = str(ep.get("number") or "")
                    if num.startswith("http"):
                        lines.append("%s$%s" % (self._safe_label(ep.get("title") or "正片"), num))
            except Exception:
                pass
        vod = {
            "vod_id": self._vod_id(vid, 6, pic),
            "vod_name": title or "视频",
            "vod_pic": self._pic_proxy(pic, 6) if pic else "",
            "vod_remarks": "共%d集" % len(lines),
            "vod_content": "",
            "vod_play_from": "正片",
            "vod_play_url": "#".join(lines),
        }
        return {"list": [vod]}

    def _comic_detail(self, vid):
        html = self._get_html(self._zone_base(9) + vid)
        title = ""
        episodes = []
        if html:
            m = re.search(r'<title>([^<]*)</title>', html)
            if m:
                title = m.group(1).strip()
            em = re.search(r'const episodes = (\[.*?\]);', html, re.S)
            if em:
                try:
                    eps = json.loads(em.group(1))
                    for ep in eps:
                        num = ep.get("number") or ""
                        nm = ep.get("title") or ""
                        pages = ep.get("pages") or 0
                        episodes.append((num, nm, pages))
                except Exception:
                    episodes = []
        play_from = "漫画"
        play_url = "#".join("%s$%s||%d" % (self._safe_label(nm or ("第%d话" % (i + 1))), num, pages)
                            for i, (num, nm, pages) in enumerate(episodes))
        vod = {
            "vod_id": self._vod_id(vid),
            "vod_name": title or "漫画",
            "vod_pic": self._comic_cover(html),
            "vod_remarks": "共%d话" % len(episodes),
            "vod_content": "",
            "vod_play_from": play_from,
            "vod_play_url": play_url,
        }
        return {"list": [vod]}

    def _comic_cover(self, html):
        if not html:
            return ""
        m = re.search(r'const imageUrl = \'([^\']+)\'', html)
        return m.group(1) if m else ""

    def _safe_label(self, t):
        return str(t or "").replace("$", "＄").replace("#", "＃").strip()

    def _fetch_play(self, play_id):
        if "||" in play_id:
            return play_id.split("||", 1)[0]
        return play_id

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "")
        page_url = ""
        if "||" in raw:
            _h, _t = raw.split("||", 1)
            if _t[:4].lower() == "http":
                raw, page_url = _h, _t
        if "||" in raw:
            head = raw.split("||", 1)[0]
            pages = 0
            try:
                pages = int(raw.split("||", 1)[1])
            except Exception:
                pages = 0
            m = re.search(r'(\d+)-(\d+)', head)
            if m and pages > 0:
                params = {"type": "comicm3u8", "c": m.group(1), "e": m.group(2), "p": str(pages)}
                return {"parse": 0, "url": self._proxy_url(params),
                        "header": self._string_map({"User-Agent": UA})}
        url = raw
        if "reqplay" in url:
            real = self._resolve_reqplay(url)
            if not real:
                if page_url:
                    return {"parse": 1, "jx": 0, "url": page_url,
                            "header": self._string_map({"User-Agent": UA})}
                return {"parse": 0, "msg": "播放地址获取失败"}
            url = real
        elif url and not url.startswith("http"):
            url = self._fix_play(url)
        if not url:
            return {"parse": 0, "msg": "无法获取播放地址"}
        return {"parse": 0, "url": url,
                "header": self._string_map({"User-Agent": UA})}

    def _resolve_reqplay(self, api):
        try:
            txt = self._get_html(api)
            j = json.loads(txt)
        except Exception:
            return ""
        d = j.get("data") or {}
        if j.get("retcode") == 3:
            u = d.get("httpurl_preview") or d.get("httpurl") or ""
        else:
            u = d.get("httpurl") or ""
        return str(u or "").replace("?300", "")

    def _fix_play(self, u):
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return "https://618791.xyz/web" + u
        return "https://618791.xyz/web/" + u

    def searchContent(self, key, quick, pg="1"):
        pg = self._int(pg, 1)
        items = self._fetch_search(key, pg)
        return {"list": [self._vod(x) for x in items], "page": pg,
                "pagecount": pg if len(items) < PAGE_SIZE else 9999, "limit": PAGE_SIZE, "total": 999999}

    def _fetch_search(self, key, pg):
        key = str(key or "").strip()
        if not key:
            return []
        allitems = []
        seen = set()
        for zi in range(9):
            if ZONE_PATH[zi] != "vod":
                continue
            base = self._zone_base(zi)
            url = base + "/index.php/vod/type/id/1/wd/%s/page/%d.html" % (quote(key, safe=""), pg)
            html = self._get_html(url)
            items = self._parse_vod_list(html, zi, "1")
            for it in items:
                if it["id"] in seen:
                    continue
                seen.add(it["id"])
                allitems.append(it)
        return allitems[:40]

    def liveContent(self, url):
        return "[]"

    def proxy(self, params):
        return self._do_proxy(params)

    def localProxy(self, params):
        return self._do_proxy(params)

    def _do_proxy(self, params):
        if isinstance(params, str):
            try:
                params = json.loads(params)
            except Exception:
                return [404, "text/plain", ""]
        if not isinstance(params, dict):
            return [404, "text/plain", ""]
        t = params.get("type")
        if t == "comicm3u8":
            c = params.get("c") or ""
            e = params.get("e") or ""
            try:
                pages = int(params.get("p") or 0)
            except Exception:
                pages = 0
            lines = ["#EXTM3U", "#EXT-X-VERSION:3",
                     "#EXT-X-TARGETDURATION:9", "#EXT-X-MEDIA-SEQUENCE:0"]
            for n in range(1, pages + 1):
                lines.append("#EXTINF:9.000,")
                lines.append(self._proxy_url({"type": "comicimg", "c": c, "e": e, "n": str(n)}))
            lines.append("#EXT-X-ENDLIST")
            return [200, "application/vnd.apple.mpegurl", "\n".join(lines) + "\n",
                    {"User-Agent": UA}]
        if t == "comicimg":
            c = params.get("c") or ""
            e = params.get("e") or ""
            n = params.get("n") or "1"
            url = "%s/%s/%s/%s" % (COMIC_IMG_API, c, e, n)
            txt = self._get_raw(url)
            if not txt:
                return [404, "text/plain", ""]
            try:
                raw = base64.b64decode(txt.strip())
            except Exception:
                return [404, "text/plain", ""]
            if not raw:
                return [404, "text/plain", ""]
            mime = self._img_mime(raw)
            if not mime:
                return [404, "text/plain", ""]
            return [200, mime, self._img_stream(raw), {"User-Agent": UA}]
        if t == "img":
            url = self._unwrap_url(params.get("url") or "")
            if not url:
                return [404, "text/plain", ""]
            ref = params.get("ref") or None
            if not ref and "drleao.cn" in url:
                ref = "https://618620.xyz/"
            raw = self._fetch_bytes(url, referer=ref)
            if not raw:
                raw = self._fetch_bytes(url)
            if not raw and url[:8] == "https://":
                raw = self._fetch_bytes("http://" + url[8:], referer=ref)
            if not raw and "drleao.cn" in url:
                for alt in ("new1", "new3", "pic", "new"):
                    u2 = re.sub(r"https?://[^/]+", "https://%s.drleao.cn" % alt, url)
                    raw = self._fetch_bytes(u2, referer=ref)
                    if raw:
                        break
            if not raw:
                return [404, "text/plain", ""]
            if str(params.get("b64") or "") == "1":
                try:
                    raw = base64.b64decode(re.sub(rb"\s", b"", raw))
                except Exception:
                    return [404, "text/plain", ""]
            if "yimg.yidi.la" in url:
                b = bytearray(raw)
                for i in range(min(16, len(b))):
                    b[i] ^= 0x5A
                raw = bytes(b)
            k = str(params.get("k") or "")
            if k.startswith("xor:"):
                bits = k.split(":", 2)
                try:
                    n = int(bits[1])
                    key = bits[2].encode("utf-8")
                except Exception:
                    n, key = 0, b""
                if key:
                    b = bytearray(raw)
                    for i in range(min(n, len(b))):
                        b[i] ^= key[i % len(key)]
                    raw = bytes(b)
            if k.startswith("aes:"):
                bits = k.split(":", 2)
                enc = raw
                try:
                    raw = aes_cbc_raw(enc, bits[1].encode("utf-8"), bits[2].encode("utf-8"))
                except Exception:
                    raw = b""
                if not self._looks_img(raw):
                    raw = enc
            if not raw:
                return [404, "text/plain", ""]
            mime = self._img_mime(raw)
            if not mime:
                return [404, "text/plain", ""]
            return [200, mime, self._img_stream(raw), {"User-Agent": UA}]
        if t == "hls":
            url = self._unwrap_url(params.get("url") or "")
            if not url:
                return [404, "text/plain", ""]
            txt = self._get_html(url)
            if not txt:
                return [404, "text/plain", ""]
            if "#EXT-X-STREAM-INF" in txt:
                from urllib.parse import urljoin
                lines = txt.replace("\r\n", "\n").split("\n")
                for i, l in enumerate(lines):
                    if "#EXT-X-STREAM-INF" in l:
                        for j in range(i + 1, len(lines)):
                            v = lines[j].strip()
                            if v and not v.startswith("#"):
                                url = urljoin(url, v)
                                txt = self._get_html(url)
                                break
                        break
            out = self._rewrite_hls(txt, url)
            return [200, "application/vnd.apple.mpegurl", out, {"User-Agent": UA}]
        if t == "seg":
            url = self._unwrap_url(params.get("url") or "")
            if not url:
                return [404, "text/plain", ""]
            raw = self._fetch_bytes(url)
            if not raw:
                return [404, "text/plain", ""]
            low = url.lower()
            if ".key" in low or "/keys/" in low:
                mime = "application/octet-stream"
            else:
                mime = "video/mp2t"
            return [200, mime, self._img_stream(raw), {"User-Agent": UA}]
        return [404, "text/plain", ""]

    def _rewrite_hls(self, text, base_url):
        from urllib.parse import urljoin
        out = []
        for line in text.replace("\r\n", "\n").split("\n"):
            s = line.strip()
            if not s:
                out.append(line)
                continue
            if s.startswith("#"):
                def repl(m):
                    return 'URI="%s"' % urljoin(base_url, m.group(1))
                out.append(re.sub(r'URI="([^"]+)"', repl, s))
            else:
                out.append(urljoin(base_url, s))
        return "\n".join(out) + "\n"

    def _unwrap_url(self, u):
        u = str(u or "")
        for _ in range(3):
            if u.startswith("http://") or u.startswith("https://"):
                break
            n = unquote(u)
            if n == u:
                break
            u = n
        return u

    def _looks_img(self, d):
        if not d:
            return False
        return d[:3] == b"\xff\xd8\xff" or d[:4] == b"\x89PNG" or d[:4] == b"GIF8" or (d[:4] == b"RIFF" and d[8:12] == b"WEBP")

    def _img_mime(self, data):
        if data[:3] == b"\xff\xd8\xff":
            return "image/jpeg"
        if data[:4] == b"\x89PNG":
            return "image/png"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "image/webp"
        if data[:3] == b"GIF":
            return "image/gif"
        return ""

    def _img_stream(self, data):
        net = getattr(self, "net", None)
        if net is not None and hasattr(net, "stream"):
            try:
                def _gen():
                    yield data
                return net.stream(_gen())["stream"]
            except Exception:
                pass
        return data

    def _proxy_url(self, params):
        net = getattr(self, "net", None)
        if net is not None and hasattr(self, "proxyUrl"):
            try:
                return self.proxyUrl(params, True)
            except Exception:
                pass
        if params.get("type") == "img":
            try:
                from com.github.catvod import Proxy as _CP
                base = str(_CP.getUrl(True))
                if not base.endswith("/proxy"):
                    base = base.rstrip("/") + "/proxy"
                sk = quote(str(getattr(self, "siteKey", "")), safe="")
                qs = "&".join("%s=%s" % (k, quote(str(v), safe="")) for k, v in params.items())
                return base + "?do=py&siteKey=" + sk + "&" + qs
            except Exception:
                pass
        qs = "&".join("%s=%s" % (k, quote(str(v), safe="")) for k, v in params.items())
        return "proxy://do=py" + ("&" + qs if qs else "")

    @staticmethod
    def _string_map(value, name="headers"):
        if value in (None, ""):
            return {}
        if not isinstance(value, dict):
            return {}
        return {str(k): str(v) for k, v in value.items() if v is not None}

    def _req(self, url, **kw):
        net = getattr(self, "net", None)
        if net is not None:
            try:
                opts = {"timeout": kw.get("timeout", 12000)}
                for k in ("params", "headers", "method", "postType", "data", "body", "buffer", "redirect", "callTimeout", "cookie"):
                    if k in kw and kw[k] is not None:
                        opts[k] = kw[k]
                resp = net.req(url, opts)
                return resp or {}
            except Exception:
                return {}
        fetch = getattr(self, "fetch", None)
        if fetch is not None and callable(fetch):
            try:
                headers = dict(kw.get("headers") or {})
                timeout = (kw.get("timeout") or 12000) / 1000.0
                rsp = fetch(url, headers=headers, timeout=timeout)
                if kw.get("buffer") == 3:
                    content = rsp.content
                else:
                    content = rsp.text if hasattr(rsp, "text") else rsp.content
                return {"code": getattr(rsp, "status_code", 200), "content": content,
                        "headers": dict(getattr(rsp, "headers", {}) or {}), "error": None}
            except Exception:
                pass
        return self._req_urllib(url, **kw)

    def _req_urllib(self, url, **kw):
        try:
            timeout = (kw.get("timeout") or 12000) / 1000.0
            headers = dict(kw.get("headers") or {})
            headers.setdefault("User-Agent", UA)
            req = urllib.request.Request(url, headers=headers)
            opener = self._opener or urllib.request
            with opener.open(req, timeout=timeout) as resp:
                raw = resp.read()
                enc = (resp.headers.get("Content-Encoding") or "").lower()
                if enc == "gzip" or raw[:2] == b"\x1f\x8b":
                    try:
                        raw = gzip.decompress(raw)
                    except Exception:
                        pass
                elif enc == "deflate":
                    try:
                        raw = zlib.decompress(raw)
                    except Exception:
                        pass
                code = resp.getcode() or 0
                ctype = resp.headers.get("Content-Type", "")
                if "text" in ctype or "json" in ctype or "mpegurl" in ctype:
                    content = raw.decode("utf-8", "replace")
                else:
                    content = raw.decode("utf-8", "replace")
                return {"code": code, "content": content, "headers": dict(resp.headers), "error": None}
        except urllib.error.HTTPError as e:
            return {"code": getattr(e, "code", 0), "content": "", "headers": {}, "error": str(e)}
        except Exception as e:
            return {"code": 0, "content": "", "headers": {}, "error": str(e)}

    def _get_html(self, url, **kw):
        ck = "u:" + url
        hit = self._cache.get(ck)
        if hit and time.time() - self._cache_time.get(ck, 0) < 300:
            return hit
        resp = self._req(url, **kw)
        txt = ""
        if resp:
            code = resp.get("code") or 0
            if code != 404 and 200 <= code < 300:
                txt = resp.get("content", "") or ""
        if txt:
            self._cache[ck] = txt
            self._cache_time[ck] = time.time()
        return txt

    def _get_raw(self, url):
        resp = self._req(url, buffer=3, timeout=12000)
        if resp and (200 <= (resp.get("code") or 0) < 300):
            c = resp.get("content")
            if isinstance(c, bytes):
                return c.decode("utf-8", "replace")
            return c or ""
        return ""

    def _fetch_bytes(self, url, referer=None):
        if not url:
            return b""
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            _op = urllib.request.build_opener(urllib.request.HTTPSHandler(context=ctx))
            headers = {"User-Agent": UA, "Referer": referer or "",
                       "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                       "Accept-Language": "zh-CN,zh;q=0.9",
                       "Sec-Fetch-Dest": "image", "Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Site": "cross-site"}
            req = urllib.request.Request(url, headers=headers)
            with _op.open(req, timeout=15) as resp:
                return resp.read()
        except Exception:
            pass
        try:
            ip = self._doh_resolve(urllib.parse.urlsplit(url).hostname or "")
            if ip:
                return self._fetch_via_ip(url, ip, headers)
        except Exception:
            pass
        return b""

    def _doh_resolve(self, host):
        if not host:
            return ""
        for api in ("https://dns.alidns.com/resolve?name=%s&type=A",
                    "https://doh.pub/dns-query?name=%s&type=A"):
            try:
                req = urllib.request.Request(api % quote(host, safe=""),
                                             headers={"User-Agent": UA, "Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=8) as r:
                    d = json.loads(r.read().decode("utf-8", "replace"))
                ips = [a.get("data") for a in (d.get("Answer") or []) if a.get("type") == 1]
                if ips:
                    return ips[0]
            except Exception:
                continue
        return ""

    def _fetch_via_ip(self, url, ip, headers=None):
        sp = urllib.parse.urlsplit(url)
        host = sp.hostname or ""
        path = sp.path or "/"
        if sp.query:
            path += "?" + sp.query
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        raw = socket.create_connection((ip, 443), timeout=15)
        sock = ctx.wrap_socket(raw, server_hostname=host)
        conn = http.client.HTTPSConnection(ip, 443, timeout=15)
        conn.sock = sock
        h = {"Host": host, "User-Agent": UA, "Accept": "*/*"}
        if headers:
            for k, v in headers.items():
                if k.lower() not in ("host", "accept-encoding"):
                    h[k] = v
        conn.request("GET", path, headers=h)
        r = conn.getresponse()
        data = r.read()
        enc = (r.getheader("Content-Encoding") or "").lower()
        try:
            conn.close()
        except Exception:
            pass
        if enc == "gzip" or data[:2] == b"\x1f\x8b":
            try:
                data = gzip.decompress(data)
            except Exception:
                pass
        return data

_SBOX = [
    0x63,0x7c,0x77,0x7b,0xf2,0x6b,0x6f,0xc5,0x30,0x01,0x67,0x2b,0xfe,0xd7,0xab,0x76,
    0xca,0x82,0xc9,0x7d,0xfa,0x59,0x47,0xf0,0xad,0xd4,0xa2,0xaf,0x9c,0xa4,0x72,0xc0,
    0xb7,0xfd,0x93,0x26,0x36,0x3f,0xf7,0xcc,0x34,0xa5,0xe5,0xf1,0x71,0xd8,0x31,0x15,
    0x04,0xc7,0x23,0xc3,0x18,0x96,0x05,0x9a,0x07,0x12,0x80,0xe2,0xeb,0x27,0xb2,0x75,
    0x09,0x83,0x2c,0x1a,0x1b,0x6e,0x5a,0xa0,0x52,0x3b,0xd6,0xb3,0x29,0xe3,0x2f,0x84,
    0x53,0xd1,0x00,0xed,0x20,0xfc,0xb1,0x5b,0x6a,0xcb,0xbe,0x39,0x4a,0x4c,0x58,0xcf,
    0xd0,0xef,0xaa,0xfb,0x43,0x4d,0x33,0x85,0x45,0xf9,0x02,0x7f,0x50,0x3c,0x9f,0xa8,
    0x51,0xa3,0x40,0x8f,0x92,0x9d,0x38,0xf5,0xbc,0xb6,0xda,0x21,0x10,0xff,0xf3,0xd2,
    0xcd,0x0c,0x13,0xec,0x5f,0x97,0x44,0x17,0xc4,0xa7,0x7e,0x3d,0x64,0x5d,0x19,0x73,
    0x60,0x81,0x4f,0xdc,0x22,0x2a,0x90,0x88,0x46,0xee,0xb8,0x14,0xde,0x5e,0x0b,0xdb,
    0xe0,0x32,0x3a,0x0a,0x49,0x06,0x24,0x5c,0xc2,0xd3,0xac,0x62,0x91,0x95,0xe4,0x79,
    0xe7,0xc8,0x37,0x6d,0x8d,0xd5,0x4e,0xa9,0x6c,0x56,0xf4,0xea,0x65,0x7a,0xae,0x08,
    0xba,0x78,0x25,0x2e,0x1c,0xa6,0xb4,0xc6,0xe8,0xdd,0x74,0x1f,0x4b,0xbd,0x8b,0x8a,
    0x70,0x3e,0xb5,0x66,0x48,0x03,0xf6,0x0e,0x61,0x35,0x57,0xb9,0x86,0xc1,0x1d,0x9e,
    0xe1,0xf8,0x98,0x11,0x69,0xd9,0x8e,0x94,0x9b,0x1e,0x87,0xe9,0xce,0x55,0x28,0xdf,
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16]
_RSBOX = [
    0x52,0x09,0x6a,0xd5,0x30,0x36,0xa5,0x38,0xbf,0x40,0xa3,0x9e,0x81,0xf3,0xd7,0xfb,
    0x7c,0xe3,0x39,0x82,0x9b,0x2f,0xff,0x87,0x34,0x8e,0x43,0x44,0xc4,0xde,0xe9,0xcb,
    0x54,0x7b,0x94,0x32,0xa6,0xc2,0x23,0x3d,0xee,0x4c,0x95,0x0b,0x42,0xfa,0xc3,0x4e,
    0x08,0x2e,0xa1,0x66,0x28,0xd9,0x24,0xb2,0x76,0x5b,0xa2,0x49,0x6d,0x8b,0xd1,0x25,
    0x72,0xf8,0xf6,0x64,0x86,0x68,0x98,0x16,0xd4,0xa4,0x5c,0xcc,0x5d,0x65,0xb6,0x92,
    0x6c,0x70,0x48,0x50,0xfd,0xed,0xb9,0xda,0x5e,0x15,0x46,0x57,0xa7,0x8d,0x9d,0x84,
    0x90,0xd8,0xab,0x00,0x8c,0xbc,0xd3,0x0a,0xf7,0xe4,0x58,0x05,0xb8,0xb3,0x45,0x06,
    0xd0,0x2c,0x1e,0x8f,0xca,0x3f,0x0f,0x02,0xc1,0xaf,0xbd,0x03,0x01,0x13,0x8a,0x6b,
    0x3a,0x91,0x11,0x41,0x4f,0x67,0xdc,0xea,0x97,0xf2,0xcf,0xce,0xf0,0xb4,0xe6,0x73,
    0x96,0xac,0x74,0x22,0xe7,0xad,0x35,0x85,0xe2,0xf9,0x37,0xe8,0x1c,0x75,0xdf,0x6e,
    0x47,0xf1,0x1a,0x71,0x1d,0x29,0xc5,0x89,0x6f,0xb7,0x62,0x0e,0xaa,0x18,0xbe,0x1b,
    0xfc,0x56,0x3e,0x4b,0xc6,0xd2,0x79,0x20,0x9a,0xdb,0xc0,0xfe,0x78,0xcd,0x5a,0xf4,
    0x1f,0xdd,0xa8,0x33,0x88,0x07,0xc7,0x31,0xb1,0x12,0x10,0x59,0x27,0x80,0xec,0x5f,
    0x60,0x51,0x7f,0xa9,0x19,0xb5,0x4a,0x0d,0x2d,0xe5,0x7a,0x9f,0x93,0xc9,0x9c,0xef,
    0xa0,0xe0,0x3b,0x4d,0xae,0x2a,0xf5,0xb0,0xc8,0xeb,0xbb,0x3c,0x83,0x53,0x99,0x61,
    0x17,0x2b,0x04,0x7e,0xba,0x77,0xd6,0x26,0xe1,0x69,0x14,0x63,0x55,0x21,0x0c,0x7d]


def _aes_xtime(a):
    a <<= 1
    if a & 0x100:
        a ^= 0x11b
    return a & 0xff


def _aes_mul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = _aes_xtime(a)
        b >>= 1
    return r & 0xff


def _aes_key_expansion(key):
    rcon = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]
    w = [list(key[4 * i:4 * i + 4]) for i in range(4)]
    for i in range(4, 44):
        temp = list(w[i - 1])
        if i % 4 == 0:
            temp = temp[1:] + temp[:1]
            temp = [_SBOX[b] for b in temp]
            temp[0] ^= rcon[i // 4 - 1]
        w.append([w[i - 4][j] ^ temp[j] for j in range(4)])
    return w


def _aes_decrypt_block(block, w):
    state = [[block[r + 4 * c] for c in range(4)] for r in range(4)]

    def add_round_key(s, rnd):
        for c in range(4):
            for r in range(4):
                s[r][c] ^= w[rnd * 4 + c][r]

    def inv_shift_rows(s):
        row = list(s[1]); s[1][0], s[1][1], s[1][2], s[1][3] = row[3], row[0], row[1], row[2]
        row = list(s[2]); s[2][0], s[2][1], s[2][2], s[2][3] = row[2], row[3], row[0], row[1]
        row = list(s[3]); s[3][0], s[3][1], s[3][2], s[3][3] = row[1], row[2], row[3], row[0]

    def inv_sub_bytes(s):
        for r in range(4):
            for c in range(4):
                s[r][c] = _RSBOX[s[r][c]]

    def inv_mix_columns(s):
        for c in range(4):
            a0, a1, a2, a3 = s[0][c], s[1][c], s[2][c], s[3][c]
            s[0][c] = _aes_mul(a0, 0x0e) ^ _aes_mul(a1, 0x0b) ^ _aes_mul(a2, 0x0d) ^ _aes_mul(a3, 0x09)
            s[1][c] = _aes_mul(a0, 0x09) ^ _aes_mul(a1, 0x0e) ^ _aes_mul(a2, 0x0b) ^ _aes_mul(a3, 0x0d)
            s[2][c] = _aes_mul(a0, 0x0d) ^ _aes_mul(a1, 0x09) ^ _aes_mul(a2, 0x0e) ^ _aes_mul(a3, 0x0b)
            s[3][c] = _aes_mul(a0, 0x0b) ^ _aes_mul(a1, 0x0d) ^ _aes_mul(a2, 0x09) ^ _aes_mul(a3, 0x0e)

    add_round_key(state, 10)
    for rnd in range(9, 0, -1):
        inv_shift_rows(state)
        inv_sub_bytes(state)
        add_round_key(state, rnd)
        inv_mix_columns(state)
    inv_shift_rows(state)
    inv_sub_bytes(state)
    add_round_key(state, 0)
    return bytes(state[r][c] for c in range(4) for r in range(4))


def _aes128_cbc_decrypt_py(ciphertext, key, iv):
    key = key if len(key) == 16 else key.encode("utf-8")
    iv = iv if len(iv) == 16 else iv.encode("utf-8")
    if len(ciphertext) % 16 != 0 or not ciphertext:
        return b""
    w = _aes_key_expansion(key)
    prev = list(iv)
    out = bytearray()
    for i in range(0, len(ciphertext), 16):
        block = ciphertext[i:i + 16]
        dec = _aes_decrypt_block(block, w)
        out.extend(bytes(dec[j] ^ prev[j] for j in range(16)))
        prev = list(block)
    if out:
        pad = out[-1]
        if 1 <= pad <= 16 and pad <= len(out):
            out = out[:-pad]
    return bytes(out)



_HAVE_CRYPTO = False
try:
    from Crypto.Cipher import AES as _PyCryptoAES
    _HAVE_CRYPTO = True
except Exception:
    _PyCryptoAES = None


def aes_cbc_raw(data, key, iv):
    if not data or len(data) % 16 != 0:
        return b""
    if isinstance(key, str):
        key = key.encode("utf-8")
    if isinstance(iv, str):
        iv = iv.encode("utf-8")
    if _HAVE_CRYPTO:
        try:
            return _PyCryptoAES.new(key, _PyCryptoAES.MODE_CBC, iv).decrypt(data)
        except Exception:
            pass
    w = _aes_key_expansion(key)
    prev = list(iv)
    out = bytearray()
    for i in range(0, len(data), 16):
        blk = data[i:i + 16]
        dec = _aes_decrypt_block(blk, w)
        out.extend(bytes(dec[j] ^ prev[j] for j in range(16)))
        prev = list(blk)
    return bytes(out)
