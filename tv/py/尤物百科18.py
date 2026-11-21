#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import re
import json
import ssl
import gzip
import zlib
import time
import http.cookiejar
import urllib.request
import urllib.parse
from urllib.parse import quote, urlsplit

from base.spider import Spider as BaseSpider


def format_remarks(brand="蝴蝶影视", meta=""):
    clean_meta = str(meta or "").strip()
    clean_meta = re.sub(r"[\r\n\t]+", " ", clean_meta).strip()
    if clean_meta:
        return "%s | %s" % (brand, clean_meta)
    return brand


def unpack_packer(src):
    text = str(src or "")
    m = re.search(r"\}\('([\s\S]*)',(\d+),(\d+),'([\s\S]*)'\.split\('\|'\)", text)
    if not m:
        return ""
    payload = m.group(1)
    radix = int(m.group(2))
    count = int(m.group(3))
    keywords = m.group(4).split("|")

    def encode_base(n):
        if n < radix:
            return str(n) if n < 10 else chr(n + 87)
        return encode_base(n // radix) + encode_base(n % radix)

    table = {}
    for i in range(count - 1, -1, -1):
        key = encode_base(i)
        table[key] = keywords[i] if i < len(keywords) and keywords[i] else key
    payload = payload.replace("\\\\", "\\").replace('\\"', '"').replace("\\'", "'")
    return re.sub(r"[A-Za-z0-9_]+", lambda mm: table.get(mm.group(0), mm.group(0)), payload)


class Spider(BaseSpider):
    BASE_CATS = [
        {"type_id": "latest", "type_name": "最新推荐", "slug": ""},
        {"type_id": "twitter", "type_name": "推特", "slug": "twitter"},
        {"type_id": "onlyfans", "type_name": "onlyfans", "slug": "onlyfans"},
        {"type_id": "tangxin", "type_name": "糖心vlog", "slug": "tangxin"},
        {"type_id": "madou", "type_name": "麻豆传媒", "slug": "madou"},
        {"type_id": "duanju", "type_name": "尤物短剧", "slug": "duanju"},
        {"type_id": "chigua", "type_name": "吃瓜", "slug": "chigua"}
    ]
    AUTHORS = [
            ["3", "小小绘 (2284粉)"],
            ["595", "Velevt8800 (1836粉)"],
            ["657", "小野整活部 (802粉)"],
            ["372", "季雨 (1930粉)"],
            ["14", "困困狗 (2239粉)"],
            ["160", "林婉婉 (505粉)"],
            ["18512", "凉仔 (306粉)"],
            ["24", "元元 (205粉)"],
            ["635", "纲手 (681粉)"],
            ["636", "热宝 (636粉)"],
            ["300", "九九橙 (1642粉)"],
            ["367", "咬耳朵 (376粉)"],
            ["672", "美奈 (598粉)"],
            ["274", "徐婉 (918粉)"],
            ["272", "nide xiaogou (587粉)"],
            ["12442", "坏小狗 (310粉)"],
            ["5", "小野猫kiki (1540粉)"],
            ["707", "嘿嘿蝴蝶 (104粉)"],
            ["17193", "曾强 (69粉)"],
            ["478", "一个ren (545粉)"],
            ["62", "cocopie (451粉)"],
            ["8", "懒懒猪 (794粉)"],
            ["1416", "小月喵 (288粉)"],
            ["7", "NPXVIP (1328粉)"],
            ["575", "一只顶美 (1230粉)"],
            ["6", "是小桃呢 (1211粉)"],
            ["201", "跳跳羊 (1303粉)"],
            ["4", "兔崽爱喷水 (425粉)"],
            ["1289", "尤物合集 (353粉)"],
            ["709", "桃乃沐香奈 (246粉)"],
            ["46", "莎弥拉 (303粉)"],
            ["712", "白虎喵 (482粉)"],
            ["192", "星野兔 (457粉)"],
            ["33", "全世界最好的酒 (204粉)"],
            ["58", "linjianvhai (374粉)"],
            ["593", "梓怡学妹 (464粉)"],
            ["1", "噗噗 (1153粉)"],
            ["11", "悠宝三岁 (481粉)"],
            ["48", "宅小咪 (173粉)"],
            ["693", "我是你的小猫啊 (73粉)"],
            ["28264", "尤物瓜哥 (335粉)"],
            ["1237", "kuzu_v0 (114粉)"],
            ["12", "小狗pro (569粉)"],
            ["159", "情深叉喔 (806粉)"],
            ["732", "温温兔 (245粉)"],
            ["26", "干干小鱼干 (220粉)"],
            ["606", "小远ovo (653粉)"],
            ["54", "是皂皂呀 (178粉)"],
            ["31145", "Zhen祯 (196粉)"],
            ["20", "肥嘟嘟右门卫 (223粉)"],
            ["83", "许愿 (153粉)"],
            ["626", "黑宫 (123粉)"],
            ["11515", "muchitinasub (246粉)"],
            ["368", "深情叉喔 (240粉)"],
            ["117", "辛尤里 (752粉)"],
            ["82", "Miuzxc (523粉)"],
            ["176", "菜菜最花 (89粉)"],
            ["11341", "阿九儿baby (56粉)"],
            ["858", "snpsdpyx (75粉)"],
            ["565", "短发加禾 (258粉)"],
            ["204", "三岁小宝宝 (237粉)"],
            ["188", "小Q小K (208粉)"],
            ["17192", "manekinekoluvu (234粉)"],
            ["18843", "夏次健 (140粉)"],
            ["15", "软软是小猪 (81粉)"],
            ["655", "玫瑰 (36粉)"],
            ["245", "Abiutmm (167粉)"],
            ["18184", "黑尾酱 (53粉)"],
            ["24557", "ICICIS (101粉)"],
            ["28", "小美miyoki (416粉)"],
            ["7383", "醋溜老师 (300粉)"],
            ["637", "Ellie (142粉)"],
            ["63538", "小狗比比 (70粉)"],
            ["200", "猫猫碎冰冰 (1084粉)"],
            ["75", "台北娜娜 (1034粉)"],
            ["70", "夏晴子 (154粉)"],
            ["22879", "伊藤诚 (186粉)"],
            ["37901", "SelenS (95粉)"],
            ["673", "姚曼川 (284粉)"],
            ["156", "鳗鱼烧 (231粉)"],
            ["867", "柚子猫 (282粉)"],
            ["853", "口巾sang (160粉)"],
            ["687", "Chloe (154粉)"],
            ["68", "菜菜不菜 (191粉)"],
            ["170", "兮兮baby (123粉)"],
            ["5152", "nidexiaogou (336粉)"],
            ["189", "小欣奈 (500粉)"],
            ["11356", "韩善月 (289粉)"],
            ["1395", "asialynn (81粉)"],
            ["191", "揉月 (109粉)"],
            ["670", "Hime_tsu (134粉)"],
            ["573", "黄玲奈 (40粉)"],
            ["20703", "瑶瑶又失眠了 (46粉)"],
            ["276", "菠萝啤beer (440粉)"],
            ["7884", "奶妹 (79粉)"],
            ["18", "兔宝大人 (156粉)"],
            ["42031", "Gattouz (35粉)"],
            ["596", "肉臀果儿 (244粉)"],
            ["691", "唐伯虎 (435粉)"],
            ["9", "犬九 (421粉)"],
            ["362", "jennie洁妮 (227粉)"],
            ["22959", "LINLIN_CPP (178粉)"],
            ["88056", "金币崽 (36粉)"],
            ["42077", "尤物短剧 (674粉)"],
            ["814", "room103 (222粉)"],
            ["744", "Kitty (236粉)"],
            ["169", "兔美酱 (261粉)"],
            ["66", "柚子 (52粉)"],
            ["320", "namprikk (54粉)"],
            ["782", "默默酱 (23粉)"],
            ["31", "奶凶大人 (180粉)"],
            ["629", "小二先生 (58粉)"],
            ["244", "捅主任 (607粉)"],
            ["88", "狐不妖 (228粉)"],
            ["733", "yaya (138粉)"],
            ["50", "桔梗 (126粉)"],
            ["63513", "xiaoxiababy (36粉)"],
            ["49", "鸡教练 (149粉)"],
            ["7876", "lovechuu (249粉)"],
            ["17", "洛宝 (192粉)"],
            ["785", "醋溜醋溜 (19粉)"],
            ["621", "jenny pinky (44粉)"],
            ["7898", "情场花蝴蝶 (142粉)"],
            ["275", "苏小涵 (225粉)"],
            ["363", "沉芯语 (33粉)"],
            ["13961", "RoseWu (334粉)"],
            ["16", "饼饼大王 (112粉)"],
            ["168", "饼干姐姐 (714粉)"],
            ["623", "工藤静香 (105粉)"],
            ["1439", "辞宝 (67粉)"],
            ["205", "爹咪 (196粉)"],
            ["364", "九条南无 (95粉)"],
            ["18197", "小羊爱吃草 (264粉)"],
            ["16517", "香月怜 (90粉)"],
            ["298", "欣欣子 (73粉)"],
            ["85", "王zu贤 (58粉)"],
            ["71", "苏畅 (230粉)"],
            ["3642", "九烟桃桃 (86粉)"],
            ["56", "呆呆萝 (103粉)"],
            ["158", "nina小蜜桃 (123粉)"],
            ["20460", "一杆钢枪 (26粉)"],
            ["22063", "姬子猫 (146粉)"],
            ["863", "默默是olive呀 (50粉)"],
            ["19470", "KpKpR (112粉)"],
            ["64", "露露 (34粉)"],
            ["549", "svj798ds (232粉)"],
            ["22060", "YoShiE冰块 (120粉)"],
            ["36724", "Luckybaby (45粉)"],
            ["1259", "yoyo (31粉)"],
            ["86", "小鸢宝宝 (137粉)"],
            ["46430", "高乔尤美 (44粉)"],
            ["14664", "qingyueyue (34粉)"],
            ["14960", "沅沅 (44粉)"],
            ["37897", "Yamisung (45粉)"],
            ["21041", "一条肌肉狗 (160粉)"],
            ["72", "桥本香菜 (490粉)"],
            ["475", "小小桃 (177粉)"],
            ["16884", "ssrpeach (47粉)"],
            ["2", "玉米 (115粉)"],
            ["47", "铃木美咲 (90粉)"],
            ["27", "你的KK (71粉)"],
            ["649", "和爱 (35粉)"],
            ["280", "yunatamago_zz (91粉)"],
            ["175", "嫩小兔 (101粉)"],
            ["39040", "仙仙桃 (72粉)"],
            ["37677", "AmGia (33粉)"],
            ["15944", "Gattouz0 (65粉)"],
            ["29", "孙禾颐 (677粉)"],
            ["16509", "kaori_xoxo (54粉)"],
            ["11391", "艾希 (199粉)"],
            ["620", "Make性专家 (33粉)"],
            ["658", "易鸣夫妻 (40粉)"],
            ["254", "bbyelalin (17粉)"],
            ["155", "小米粥 (57粉)"],
            ["171", "菠萝包 (107粉)"],
            ["758", "yui (19粉)"],
            ["190", "爱吃雪糕 (72粉)"],
            ["706", "斑斑 (56粉)"],
            ["22", "一口白桃七 (65粉)"],
            ["862", "萌崽儿 (65粉)"],
            ["27257", "雪狐 (24粉)"],
            ["1402", "meriochan (69粉)"],
            ["53", "白日梦想鸭 (60粉)"],
            ["1061", "林千夜 (39粉)"],
            ["360", "下面有根棒棒糖 (125粉)"],
            ["13", "沈思缪 (341粉)"],
            ["654", "黑猫露娜酱 (121粉)"],
            ["854", "奶酪 (32粉)"],
            ["81", "米胡桃 (238粉)"],
            ["669", "AlinaMei (23粉)"],
            ["476", "小羊妹妹 (49粉)"],
            ["26307", "Sexy_Yuki (94粉)"],
            ["16349", "月野兔 (61粉)"],
            ["1216", "潘潘 (143粉)"],
            ["57", "饱饱咪 (53粉)"],
            ["534", "顶级碧螺春 (95粉)"],
            ["22970", "铃木奈雪 (105粉)"],
            ["16878", "Dainty Wilder (74粉)"],
            ["47474", "Sherry_niko (67粉)"],
            ["18183", "冉冉学姐 (131粉)"],
            ["38187", "露娜妈妈 (30粉)"],
            ["708", "蓝色浪漫 (15粉)"],
            ["1018", "西野加奈 (230粉)"],
            ["246", "周慕云 (47粉)"],
            ["16895", "pittyswg (14粉)"],
            ["1396", "meriolchan (144粉)"],
            ["173", "白日梦想家 (28粉)"],
            ["80", "一颗甜桃 (76粉)"],
            ["12501", "Deerlong (109粉)"],
            ["40552", "母狗俱乐部 (36粉)"],
            ["47472", "烈 (39粉)"],
            ["690", "美杜莎 (68粉)"],
            ["12460", "Himetsu (78粉)"],
            ["174", "喵叽小糯 (173粉)"],
            ["203", "创可贴贴 (260粉)"],
            ["52", "Kittyxkum (334粉)"],
            ["813", "kitty2002102 (13粉)"],
            ["86006", "萌宅卡 (33粉)"],
            ["730", "andmlove (112粉)"],
            ["1022", "宋雨川 (48粉)"],
            ["18824", "babysexnitynine (40粉)"],
            ["743", "极限反差团 (17粉)"],
            ["14952", "蜡笔甜心 (126粉)"],
            ["16511", "yuumeilyn (105粉)"],
            ["13970", "砂糖 (59粉)"],
            ["4125", "纯纯是纯爱 (28粉)"],
            ["15826", "Dom深渊 (69粉)"],
            ["23664", "Big烟枪 (76粉)"],
            ["69", "李蓉蓉 (44粉)"],
            ["8526", "DUDU (38粉)"],
            ["269", "汐梦瑶 (197粉)"],
            ["32", "御梦子 (284粉)"],
            ["18841", "汉生 (65粉)"],
            ["1246", "玩偶姐姐 (387粉)"],
            ["1176", "李露丝 (47粉)"],
            ["91370", "LuckyDog77 (6粉)"],
            ["16513", "TWIN双胞胎 (52粉)"],
            ["692", "微微安 (24粉)"],
            ["1411", "蜜汁猫裘 (14粉)"],
            ["1177", "北野爱 (60粉)"],
            ["73", "明纱芽衣 (28粉)"],
            ["299", "浵卡 (46粉)"],
            ["656", "夏水水 (18粉)"],
            ["10280", "小兔牙 (27粉)"],
            ["400", "温凉 (30粉)"],
            ["29133", "Azu (14粉)"],
            ["23985", "小千 (74粉)"],
            ["369", "yurinslittlepeach (19粉)"],
            ["314", "优娜 (42粉)"],
            ["7391", "好大的爆米花 (26粉)"],
            ["634", "ruthlee (25粉)"],
            ["20455", "highsstn (102粉)"],
            ["16512", "naomiiichannel (58粉)"],
            ["742", "恩凯 (12粉)"],
            ["161", "妍熙 (18粉)"],
            ["713", "miuzxc (25粉)"],
    ]

    def __init__(self):
        super(Spider, self).__init__()
        self.siteName = "尤物百科"
        self.siteUrl = "https://big.zkdmig.com"
        self.brandName = "蝴蝶影视"
        self.brandActor = "🦋 TG群: @tvshare23"
        self.brandDirector = "🦋 蝴蝶影视"
        self.lineName = "🦋 蝴蝶专线"
        self.posterRatio = 1.78
        self._ua = "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36"
        self.options = {}
        self.ctx = ssl.create_default_context()
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.cj = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj),
            urllib.request.HTTPSHandler(context=self.ctx)
        )

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

    def _fetch_once(self, target_url):
        headers = {
            "User-Agent": self._ua,
            "Accept": "*/*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Referer": self.siteUrl + "/",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive"
        }
        try:
            req = urllib.request.Request(target_url, headers=headers)
            with self.opener.open(req, timeout=8) as resp:
                code = resp.getcode()
                raw = resp.read()
                if code < 200 or code >= 300 or not raw:
                    return ""
                enc = ""
                try:
                    enc = resp.headers.get("Content-Encoding", "") or ""
                except Exception:
                    enc = ""
                if raw.startswith(b"\x1f\x8b") or enc == "gzip":
                    raw = gzip.decompress(raw)
                elif enc == "deflate":
                    try:
                        raw = zlib.decompress(raw)
                    except Exception:
                        raw = zlib.decompress(raw, -zlib.MAX_WBITS)
                try:
                    return raw.decode("utf-8")
                except Exception:
                    return raw.decode("utf-8", errors="ignore")
        except Exception:
            return ""

    def _fetch(self, target_url):
        if not target_url:
            return ""
        for attempt in range(2):
            text = self._fetch_once(target_url)
            if text:
                return text
            if target_url.startswith("https://"):
                text = self._fetch_once("http://" + target_url[8:])
                if text:
                    return text
        return ""

    def _clean_text(self, value):
        text = re.sub(r"<[^>]+>", " ", str(value or ""))
        text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&quot;", '"')
        text = text.replace("&#39;", "'").replace("&lt;", "<").replace("&gt;", ">")
        return re.sub(r"\s+", " ", text).strip()

    def _strip_ld(self, html):
        return re.sub(r'<script[^>]*ld\+json[^>]*>[\s\S]*?</script>', "", html or "", flags=re.I)

    def _format_poster(self, raw_url):
        if not raw_url:
            return ""
        url = str(raw_url).strip().replace("&amp;", "&")
        if not url:
            return ""
        if url.startswith("//"):
            url = "https:" + url
        elif url.startswith("/"):
            url = self.siteUrl + url
        if not url.startswith("http"):
            return ""
        pm = re.search(r'[?&]p=([^&]+)', url)
        if "/og/img" in url and pm and pm.group(1):
            try:
                dec = urllib.parse.unquote(pm.group(1))
            except Exception:
                dec = pm.group(1)
            url = self.siteUrl + "/og/img/?p=" + quote(dec, safe="")
        else:
            um = re.match(r'^https?://[^/]+(/upload_[^?#]+)', url)
            if um and um.group(1):
                url = self.siteUrl + "/og/img/?p=" + quote(um.group(1), safe="")
        return url

    def _parse_cards(self, html):
        clean = self._strip_ld(html)
        out = []
        seen = {}
        for m in re.finditer(r'<li[^>]*post-list-item[^>]*>([\s\S]*?)</li>', clean, re.I):
            blk = m.group(1)
            im = re.search(r'href=["\'][^"\']*?/archives/(\d+)/?["\']', blk, re.I)
            if not im:
                continue
            vid = im.group(1).strip()
            if not vid or vid in seen:
                continue
            name = ""
            h2 = re.search(r'<h2[^>]*>([\s\S]{1,300}?)</h2>', blk, re.I)
            if h2 and h2.group(1):
                name = self._clean_text(h2.group(1))
            if not name:
                alt = re.search(r'alt=["\']([^"\']{1,300})["\']', blk, re.I)
                name = self._clean_text(alt.group(1)) if alt else vid
            pic = ""
            ds = re.search(r'data-src=["\'](https?://[^"\']+)["\']', blk, re.I)
            if ds and ds.group(1):
                pic = ds.group(1)
            else:
                sm = re.search(r'src=["\'](https?://[^"\']+)["\']', blk, re.I)
                if sm and sm.group(1):
                    pic = sm.group(1)
            tm = re.search(r'<time[^>]*>([^<]+)</time>', blk, re.I)
            meta = self._clean_text(tm.group(1)) if tm else ""
            seen[vid] = True
            out.append({
                "vod_id": vid,
                "vod_name": name,
                "vod_pic": self._format_poster(pic),
                "vod_remarks": format_remarks(self.brandName, meta),
                "style": {"type": "rect", "ratio": self.posterRatio}
            })
        return out

    def _page_num(self, pg):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        return page

    def _empty(self, page):
        return {"list": [], "page": page, "pagecount": page if page >= 1 else 1, "limit": 20, "total": 0}

    def _paged_result(self, html, page):
        cards = self._parse_cards(html)
        if not cards:
            return self._empty(page)
        links = [int(x) for x in re.findall(r'/page/(\d+)/', html or "")]
        pagecount = max(links) if links else page
        if pagecount < page + 1:
            pagecount = page + 1
        return {"list": cards, "page": page, "pagecount": pagecount, "limit": len(cards), "total": pagecount * len(cards)}

    def homeContent(self, filter):
        classes = [{"type_id": c["type_id"], "type_name": c["type_name"]} for c in self.BASE_CATS]
        classes.append({"type_id": "filter@@up", "type_name": "UP主专栏"})
        result = {"class": classes}
        if filter:
            values = [{"n": "全部UP主 (默认最新)", "v": ""}]
            for pair in self.AUTHORS:
                values.append({"n": pair[1], "v": pair[0]})
            result["filters"] = {
                "filter@@up": [{"key": "author", "name": "选择UP主", "init": "", "value": values}]
            }
        return result

    def homeVideoContent(self):
        html = self._fetch(self.siteUrl + "/")
        if not html:
            return {"list": []}
        return {"list": self._parse_cards(html)[:30]}

    def categoryContent(self, tid, pg, filter, extend):
        tid = str(tid or "")
        page = self._page_num(pg)
        extend = extend if isinstance(extend, dict) else {}
        if tid == "filter@@up":
            aid = str(extend.get("author") or "").strip()
            if aid and aid.isdigit():
                if page == 1:
                    url = "%s/author/%s/" % (self.siteUrl, aid)
                else:
                    url = "%s/author/%s/page/%s/" % (self.siteUrl, aid, page)
            else:
                url = self.siteUrl + "/" if page == 1 else "%s/page/%s/" % (self.siteUrl, page)
        else:
            slug = None
            for cat in self.BASE_CATS:
                if cat["type_id"] == tid or cat["type_name"] == tid:
                    slug = cat["slug"]
                    break
            if slug:
                if page == 1:
                    url = "%s/category/%s/" % (self.siteUrl, slug)
                else:
                    url = "%s/category/%s/page/%s/" % (self.siteUrl, slug, page)
            else:
                url = self.siteUrl + "/" if page == 1 else "%s/page/%s/" % (self.siteUrl, page)
        html = self._fetch(url)
        if not html:
            return self._empty(page)
        return self._paged_result(html, page)

    def searchContent(self, key, quick, pg="1"):
        page = self._page_num(pg)
        keyword = str(key or "").strip()
        if not keyword:
            return self._empty(page)
        enc = quote(keyword, safe="!~*'()")
        if page == 1:
            url = "%s/posts/search/%s/" % (self.siteUrl, enc)
        else:
            url = "%s/posts/search/%s/page/%s/" % (self.siteUrl, enc, page)
        html = self._fetch(url)
        if not html:
            return self._empty(page)
        return self._paged_result(html, page)

    def _brand_block(self):
        return [
            "🦋 %s官方交流群：@tvshare23" % self.siteName,
            "导演：🦋 蝴蝶影视",
            "当前主站：%s" % self.siteUrl,
            "━" * 28,
            "━" * 7
        ]

    def _extract_categories(self, html):
        cats = []
        seen = {}
        for m in re.finditer(r'<a[^>]+href=["\'][^"\']*?/category/[^"\']+["\'][^>]*>([\s\S]{1,80}?)</a>', html or "", re.I):
            label = self._clean_text(m.group(1))
            if label and len(label) <= 20 and label not in seen:
                seen[label] = True
                cats.append(label)
        return cats

    def _extract_title_from_inner(self, inner):
        hm = re.search(r'<h[234][^>]*>([\s\S]{1,200}?)</h[234]>', inner, re.I)
        if hm and hm.group(1):
            return self._clean_text(hm.group(1))
        am = re.search(r'(?:alt|title)=["\']([^"\']{2,200})["\']', inner, re.I)
        if am and am.group(1):
            return self._clean_text(am.group(1))
        return self._clean_text(inner)

    def _extract_related(self, html, current_vid, current_title):
        clean = self._strip_ld(html)
        pairs = []
        seen = {}
        sec = re.search(r'(?:相关推荐|猜你喜欢|相关文章|相关视频|related-posts|post-list)[\s\S]*$', clean, re.I)
        rel_section = sec.group(0) if sec else clean

        def collect(text):
            for m in re.finditer(r'<a[^>]+href=["\'][^"\']*?/archives/(\d+)/?["\'][^>]*>([\s\S]{1,400}?)</a>', text, re.I):
                rvid = m.group(1)
                if not rvid or rvid == current_vid or rvid in seen:
                    continue
                rtitle = self._extract_title_from_inner(m.group(2))
                if rtitle and len(rtitle) >= 2 and rtitle != current_title:
                    seen[rvid] = True
                    pairs.append((rvid, rtitle))
                    if len(pairs) >= 6:
                        return

        collect(rel_section)
        if len(pairs) < 6 and rel_section is not clean:
            collect(clean)
        return pairs

    def _extract_tokens(self, html):
        tokens = []
        seen = {}
        for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>', html or "", re.I):
            body = m.group(1)
            if "eval(function(p,a,c,k,e,d)" not in body:
                continue
            unpacked = unpack_packer(body)
            tm = re.search(r'/api/player/([A-Za-z0-9_-]+)/', unpacked)
            if tm and tm.group(1) and tm.group(1) not in seen:
                seen[tm.group(1)] = True
                tokens.append(tm.group(1))
        return tokens

    def _extract_episode_titles(self, html):
        text = str(html or "")
        out = []
        for m in re.finditer(r'id=["\']youwu-player-shell-([0-9a-z]+)["\']', text, re.I):
            seg = text[max(0, m.start() - 4000):m.start()]
            last = ""
            for hm in re.finditer(r'<h2[^>]*>([\s\S]{1,200}?)</h2>', seg, re.I):
                last = self._clean_text(hm.group(1))
            out.append(last)
        return out

    def detailContent(self, ids):
        raw = ids[0] if isinstance(ids, (list, tuple)) and ids else ids
        raw_id = str(raw or "").strip()
        if raw_id.startswith("vod/"):
            raw_id = raw_id[4:]
        vid = raw_id.split("|")[0].strip()
        if not vid:
            return {"list": []}
        page_url = "%s/archives/%s/" % (self.siteUrl, vid)
        html = self._fetch(page_url)
        if not html:
            return {"list": []}
        title = ""
        h1 = re.search(r'<h1[^>]*>([\s\S]{1,300}?)</h1>', html, re.I)
        if h1 and h1.group(1):
            title = self._clean_text(h1.group(1))
        if not title:
            tmatch = re.search(r'<title>([^<]+)</title>', html, re.I)
            title = self._clean_text(tmatch.group(1)) if tmatch else vid
        pic = ""
        og = re.search(r'property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']', html, re.I) or re.search(r'content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']', html, re.I)
        if og and og.group(1):
            pic = og.group(1)
        if not pic:
            ds = re.search(r'data-src=["\'](https?://[^"\']+)["\']', self._strip_ld(html), re.I)
            if ds and ds.group(1):
                pic = ds.group(1)
        poster = self._format_poster(pic)
        raw_desc = ""
        dm = re.search(r'name=["\']description["\'][^>]+content=["\']([^"\']*)["\']', html, re.I) or re.search(r'content=["\']([^"\']*)["\'][^>]+name=["\']description["\']', html, re.I)
        if dm and dm.group(1):
            raw_desc = self._clean_text(dm.group(1))
        categories = self._extract_categories(html)
        related = self._extract_related(html, vid, title)
        tokens = self._extract_tokens(html)
        ep_titles = self._extract_episode_titles(html)
        play_from = []
        play_url = []
        if tokens:
            eps = []
            for i in range(len(tokens)):
                ep_title = ep_titles[i] if i < len(ep_titles) and ep_titles[i] else ("第%s集" % (i + 1))
                ep_title = ep_title.replace("$", "").replace("#", "").strip() or ("第%s集" % (i + 1))
                eps.append("%s$%s:%s" % (ep_title, vid, i))
            play_from.append(self.lineName)
            play_url.append("#".join(eps))
        if related:
            rel_eps = []
            for rvid, rtitle in related:
                clean_title = rtitle.replace("$", "").replace("#", "").strip()
                rel_eps.append("%s$rel:%s" % (clean_title, rvid))
            play_from.append("相关推荐")
            play_url.append("#".join(rel_eps))
        if len(tokens) == 1:
            ep_meta = "正片"
        elif len(tokens) > 1:
            ep_meta = "%s集全" % len(tokens)
        else:
            ep_meta = ""
        content_lines = self._brand_block()
        if raw_desc:
            content_lines.append(raw_desc)
        else:
            content_lines.append("标题：%s" % title)
            content_lines.append("分类：%s" % (" / ".join(categories) if categories else "尤物精选"))
            content_lines.append("片源：%s" % self.lineName)
            content_lines.append("编号：%s" % vid)
            if related:
                names = [rtitle for _, rtitle in related[:6]]
                content_lines.append("相关推荐：%s" % " / ".join(names))
        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": self.brandActor,
            "vod_director": self.brandDirector,
            "vod_remarks": format_remarks(self.brandName, ep_meta),
            "vod_content": "\n".join(content_lines),
            "vod_play_from": "$$$".join(play_from),
            "vod_play_url": "$$$".join(play_url)
        }
        vod["type_name"] = categories[0] if categories else "尤物精选"
        vod["vod_tag"] = vod["type_name"]
        return {"list": [vod]}

    def _resolve_episode(self, vid, index):
        headers = {
            "User-Agent": self._ua,
            "Referer": self.siteUrl + "/",
            "Origin": self.siteUrl
        }
        detail_url = "%s/archives/%s/" % (self.siteUrl, vid)
        for attempt in range(2):
            html = self._fetch(detail_url)
            tokens = self._extract_tokens(html)
            if not tokens:
                continue
            safe_idx = index if 0 <= index < len(tokens) else 0
            token = tokens[safe_idx]
            ts = int(time.time() * 1000) // 2000
            api_url = "%s/api/player/%s/%s" % (self.siteUrl, token, ts)
            resp = self._fetch(api_url)
            if not resp:
                continue
            unpacked = unpack_packer(resp)
            video_url = ""
            vm = re.search(r'"video"\s*:\s*\{[\s\S]{0,400}?"url"\s*:\s*"([^"]+)"', unpacked)
            if vm and vm.group(1):
                video_url = vm.group(1)
            else:
                mm = re.search(r'"(https?:[^"]*?\.m3u8[^"]*)"', unpacked)
                if mm and mm.group(1):
                    video_url = mm.group(1)
            if video_url:
                video_url = re.sub(r"\\+/", "/", video_url).replace("&amp;", "&")
                if ".m3u8" not in video_url.lower():
                    sep = "&" if "?" in video_url else "?"
                    video_url = video_url + sep + "format=.m3u8"
                return {"parse": 0, "jx": 0, "url": video_url, "header": headers}
        return {"parse": 1, "playUrl": "", "url": detail_url, "header": headers}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "").strip()
        if raw.startswith("rel:"):
            vid = raw[4:]
            html = self._fetch("%s/archives/%s/" % (self.siteUrl, vid))
            tokens = self._extract_tokens(html)
            if not tokens:
                return {"parse": 1, "playUrl": "", "url": "%s/archives/%s/" % (self.siteUrl, vid), "header": {"User-Agent": self._ua, "Referer": self.siteUrl + "/"}}
            return self._resolve_episode(vid, 0)
        parts = raw.split(":")
        if len(parts) != 2 or not parts[0]:
            return {"parse": 0, "jx": 0, "url": ""}
        try:
            index = int(parts[1])
        except Exception:
            index = 0
        return self._resolve_episode(parts[0], index)

    def action(self, action):
        return {"msg": "ok"}

    def liveContent(self):
        return ""

    def localProxy(self, params):
        return [404, "text/plain; charset=utf-8", "Proxy not configured"]

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249930608&sig=bf74135a62c2d91b
