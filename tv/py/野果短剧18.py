# -*- coding: utf-8 -*-
# 野果短剧 蜘蛛（源自 Hamo 插件 com.butterfly.yeguoduanju 的接口逻辑移植）
import base64
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


_AES_SBOX = (
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
    0x8c,0xa1,0x89,0x0d,0xbf,0xe6,0x42,0x68,0x41,0x99,0x2d,0x0f,0xb0,0x54,0xbb,0x16
)
_AES_INV = [0] * 256
for _i, _v in enumerate(_AES_SBOX):
    _AES_INV[_v] = _i
_AES_RCON = (0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36)


def _aes_xtime(x):
    return ((x << 1) ^ (0x1b if x & 0x80 else 0)) & 0xff


def _aes_gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = _aes_xtime(a)
        b >>= 1
    return r


def _aes_expand_key(key):
    w = list(key)
    r = 0
    while len(w) < 176:
        t = w[-4:]
        if len(w) % 16 == 0:
            t = [_AES_SBOX[t[1]] ^ _AES_RCON[r], _AES_SBOX[t[2]], _AES_SBOX[t[3]], _AES_SBOX[t[0]]]
            r += 1
        for i in range(4):
            w.append(w[-16] ^ t[i])
    return w


def _aes_decrypt_block(w, block):
    s = [block[i] ^ w[160 + i] for i in range(16)]
    for rnd in range(9, 0, -1):
        t = [0] * 16
        for row in range(4):
            for col in range(4):
                t[col * 4 + row] = s[((col - row) % 4) * 4 + row]
        s = [_AES_INV[b] for b in t]
        s = [s[i] ^ w[rnd * 16 + i] for i in range(16)]
        o = [0] * 16
        for col in range(4):
            a0, a1, a2, a3 = s[col * 4], s[col * 4 + 1], s[col * 4 + 2], s[col * 4 + 3]
            o[col * 4] = _aes_gmul(a0, 14) ^ _aes_gmul(a1, 11) ^ _aes_gmul(a2, 13) ^ _aes_gmul(a3, 9)
            o[col * 4 + 1] = _aes_gmul(a0, 9) ^ _aes_gmul(a1, 14) ^ _aes_gmul(a2, 11) ^ _aes_gmul(a3, 13)
            o[col * 4 + 2] = _aes_gmul(a0, 13) ^ _aes_gmul(a1, 9) ^ _aes_gmul(a2, 14) ^ _aes_gmul(a3, 11)
            o[col * 4 + 3] = _aes_gmul(a0, 11) ^ _aes_gmul(a1, 13) ^ _aes_gmul(a2, 9) ^ _aes_gmul(a3, 14)
        s = o
    t = [0] * 16
    for row in range(4):
        for col in range(4):
            t[col * 4 + row] = s[((col - row) % 4) * 4 + row]
    s = [_AES_INV[b] for b in t]
    s = [s[i] ^ w[i] for i in range(16)]
    return bytes(s)


def _aes_cbc_decrypt(key_str, iv_str, cipher_b64):
    try:
        key = key_str.encode("utf-8")
        iv = iv_str.encode("utf-8")
        data = base64.b64decode(cipher_b64)
        if not data or len(data) % 16 != 0:
            return ""
        w = _aes_expand_key(key)
        out = bytearray()
        prev = iv
        for i in range(0, len(data), 16):
            blk = data[i:i + 16]
            dec = _aes_decrypt_block(w, blk)
            out += bytes(dec[j] ^ prev[j] for j in range(16))
            prev = blk
        if out:
            pad = out[-1]
            if 0 < pad <= 16:
                del out[len(out) - pad:]
        return bytes(out).decode("utf-8", "replace")
    except Exception:
        return ""


class Spider(BaseSpider):
    HOST = "https://www.yeguodj.com"
    UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
    PLACEHOLDER = "https://dummyimage.com/600x800/1e293b/ffffff.png&text=NO_COVER"
    COVER_PROXY = "https://huangguo.wulii.de5.net"
    COVER_TOKEN = "hg8f3a2c91b7e04d6a"
    API_KEY = "2acf7e91e9864673"
    API_IV = "1c29882d3ddfcfd6"
    FETCH_LIMIT = 14
    CLASSES = [
        ("explore", "发现"), ("rank", "排行榜"), ("dushi", "都市"), ("xiandai", "现代"),
        ("xiaoyuan", "校园"), ("gudai", "古代"), ("xiangcun", "乡村"), ("zhichang", "职场"),
        ("chongsheng", "重生"), ("chuanyue", "穿越"), ("xitong", "系统"), ("nixi", "逆袭"),
        ("mogai", "魔改"),
    ]
    BG_MAP = {"dushi": 40, "xiandai": 39, "xiaoyuan": 47, "gudai": 41, "xiangcun": 42, "zhichang": 44}
    SETTING_MAP = {"chongsheng": 26, "chuanyue": 27, "xitong": 28, "nixi": 53, "mogai": 56}

    def getName(self):
        return "野果短剧"

    def init(self, extend=""):
        self.host = self.HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")
        self.home_cache = None

    def _headers(self):
        return {
            "User-Agent": self.UA,
            "Referer": self.host + "/",
            "Origin": self.host,
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json;charset=UTF-8",
        }

    def _fetch(self, url, body):
        urls = [url]
        if url.startswith("https://"):
            urls.append("http://" + url[8:])
        data = json.dumps(body or {}).encode("utf-8")
        for u in urls:
            for _ in range(3):
                try:
                    req = urllib.request.Request(u, headers=self._headers(), data=data, method="POST")
                    with urllib.request.urlopen(req, timeout=20) as resp:
                        raw = resp.read()
                    if raw:
                        text = raw.decode("utf-8", "replace")
                        if text.strip():
                            return text
                except Exception:
                    pass
                time.sleep(0.5)
        return ""

    def _api_post(self, path, body):
        text = self._fetch(self.host + "/api.php" + path, body)
        if not text:
            return {}
        try:
            obj = json.loads(text)
        except Exception:
            return {}
        if not isinstance(obj, dict):
            return {}
        data = obj.get("data")
        if isinstance(data, str) and len(data) > 20:
            plain = _aes_cbc_decrypt(self.API_KEY, self.API_IV, data)
            if plain:
                try:
                    obj["data"] = json.loads(plain)
                except Exception:
                    pass
        return obj

    def _unwrap(self, res):
        if not isinstance(res, dict):
            return {}
        x = res.get("data") if res.get("data") is not None else res
        if isinstance(x, dict) and isinstance(x.get("data"), dict):
            return x["data"]
        return x if isinstance(x, dict) else {}

    def _strip_tags(self, text):
        if not text:
            return ""
        s = str(text)
        s = re.sub(r"<[^>]+>", "", s)
        s = s.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
        s = s.replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")
        return re.sub(r"\s+", " ", s).strip()

    def _remarks(self, meta):
        clean = self._strip_tags(meta).replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()
        clean = re.sub(r"\s+", " ", clean)
        if clean:
            return "蝴蝶影视 | " + clean
        return "蝴蝶影视"

    def _pic(self, pic_url):
        p = str(pic_url or "").strip()
        if not p:
            return self.PLACEHOLDER
        if p.startswith("//"):
            p = "https:" + p
        elif p.startswith("/"):
            p = self.host + p
        sep = "&" if "?" in self.COVER_PROXY else "?"
        return (self.COVER_PROXY + sep + "url=" + urllib.parse.quote(p, safe="")
                + "&token=" + urllib.parse.quote(self.COVER_TOKEN, safe=""))

    def _card(self, it):
        if not isinstance(it, dict):
            return None
        raw_id = it.get("video_id") if it.get("video_id") is not None else it.get("id")
        vid = str(raw_id or "").strip()
        if not vid:
            return None
        title = str(it.get("title") or it.get("video_title") or it.get("name") or vid).strip()
        raw_pic = str(it.get("cover") or it.get("cover_img") or it.get("pic") or "").strip()
        ep = it.get("episode_count") or it.get("episodes") or it.get("total_serial") or ""
        remark = str(it.get("update_status") or it.get("serialize_status_text") or "").strip()
        if not remark and ep:
            remark = "更新至" + str(ep) + "集"
        return {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": self._pic(raw_pic),
            "vod_remarks": self._remarks(remark),
            "style": {"type": "rect", "ratio": 0.75},
        }

    def _card_list(self, payload):
        inner = self._unwrap(payload)
        arr = []
        if isinstance(inner, dict):
            if isinstance(inner.get("list"), list):
                arr = inner["list"]
            elif isinstance(inner.get("top_list"), list):
                arr = inner["top_list"]
        out = []
        for it in arr:
            card = self._card(it)
            if card:
                out.append(card)
        return out

    def homeContent(self, filter=False):
        return {"class": [{"type_id": cid, "type_name": name} for cid, name in self.CLASSES]}

    def homeVideoContent(self):
        if self.home_cache is not None:
            return {"list": self.home_cache}
        res = self._api_post("/api/home/homePage", {})
        inner = self._unwrap(res)
        combined = []
        if isinstance(inner, dict):
            if isinstance(inner.get("top_list"), list):
                combined.extend(inner["top_list"])
            mods = inner.get("modules") if isinstance(inner.get("modules"), dict) else {}
            mod_list = mods.get("list") if isinstance(mods.get("list"), list) else []
            for mod in mod_list:
                if isinstance(mod, dict):
                    if isinstance(mod.get("list"), list):
                        combined.extend(mod["list"])
                    elif mod.get("video_id"):
                        combined.append(mod)
        seen = set()
        items = []
        for raw in combined:
            card = self._card(raw)
            if card and card["vod_id"] not in seen:
                seen.add(card["vod_id"])
                items.append(card)
                if len(items) >= self.FETCH_LIMIT:
                    break
        if not items:
            items = self._card_list(self._api_post("/api/theater/exploreList", {"page": 1, "limit": self.FETCH_LIMIT}))
        self.home_cache = items
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        cid = str(tid or "explore")
        if cid == "rank":
            res = self._api_post("/api/theater/videoRank", {"page": page, "limit": self.FETCH_LIMIT})
        elif cid in self.BG_MAP:
            res = self._api_post("/api/theater/exploreList", {"page": page, "limit": self.FETCH_LIMIT, "background": self.BG_MAP[cid]})
        elif cid in self.SETTING_MAP:
            res = self._api_post("/api/theater/exploreList", {"page": page, "limit": self.FETCH_LIMIT, "setting": self.SETTING_MAP[cid]})
        else:
            res = self._api_post("/api/theater/exploreList", {"page": page, "limit": self.FETCH_LIMIT})
        items = self._card_list(res)
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if not str(key or "").strip():
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        res = self._api_post("/api/search/result", {"keyword": str(key), "page": page})
        items = self._card_list(res)
        return {"list": items, "page": page, "pagecount": page, "limit": len(items), "total": len(items)}

    def _vid_value(self, vid):
        if re.match(r"^\d+$", str(vid)):
            return int(vid)
        return vid

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        vid = str(ids[0] or "").strip()
        res = self._api_post("/api/playlet/detail", {"video_id": self._vid_value(vid)})
        info = self._unwrap(res)
        if isinstance(info, dict) and info.get("video_id") is None and isinstance(info.get("data"), dict):
            info = info["data"]
        if not isinstance(info, dict):
            info = {}
        title = str(info.get("title") or info.get("name") or vid).strip()
        raw_pic = str(info.get("cover") or info.get("cover_img") or "").strip()
        raw_desc = str(info.get("description") or info.get("intro") or "").strip()
        eps = info.get("episodes") if isinstance(info.get("episodes"), list) else []
        episodes = []
        if eps:
            for i, ep in enumerate(eps):
                if not isinstance(ep, dict):
                    continue
                ep_no = str(ep.get("sort") or ep.get("episode") or (i + 1)).strip()
                ep_title = str(ep.get("title") or ("第" + ep_no + "集")).strip()
                ep_title = re.sub(r"[$#\r\n\t]+", "", ep_title)
                val = json.dumps({"vid": vid, "ep": ep_no}, ensure_ascii=False)
                episodes.append(ep_title + "$" + val)
        else:
            try:
                total = int(info.get("episode_count") or info.get("total_serial") or 1)
            except Exception:
                total = 1
            for i in range(1, total + 1):
                val = json.dumps({"vid": vid, "ep": str(i)}, ensure_ascii=False)
                episodes.append("第" + str(i) + "集$" + val)
        lines = [
            "🦋 野果短剧官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if raw_desc:
            lines.append(raw_desc)
        else:
            lines.append("标题：" + title)
            lines.append("片源：🦋 野果专线")
            lines.append("编号：" + vid)
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": self._pic(raw_pic),
            "vod_remarks": "蝴蝶影视 | 全" + str(len(episodes)) + "集",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 野果专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.75},
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        vid = ""
        ep = "1"
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                vid = str(data.get("vid") or "")
                ep = str(data.get("ep") or "1")
        except Exception:
            pass
        headers = {"User-Agent": self.UA, "Referer": self.host + "/", "Origin": self.host}
        if not vid:
            return {"parse": 1, "playUrl": "", "url": self.host, "header": headers}
        ep_val = int(ep) if re.match(r"^\d+$", ep) else ep
        res = self._api_post("/api/playlet/play", {"video_id": self._vid_value(vid), "ep": ep_val})
        info = self._unwrap(res)
        if isinstance(info, dict) and not info.get("video_url") and isinstance(info.get("data"), dict):
            info = info["data"]
        if not isinstance(info, dict):
            info = {}
        video_url = ""
        ep_all = info.get("episodeAll")
        if isinstance(ep_all, list) and ep_all:
            for i, item in enumerate(ep_all):
                if not isinstance(item, dict):
                    continue
                item_ep = str(item.get("sort") or item.get("episode") or item.get("index") or (i + 1)).strip()
                if item_ep == ep:
                    video_url = str(item.get("video_url") or "").strip()
                    break
            if not video_url and str(info.get("episode_sort") or "").strip() == ep:
                video_url = str(info.get("video_url") or "").strip()
        elif info.get("video_url"):
            video_url = str(info.get("video_url")).strip()
        if video_url.startswith("http"):
            return {"parse": 0, "playUrl": "", "url": video_url, "header": headers}
        return {"parse": 1, "playUrl": "", "url": self.host, "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249889144&sig=2918a367ff9bd7f4
