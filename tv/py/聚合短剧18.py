#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import os
import ssl
import json
import gzip
import zlib
import time
import base64
import random
import hashlib
import hmac as hmac_mod
import http.client
import http.cookiejar
import urllib.request
import urllib.error
import urllib.parse
from urllib.parse import quote, urlsplit

from base.spider import Spider as BaseSpider


def format_remarks(brand="蝴蝶影视", meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


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
_AES_INV_SBOX = [0] * 256
for _i, _v in enumerate(_AES_SBOX):
    _AES_INV_SBOX[_v] = _i
_AES_INV_SBOX = tuple(_AES_INV_SBOX)
_AES_RCON = (0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80,0x1b,0x36)

def _aes_xtime(a):
    return (((a << 1) ^ 0x1b) & 0xff) if (a & 0x80) else ((a << 1) & 0xff)

def _aes_gmul(a, b):
    p = 0
    while b:
        if b & 1:
            p ^= a
        a = _aes_xtime(a)
        b >>= 1
    return p

_AES_M09 = tuple(_aes_gmul(i, 0x09) for i in range(256))
_AES_M0B = tuple(_aes_gmul(i, 0x0b) for i in range(256))
_AES_M0D = tuple(_aes_gmul(i, 0x0d) for i in range(256))
_AES_M0E = tuple(_aes_gmul(i, 0x0e) for i in range(256))

def _aes_expand_key(key):
    ek = list(key)
    for i in range(10):
        t = ek[-4:]
        t = t[1:] + t[:1]
        t = [_AES_SBOX[b] for b in t]
        t[0] ^= _AES_RCON[i]
        for _j in range(4):
            t = [t[k] ^ ek[-16+k] for k in range(4)]
            ek += t
    return [ek[i:i+16] for i in range(0, 176, 16)]

def _aes_decrypt_block(blk, rk):
    s = [a ^ b for a, b in zip(blk, rk[10])]
    for r in range(9, 0, -1):
        s = [s[0],s[13],s[10],s[7],s[4],s[1],s[14],s[11],s[8],s[5],s[2],s[15],s[12],s[9],s[6],s[3]]
        s = [_AES_INV_SBOX[b] for b in s]
        s = [a ^ b for a, b in zip(s, rk[r])]
        o = [0] * 16
        for c in range(4):
            a0, a1, a2, a3 = s[c*4], s[c*4+1], s[c*4+2], s[c*4+3]
            o[c*4]   = _AES_M0E[a0] ^ _AES_M0B[a1] ^ _AES_M0D[a2] ^ _AES_M09[a3]
            o[c*4+1] = _AES_M09[a0] ^ _AES_M0E[a1] ^ _AES_M0B[a2] ^ _AES_M0D[a3]
            o[c*4+2] = _AES_M0D[a0] ^ _AES_M09[a1] ^ _AES_M0E[a2] ^ _AES_M0B[a3]
            o[c*4+3] = _AES_M0B[a0] ^ _AES_M0D[a1] ^ _AES_M09[a2] ^ _AES_M0E[a3]
        s = o
    s = [s[0],s[13],s[10],s[7],s[4],s[1],s[14],s[11],s[8],s[5],s[2],s[15],s[12],s[9],s[6],s[3]]
    s = [_AES_INV_SBOX[b] for b in s]
    return bytes(a ^ b for a, b in zip(s, rk[0]))

class FastAesCbc(object):
    def __init__(self, key, iv):
        self.rk = _aes_expand_key(key)
        self.iv = bytes(iv)

    def decrypt(self, data):
        out = bytearray()
        prev = self.iv
        for i in range(0, len(data) - 15, 16):
            blk = _aes_decrypt_block(data[i:i+16], self.rk)
            out += bytes(a ^ b for a, b in zip(blk, prev))
            prev = data[i:i+16]
        if not out:
            return b""
        pad = out[-1]
        if 1 <= pad <= 16 and bytes(out[-pad:]) == bytes([pad]) * pad:
            del out[-pad:]
        return bytes(out)


def _gmul(a, b):
    r = 0
    while b:
        if b & 1:
            r ^= a
        a = ((a << 1) & 0xff) ^ (0x1b if a & 0x80 else 0)
        b >>= 1
    return r


def _ginv(x):
    if x == 0:
        return 0
    r = 1
    base = x
    e = 254
    while e:
        if e & 1:
            r = _gmul(r, base)
        base = _gmul(base, base)
        e >>= 1
    return r


def _rotl8(x, n):
    return ((x << n) | (x >> (8 - n))) & 0xff


_AES_SBOX = []
for _x in range(256):
    _inv = _ginv(_x)
    _AES_SBOX.append((_inv ^ _rotl8(_inv, 1) ^ _rotl8(_inv, 2) ^ _rotl8(_inv, 3) ^ _rotl8(_inv, 4) ^ 0x63) & 0xff)
_AES_RCON = [0x01, 0x02, 0x04, 0x08, 0x10, 0x20, 0x40, 0x80, 0x1b, 0x36]


def _aes_expand(key):
    w = list(key)
    for i in range(4, 44):
        t = w[4 * (i - 1):4 * i]
        if i % 4 == 0:
            t = [_AES_SBOX[t[1]] ^ _AES_RCON[i // 4 - 1], _AES_SBOX[t[2]], _AES_SBOX[t[3]], _AES_SBOX[t[0]]]
        w += [w[4 * (i - 4) + j] ^ t[j] for j in range(4)]
    return w


def _aes_xtime(a):
    return ((a << 1) & 0xff) ^ (0x1b if a & 0x80 else 0)


def _aes_encrypt_block(key, block):
    w = _aes_expand(key)
    s = [block[i] ^ w[i] for i in range(16)]

    def sub_shift(state):
        t = [_AES_SBOX[b] for b in state]
        out = [0] * 16
        for r in range(4):
            for c in range(4):
                out[r + 4 * c] = t[r + 4 * ((c + r) % 4)]
        return out

    for rnd in range(1, 10):
        s = sub_shift(s)
        mixed = [0] * 16
        for c in range(4):
            a = s[4 * c:4 * c + 4]
            mixed[4 * c + 0] = _aes_xtime(a[0]) ^ (_aes_xtime(a[1]) ^ a[1]) ^ a[2] ^ a[3]
            mixed[4 * c + 1] = a[0] ^ _aes_xtime(a[1]) ^ (_aes_xtime(a[2]) ^ a[2]) ^ a[3]
            mixed[4 * c + 2] = a[0] ^ a[1] ^ _aes_xtime(a[2]) ^ (_aes_xtime(a[3]) ^ a[3])
            mixed[4 * c + 3] = (_aes_xtime(a[0]) ^ a[0]) ^ a[1] ^ a[2] ^ _aes_xtime(a[3])
        s = [mixed[i] ^ w[16 * rnd + i] for i in range(16)]
    s = sub_shift(s)
    s = [s[i] ^ w[160 + i] for i in range(16)]
    return bytes(s)


def aes_ecb_encrypt_b64(key_str, plain_str):
    key = key_str.encode("utf-8")
    data = plain_str.encode("utf-8")
    pad = 16 - (len(data) % 16)
    data = data + bytes([pad] * pad)
    out = b""
    for i in range(0, len(data), 16):
        out += _aes_encrypt_block(key, data[i:i + 16])
    return base64.b64encode(out).decode()


_EC_P = 0xffffffff00000001000000000000000000000000ffffffffffffffffffffffff
_EC_A = _EC_P - 3
_EC_GX = 0x6b17d1f2e12c4247f8bce6e563a440f277037d812deb33a0f4a13945d898c296
_EC_GY = 0x4fe342e2fe1a7f9b8ee7eb4a7c0f9e162bce33576b315ececbb6406837bf51f5
_EC_N = 0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551
_EC_SPKI_PREFIX = bytes.fromhex("3059301306072a8648ce3d020106082a8648ce3d030107034200")


def _ec_add(p1, p2):
    if p1 is None:
        return p2
    if p2 is None:
        return p1
    x1, y1 = p1
    x2, y2 = p2
    if x1 == x2 and (y1 + y2) % _EC_P == 0:
        return None
    if p1 == p2:
        lam = (3 * x1 * x1 + _EC_A) * pow(2 * y1, -1, _EC_P) % _EC_P
    else:
        lam = (y2 - y1) * pow(x2 - x1, -1, _EC_P) % _EC_P
    x3 = (lam * lam - x1 - x2) % _EC_P
    return (x3, (lam * (x1 - x3) - y1) % _EC_P)


def _ec_mul(k, pt):
    r = None
    while k:
        if k & 1:
            r = _ec_add(r, pt)
        pt = _ec_add(pt, pt)
        k >>= 1
    return r


def _der_read(buf, off):
    tag = buf[off]
    b = buf[off + 1]
    if b < 0x80:
        return tag, off + 2, off + 2 + b, off + 2 + b
    n = b & 0x7f
    ln = int.from_bytes(buf[off + 2:off + 2 + n], "big")
    return tag, off + 2 + n, off + 2 + n + ln, off + 2 + n + ln


def _rsa_n_e(spki_der):
    tag, s, e, nx = _der_read(spki_der, 0)
    tag2, s2, e2, nx2 = _der_read(spki_der, s)
    tag3, s3, e3, nx3 = _der_read(spki_der, nx2)
    pkcs1 = spki_der[s3 + 1:e3]
    tag, s, e, nx = _der_read(pkcs1, 0)
    tag_n, s_n, e_n, nx_n = _der_read(pkcs1, s)
    n = int.from_bytes(pkcs1[s_n:e_n], "big")
    tag_e, s_e, e_e, nx_e = _der_read(pkcs1, nx_n)
    ev = int.from_bytes(pkcs1[s_e:e_e], "big")
    return n, ev


def _rsa_encrypt_b64(spki_der, msg):
    n, e = _rsa_n_e(spki_der)
    k = 256
    ps = bytearray()
    while len(ps) < k - len(msg) - 3:
        b = os.urandom(1)
        if b != b"\x00":
            ps += b
    em = b"\x00\x02" + bytes(ps) + b"\x00" + msg
    c = pow(int.from_bytes(em, "big"), e, n)
    return base64.b64encode(c.to_bytes(k, "big")).decode()


class Spider(BaseSpider):
    PLATS = [
        ["qm", "七猫"], ["wg", "围观"], ["xy", "星芽"], ["hk", "好看"],
        ["jg", "禁果"], ["kb", "狂飙"], ["yg", "野果"], ["hg", "黄果"]
    ]
    SUBS = {
        "qm": [
            ["10000000-0000-4000-8000-0000000000c0", "热门短剧"], ["10000000-0000-4000-8000-000000000002", "原创短剧"],
            ["10000000-0000-4000-8000-0000000000b0", "真人短剧"], ["10000000-0000-4000-8000-000000000005", "擦边短剧"],
            ["10000000-0000-4000-8000-0000000000b3", "AI短剧"], ["10000000-0000-4000-8000-000000000003", "AI漫剧"],
            ["10000000-0000-4000-8000-0000000000b1", "AI魔改"], ["10000000-0000-4000-8000-0000000000b2", "AI换脸"],
            ["10000000-0000-4000-8000-0000000000b4", "影视综艺"]
        ],
        "wg": [
            ["rec", "推荐"], ["lib", "片库"], ["type0", "真人剧"], ["type1", "AI剧"],
            ["rank1", "热播榜"], ["rank2", "飙升榜"], ["rank3", "新剧榜"], ["rank4", "好剧榜"],
            ["rank5", "好看榜"], ["new", "新剧"], ["series", "系列剧"]
        ],
        "xy": [["1", "剧场"], ["3", "新剧"], ["2", "热播剧"], ["7", "星选好剧"], ["5", "阳光剧场"]],
        "hk": [
            ["1", "热播剧"], ["5", "漫剧"], ["2", "新剧"], ["1001", "战神"], ["2001", "神豪"],
            ["1002", "神医"], ["1007", "甜宠"], ["1003", "赘婿"], ["2004", "穿越重生"], ["2005", "异能"],
            ["1006", "虐恋"], ["2006", "宫斗宅斗"], ["2009", "玄幻"], ["1005", "穿越"]
        ],
        "jg": [["landing", "精选推荐"], ["latest", "最新上线"]],
        "kb": [["recommend", "狂飙推荐"], ["adult_short", "成人短剧"]],
        "yg": [["explore", "野果发现"], ["rank", "排行榜"]],
        "hg": [["1", "黄果MV"], ["3", "连续剧"]]
    }
    IPHONE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

    def __init__(self):
        super(Spider, self).__init__()
        self.siteName = "聚合短剧"
        self.siteUrl = "https://www.butterfly.tv"
        self.brandName = "蝴蝶影视"
        self.brandActor = "🦋 TG群: @tvshare23"
        self.brandDirector = "🦋 蝴蝶影视"
        self.options = {}
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=self.ctx)
        )
        self._wg_session = None
        self._wg_device = ""
        self._xy_token = ""
        self._qm_token = ""

    def init(self, extend=""):
        if isinstance(extend, dict):
            self.options = extend
        elif extend:
            text = str(extend).strip()
            if text.startswith("http"):
                self.options = {"host": text}
            else:
                try:
                    parsed = json.loads(text)
                    self.options = parsed if isinstance(parsed, dict) else {}
                except Exception:
                    self.options = {}
        host = str(self.options.get("host") or "").strip()
        if host.startswith("http"):
            self.siteUrl = host.rstrip("/")
        return True

    def getName(self):
        return self.siteName

    def isVideoFormat(self, url):
        path = urlsplit(str(url or "")).path.lower()
        return path.endswith((".m3u8", ".mpd", ".mp4", ".mkv", ".flv", ".mp3", ".m4a", ".aac"))

    def manualVideoCheck(self):
        return False

    def destroy(self):
        self.options = {}

    def _enc(self, value):
        return quote(str(value if value is not None else ""), safe="")

    def _read_body(self, resp):
        try:
            raw = resp.read()
        except http.client.IncompleteRead as e:
            raw = e.partial or b""
        enc = ""
        try:
            enc = resp.headers.get("Content-Encoding", "") or ""
        except Exception:
            enc = ""
        if raw.startswith(b"\x1f\x8b") or enc == "gzip":
            try:
                raw = gzip.decompress(raw)
            except Exception:
                pass
        elif enc == "deflate":
            try:
                raw = zlib.decompress(raw)
            except Exception:
                try:
                    raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                except Exception:
                    pass
        return raw

    def _fetch(self, url, ua=None, method="GET", data=None, headers=None, timeout=8, tries=2):
        h = {"Accept-Encoding": "gzip, deflate", "Connection": "keep-alive"}
        if ua:
            h["User-Agent"] = ua
        if headers:
            h.update(headers)
        last = ""
        for i in range(tries):
            try:
                req = urllib.request.Request(url, data=data, headers=h, method=method)
                with self.opener.open(req, timeout=timeout) as resp:
                    return resp.getcode(), self._read_body(resp).decode("utf-8", errors="ignore")
            except urllib.error.HTTPError as e:
                try:
                    body = self._read_body(e).decode("utf-8", errors="ignore")
                except Exception:
                    body = ""
                if e.code != 429 and e.code < 500:
                    return e.code, body
                last = body
            except Exception:
                last = ""
            if i < tries - 1:
                time.sleep(0.5)
        return 0, last

    def _fetch_json(self, url, ua=None, method="GET", data=None, headers=None, timeout=8, tries=2):
        code, text = self._fetch(url, ua=ua, method=method, data=data, headers=headers, timeout=timeout, tries=tries)
        if code and (code < 200 or code >= 300):
            raise ValueError("HTTP %s" % code)
        parsed = json.loads(text)
        if not isinstance(parsed, (dict, list)):
            raise ValueError("bad json")
        return parsed

    def _rand_hex(self, n):
        return os.urandom((n + 1) // 2).hex()[:n]

    # ---------------- qm ----------------
    QM_HOST = "https://7maoduanju.com"

    def _qm_api(self, path, params=None, token=None):
        url = self.QM_HOST + "/api/toc/v1" + path
        bits = []
        for k, v in (params or {}).items():
            if v is None or v == "":
                continue
            bits.append(self._enc(k) + "=" + self._enc(v))
        if bits:
            url += "?" + "&".join(bits)
        headers = {"Accept": "application/json", "Referer": self.QM_HOST + "/", "Origin": self.QM_HOST}
        if token:
            headers["Authorization"] = "Bearer " + token
        return self._fetch_json(url, ua=self.IPHONE_UA, headers=headers, timeout=8)

    def _qm_card(self, d):
        if not isinstance(d, dict):
            return None
        if str(d.get("payMode") or "") == "coin_only":
            try:
                if int(d.get("freeEpisodeCount") or 0) == 0:
                    return None
            except Exception:
                pass
        did = str(d.get("id") or "")
        title = str(d.get("title") or "")
        if not did or not title:
            return None
        try:
            eps = int(d.get("episodeCount") or 0)
        except Exception:
            eps = 0
        try:
            free = int(d.get("freeEpisodeCount") or 0)
        except Exception:
            free = 0
        pay = str(d.get("payMode") or "")
        vip = bool(d.get("isVipBadge"))
        notes = []
        if eps > 0:
            notes.append("%s集" % eps)
        if vip or pay == "vip_only":
            notes.append(("免%s·VIP" % free) if free < 9000 else "VIP")
        elif free < 9000 and eps > 0:
            notes.append("免%s集" % free)
        pic = str(d.get("coverUrl") or "")
        if pic.startswith("//"):
            pic = "https:" + pic
        pic = pic.split("@Referer")[0].split("@User-Agent")[0].strip()
        return {"id": did, "title": title, "poster": pic,
                "status": format_remarks(self.brandName, " · ".join(notes)) if notes else self.brandName}

    def _qm_cards(self, arr):
        out = []
        for d in arr or []:
            card = self._qm_card(d)
            if card:
                out.append(card)
        return out

    def _qm_category(self, sub, page):
        d = self._qm_api("/browse", {"line": sub, "offset": (page - 1) * 12})
        items = d.get("items") if isinstance(d, dict) else []
        return self._qm_cards(items), bool(isinstance(d, dict) and d.get("hasMore")), len(items or [])

    def _qm_home_items(self):
        cards, has_more, raw = self._qm_category(self.SUBS["qm"][0][0], 1)
        return cards

    def _qm_search(self, keyword, page):
        if page > 1:
            return []
        d = self._qm_api("/search", {"q": keyword})
        if isinstance(d, list):
            arr = d
        elif isinstance(d, dict):
            arr = d.get("items") or d.get("data") or d.get("list") or []
        else:
            arr = []
        return self._qm_cards(arr)

    def _qm_fetch_drama(self, did):
        d = self._qm_api("/dramas/" + self._enc(did), {})
        eps = []
        for e in (d.get("episodes") if isinstance(d, dict) else []) or []:
            if not isinstance(e, dict):
                continue
            try:
                idx = int(e.get("indexNo") or 0)
            except Exception:
                idx = 0
            eps.append({"id": str(e.get("id") or ""), "index": idx, "title": str(e.get("title") or ""), "seo": str(e.get("seoContentUrl") or "")})
        eps.sort(key=lambda x: x["index"])
        prefix = ""
        for e in eps:
            m = re.match(r"^(https?://[^/\s]+/7cat/[^/\s]+)/hls/", e["seo"])
            if m:
                prefix = m.group(1)
                break
        if not prefix:
            for e in eps:
                m = re.match(r"^(https?://[^/\s]+/.+?)/hls/ep\d+/ep\d+\.m3u8", e["seo"])
                if m:
                    prefix = m.group(1)
                    break
        return d, eps, prefix

    def _qm_seo_url(self, prefix, index):
        if not prefix or index <= 0:
            return ""
        p = ("0" + str(index)) if index < 10 else str(index)
        return prefix + "/hls/ep" + p + "/ep" + p + ".m3u8"

    def _qm_detail(self, raw):
        d, eps, prefix = self._qm_fetch_drama(raw)
        if not eps:
            raise ValueError("no episodes")
        episodes = []
        for e in eps:
            flag = raw + "|" + e["id"] + "|" + str(e["index"])
            seo = e["seo"] or self._qm_seo_url(prefix, e["index"])
            episodes.append({"name": e["title"] or ("第%s集" % e["index"]),
                             "value": {"agg": "qm", "flag": flag, "seo": seo}})
        notes = []
        try:
            eps_n = int(d.get("episodeCount") or len(eps))
        except Exception:
            eps_n = len(eps)
        try:
            free = int(d.get("freeEpisodeCount") or 0)
        except Exception:
            free = 0
        if eps_n:
            notes.append("%s集" % eps_n)
        if free and free < 9000:
            notes.append("免%s集" % free)
        tags = d.get("tags") if isinstance(d, dict) else None
        if isinstance(tags, list) and tags:
            notes.append("/".join(str(t) for t in tags[:3]))
        pic = str(d.get("coverUrl") or "")
        if pic.startswith("//"):
            pic = "https:" + pic
        pic = pic.split("@Referer")[0].strip()
        return {"title": str(d.get("title") or ""), "poster": pic,
                "summary": str(d.get("description") or "七猫精品短剧"),
                "status": format_remarks(self.brandName, " · ".join(notes) if notes else "正片"),
                "episodes": episodes}

    def _qm_anon_token(self):
        if self._qm_token:
            return self._qm_token
        dev = "%s-4%s-%s-%s-%s" % (self._rand_hex(8), self._rand_hex(3), self._rand_hex(4), self._rand_hex(4), self._rand_hex(12))
        dev = dev[:36]
        code, text = self._fetch(self.QM_HOST + "/api/toc/v1/auth/device", ua=self.IPHONE_UA, method="POST",
                                 data=json.dumps({"deviceId": dev}).encode("utf-8"),
                                 headers={"Accept": "application/json", "Referer": self.QM_HOST + "/", "Origin": self.QM_HOST, "Content-Type": "application/json"}, timeout=8)
        try:
            data = json.loads(text)
            tok = str(data.get("token") or "")
        except Exception:
            tok = ""
        if tok:
            self._qm_token = tok
        return tok

    def _qm_resolve(self, ref):
        headers = {"User-Agent": self.IPHONE_UA, "Referer": self.QM_HOST + "/"}
        target = str(ref.get("seo") or "")
        flag = str(ref.get("flag") or "")
        parts = flag.split("|")
        did = parts[0] if parts else ""
        ep_id = parts[1] if len(parts) > 1 else ""
        idx = 0
        if len(parts) > 2:
            try:
                idx = int(parts[2])
            except Exception:
                idx = 0
        if not target and did:
            try:
                d, eps, prefix = self._qm_fetch_drama(did)
                for e in eps:
                    if ep_id and e["id"] == ep_id:
                        target = e["seo"] or self._qm_seo_url(prefix, e["index"])
                        break
                if not target and eps:
                    target = self._qm_seo_url(prefix, idx or eps[0]["index"])
            except Exception:
                pass
        if not target and did and ep_id:
            try:
                tok = self._qm_anon_token()
                if tok:
                    r = self._qm_api("/dramas/" + self._enc(did) + "/episodes/" + self._enc(ep_id) + "/play", {}, token=tok)
                    target = str(r.get("playUrl") or "") if isinstance(r, dict) else ""
            except Exception:
                pass
        if not target:
            raise ValueError("no target")
        return target, headers

    # ---------------- wg ----------------
    WG_BASE = "https://api.drama.9ddm.com/"
    WG_UA_APP = "okhttp/4.12.0"
    WG_UA_PLAY = "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36"
    WG_RSA_PUB_B64 = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEArzgQcG8qE8izInIKx1lia2Qmx1tzzsdAB49oPtar2DXg8MHO/qC8vyx26JQgBHTEY2FS1FbAOd+yZpo0qq2CFqxE5Vqsj2yq/6iouDxnmMuFoaiZkyeyobeXn8nCVyqMnztSotF248lEHgaJh0q2EHZIPxHBp1uCXEoLe7qTTs4eUpJD7K0z492SNzQjsNdoZOlCkKfusRf3iXP1tn0yP8j3fkLd8hjI2ZeUA33/MgyI4qDcpUil+4q2aUxcZWEcxm16SS9A5DWmp6XociqRHikCDBaF45zpfDz3ry1/6k7ntYHRMq3YmWxsIoat0HxW0S89JAJYSuBcCoNI7uIkRwIDAQAB"

    def _wg_device_id(self):
        if not self._wg_device:
            self._wg_device = self._rand_hex(16)
        return self._wg_device

    def _wg_create_session(self):
        dev = self._wg_device_id()
        d = int.from_bytes(os.urandom(32), "big")
        if d >= _EC_N:
            d -= _EC_N
        if d == 0:
            d = 1
        pub = _ec_mul(d, (_EC_GX, _EC_GY))
        spki = _EC_SPKI_PREFIX + b"\x04" + pub[0].to_bytes(32, "big") + pub[1].to_bytes(32, "big")
        pub_b64 = base64.b64encode(spki).decode()
        enc_b64 = _rsa_encrypt_b64(base64.b64decode(self.WG_RSA_PUB_B64), pub_b64.encode("utf-8"))
        qs = urllib.parse.urlencode({
            "encryptedClientPublicKey": enc_b64, "nonce": self._rand_hex(32),
            "timestamp": str(int(time.time() * 1000)), "deviceId": dev,
            "deviceName": "Pixel 8", "osType": "1"
        })
        code, text = self._fetch(self.WG_BASE + "drama/session/create?" + qs, ua=self.WG_UA_APP, method="POST",
                                 data=b"", headers={"Content-Type": "application/json; charset=utf-8"}, timeout=8, tries=2)
        if code < 200 or code >= 300:
            raise ValueError("session HTTP %s" % code)
        j = json.loads(text)
        dd = j.get("data") or {}
        if not dd.get("sessionId") or not dd.get("serverEphemeralPublicKey"):
            raise ValueError("session rejected")
        server_der = base64.b64decode(str(dd["serverEphemeralPublicKey"]))
        tail = server_der[-65:]
        if tail[0] != 4:
            raise ValueError("bad server key")
        sp = (int.from_bytes(tail[1:33], "big"), int.from_bytes(tail[33:65], "big"))
        shared = _ec_mul(d, sp)
        if shared is None:
            raise ValueError("ecdh failed")
        secret = shared[0].to_bytes(32, "big")
        self._wg_session = {"sid": str(dd["sessionId"]), "key": base64.b64encode(secret).decode(), "exp": time.time() + 20 * 60}
        return self._wg_session

    def _wg_get_session(self, force=False):
        if not force and self._wg_session and self._wg_session.get("exp", 0) > time.time():
            return self._wg_session
        return self._wg_create_session()

    def _wg_call(self, method, path, query=None, body=None):
        last_err = None
        for attempt in range(2):
            sess = self._wg_get_session(force=attempt > 0)
            params = {}
            for src in (query, body):
                if src:
                    for k, v in src.items():
                        if v is not None:
                            params[k] = str(v)
            ts = str(int(time.time() * 1000))
            nonce = self._rand_hex(32)
            pstr = "".join(k + params[k] for k in sorted(params))
            sign = hmac_mod.new(sess["key"].encode("utf-8"), (pstr + ts + nonce).encode("utf-8"), hashlib.sha256).hexdigest()
            headers = {"X-Session-Id": sess["sid"], "X-Sign": sign, "X-Timestamp": ts, "X-Nonce": nonce}
            url = self.WG_BASE + path
            data = None
            if query:
                url += "?" + urllib.parse.urlencode(query)
            if method == "POST":
                headers["Content-Type"] = "application/json; charset=utf-8"
                data = json.dumps(body).encode("utf-8") if body is not None else b""
            code, text = self._fetch(url, ua=self.WG_UA_APP, method=method, data=data, headers=headers, timeout=8, tries=1)
            if code == 403 and attempt == 0:
                self._wg_session = None
                continue
            if code < 200 or code >= 300:
                raise ValueError("upstream HTTP %s" % code)
            return json.loads(text)
        raise ValueError("wg request failed")

    def _wg_item(self, vo):
        if not isinstance(vo, dict):
            return None
        one_id = str(vo.get("oneId") or "")
        if not one_id:
            return None
        parts = []
        if vo.get("channelName"):
            parts.append(str(vo["channelName"]))
        try:
            n = int(vo.get("episodeCount") or 0)
        except Exception:
            n = 0
        if n > 0:
            parts.append("全%s集" % n)
        return {"id": one_id, "title": str(vo.get("title") or one_id),
                "poster": str(vo.get("vertPoster") or vo.get("horzPoster") or ""),
                "status": format_remarks(self.brandName, " · ".join(parts) if parts else "正片")}

    def _wg_items(self, arr):
        out = []
        seen = set()
        for vo in arr or []:
            item = self._wg_item(vo)
            if item and item["id"] not in seen:
                seen.add(item["id"])
                out.append(item)
        return out

    def _wg_home_items(self):
        r = self._wg_call("POST", "drama/home/tab", body={"page": 1, "pageSize": 20})
        return self._wg_items(r.get("recommendDramaList") if isinstance(r, dict) else [])

    def _wg_category(self, sub, page):
        dev = self._wg_device_id()
        if sub == "lib":
            r = self._wg_call("POST", "drama/home/searchV2", body={
                "searchWord": "", "audience": "", "subject": "", "shortPlayType": "",
                "order": "", "episodeCount": "", "page": page, "pageSize": 20, "userId": ""})
            return self._wg_items(r.get("data") if isinstance(r, dict) else [])
        if sub in ("type0", "type1"):
            r = self._wg_call("POST", "drama/home/recommend/category", query={"clientInfo": dev}, body={
                "page": page, "pageSize": 20, "deviceId": dev, "userId": "", "categoryType": 0 if sub == "type0" else 1})
            return self._wg_items(r.get("recommendDramaList") if isinstance(r, dict) else [])
        if sub.startswith("rank"):
            try:
                rt = int(sub[4:]) or 1
            except Exception:
                rt = 1
            r = self._wg_call("GET", "drama/rank/list", query={"rankType": rt, "page": page, "pageSize": 20})
            return self._wg_items(r.get("data") if isinstance(r, dict) else [])
        r = self._wg_call("POST", "drama/home/tab", body={"page": page, "pageSize": 20})
        return self._wg_items(r.get("recommendDramaList") if isinstance(r, dict) else [])

    def _wg_search(self, keyword, page):
        r = self._wg_call("POST", "drama/home/searchV2", body={"searchWord": keyword, "page": page, "pageSize": 20})
        return self._wg_items(r.get("data") if isinstance(r, dict) else [])

    def _wg_episodes(self, one_id, page, size):
        r = self._wg_call("GET", "drama/home/shortVideoDetail", query={"oneId": one_id, "page": page, "pageSize": size, "userId": 0})
        if not isinstance(r, dict) or r.get("code") != 200:
            raise ValueError("wg detail rejected")
        return r

    def _wg_play_url(self, ep):
        try:
            if int(ep.get("payStatus") or 0) != 0:
                return ""
        except Exception:
            return ""
        raw = ep.get("playSetting")
        if not isinstance(raw, str) or not raw:
            return ""
        try:
            ps = json.loads(raw)
        except Exception:
            return ""
        if not isinstance(ps, dict):
            return ""
        return str(ps.get("super") or ps.get("high") or ps.get("normal") or "")

    def _wg_detail(self, raw):
        first = self._wg_episodes(raw, 1, 100)
        try:
            total = int(first.get("totalEpisodeCount") or 0)
        except Exception:
            total = 0
        episodes = []
        for ep in first.get("data") or []:
            if not isinstance(ep, dict):
                continue
            try:
                order = int(ep.get("playOrder") or 0)
            except Exception:
                order = 0
            if not order:
                continue
            if not self._wg_play_url(ep):
                continue
            episodes.append({"name": "第%s集" % order, "value": {"agg": "wg", "oneId": raw, "ep": order}})
        if not episodes:
            raise ValueError("no playable episodes")
        return {"title": str(first.get("title") or raw), "poster": str(first.get("vertPoster") or ""),
                "summary": str(first.get("description") or "围观短剧全集高清直播"),
                "status": format_remarks(self.brandName, ("全%s集" % total) if total > 0 else ("共%s集" % len(episodes))),
                "episodes": episodes}

    def _wg_resolve(self, ref):
        one_id = str(ref.get("oneId") or "")
        try:
            ep_order = int(ref.get("ep") or 0)
        except Exception:
            ep_order = 0
        if not one_id or not ep_order:
            raise ValueError("missing ep ref")
        page = max(1, -(-ep_order // 50))
        r = self._wg_episodes(one_id, page, 50)
        target = None
        for ep in r.get("data") or []:
            if isinstance(ep, dict):
                try:
                    if int(ep.get("playOrder") or 0) == ep_order:
                        target = ep
                        break
                except Exception:
                    pass
        if target is None:
            raise ValueError("ep not found")
        url = self._wg_play_url(target)
        if not url:
            raise ValueError("no play url")
        return url, {"User-Agent": self.WG_UA_PLAY}

    # ---------------- xy ----------------
    XY_API = "https://app.whjzjx.cn"
    XY_LOGIN_URL = "https://u.shytkjgs.com/user/v3/account/login"
    XY_LOGIN_KEY = "B@ecf920Od8A4df7"
    XY_UA_LOGIN = "Mozilla/5.0 (Linux; Android 9; V1938T Build/PQ3A.190705.08211809; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Safari/537.36"
    XY_UA_PLAY = "Mozilla/5.0 (Linux; Android 12; Pixel 3 XL) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.101 Mobile Safari/537.36"

    def _xy_login(self):
        now = int(time.time() * 1000)
        body_obj = {
            "device": self._rand_hex(32), "package_name": "com.jz.xydj", "android_id": self._rand_hex(16),
            "install_first_open": True, "first_install_time": now - 86400000, "last_update_time": now - 86400000,
            "report_link_url": "", "authorization": "", "timestamp": now
        }
        cipher = aes_ecb_encrypt_b64(self.XY_LOGIN_KEY, json.dumps(body_obj))
        code, text = self._fetch(self.XY_LOGIN_URL, method="POST", data=cipher.encode("utf-8"),
                                 headers={"platform": "1", "user_agent": self.XY_UA_LOGIN, "Content-Type": "application/json; charset=utf-8"}, timeout=8)
        v = json.loads(text)
        token = str(((v.get("data") or {}).get("token")) or "") if isinstance(v, dict) else ""
        if not token:
            raise ValueError("xy login failed")
        self._xy_token = token
        return token

    def _xy_token_get(self, force=False):
        if not force and self._xy_token:
            return self._xy_token
        return self._xy_login()

    def _xy_api(self, path, post_body=None):
        for attempt in range(2):
            token = self._xy_token_get(force=attempt > 0)
            headers = {"authorization": token, "platform": "1", "version_name": "3.8.3.1"}
            if post_body is not None:
                headers["Content-Type"] = "application/json"
                code, text = self._fetch(self.XY_API + path, method="POST", data=json.dumps(post_body).encode("utf-8"), headers=headers, timeout=8, tries=1)
            else:
                code, text = self._fetch(self.XY_API + path, headers=headers, timeout=8, tries=1)
            v = json.loads(text) if text else {}
            if isinstance(v, dict) and v.get("code") == "ok":
                return v.get("data") or {}
            if attempt == 0:
                continue
            raise ValueError("xy rejected")
        raise ValueError("xy failed")

    def _xy_item(self, t):
        if not isinstance(t, dict) or t.get("id") is None:
            return None
        pid = str(t["id"])
        parts = []
        if t.get("theme"):
            parts.append(str(t["theme"]))
        if t.get("total"):
            parts.append("全%s集" % t["total"])
        return {"id": pid, "title": str(t.get("title") or pid), "poster": str(t.get("cover_url") or ""),
                "status": format_remarks(self.brandName, " · ".join(parts) if parts else "正片")}

    def _xy_list(self, data):
        out = []
        rows = data.get("list") if isinstance(data, dict) else []
        for row in rows or []:
            t = (row.get("theater") if isinstance(row, dict) else None) or row
            item = self._xy_item(t)
            if item:
                out.append(item)
        return out

    def _xy_home_items(self):
        data = self._xy_api("/v1/theater/home_page?theater_class_id=1&page_num=1&page_size=24")
        return self._xy_list(data)

    def _xy_category(self, sub, page):
        data = self._xy_api("/v1/theater/home_page?theater_class_id=" + self._enc(sub) + "&page_num=" + str(page) + "&page_size=24")
        return self._xy_list(data)

    def _xy_search(self, keyword, page):
        if page > 1:
            return []
        data = self._xy_api("/v3/search", {"text": keyword})
        sd = []
        if isinstance(data, dict):
            sd = ((data.get("theater") or {}).get("search_data")) or []
        out = []
        for t in sd:
            if not isinstance(t, dict) or keyword not in str(t.get("title") or ""):
                continue
            item = self._xy_item(t)
            if item:
                out.append(item)
        return out

    def _xy_detail_data(self, pid):
        return self._xy_api("/v2/theater_parent/detail?theater_parent_id=" + self._enc(pid))

    def _xy_detail(self, raw):
        d = self._xy_detail_data(raw)
        sons = list(d.get("theaters") or []) if isinstance(d, dict) else []
        sons.sort(key=lambda s: (int(s.get("num") or 0) if isinstance(s, dict) else 0))
        episodes = []
        for s in sons:
            if not isinstance(s, dict) or s.get("id") is None or not s.get("son_video_url"):
                continue
            try:
                num = int(s.get("num") or len(episodes) + 1)
            except Exception:
                num = len(episodes) + 1
            episodes.append({"name": "第%s集" % num, "value": {"agg": "xy", "pid": raw, "sid": str(s["id"])}})
        if not episodes and isinstance(d, dict) and d.get("video_url"):
            episodes.append({"name": "正片", "value": {"agg": "xy", "pid": raw, "sid": "main"}})
        if not episodes:
            raise ValueError("no episodes")
        return {"title": str(d.get("title") or raw), "poster": str(d.get("cover_url") or ""),
                "summary": str(d.get("introduction") or "星芽热映正片"),
                "status": format_remarks(self.brandName, "共%s集" % len(episodes)),
                "episodes": episodes}

    def _xy_resolve(self, ref):
        pid = str(ref.get("pid") or "")
        sid = str(ref.get("sid") or "")
        if not pid or not sid:
            raise ValueError("missing ref")
        d = self._xy_detail_data(pid)
        url = ""
        if sid == "main":
            url = str(d.get("video_url") or "") if isinstance(d, dict) else ""
        else:
            for s in (d.get("theaters") or []) if isinstance(d, dict) else []:
                if isinstance(s, dict) and str(s.get("id")) == sid:
                    url = str(s.get("son_video_url") or "")
                    break
        if not url:
            raise ValueError("no play url")
        if url.startswith("http://"):
            url = "https://" + url[7:]
        return url, {"User-Agent": self.XY_UA_PLAY}

    # ---------------- hk ----------------
    HK_HOST = "https://sv.baidu.com"
    HK_UA = "Mozilla/5.0 (Linux; Android 11; M2012K10C Build/RP1A.200720.011; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/87.0.4280.141 Mobile Safari/537.36 haokan/7.80.0.18 (Baidu; P1 11)/imoaiX_03_11_C01K2102M/1043677m/5ACDB023CFB9D64743B08E51953F7C76%7CVSAJ32AVA/1/7.80.0.18/780001/1/immersiveMode/modeV4PlusWhite/isFirstInstall/bbqMode/bbqModeV2/blackStyle/isPlaylet Talos/1.8.7"
    HK_CUID = "giHCu0azv80G8SfQ0avU8gaaH8jfiv86ju2MugiR2i8-k3a35avAa1_mA"
    HK_QUALITY = ["4k", "2k", "高清", "蓝光", "超清", "标清"]

    def _hk_post(self, path, body, cookie=False):
        headers = {"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"}
        if cookie:
            headers["Cookie"] = "BAIDUCUID=" + self.HK_CUID
        code, text = self._fetch(self.HK_HOST + path, ua=self.HK_UA, method="POST", data=body.encode("utf-8"), headers=headers, timeout=8)
        try:
            parsed = json.loads(text or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    def _hk_appui(self, key, inner):
        j = self._hk_post("/appui/api?osbranch=a0", key + "=" + self._enc(inner), cookie=True)
        return ((j.get(key) or {}).get("data")) or {}

    def _hk_item(self, b):
        if not isinstance(b, dict):
            return None
        pid = str(b.get("playlet_id") or "")
        if not pid:
            return None
        return {"id": pid, "title": str(b.get("playlet_title") or pid), "poster": str(b.get("playlet_poster") or ""),
                "status": format_remarks(self.brandName, str(b.get("episodes_num_text") or "连载中"))}

    def _hk_home_items(self):
        j = self._hk_post("/haokan/ui-feed/playletShelfFeed?osbranch=a0", "", cookie=False)
        d = j.get("data") or {}
        out = []
        for b in d.get("playlet_banner") or []:
            item = self._hk_item(b)
            if item:
                out.append(item)
        return out

    def _hk_category(self, sub, page):
        j = self._hk_post("/haokan/ui-feed/playletTagsFeed?osbranch=a0", "tag_id=" + self._enc(sub) + "&rn=20&pn=" + str(page), cookie=False)
        out = []
        for b in ((j.get("data") or {}).get("list")) or []:
            item = self._hk_item(b)
            if item:
                out.append(item)
        return out

    def _hk_search(self, keyword, page):
        return []

    def _hk_detail(self, raw):
        inner = "enable_enter_playlet=0&type=playlet&commonlist_id=" + str(int(time.time() * 1000))[:13] + "&id=" + raw + "&rn=20&pn=1&direction=3"
        cdata = self._hk_appui("video/commonlist", inner)
        results = cdata.get("results") or []
        first_vid = ""
        if results and isinstance(results[0], dict):
            first_vid = str(((results[0].get("content") or {}).get("vid")) or results[0].get("vid") or "")
        jd = self._hk_post("/haokan/ui-video/playlet/rec/detail?osbranch=a0", "vid=" + self._enc(first_vid) + "&playlet_id=" + self._enc(raw), cookie=True)
        d = jd.get("data") or {}
        vids = d.get("vid_list") or []
        episodes = []
        for i, vid in enumerate(vids):
            episodes.append({"name": "第%s集" % (i + 1), "value": {"agg": "hk", "pid": raw, "vid": str(vid)}})
        if not episodes:
            raise ValueError("no episodes")
        return {"title": str(d.get("playlet_title") or raw), "poster": str(d.get("playlet_poster") or ""),
                "summary": str(d.get("description") or "百度好看短剧专线"),
                "status": format_remarks(self.brandName, "共%s集" % len(episodes)),
                "episodes": episodes}

    def _hk_resolve(self, ref):
        pid = str(ref.get("pid") or "")
        vid = str(ref.get("vid") or "")
        if not pid or not vid:
            raise ValueError("missing ref")
        inner = "method=post&vid=" + vid + "&immersive_mode=v4_5&tplname=feed_small_video&tag=playlet_talos&tab=detail&video_set_id=" + pid + "&play_screen_type=1"
        data = self._hk_appui("video/relate", inner)
        cv = data.get("cur_video") or {}
        by_title = {}
        for c in cv.get("clarityUrl") or []:
            if isinstance(c, dict) and c.get("title") and c.get("url"):
                by_title[str(c["title"])] = str(c["url"])
        url = ""
        for q in self.HK_QUALITY:
            if by_title.get(q):
                url = by_title[q]
                break
        if not url and isinstance(cv.get("video_list"), dict) and cv["video_list"]:
            url = str(cv["video_list"][list(cv["video_list"].keys())[0]])
        if not url:
            raise ValueError("no play url")
        return url, {"User-Agent": self.HK_UA}

    # ---------------- jg ----------------
    JG_HOST = "https://jinguoduanju.app"

    def _jg_get(self, path):
        code, text = self._fetch(self.JG_HOST + "/api/v1" + path, ua=self.IPHONE_UA, headers={"Referer": self.JG_HOST + "/"}, timeout=8)
        try:
            parsed = json.loads(text or "{}")
            return parsed if isinstance(parsed, (dict, list)) else {}
        except Exception:
            return {}

    def _jg_card(self, it):
        if not isinstance(it, dict):
            return None
        vid = str(it.get("id") or "").strip()
        if not vid:
            return None
        cover = str(it.get("coverUrl") or it.get("cover") or "").strip()
        if cover.startswith("//"):
            cover = "https:" + cover
        elif cover and not cover.startswith("http"):
            cover = self.JG_HOST + "/" + cover.lstrip("/")
        return {"id": vid, "title": str(it.get("title") or vid).strip(), "poster": cover,
                "status": format_remarks(self.brandName, ("全%s集" % it["episodeCount"]) if it.get("episodeCount") else "正片")}

    def _jg_cards(self, arr):
        out = []
        for it in arr or []:
            card = self._jg_card(it)
            if card:
                out.append(card)
        return out

    def _jg_home_items(self):
        data = self._jg_get("/landing")
        arr = data if isinstance(data, list) else (data.get("dramas") or [])
        return self._jg_cards(arr[:24])

    def _jg_category(self, sub, page):
        data = self._jg_get("/dramas?sort=latest&page=" + str(page))
        return self._jg_cards(data if isinstance(data, list) else [])

    def _jg_search(self, keyword, page):
        data = self._jg_get("/dramas?q=" + self._enc(keyword))
        return self._jg_cards(data if isinstance(data, list) else [])

    def _jg_detail(self, raw):
        data = self._jg_get("/dramas/" + self._enc(raw))
        drama = (data.get("drama") or {}) if isinstance(data, dict) else {}
        eps = (data.get("episodes") or []) if isinstance(data, dict) else []
        episodes = []
        for i, ep in enumerate(eps):
            episodes.append({"name": "第%s集" % (i + 1),
                             "value": {"agg": "jg", "epId": str(ep.get("id") or "") if isinstance(ep, dict) else ""}})
        if not episodes:
            raise ValueError("no episodes")
        cover = str(drama.get("coverUrl") or drama.get("cover") or "")
        if cover.startswith("//"):
            cover = "https:" + cover
        elif cover and not cover.startswith("http"):
            cover = self.JG_HOST + "/" + cover.lstrip("/")
        return {"title": str(drama.get("title") or raw), "poster": cover,
                "summary": str(drama.get("description") or "禁果精选短剧"),
                "status": format_remarks(self.brandName, "共%s集" % len(episodes)),
                "episodes": episodes}

    def _jg_resolve(self, ref):
        ep_id = str(ref.get("epId") or "")
        if not ep_id:
            raise ValueError("missing ref")
        play = self._jg_get("/episodes/" + self._enc(ep_id) + "/play")
        url = str((play.get("videoUrl") or "") if isinstance(play, dict) else "").strip()
        if not url:
            raise ValueError("no play url")
        return url, {"User-Agent": self.IPHONE_UA, "Referer": self.JG_HOST + "/"}

    # ---------------- kb ----------------
    KB_HOST = "https://ai.dramarush.tv"
    KB_UA = "Mozilla/5.0 (Linux; Android 12; Mobile) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"

    def _kb_api(self, name, data):
        url = self.KB_HOST + "/api/trpc/" + name + "?input=" + self._enc(json.dumps({"json": data}))
        code, text = self._fetch(url, ua=self.KB_UA, headers={"Accept": "application/json", "Referer": self.KB_HOST + "/zh/"}, timeout=8)
        try:
            obj = json.loads(text or "")
            return (((obj.get("result") or {}).get("data") or {}).get("json")) or {}
        except Exception:
            return {}

    def _kb_card(self, it):
        v = (it.get("drama") if isinstance(it, dict) else None) or it or {}
        if not isinstance(v, dict):
            return None
        vid = str(v.get("id") or "")
        if not vid:
            return None
        return {"id": vid, "title": str(v.get("title") or vid), "poster": str(v.get("cover") or v.get("poster") or ""),
                "status": format_remarks(self.brandName, ("%s集" % v["totalEpisodes"]) if v.get("totalEpisodes") else "正片")}

    def _kb_cards(self, d):
        arr = d if isinstance(d, list) else (d.get("items") or [] if isinstance(d, dict) else [])
        out = []
        for it in arr:
            card = self._kb_card(it)
            if card:
                out.append(card)
        return out

    def _kb_home_items(self):
        return self._kb_cards(self._kb_api("feed.recommend", {"limit": 12}))

    def _kb_category(self, sub, page):
        if page > 1:
            return []
        return self._kb_cards(self._kb_api("feed.browse", {"limit": 12, "tagSlug": "adult"}))

    def _kb_search(self, keyword, page):
        return []

    def _kb_detail(self, raw):
        d = self._kb_api("episode.watch", {"dramaId": raw, "episodeNumber": 1})
        eps_arr = d.get("episodes") if isinstance(d, dict) else []
        episodes = []
        for i, ep in enumerate(eps_arr or []):
            episodes.append({"name": "第%s集" % (i + 1),
                             "value": {"agg": "kb", "eid": str(ep.get("id") or "") if isinstance(ep, dict) else ""}})
        if not episodes:
            raise ValueError("no episodes")
        return {"title": "狂飙剧集 " + raw, "poster": "", "summary": "狂飙精品短剧在线热播",
                "status": format_remarks(self.brandName, "共%s集" % len(episodes)),
                "episodes": episodes}

    def _kb_resolve(self, ref):
        eid = str(ref.get("eid") or "")
        if not eid:
            raise ValueError("missing ref")
        return "https://raw.shorttv.online/uploads/direct/" + eid + "/video.mp4", {"User-Agent": self.KB_UA, "Referer": self.KB_HOST + "/"}

    # ---------------- yg ----------------
    YG_HOST = "https://www.yeguodj.com"
    YG_KEY = "2acf7e91e9864673"
    YG_IV = "1c29882d3ddfcfd6"

    def _yg_post(self, path, body):
        url = self.YG_HOST + "/api.php" + path
        for attempt in range(2):
            code, text = self._fetch(url, ua=self.IPHONE_UA, method="POST", data=json.dumps(body or {}).encode("utf-8"),
                                     headers={"Content-Type": "application/json;charset=UTF-8"}, timeout=8, tries=1)
            try:
                parsed = json.loads(text or "{}")
            except Exception:
                parsed = {}
            if isinstance(parsed, dict) and isinstance(parsed.get("data"), str) and len(parsed["data"]) > 20:
                try:
                    plain = FastAesCbc(self.YG_KEY.encode("utf-8"), self.YG_IV.encode("utf-8")).decrypt(base64.b64decode(parsed["data"]))
                    wrapper = json.loads(plain.decode("utf-8", errors="ignore"))
                    if isinstance(wrapper, dict) and isinstance(wrapper.get("data"), (dict, list)):
                        parsed["data"] = wrapper["data"]
                except Exception:
                    pass
            if isinstance(parsed, dict) and parsed.get("data"):
                return parsed
            if attempt == 0:
                time.sleep(0.5)
        return parsed if isinstance(parsed, dict) else {}

    def _yg_item(self, it):
        if not isinstance(it, dict):
            return None
        vid = str(it.get("video_id") if it.get("video_id") is not None else (it.get("id") or "")).strip()
        if not vid:
            return None
        return {"id": vid, "title": str(it.get("title") or it.get("video_title") or vid).strip(),
                "poster": str(it.get("cover") or it.get("cover_img") or "").strip(),
                "status": format_remarks(self.brandName, str(it.get("update_status") or "正片"))}

    def _yg_items(self, arr):
        out = []
        for it in arr or []:
            item = self._yg_item(it)
            if item:
                out.append(item)
        return out

    def _yg_home_items(self):
        d = self._yg_post("/api/home/homePage", {})
        inner = d.get("data") or {}
        return self._yg_items(inner.get("top_list") if isinstance(inner, dict) else [])

    def _yg_category(self, sub, page):
        d = self._yg_post("/api/theater/exploreList", {"page": page, "limit": 14})
        inner = d.get("data") or {}
        return self._yg_items(inner.get("list") if isinstance(inner, dict) else [])

    def _yg_search(self, keyword, page):
        d = self._yg_post("/api/search/result", {"keyword": keyword, "page": 1})
        inner = d.get("data") or {}
        return self._yg_items(inner.get("list") if isinstance(inner, dict) else [])

    def _yg_vid(self, vid):
        return int(vid) if str(vid).isdigit() else vid

    def _yg_detail(self, raw):
        d = self._yg_post("/api/playlet/detail", {"video_id": self._yg_vid(raw)})
        info = d.get("data") or {}
        if not isinstance(info, dict):
            info = {}
        eps = info.get("episodes") or []
        episodes = []
        for i in range(len(eps)):
            episodes.append({"name": "第%s集" % (i + 1), "value": {"agg": "yg", "vodId": raw, "ep": str(i + 1)}})
        if not episodes:
            raise ValueError("no episodes")
        return {"title": str(info.get("title") or raw), "poster": str(info.get("cover") or info.get("cover_img") or ""),
                "summary": str(info.get("description") or info.get("intro") or "野果短剧精选热播"),
                "status": format_remarks(self.brandName, "共%s集" % len(episodes)),
                "episodes": episodes}

    def _yg_resolve(self, ref):
        vid = str(ref.get("vodId") or "")
        try:
            ep = int(ref.get("ep") or 1)
        except Exception:
            ep = 1
        d = self._yg_post("/api/playlet/play", {"video_id": self._yg_vid(vid), "ep": ep})
        info = d.get("data") or {}
        url = str((info.get("video_url") or "") if isinstance(info, dict) else "").strip()
        if not url:
            raise ValueError("no play url")
        return url, {"User-Agent": self.IPHONE_UA, "Referer": self.YG_HOST + "/"}

    # ---------------- hg ----------------
    HG_HOST = "https://huangguo.video"
    HG_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/27.0.1 Mobile/15E148 Safari/604.1"

    def _hg_get(self, path):
        code, text = self._fetch(self.HG_HOST + path, ua=self.HG_UA, headers={"Cookie": "hg_age=1"}, timeout=8)
        return text

    def _hg_parse(self, html):
        items = []
        seen = set()
        for m in re.finditer(r'<article class="(?:video-card|search-content-card)[^"]*">([\s\S]*?)</article>', html or ""):
            block = m.group(1)
            link = re.search(r'<a\s+href="(/(?:video|series)/[^"]+)"', block)
            if not link:
                continue
            vid = link.group(1).strip("/")
            if vid in seen:
                continue
            seen.add(vid)
            img = re.search(r'<img[^>]+src="([^"]+)"', block)
            cover = img.group(1).strip() if img else ""
            if cover.startswith("/"):
                cover = self.HG_HOST + cover
            alt = re.search(r'<img[^>]+alt="([^"]*)"', block)
            title = alt.group(1).strip() if alt else vid
            items.append({"id": vid, "title": title, "poster": cover, "status": format_remarks(self.brandName, "正片")})
        return items

    def _hg_home_items(self):
        return self._hg_parse(self._hg_get("/videos"))[:20]

    def _hg_category(self, sub, page):
        return self._hg_parse(self._hg_get("/videos?category=1&page=" + str(page)))

    def _hg_search(self, keyword, page):
        if not keyword:
            return []
        return self._hg_parse(self._hg_get("/search?q=" + self._enc(keyword)))

    def _hg_detail(self, raw):
        html = self._hg_get("/" + raw)
        m = re.search(r'data-hls="([^"]+)"', html or "")
        episodes = []
        if m:
            episodes.append({"name": "正片", "value": {"agg": "hg", "directUrl": m.group(1)}})
        if not episodes:
            raise ValueError("no episodes")
        return {"title": "黄果剧集 " + raw, "poster": "", "summary": "黄果高清短剧连载中",
                "status": format_remarks(self.brandName, "共%s集" % len(episodes)),
                "episodes": episodes}

    def _hg_resolve(self, ref):
        url = str(ref.get("directUrl") or "")
        if not url:
            raise ValueError("missing ref")
        return url, {"User-Agent": self.HG_UA, "Referer": self.HG_HOST + "/", "Cookie": "hg_age=1"}

    # ---------------- aggregation shell ----------------
    def _plat_name(self, key):
        for pair in self.PLATS:
            if pair[0] == key:
                return pair[1]
        return ""

    def _to_card(self, key, item):
        return {
            "vod_id": key + "::" + item["id"],
            "vod_name": item["title"],
            "vod_pic": item.get("poster") or "",
            "vod_remarks": item.get("status") or self.brandName,
            "style": {"type": "rect", "ratio": 0.75}
        }

    def _cards(self, key, items):
        return [self._to_card(key, item) for item in items or []]

    def _engine_home_items(self, key):
        fn = {"qm": self._qm_home_items, "wg": self._wg_home_items, "xy": self._xy_home_items,
              "hk": self._hk_home_items, "jg": self._jg_home_items, "kb": self._kb_home_items,
              "yg": self._yg_home_items, "hg": self._hg_home_items}[key]
        return fn()

    def _engine_category(self, key, sub, page):
        if key == "qm":
            cards, has_more, raw_count = self._qm_category(sub, page)
            return cards, (page + 1 if has_more else page)
        if key == "wg":
            items = self._wg_category(sub, page)
            return items, (page + 1 if len(items) >= 20 else page)
        if key == "xy":
            items = self._xy_category(sub, page)
            return items, (page + 1 if len(items) >= 24 else page)
        if key == "hk":
            items = self._hk_category(sub, page)
            return items, (page + 1 if len(items) >= 20 else page)
        if key == "jg":
            items = self._jg_category(sub, page)
            return items, (page + 1 if items else page)
        if key == "kb":
            items = self._kb_category(sub, page)
            return items, page
        if key == "yg":
            items = self._yg_category(sub, page)
            return items, (page + 1 if len(items) >= 14 else page)
        if key == "hg":
            items = self._hg_category(sub, page)
            return items, (page + 1 if items else page)
        return [], page

    def _engine_search(self, key, keyword, page):
        fn = {"qm": self._qm_search, "wg": self._wg_search, "xy": self._xy_search,
              "hk": self._hk_search, "jg": self._jg_search, "kb": self._kb_search,
              "yg": self._yg_search, "hg": self._hg_search}[key]
        return fn(keyword, page)

    def _engine_detail(self, key, raw):
        fn = {"qm": self._qm_detail, "wg": self._wg_detail, "xy": self._xy_detail,
              "hk": self._hk_detail, "jg": self._jg_detail, "kb": self._kb_detail,
              "yg": self._yg_detail, "hg": self._hg_detail}[key]
        return fn(raw)

    def _engine_resolve(self, key, ref):
        fn = {"qm": self._qm_resolve, "wg": self._wg_resolve, "xy": self._xy_resolve,
              "hk": self._hk_resolve, "jg": self._jg_resolve, "kb": self._kb_resolve,
              "yg": self._yg_resolve, "hg": self._hg_resolve}[key]
        return fn(ref)

    def _page_num(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def _empty(self, page):
        return {"list": [], "page": page, "pagecount": page if page >= 1 else 1, "limit": 30, "total": 0}

    def homeContent(self, filter):
        classes = []
        filters = {}
        for pair in self.PLATS:
            key = pair[0]
            classes.append({"type_id": key, "type_name": pair[1]})
            subs = self.SUBS.get(key) or []
            if filter and len(subs) > 1:
                filters[key] = [{
                    "key": "agg_sub", "name": "分类", "init": subs[0][0],
                    "value": [{"n": s[1], "v": s[0]} for s in subs]
                }]
        result = {"class": classes}
        if filters:
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        items = []
        for pair in self.PLATS:
            key = pair[0]
            try:
                engine_items = self._engine_home_items(key)
            except Exception:
                engine_items = []
            items.extend(self._cards(key, (engine_items or [])[:6]))
            if len(items) >= 40:
                break
        return {"list": items[:40]}

    def categoryContent(self, tid, pg, filter, extend):
        page = self._page_num(pg)
        key = str(tid or "")
        if key not in self.SUBS:
            return self._empty(page)
        sub = ""
        if isinstance(extend, dict):
            sub = str(extend.get("agg_sub") or "")
        subs = self.SUBS[key]
        valid = [s[0] for s in subs]
        if sub not in valid:
            sub = subs[0][0]
        try:
            items, pagecount = self._engine_category(key, sub, page)
        except Exception:
            return self._empty(page)
        cards = self._cards(key, items)
        if not cards:
            return {"list": [], "page": page, "pagecount": pagecount if pagecount >= page else page, "limit": 30, "total": 0}
        return {"list": cards, "page": page, "pagecount": pagecount, "limit": 30, "total": pagecount * len(cards)}

    def searchContent(self, key, quick, pg="1"):
        page = self._page_num(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._empty(page)
        items = []
        for pair in self.PLATS:
            plat = pair[0]
            try:
                found = self._engine_search(plat, keyword, page)
            except Exception:
                found = []
            items.extend(self._cards(plat, (found or [])[:10]))
        if not items:
            return self._empty(page)
        return {"list": items, "page": page, "pagecount": page + 1, "limit": 30, "total": len(items)}

    def _brand_block(self):
        return [
            "🦋 %s官方交流群：@tvshare23" % self.siteName,
            "导演：🦋 蝴蝶影视",
            "当前主站：%s" % self.siteUrl,
            "━" * 28,
            "━" * 7
        ]

    def detailContent(self, ids):
        raw_id = ids[0] if isinstance(ids, (list, tuple)) and ids else ids
        text = str(raw_id or "")
        if "::" not in text:
            return {"list": []}
        key, raw = text.split("::", 1)
        if key not in self.SUBS or not raw:
            return {"list": []}
        try:
            info = self._engine_detail(key, raw)
        except Exception:
            return {"list": []}
        plat_name = self._plat_name(key)
        source_name = "🦋 蝴蝶" + plat_name + "专线"
        eps = []
        for ep in info["episodes"]:
            eps.append("%s$%s" % (ep["name"], json.dumps(ep["value"], ensure_ascii=False, separators=(",", ":"))))
        summary = str(info.get("summary") or "").strip()
        content_lines = self._brand_block()
        if summary:
            content_lines.append(summary)
        else:
            content_lines.append("标题：%s" % info.get("title") or "")
            content_lines.append("分类：%s" % plat_name)
            content_lines.append("片源：%s" % source_name)
            content_lines.append("编号：%s" % raw)
        vod = {
            "vod_id": text,
            "vod_name": info.get("title") or "",
            "vod_pic": info.get("poster") or "",
            "vod_actor": self.brandActor,
            "vod_director": self.brandDirector,
            "vod_remarks": info.get("status") or self.brandName,
            "vod_content": "\n".join(content_lines),
            "vod_play_from": source_name,
            "vod_play_url": "#".join(eps),
            "type_name": plat_name
        }
        vod["vod_tag"] = plat_name
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        text = str(id or "").strip()
        ref = {}
        if text.startswith("{"):
            try:
                parsed = json.loads(text)
                if isinstance(parsed, dict):
                    ref = parsed
            except Exception:
                ref = {}
        key = str(ref.get("agg") or "")
        if key not in self.SUBS:
            return {"parse": 0, "jx": 0, "url": ""}
        try:
            url, headers = self._engine_resolve(key, ref)
        except Exception:
            return {"parse": 0, "jx": 0, "url": ""}
        if not url:
            return {"parse": 0, "jx": 0, "url": ""}
        return {"parse": 0, "jx": 0, "url": url, "header": headers}

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249783337&sig=17c41be7252646e0
