# -*- coding: utf-8 -*-
# 樱花动漫 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.yinghuadongman)
import base64
import copy
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://www.91yhdm.com"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND = "蝴蝶影视"
SITE_NAME = "樱花动漫"
PAGE_SIZE = 36
POSTER_RATIO = 0.75

CATEGORIES = [
    ("1", "国内动漫"),
    ("2", "日韩动漫"),
    ("3", "欧美动漫"),
    ("20", "动漫电影"),
]

FILTERS = {'1': [{'key': 'class', 'name': '剧情', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '喜剧', 'v': '喜剧'}, {'n': '爱情', 'v': '爱情'}, {'n': '恐怖', 'v': '恐怖'}, {'n': '动作', 'v': '动作'}, {'n': '科幻', 'v': '科幻'}, {'n': '剧情', 'v': '剧情'}, {'n': '战争', 'v': '战争'}, {'n': '警匪', 'v': '警匪'}, {'n': '犯罪', 'v': '犯罪'}, {'n': '动画', 'v': '动画'}, {'n': '奇幻', 'v': '奇幻'}, {'n': '武侠', 'v': '武侠'}, {'n': '冒险', 'v': '冒险'}]}, {'key': 'area', 'name': '地区', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '大陆', 'v': '大陆'}, {'n': '香港', 'v': '香港'}, {'n': '台湾', 'v': '台湾'}, {'n': '澳门', 'v': '澳门'}]}, {'key': 'year', 'name': '年份', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '2026', 'v': '2026'}, {'n': '2025', 'v': '2025'}, {'n': '2024', 'v': '2024'}, {'n': '2023', 'v': '2023'}, {'n': '2022', 'v': '2022'}, {'n': '2021', 'v': '2021'}, {'n': '2020', 'v': '2020'}, {'n': '2019', 'v': '2019'}, {'n': '2018', 'v': '2018'}, {'n': '2017', 'v': '2017'}, {'n': '2016', 'v': '2016'}]}, {'key': 'lang', 'name': '语言', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '国语', 'v': '国语'}, {'n': '粤语', 'v': '粤语'}, {'n': '英语', 'v': '英语'}]}, {'key': 'by', 'name': '排序', 'init': '', 'value': [{'n': '默认', 'v': ''}, {'n': '最新', 'v': 'time'}, {'n': '人气', 'v': 'hits'}, {'n': '评分', 'v': 'score'}]}, {'key': 'letter', 'name': '字母', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': 'A', 'v': 'A'}, {'n': 'B', 'v': 'B'}, {'n': 'C', 'v': 'C'}, {'n': 'D', 'v': 'D'}, {'n': 'E', 'v': 'E'}, {'n': 'F', 'v': 'F'}, {'n': 'G', 'v': 'G'}, {'n': 'H', 'v': 'H'}, {'n': 'I', 'v': 'I'}, {'n': 'J', 'v': 'J'}, {'n': 'K', 'v': 'K'}, {'n': 'L', 'v': 'L'}, {'n': 'M', 'v': 'M'}, {'n': 'N', 'v': 'N'}, {'n': 'O', 'v': 'O'}, {'n': 'P', 'v': 'P'}, {'n': 'Q', 'v': 'Q'}, {'n': 'R', 'v': 'R'}, {'n': 'S', 'v': 'S'}, {'n': 'T', 'v': 'T'}, {'n': 'U', 'v': 'U'}, {'n': 'V', 'v': 'V'}, {'n': 'W', 'v': 'W'}, {'n': 'X', 'v': 'X'}, {'n': 'Y', 'v': 'Y'}, {'n': 'Z', 'v': 'Z'}, {'n': '0-9', 'v': '0'}]}], '2': [{'key': 'class', 'name': '剧情', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '喜剧', 'v': '喜剧'}, {'n': '爱情', 'v': '爱情'}, {'n': '恐怖', 'v': '恐怖'}, {'n': '动作', 'v': '动作'}, {'n': '科幻', 'v': '科幻'}, {'n': '剧情', 'v': '剧情'}, {'n': '战争', 'v': '战争'}, {'n': '警匪', 'v': '警匪'}, {'n': '犯罪', 'v': '犯罪'}, {'n': '动画', 'v': '动画'}, {'n': '奇幻', 'v': '奇幻'}, {'n': '武侠', 'v': '武侠'}, {'n': '冒险', 'v': '冒险'}]}, {'key': 'area', 'name': '地区', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '日本', 'v': '日本'}, {'n': '韩国', 'v': '韩国'}]}, {'key': 'year', 'name': '年份', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '2026', 'v': '2026'}, {'n': '2025', 'v': '2025'}, {'n': '2024', 'v': '2024'}, {'n': '2023', 'v': '2023'}, {'n': '2022', 'v': '2022'}, {'n': '2021', 'v': '2021'}, {'n': '2020', 'v': '2020'}, {'n': '2019', 'v': '2019'}, {'n': '2018', 'v': '2018'}, {'n': '2017', 'v': '2017'}, {'n': '2016', 'v': '2016'}]}, {'key': 'lang', 'name': '语言', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '日语', 'v': '日语'}, {'n': '韩语', 'v': '韩语'}, {'n': '国语', 'v': '国语'}, {'n': '粤语', 'v': '粤语'}, {'n': '英语', 'v': '英语'}]}, {'key': 'by', 'name': '排序', 'init': '', 'value': [{'n': '默认', 'v': ''}, {'n': '最新', 'v': 'time'}, {'n': '人气', 'v': 'hits'}, {'n': '评分', 'v': 'score'}]}, {'key': 'letter', 'name': '字母', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': 'A', 'v': 'A'}, {'n': 'B', 'v': 'B'}, {'n': 'C', 'v': 'C'}, {'n': 'D', 'v': 'D'}, {'n': 'E', 'v': 'E'}, {'n': 'F', 'v': 'F'}, {'n': 'G', 'v': 'G'}, {'n': 'H', 'v': 'H'}, {'n': 'I', 'v': 'I'}, {'n': 'J', 'v': 'J'}, {'n': 'K', 'v': 'K'}, {'n': 'L', 'v': 'L'}, {'n': 'M', 'v': 'M'}, {'n': 'N', 'v': 'N'}, {'n': 'O', 'v': 'O'}, {'n': 'P', 'v': 'P'}, {'n': 'Q', 'v': 'Q'}, {'n': 'R', 'v': 'R'}, {'n': 'S', 'v': 'S'}, {'n': 'T', 'v': 'T'}, {'n': 'U', 'v': 'U'}, {'n': 'V', 'v': 'V'}, {'n': 'W', 'v': 'W'}, {'n': 'X', 'v': 'X'}, {'n': 'Y', 'v': 'Y'}, {'n': 'Z', 'v': 'Z'}, {'n': '0-9', 'v': '0'}]}], '3': [{'key': 'class', 'name': '剧情', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '喜剧', 'v': '喜剧'}, {'n': '爱情', 'v': '爱情'}, {'n': '恐怖', 'v': '恐怖'}, {'n': '动作', 'v': '动作'}, {'n': '科幻', 'v': '科幻'}, {'n': '剧情', 'v': '剧情'}, {'n': '战争', 'v': '战争'}, {'n': '警匪', 'v': '警匪'}, {'n': '犯罪', 'v': '犯罪'}, {'n': '动画', 'v': '动画'}, {'n': '奇幻', 'v': '奇幻'}, {'n': '武侠', 'v': '武侠'}, {'n': '冒险', 'v': '冒险'}]}, {'key': 'area', 'name': '地区', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '美国', 'v': '美国'}, {'n': '法国', 'v': '法国'}, {'n': '英国', 'v': '英国'}, {'n': '德国', 'v': '德国'}, {'n': '意大利', 'v': '意大利'}, {'n': '西班牙', 'v': '西班牙'}, {'n': '葡萄牙', 'v': '葡萄牙'}, {'n': '比利时', 'v': '比利时'}, {'n': '挪威', 'v': '挪威'}, {'n': '丹麦', 'v': '丹麦'}, {'n': '俄罗斯', 'v': '俄罗斯'}]}, {'key': 'year', 'name': '年份', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '2026', 'v': '2026'}, {'n': '2025', 'v': '2025'}, {'n': '2024', 'v': '2024'}, {'n': '2023', 'v': '2023'}, {'n': '2022', 'v': '2022'}, {'n': '2021', 'v': '2021'}, {'n': '2020', 'v': '2020'}, {'n': '2019', 'v': '2019'}, {'n': '2018', 'v': '2018'}, {'n': '2017', 'v': '2017'}, {'n': '2016', 'v': '2016'}]}, {'key': 'lang', 'name': '语言', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '英语', 'v': '英语'}, {'n': '法语', 'v': '法语'}, {'n': '德语', 'v': '德语'}, {'n': '国语', 'v': '国语'}, {'n': '粤语', 'v': '粤语'}]}, {'key': 'by', 'name': '排序', 'init': '', 'value': [{'n': '默认', 'v': ''}, {'n': '最新', 'v': 'time'}, {'n': '人气', 'v': 'hits'}, {'n': '评分', 'v': 'score'}]}, {'key': 'letter', 'name': '字母', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': 'A', 'v': 'A'}, {'n': 'B', 'v': 'B'}, {'n': 'C', 'v': 'C'}, {'n': 'D', 'v': 'D'}, {'n': 'E', 'v': 'E'}, {'n': 'F', 'v': 'F'}, {'n': 'G', 'v': 'G'}, {'n': 'H', 'v': 'H'}, {'n': 'I', 'v': 'I'}, {'n': 'J', 'v': 'J'}, {'n': 'K', 'v': 'K'}, {'n': 'L', 'v': 'L'}, {'n': 'M', 'v': 'M'}, {'n': 'N', 'v': 'N'}, {'n': 'O', 'v': 'O'}, {'n': 'P', 'v': 'P'}, {'n': 'Q', 'v': 'Q'}, {'n': 'R', 'v': 'R'}, {'n': 'S', 'v': 'S'}, {'n': 'T', 'v': 'T'}, {'n': 'U', 'v': 'U'}, {'n': 'V', 'v': 'V'}, {'n': 'W', 'v': 'W'}, {'n': 'X', 'v': 'X'}, {'n': 'Y', 'v': 'Y'}, {'n': 'Z', 'v': 'Z'}, {'n': '0-9', 'v': '0'}]}], '20': [{'key': 'class', 'name': '剧情', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '喜剧', 'v': '喜剧'}, {'n': '爱情', 'v': '爱情'}, {'n': '恐怖', 'v': '恐怖'}, {'n': '动作', 'v': '动作'}, {'n': '科幻', 'v': '科幻'}, {'n': '剧情', 'v': '剧情'}, {'n': '战争', 'v': '战争'}, {'n': '警匪', 'v': '警匪'}, {'n': '犯罪', 'v': '犯罪'}, {'n': '动画', 'v': '动画'}, {'n': '奇幻', 'v': '奇幻'}, {'n': '武侠', 'v': '武侠'}, {'n': '冒险', 'v': '冒险'}]}, {'key': 'area', 'name': '地区', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '大陆', 'v': '大陆'}, {'n': '香港', 'v': '香港'}, {'n': '台湾', 'v': '台湾'}, {'n': '日本', 'v': '日本'}, {'n': '韩国', 'v': '韩国'}, {'n': '美国', 'v': '美国'}, {'n': '法国', 'v': '法国'}, {'n': '英国', 'v': '英国'}, {'n': '德国', 'v': '德国'}, {'n': '意大利', 'v': '意大利'}, {'n': '西班牙', 'v': '西班牙'}, {'n': '葡萄牙', 'v': '葡萄牙'}, {'n': '比利时', 'v': '比利时'}, {'n': '挪威', 'v': '挪威'}, {'n': '丹麦', 'v': '丹麦'}, {'n': '俄罗斯', 'v': '俄罗斯'}, {'n': '泰国', 'v': '泰国'}, {'n': '印度', 'v': '印度'}]}, {'key': 'year', 'name': '年份', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '2026', 'v': '2026'}, {'n': '2025', 'v': '2025'}, {'n': '2024', 'v': '2024'}, {'n': '2023', 'v': '2023'}, {'n': '2022', 'v': '2022'}, {'n': '2021', 'v': '2021'}, {'n': '2020', 'v': '2020'}, {'n': '2019', 'v': '2019'}, {'n': '2018', 'v': '2018'}, {'n': '2017', 'v': '2017'}, {'n': '2016', 'v': '2016'}]}, {'key': 'lang', 'name': '语言', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': '国语', 'v': '国语'}, {'n': '粤语', 'v': '粤语'}, {'n': '日语', 'v': '日语'}, {'n': '韩语', 'v': '韩语'}, {'n': '英语', 'v': '英语'}, {'n': '法语', 'v': '法语'}, {'n': '德语', 'v': '德语'}]}, {'key': 'by', 'name': '排序', 'init': '', 'value': [{'n': '默认', 'v': ''}, {'n': '最新', 'v': 'time'}, {'n': '人气', 'v': 'hits'}, {'n': '评分', 'v': 'score'}]}, {'key': 'letter', 'name': '字母', 'init': '', 'value': [{'n': '全部', 'v': ''}, {'n': 'A', 'v': 'A'}, {'n': 'B', 'v': 'B'}, {'n': 'C', 'v': 'C'}, {'n': 'D', 'v': 'D'}, {'n': 'E', 'v': 'E'}, {'n': 'F', 'v': 'F'}, {'n': 'G', 'v': 'G'}, {'n': 'H', 'v': 'H'}, {'n': 'I', 'v': 'I'}, {'n': 'J', 'v': 'J'}, {'n': 'K', 'v': 'K'}, {'n': 'L', 'v': 'L'}, {'n': 'M', 'v': 'M'}, {'n': 'N', 'v': 'N'}, {'n': 'O', 'v': 'O'}, {'n': 'P', 'v': 'P'}, {'n': 'Q', 'v': 'Q'}, {'n': 'R', 'v': 'R'}, {'n': 'S', 'v': 'S'}, {'n': 'T', 'v': 'T'}, {'n': 'U', 'v': 'U'}, {'n': 'V', 'v': 'V'}, {'n': 'W', 'v': 'W'}, {'n': 'X', 'v': 'X'}, {'n': 'Y', 'v': 'Y'}, {'n': 'Z', 'v': 'Z'}, {'n': '0-9', 'v': '0'}]}]}

FILTER_SLOT = {
    "tid": 0, "area": 1, "by": 2, "class": 3, "lang": 4, "letter": 5,
    "plot": 6, "state": 7, "page": 8, "tag": 9, "version": 10, "year": 11,
}

CARD_PRIMARY_RE = re.compile(r'<a[^>]+class=["\'][^"\']*stui-vodlist__thumb[^"\']*["\'][^>]*>([\s\S]{0,600}?)</a>', re.I)
CARD_FALLBACK_RE = re.compile(r'class=["\']title text-overflow["\'][^>]*>\s*<a[^>]+href=["\']/vodhtml/(\d+)\.html["\'][^>]*title=["\']([^"\']*)["\']', re.I)
HREF_VID_RE = re.compile(r'href=["\']/vodhtml/(\d+)\.html["\']', re.I)
TITLE_ATTR_RE = re.compile(r'title=["\']([^"\']*)["\']', re.I)
PIC_TEXT_RE = re.compile(r'<span[^>]+class=["\'][^"\']*pic-text[^"\']*["\'][^>]*>([\s\S]*?)</span>', re.I)
DETAIL_BLOCK_RE1 = re.compile(r'<div[^>]+class=["\']stui-content__detail["\'][^>]*>([\s\S]*?)<div[^>]+class=["\']play-btn', re.I)
DETAIL_BLOCK_RE2 = re.compile(r'<div[^>]+class=["\']stui-content__detail["\'][^>]*>([\s\S]{0,4000})', re.I)
H1_RE = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
DETAIL_PIC_RE = re.compile(r'<div[^>]+class=["\']stui-content__thumb["\'][^>]*>[\s\S]{0,400}?data-original=["\']([^"\']+)["\']', re.I)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', re.I)
THUMB_REM_RE = re.compile(r'<div[^>]+class=["\']stui-content__thumb["\'][^>]*>[\s\S]{0,600}?<span[^>]+class=["\'][^"\']*pic-text[^"\']*["\'][^>]*>([\s\S]*?)</span>', re.I)
DESC_RE1 = re.compile(r'id=["\']desc["\'][\s\S]{0,800}?<div[^>]+class=["\']stui-pannel_bd["\'][^>]*>\s*<p[^>]*>([\s\S]*?)</p>', re.I)
DESC_RE2 = re.compile(r'<p[^>]+class=["\']desc[^"\']*["\'][^>]*>([\s\S]*?)</p>', re.I)
YEAR_FALLBACK_RE = re.compile(r'年份：\s*</span>\s*<a[^>]*>\s*((?:19|20)\d{2})', re.I)
YEAR_VALID_RE = re.compile(r"^(19|20)\d{2}$")
TABS_UL_RE = re.compile(r'<ul[^>]+class=["\']nav nav-tabs[^"\']*["\'][^>]*>([\s\S]*?)</ul>', re.I)
TAB_A_RE = re.compile(r'<a[^>]+data-toggle=["\']tab["\'][^>]*>([\s\S]*?)</a>', re.I)
SMALL_RE = re.compile(r"<small>[\s\S]*?</small>", re.I)
PLAYLIST_UL_RE = re.compile(r'<ul[^>]+class=["\']stui-content__playlist[^"\']*["\'][^>]*>([\s\S]*?)</ul>', re.I)
EP_A_RE = re.compile(r'<a[^>]+href=["\'](/vodplay/[^"\']+\.html)["\'][^>]*>([^<]*)</a>', re.I)
GUESS_UL_RE = re.compile(r'<ul[^>]+class=["\'][^"\']*stui-vodlist__bd[^"\']*["\'][^>]*>([\s\S]*?)</ul>', re.I)
PLAYER_AAAA_RE = re.compile(r"player_aaaa\s*=\s*(\{[\s\S]*?\})\s*</script>", re.I)
CFG_URL_RE = re.compile(r'"url"\s*:\s*"([^"]*)"')
CFG_ENC_RE = re.compile(r'"encrypt"\s*:\s*"?(\d)"?')
IFRAME_RE = re.compile(r'<iframe[^>]+src=["\']([^"\']+)["\']', re.I)
IFRAME_URL_PARAM_RE = re.compile(r"[?&]url=([^&\"']+)")
M3U8_SCAN_RE = re.compile(r"(https?://[^\s\"'\\]+\.m3u8[^\s\"'\\]*)", re.I)
VIDEO_DIRECT_RE = re.compile(r"\.(m3u8|mp4|flv|mkv|avi|ts|m4a)(?:[?#]|$)", re.I)
COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")


def strip_tags(html_text):
    s = str(html_text or "")
    s = COMMENT_RE.sub("", s)
    s = TAG_RE.sub(" ", s)
    s = s.replace("&nbsp;", " ")
    s = s.replace("&amp;", "&").replace("&quot;", '"').replace("&#39;", "'")
    s = s.replace("&lt;", "<").replace("&gt;", ">")
    return WS_RE.sub(" ", s).strip()


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST

    def getName(self):
        return SITE_NAME

    def init(self, extend=""):
        host = ""
        ext = extend
        if isinstance(ext, str) and ext.strip():
            text = ext.strip()
            if text.startswith("http"):
                host = text
            else:
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        host = str(data.get("host") or "")
                except Exception:
                    pass
        elif isinstance(ext, dict):
            host = str(ext.get("host") or "")
        if host.startswith("http"):
            self.host = host.rstrip("/")

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- fetch ----------

    def _headers(self, referer=None):
        return {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": referer if referer else (self.host + "/"),
        }

    def _fetch_once(self, url, referer=None):
        resp = requests.get(url, headers=self._headers(referer), timeout=8)
        if resp is not None and resp.status_code == 200 and resp.text:
            return resp.text
        return ""

    def _fetch(self, url, referer=None):
        target = url
        if target.startswith("//"):
            target = "https:" + target
        elif target.startswith("/"):
            target = self.host + target
        try:
            body = self._fetch_once(target, referer)
            if body:
                return body
        except Exception:
            if target.startswith("https://"):
                try:
                    return self._fetch_once("http://" + target[8:], referer)
                except Exception:
                    return ""
        return ""

    # ---------- url / poster ----------

    def _resolve_url(self, raw_url):
        if not raw_url:
            return ""
        u = str(raw_url).strip().replace("&amp;", "&")
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("http://") or u.startswith("https://"):
            return u
        path = u if u.startswith("/") else ("/" + u)
        return self.host.rstrip("/") + path

    def _format_poster(self, raw_url):
        if not raw_url:
            return ""
        u = str(raw_url).strip()
        if not u or "load.gif" in u:
            return ""
        full = self._resolve_url(u)
        if not full:
            return ""
        referer = self.host + "/"
        return full + "@Referer=" + quote(referer, safe="") + "&User-Agent=" + quote(UA, safe="")

    # ---------- cards ----------

    def _parse_cards(self, html_text):
        text = str(html_text or "")
        items = []
        seen = set()
        if not text:
            return items
        for m in CARD_PRIMARY_RE.finditer(text):
            full_tag = m.group(0)
            inner = m.group(1) or ""
            hm = HREF_VID_RE.search(full_tag)
            if not hm:
                continue
            vid = hm.group(1)
            if not vid or vid in seen:
                continue
            tm = TITLE_ATTR_RE.search(full_tag)
            title = strip_tags(tm.group(1)) if tm else ""
            if not title:
                title = strip_tags(inner) or vid
            raw_pic = ""
            for attr in ("data-original", "data-src", "src"):
                pm = re.search(attr + r'=["\']([^"\']*)["\']', full_tag, re.I)
                if pm:
                    raw_pic = pm.group(1)
                    break
            rm = PIC_TEXT_RE.search(inner)
            remark = strip_tags(rm.group(1)) if rm else ""
            status = (BRAND + " | " + remark) if remark else BRAND
            seen.add(vid)
            items.append({
                "vod_id": vid,
                "vod_name": title,
                "vod_pic": self._format_poster(raw_pic),
                "vod_remarks": status,
                "style": {"type": "rect", "ratio": POSTER_RATIO},
            })
        if items:
            return items
        for m in CARD_FALLBACK_RE.finditer(text):
            f_vid = m.group(1)
            if not f_vid or f_vid in seen:
                continue
            seen.add(f_vid)
            items.append({
                "vod_id": f_vid,
                "vod_name": strip_tags(m.group(2)) or f_vid,
                "vod_pic": "",
                "vod_remarks": BRAND,
                "style": {"type": "rect", "ratio": POSTER_RATIO},
            })
        return items

    # ---------- url builders ----------

    def _build_show_url(self, tid, page, filters):
        segs = ["", "", "", "", "", "", "", "", "", "", "", ""]
        segs[0] = str(tid or "")
        f = filters or {}
        for k in f:
            slot = FILTER_SLOT.get(k)
            if slot is None:
                continue
            val = str(f.get(k) or "").strip()
            if not val or val == "全部" or val == "0":
                continue
            segs[slot] = val
        try:
            pn = int(page)
        except Exception:
            pn = 1
        if pn > 1:
            segs[8] = str(pn)
        return self.host + "/vodshow/" + "-".join(quote(s, safe="") for s in segs) + ".html"

    def _build_type_url(self, tid, page):
        try:
            pn = int(page)
        except Exception:
            pn = 1
        if pn > 1:
            return self._build_show_url(tid, pn, {})
        return self.host + "/vodtypehtml/" + quote(str(tid), safe="") + ".html"

    def _build_search_url(self, keyword, page):
        segs = ["", "", "", "", "", "", "", "", "", "", "", "", "", ""]
        segs[0] = str(keyword or "")
        try:
            pn = int(page)
        except Exception:
            pn = 1
        if pn > 1:
            segs[10] = str(pn)
        return self.host + "/vodsearch/" + "-".join(quote(s, safe="") for s in segs) + ".html"

    # ---------- home / category / search ----------

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

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        result = {"class": classes}
        if filter:
            result["filters"] = copy.deepcopy(FILTERS)
        return result

    def homeVideoContent(self):
        html = self._fetch(self.host + "/")
        items = self._parse_cards(html)
        if not items and CATEGORIES:
            html2 = self._fetch(self._build_type_url(CATEGORIES[0][0], 1))
            items = self._parse_cards(html2)
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
        filters = extend if isinstance(extend, dict) else {}
        has_active = False
        for k in filters:
            v = str(filters.get(k) or "").strip()
            if v and v != "全部" and v != "0":
                has_active = True
                break
        if page == 1 and not has_active:
            target = self._build_type_url(cid, 1)
        else:
            target = self._build_show_url(cid, page, filters)
        html = self._fetch(target)
        items = self._parse_cards(html)
        if not items and page == 1 and not has_active:
            html2 = self._fetch(self._build_show_url(cid, 1, {}))
            items = self._parse_cards(html2)
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
        html = self._fetch(self._build_search_url(keyword, page))
        items = self._parse_cards(html)
        if not items and page == 1:
            fallback = self.host + "/vodsearch/-------------.html?wd=" + quote(keyword, safe="")
            html2 = self._fetch(fallback)
            items = self._parse_cards(html2)
        return self._page_form(items, page)

    # ---------- detail ----------

    def _extract_field(self, block, label):
        reg = re.compile(r'<span[^>]+class=["\']text-muted[^"\']*["\'][^>]*>\s*' + label + r'：\s*</span>([\s\S]*?)(?:<span[^>]+class=["\']split-line["\']|</p>)', re.I)
        m = reg.search(block or "")
        return strip_tags(m.group(1)) if m else ""

    def _parse_sources(self, html_text):
        text = str(html_text or "")
        tab_names = []
        tabs_m = TABS_UL_RE.search(text)
        if tabs_m:
            for tm in TAB_A_RE.finditer(tabs_m.group(1)):
                tab_names.append(strip_tags(SMALL_RE.sub("", tm.group(1))))
        sources = []
        idx = 0
        for pm in PLAYLIST_UL_RE.finditer(text):
            ul_body = pm.group(1) or ""
            episodes = []
            count = 0
            for em in EP_A_RE.finditer(ul_body):
                count += 1
                play_path = em.group(1)
                ep_name = strip_tags(em.group(2)) or ("第" + str(count) + "集")
                ep_name = ep_name.replace("$", "_").replace("#", "_")
                episodes.append((ep_name, play_path))
            if episodes:
                raw_name = tab_names[idx] if idx < len(tab_names) and tab_names[idx] else ("专线" + str(idx + 1))
                sources.append(("🦋 " + raw_name, episodes))
            idx += 1
        return sources

    def _guess_like(self, html_text, self_vid):
        text = str(html_text or "")
        pos = text.find("猜你喜欢")
        if pos < 0:
            return []
        seg = text[pos:]
        m = GUESS_UL_RE.search(seg)
        if not m:
            return []
        block = m.group(0)
        out = []
        seen = set()
        for cm in CARD_PRIMARY_RE.finditer(block):
            full_tag = cm.group(0)
            hm = HREF_VID_RE.search(full_tag)
            if not hm:
                continue
            rvid = hm.group(1)
            if not rvid or rvid == self_vid or rvid in seen:
                continue
            tm = TITLE_ATTR_RE.search(full_tag)
            title = strip_tags(tm.group(1)) if tm else ""
            if not title:
                title = strip_tags(cm.group(1) or "") or rvid
            seen.add(rvid)
            out.append((rvid, title))
        return out

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        vid = re.sub(r"\D", "", raw)
        if not vid:
            return {"list": []}
        page_url = self.host + "/vodhtml/" + vid + ".html"
        html = self._fetch(page_url)

        dm = DETAIL_BLOCK_RE1.search(html) or DETAIL_BLOCK_RE2.search(html)
        detail_block = dm.group(1) if dm else html

        h1m = H1_RE.search(detail_block) or H1_RE.search(html)
        title = strip_tags(h1m.group(1)) if h1m else vid

        pic_m = DETAIL_PIC_RE.search(html) or OG_IMAGE_RE.search(html)
        poster = self._format_poster(pic_m.group(1)) if pic_m else ""

        type_text = self._extract_field(detail_block, "类型")
        area_text = self._extract_field(detail_block, "地区")
        year_text = self._extract_field(detail_block, "年份")
        update_text = self._extract_field(detail_block, "更新")
        if not YEAR_VALID_RE.match(year_text or ""):
            ym = YEAR_FALLBACK_RE.search(detail_block)
            year_text = ym.group(1) if ym else ""

        rem_m = THUMB_REM_RE.search(html)
        remark = strip_tags(rem_m.group(1)) if rem_m else (("更新：" + update_text) if update_text else "")
        status = (BRAND + " | " + remark) if remark else BRAND

        desc_m = DESC_RE1.search(html)
        raw_desc = strip_tags(desc_m.group(1)) if desc_m else ""
        if not raw_desc:
            dm2 = DESC_RE2.search(detail_block)
            if dm2:
                raw_desc = strip_tags(dm2.group(1))
                raw_desc = re.sub(r"^简介：\s*", "", raw_desc)
                raw_desc = re.sub(r"\s*详情\s*$", "", raw_desc)

        sources = self._parse_sources(html)
        related = self._guess_like(html, vid)

        play_from_parts = []
        play_url_parts = []
        for sname, episodes in sources:
            play_from_parts.append(sname)
            ep_strs = []
            for ep_name, play_path in episodes:
                ep_strs.append(ep_name + "$" + play_path)
            play_url_parts.append("#".join(ep_strs))
        if related:
            play_from_parts.append("相关推荐")
            rel_strs = []
            for rvid, rtitle in related:
                clean_title = rtitle.replace("$", "_").replace("#", "_")
                rel_strs.append(clean_title + "$rel:" + rvid)
            play_url_parts.append("#".join(rel_strs))

        block = self._brand_block()
        if raw_desc:
            content = block + "\n" + raw_desc
        else:
            lines = [
                "标题：" + title,
                "分类：" + type_text,
                "片源：" + (play_from_parts[0] if play_from_parts else ""),
                "编号：" + vid,
            ]
            if related:
                names = [rtitle for _, rtitle in related[:6]]
                lines.append("相关推荐：" + " / ".join(names))
            content = block + "\n" + "\n".join(lines)

        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": status,
            "vod_content": content,
            "vod_play_from": "$$$".join(play_from_parts),
            "vod_play_url": "$$$".join(play_url_parts),
        }
        if type_text:
            vod["type_name"] = type_text
        if area_text:
            vod["vod_area"] = area_text
        if year_text:
            vod["vod_year"] = year_text
        return {"list": [vod]}

    # ---------- player ----------

    def _resolve_play(self, play_path, headers):
        if play_path.startswith("http") and VIDEO_DIRECT_RE.search(play_path):
            return {"parse": 0, "url": play_path, "header": headers}
        target = self._resolve_url(play_path)
        html = self._fetch(target)
        real = ""
        pm = PLAYER_AAAA_RE.search(html)
        if pm:
            raw_json = pm.group(1)
            obj = None
            try:
                parsed = json.loads(raw_json)
                if isinstance(parsed, dict):
                    obj = parsed
            except Exception:
                obj = None
            if obj is None:
                um = CFG_URL_RE.search(raw_json)
                em = CFG_ENC_RE.search(raw_json)
                obj = {"url": um.group(1) if um else "", "encrypt": em.group(1) if em else "0"}
            if isinstance(obj, dict) and obj.get("url"):
                real = str(obj.get("url")).replace("\\/", "/")
                enc = str(obj.get("encrypt") or "0")
                if enc == "1":
                    real = unquote(real)
                elif enc == "2":
                    decoded = ""
                    try:
                        decoded = base64.b64decode(real).decode("utf-8", "ignore")
                    except Exception:
                        decoded = ""
                    if decoded:
                        real = unquote(decoded)
        if not real:
            im = IFRAME_RE.search(html)
            if im:
                src = im.group(1)
                sm = IFRAME_URL_PARAM_RE.search(src)
                real = unquote(sm.group(1)) if sm else self._resolve_url(src)
        if not real:
            mm = M3U8_SCAN_RE.search(html)
            if mm:
                real = mm.group(1)
        if not real:
            return {"parse": 1, "url": target, "header": headers}
        final = self._resolve_url(real)
        if VIDEO_DIRECT_RE.search(final):
            return {"parse": 0, "url": final, "header": headers}
        return {"parse": 1, "url": final, "header": headers}

    def playerContent(self, flag, pid, vipFlags):
        headers = {
            "User-Agent": UA,
            "Referer": self.host + "/",
            "Origin": self.host,
        }
        raw = str(pid or "")
        if raw.startswith("rel:"):
            rvid = raw[4:].strip()
            target_url = self.host + "/vodhtml/" + rvid + ".html"
            html = self._fetch(target_url)
            sources = self._parse_sources(html)
            first_path = ""
            for sname, episodes in sources:
                if episodes:
                    first_path = episodes[0][1]
                    break
            if first_path:
                return self._resolve_play(first_path, headers)
            return {"parse": 1, "url": target_url, "header": headers}
        if not raw:
            return {"parse": 1, "url": self.host + "/", "header": headers}
        return self._resolve_play(raw, headers)

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249910717&sig=d2923f1e7be9c678
