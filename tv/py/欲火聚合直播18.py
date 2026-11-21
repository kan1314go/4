# 欲火聚合直播 FongMi 爬虫（由 Hamo 插件 com.butterfly.yuhuo v1.0.3 转换）
# 直播聚合源：双主站竞速、平台房间列表、连刷聚合频道，流地址原样直出
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import quote

import requests
from base.spider import Spider as BaseSpider

HOSTS = ["http://api.maiyoux.com:81/mf", "http://api.vipmisss.com:81/xcdsw"]
DEFAULT_HOST = HOSTS[0]
UA = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36"
PROBE_PATH = "/json.txt"
PAGE_SIZE = 60
CAT_LIMIT = 98
OVERFLOW_ID = "__more__"
BRAND_NAME = "蝴蝶影视"
HOST_FAIL_TTL = 600
PLAT_CACHE_TTL = 600
COVER_CACHE_TTL = 600
PROBE_TIMEOUT = 6
FETCH_TIMEOUT = 8
FEED_LIMIT = 48

PLATFORMS_SNAPSHOT = [["jsonkawayi.txt", "卡哇伊"], ["jsonmihu.txt", "咪狐"], ["jsonhuahudie.txt", "花蝴蝶"], ["jsonmitao.txt", "蜜桃"], ["jsonfanjiashequ.txt", "番茄社区"], ["jsonLOVE.txt", "LOVE"], ["jsonxiaodaji.txt", "小妲己"], ["json77zhibo.txt", "77直播"], ["jsonyiyi.txt", "依依"], ["jsonrichu.txt", "日出"], ["jsoncaihong.txt", "彩虹"], ["jsonjiujiu.txt", "久久"], ["jsonyami.txt", "亚米"], ["jsondielian.txt", "蝶恋"], ["jsonyeyaoji.txt", "夜妖姬"], ["jsontaolu.txt", "套路"], ["jsonyinghua.txt", "樱花"], ["jsonxiangse.txt", "享色"], ["jsonhonglangman.txt", "红浪漫"], ["jsonjinyu.txt", "金鱼"], ["jsontaohua.txt", "桃花"], ["jsonhuafang.txt", "花房"], ["jsonxiaoxiannu.txt", "小仙女"], ["jsonshijuexiu.txt", "视觉秀"], ["jsonxiaotianshi.txt", "小天使"], ["jsonyizhibo.txt", "一直播"], ["jsoncaiyun.txt", "彩云"], ["jsonanyu.txt", "暗语"], ["jsonmimi.txt", "咪咪"], ["jsonjiaomei.txt", "娇媚"], ["jsonhuanggua.txt", "黄瓜"], ["jsonsequ.txt", "色趣"], ["jsonnuomi.txt", "糯米"], ["jsonxiaomifeng.txt", "小蜜蜂"], ["jsonxiaohongmao.txt", "小红帽"], ["jsontaohuayun.txt", "桃花运"], ["jsonkugua.txt", "苦瓜"], ["jsonaiaini.txt", "爱爱你"], ["jsonyinghuayui.txt", "樱花雨i"], ["jsonpanta.txt", "盘他"], ["jsonyese.txt", "夜色"], ["jsonhudie.txt", "蝴蝶"], ["jsonxiaotianxian.txt", "小天仙"], ["jsonxingqu.txt", "杏趣"], ["jsonxiaohuaidan.txt", "小坏蛋"], ["jsonpiaoxue.txt", "飘雪"], ["jsonyingtao.txt", "樱桃"], ["jsonaosika.txt", "奥斯卡"], ["jsonkaluli.txt", "卡路里"], ["jsonhonggaoliang.txt", "红高粱"], ["jsonfubao.txt", "付宝"], ["jsonxiaohuangshu.txt", "小黄书"], ["jsonersao.txt", "二嫂"], ["jsonhuaguoshan.txt", "花果山"], ["jsonyunlu.txt", "云鹿"], ["jsonboluo.txt", "菠萝"], ["jsonxingbaobei.txt", "星宝贝"], ["jsonyeyan.txt", "夜艳"], ["jsonqixiannus.txt", "七仙女s"], ["jsonyelaixiang.txt", "夜来香"], ["jsonailing.txt", "爱零"], ["jsonshibajin.txt", "十八禁"], ["jsonlanguifang.txt", "兰桂坊"], ["jsonDancelife.txt", "Dancelife"], ["jsonxiaomengzhu.txt", "小萌猪"], ["jsonhudiefei.txt", "蝴蝶飞"], ["jsonyoumeng.txt", "幽梦"], ["jsonliguiting.txt", "丽柜厅"], ["jsonjiaolong.txt", "蛟龙"], ["jsonyanruyu.txt", "颜如玉"], ["jsonchengxiu.txt", "橙秀"], ["jsonbaoyul.txt", "豹娱l"], ["jsonxiaohualuo.txt", "小花螺"], ["jsonhuanghou.txt", "皇后"], ["jsonxinzhilian.txt", "心之恋"], ["jsontaimeil.txt", "台妹l"], ["jsonailian.txt", "爱恋"], ["json903yule.txt", "903娱乐"], ["jsonjiuweihu.txt", "九尾狐"], ["jsonyouwudao.txt", "尤物岛"], ["jsontanke.txt", "坦克"], ["jsonhaojiyou.txt", "好基友"], ["jsonyenulang.txt", "夜女郎"], ["jsonjiaochuan.txt", "娇喘"], ["jsonmangguopai.txt", "芒果派"], ["jsonmeiyan.txt", "媚颜"], ["jsonfengliu.txt", "风流"], ["jsonyelu.txt", "夜律"], ["jsonlinglong.txt", "玲珑"], ["jsonyuhuo.txt", "浴火"], ["jsoncuiniao.txt", "翠鸟"], ["jsonxingyunxing.txt", "幸运星"], ["jsontaxiu.txt", "她秀"], ["jsonzhaocaimao.txt", "招财猫"], ["jsonshuangdie.txt", "双碟"], ["jsontangguo.txt", "糖果"], ["jsonmemeda.txt", "么么哒"], ["jsonxiaoxinggan.txt", "小性感"], ["jsonxiaomiaochong.txt", "小喵宠"], ["jsontunulang.txt", "兔女郎"], ["jsonshuimeiren.txt", "睡美人"], ["jsonjinbei.txt", "金呗"], ["jsonmeixi.txt", "美夕"], ["jsonxiaoyao.txt", "小妖"], ["jsonyuezhibo.txt", "约直播"], ["jsonhuaxianzi.txt", "花仙子"], ["jsontuhao.txt", "土豪"], ["jsonhongzhuang.txt", "红妆"], ["jsonniuniu.txt", "妞妞"], ["jsonyanhou.txt", "艳后"], ["jsonmoon.txt", "moon"], ["jsonlanmao.txt", "蓝猫"], ["jsonmeirenzhuang.txt", "美人妆"], ["jsonruxiang.txt", "入巷"], ["jsonchijiunan.txt", "持久男"], ["jsonqingxin.txt", "倾心"], ["jsonxiaojingling.txt", "小精灵"], ["jsonouyu.txt", "偶遇"], ["jsonhuihui.txt", "灰灰"], ["jsonmaotouying.txt", "猫头鹰"], ["jsonxihuanni.txt", "喜欢你"], ["jsonyechun.txt", "夜纯"], ["jsonxingbo.txt", "杏播"], ["jsonmingliu.txt", "名流"], ["jsonxiaolajiao.txt", "小辣椒"], ["jsonwenxiangshe.txt", "蚊香社"], ["jsonqianshou.txt", "牵手"], ["jsonqingqu.txt", "情趣"], ["jsonlanyueliang.txt", "蓝月亮"], ["jsonxiaomianao.txt", "小棉袄"]]


def _svg_cover(title, sub, c1, c2):
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="600" height="340" viewBox="0 0 600 340">'
           '<defs>'
           '<linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">'
           '<stop offset="0%" stop-color="' + c1 + '" />'
           '<stop offset="100%" stop-color="' + c2 + '" />'
           '</linearGradient>'
           '</defs>'
           '<rect width="100%" height="100%" fill="url(#g)" />'
           '<circle cx="300" cy="130" r="46" fill="rgba(255,255,255,0.18)" />'
           '<polygon points="288,110 322,130 288,150" fill="#ffffff" />'
           '<text x="50%" y="225" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="28" font-weight="bold" fill="#ffffff" text-anchor="middle">' + title + '</text>'
           '<text x="50%" y="265" font-family="-apple-system,BlinkMacSystemFont,PingFang SC,sans-serif" font-size="16" fill="rgba(255,255,255,0.85)" text-anchor="middle">' + sub + '</text>'
           '</svg>')
    return "data:image/svg+xml;utf8," + quote(svg, safe="-_.!~*'()")


FEED_CHANNELS = [
    {
        "id": "feed_hot",
        "name": "🔥 全网聚合·热门直播连刷",
        "fallback": _svg_cover("热门聚合连刷", "欲火聚合 · 自动连续切台", "#ff0844", "#ffb199"),
    },
    {
        "id": "feed_top_platforms",
        "name": "✨ 精选大台·多平台全连刷",
        "fallback": _svg_cover("精选大台连刷", "欲火聚合 · 汇聚精选主播", "#6a11cb", "#2575fc"),
    },
]

ACTORS_TEXT = "🦋 TG交流群,🌐 官方发布频道,🚀 官方自愈节点"
ROOM_GENRES = "欲火聚合,在线直播,高清秒播"
FEED_GENRES = "📺 连刷直通车,🦋 蝴蝶专属,欲火聚合"


def _origin_of(u):
    m = re.match(r"^(https?://[^/]+)", str(u or ""), re.I)
    return m.group(1) if m else ""


def _stem(u):
    return str(u or "").split("#", 1)[0].split("?", 1)[0]


def _clean_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        self._custom_host = ""
        self._host_winner = ""
        self._host_fail_at = 0.0
        self._plats = None
        self._plats_at = 0.0
        self._cover_cache = {}

    def init(self, extend=""):
        custom = ""
        if extend:
            try:
                obj = json.loads(extend)
                if isinstance(obj, dict):
                    custom = str(obj.get("host") or "").strip()
            except Exception:
                s = str(extend).strip()
                if s.startswith("http"):
                    custom = s
        if custom and custom.startswith("http"):
            self._custom_host = custom.rstrip("/")

    def getName(self):
        return "欲火聚合直播"

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

    # ---- host selection (JS getActiveHost / raceHosts port) ----
    def _probe_host(self, host):
        try:
            resp = requests.get(host + PROBE_PATH,
                                headers={"User-Agent": UA},
                                timeout=PROBE_TIMEOUT)
            if 200 <= resp.status_code < 400 and "pingtai" in (resp.text or ""):
                return host
        except Exception:
            pass
        return None

    def _pick_fastest(self):
        if self._host_fail_at and time.time() - self._host_fail_at < HOST_FAIL_TTL:
            return None
        winner = None
        seen = set()
        for h in HOSTS:
            hh = str(h or "").strip().rstrip("/")
            if not hh or not re.match(r"^https?://", hh, re.I) or hh in seen:
                continue
            seen.add(hh)
            winner = self._probe_host(hh)
            if winner:
                break
        if winner:
            self._host_winner = winner
            return winner
        self._host_fail_at = time.time()
        return None

    def _active_host(self):
        if self._custom_host:
            return self._custom_host
        if self._host_winner:
            return self._host_winner
        return self._pick_fastest() or DEFAULT_HOST

    def _clear_cached_host(self, host):
        if self._host_winner and self._host_winner.rstrip("/") == host:
            self._host_winner = ""

    # ---- transport (JS fetchRaw / fetchJson port) ----
    def _fetch_text(self, full_url, retry=True):
        headers = {
            "User-Agent": UA,
            "Referer": (_origin_of(full_url) or self._active_host()) + "/",
            "Accept": "application/json,*/*;q=0.8",
        }
        try:
            resp = requests.get(full_url, headers=headers, timeout=FETCH_TIMEOUT)
            if resp.status_code >= 400:
                raise Exception("HTTP {0} {1}".format(resp.status_code, full_url))
            return resp.text or ""
        except Exception:
            if not retry:
                raise
            base = None
            for h in HOSTS:
                hh = h.rstrip("/")
                if full_url.startswith(hh):
                    base = hh
                    break
            if base:
                self._clear_cached_host(base)
                winner = self._pick_fastest()
                if winner and winner != base:
                    return self._fetch_text(winner + full_url[len(base):], retry=False)
            raise

    def _fetch_json(self, path):
        host = self._active_host()
        if re.match(r"^https?://", str(path), re.I):
            url = str(path)
        else:
            p = str(path)
            url = host + (p if p.startswith("/") else "/" + p)
        text = self._fetch_text(url)
        try:
            return json.loads(text)
        except Exception:
            raise Exception("JSON parse fail " + url)

    def _abs_url(self, u, host):
        u = str(u or "").strip().replace("\\/", "/")
        if not u:
            return ""
        if u.startswith("http"):
            return u
        if u.startswith("//"):
            return "http:" + u
        if u.startswith("/"):
            return host + u
        return host + "/" + u

    # ---- data (JS platforms / rooms port) ----
    def _platforms(self):
        now = time.time()
        if self._plats is not None and now - self._plats_at < PLAT_CACHE_TTL:
            return self._plats
        host = self._active_host()
        data = self._fetch_json(PROBE_PATH)
        out = []
        for p in (data or {}).get("pingtai") or []:
            if p and p.get("address") and p.get("title"):
                out.append({
                    "addr": re.sub(r"^/+", "", str(p["address"])),
                    "title": str(p["title"]),
                    "pic": self._abs_url(str(p.get("xinimg") or p.get("img") or ""), host),
                    "number": str(p.get("Number") or ""),
                })
        if out:
            self._plats = out
            self._plats_at = now
        return out

    def _rooms(self, platform_addr):
        target = platform_addr if platform_addr.startswith("/") else "/" + platform_addr
        data = self._fetch_json(target)
        host = self._active_host()
        out = []
        for r in (data or {}).get("zhubo") or []:
            if r and r.get("address"):
                addr = str(r["address"]).strip()
                if not addr or re.search(r"rtmp", addr, re.I):
                    continue
                out.append({
                    "addr": addr,
                    "title": str(r.get("title") or "直播"),
                    "pic": self._abs_url(str(r.get("img") or ""), host),
                })
        return out

    def _rooms_safe(self, platform_addr):
        try:
            return self._rooms(platform_addr)
        except Exception:
            return []

    def _rooms_parallel(self, addrs):
        if not addrs:
            return []
        results = [None] * len(addrs)
        with ThreadPoolExecutor(max_workers=min(8, len(addrs))) as ex:
            futs = dict((ex.submit(self._rooms, a), i) for i, a in enumerate(addrs))
            for fut, i in futs.items():
                try:
                    results[i] = fut.result()
                except Exception:
                    results[i] = None
        return results

    # ---- cards ----
    def _room_card(self, platform_addr, r):
        return {
            "vod_id": platform_addr + "@@" + r["addr"],
            "vod_name": r["title"],
            "vod_pic": r["pic"],
            "vod_remarks": BRAND_NAME + " | 直播中",
        }

    def _feed_cards(self):
        plats = self._platforms()
        cards = []
        for f, ch in enumerate(FEED_CHANNELS):
            cover = ""
            try:
                ent = self._cover_cache.get(ch["id"])
                if ent and time.time() - ent[1] < COVER_CACHE_TTL:
                    cover = ent[0]
                if not cover and plats:
                    target = plats[0] if f == 0 else (plats[1] if len(plats) > 1 else plats[0])
                    sample = self._rooms(target["addr"])
                    if sample and sample[0]["pic"]:
                        cover = sample[0]["pic"]
                        self._cover_cache[ch["id"]] = (cover, time.time())
            except Exception:
                cover = cover or ""
            cards.append({
                "vod_id": ch["id"],
                "vod_name": ch["name"],
                "vod_pic": cover or ch["fallback"],
                "vod_remarks": BRAND_NAME + " | 自动切台",
            })
        return cards

    def _page_form(self, items, page, total):
        pagecount = (total + PAGE_SIZE - 1) // PAGE_SIZE if total > 0 else page
        return {"list": items, "page": page, "pagecount": pagecount,
                "limit": PAGE_SIZE, "total": total}

    def _empty_page(self, page):
        return {"list": [], "page": page, "pagecount": page,
                "limit": PAGE_SIZE, "total": 0}

    # ---- container entries ----
    def homeContent(self, filter):
        classes = [{"type_id": "continuous_feed", "type_name": "📺 连刷模式"}]
        for addr, title in PLATFORMS_SNAPSHOT[:CAT_LIMIT]:
            classes.append({"type_id": addr, "type_name": title})
        if len(PLATFORMS_SNAPSHOT) > CAT_LIMIT:
            classes.append({"type_id": OVERFLOW_ID, "type_name": "更多平台"})
        return {"class": classes}

    def homeVideoContent(self):
        try:
            return {"list": self._feed_cards()}
        except Exception:
            return {"list": []}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        cid = str(tid or "continuous_feed")
        if cid == "continuous_feed":
            if page > 1:
                return self._empty_page(page)
            try:
                cards = self._feed_cards()
            except Exception:
                return self._empty_page(page)
            return self._page_form(cards, page, len(cards))
        if cid == OVERFLOW_ID:
            try:
                plats = self._platforms()
            except Exception:
                return self._empty_page(page)
            rest = plats[CAT_LIMIT:]
            all_items = []
            for i in range(0, len(rest), 8):
                batch = rest[i:i + 8]
                results = self._rooms_parallel([p["addr"] for p in batch])
                for p, rs in zip(batch, results):
                    if rs is None:
                        continue
                    for r in rs:
                        all_items.append(self._room_card(p["addr"], r))
            start = (page - 1) * PAGE_SIZE
            return self._page_form(all_items[start:start + PAGE_SIZE], page, len(all_items))
        try:
            rs = self._rooms(cid)
        except Exception:
            return self._empty_page(page)
        all_items = [self._room_card(cid, r) for r in rs]
        start = (page - 1) * PAGE_SIZE
        return self._page_form(all_items[start:start + PAGE_SIZE], page, len(all_items))

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page > 1:
            return self._empty_page(page)
        kw = str(key or "").strip().lower()
        if not kw:
            return self._empty_page(page)
        try:
            plats = self._platforms()
        except Exception:
            return self._empty_page(page)
        hits = []
        seen = set()

        def add(p, r):
            k = p["addr"] + "@@" + r["addr"]
            if k in seen or len(hits) >= 60:
                return
            seen.add(k)
            hits.append(self._room_card(p["addr"], r))

        matched = [p for p in plats if kw in p["title"].lower()]
        rest = [p for p in plats if p not in matched]
        for p in matched:
            try:
                for r in self._rooms(p["addr"]):
                    add(p, r)
            except Exception:
                pass
            if len(hits) >= 60:
                return {"list": hits, "page": page, "pagecount": 1,
                        "limit": PAGE_SIZE, "total": len(hits)}
        for i in range(0, len(rest), 8):
            if len(hits) >= 60:
                break
            batch = rest[i:i + 8]
            results = self._rooms_parallel([p["addr"] for p in batch])
            for p, rs in zip(batch, results):
                if rs is None:
                    continue
                for r in rs:
                    if kw in r["title"].lower():
                        add(p, r)
        return {"list": hits, "page": page, "pagecount": 1,
                "limit": PAGE_SIZE, "total": len(hits)}

    # ---- detail ----
    def _brand_block(self, host):
        return ("🦋 欲火聚合直播官方交流群：@tvshare23\n"
                "导演：🦋 蝴蝶影视\n"
                "当前主站：" + host + "\n"
                + "━" * 28 + "\n"
                + "━" * 7)

    def _envelope(self, play_url, title, pic):
        return json.dumps({"playUrl": play_url, "title": title, "pic": pic},
                          ensure_ascii=False)

    def _detail_feed(self, vid):
        host = self._active_host()
        ch = FEED_CHANNELS[0]
        for c in FEED_CHANNELS:
            if c["id"] == vid:
                ch = c
                break
        plats = self._platforms()
        targets = plats[0:4] if vid == "feed_hot" else plats[4:9]
        if len(targets) == 0:
            targets = plats[0:3]
        results = self._rooms_parallel([p["addr"] for p in targets])
        all_rooms = []
        for rs in results:
            if rs:
                all_rooms.extend(rs)
        episodes = []
        seen = set()
        idx = 1
        for room in all_rooms:
            if not room or not room["addr"] or room["addr"] in seen:
                continue
            seen.add(room["addr"])
            name = _clean_name("{0}. {1}".format(idx, room["title"]))
            episodes.append((name, self._envelope(room["addr"], room["title"], room["pic"]),
                             room["pic"]))
            idx += 1
        if not episodes:
            episodes.append((_clean_name("暂无在线主播"),
                              self._envelope("", "无信号", ""), ""))
        n = len(episodes)
        body = "【连刷功能提示】在播放器中开启“自动连播”或直接手势上下划动选集，即可秒速无缝切台！"
        vod = {
            "vod_id": vid,
            "vod_name": ch["name"],
            "vod_pic": episodes[0][2] or ch["fallback"],
            "vod_class": FEED_GENRES,
            "vod_actor": ACTORS_TEXT,
            "vod_remarks": BRAND_NAME + " | 共" + str(n) + "位在线",
            "vod_content": self._brand_block(host) + "\n" + body,
            "vod_play_from": "🦋 连续刷流专线",
            "vod_play_url": "#".join("{0}${1}".format(nm, env) for nm, env, _ in episodes),
        }
        for k in ("vod_bg", "vod_background", "vod_banner"):
            vod[k] = vod["vod_pic"]
        return {"list": [vod]}

    def _detail_room(self, vid):
        host = self._active_host()
        cut = vid.find("@@")
        platform = vid[:cut] if cut >= 0 else ""
        room_addr = vid[cut + 2:] if cut >= 0 else vid
        rs = []
        if platform:
            rs = self._rooms_safe(platform)
        idx = -1
        for i, r in enumerate(rs):
            if r["addr"] == room_addr:
                idx = i
                break
        if idx < 0:
            for i, r in enumerate(rs):
                if _stem(r["addr"]) == _stem(room_addr):
                    idx = i
                    break
        if idx >= 0:
            queue = (rs[idx:] + rs[:idx])[:FEED_LIMIT]
        elif rs:
            queue = rs[:FEED_LIMIT]
        else:
            queue = [{"addr": room_addr, "title": "直播", "pic": ""}]
        first = queue[0]
        play_url = "#".join(
            "{0}${1}".format(_clean_name(r["title"]),
                             self._envelope(r["addr"], r["title"], r["pic"]))
            for r in queue)
        body = ("主播名: " + (first["title"] or "直播") + "\n"
                "房间状态: 正在公开直播中\n"
                "如遇卡顿可在右上角切换主站节点。")
        vod = {
            "vod_id": vid,
            "vod_name": first["title"] or "直播",
            "vod_pic": first["pic"] or "",
            "vod_class": ROOM_GENRES,
            "vod_actor": ACTORS_TEXT,
            "vod_remarks": BRAND_NAME + " | 直播中",
            "vod_content": self._brand_block(host) + "\n" + body,
            "vod_play_from": "🦋 蝴蝶超清专线",
            "vod_play_url": play_url,
        }
        for k in ("vod_bg", "vod_background", "vod_banner"):
            vod[k] = vod["vod_pic"]
        return {"list": [vod]}

    def detailContent(self, ids):
        vid = str(ids[0]) if isinstance(ids, (list, tuple)) and ids else str(ids or "")
        if vid.startswith("feed_"):
            try:
                return self._detail_feed(vid)
            except Exception as e:
                return {"list": [], "msg": str(e)}
        return self._detail_room(vid)

    def playerContent(self, flag, id, vipFlags):
        play_url = ""
        raw = str(id or "")
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                play_url = str(obj.get("playUrl") or "")
            else:
                play_url = raw
        except Exception:
            play_url = raw
        if not play_url:
            return {"parse": 0, "msg": "直播信号已离线或流解析失败"}
        host = self._active_host()
        return {
            "parse": 0,
            "url": play_url,
            "header": {"User-Agent": UA, "Referer": _origin_of(host) + "/"},
        }

    def localProxy(self, param):
        return None

    def liveContent(self, url):
        return ""

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249933481&sig=74bd923bb8a4d09b
