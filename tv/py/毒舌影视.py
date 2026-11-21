# -*- coding: utf-8 -*-
# 毒舌影视 蜘蛛（源自 Hamo 插件 com.butterfly.dusheyingshi 的解析逻辑移植）
import hashlib
import http.cookiejar
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://m.xnhrsb.com"
    UA = "Mozilla/5.0 (Linux; Android 10; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
    CLASSES = [("1", "电影"), ("2", "电视剧"), ("3", "综艺"), ("4", "动漫"), ("5", "短剧"), ("duoban", "豆瓣Top250")]
    FILTER_DEFS = {
        "1": [
            ("class", "影片类型", ["", "喜剧", "爱情", "恐怖", "动作", "科幻", "剧情", "战争", "警匪", "犯罪", "动画", "奇幻", "武侠", "冒险", "枪战", "悬疑", "惊悚", "经典", "青春", "文艺", "微电影", "古装", "历史", "运动", "农村", "儿童", "网络电影"]),
            ("area", "地区", ["", "大陆", "香港", "台湾", "美国", "法国", "英国", "日本", "韩国", "德国", "泰国", "印度", "意大利", "西班牙", "加拿大", "其他"]),
            ("lang", "语言", ["", "国语", "英语", "粤语", "闽南语", "韩语", "日语", "法语", "德语", "其它"]),
        ],
        "2": [
            ("class", "影片类型", ["", "古装", "战争", "青春偶像", "喜剧", "家庭", "犯罪", "动作", "奇幻", "剧情", "历史", "经典", "乡村", "情景", "商战", "网剧", "其他"]),
            ("area", "地区", ["", "内地", "韩国", "香港", "台湾", "日本", "美国", "泰国", "英国", "新加坡", "其他"]),
            ("lang", "语言", ["", "国语", "英语", "粤语", "闽南语", "韩语", "日语", "其它"]),
        ],
        "3": [
            ("class", "影片类型", ["", "选秀", "情感", "访谈", "播报", "旅游", "音乐", "美食", "纪实", "曲艺", "生活", "游戏互动", "财经", "求职"]),
            ("area", "地区", ["", "内地", "港台", "日韩", "欧美"]),
            ("lang", "语言", ["", "国语", "英语", "粤语", "闽南语", "韩语", "日语", "其它"]),
        ],
        "4": [
            ("class", "影片类型", ["", "情感", "科幻", "热血", "推理", "搞笑", "冒险", "萝莉", "校园", "动作", "机战", "运动", "战争", "少年", "少女", "社会", "原创", "亲子", "益智", "励志", "其他"]),
            ("area", "地区", ["", "国产", "日本", "欧美", "其他"]),
            ("lang", "语言", ["", "国语", "英语", "粤语", "闽南语", "韩语", "日语", "其它"]),
        ],
        "5": [
            ("class", "影片类型", ["", "短剧"]),
            ("area", "地区", ["", "大陆"]),
            ("lang", "语言", ["", "国语"]),
        ],
        "duoban": [
            ("class", "影片类型", ["", "动作片", "喜剧片", "爱情片", "科幻片", "恐怖片", "剧情片", "战争片", "纪录片", "悬疑片", "犯罪片"]),
        ],
    }
    SORTS = [("", "全部"), ("time", "按时间"), ("hits", "按人气"), ("score", "按评分")]
    CARD_LI_RE = re.compile(r"<li[^>]*>([\s\S]*?)</li>", re.I)
    EP_A_RE = re.compile(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>([\s\S]*?)</a>', re.I)

    def getName(self):
        return "毒舌影视"

    def init(self, extend=""):
        self.host = self.DEFAULT_HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cj))

    # ---------- transport (cookie jar + PoW captcha flow) ----------
    def _request_raw(self, url, extra_headers=None, post_data=None):
        headers = {
            "User-Agent": self.UA,
            "Referer": self.host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Connection": "keep-alive",
        }
        if extra_headers:
            headers.update(extra_headers)
        data = post_data.encode("utf-8") if isinstance(post_data, str) else post_data
        try:
            req = urllib.request.Request(url, headers=headers, data=data)
            with self.opener.open(req, timeout=8) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            try:
                return e.code, e.read().decode("utf-8", "replace")
            except Exception:
                return e.code, ""
        except Exception:
            pass
        if url.startswith("https://"):
            fallback = "http://" + url[8:]
            try:
                req = urllib.request.Request(fallback, headers=headers, data=data)
                with self.opener.open(req, timeout=8) as resp:
                    return resp.status, resp.read().decode("utf-8", "replace")
            except urllib.error.HTTPError as e:
                try:
                    return e.code, e.read().decode("utf-8", "replace")
                except Exception:
                    return e.code, ""
            except Exception:
                pass
        return 0, ""

    def _solve_pow(self, challenge, difficulty):
        try:
            diff = int(difficulty)
        except Exception:
            diff = 4
        target = "0" * diff
        for nonce in range(200000):
            digest = hashlib.sha256((str(challenge) + str(nonce)).encode("utf-8")).hexdigest()
            if digest.startswith(target):
                return nonce, digest
        return None, None

    def _fetch(self, target_url):
        full = target_url
        if not full.startswith("http"):
            full = self.host + "/" + full.lstrip("/")
        status, html = self._request_raw(full)
        if status == 408 or "Bot detection" in html or "安全绿色" in html:
            self._request_raw(self.host + "/")
            _s, init_text = self._request_raw(self.host + "/__xcdn/captcha/api/init")
            try:
                init_data = json.loads(init_text or "{}")
            except Exception:
                init_data = {}
            challenge = init_data.get("challenge") or ""
            difficulty = init_data.get("difficulty") or 4
            if challenge:
                nonce, digest = self._solve_pow(challenge, difficulty)
                if nonce is not None:
                    verify_headers = {
                        "Content-Type": "application/json;charset=UTF-8",
                        "X-CDN-VERIFY-NONCE": str(nonce),
                        "X-CDN-VERIFY-RESULT": digest,
                    }
                    self._request_raw(self.host + "/__xcdn/captcha/api/verify", verify_headers, json.dumps({"challenge": challenge, "nonce": nonce}))
                    _status2, html = self._request_raw(full)
        return html or ""

    # ---------- helpers ----------
    def _strip(self, s):
        if not s:
            return ""
        return re.sub(r"<[^>]+>", "", str(s)).strip()

    def _format_pic(self, raw_pic):
        if not raw_pic:
            return ""
        clean = str(raw_pic).strip().replace("&amp;", "&")
        if clean.startswith("//"):
            return "https:" + clean
        if clean.startswith("/"):
            return self.host + clean
        if not clean.startswith("http"):
            return self.host + "/" + clean
        return clean

    def _parse_cards(self, html_text):
        items = []
        main = str(html_text or "")
        if '<div class="mrb"' in main:
            main = main.split('<div class="mrb"', 1)[1]
            if '<div class="page"' in main:
                main = main.split('<div class="page"', 1)[0]
        seen = set()
        for block in self.CARD_LI_RE.findall(main):
            hm = re.search(r'<a[^>]+href=["\']([^"\']+)["\']', block, re.I)
            pm = re.search(r'<img[^>]+(?:data-original|src)=["\']([^"\']+)["\']', block, re.I)
            nm = re.search(r'<(?:span|h3|h2|p)[^>]*class=["\'](?:dytit|name|title)["\'][^>]*>([\s\S]*?)</', block, re.I)
            if not (hm and pm and nm):
                continue
            raw_href = hm.group(1).strip()
            if raw_href in ("/", "#", self.host, self.host + "/") or "dsshiyisw" in raw_href or "javascript" in raw_href:
                continue
            title = self._strip(nm.group(1))
            if not title or title == "未命名视频":
                continue
            if raw_href in seen:
                continue
            seen.add(raw_href)
            remark = ""
            rm = re.search(r'<span[^>]*class=["\']hdinfo["\'][^>]*>([\s\S]*?)</span>', block, re.I)
            if rm:
                remark = re.sub(r"[\r\n\t]+", " ", self._strip(rm.group(1))).strip()
            items.append({
                "vod_id": raw_href,
                "vod_name": title,
                "vod_pic": self._format_pic(pm.group(1).strip()),
                "vod_remarks": ("蝴蝶影视 | " + remark) if remark else "蝴蝶影视",
                "style": {"type": "rect", "ratio": 0.75},
            })
        return items

    def _filter_rows(self, tid):
        rows = []
        defs = self.FILTER_DEFS.get(tid) or []
        by_key = {}
        for key, label, values in defs:
            by_key[key] = (label, values)
        order = ["class", "year", "area", "lang", "letter", "by"]
        for key in order:
            if key == "year":
                if tid == "duoban":
                    continue
                if tid == "5":
                    years = ["", "2026", "2025", "2024", "2023", "2022"]
                else:
                    years = [""] + [str(y) for y in range(2026, 2003, -1)]
                rows.append({"key": "year", "name": "年份", "init": years[0], "value": [{"n": (v if v else "全部"), "v": v} for v in years]})
            elif key == "letter":
                if tid == "duoban":
                    continue
                letters = [""] + [chr(c) for c in range(65, 91)] + ["0-9"]
                rows.append({"key": "letter", "name": "字母", "init": letters[0], "value": [{"n": ("0~9" if v == "0-9" else (v if v else "全部")), "v": v} for v in letters]})
            elif key == "by":
                if tid == "duoban":
                    continue
                rows.append({"key": "by", "name": "排序", "init": self.SORTS[0][0], "value": [{"n": n, "v": v} for v, n in self.SORTS]})
            elif key in by_key:
                label, values = by_key[key]
                rows.append({"key": key, "name": label, "init": values[0], "value": [{"n": (v if v else "全部"), "v": v} for v in values]})
        return rows

    # ---------- entries ----------
    def homeContent(self, filter=False):
        classes = [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]
        result = {"class": classes}
        if filter:
            result["filters"] = {cid: self._filter_rows(cid) for cid, _ in self.CLASSES}
        return result

    def homeVideoContent(self):
        html_text = self._fetch(self.host + "/dsshiyisw/1-----------.html")
        return {"list": self._parse_cards(html_text)}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        ext = extend if isinstance(extend, dict) else {}

        def enc(v):
            v = str(v or "")
            return urllib.parse.quote(v, safe="") if v else ""

        parts = [
            str(tid or "1"), "", "",
            enc(ext.get("class")), enc(ext.get("area")), enc(ext.get("lang")),
            enc(ext.get("year")), enc(ext.get("letter")), enc(ext.get("by")),
            str(page) if page > 1 else "", "", "",
        ]
        url = self.host + "/dsshiyisw/" + "-".join(parts) + ".html"
        html_text = self._fetch(url)
        items = self._parse_cards(html_text)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        keyword = str(key or "").strip()
        if not keyword:
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        url = self.host + "/dsshiyisc/" + urllib.parse.quote(keyword, safe="") + "----------" + str(page) + "---.html"
        html_text = self._fetch(url)
        items = self._parse_cards(html_text)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        item_id = str(ids[0] or "").strip()
        target = item_id
        if not target.startswith("http"):
            target = self.host + "/" + target.lstrip("/")
        html_text = self._fetch(target)
        h1 = re.search(r"<h1>([\s\S]*?)</h1>", html_text, re.I)
        title = self._strip(h1.group(1)) if h1 else "高清正片"
        pic = ""
        pm = re.search(r'<div[^>]*class=["\']dyimg["\'][^>]*>[\s\S]*?<img[^>]+src=["\']([^"\']+)["\']', html_text, re.I)
        if pm:
            pic = self._format_pic(pm.group(1).strip())
        desc = ""
        dm = re.search(r'<div[^>]*class=["\']yp_context["\'][^>]*>([\s\S]*?)</div>', html_text, re.I)
        if dm:
            desc = self._strip(dm.group(1))
        boxes = re.findall(r'<div[^>]*class=["\']mi_paly_box["\'][^>]*>([\s\S]*?)</div>\s*</div>\s*</div>', html_text, re.I)
        if not boxes:
            boxes = re.findall(r'<div[^>]*class=["\']mi_paly_box["\'][^>]*>([\s\S]*?)(?=<div[^>]*class=["\']mi_paly_box["\']|$)', html_text, re.I)
        froms = []
        play_urls = []
        for b, box in enumerate(boxes):
            tm = re.search(r'<div[^>]*class=["\']ypxingq_t["\'][^>]*>([\s\S]*?)</div>', box, re.I)
            raw_line = self._strip(tm.group(1)) if tm else ""
            clean_line = raw_line.replace("-在线播放", "").strip() or ("线路 " + str(b + 1))
            eps = []
            ep_idx = 1
            for am in self.EP_A_RE.finditer(box):
                href = am.group(1).strip()
                ep_text = self._strip(am.group(2))
                if "app2.zstv47" in href or "APP" in ep_text or "下载" in ep_text:
                    continue
                if "/dsshiyipy/" not in href and "play" not in href:
                    continue
                full_href = href if href.startswith("http") else self.host + "/" + href.lstrip("/")
                ep_name = (ep_text or ("第 " + str(ep_idx) + " 集")).replace("$", "").replace("#", "").strip() or ("第 " + str(ep_idx) + " 集")
                val = json.dumps({"playUrl": full_href}, ensure_ascii=False)
                eps.append(ep_name + "$" + val)
                ep_idx += 1
            if eps:
                froms.append("🦋 " + clean_line)
                play_urls.append("#".join(eps))
        if not froms:
            froms = ["🦋 蝴蝶专线"]
            play_urls = ["正片$" + json.dumps({"playUrl": target}, ensure_ascii=False)]
        lines = [
            "🦋 毒舌影视官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc and desc != "暂无剧情简介":
            lines.append(desc)
        else:
            lines.append("标题：" + title)
            lines.append("片源：毒舌影视")
            lines.append("编号：" + item_id)
        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": pic,
            "vod_bg": pic,
            "vod_background": pic,
            "vod_banner": pic,
            "vod_remarks": "蝴蝶影视",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "$$$".join(froms),
            "vod_play_url": "$$$".join(play_urls),
            "style": {"type": "rect", "ratio": 0.75},
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                play_url = str(data.get("playUrl") or "").strip()
        except Exception:
            pass
        if not play_url:
            play_url = str(id or "").strip()
        if not play_url.startswith("http"):
            play_url = self.host + "/" + play_url.lstrip("/")
        html_text = self._fetch(play_url)
        headers = {"User-Agent": self.UA, "Referer": play_url}
        target_media = ""
        scope = html_text
        anchor = html_text.find("player_aaaa")
        if anchor >= 0:
            scope = html_text[anchor:]
        um = re.search(r'"url"\s*:\s*"([^"]+)"', scope)
        if not um and scope is not html_text:
            um = re.search(r'"url"\s*:\s*"([^"]+)"', html_text)
        if um:
            raw_target = um.group(1).replace("\\/", "/")
            if ".m3u8" in raw_target or ".mp4" in raw_target:
                target_media = raw_target
        if target_media and target_media.startswith("http"):
            is_hls = bool(re.search(r"\.m3u8(?:[?#]|$)", target_media, re.I))
            return {"parse": 0, "playUrl": "", "url": target_media, "header": headers}
        im = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', html_text, re.I)
        if im:
            cand = im.group(1).strip()
            if cand.startswith("//"):
                cand = "https:" + cand
            elif cand.startswith("/"):
                cand = self.host + cand
            return {"parse": 1, "playUrl": "", "url": cand, "header": headers}
        return {"parse": 1, "playUrl": "", "url": play_url, "header": {"User-Agent": self.UA, "Referer": self.host + "/"}}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249298265&sig=fe749f98b4fe1a5d
