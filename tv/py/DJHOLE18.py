# -*- coding: utf-8 -*-
# DJHOLE 蜘蛛（源自 Hamo 插件 com.butterfly.avgc9 的接口逻辑移植）
import base64
import json
import re
import time
import urllib.request
import urllib.error
import urllib.parse

from base.spider import Spider as BaseSpider


class Spider(BaseSpider):
    DEFAULT_HOST = "https://avgc9.store"
    UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    CLASSES = [
        ("latest", "最新视频", None),
        ("home", "热门播放", None),
        ("nav_ai", "人工智能", None),
        ("nav_media", "传媒精选", ("tag", "传媒", "MEDIA_OPTS")),
        ("nav_cloth", "服装专区", ("tag", "服装", "CLOTH_OPTS")),
        ("nav_role", "角色扮演", ("tag", "角色", "ROLE_OPTS")),
        ("nav_actress", "演员专区", ("actress", "演员", "ACTRESS_OPTS")),
    ]
    MEDIA_OPTS = (("", "全部传媒"), ("麻豆传媒", "麻豆传媒"), ("天美传媒", "天美传媒"), ("大象传媒", "大象传媒"), ("糖心Vlog", "糖心Vlog"), ("果冻传媒", "果冻传媒"), ("星空传媒", "星空传媒"), ("香蕉秀", "香蕉秀"), ("爱豆传媒", "爱豆传媒"), ("SA国际传媒", "SA国际传媒"), ("蜜桃传媒", "蜜桃传媒"), ("渡边传媒", "渡边传媒"), ("爱神传媒", "爱神传媒"), ("SWAG", "SWAG"), ("精东影业", "精东影业"), ("乐播传媒", "乐播传媒"), ("扣扣传媒", "扣扣传媒"), ("91制片厂", "91制片厂"))
    CLOTH_OPTS = (("旗袍", "旗袍"), ("黑丝", "黑丝"), ("情趣衣", "情趣服"), ("和服", "和服"), ("白丝", "白丝"), ("牛仔裤", "牛仔裤"))
    ROLE_OPTS = (("", "全部角色"), ("空姐", "空姐"), ("女仆", "女仆"), ("OL", "OL"), ("护士", "护士"), ("萝莉", "萝莉"), ("秘书", "秘书"), ("女大学生", "女大学生"), ("模特", "模特"), ("明星", "明星"), ("女主播", "女主播"), ("女上司", "女上司"))
    ACTRESS_OPTS = (("ai短剧", "AI短剧(1130部)"), ("金钢狼", "金钢狼(236部)"), ("love姐", "love姐(162部)"), ("狂情哥哥", "狂情哥哥(158部)"), ("糖糖", "糖糖(150部)"), ("运动宅男", "运动宅男(142部)"), ("Emily", "Emily(139部)"), ("孟若羽", "孟若羽(131部)"), ("饼干姐姐", "饼干姐姐(130部)"), ("辛尤里", "辛尤里(126部)"), ("小水水", "小水水(125部)"), ("吴梦梦", "吴梦梦(125部)"), ("黑杰克", "黑杰克(122部)"), ("宽哥", "宽哥(122部)"), ("李蓉蓉", "李蓉蓉(120部)"), ("苏畅", "苏畅(116部)"), ("桥本香菜", "桥本香菜(114部)"), ("nana", "nana(114部)"), ("Fantasy", "Fantasy(107部)"), ("米菲兔", "米菲兔(106部)"), ("狐不妖", "狐不妖(98部)"), ("NicoLove", "NicoLove(98部)"), ("沈娜娜", "沈娜娜(96部)"), ("夏晴子", "夏晴子(95部)"), ("小Q", "小Q(92部)"), ("唐伯虎", "唐伯虎(92部)"), ("懒懒猪", "懒懒猪(91部)"), ("MISSCAT", "MISSCAT(86部)"), ("汉生", "汉生(85部)"), ("斑斑", "斑斑(85部)"), ("宇宙列车", "宇宙列车(84部)"), ("捅主任", "捅主任(84部)"), ("柚子猫", "柚子猫(84部)"), ("壹柒柒", "壹柒柒(77部)"), ("艾莉", "艾莉(76部)"), ("Miuzxc", "Miuzxc(72部)"), ("情深叉喔", "情深叉喔(71部)"), ("跳跳羊", "跳跳羊(69部)"), ("冰凌紫萱", "冰凌紫萱(68部)"), ("樱空桃桃", "樱空桃桃(68部)"), ("玩偶姐姐", "玩偶姐姐(68部)"), ("丝袜小淫妻", "丝袜小淫妻(67部)"), ("冉冉学姐", "冉冉学姐(67部)"), ("YoShiE", "YoShiE(64部)"), ("汐梦瑶", "汐梦瑶(64部)"), ("锅锅酱", "锅锅酱(63部)"), ("小敏儿", "小敏儿(62部)"), ("深海杀人鲸", "深海杀人鲸(61部)"), ("亦可姐姐", "亦可姐姐(61部)"), ("粉色情人", "粉色情人(61部)"), ("是小桃呢", "是小桃呢(56部)"), ("Xreindeers", "Xreindeers(56部)"), ("渣男", "渣男(56部)"), ("鸡教练", "鸡教练(56部)"), ("小蜜桃", "小蜜桃(55部)"), ("赤麟狂舞", "赤麟狂舞(55部)"), ("苏语棠", "苏语棠(54部)"), ("pupu", "pupu(53部)"), ("困困狗", "困困狗(52部)"), ("北野爱", "北野爱(51部)"), ("中英字幕", "中英字幕(50部)"), ("犬九", "犬九(50部)"), ("伊藤诚", "伊藤诚(50部)"), ("小欣奈", "小欣奈(50部)"), ("艾秋", "艾秋(50部)"), ("小桃", "小桃(49部)"), ("仔仔", "仔仔(47部)"), ("TWIN", "TWIN(47部)"), ("小樱", "小樱(47部)"), ("肥臀人妻", "肥臀人妻(46部)"), ("米胡桃", "米胡桃(46部)"), ("韩棠", "韩棠(46部)"), ("软软兔", "软软兔(45部)"), ("小巨", "小巨(45部)"), ("林思妤", "林思妤(45部)"), ("洁妮", "洁妮(44部)"), ("深情小K", "深情小K(44部)"), ("十三叔", "十三叔(43部)"), ("凌薇", "凌薇(43部)"), ("艾熙", "艾熙(42部)"), ("秦可欣", "秦可欣(42部)"), ("胖爷", "胖爷(41部)"), ("银丝雀", "银丝雀(39部)"), ("鱼哥", "鱼哥(39部)"), ("cola酱", "cola酱(39部)"), ("玥可岚", "玥可岚(39部)"), ("Gattouz", "Gattouz(38部)"), ("粉红兔", "粉红兔(38部)"), ("林千夜", "林千夜(37部)"), ("狮子座", "狮子座(37部)"), ("苏小涵", "苏小涵(37部)"), ("周宁", "周宁(37部)"), ("徐蕾", "徐蕾(37部)"), ("季妍希", "季妍希(37部)"), ("风流财子", "风流财子(36部)"), ("雪千夏", "雪千夏(36部)"), ("董庆良", "董庆良(35部)"), ("MaryBarrie", "MaryBarrie(35部)"), ("深入快热", "深入快热(35部)"), ("小林", "小林(35部)"), ("胖哥", "胖哥(35部)"), ("阿姨终结者", "阿姨终结者(35部)"), ("公鸡俱乐部", "公鸡俱乐部(35部)"), ("强推哥", "强推哥(35部)"), ("嫚嫚", "嫚嫚(35部)"), ("OOXXBLACK", "OOXXBLACK(34部)"), ("南橘", "南橘(34部)"), ("西门庆", "西门庆(34部)"), ("我的枪好长", "我的枪好长(33部)"), ("黑椒盖饭", "黑椒盖饭(33部)"), ("D先生", "D先生(33部)"), ("金先生", "金先生(33部)"), ("金宝娜", "金宝娜(33部)"), ("爱情鸟", "爱情鸟(32部)"), ("提拉米苏", "提拉米苏(32部)"), ("美缝有约", "美缝有约(32部)"), ("老虎菜", "老虎菜(32部)"), ("菠萝啤", "菠萝啤(32部)"), ("羞羞兔", "羞羞兔(32部)"), ("丝丝女神", "丝丝女神(32部)"), ("管明美", "管明美(32部)"), ("九九橙", "九九橙(31部)"), ("天生爱风流", "天生爱风流(31部)"), ("兔美酱", "兔美酱(31部)"), ("小巧芋艿", "小巧芋艿(31部)"), ("优咪", "优咪(31部)"), ("杰尼龟", "杰尼龟(31部)"), ("西野加奈", "西野加奈(31部)"), ("米欧", "米欧(31部)"), ("苏清歌", "苏清歌(31部)"), ("SuperS", "SuperS(30部)"), ("夫妻交换", "夫妻交换(30部)"), ("白菜妹妹", "白菜妹妹(30部)"), ("董洁", "董洁(30部)"), ("硬壳探花", "硬壳探花(30部)"), ("樱花小猫", "樱花小猫(30部)"), ("优米", "优米(30部)"), ("猫猫碎冰冰", "猫猫碎冰冰(29部)"), ("布丁", "布丁(29部)"), ("性幻想日记", "性幻想日记(29部)"), ("芒果", "芒果(29部)"), ("曹长卿", "曹长卿(29部)"), ("宋南伊", "宋南伊(29部)"), ("李娜娜", "李娜娜(29部)"), ("EJ小情侣", "EJ小情侣(28部)"), ("嘉洛", "嘉洛(28部)"), ("misav", "misav(28部)"), ("许木学长", "许木学长(28部)"), ("优娜", "优娜(28部)"), ("蜜苏", "蜜苏(28部)"), ("唐茜", "唐茜(28部)"), ("上湾晋紫宫", "上湾晋紫宫(27部)"), ("GummyPoppy", "GummyPoppy(27部)"), ("老司机", "老司机(27部)"), ("鱿鱼", "鱿鱼(27部)"), ("Looks", "Looks(27部)"), ("梁芸菲", "梁芸菲(27部)"), ("老污龟", "老污龟(27部)"), ("糖葫芦", "糖葫芦(26部)"), ("九烟桃桃", "九烟桃桃(26部)"), ("Ellie", "Ellie(26部)"), ("妹姬", "妹姬(26部)"), ("姨甥恋", "姨甥恋(26部)"), ("斯文禽兽", "斯文禽兽(26部)"), ("苡若", "苡若(26部)"), ("寻小小", "寻小小(26部)"), ("白晶晶", "白晶晶(26部)"), ("捏面人啾啾", "捏面人啾啾(25部)"), ("Eva", "Eva(25部)"), ("金童钟", "金童钟(25部)"), ("星野兔", "星野兔(25部)"), ("张芸熙", "张芸熙(25部)"), ("艾嫣", "艾嫣(24部)"), ("秋元今", "秋元今(24部)"), ("梁幂", "梁幂(24部)"), ("仙儿媛", "仙儿媛(24部)"), ("虚焦大王", "虚焦大王(23部)"), ("喵叽小糯", "喵叽小糯(23部)"), ("果儿", "果儿(23部)"), ("xx君", "xx君(23部)"), ("天堂", "天堂(23部)"), ("王安全", "王安全(23部)"), ("美酱", "美酱(23部)"), ("玖玖", "玖玖(23部)"), ("白靖寒", "白靖寒(23部)"), ("刘玥", "刘玥(23部)"), ("艾玛", "艾玛(23部)"), ("jklove", "jklove(22部)"), ("妳的教练", "妳的教练(22部)"), ("普朗克", "普朗克(22部)"), ("流泪番茄", "流泪番茄(22部)"), ("小二先生", "小二先生(22部)"), ("大汉刘备", "大汉刘备(22部)"), ("舒可芯", "舒可芯(22部)"), ("娃娃", "娃娃(22部)"), ("袁子仪", "袁子仪(22部)"), ("MacyChan", "MacyChan(21部)"), ("小羊爱吃草", "小羊爱吃草(21部)"), ("GrapeeSoda", "GrapeeSoda(21部)"), ("咪Show", "咪Show(21部)"), ("NTR重度控", "NTR重度控(21部)"), ("派崔克", "派崔克(21部)"), ("燕姐", "燕姐(21部)"), ("糯米宝宝", "糯米宝宝(21部)"), ("小艾", "小艾(21部)"), ("温芮欣", "温芮欣(21部)"), ("林嫣", "林嫣(21部)"), ("多乙", "多乙(21部)"), ("吴芳宜", "吴芳宜(21部)"), ("夜夜", "夜夜(21部)"), ("耶稣", "耶稣(20部)"), ("嫩小兔", "嫩小兔(20部)"), ("圣诞老人", "圣诞老人(20部)"), ("巨乳e嫂", "巨乳e嫂(20部)"), ("工藤静香", "工藤静香(20部)"), ("空虚猫", "空虚猫(20部)"), ("派大星", "派大星(20部)"), ("kitty", "kitty(20部)"), ("欧阳克", "欧阳克(20部)"), ("花花", "花花(20部)"), ("国大夫妇", "国大夫妇(20部)"), ("韩国骚妻", "韩国骚妻(20部)"))

    def getName(self):
        return "DJHOLE"

    def init(self, extend=""):
        self.host = self.DEFAULT_HOST
        if isinstance(extend, str) and extend.strip().startswith("http"):
            self.host = extend.strip().rstrip("/")

    # ---------- transport: envelope = {code:200, data: base64(percent-encoded JSON)} ----------
    def _fetch_api(self, path):
        url = self.host + "/api" + path
        headers = {"User-Agent": self.UA, "Referer": self.host + "/", "Accept": "application/json, text/plain, */*"}
        for _ in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read()
                env = json.loads(raw.decode("utf-8", "replace"))
                if isinstance(env, dict) and env.get("code") == 200 and isinstance(env.get("data"), str):
                    decoded = base64.b64decode(env["data"])
                    unq = urllib.parse.unquote(decoded.decode("utf-8", "replace"))
                    parsed = json.loads(unq)
                    return parsed if isinstance(parsed, (dict, list)) else None
                return None
            except Exception:
                pass
            time.sleep(0.5)
        return None

    # ---------- helpers ----------
    def _is_ai_drama(self, item):
        tags = item.get("tags") if isinstance(item.get("tags"), list) else []
        for t in tags:
            if isinstance(t, dict) and (t.get("name_code") == "ai-短剧" or t.get("name") == "AI短剧"):
                return True
        return False

    def _format_cards(self, lst):
        items = []
        if not isinstance(lst, list):
            return items
        for v in lst:
            if not isinstance(v, dict):
                continue
            code = str(v.get("title_code") or v.get("id") or "").strip()
            title = str(v.get("title_zh") or v.get("title") or "").strip()
            if not title or not code:
                continue
            items.append({
                "vod_id": code,
                "vod_name": title,
                "vod_pic": str(v.get("cover") or "").strip(),
                "vod_remarks": "蝴蝶影视 | 无码" if v.get("is_uncensored") else "蝴蝶影视 | 高清",
                "style": {"type": "rect", "ratio": 0.75 if self._is_ai_drama(v) else 1.78},
            })
        return items

    def _category_path(self, tid, page, ext):
        if tid == "latest":
            return "/movies?page_no=" + str(page) + "&page_size=20&sort_by=updated_at&sort_order=desc"
        if tid == "home":
            return "/movies?page_no=" + str(page) + "&page_size=20&is_home=1"
        if tid == "nav_ai":
            return "/movies?page_no=" + str(page) + "&page_size=20&tag_code=ai-%E7%9F%AD%E5%89%A7"
        if tid == "nav_actress":
            actress_val = str(ext.get("actress") or "").strip() or "ai短剧"
            return "/movies?page_no=" + str(page) + "&page_size=20&actress_code=" + urllib.parse.quote(actress_val, safe="-_.!~*'()")
        if tid in ("nav_media", "nav_cloth", "nav_role"):
            tag_val = str(ext.get("tag") or "").strip()
            if not tag_val and tid == "nav_cloth":
                tag_val = "旗袍"
            if tag_val:
                return "/movies?page_no=" + str(page) + "&page_size=20&tag_code=" + urllib.parse.quote(tag_val, safe="-_.!~*'()")
            return "/movies?page_no=" + str(page) + "&page_size=20&sort_by=updated_at&sort_order=desc"
        return "/movies?page_no=" + str(page) + "&page_size=20&sort_by=updated_at&sort_order=desc"

    # ---------- entries ----------
    def homeContent(self, filter=False):
        classes = [{"type_id": cid, "type_name": name} for cid, name, _ in self.CLASSES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, name, spec in self.CLASSES:
                if spec:
                    key, label, attr = spec
                    opts = getattr(self, attr)
                    filters[cid] = [{"key": key, "name": label, "value": [{"n": n, "v": v} for v, n in opts]}]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        d = self._fetch_api(self._category_path("latest", 1, {}))
        items = self._format_cards(d.get("list") if isinstance(d, dict) else None)
        return {"list": items[:18]}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        ext = extend if isinstance(extend, dict) else {}
        d = self._fetch_api(self._category_path(str(tid or "latest"), page, ext))
        items = self._format_cards(d.get("list") if isinstance(d, dict) else None)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        keyword = str(key or "").strip()
        if not keyword:
            return {"list": [], "page": page, "pagecount": page, "limit": 0, "total": 0}
        path = "/movies/search?keyword=" + urllib.parse.quote(keyword, safe="-_.!~*'()") + "&page_no=" + str(page) + "&page_size=20"
        d = self._fetch_api(path)
        items = self._format_cards(d.get("list") if isinstance(d, dict) else None)
        return {"list": items, "page": page, "pagecount": page + 1 if items else page, "limit": len(items), "total": len(items)}

    def detailContent(self, ids):
        if not ids:
            return {"list": []}
        code = str(ids[0] or "").strip()
        if not code:
            return {"list": []}
        d = self._fetch_api("/movies/" + urllib.parse.quote(code, safe=""))
        if not isinstance(d, dict) or not d.get("title"):
            return {"list": []}
        title = str(d.get("title_zh") or d.get("title") or "").strip()
        cover = str(d.get("cover") or "").strip()
        desc = str(d.get("desc") or d.get("intro") or "").strip()
        episodes = []
        videos = d.get("videos") if isinstance(d.get("videos"), list) else []
        for i, v in enumerate(videos):
            if not isinstance(v, dict):
                continue
            u = str(v.get("value") or "").strip()
            if not u:
                continue
            ep_name = str(v.get("label") or ("正片 " + str(i + 1).zfill(2))).strip()
            ep_name = ep_name.replace("$", "").replace("#", "")
            val = json.dumps({"playUrl": u}, ensure_ascii=False)
            episodes.append(ep_name + "$" + val)
        tag_names = []
        for t in (d.get("tags") if isinstance(d.get("tags"), list) else []):
            if isinstance(t, dict) and t.get("name_zh"):
                tag_names.append(str(t["name_zh"]))
        lines = [
            "🦋 DJHOLE官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "━━━━━━━",
        ]
        if desc:
            lines.append(desc)
        else:
            lines.append("标题：" + title)
            if tag_names:
                lines.append("分类：" + " · ".join(tag_names))
            lines.append("状态：" + ("无码高清" if d.get("is_uncensored") else "高清画质"))
            lines.append("片源：🦋 蝴蝶专线")
            lines.append("编号：" + code)
        vod = {
            "vod_id": code,
            "vod_name": title,
            "vod_pic": cover,
            "vod_remarks": "蝴蝶影视 | 无码" if d.get("is_uncensored") else "蝴蝶影视 | 高清",
            "vod_actor": "🦋 TG群: @tvshare23",
            "vod_director": "🦋 蝴蝶影视",
            "vod_content": "\n".join(lines),
            "vod_play_from": "🦋 蝴蝶专线",
            "vod_play_url": "#".join(episodes),
            "style": {"type": "rect", "ratio": 0.75 if self._is_ai_drama(d) else 1.78},
        }
        if tag_names:
            vod["vod_class"] = ",".join(tag_names)
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        play_url = ""
        try:
            data = json.loads(id)
            if isinstance(data, dict):
                play_url = str(data.get("playUrl") or "").strip()
        except Exception:
            pass
        headers = {"User-Agent": self.UA}
        if play_url:
            host_part = re.sub(r"^https?://", "", self.host)
            if "avgc9.store" in play_url or host_part in play_url:
                headers["Referer"] = self.host + "/"
            return {"parse": 0, "playUrl": "", "url": play_url, "header": headers}
        return {"parse": 1, "playUrl": "", "url": "", "header": headers}

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    def destroy(self):
        pass

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795250032836&sig=a47e15cf1008ad5d
