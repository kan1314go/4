# -*- coding: utf-8 -*-
# 9G8XX 蜘蛛（源自 Hamo 插件 com.butterfly.9g88x 的接口逻辑移植）
import html as html_lib
import json
import re
import time
import urllib.request
import urllib.error

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_SITE = "https://www.9g88x.com"
    DATA_API = "https://data.7wzx9.com/forward"
    CDN_API = "https://data.7wzx9.com/getDataInit"
    UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
    CLASSES = [
        ("6", "91传媒"), ("7", "精东传媒"), ("8", "麻豆传媒"), ("9", "麻豆映画"),
        ("10", "麻豆猫爪"), ("11", "蜜桃传媒"), ("12", "天美传媒"), ("13", "星空传媒"),
        ("14", "偷拍自拍"), ("15", "日韩视频"), ("16", "欧美性爱"), ("17", "智能换脸"),
        ("18", "经典三级"), ("19", "网红主播"), ("20", "台湾辣妹"), ("21", "onlyfans"),
        ("22", "中文字幕"), ("23", "经典素人"), ("24", "高清无码"), ("25", "美颜巨乳"),
        ("26", "丝袜制服"), ("27", "SM系列"), ("28", "欧美系列"), ("29", "H動畫"),
    ]
    IMG_RE = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.I)

    def getName(self):
        return "9G8XX"

    def init(self, extend=""):
        self.site = self.DEFAULT_SITE
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.site = extend.strip().rstrip("/")
        self.cdn = None
        self.cdn_ts = 0.0

    # ---------- transport ----------
    def _post_json(self, url, body):
        headers = {
            "Content-Type": "application/json",
            "User-Agent": self.UA,
            "Origin": self.site,
            "Referer": self.site + "/",
        }
        for _ in range(2):
            try:
                data = json.dumps(body).encode("utf-8")
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=20) as resp:
                    status = resp.status
                    raw = resp.read()
                if 200 <= status < 400 and raw:
                    parsed = json.loads(raw.decode("utf-8", "replace"))
                    return parsed if isinstance(parsed, dict) else {}
                return {}
            except urllib.error.HTTPError:
                return {}
            except Exception:
                pass
            time.sleep(0.5)
        return {}

    def _cdn_map(self, force=False):
        now = time.time()
        if not force and self.cdn and (now - self.cdn_ts) < 3600:
            return self.cdn
        cmap = {}
        for _ in range(2):
            if cmap:
                break
            res = self._post_json(self.CDN_API, {"name": "John", "age": 31, "city": "New York"})
            data = res.get("data") if isinstance(res.get("data"), dict) else {}
            cmap = data.get("macVodLinkMap") if isinstance(data.get("macVodLinkMap"), dict) else {}
        if cmap:
            self.cdn = cmap
            self.cdn_ts = now
            return cmap
        return self.cdn or {}

    def _api_info(self, type_id, type_mid, page, records, content, search_type=None):
        body = {
            "command": "WEB_GET_INFO",
            "pageNumber": page,
            "RecordsPage": records or 30,
            "typeId": type_id,
            "typeMid": type_mid,
            "languageType": "CN",
            "content": content or "",
        }
        if search_type:
            body["type"] = search_type
        return self._post_json(self.DATA_API, body)

    def _api_detail(self, item_id, type_mid):
        return self._post_json(self.DATA_API, {
            "command": "WEB_GET_INFO_DETAIL",
            "languageType": "CN",
            "content": "",
            "id": item_id,
            "type_Mid": type_mid,
        })

    # ---------- helpers ----------
    def _clean(self, s):
        t = re.sub(r"<[^>]+>", "", str(s or ""))
        t = html_lib.unescape(t)
        return re.sub(r"[\r\n\t]+", " ", t).strip()

    def _remarks(self, meta):
        cm = self._clean(meta)
        return ("蝴蝶影视 | " + cm) if cm else "蝴蝶影视"

    def _build_pic(self, vod_pic, server_id, cdn):
        if not vod_pic:
            return ""
        raw = str(vod_pic).strip()
        if raw.startswith("http"):
            return raw
        srv = cdn.get(str(server_id)) if isinstance(cdn.get(str(server_id)), dict) else {}
        pre = (srv or {}).get("PIC_LINK_1") or ""
        return (pre + raw) if pre else raw

    def _build_play(self, vod_url, server_id, cdn):
        if not vod_url:
            return ""
        raw = str(vod_url).strip()
        if raw.startswith("http"):
            return raw
        srv = cdn.get(str(server_id)) if isinstance(cdn.get(str(server_id)), dict) else {}
        pre = (srv or {}).get("LINK_1") or ""
        return (pre + raw) if pre else raw

    def _fmt_item(self, item, cdn):
        sid = item.get("vod_server_id") or ""
        pic = item.get("vod_pic") or item.get("art_pic") or ""
        name = self._clean(item.get("vod_name") or item.get("art_name") or "视频")
        meta = item.get("vod_class") or item.get("art_class") or item.get("vod_remarks") or "高清"
        return {
            "vod_id": str(item.get("id") or ""),
            "vod_name": name,
            "vod_pic": self._build_pic(pic, sid, cdn),
            "vod_remarks": self._remarks(meta),
            "style": {"type": "rect", "ratio": 1.78},
        }

    def _result_list(self, res):
        data = res.get("data") if isinstance(res.get("data"), dict) else {}
        lst = data.get("resultList")
        return lst if isinstance(lst, list) else []

    # ---------- entries ----------
    def homeContent(self, filter=False):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]}

    def homeVideoContent(self):
        cdn = self._cdn_map()
        items = []
        for tid, _name in self.CLASSES[:6]:
            res = self._api_info(tid, "1", 1, 5, "")
            for item in self._result_list(res):
                if isinstance(item, dict):
                    items.append(self._fmt_item(item, cdn))
            if len(items) >= 30:
                break
        return {"list": items[:30]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        cdn = self._cdn_map()
        res = self._api_info(str(tid or "6"), "1", page, 30, "")
        items = [self._fmt_item(it, cdn) for it in self._result_list(res) if isinstance(it, dict)]
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        kw = str(key or "").strip()
        if not kw:
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        cdn = self._cdn_map()
        res = self._api_info("0", "1", page, 30, kw, "1")
        items = [self._fmt_item(it, cdn) for it in self._result_list(res) if isinstance(it, dict)]
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        item_id = str(ids[0] or "")
        if not item_id:
            return {"list": []}
        cdn = self._cdn_map()
        mid = "1"
        det = {}
        r1 = self._api_detail(item_id, "1")
        d1 = (r1.get("data") or {}).get("result") if isinstance(r1.get("data"), dict) else {}
        if isinstance(d1, dict) and (d1.get("vod_name") or d1.get("vod_url")):
            det = d1
        else:
            r2 = self._api_detail(item_id, "2")
            d2 = (r2.get("data") or {}).get("result") if isinstance(r2.get("data"), dict) else {}
            if isinstance(d2, dict) and d2:
                mid = "2"
                det = d2
        lines = [
            "🦋 9G8XX官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.site + "/",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if mid == "1":
            play = self._build_play(det.get("vod_url") or "", det.get("vod_server_id") or "", cdn)
            pic = self._build_pic(det.get("vod_pic") or "", det.get("vod_server_id") or "", cdn)
            title = self._clean(det.get("vod_name") or ("视频 " + item_id))
            lines.append("标题：" + title)
            if det.get("vod_class"):
                lines.append("分类：" + self._clean(det.get("vod_class")))
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + item_id)
            val = json.dumps({"playUrl": play, "vid": item_id}, ensure_ascii=False)
            vod = {
                "vod_id": item_id,
                "vod_name": title,
                "vod_pic": pic,
                "vod_remarks": self._remarks(det.get("vod_remarks") or det.get("vod_class") or "正片"),
                "vod_actor": "🦋 TG群: @tvshare23",
                "vod_director": "🦋 蝴蝶影视",
                "vod_content": "\n".join(lines),
                "vod_play_from": "🦋 蝴蝶专线",
                "vod_play_url": "超清正片$" + val,
                "style": {"type": "rect", "ratio": 1.78},
            }
            if det.get("vod_year"):
                vod["vod_year"] = str(det.get("vod_year"))
            if det.get("vod_class"):
                vod["vod_class"] = self._clean(det.get("vod_class"))
            return {"list": [vod]}
        title = self._clean(det.get("art_name") or ("写真 " + item_id))
        lines.append("标题：" + title)
        lines.append("片源：🦋 蝴蝶专线")
        lines.append("编号：" + item_id)
        eps = []
        for idx, m in enumerate(self.IMG_RE.finditer(str(det.get("art_url") or "")), 1):
            val = json.dumps({"playUrl": m.group(1), "vid": item_id}, ensure_ascii=False)
            eps.append("图片 " + str(idx) + "$" + val)
        if not eps:
            val = json.dumps({"vid": item_id}, ensure_ascii=False)
            eps.append("正片$" + val)
        vod = {
            "vod_id": item_id,
            "vod_name": title,
            "vod_pic": det.get("art_pic") or "",
            "vod_remarks": self._remarks("图片写真"),
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(eps),
            "style": {"type": "rect", "ratio": 1.78},
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        headers = {"User-Agent": self.UA, "Referer": self.site + "/"}
        play_url = ""
        vid = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                play_url = str(data.get("playUrl") or "").strip()
                vid = str(data.get("vid") or "")
        except Exception:
            pass
        if play_url.startswith("http"):
            return {"parse": 0, "playUrl": "", "url": play_url, "header": headers}
        if vid:
            cdn = self._cdn_map()
            r1 = self._api_detail(vid, "1")
            d1 = (r1.get("data") or {}).get("result") if isinstance(r1.get("data"), dict) else {}
            if isinstance(d1, dict):
                play = self._build_play(d1.get("vod_url") or "", d1.get("vod_server_id") or "", cdn)
                if not play and d1.get("vod_url") and not str(d1.get("vod_url")).startswith("http"):
                    cdn2 = self._cdn_map(force=True)
                    play = self._build_play(d1.get("vod_url") or "", d1.get("vod_server_id") or "", cdn2)
                if play:
                    return {"parse": 0, "playUrl": "", "url": play, "header": headers}
        return {"parse": 1, "playUrl": "", "url": "", "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249325906&sig=baf3fa213c774fd1
