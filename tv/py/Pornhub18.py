# -*- coding: utf-8 -*-
# Pornhub

import re
import json
import requests
from urllib.parse import quote
from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://www.pornhub.com"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    BRAND = "蝴蝶影视"
    POSTER_RATIO = 1.78
    PAGE_SIZE = 42
    TIMEOUT = 8

    CATEGORIES = [
        ("28", "熟女"), ("37", "青春少女 (18-25)"), ("29", "熟妇"), ("17", "黑人"),
        ("35", "肛交"), ("181", "忘年恋 (18+)"), ("27", "女同"), ("65", "三人行"),
        ("111", "日本"), ("36", "动漫"), ("8", "大胸"), ("24", "户外"),
        ("86", "卡通"), ("10", "捆绑"), ("15", "内射"), ("80", "群交"),
        ("7", "大屌"), ("22", "自慰"), ("69", "潮吹"), ("6", "丰满"),
        ("492", "单人女优"), ("30", "女优"), ("115", "独家"), ("25", "跨种族"),
        ("59", "小胸"), ("105", "60帧"), ("3", "素人"), ("98", "阿拉伯"),
        ("1", "亚洲"), ("5", "美女"), ("89", "保姆 (18+)"), ("141", "幕后花絮"),
        ("4", "大屁股"), ("76", "双性恋男"), ("9", "金发"), ("13", "口交"),
        ("102", "巴西"), ("96", "英国"), ("11", "褐发"), ("14", "颜射"),
        ("90", "试镜"), ("12", "明星"), ("732", "字幕"), ("68", "大学生 (18+)"),
        ("57", "精选合集"), ("241", "角色扮演"), ("242", "绿帽"), ("16", "射精"),
        ("100", "捷克"), ("72", "双插"), ("55", "欧洲"), ("93", "恋足"),
        ("502", "女性高潮"), ("18", "恋物癖"), ("592", "指交"), ("19", "拳交"),
        ("94", "法国"), ("32", "搞笑"), ("881", "游戏"), ("95", "德国"),
        ("20", "手交"), ("21", "硬核"), ("101", "印度"), ("97", "意大利"),
        ("103", "韩国"), ("26", "拉丁裔"), ("78", "按摩"), ("512", "肌肉男"),
        ("121", "音乐"), ("2", "群交派对"), ("201", "恶搞"), ("53", "派对"),
        ("211", "撒尿"), ("891", "播客"), ("41", "第一视角"), ("131", "舔阴"),
        ("31", "实拍"), ("42", "红发"), ("81", "情境扮演"), ("522", "浪漫"),
        ("67", "粗暴性爱"), ("99", "俄罗斯"), ("88", "校园 (18+)"), ("91", "抽烟"),
        ("92", "单人男优"), ("444", "继亲幻想"), ("542", "假阳具"), ("33", "脱衣舞"),
        ("562", "纹身女"), ("23", "情趣玩具"), ("138", "认证素人"), ("482", "认证情侣"),
        ("139", "认证模特"), ("43", "复古"), ("61", "直播"),
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
        return "Pornhub"

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

    def _decode_entities(self, s):
        out = str(s or "")
        out = out.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
        out = out.replace("&#039;", "'").replace("&lt;", "<").replace("&gt;", ">").replace("&nbsp;", " ")
        return out

    def _json_unquote(self, raw):
        try:
            return json.loads('"' + raw + '"')
        except Exception:
            return raw

    def _abs_poster(self, raw):
        u = self._decode_entities(str(raw or "").strip())
        if not u:
            return ""
        if u.startswith("http://"):
            u = "https://" + u[7:]
        if u.startswith("//"):
            u = "https:" + u
        if u.startswith("/"):
            u = self.host + u
        if not u.startswith("http"):
            u = "https://" + u
        return u

    def _parse_cards(self, doc, is_search):
        seg = doc or ""
        if not is_search:
            m = re.search(r'<ul id="videoCategory"[\s\S]*?</ul>', seg)
            if m:
                seg = m.group(0)
        items = []
        seen = set()
        parts = seg.split('<li class="pcVideoListItem')
        for chunk in parts[1:]:
            km = re.search(r'data-video-vkey="([0-9A-Za-z]+)"', chunk)
            if not km:
                continue
            vkey = km.group(1)
            if 'data-action="channel_info"' in chunk[:800]:
                continue
            if vkey in seen:
                continue
            tm = re.search(r'title="([^"]*)"', chunk)
            if tm and tm.group(1):
                title = self._decode_entities(tm.group(1)).strip()
            else:
                title = vkey
            poster = ""
            pm = re.search(r'data-mediumthumb="([^"]+)"', chunk)
            if pm and pm.group(1):
                poster = self._abs_poster(pm.group(1))
            else:
                im = re.search(r'<img[^>]*src="([^"]+)"', chunk)
                if im and im.group(1):
                    poster = self._abs_poster(im.group(1))
            if not poster:
                continue
            dur = ""
            dm = re.search(r'<var class="duration">([^<]+)</var>', chunk)
            if dm and dm.group(1):
                dur = dm.group(1).strip()
            seen.add(vkey)
            items.append({
                "vod_id": vkey,
                "vod_name": title,
                "vod_pic": poster,
                "vod_remarks": (self.BRAND + " | " + dur) if dur else self.BRAND,
                "style": {"type": "rect", "ratio": self.POSTER_RATIO},
            })
        return items

    def _filter_groups(self):
        return [
            {"key": "order", "name": "排序", "init": "", "value": [
                {"n": "默认推荐", "v": ""},
                {"n": "最多观看", "v": "mv"},
                {"n": "评分最高", "v": "tr"},
                {"n": "最热门", "v": "ht"},
                {"n": "最长", "v": "lg"},
                {"n": "最新", "v": "cm"},
            ]},
            {"key": "p", "name": "制作方", "init": "", "value": [
                {"n": "全部", "v": ""},
                {"n": "专业制作", "v": "professional"},
                {"n": "自制", "v": "homemade"},
            ]},
            {"key": "hd", "name": "清晰度", "init": "", "value": [
                {"n": "全部", "v": ""},
                {"n": "仅高清", "v": "1"},
            ]},
        ]

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.CATEGORIES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, _name in self.CATEGORIES:
                filters[cid] = self._filter_groups()
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        status, doc = self._fetch(self.host + "/video?o=mv", self.host + "/")
        if status != 200:
            return {"list": []}
        return {"list": self._parse_cards(doc, False)}

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
        category_id = str(tid) if tid else "28"
        ext = extend if isinstance(extend, dict) else {}
        order = str(ext.get("order", "") or "").strip()
        if not order:
            order = "mv"
        if order not in ("mr", "mv", "tr", "ht", "lg", "cm"):
            order = "mv"
        url = self.host + "/video?c=" + quote(category_id, safe="") + "&o=" + order
        if page > 1:
            url += "&page=" + str(page)
        p = str(ext.get("p", "") or "").strip()
        if p in ("professional", "homemade"):
            url += "&p=" + p
        if str(ext.get("hd", "")) == "1":
            url += "&hd=1"
        status, doc = self._fetch(url, self.host + "/")
        if status != 200:
            return self._page_result(page, [])
        return self._page_result(page, self._parse_cards(doc, False))

    def searchContent(self, key, quick, pg="1"):
        page = self._to_page(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._page_result(page, [])
        url = self.host + "/video/search?search=" + quote(keyword, safe="")
        if page > 1:
            url += "&page=" + str(page)
        status, doc = self._fetch(url, self.host + "/")
        if status != 200:
            return self._page_result(page, [])
        return self._page_result(page, self._parse_cards(doc, True))

    def _extract_ld(self, doc):
        out = {"name": "", "duration": "", "thumbnailUrl": "", "uploadDate": "", "creator": "", "views": ""}
        m = re.search(r'<script type="application/ld\+json">([\s\S]*?)</script>', doc or "")
        if not m:
            return out
        block = m.group(1)
        nm = re.search(r'"name":\s*"((?:[^"\\]|\\.)*)"', block)
        if nm:
            out["name"] = self._json_unquote(nm.group(1))
        dm = re.search(r'"duration":\s*"([^"]+)"', block)
        if dm:
            out["duration"] = dm.group(1)
        th = re.search(r'"thumbnailUrl":\s*"([^"]+)"', block)
        if th:
            out["thumbnailUrl"] = self._json_unquote(th.group(1))
        um = re.search(r'"uploadDate":\s*"([^"]+)"', block)
        if um:
            out["uploadDate"] = um.group(1)
        cm = re.search(r'"creator":\s*\{[^}]*?"name":\s*"((?:[^"\\]|\\.)*)"', block)
        if cm:
            out["creator"] = self._json_unquote(cm.group(1))
        wm = re.search(r'"interactionType":\s*"https://schema\.org/WatchAction",\s*"userInteractionCount":\s*(\d+)', block)
        if wm:
            out["views"] = wm.group(1)
        return out

    def _extract_media(self, doc):
        text = doc or ""
        start = text.find('"mediaDefinitions":[')
        if start == -1:
            return []
        open_idx = text.find("[", start)
        if open_idx == -1:
            return []
        depth = 0
        i = open_idx
        while i < len(text):
            ch = text[i]
            if ch == "[":
                depth += 1
            elif ch == "]":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        if depth != 0:
            return []
        arr = None
        try:
            arr = json.loads(text[open_idx:i + 1])
        except Exception:
            arr = None
        out = []
        seen = set()
        if arr:
            for d in arr:
                if not isinstance(d, dict):
                    continue
                vu = d.get("videoUrl")
                if not isinstance(vu, str) or not vu:
                    continue
                if vu in seen:
                    continue
                seen.add(vu)
                out.append(d)
            if out:
                return out
        for m in re.finditer(r'"videoUrl"\s*:\s*"((?:[^"\\]|\\.)*)"', text):
            url = self._json_unquote(m.group(1))
            if not url or url in seen:
                continue
            before = text[max(0, m.start() - 400):m.start()]
            fm = re.search(r'"format"\s*:\s*"(hls|mp4)"', before)
            qm = re.search(r'"quality"\s*:\s*"?([0-9]+)"?', before)
            dq = '"defaultQuality":true' in before
            seen.add(url)
            out.append({
                "format": fm.group(1) if fm else "",
                "quality": qm.group(1) if qm else "",
                "defaultQuality": dq,
                "videoUrl": url,
            })
        return out

    def _pick_playable(self, media):
        for d in media:
            if d.get("format") == "hls" and d.get("defaultQuality") is True:
                return d
        for d in media:
            if d.get("format") == "hls":
                return d
        for d in media:
            if d.get("format") == "mp4":
                return d
        return None

    def _parse_related(self, doc, self_key):
        out = []
        seen = set()
        for m in re.finditer(r'<a[^>]*data-label="related_video_container"[^>]*>', doc or "", re.I):
            tag = m.group(0)
            km = re.search(r'viewkey=([0-9A-Za-z]+)', tag)
            if not km:
                continue
            vkey = km.group(1)
            if vkey == self_key or vkey in seen:
                continue
            seen.add(vkey)
            tm = re.search(r'title="([^"]*)"', tag)
            if tm and tm.group(1):
                title = self._decode_entities(tm.group(1)).strip()
            else:
                title = vkey
            out.append((vkey, title))
        return out

    def _parse_iso_duration(self, s):
        m = re.search(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?', str(s or ""))
        if not m:
            return 0
        h = int(m.group(1)) if m.group(1) else 0
        mi = int(m.group(2)) if m.group(2) else 0
        sec = float(m.group(3)) if m.group(3) else 0
        return int(round(h * 3600 + mi * 60 + sec))

    def _fmt_duration(self, total):
        total = max(0, int(round(total or 0)))
        h = total // 3600
        mi = (total % 3600) // 60
        s = total % 60
        mm = str(h * 60 + mi) if h > 0 else str(mi)
        ss = ("0" + str(s)) if s < 10 else str(s)
        return mm + ":" + ss

    def _brand_block(self):
        lines = [
            "🦋 Pornhub官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _episode_name(self, name):
        return str(name).replace("$", "_").replace("#", "_")

    def detailContent(self, ids):
        item_id = ""
        if isinstance(ids, (list, tuple)) and ids:
            item_id = str(ids[0])
        elif ids:
            item_id = str(ids)
        if not item_id:
            return {"list": [], "msg": "未找到该影片"}
        detail_url = self.host + "/view_video.php?viewkey=" + quote(item_id, safe="")
        status, doc = self._fetch(detail_url, self.host + "/")
        if status != 200 or not doc:
            return {"list": [], "msg": "未找到该影片"}
        ld = self._extract_ld(doc)
        title = ld["name"] or ""
        if not title:
            tm = re.search(r'<title>([\s\S]*?)</title>', doc, re.I)
            if tm:
                title = re.sub(r' - Pornhub\.com\s*$', "", self._decode_entities(tm.group(1))).strip()
        if not title:
            title = item_id
        poster = ""
        om = re.search(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', doc, re.I)
        if not om:
            om = re.search(r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"', doc, re.I)
        if om:
            poster = self._abs_poster(om.group(1))
        if not poster and ld["thumbnailUrl"]:
            poster = self._abs_poster(ld["thumbnailUrl"])
        media = self._extract_media(doc)
        cats = []
        for cm in re.finditer(r'<a[^>]*data-label="category"[^>]*>([^<]+)</a>', doc, re.I):
            ct = self._decode_entities(cm.group(1)).strip()
            if ct and ct not in cats:
                cats.append(ct)
        tags = []
        for gm in re.finditer(r'<a[^>]*data-label="tag"[^>]*><span>([^<]+)</span></a>', doc, re.I):
            tg = self._decode_entities(gm.group(1)).strip()
            if tg and tg not in tags:
                tags.append(tg)
        if ld["creator"]:
            actor = ld["creator"] + ", 🦋 TG群: @tvshare23"
        else:
            actor = "🦋 TG群: @tvshare23"
        related = self._parse_related(doc, item_id)
        year = ld["uploadDate"][:4] if len(ld["uploadDate"]) >= 4 else ""
        dur_sec = self._parse_iso_duration(ld["duration"])
        dur_text = self._fmt_duration(dur_sec) if dur_sec > 0 else ""
        views = ld["views"]
        rel_names = [t for _k, t in related[:6]]
        body_lines = [
            "标题：" + title,
            "分类：" + (" / ".join(cats) if cats else "未知"),
            "上传：" + (ld["uploadDate"][:10] if ld["uploadDate"] else "未知"),
            "时长：" + (dur_text if dur_text else "未知"),
            "观看：" + ((views + "次") if views else "未知"),
            "片源：🦋 蝴蝶专线",
            "编号：" + item_id,
            "标签：" + (" / ".join(tags[:8]) if tags else "无"),
            "相关推荐：" + " / ".join(rel_names),
        ]
        content = self._brand_block() + "\n" + "\n".join(body_lines)
        episodes = []
        if media:
            episodes.append(self._episode_name("正片") + "$" + json.dumps({"viewkey": item_id}, ensure_ascii=False))
            for idx, (rk, rt) in enumerate(related):
                name = rt if rt else ("第" + str(idx + 2) + "集")
                episodes.append(self._episode_name(name) + "$" + json.dumps({"viewkey": rk}, ensure_ascii=False))
        else:
            note = "未找到可播放片源"
            content = content + "\n" + note
            episodes.append(self._episode_name("暂无播放源") + "$" + json.dumps({"notice": note}, ensure_ascii=False))
        remarks = self.BRAND
        if dur_text:
            remarks += " | " + dur_text
        if views:
            remarks += " · " + views + "次观看"
        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_year": year,
            "vod_class": ", ".join(cats),
            "vod_actor": actor,
            "vod_director": "🦋 蝴蝶影视",
            "vod_remarks": remarks,
            "vod_content": content,
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes),
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        viewkey = ""
        if raw.startswith("{"):
            try:
                obj = json.loads(raw)
            except Exception:
                obj = None
            if isinstance(obj, dict):
                if obj.get("notice"):
                    return {"parse": 0, "msg": str(obj["notice"])}
                viewkey = str(obj.get("viewkey", "") or "")
        else:
            viewkey = raw
        if not viewkey:
            return {"parse": 0, "jx": 0, "url": "", "msg": "缺少播放标识"}
        detail_url = self.host + "/view_video.php?viewkey=" + quote(viewkey, safe="")
        status, doc = self._fetch(detail_url, self.host + "/")
        if status != 200 or not doc:
            return {"parse": 0, "jx": 0, "url": "", "msg": "请求失败：HTTP " + str(status)}
        media = self._extract_media(doc)
        pick = self._pick_playable(media)
        if not pick:
            return {"parse": 0, "jx": 0, "url": "", "msg": "未能提取到播放地址"}
        return {
            "parse": 0,
            "jx": 0,
            "url": pick["videoUrl"],
            "header": {"User-Agent": self.DEFAULT_UA, "Referer": detail_url},
        }

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Not Found"]

    def destroy(self):
        return True

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250162248&sig=51e982147814c539
