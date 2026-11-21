# -*- coding: utf-8 -*-
# 疯猫AV - com.butterfly.fmav
import re
import json
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

SITE_NAME = "疯猫AV"
BRAND_NAME = "蝴蝶影视"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
DEFAULT_HOST = "https://n-20261020.fmav786.icu"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
PAGE_SIZE = 16
PIC_RATIO = 1.78

CLASSES = [
    ("route_actor_hot", "🔥本周热播"),
    ("route_role_10min", "⏱️10分钟以上"),
    ("x4B4", "91加精视频"),
    ("S4B4", "91最新视频"),
    ("F4B4", "快播系列"),
    ("Z4B4", "国产自拍"),
    ("94B4", "网曝吃瓜"),
    ("b4B4", "AI短剧"),
    ("W4B4", "日韩系列"),
    ("w4B4", "探花约炮"),
    ("c4B4", "主播诱惑"),
    ("54B4", "乱伦侵犯"),
    ("H4B4", "传媒剧情"),
    ("E4B4", "抖音快手"),
    ("84B4", "伦理三级"),
    ("R4B4", "动漫动画"),
]

CARD_RE = re.compile(r'class="[^"]*resent-grid[^"]*"[\s\S]*?</h5>', re.I)
LINK_RE = re.compile(r'href=["\'](/js/[^"\']+\.html)["\']', re.I)
PIC_RE = re.compile(r'(?:data-original|src)=["\']([^"\']+)["\']', re.I)
CARD_TITLE_RE = re.compile(r'class="title"[^>]*>([\s\S]*?)</a>', re.I)
ALT_RE = re.compile(r'alt=["\']([^"\']+)["\']', re.I)
DUR_RE = re.compile(r'class="duration-time"[^>]*>([\s\S]*?)</p>', re.I)
TITLE_TAG_RE = re.compile(r"<title>(.*?)</title>", re.I)
TITLE_CUT_RE = re.compile(r"_(?:影片介绍|疯猫av|免费在线播放).*$", re.I)
BF_RE = re.compile(r'href=["\'](/bf/[^"\']+\.html)["\']', re.I)
CFG_RE = re.compile(r"var\s+player_aaaa\s*=\s*(\{[\s\S]*?\});")
CFG_URL_RE = re.compile(r'"url"\s*:\s*"([^"]+)"')
CFG_NOTE_RE = re.compile(r'"note"\s*:\s*"([^"]*)"')
CFG_FROM_RE = re.compile(r'"from"\s*:\s*"([^"]*)"')
M3U8_RE = re.compile(r'https?://[^\s"\'\$<>]+\.m3u8[^\s"\'\$<>!]*', re.I)
VAR_URL_RE = re.compile(r'(?:var\s+plyerurl|var\s+url|video_url)\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']', re.I)


def strip_tags(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", str(text))).strip()


def clean_label(text):
    if not text:
        return ""
    t = re.sub(r"[\$#\r\n\t]+", " ", str(text))
    return re.sub(r"\s+", " ", t).strip()


def format_remarks(meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (BRAND_NAME, clean_meta)
    return BRAND_NAME


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST

    def getName(self):
        return SITE_NAME

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "").strip()
        elif extend:
            text = str(extend).strip()
            if text.startswith("{"):
                try:
                    obj = json.loads(text)
                    if isinstance(obj, dict):
                        custom = str(obj.get("host") or "").strip()
                except Exception:
                    custom = ""
            else:
                custom = text
        if custom.startswith("http"):
            self.host = custom.rstrip("/")

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- network ----------

    def _abs_url(self, url):
        target = str(url or "")
        if target.startswith("//"):
            target = "https:" + target
        elif target.startswith("/"):
            target = self.host + target
        return target

    def _fetch(self, url, referer=None, form=None):
        target = self._abs_url(url)
        headers = {
            "User-Agent": UA,
            "Referer": referer if referer else (self.host + "/"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            if form is not None:
                headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
                resp = requests.post(target, data=form, headers=headers, timeout=8)
            else:
                resp = requests.get(target, headers=headers, timeout=8)
            if resp is not None and isinstance(resp.text, str):
                return resp.text
        except Exception:
            return ""
        return ""

    # ---------- parsing ----------

    def _format_poster(self, raw_url):
        if not raw_url:
            return ""
        target = str(raw_url).strip()
        if target.startswith("//"):
            target = "https:" + target
        elif target.startswith("/"):
            target = self.host + target
        return target + "@Referer=" + quote(self.host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def _build_cate_path(self, tid, page):
        if tid == "route_actor_hot":
            return "/actor/p" + str(page) + ".html?a=hot"
        if tid == "route_role_10min":
            return "/role/p" + str(page) + ".html?a=10min"
        if tid.startswith("route_"):
            return "/" + tid[len("route_"):]
        if page == 1:
            return "/fly/" + tid + "_p.html"
        return "/fly/" + tid + "_p" + str(page) + ".html"

    def _card_title(self, chunk):
        m = CARD_TITLE_RE.search(chunk)
        title = strip_tags(m.group(1)) if m else ""
        if not title:
            am = ALT_RE.search(chunk)
            if am:
                title = am.group(1).strip()
        return title

    def _parse_cards(self, html_text):
        items = []
        if not html_text:
            return items
        seen = {}
        for m in CARD_RE.finditer(html_text):
            chunk = m.group(0)
            lm = LINK_RE.search(chunk)
            if not lm:
                continue
            v_url = lm.group(1).strip()
            if v_url in seen:
                continue
            pm = PIC_RE.search(chunk)
            pic = pm.group(1).strip() if pm else ""
            title = self._card_title(chunk)
            if not title:
                title = "精彩视频"
            dm = DUR_RE.search(chunk)
            duration = strip_tags(dm.group(1)) if dm else ""
            if v_url and pic:
                seen[v_url] = True
                poster = self._format_poster(pic)
                vod_id = v_url + "@@" + quote(title, safe="") + "@@" + quote(poster, safe="")
                items.append({
                    "vod_id": vod_id,
                    "vod_name": title,
                    "vod_pic": poster,
                    "vod_remarks": format_remarks(duration),
                    "style": {"type": "rect", "ratio": PIC_RATIO},
                })
        return items

    def _page_form(self, items, page):
        if items:
            return {
                "list": items,
                "page": page,
                "pagecount": page + 1,
                "limit": PAGE_SIZE,
                "total": (page + 1) * PAGE_SIZE,
            }
        return {"list": [], "page": page, "pagecount": page, "limit": PAGE_SIZE, "total": 0}

    def _to_page(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    # ---------- entries ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CLASSES]
        return {"class": classes}

    def homeVideoContent(self):
        path = self._build_cate_path(CLASSES[0][0], 1)
        html_text = self._fetch(path, referer=self.host + "/")
        return {"list": self._parse_cards(html_text)}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._to_page(pg)
        path = self._build_cate_path(str(tid), page)
        html_text = self._fetch(path, referer=self.host + "/")
        return self._page_form(self._parse_cards(html_text), page)

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_form([], page)
        if page > 1:
            return self._page_form([], page)
        html_text = self._fetch("/ss/key__p.html", referer=self.host + "/", form={"wd": keyword})
        return self._page_form(self._parse_cards(html_text), page)

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return lines

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        raw = str(ids[0] or "")
        parts = raw.split("@@")
        path = parts[0]
        ref_title = unquote(parts[1]) if len(parts) > 1 else ""
        ref_pic = unquote(parts[2]) if len(parts) > 2 else ""

        if path.startswith("http"):
            detail_url = path
        else:
            detail_url = self.host + ("" if path.startswith("/") else "/") + path

        d_html = self._fetch(detail_url, referer=self.host + "/")

        main_title = ref_title if ref_title else "蝴蝶专线高清视频"
        if d_html:
            tm = TITLE_TAG_RE.search(d_html)
            if tm:
                raw_title = strip_tags(tm.group(1))
                main_title = TITLE_CUT_RE.sub("", raw_title).strip()

        bf_m = BF_RE.search(d_html) if d_html else None
        target_play_page = bf_m.group(1).strip() if bf_m else detail_url
        if target_play_page.startswith("http"):
            main_play_target = target_play_page
        else:
            main_play_target = self.host + ("" if target_play_page.startswith("/") else "/") + target_play_page

        episodes = [{"name": "超清正片", "value": main_play_target}]
        rec_titles = []

        seen = {path: True, detail_url: True, target_play_page: True, main_play_target: True}
        rec_idx = 1
        if d_html:
            for m in CARD_RE.finditer(d_html):
                chunk = m.group(0)
                vm = LINK_RE.search(chunk)
                if not vm:
                    continue
                rec_href = vm.group(1).strip()
                if rec_href in seen:
                    continue
                seen[rec_href] = True
                rec_title = self._card_title(chunk)
                if not rec_title:
                    continue
                rec_titles.append(rec_title)
                clean_t = clean_label(rec_title)
                display_t = (clean_t[:20] + "...") if len(clean_t) > 20 else clean_t
                label = (("0" + str(rec_idx)) if rec_idx < 10 else str(rec_idx)) + "·" + display_t
                if rec_href.startswith("http"):
                    rec_full_url = rec_href
                else:
                    rec_full_url = self.host + ("" if rec_href.startswith("/") else "/") + rec_href
                episodes.append({"name": label, "value": rec_full_url})
                rec_idx += 1
                if rec_idx > 30:
                    break

        content_lines = self._brand_block()
        content_lines.append("标题：" + main_title)
        content_lines.append("分类：")
        content_lines.append("片源：" + LINE_NAME)
        content_lines.append("编号：" + path)
        if rec_titles:
            content_lines.append("相关推荐：" + "、".join(rec_titles[:6]))

        play_url = "#".join(ep["name"] + "$" + ep["value"] for ep in episodes)
        vod = {
            "vod_id": path,
            "vod_name": main_title,
            "vod_pic": ref_pic,
            "vod_bg": ref_pic,
            "vod_background": ref_pic,
            "vod_banner": ref_pic,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": format_remarks("全" + str(len(episodes)) + "部连播"),
            "vod_content": "\n".join(content_lines),
            "vod_play_from": LINE_NAME,
            "vod_play_url": play_url,
        }
        return {"list": [vod]}

    # ---------- resolve ----------

    def _resolve_real_stream(self, bf_page_url):
        p_html = self._fetch(bf_page_url, referer=self.host + "/")
        if not p_html:
            return ""
        cfg_m = CFG_RE.search(p_html)
        if not cfg_m:
            return ""
        raw_cfg = cfg_m.group(1).replace("\\/", "/")
        url_m = CFG_URL_RE.search(raw_cfg)
        note_m = CFG_NOTE_RE.search(raw_cfg)
        from_m = CFG_FROM_RE.search(raw_cfg)
        target_stream_url = url_m.group(1) if url_m else ""
        play_note = note_m.group(1) if note_m else ""
        play_from = from_m.group(1) if from_m else "ck91player"
        endpoint = "/ck91.php" if "ck91" in play_from else "/ck.php"
        api_url = endpoint + "?url=" + quote(target_stream_url, safe="") + "&key=" + quote(play_note, safe="")
        api_html = self._fetch(api_url, referer=bf_page_url)
        if not api_html:
            return ""
        m3u8_list = M3U8_RE.findall(api_html)
        if m3u8_list:
            return m3u8_list[0].replace("\\u002F", "/").replace("\\/", "/")
        var_m = VAR_URL_RE.search(api_html)
        if var_m:
            return var_m.group(1).replace("\\u002F", "/").replace("\\/", "/")
        return ""

    def playerContent(self, flag, id, vipFlags):
        target_page = str(id or "").strip()
        actual_bf = target_page
        if "/js/" in target_page:
            d_html = self._fetch(target_page, referer=self.host + "/")
            if d_html:
                bf_m = BF_RE.search(d_html)
                if bf_m:
                    actual_bf = bf_m.group(1).strip()
                    if not actual_bf.startswith("http"):
                        actual_bf = self.host + ("" if actual_bf.startswith("/") else "/") + actual_bf
        real_stream = self._resolve_real_stream(actual_bf)
        if not real_stream:
            real_stream = actual_bf
        headers = {"User-Agent": UA, "Referer": self.host + "/"}
        lower = real_stream.lower()
        is_stream = (".m3u8" in lower) or (".mp4" in lower) or (".ts" in lower)
        if is_stream:
            return {"parse": 0, "url": real_stream, "header": headers}
        return {"parse": 1, "url": real_stream, "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249569894&sig=2a6c4db807ae6283
