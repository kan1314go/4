# -*- coding: utf-8 -*-
# 浮生影院

import re
import json
import requests
from urllib.parse import quote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://tv.fushengr.cc"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    BRAND = "🦋 蝴蝶影视"
    RELATED_LINE = "相关推荐"
    POSTER_RATIO = 1.78
    PAGE_SIZE = 20
    TIMEOUT = 8

    FALLBACK_LINES = [
        ("🦋 蝴蝶专线01", "https://d32bg2g0w9aqg4.cloudfront.net"),
        ("🦋 蝴蝶专线02", "https://vsdsq.tjacq.com"),
    ]

    CLASSES = [
        ("一手原创", "cate29"),
        ("独家热播", "cate37"),
        ("乱伦之爱", "cate17"),
        ("福利姬", "cate47"),
        ("优选UP", "cate65"),
        ("P站精选", "cate81"),
        ("国产传媒", "cate98"),
        ("日本AV", "cate113"),
        ("性癖", "cate129"),
        ("动漫", "cate138"),
        ("欧美", "cate148"),
        ("劲爆综艺", "cate162"),
    ]

    FILTER_OPTIONS = {
        "cate29": [("全部", ""), ("御姐李老师", "cate31"), ("奶气草莓", "cate32"), ("会喷水的姐姐", "cate33"), ("伊藤诚", "cate34"), ("狠台北", "cate35"), ("公鸡俱乐部", "cate36")],
        "cate37": [("全部", ""), ("颜值女神", "cate39"), ("探花嫖妓", "cate40"), ("绿帽淫妻", "cate41"), ("母狗性奴", "cate42"), ("针孔偷拍", "cate43"), ("野战户外", "cate44"), ("成人综艺", "cate45"), ("网红骚播", "cate46")],
        "cate17": [("全部", ""), ("鬼父操女", "cate19"), ("淫母兽儿", "cate20"), ("嫂子诱惑", "cate21"), ("姐夫小姨子", "cate22"), ("爷孙禁忌", "cate26")],
        "cate65": [("全部", ""), ("菠萝啤beer~", "cate67"), ("网红妹妹", "cate68"), ("香艳职场", "cate69"), ("捅主任", "cate70"), ("双生の恋", "cate71"), ("台湾臀后艾丽", "cate72"), ("粉红兔的诱惑", "cate73"), ("COS美少女", "cate74"), ("女王梨奈", "cate75"), ("性感小猫咪", "cate76"), ("宜家门", "cate77"), ("颜射少女", "cate78"), ("迷奸柚", "cate79"), ("拳交女皇", "cate80")],
        "cate81": [("全部", ""), ("米胡桃", "cate83"), ("Andmlove", "cate84"), ("羞羞兔", "cate85"), ("Roko", "cate86"), ("Yominokuni", "cate87"), ("桃子派", "cate88"), ("下面有根棒棒糖", "cate89"), ("宝贝奶兽", "cate90"), ("BabyYurin", "cate91"), ("优咪Yumi", "cate92"), ("台湾兔兔", "cate93"), ("爱玩熊熊", "cate94"), ("鸡教练", "cate95"), ("樱桃空空", "cate96"), ("Miuzxc", "cate97")],
        "cate98": [("全部", ""), ("精东影业", "cate108")],
        "cate113": [("全部", ""), ("凌辱快感", "cate121")],
        "cate129": [("全部", ""), ("SM调教", "cate131"), ("媚黑骚逼", "cate132"), ("强奸迷奸", "cate133"), ("人妖伪娘", "cate134"), ("百合女同", "cate135"), ("男男之恋", "cate136"), ("偷窥偷拍", "cate137")],
        "cate138": [("全部", ""), ("王者荣耀", "cate140"), ("经典老片", "cate141"), ("禁漫里番", "cate142"), ("巨乳动漫", "cate143"), ("中文字幕", "cate144"), ("魔", "cate145"), ("原神", "cate146"), ("综合", "cate147")],
        "cate162": [("全部", ""), ("性爱自修室", "cate164"), ("突袭女优家", "cate165"), ("淫娃培训营", "cate166"), ("淫欲游戏王", "cate167"), ("情趣K歌房", "cate168"), ("乱伦家庭", "cate169")],
    }

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
        return "浮生影院"

    def isVideoFormat(self, url):
        low = str(url or "").lower()
        return (".m3u8" in low) or (".mp4" in low) or (".flv" in low) or (".mpd" in low)

    def manualVideoCheck(self):
        return False

    def _fetch(self, url, referer=None):
        headers = {
            "User-Agent": self.DEFAULT_UA,
            "Referer": referer or (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(url, headers=headers, timeout=self.TIMEOUT)
            return resp.status_code, resp.text or ""
        except Exception:
            return -1, ""

    def _unescape_html(self, s):
        out = str(s or "")
        out = out.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
        out = out.replace("&quot;", '"')
        out = re.sub(r"&#0?39;", "'", out)
        out = out.replace("&nbsp;", " ")
        out = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), out)
        return out

    def _clean_label(self, s):
        out = self._unescape_html(re.sub(r"<[^>]+>", "", str(s or "")))
        out = re.sub(r"[\r\n\t]+", " ", out)
        out = re.sub(r"\s+", " ", out)
        return out.strip()

    def _abs_url(self, u):
        u = str(u or "").strip()
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return self.host + u
        return u

    def _format_poster(self, raw_pic):
        if not raw_pic:
            return ""
        p = self._abs_url(raw_pic)
        p = re.sub(r"^(https?):/(?!/)", r"\1://", p, flags=re.I)
        if not p.startswith("http"):
            return p
        return p + "@" + "Referer=" + quote(self.host + "/", safe="!*'()") + "&" + "User-Agent=" + quote(self.DEFAULT_UA, safe="!*'()")

    def _format_remarks(self, meta):
        m = self._clean_label(meta or "").replace("$", "").replace("#", "")
        if not m:
            return self.BRAND
        return self.BRAND + " | " + m

    def _parse_cards(self, html):
        items = []
        if not html:
            return items
        seen = set()
        for m in re.finditer(r'(<a\b[^>]*href=["\'][^"\']*?/video/(\d+)/?["\'][^>]*>)([\s\S]*?)</a>', html, re.I):
            vod_id = m.group(2)
            if vod_id in seen:
                continue
            tag = m.group(1)
            inner = m.group(3)
            name = ""
            am = re.search(r'aria-label=["\']([^"\']+)["\']', tag, re.I)
            if am:
                name = am.group(1).strip()
            if not name:
                tm = re.search(r'title=["\']([^"\']+)["\']', tag, re.I)
                if tm:
                    name = tm.group(1).strip()
            if not name:
                gm = re.search(r'<(?:strong|em|h\d+)[^>]*>(.*?)</(?:strong|em|h\d+)>', inner, re.I | re.S)
                if gm:
                    name = gm.group(1).strip()
            if not name:
                alm = re.search(r'alt=["\']([^"\']+)["\']', inner, re.I)
                if alm:
                    name = alm.group(1).strip()
            if not name:
                continue
            name = self._clean_label(name)
            pic = ""
            dm = re.search(r'data-src=["\']([^"\']+)["\']', inner, re.I)
            if dm:
                pic = dm.group(1).strip()
            else:
                sm = re.search(r'src=["\']([^"\']+)["\']', inner, re.I)
                if sm and "loading.gif" not in sm.group(1):
                    pic = sm.group(1).strip()
            dur = ""
            durm = re.search(r'class=["\'][^"\']*duration[^"\']*["\'][^>]*>(.*?)</span>', inner, re.I | re.S)
            if durm:
                dur = self._clean_label(durm.group(1))
            seen.add(vod_id)
            items.append({
                "vod_id": vod_id,
                "vod_name": name,
                "vod_pic": self._format_poster(pic),
                "vod_remarks": self._format_remarks(dur),
                "style": {"type": "rect", "ratio": self.POSTER_RATIO},
            })
        return items

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": name} for name, cid in self.CLASSES]
        result = {"class": classes}
        if filter:
            filters = {}
            for _name, cid in self.CLASSES:
                opts = self.FILTER_OPTIONS.get(cid) or []
                if not opts:
                    continue
                filters[cid] = [{
                    "key": "sub_cat",
                    "name": "细分子频道",
                    "init": "",
                    "value": [{"n": n, "v": v} for n, v in opts],
                }]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        status, doc = self._fetch(self.host + "/group-category/" + self.CLASSES[0][1] + "/")
        if not doc:
            return {"list": []}
        return {"list": self._parse_cards(doc)}

    def _page_result(self, page, items, limit):
        if items:
            return {"page": page, "pagecount": page + 1, "limit": limit, "total": 999, "list": items}
        return {"page": page, "pagecount": page, "limit": limit, "total": 0, "list": []}

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
        category_id = str(tid or "").strip() or self.CLASSES[0][1]
        sub = ""
        if isinstance(extend, dict):
            sub = str(extend.get("sub_cat", "") or "").strip()
        if sub:
            path = "/category/" + sub + "/" if page <= 1 else "/category/" + sub + "/" + str(page) + "/"
        else:
            path = "/group-category/" + category_id + "/" if page <= 1 else "/group-category/" + category_id + "/page/" + str(page) + "/"
        status, doc = self._fetch(self.host + path)
        items = self._parse_cards(doc)
        limit = len(items) if items else self.PAGE_SIZE
        return self._page_result(page, items, limit)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_result(page, [], self.PAGE_SIZE)
        kw = quote(keyword, safe="!*'()")
        path = "/search/" + kw + "/" if page <= 1 else "/search/" + kw + "/" + str(page) + "/"
        status, doc = self._fetch(self.host + path)
        items = self._parse_cards(doc)
        return self._page_result(page, items, self.PAGE_SIZE)

    def _brand_block(self):
        lines = [
            "🦋 浮生影院官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _episode_name(self, name):
        return str(name).replace("$", "_").replace("#", "_")

    def _extract_detail(self, doc, vid):
        title = "超清视频"
        tm = re.search(r"<title>(.*?)</title>", doc, re.I | re.S)
        if tm:
            cand = self._unescape_html(tm.group(1).split("-")[0].strip())
            if cand:
                title = cand
        raw_path = ""
        vod_pic = ""
        pdm = re.search(r"window\.__ARCHIVE_PLAYER__\s*=\s*(\{[\s\S]*?\});", doc)
        if pdm:
            try:
                info = json.loads(pdm.group(1))
            except Exception:
                info = None
            if isinstance(info, dict):
                raw_path = str(info.get("rawPath") or "").replace("\\/", "/")
                vod_pic = str(info.get("posterImg") or "").replace("\\/", "/")
        if not raw_path:
            dm = re.search(r"""["'](/video/[^"']+?\.m3u8)["']""", doc)
            if dm:
                raw_path = dm.group(1)
        candidates = []
        clm = re.search(r"var\s+cdn_lines\s*=\s*(['\"][\s\S]*?['\"]);", doc)
        if clm:
            try:
                raw_json = clm.group(1).strip()
                if len(raw_json) >= 2 and raw_json[0] in "'\"" and raw_json[-1] == raw_json[0]:
                    raw_json = raw_json[1:-1]
                raw_json = raw_json.replace("\\/", "/").replace('\\"', '"').replace("\\'", "'")
                parsed = json.loads(raw_json)
                if isinstance(parsed, str):
                    parsed = json.loads(parsed)
                if isinstance(parsed, list):
                    for item in parsed:
                        if not isinstance(item, dict):
                            continue
                        line_url = str(item.get("cdnLine") or "").replace("\\/", "").rstrip("/")
                        line_name = str(item.get("lineName") or "专线")
                        if line_url and (line_name, line_url) not in candidates:
                            candidates.append((line_name, line_url))
            except Exception:
                candidates = candidates
        if not candidates:
            candidates = list(self.FALLBACK_LINES)
        clean_path = ("/" + raw_path.lstrip("/")) if raw_path else ""
        lines = []
        for line_name, cdn_base in candidates:
            name = line_name if "🦋" in line_name else ("🦋 " + line_name)
            full = (cdn_base.rstrip("/") + clean_path) if clean_path else (self.host + "/video/" + vid + "/")
            full = re.sub(r"^(https?):/(?!/)", r"\1://", full, flags=re.I)
            env = {"directUrl": full} if clean_path else {"pageUrl": full}
            lines.append((name, env))
        related = []
        ridx = doc.find("相关视频")
        if ridx >= 0:
            region = doc[ridx:]
            end = region.find("</aside>")
            if end > 0:
                region = region[:end]
            for card in self._parse_cards(region):
                if card["vod_id"] != vid:
                    related.append(card)
        return title, vod_pic, lines, related

    def detailContent(self, ids):
        raw = ""
        if isinstance(ids, (list, tuple)) and ids:
            raw = str(ids[0])
        elif ids:
            raw = str(ids)
        if not raw:
            return {"list": [], "msg": "未找到该影片"}
        idm = re.search(r"\d+", raw)
        vid = idm.group(0) if idm else raw
        status, doc = self._fetch(self.host + "/video/" + vid + "/")
        if status != 200 or not doc:
            return {"list": [], "msg": "未找到该影片"}
        title, vod_pic, lines, related = self._extract_detail(doc, vid)
        poster = self._format_poster(vod_pic)
        flags = []
        ep_lines = []
        for line_name, env in lines:
            flags.append(line_name)
            ep = self._episode_name("超清正片") + "$" + json.dumps(env, ensure_ascii=False)
            ep_lines.append(ep)
        if related:
            flags.append(self.RELATED_LINE)
            rel_eps = []
            for card in related:
                rel_eps.append(self._episode_name(card["vod_name"]) + "$" + "rel:" + card["vod_id"])
            ep_lines.append("#".join(rel_eps))
        vod = {
            "vod_id": raw,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_remarks": self.BRAND + " | 正片直链",
            "vod_actor": "🦋 蝴蝶影视官方交流群: @tvshare23,🦋 蝴蝶专线",
            "vod_content": self._brand_block() + "\n" + "【影片标题】" + title,
            "vod_play_from": "$$$".join(flags),
            "vod_play_url": "$$$".join(ep_lines),
        }
        return {"list": [vod]}

    def _resolve_env(self, env):
        headers = {"User-Agent": self.DEFAULT_UA, "Referer": self.host + "/", "Accept": "*/*"}
        direct = str(env.get("directUrl") or "")
        if direct:
            play_url = direct
            if ".m3u8" not in play_url and ".mp4" not in play_url:
                play_url = play_url + ("&format=.m3u8" if "?" in play_url else "?format=.m3u8")
            return {"parse": 0, "jx": 0, "url": play_url, "header": headers}
        if env.get("pageUrl"):
            return {"parse": 0, "jx": 0, "url": "", "msg": "No direct stream for this item"}
        return {"parse": 0, "jx": 0, "url": "", "msg": "Nothing to resolve"}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("rel:"):
            target = raw[4:].strip()
            idm = re.search(r"\d+", target)
            vid = idm.group(0) if idm else target
            if not vid:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放地址"}
            status, doc = self._fetch(self.host + "/video/" + vid + "/")
            if status != 200 or not doc:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放地址"}
            _title, _pic, lines, _related = self._extract_detail(doc, vid)
            if not lines:
                return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放地址"}
            return self._resolve_env(lines[0][1])
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if isinstance(obj, dict):
                if obj.get("notice"):
                    return {"parse": 0, "msg": str(obj["notice"])}
                return self._resolve_env(obj)
        return {"parse": 0, "jx": 0, "url": "", "msg": "Nothing to resolve"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Not Found"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249571913&sig=d12e01d35dbb3967
