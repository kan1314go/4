# -*- coding: utf-8 -*-
# 稀饭动漫 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.xifanacg)
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://next.xifanacg.com"
DEFAULT_API = "https://api.xifanacg.com"
DEFAULT_IMG_PROXY = "https://xifandongman.yishengheqiu7679.workers.dev/?url="
SB_KEY = "sb_publishable_OBIVAWACIX6lPXrO98_z24_HcsmalkA"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND_NAME = "稀饭动漫"
PAGE_SIZE = 30
PER_PAGE = 24
PIC_RATIO = 0.67

CATEGORIES = [
    ("1", "连载新番"),
    ("2", "完结旧番"),
    ("3", "剧场版"),
    ("4", "美漫"),
    ("all", "全部番剧"),
    ("hot", "人气榜单"),
]

FORMAT_OPTIONS = [
    ("", "全部"),
    ("tv", "TV 动画"),
    ("movie", "剧场版"),
    ("ova", "OVA"),
    ("oad", "OAD"),
    ("web", "Web 动画"),
    ("other", "其他"),
]

TAG_NAMES = [
    "漫画改", "小说改", "奇幻", "战斗", "原创", "恋爱", "校园", "日常",
    "百合", "后宫", "科幻", "游戏改", "悬疑", "冒险", "穿越", "音乐",
    "运动", "机战", "喜剧", "少年向", "推理", "少女向", "职场", "美食", "青年向",
]

SORT_OPTIONS = [
    ("", "默认"),
    ("release_date", "最新"),
    ("view_count", "热度"),
    ("bangumi_score", "评分"),
]

CARD_RE = re.compile(r'<a[^>]+aria-label="([^"]*)"[^>]*?href="/anime/(\d+)"[^>]*>([\s\S]*?)</a>', re.I)
CARD_IMG_RE = re.compile(r'<img[^>]*?src="([^"]+)"', re.I)
CARD_RM1_RE = re.compile(r'<div class="absolute right-0 bottom-0[^"]*"[^>]*>([^<]+)</div>', re.I)
CARD_RM2_RE = re.compile(r'text-xs text-ink-muted">([^<]+)', re.I)
TITLE_TAG_RE = re.compile(r"<title>([^<]*)</title>", re.I)
DETAIL_IMG_RE = re.compile(r'<img[^>]*?src="(https://img2\.[^"]+)"', re.I)
REC_CARD_RE = re.compile(r'"href":"/anime/(\d+)","prefetch":false,"aria-label":"([^"]*)"')
R800_RE = re.compile(r"/r/800/", re.I)
WS_RUN_RE = re.compile(r"\s+")

_EXC = object()


def _filter_rows():
    tag_options = [("", "全部")]
    for t in TAG_NAMES:
        tag_options.append((t, t))
    year_options = [("", "全部")]
    for y in range(2026, 2004, -1):
        year_options.append((str(y), str(y)))
    rows = []
    for key, name, options in (
        ("format", "类型", FORMAT_OPTIONS),
        ("tag", "题材", tag_options),
        ("year", "年份", year_options),
        ("sort", "排序", SORT_OPTIONS),
    ):
        rows.append({
            "key": key,
            "name": name,
            "init": "",
            "value": [{"n": n, "v": v} for v, n in options],
        })
    return rows


def _format_status(tail):
    if tail:
        return "蝴蝶影视 | " + tail
    return "蝴蝶影视"


def _clean_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST
        self.api = DEFAULT_API
        self.img_proxy_raw = None

    def getName(self):
        return BRAND_NAME

    def init(self, extend=""):
        ext = extend
        data = None
        if isinstance(ext, dict):
            data = ext
        elif isinstance(ext, str) and ext.strip():
            text = ext.strip()
            if text.startswith("http"):
                self.host = text.rstrip("/")
            else:
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        data = parsed
                except Exception:
                    data = None
        if isinstance(data, dict):
            host = str(data.get("host") or "").strip()
            if host.startswith("http"):
                self.host = host.rstrip("/")
            api = str(data.get("api") or "").strip()
            if api.startswith("http"):
                self.api = api.rstrip("/")
            if data.get("imgProxy") is not None:
                self.img_proxy_raw = str(data.get("imgProxy"))

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- fetch ----------

    def _html_headers(self):
        return {
            "User-Agent": UA,
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": self.host + "/",
        }

    def _api_headers(self):
        return {
            "apikey": SB_KEY,
            "Authorization": "Bearer " + SB_KEY,
            "Content-Type": "application/json",
            "Origin": self.host,
            "Referer": self.host + "/",
            "User-Agent": UA,
        }

    def _fetch_once(self, url):
        try:
            resp = requests.get(url, headers=self._html_headers(), timeout=8)
            if resp is not None and 200 <= resp.status_code < 300 and resp.text:
                return resp.text
            return ""
        except Exception:
            return None

    def _fetch_text(self, url):
        target = url
        if target.startswith("//"):
            target = "https:" + target
        elif target.startswith("/"):
            target = self.host + target
        body = self._fetch_once(target)
        if body is None and target.startswith("https://"):
            retry = self._fetch_once("http://" + target[8:])
            return retry if retry else ""
        return body if body else ""

    def _post_once(self, url, body):
        try:
            resp = requests.post(url, json=body, headers=self._api_headers(), timeout=8)
            if resp is not None and 200 <= resp.status_code < 300:
                try:
                    return resp.json()
                except Exception:
                    return None
            return None
        except Exception:
            return _EXC

    def _post_json(self, url, body):
        data = self._post_once(url, body)
        if data is _EXC and url.startswith("https://"):
            data = self._post_once("http://" + url[8:], body)
        if data is _EXC:
            return None
        return data

    def _rpc(self, name, body):
        data = self._post_json(self.api + "/rest/v1/rpc/" + name, body)
        if isinstance(data, list):
            return data
        return None

    def _playback_data(self, ep_id):
        body = {"action": "fallback", "episode_id": int(ep_id)}
        data = self._post_json(self.api + "/functions/v1/issue-web-playback", body)
        if isinstance(data, dict) and data.get("ok"):
            return data
        return None

    # ---------- poster ----------

    def _normalize_proxy_base(self, raw_prefix):
        p = str(raw_prefix or "").strip()
        if not p:
            return ""
        if p.lower() in ("direct", "off", "none"):
            return "DIRECT"
        if "?url=" in p or "&url=" in p:
            return p
        if "?" in p:
            return (p + "url=") if p.endswith("&") else (p + "&url=")
        return p.rstrip("/") + "/?url="

    def _img_proxy_prefix(self):
        if self.img_proxy_raw is None:
            return DEFAULT_IMG_PROXY
        raw_val = str(self.img_proxy_raw).strip()
        if not raw_val:
            return DEFAULT_IMG_PROXY
        normalized = self._normalize_proxy_base(raw_val)
        if normalized == "DIRECT":
            return ""
        return normalized

    def _clean_img_url(self, raw_url):
        if not raw_url:
            return ""
        raw = str(raw_url).strip().replace("&amp;", "&")
        if not raw:
            return ""
        if raw.startswith("//"):
            raw = "https:" + raw
        elif raw.startswith("/"):
            raw = self.host + raw
        elif not raw.startswith("http"):
            raw = "https://" + raw
        raw = R800_RE.sub("/r/400/", raw)
        prefix = self._img_proxy_prefix()
        if not prefix:
            return raw
        if raw.startswith(prefix) or "workers.dev/?url=" in raw:
            return raw
        return prefix + quote(raw, safe="")

    # ---------- cards ----------

    def _row_tail(self, it):
        try:
            cur = int(it.get("current_episodes") or 0)
        except Exception:
            cur = 0
        try:
            tot = int(it.get("total_episodes") or 0)
        except Exception:
            tot = 0
        if it.get("is_finished") and tot > 0:
            return "全 " + str(tot) + " 集"
        if cur > 0 and tot > 0:
            return "更新至 " + str(cur) + "/" + str(tot)
        if cur > 0:
            return "更新至 " + str(cur)
        if it.get("release_year"):
            return str(it.get("release_year"))
        return ""

    def _card_vod(self, vid, title, pic, remarks):
        return {
            "vod_id": vid + "@@" + quote(title, safe=""),
            "vod_name": title,
            "vod_pic": pic,
            "vod_remarks": remarks,
            "style": {"type": "rect", "ratio": PIC_RATIO},
        }

    def _map_rpc_rows(self, rows):
        out = []
        if not isinstance(rows, list):
            return out
        seen = set()
        for it in rows:
            if not isinstance(it, dict):
                continue
            vid = str(it.get("id")).strip() if it.get("id") is not None else ""
            title = str(it.get("title")).strip() if it.get("title") else ""
            if not vid or not title or vid in seen:
                continue
            seen.add(vid)
            pic = self._clean_img_url(it.get("cover_url"))
            out.append(self._card_vod(vid, title, pic, _format_status(self._row_tail(it))))
        return out

    def _parse_html_cards(self, html):
        out = []
        if not html:
            return out
        seen = set()
        for m in CARD_RE.finditer(html):
            title = (m.group(1) or "").strip()
            vid = (m.group(2) or "").strip()
            inner = m.group(3) or ""
            if not vid or not title or vid in seen:
                continue
            seen.add(vid)
            pic = ""
            m_pic = CARD_IMG_RE.search(inner)
            if m_pic and m_pic.group(1):
                pic = self._clean_img_url(m_pic.group(1))
            remark = ""
            m_rm = CARD_RM1_RE.search(inner)
            if m_rm and m_rm.group(1):
                remark = m_rm.group(1).strip()
            else:
                m_sb = CARD_RM2_RE.search(inner)
                if m_sb and m_sb.group(1):
                    remark = m_sb.group(1).strip()
            out.append(self._card_vod(vid, title, pic, _format_status(remark)))
        return out

    def _page_form(self, items, page):
        if items:
            return {
                "list": items,
                "page": page,
                "pagecount": page + 1,
                "limit": PAGE_SIZE,
                "total": (page + 1) * PAGE_SIZE,
            }
        return {
            "list": [],
            "page": page,
            "pagecount": page,
            "limit": PAGE_SIZE,
            "total": page * PAGE_SIZE,
        }

    # ---------- home / category / search ----------

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        result = {"class": classes}
        if filter:
            rows = _filter_rows()
            filters = {}
            for cid, _cname in CATEGORIES:
                filters[cid] = rows
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        rows = self._rpc("search_animes", {
            "search_term": "",
            "page_number": 1,
            "items_per_page": 30,
            "sort_by": "release_date",
            "sort_order": "desc",
        })
        items = self._map_rpc_rows(rows)
        if not items:
            html = self._fetch_text(self.host + "/")
            items = self._parse_html_cards(html)[:30]
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        cid = str(tid or "").strip("/")
        if not cid:
            cid = "1"
        body = {
            "search_term": "",
            "page_number": page,
            "items_per_page": PER_PAGE,
        }
        if cid.isdigit():
            body["filter_type_id"] = int(cid)
        if cid == "hot":
            body["sort_by"] = "view_count"
            body["sort_order"] = "desc"
        ext = extend if isinstance(extend, dict) else {}
        fmt = str(ext.get("format") or "").strip()
        tag = str(ext.get("tag") or "").strip()
        year = str(ext.get("year") or "").strip()
        sort = str(ext.get("sort") or "").strip()
        if fmt:
            body["filter_format"] = fmt
        if tag:
            body["filter_meta_tags"] = [tag]
        if year.isdigit():
            body["filter_release_year"] = int(year)
        if sort:
            body["sort_by"] = sort
            body["sort_order"] = "desc"
        rows = self._rpc("search_animes", body)
        items = self._map_rpc_rows(rows)
        return self._page_form(items, page)

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_form([], page)
        rows = self._rpc("search_animes", {
            "search_term": keyword,
            "page_number": page,
            "items_per_page": PER_PAGE,
        })
        items = self._map_rpc_rows(rows)
        return self._page_form(items, page)

    # ---------- flight data ----------

    def _extract_flight_text(self, html):
        if not html:
            return ""
        chunks = []
        marker = "self.__next_f.push([1,"
        pos = 0
        total = len(html)
        while pos < total:
            start = html.find(marker, pos)
            if start < 0:
                break
            q = start + len(marker)
            while q < total and html[q] in " \t\r\n":
                q += 1
            if q >= total or html[q] != '"':
                pos = q + 1
                continue
            i = q + 1
            escaped = False
            end = -1
            while i < total:
                ch = html[i]
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    end = i
                    break
                i += 1
            if end > q:
                try:
                    decoded = json.loads(html[q:end + 1])
                    if isinstance(decoded, str):
                        chunks.append(decoded)
                except Exception:
                    pass
                pos = end + 1
            else:
                break
        return "".join(chunks)

    def _extract_json_after_key(self, text, key):
        if not text:
            return None
        idx = text.find(key)
        if idx < 0:
            return None
        start = idx + len(key)
        total = len(text)
        while start < total and text[start] in " \t\r\n":
            start += 1
        if start >= total:
            return None
        open_char = text[start]
        if open_char not in "{[":
            return None
        close_char = "}" if open_char == "{" else "]"
        depth = 0
        in_str = False
        escaped = False
        for i in range(start, total):
            ch = text[i]
            if in_str:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == open_char:
                depth += 1
            elif ch == close_char:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        return None
        return None

    def _extract_recommendations(self, fly, self_vid):
        out = []
        if not fly:
            return out
        idx = fly.find("相关推荐")
        if idx < 0:
            return out
        seg = fly[idx:idx + 150000]
        seen = set()
        for m in REC_CARD_RE.finditer(seg):
            rid = (m.group(1) or "").strip()
            rtitle = (m.group(2) or "").strip()
            if not rid or not rtitle or rid in seen or rid == self_vid:
                continue
            seen.add(rid)
            out.append((rid, rtitle))
            if len(out) >= 12:
                break
        return out

    # ---------- detail ----------

    def _brand_block(self):
        lines = [
            "🦋 " + BRAND_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _build_sources(self, raw_sources, format_str, vid):
        lines = []
        seen_pairs = set()
        if not isinstance(raw_sources, list):
            return lines
        for s_idx, src in enumerate(raw_sources):
            if not isinstance(src, dict):
                continue
            if src.get("id") is not None:
                sid = str(src.get("id")).strip()
            else:
                sid = str(s_idx + 1)
            sname = str(src.get("name")).strip() if src.get("name") else ("线路" + sid)
            display_name = "🦋 " + sname
            raw_eps = src.get("episodes") if isinstance(src.get("episodes"), list) else []
            ep_list = []
            for e_idx, ep in enumerate(raw_eps):
                if not isinstance(ep, dict) or not ep.get("id"):
                    continue
                eid = str(ep.get("id")).strip()
                pair_key = eid + "_" + sid
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)
                try:
                    num = int(ep.get("episode_number") or 0)
                except Exception:
                    num = 0
                ep_title = str(ep.get("title")).strip() if ep.get("title") else ""
                if num > 0 and format_str == "movie":
                    label = "正片"
                elif num > 0:
                    label = ("第0" + str(num) + "集") if num < 10 else ("第" + str(num) + "集")
                elif ep_title:
                    label = ep_title
                else:
                    label = "EP" + eid
                ep_list.append({
                    "name": _clean_ep_name(label),
                    "value": json.dumps({"episodeId": eid, "sourceId": sid, "vodId": vid}, ensure_ascii=False),
                    "sort": num if num > 0 else (e_idx + 10000),
                })
            ep_list.sort(key=lambda x: x["sort"])
            if ep_list:
                lines.append((display_name, ep_list))
        return lines

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        parts = raw.split("@@")
        vid = parts[0].strip("/") if parts else ""
        carried_title = unquote(parts[1]) if len(parts) > 1 else ""

        if not vid.isdigit():
            vod = {
                "vod_id": raw,
                "vod_name": carried_title if carried_title else "未知番剧",
                "vod_pic": "",
                "vod_bg": "",
                "vod_background": "",
                "vod_banner": "",
                "vod_actor": BRAND_ACTOR,
                "vod_director": BRAND_DIRECTOR,
                "vod_remarks": _format_status(""),
                "vod_content": self._brand_block() + "\n【番剧简介】无效的番剧 ID",
                "vod_play_from": "",
                "vod_play_url": "",
            }
            return {"list": [vod]}

        html = self._fetch_text(self.host + "/anime/" + vid)
        if not html:
            return {"list": []}

        fly = self._extract_flight_text(html)
        anime = self._extract_json_after_key(fly, '"anime":')
        if not isinstance(anime, dict):
            anime = {}
        raw_sources = self._extract_json_after_key(fly, '"sources":')
        if not isinstance(raw_sources, list):
            raw_sources = []

        title = str(anime.get("title")).strip() if anime.get("title") else ""
        if not title:
            m_title = TITLE_TAG_RE.search(html)
            if m_title and m_title.group(1):
                title = m_title.group(1).split("·")[0].strip()
        if not title:
            title = carried_title if carried_title else ("番剧 " + vid)

        poster = ""
        if anime.get("cover_url"):
            poster = self._clean_img_url(anime.get("cover_url"))
        if not poster:
            m_pic = DETAIL_IMG_RE.search(html)
            if m_pic and m_pic.group(1):
                poster = self._clean_img_url(m_pic.group(1))

        desc = str(anime.get("description")).strip() if anime.get("description") else ""

        genres = []
        if isinstance(anime.get("meta_tags"), list):
            for t in anime.get("meta_tags"):
                if t:
                    genres.append(str(t))
        if not genres and anime.get("format"):
            genres.append(str(anime.get("format")))

        try:
            cur = int(anime.get("current_episodes") or 0)
        except Exception:
            cur = 0
        try:
            tot = int(anime.get("total_episodes") or 0)
        except Exception:
            tot = 0
        if anime.get("is_finished") and tot > 0:
            tail = "全 " + str(tot) + " 集"
        elif cur > 0 and tot > 0:
            tail = "更新至 " + str(cur) + "/" + str(tot)
        elif anime.get("remarks"):
            tail = str(anime.get("remarks")).strip()
        else:
            tail = "连载中"

        format_str = str(anime.get("format")).lower() if anime.get("format") else ""
        lines = self._build_sources(raw_sources, format_str, vid)

        recs = self._extract_recommendations(fly, vid)

        play_from_names = []
        play_url_parts = []
        for display_name, ep_list in lines:
            play_from_names.append(display_name)
            play_url_parts.append("#".join(ep["name"] + "$" + ep["value"] for ep in ep_list))
        if recs:
            rec_eps = []
            for rid, rtitle in recs:
                rec_eps.append(_clean_ep_name(rtitle) + "$" + json.dumps({"relId": rid}, ensure_ascii=False))
            play_from_names.append("相关推荐")
            play_url_parts.append("#".join(rec_eps))

        if desc:
            content = self._brand_block() + "\n" + desc
        else:
            fallback = ["标题：" + title]
            fallback.append("分类：" + "、".join(genres))
            fallback.append("片源：" + "、".join(play_from_names))
            fallback.append("编号：" + vid)
            if recs:
                fallback.append("相关推荐：" + "、".join(t for _rid, t in recs[:6]))
            content = self._brand_block() + "\n" + "\n".join(fallback)

        vod = {
            "vod_id": vid + "@@" + quote(title, safe=""),
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": _format_status(tail),
            "vod_content": content,
            "vod_play_from": "$$$".join(play_from_names),
            "vod_play_url": "$$$".join(play_url_parts),
        }
        if anime.get("release_year"):
            vod["vod_year"] = str(anime.get("release_year"))
        return {"list": [vod]}

    # ---------- player ----------

    def _pick_best_candidate(self, data, source_id):
        if not isinstance(data, dict) or not isinstance(data.get("candidates"), list):
            return ""
        valid = []
        for c in data.get("candidates"):
            if isinstance(c, dict) and c.get("url") and str(c.get("url")).startswith("http"):
                valid.append(c)
        if not valid:
            return ""
        if source_id:
            for c in valid:
                if str(c.get("source_id")) == str(source_id):
                    return str(c.get("url")).strip()
        for c in valid:
            if ".m3u8" in str(c.get("url")).split("?")[0].lower():
                return str(c.get("url")).strip()
        for c in valid:
            if ".mp4" in str(c.get("url")).split("?")[0].lower():
                return str(c.get("url")).strip()
        return str(valid[0].get("url")).strip()

    def _resolve_episode(self, ep_id, source_id, vod_id):
        headers = {"User-Agent": UA}
        if str(ep_id).isdigit():
            playback = self._playback_data(ep_id)
            if playback:
                direct = self._pick_best_candidate(playback, source_id)
                if direct:
                    final_url = WS_RUN_RE.sub("%20", direct.strip())
                    return {"parse": 0, "url": final_url, "header": headers}
        if str(vod_id).isdigit() and str(ep_id).isdigit():
            sniff = self.host + "/anime/" + str(vod_id) + "/play/" + str(ep_id)
            if source_id:
                sniff = sniff + "?source=" + quote(str(source_id), safe="")
            return {
                "parse": 1,
                "url": sniff,
                "header": {"User-Agent": UA, "Referer": self.host + "/"},
            }
        return {"parse": 1, "url": self.host + "/", "header": headers}

    def playerContent(self, flag, pid, vipFlags):
        headers = {"User-Agent": UA}
        data = None
        try:
            parsed = json.loads(pid)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = None

        if data is not None and data.get("relId"):
            rid = str(data.get("relId")).strip()
            html = self._fetch_text(self.host + "/anime/" + rid)
            if html:
                fly = self._extract_flight_text(html)
                anime = self._extract_json_after_key(fly, '"anime":')
                if not isinstance(anime, dict):
                    anime = {}
                raw_sources = self._extract_json_after_key(fly, '"sources":')
                if not isinstance(raw_sources, list):
                    raw_sources = []
                format_str = str(anime.get("format")).lower() if anime.get("format") else ""
                lines = self._build_sources(raw_sources, format_str, rid)
                for _name, ep_list in lines:
                    if ep_list:
                        first = json.loads(ep_list[0]["value"])
                        return self._resolve_episode(first.get("episodeId"), first.get("sourceId"), rid)
            return {
                "parse": 1,
                "url": self.host + "/anime/" + rid + "/",
                "header": {"User-Agent": UA, "Referer": self.host + "/"},
            }

        if data is not None and data.get("episodeId"):
            return self._resolve_episode(
                data.get("episodeId"),
                str(data.get("sourceId") or ""),
                str(data.get("vodId") or ""),
            )

        if isinstance(pid, str) and pid.startswith("http"):
            return {"parse": 0, "url": pid, "header": headers}

        return {"parse": 1, "url": self.host + "/", "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249885343&sig=b42b719bc51fdeb9
