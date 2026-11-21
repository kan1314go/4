# -*- coding: utf-8 -*-
# 暗夜蜜桃 蜘蛛（源自 Hamo 插件 com.hamo.source.mitaoline 的接口逻辑移植）
import hashlib
import hmac as hmac_lib
import json
import random
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    SITE = "https://mitaoline.com"
    REFERER = "https://honeypeach.cc/"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    DRAMA_MODS = ("duanju", "hongtao", "hbo")
    PORTRAIT_MODS = ("duanju", "hongtao", "hbo", "caibian")
    SRC_MAP = {
        "huangtao": "duoju86", "huangguo": "huangguo", "yeguo": "duoju86", "chengguo": "duoju86",
        "yizk": "duoju86", "huangdou": "huangdou", "chiguo": "chiguo", "pengran": "pengran",
        "erciyuan": "huangdou", "jinbi": "huangdou", "huiyuan": "huangdou", "zhenren": "huangdou",
        "tc": "duoju89", "nx": "duoju89", "gz": "duoju89", "ds": "duoju89", "xh": "duoju89",
        "xy": "duoju89", "manju": "huangdou", "unclassified": "duoju89", "meiju": "huangdou", "hanju": "huangdou",
    }
    CATEGORIES = [
        ("video", "蜜桃视频", [("cat", "分类", [("", "全部"), ("new", "最近更新"), ("release", "新作上市"), ("chinese-subtitle", "中文字幕"), ("madou", "麻豆传媒"), ("uncensored-leak", "无码流出"), ("fc2", "FC2"), ("monthly-hot", "热门"), ("genres/VR", "VR"), ("heyzo", "HEYZO"), ("tokyohot", "东京热"), ("1pondo", "一本道"), ("caribbeancom", "Caribbeancom"), ("caribbeancompr", "Caribbeancompr"), ("siro", "SIRO"), ("luxu", "LUXU"), ("twav", "TWAV"), ("furuke", "Furuke"), ("today-hot", "今日热门"), ("weekly-hot", "本週热门")])]),
        ("duanju", "蜜桃短剧", [("cat", "厂牌分类", [("", "全部"), ("huangtao", "黄桃短剧"), ("huangguo", "黄果短剧"), ("yeguo", "野果短剧"), ("chengguo", "橙果短剧"), ("yizk", "一直看短剧"), ("huangdou", "黄豆短剧"), ("chiguo", "赤果短剧"), ("pengran", "怦然心动"), ("erciyuan", "动漫"), ("jinbi", "金币专区"), ("huiyuan", "会员专区")]),
                                ("sub", "二级筛选", [("0", "全部/精选/推荐"), ("1", "子类1(AI短剧/野果原创/国漫)"), ("2", "子类2(AI漫剧/真人短剧/民国/日漫)"), ("3", "子类3(魔改漫剧/悬疑/动画同人)"), ("4", "子类4(网红改编/单体作品/游戏同人)"), ("5", "子类5(影视魔改/排行榜)"), ("6", "子类6(国漫AI/都市艳遇)"), ("7", "子类7(魔改短剧/恋爱情感)"), ("8", "子类8(爆爽逆袭)"), ("9", "子类9(职场沉浮)"), ("10", "子类10(家庭伦理)"), ("11", "子类11(奇幻修仙)")])]),
        ("hongtao", "红桃短剧", [("cat", "频道", [("", "全部"), ("zhenren", "红桃原创"), ("tc", "甜宠言情"), ("nx", "逆袭爽剧"), ("gz", "古装传奇"), ("ds", "都市生活"), ("xh", "玄幻奇幻"), ("xy", "悬疑热血"), ("manju", "正经漫剧"), ("unclassified", "未分类短剧")]),
                                 ("sub", "题材(原创专享)", [("", "全部"), ("0", "都市"), ("1", "古装"), ("2", "民国"), ("3", "重生"), ("4", "异能")])]),
        ("caibian", "擦边短剧", [("cat", "排序", [("0", "最新"), ("1", "推荐"), ("2", "全部")])]),
        ("shortv", "蜜桃动漫", [("cat", "源频道", [("all", "全部"), ("Hanime", "Hanime"), ("NaughtyMachinima", "NaughtyMachinima"), ("HS日本4K动漫", "HS日本4K动漫")])]),
        ("guochan", "国产精品", []),
        ("heiliao", "黑料吃瓜", [("cat", "频道", [("0", "最新"), ("1", "推荐")])]),
        ("hbo", "HBO精选", [("cat", "剧集类型", [("meiju", "美剧"), ("hanju", "韩剧")])]),
        ("live", "蜜桃直播", [("cat", "分类与地区", [("", "全部"), ("girls", "女主播"), ("couples", "情侣"), ("men", "男主播"), ("trans", "跨性别"), ("cn", "中国"), ("jp", "日本"), ("kr", "韩国"), ("us", "美国"), ("th", "泰国"), ("vn", "越南"), ("ru", "俄罗斯")])]),
    ]

    def getName(self):
        return "暗夜蜜桃"

    def init(self, extend=""):
        self.auth = None
        self.dev = format(random.randint(10000000, 99999999), "x") + format(int(time.time() * 1000), "x")

    # ---------- PoW (FNV-1a, ported from the JS) ----------
    def _hp_hash(self, s):
        h = 0x811C9DC5
        for ch in str(s):
            h ^= ord(ch)
            h = (h * 0x01000193) & 0xFFFFFFFF
        return h

    def _to_hex8(self, n):
        return format(n & 0xFFFFFFFF, "08x")[-8:]

    def _hp_pow(self, chal, nonce):
        h = self._hp_hash(str(chal) + ":" + str(nonce))
        for _ in range(4):
            h = self._hp_hash(self._to_hex8(h) + str(chal))
        return self._to_hex8(h)

    def _hp_solve(self, chal, bits=16):
        want = "0" * (int(bits) >> 2)
        n = 0
        while n < 2000000:
            nx = format(n, "x")
            if self._hp_pow(chal, nx).startswith(want):
                return str(chal) + "." + nx
            n += 1
        return ""

    # ---------- transport ----------
    def _fetch_json(self, url, headers):
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    status = resp.status
                    raw = resp.read()
                text = raw.decode("utf-8", "replace") if raw else ""
                try:
                    return status, json.loads(text) if text else {}
                except Exception:
                    return status, {}
            except urllib.error.HTTPError as e:
                try:
                    raw = e.read()
                    text = raw.decode("utf-8", "replace") if raw else ""
                    parsed = json.loads(text) if text else {}
                except Exception:
                    parsed = {}
                return e.code, parsed if isinstance(parsed, dict) else {}
            except Exception:
                pass
            time.sleep(0.5)
        return 0, {}

    def _base_headers(self):
        return {"User-Agent": self.UA, "Referer": self.REFERER, "Accept": "application/json, text/plain, */*"}

    def _handshake(self):
        hs_url = self.SITE + "/api/handshake?dev=" + urllib.parse.quote(self.dev, safe="")
        status, data = self._fetch_json(hs_url, self._base_headers())
        if isinstance(data, dict) and data.get("need_chal"):
            tok = self._hp_solve(str(data["need_chal"]), int(data.get("bits") or 16))
            if not tok:
                return None
            status, data = self._fetch_json(hs_url + "&c=" + urllib.parse.quote(tok, safe=""), self._base_headers())
        if isinstance(data, dict) and data.get("sid") and data.get("skey"):
            try:
                exp = int(data.get("exp") or (int(time.time()) + 7200))
            except Exception:
                exp = int(time.time()) + 7200
            self.auth = {"sid": str(data["sid"]), "skey": str(data["skey"]), "exp": exp}
            return self.auth
        return None

    def _ensure_auth(self):
        now = int(time.time())
        if self.auth and now < self.auth["exp"] - 60:
            return self.auth
        return self._handshake()

    def _build_query(self, params):
        parts = []
        for k, v in params.items():
            if v is not None and str(v) != "":
                parts.append(urllib.parse.quote(str(k), safe="-_.!~*'()") + "=" + urllib.parse.quote(str(v), safe="-_.!~*'()"))
        return "&".join(parts)

    def _signed(self, path, params, retried=False):
        query = self._build_query(params)
        full_url = self.SITE + path + (("?" + query) if query else "")
        auth = self._ensure_auth()
        if not auth:
            status, data = self._fetch_json(full_url, {"User-Agent": self.UA, "Referer": self.REFERER})
            return data if isinstance(data, dict) else {}
        ts = str(int(time.time()))
        nonce = format(random.randint(100000, 999999), "x") + format(int(time.time() * 1000), "x")
        body_hash = hashlib.sha256(b"").hexdigest()
        canon = "GET\n" + path + "\n" + query + "\n" + body_hash + "\n" + ts + "\n" + nonce + "\n" + auth["sid"]
        try:
            key_bytes = bytes.fromhex(auth["skey"])
        except Exception:
            key_bytes = auth["skey"].encode("utf-8")
        sig = hmac_lib.new(key_bytes, canon.encode("utf-8"), hashlib.sha256).hexdigest()
        headers = self._base_headers()
        headers["X-Hp-Sid"] = auth["sid"]
        headers["X-Hp-Ts"] = ts
        headers["X-Hp-Nonce"] = nonce
        headers["X-Hp-Sign"] = sig
        status, data = self._fetch_json(full_url, headers)
        if status == 401 and not retried:
            self.auth = None
            if self._handshake():
                return self._signed(path, params, retried=True)
        return data if isinstance(data, dict) else {}

    # ---------- covers ----------
    def _format_cover(self, mod, raw_url):
        if not raw_url:
            return ""
        pic = str(raw_url).strip()
        if mod == "live" or pic.startswith("/") or not (pic.startswith("http://") or pic.startswith("https://")):
            if pic.startswith("/"):
                pic = self.SITE + pic
        else:
            pic = self.SITE + "/cover/" + mod + "?u=" + urllib.parse.quote(pic, safe="")
        return pic

    def _ratio(self, mod):
        return 0.75 if mod in self.PORTRAIT_MODS else 1.49

    def _card(self, tid, item_id, src, item):
        title = str(item.get("title") or item_id).strip()
        cover_mod = src if tid in self.DRAMA_MODS else tid
        poster = self._format_cover(cover_mod, item.get("cover_n") or item.get("cover") or "")
        remark = str(item.get("remark") or item.get("desc") or "").strip()
        return {
            "vod_id": tid + "@@" + item_id + "@@" + src,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": ("蝴蝶影视 | " + remark) if remark else "蝴蝶影视",
            "style": {"type": "rect", "ratio": self._ratio(tid)},
        }

    def _items_from(self, tid, src, data):
        out = []
        raw_list = data.get("list") if isinstance(data, dict) and isinstance(data.get("list"), list) else []
        for item in raw_list:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or item.get("code") or "")
            if not item_id:
                continue
            out.append(self._card(tid, item_id, src, item))
        return out

    # ---------- entries ----------
    def homeContent(self, filter=False):
        classes = [{"type_id": cid, "type_name": name} for cid, name, _ in self.CATEGORIES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, name, rows in self.CATEGORIES:
                if rows:
                    filters[cid] = [{"key": k, "name": n, "value": [{"n": vn, "v": vv} for vv, vn in opts]} for k, n, opts in rows]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        return {"list": self._category_items("video", 1, {})}

    def _category_query(self, tid, page, ext):
        cat = str(ext.get("cat") or "")
        sub = str(ext.get("sub")) if ext.get("sub") is not None else ""
        q = {"key": tid, "page": page}
        src = "huangdou"
        if tid == "duanju":
            cat_val = cat or "huangtao"
            src = self.SRC_MAP.get(cat_val, "duoju86")
            q["cat"] = cat_val
            q["src"] = src
            q["sub"] = sub if sub != "" else 0
        elif tid == "hongtao":
            cat_val = cat or "zhenren"
            src = self.SRC_MAP.get(cat_val, "huangdou")
            q["cat"] = cat_val
            q["src"] = src
            q["sub"] = (sub if sub != "" else 0) if cat_val == "zhenren" else 0
        elif tid == "hbo":
            cat_val = cat or "meiju"
            src = "huangdou"
            q["cat"] = cat_val
            q["src"] = src
            q["sub"] = 0
        elif tid == "caibian":
            cat_val = cat or "0"
            src = "huangdou"
            q["cat"] = cat_val
            q["src"] = src
            q["nav"] = "caibian"
            q["sub"] = cat_val
        elif tid == "guochan":
            src = "guochan"
            q["src"] = src
        elif tid == "video":
            src = "missav"
            q["src"] = src
            if cat:
                q["cat"] = cat
        elif tid == "shortv":
            src = "dongman"
            q["src"] = src
            if cat:
                q["cat"] = cat
        else:
            if cat:
                q["cat"] = cat
        return q, src

    def _category_items(self, tid, page, ext):
        q, src = self._category_query(tid, page, ext)
        data = self._signed("/api/module", q)
        return self._items_from(tid, src, data)

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        ext = extend if isinstance(extend, dict) else {}
        items = self._category_items(str(tid or "video"), page, ext)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        keyword = str(key or "")
        items = []
        for mod in ["video", "duanju", "hongtao", "hbo", "shortv", "guochan", "caibian"]:
            data = self._signed("/api/search", {"key": mod, "kw": keyword, "page": page})
            raw_list = data.get("list") if isinstance(data, dict) and isinstance(data.get("list"), list) else []
            for item in raw_list:
                if not isinstance(item, dict):
                    continue
                item_id = str(item.get("id") or item.get("code") or "")
                if not item_id:
                    continue
                item_src = str(item.get("src") or mod)
                items.append(self._card(mod, item_id, item_src, item))
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        raw_id = str(ids[0] or "")
        parts = raw_id.split("@@")
        mod = parts[0] if len(parts) > 0 and parts[0] else "video"
        real_id = parts[1] if len(parts) > 1 and parts[1] else raw_id
        src = parts[2] if len(parts) > 2 else ""
        params = {"src": src} if src else {}
        data = self._signed("/api/detail/" + mod + "/" + urllib.parse.quote(real_id, safe=""), params)
        det = data.get("detail") if isinstance(data, dict) and isinstance(data.get("detail"), dict) else {}
        title = str(det.get("title") or real_id).strip()
        cover_mod = src if mod in self.DRAMA_MODS else mod
        poster = self._format_cover(cover_mod, det.get("cover") or "")
        desc = str(det.get("desc") or "").strip()
        episodes = []
        raw_eps = det.get("episodes") if isinstance(det.get("episodes"), list) else []
        if raw_eps:
            for ep_item in raw_eps:
                if not isinstance(ep_item, dict):
                    continue
                ep_no = str(ep_item.get("ep") if ep_item.get("ep") is not None else "1")
                ep_name = str(ep_item.get("name") or ("第" + ep_no + "集"))
                if re.fullmatch(r"\d+", ep_name):
                    ep_name = "第" + ep_name + "集"
                if ep_item.get("lock"):
                    ep_name += "[预告10s]"
                val = json.dumps({"mod": mod, "realId": real_id, "ep": ep_no, "src": src}, ensure_ascii=False)
                episodes.append(ep_name + "$" + val)
        else:
            val = json.dumps({"mod": mod, "realId": real_id, "ep": "1", "src": src}, ensure_ascii=False)
            episodes.append("正片$" + val)
        lines = [
            "🦋 暗夜蜜桃官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.SITE,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        else:
            lines.append("标题：" + title)
            lines.append("片源：蜜桃专线")
            lines.append("编号：" + real_id)
        vod = {
            "vod_id": raw_id,
            "vod_name": title,
            "vod_pic": poster,
            "vod_remarks": "蝴蝶影视",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "蜜桃专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": self._ratio(mod)},
        }
        if det.get("date"):
            vod["vod_year"] = str(det.get("date"))[:4]
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        mod, real_id, ep, src = "video", "", "1", ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                mod = str(data.get("mod") or "video")
                real_id = str(data.get("realId") or "")
                ep = str(data.get("ep") or "1")
                src = str(data.get("src") or "")
        except Exception:
            pass
        headers = {"User-Agent": self.UA, "Referer": self.REFERER}
        if not real_id:
            return {"parse": 1, "playUrl": "", "url": "", "header": headers}
        params = {"src": src} if src else {}
        data = self._signed("/api/play/" + mod + "/" + urllib.parse.quote(real_id, safe="") + "/" + ep, params)
        pl = data.get("play") if isinstance(data, dict) and isinstance(data.get("play"), dict) else {}
        raw_src = str(pl.get("src") or "")
        raw_proxy = str(pl.get("src_proxy") or "")
        if "preview-r10" in raw_src and raw_proxy:
            chosen = raw_proxy
        else:
            chosen = raw_src or raw_proxy
        final_url = ""
        if chosen:
            final_url = (self.SITE + chosen) if chosen.startswith("/") else chosen
        if final_url:
            lower = final_url.lower()
            if ".m3u8" not in lower and ".mp4" not in lower and ".mpd" not in lower:
                final_url += ("&" if "?" in final_url else "?") + "format=.m3u8"
            if "hembed.com" in final_url or "hanime" in final_url:
                headers["Referer"] = "https://hanime1.me/"
            return {"parse": 0, "playUrl": "", "url": final_url, "header": headers}
        return {"parse": 1, "playUrl": "", "url": "", "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249492260&sig=15bd43e0b79d6f39
