# -*- coding: utf-8 -*-
# SweetPorn

import re
import json
import requests
from urllib.parse import quote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://se.sweetpornos.com"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    BRAND = "蝴蝶影视"
    LINE_NAME = "🦋 蝴蝶专线"
    RELATED_LINE = "相关推荐"
    POSTER_RATIO = 1.65
    PAGE_SIZE = 24
    TIMEOUT = 8

    CATEGORIES = [
        ("hd-porno", "高清视界"), ("russian", "俄罗斯风"), ("russkaya-ozvuchka", "俄语配音"),
        ("domashnee", "素人自拍"), ("aziatki", "东方诱惑"), ("anal", "后庭盛宴"),
        ("studentki", "青春女校"), ("milf", "风韵少妇"), ("zrelye-milfy", "极品熟女"),
        ("molodye", "年轻女孩"), ("kasting", "名优试镜"), ("grupovoe", "多人狂欢"),
        ("kukold", "绿帽迷局"), ("kunilingus", "舌尖深吻"), ("anilingus", "秘境探幽"),
        ("minet", "深喉唇齿"), ("orgazm", "高潮绝顶"), ("konchil-v-pizdu-krempay", "内射中出"),
        ("dvoynoe-proniknovenie", "双管齐下"), ("negry", "巨器狂欢"), ("blondinki", "金发娇娃"),
        ("bryunetki", "深发尤物"), ("shatenki", "棕发丽人"), ("redhead", "红发天使"),
        ("bolshie-siski", "巨乳波霸"), ("bolshie-jopy", "丰臀美尻"), ("fetish", "恋物情结"),
        ("chulki-i-kolgotki", "丝袜美腿"), ("strapon", "假阳支配"), ("dominirovanie", "女王调教"),
        ("jestkoe", "硬核狂暴"), ("fisting", "深度极限"), ("izmena", "禁忌出轨"),
        ("incest", "家庭密事"), ("medsestry", "白衣护士"), ("maid", "贴身女仆"),
        ("secretaries", "职场秘恋"), ("massaj", "精油按摩"), ("masturbaciya", "独奏自慰"),
        ("lesbiyanki", "百合闺蜜"), ("porno-podborki", "精彩合集"), ("multiki", "动漫二次元"),
        ("skrytaya-kamera", "针孔偷拍"), ("beautiful", "唯美写真"),
    ]

    QUALITY_ORDER = ["1080P", "720P", "480P", "360P", "HD", "标清"]

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
        return "SweetPorn"

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        return (".m3u8" in low) or (".mp4" in low) or (".flv" in low) or (".mpd" in low)

    def manualVideoCheck(self):
        return False

    def _fetch(self, url, referer=None):
        headers = {"User-Agent": self.DEFAULT_UA, "Referer": referer or (self.host + "/")}
        try:
            resp = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            return resp.status_code, resp.text or ""
        except Exception:
            return -1, ""

    def _clean(self, s):
        out = str(s or "")
        out = out.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        out = out.replace("&quot;", '"').replace("&#39;", "'")
        return out.strip()

    def _absolutize(self, u):
        u = str(u or "").strip()
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return self.host + u
        return u

    def _format_poster(self, raw):
        if not raw:
            return ""
        return self._absolutize(self._clean(raw))

    def _parse_duration_iso(self, iso):
        if not iso:
            return ""
        m = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", str(iso))
        if not m:
            return str(iso)
        h = m.group(1) or "0"
        mi = (m.group(2) or "0").zfill(2)
        s = (m.group(3) or "0").zfill(2)
        if h != "0":
            return h + ":" + mi + ":" + s
        return mi + ":" + s

    def _translate_ru2zh(self, text):
        if not text:
            return ""
        try:
            resp = requests.post(
                "https://aidemo.youdao.com/trans",
                data={"q": text, "from": "Auto", "to": "zh-CHS"},
                headers={"User-Agent": self.DEFAULT_UA},
                timeout=3,
            )
            data = resp.json()
            tr = data.get("translation") if isinstance(data, dict) else None
            if isinstance(tr, list) and tr and str(tr[0]).strip():
                return str(tr[0]).strip()
        except Exception:
            pass
        try:
            resp = requests.get(
                "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=zh-CN&dt=t&q=" + quote(str(text), safe=""),
                headers={"User-Agent": self.DEFAULT_UA},
                timeout=3,
            )
            data = resp.json()
            if isinstance(data, list) and data and isinstance(data[0], list):
                full = ""
                for seg in data[0]:
                    if isinstance(seg, list) and seg and seg[0]:
                        full += str(seg[0])
                if full.strip():
                    return full.strip()
        except Exception:
            pass
        return text

    def _parse_items(self, html):
        items = []
        if not html:
            return items
        seen = set()
        blocks = re.split(r'<div class="col item">', html, flags=re.I)[1:]
        for block in blocks:
            hm = re.search(r'href="([^"]+)"', block)
            tm = re.search(r'title="([^"]+)"', block)
            if not hm or not tm:
                continue
            vurl = hm.group(1).strip()
            if vurl.startswith("//"):
                vurl = "https:" + vurl
            elif vurl.startswith("/"):
                vurl = self.host + vurl
            if vurl in seen:
                continue
            pic = ""
            for im in re.finditer(r'(?:src|data-src|data-original)="([^"]+)"', block, re.I):
                cand = im.group(1)
                if "base64" not in cand and ".gif" not in cand and re.search(r"\.(?:jpg|png|webp|jpeg)", cand, re.I):
                    pic = cand
                    break
            if not pic:
                fm = re.search(r'https?://[^"]+\.(?:jpg|png|webp|jpeg)', block, re.I)
                if fm:
                    pic = fm.group(0)
            vals = re.findall(r'<span\s+class="value">([^<]*)</span>', block, re.I)
            dur = vals[2].strip() if len(vals) >= 3 else ""
            title = self._clean(tm.group(1))
            remarks = (self.BRAND + " | " + dur) if dur else self.BRAND
            seen.add(vurl)
            items.append({
                "vod_id": vurl,
                "vod_name": title,
                "vod_pic": self._format_poster(pic),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": self.POSTER_RATIO},
            })
        return items

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.CATEGORIES]
        return {"class": classes}

    def homeVideoContent(self):
        status, doc = self._fetch(self.host + "/", self.host + "/")
        if status != 200:
            return {"list": []}
        return {"list": self._parse_items(doc)}

    def _page_result(self, page, items):
        if items:
            return {"page": page, "pagecount": page + 1, "limit": self.PAGE_SIZE, "total": 999, "list": items}
        return {"page": page, "pagecount": page, "limit": self.PAGE_SIZE, "total": 0, "list": []}

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        category_id = str(tid or "").strip().strip("/") or "hd-porno"
        if page > 1:
            url = self.host + "/categories/" + category_id + "/" + str(page) + "/"
        else:
            url = self.host + "/categories/" + category_id + "/"
        status, doc = self._fetch(url, self.host + "/")
        items = self._parse_items(doc) if status == 200 else []
        if page > 1 and not items:
            alt = self.host + "/categories/" + category_id + "/?from=" + str(page)
            status2, doc2 = self._fetch(alt, self.host + "/")
            if status2 == 200:
                items = self._parse_items(doc2)
        return self._page_result(page, items)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_result(page, [])
        kw = quote(keyword, safe="")
        if page > 1:
            url = self.host + "/search/" + kw + "/" + str(page) + "/"
        else:
            url = self.host + "/search/" + kw + "/"
        status, doc = self._fetch(url, self.host + "/")
        items = self._parse_items(doc) if status == 200 else []
        if page > 1 and not items:
            alt = self.host + "/search/" + kw + "/?from=" + str(page)
            status2, doc2 = self._fetch(alt, self.host + "/")
            if status2 == 200:
                items = self._parse_items(doc2)
        return self._page_result(page, items)

    def _extract_sources(self, doc, target_url):
        qualities = {}
        ld = {}
        lm = re.search(r'<script\s+type="application/ld\+json">(.*?)</script>', doc, re.S)
        if lm and lm.group(1):
            try:
                parsed = json.loads(lm.group(1))
                if isinstance(parsed, dict):
                    ld = parsed
            except Exception:
                ld = {}
        cu = str(ld.get("contentUrl") or "")
        if cu and cu.startswith("http"):
            qualities["480P"] = cu
        for dm in re.finditer(r'href="([^"]+/get_file/[^"]+)"', doc, re.I):
            link = self._absolutize(dm.group(1))
            low = link.lower()
            if "1080p" in low:
                qname = "1080P"
            elif "720p" in low:
                qname = "720P"
            elif "480p" in low:
                qname = "480P"
            elif "360p" in low:
                qname = "360P"
            else:
                qname = "HD"
            qualities[qname] = link
        for km in re.finditer(r"(?:video_url|video_alt_url\d*|file)\s*:\s*['\"]([^'\"]+)['\"]", doc, re.I):
            surl = km.group(1).strip()
            if not surl or "preview" in surl.lower():
                continue
            surl = self._absolutize(surl)
            low = surl.lower()
            if ".mp4" in low or ".m3u8" in low or "get_file" in low:
                if "1080" in low:
                    kq = "1080P"
                elif "720" in low:
                    kq = "720P"
                elif "480" in low:
                    kq = "480P"
                elif "360" in low:
                    kq = "360P"
                else:
                    kq = "标清"
                if kq not in qualities:
                    qualities[kq] = surl
        episodes = []
        for qname in self.QUALITY_ORDER:
            if qname in qualities:
                env = {"url": qualities[qname], "referer": target_url}
                episodes.append((qname, env))
        if not episodes:
            env = {"url": target_url, "referer": self.host + "/", "isWeb": True}
            episodes.append(("网页嗅探", env))
        return ld, episodes

    def _brand_block(self):
        lines = [
            "🦋 SweetPorn官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _episode_name(self, name):
        return str(name).replace("$", "_").replace("#", "_")

    def detailContent(self, ids):
        raw = ""
        if isinstance(ids, (list, tuple)) and ids:
            raw = str(ids[0])
        elif ids:
            raw = str(ids)
        if not raw:
            return {"list": [], "msg": "未找到该影片"}
        if raw.startswith("http"):
            target_url = raw
        else:
            target_url = self.host + "/video/" + raw.strip("/") + "/"
        status, doc = self._fetch(target_url, self.host + "/")
        if status != 200 or not doc:
            return {"list": [], "msg": "未找到该影片"}
        ld, episodes = self._extract_sources(doc, target_url)
        title = str(ld.get("name") or "")
        if not title:
            h1 = re.search(r"<h1[^>]*>([^<]+)</h1>", doc, re.I)
            if h1:
                title = h1.group(1).strip()
        pic = str(ld.get("thumbnailUrl") or "")
        duration = self._parse_duration_iso(str(ld.get("duration") or ""))
        desc = str(ld.get("description") or "")
        poster = self._format_poster(pic)
        related = []
        ridx = doc.find('id="list_videos_related_videos"')
        if ridx >= 0:
            for card in self._parse_items(doc[ridx:]):
                if card["vod_id"] != raw and card["vod_id"] != target_url:
                    related.append(card)
        zh_title = self._translate_ru2zh(title)
        display_title = zh_title if zh_title else title
        vod_name = self._clean(display_title) or raw
        body_lines = []
        if title and display_title != title:
            body_lines.append("原名：" + title)
        if desc:
            body_lines.append(desc)
        else:
            rel_names = [c["vod_name"] for c in related[:6]]
            body_lines.append("标题：" + vod_name)
            body_lines.append("时长：" + (duration if duration else "未知"))
            body_lines.append("片源：" + self.LINE_NAME)
            body_lines.append("相关推荐：" + (" / ".join(rel_names) if rel_names else "无"))
        content = self._brand_block() + "\n" + "\n".join(body_lines)
        remarks = (self.BRAND + " | " + duration) if duration else self.BRAND
        flags = [self.LINE_NAME]
        ep_lines = []
        main_eps = []
        for qname, env in episodes:
            main_eps.append(self._episode_name(qname) + "$" + json.dumps(env, ensure_ascii=False))
        ep_lines.append("#".join(main_eps))
        if related:
            flags.append(self.RELATED_LINE)
            rel_eps = []
            for card in related:
                rel_eps.append(self._episode_name(card["vod_name"]) + "$" + "rel:" + card["vod_id"])
            ep_lines.append("#".join(rel_eps))
        upload = str(ld.get("uploadDate") or "")
        vod = {
            "vod_id": raw,
            "vod_name": vod_name,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_year": upload[:4] if len(upload) >= 4 else "",
            "vod_remarks": remarks,
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_content": content,
            "vod_play_from": "$$$".join(flags),
            "vod_play_url": "$$$".join(ep_lines),
        }
        return {"list": [vod]}

    def _play_from_env(self, env):
        play_url = str(env.get("url") or "")
        referer = str(env.get("referer") or (self.host + "/"))
        if not play_url:
            return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
        headers = {"User-Agent": self.DEFAULT_UA, "Referer": referer, "Accept": "*/*"}
        if env.get("isWeb"):
            return {"parse": 1, "jx": 0, "url": play_url, "header": headers}
        return {"parse": 0, "jx": 0, "url": play_url, "header": headers}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("rel:"):
            target = raw[4:].strip()
            if not target:
                return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
            if not target.startswith("http"):
                target = self.host + "/video/" + target.strip("/") + "/"
            status, doc = self._fetch(target, self.host + "/")
            if status != 200 or not doc:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放地址"}
            _ld, episodes = self._extract_sources(doc, target)
            if not episodes:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放地址"}
            return self._play_from_env(episodes[0][1])
        env = None
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if isinstance(obj, dict):
                if obj.get("notice"):
                    return {"parse": 0, "msg": str(obj["notice"])}
                env = obj
        if env is None:
            if raw.startswith("http"):
                env = {"url": raw, "referer": self.host + "/"}
            else:
                return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
        return self._play_from_env(env)

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Not Found"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250202493&sig=8f8190662a647e0e
