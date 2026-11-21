# -*- coding: utf-8 -*-
# 123AV - com.butterfly.123av
import base64
import json
import re
from urllib.parse import quote, unquote

import requests
from base.spider import Spider as BaseSpider

SITE_NAME = "123AV"
DEFAULT_HOST = "https://123av.com"
NAV_URLS = ["https://x99dh.net", "https://x99dh.lat"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
LINE_NAME = "🦋 蝴蝶专线"
RELATED_NAME = "相关推荐"
PAGE_SIZE = 12
PIC_RATIO = 1.78

COMMON_FILTERS = [
    {
        "key": "type",
        "name": "类型",
        "init": "",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "有码", "v": "censored"},
            {"n": "无码", "v": "uncensored"},
            {"n": "无码泄露", "v": "uncensored-leaked"},
        ],
    },
    {
        "key": "year",
        "name": "年份",
        "init": "",
        "value": [{"n": "全部", "v": ""}]
        + [{"n": str(2026 - i), "v": str(2026 - i)} for i in range(19)],
    },
    {
        "key": "actress",
        "name": "女演员",
        "init": "",
        "value": [
            {"n": "全部", "v": ""},
            {"n": "单人", "v": "single"},
            {"n": "多人", "v": "multiple"},
        ],
    },
]

ACTRESS_OPTIONS = [
    ('yui-hatano', 'Yui Hatano'),
    ('shinoda-yu', 'Hibiki Ohtsuki'),
    ('hibiki-ohtsuki', 'Hamazaki Mao'),
    ('hamazaki-mao', 'Kana Morisawa (Kanako Iioka)'),
    ('kana-morisawa-kanako-iioka', 'Ichika Matsumoto'),
    ('ichika-matsumoto', 'Hasumi Claire'),
    ('hasumi-claire', 'Niimura Akari'),
    ('niimura-akari', 'Aika'),
    ('aika', 'Mizuki Yayoi'),
    ('mizuki-yayoi-1', 'Kobayakawa Reiko'),
    ('kobayakawa-reiko', 'Waka Misono'),
    ('waka-misono', 'Aki Sasaki'),
    ('aki-sasaki', 'Asahi Mizuno'),
    ('asahi-mizuno', 'Julia'),
    ('julia', 'Kinoshita Himari (Hanazawa Himari)'),
    ('kinoshita-himari-hanazawa-himari', 'Mitsuki Nagisa'),
    ('mitsuki-nagisa', 'Yuu Kawakami (Shizuku Morino)'),
    ('yuu-kawakami-shizuku-morino', 'Yumi Kazama'),
    ('yumi-kazama', 'Alice Otsu'),
    ('alice-otsu', 'Akari Mitani'),
    ('akari-mitani', 'Minazuki Hikaru'),
    ('minazuki-hikaru', 'Ayumi Shinoda'),
    ('ayumi-shinoda', 'Kimishima Mio'),
]

GENRE_OPTIONS = [
    ('solowork', 'Solowork'),
    ('creampie', '中出'),
    ('big-tits', '大胸部'),
    ('married-womanhousewife', '已婚女性/家庭主妇'),
    ('amateur', '业余'),
    ('high-vision', '高视力'),
    ('e22f5b4c15', '口交'),
    ('beautiful-girl', '美丽的女孩'),
    ('beautiful-breasts', '美丽的乳房'),
    ('slender', '苗条'),
    ('gonzo', '哈梅哈'),
    ('slut', '荡妇'),
    ('threesome-foursome', '3P/4P'),
    ('squirting', '喷出'),
    ('digimo', '数字的'),
    ('cuckold-cuckolded-ntr', '乌龟, 乌龟, Ntr'),
    ('exclusive', '独家的'),
    ('over-4-hours', '4小时或以上'),
    ('paizuri', '乳交'),
    ('cowgirl', '女牛仔'),
    ('competitive-swimmingschool-swimwear', '竞技游泳/学校泳衣'),
    ('lewdhard', '淫秽/硬核'),
    ('facial', '面部的'),
    ('shaved-pussy', '排盘'),
    ('drama', '戏剧'),
    ('schoolgirl', '女学生'),
    ('older-sister', '姐姐'),
    ('handjob', '手淫'),
    ('big-ass', '大屁股'),
    ('planning', '规划'),
    ('masturbation', '手淫'),
    ('adultery', '事务'),
    ('mousozoku', '妄想集团'),
    ('nampa', '捡起'),
    ('cunnilingus', '舔阴'),
    ('documentary', '记录'),
    ('incest', '乱伦'),
    ('7889ef8307', '角色扮演'),
    ('humiliation', '屈辱'),
    ('sex-toys', '玩具'),
    ('bareback', '无套'),
    ('female-college-student', '大学女生'),
    ('deep-throat', '伊拉马乔'),
    ('beautiful-buttocks', '美丽的臀部'),
    ('ol', '奥尔'),
    ('uniform', '制服'),
    ('gal', '加尔'),
    ('orgy', '狂欢'),
    ('voyeurismpeeping', '偷窥癖'),
    ('shame', '耻辱'),
    ('other-fetishes', '其他恋物癖'),
    ('kisskiss', '吻'),
    ('anal', '肛门'),
    ('debut-work', '处女作'),
    ('butt-fetish', '屁股恋物癖'),
    ('idolcelebrity', '偶像和名人'),
    ('beautiful-legs', '美丽的双腿'),
    ('dirty-talk', '脏话'),
    ('restraint', '克制'),
    ('bestcompilation', '最佳/合辑'),
    ('acme-orgasm', '极致高潮'),
    ('small-breaststiny-breasts', '小乳房'),
    ('gulp', '吞'),
    ('lotion', '乳液/油'),
    ('bukkake', '颜射'),
    ('mother', '母亲'),
    ('club-hostess-sex-worker', '女主人, 妓女'),
    ('massage-reflex', '按摩和茶点'),
    ('electric-machine', '电动按摩器'),
    ('subjectivity', '主观'),
    ('vibrator', '氛围'),
    ('minimal-mosaic', '吉里莫扎'),
    ('pornstar', '色情明星'),
    ('back', '后退'),
    ('finger-fuck', '指法'),
    ('pantyhosetights', '连裤袜和紧身裤'),
    ('f0f0e4571c', '女同性恋'),
    ('sm', '钐'),
    ('older-sisteryounger-sister', '姐姐'),
    ('school-uniform', '校服'),
    ('14bfa6bb14', '六九'),
    ('bondage', '束缚'),
    ('various-occupations', '各种职业'),
    ('chubby', '波恰里'),
    ('urinationwetting', '撒尿/撒尿'),
    ('female-teacher', '女教师'),
    ('big-dickhuge-dick', '大鸡巴'),
    ('outdoorexposed', '户外/暴露'),
    ('young-wifeyoung-wife', '年轻的妻子'),
    ('beauty-salon', '美学'),
    ('swimsuit', '泳衣'),
    ('virginity', '处女'),
    ('tall', '高的'),
    ('fair-skin', '白皙的皮肤'),
    ('mouth-cumshot', '口交射精'),
    ('big-breast-fetish', '巨乳恋物癖'),
    ('m-man', 'M-Man'),
    ('vr-only', '仅限虚拟现实'),
    ('hot-spring', '温泉'),
    ('sweaty', '出汗'),
    ('lolichildlike-look', '萝莉/童趣外貌'),
    ('beautybeautiful-woman', '美女/漂亮女人'),
    ('nursenurse', '护士'),
    ('image-video', '图片视频'),
    ('cute-1', '可爱的'),
    ('devil', '残忍的'),
    ('age-bracket-30s40setc', '年龄段（30岁/40岁/等等）'),
    ('lingerie', '内衣'),
    ('panty-shots', 'Panchira'),
    ('foot-fetish', '恋腿癖'),
    ('m-woman', 'M女人'),
    ('vr', 'Vr'),
    ('petite', '娇小'),
    ('neat', '整洁的'),
    ('kimono', '日式服装/浴衣'),
    ('mini-series', '小型的'),
    ('emmanuelle', '伊曼纽尔'),
    ('drag', '拖'),
    ('mother-in-law', '岳母'),
    ('super-milk', '巨大的乳房'),
    ('face-sitting', '颜面骑乘'),
    ('glasses', '眼镜'),
    ('harem', '后宫'),
    ('lesbian-kissing', '女同之吻'),
    ('8kvr', '8Kvr'),
    ('sailor-suit', '水手服'),
    ('maid', '女佣'),
    ('virgin-1', '处女'),
    ('couple', '夫妻'),
    ('footjob', '足交'),
    ('close-up', '特写'),
    ('high-quality-vr', '高品质虚拟现实'),
    ('shemale', '新一半'),
    ('mischief', '恶作剧'),
    ('immediate-saddle', '立即的'),
    ('confinement', '禁闭'),
    ('cross-dressingmale-girl', '变装/男孩'),
    ('gym-clothes-bloomers', '运动服/灯笼裤'),
    ('bitch', '贱人'),
    ('black-hair', '黑发'),
    ('actress-best-compilation', '最佳女主角合辑'),
    ('bath', '洗澡'),
    ('multiple-episodes', '多个故事'),
    ('erotic-wear', '情趣服装'),
    ('impregnate', '怀孕'),
    ('female-boss', '女老板'),
    ('health-soap', '健康香皂'),
    ('post', '帖子'),
    ('drinking-party', '酒会/约会'),
    ('black-actor', '黑人演员'),
    ('miniskirt', '超短裙'),
    ('enema', '灌肠剂'),
    ('love-affair', '爱'),
    ('dvd-toaster', 'Dvd 烤面包机'),
    ('original-collaboration', '原创合作'),
    ('female-investigator', '女调查员'),
    ('model', '模型'),
    ('dating', '日期'),
    ('school-stuff', '学校用品'),
    ('tutor', '私人教师'),
    ('lesbian', '女同性恋'),
    ('sports', '运动的'),
    ('fan-appreciation-home-visit', '粉丝欣赏/访问'),
    ('sunburn', '晒斑'),
    ('torture', '酷刑'),
    ('stewardess', '空中小姐'),
    ('others', '其他'),
    ('shota', '翔太'),
    ('sexy', '性感'),
    ('white-actress', '白人女演员'),
    ('widow', '寡妇'),
    ('ladydaughter', '女士'),
    ('baby-facechildlike-face', '婴儿脸/稚嫩脸'),
    ('hotel', '酒店'),
    ('childhood-friend', '年轻的纳吉米'),
    ('delusion', '妄想'),
    ('rotor', '转子'),
    ('leotards', '紧身衣'),
    ('female-announcer', '女性安娜'),
    ('secretary', '秘书'),
    ('business-attire', '商务套装'),
    ('reverse-number', '反向 Nan'),
    ('for-women', '对女性来说'),
    ('special-effects', '特殊效果'),
    ('manguripiledriver-position', '芒古里/打桩机位置'),
    ('bunny-girl', '兔女郎'),
    ('breast-milk', '母乳'),
    ('hairypubic-hair', '阴毛'),
    ('dildo', '假阳具'),
    ('female-doctor', '女医生'),
    ('drinking-urine', '喝尿'),
    ('innocent', '清白的'),
    ('subordinatescolleagues', '下属/同事'),
    ('man-squirting', '男性潮吹'),
    ('instructor', '讲师'),
    ('short-hair', '短发'),
    ('muscle', '肌肉'),
    ('7520ed52ed', '美臀'),
    ('waist', '腰部'),
    ('no-bra', '诺布拉'),
    ('foreign-object-insertion', '异物插入'),
    ('portio', '波尔基奥'),
    ('car-sex', '汽车性爱'),
    ('nice-bodygreat-style', '身材好/风格很棒'),
    ('travel', '旅行'),
    ('actionfighting', '动作/格斗'),
    ('sex-position-misc', '性爱姿势（其他）'),
    ('white-of-the-eyesfainting', '眼白/昏厥'),
    ('race-queen', '赛车皇后'),
    ('western-pinsoverseas-imports', '西部别针和进口商品'),
    ('cusco', '楠子'),
    ('athlete', '运动员'),
    ('onasapo', 'Ona 支持'),
    ('proprietress-landlady', '女房东/情妇'),
    ('tsundere', '傲娇'),
    ('spanking', '打屁股'),
    ('hospitalclinic', '医院和诊所'),
    ('naked-apron', '裸体围裙'),
    ('fantasy', '幻想'),
    ('rape', '强奸'),
    ('long-hair', '长发'),
    ('beautiful-skinwhitening', '美白肌肤'),
    ('daughteradoptive-daughter', '女儿/养女'),
    ('58fc0c7a98', '原始性爱'),
    ('aunt', '阿姨'),
    ('knee-socks', '及膝袜'),
    ('molesterchikan', '性骚扰者/痴汉'),
    ('ff46e22870', '荣耀探索 40% 折扣促销'),
    ('vip', 'Vip'),
    ('dc863e2c60', '美丽'),
    ('queen', '情妇'),
    ('dance', '舞蹈'),
    ('club-activities-manager', '俱乐部/经理'),
    ('bodycon', '紧身连衣裙'),
    ('cat-earsbeast-type', '猫耳/动物'),
    ('eb19a4e304', '可爱的'),
    ('fist', '拳头'),
    ('pregnant-woman', '孕妇'),
    ('bride', '新娘'),
    ('teenyoung-18', '青少年/青年（18岁以上）'),
    ('female-warrior', '女战士'),
    ('premature-ejaculation', '早泄'),
    ('av-3', 'AV女優'),
    ('pervert', '变态'),
    ('action', '行动'),
    ('sod3040', 'SOD30周年40%オフセール'),
    ('grandfather', '爷爷'),
    ('brutal-expression', '残酷'),
    ('time-stop', '时间停止'),
    ('transformation-heroine', '变身女主角'),
    ('how-to', '如何'),
    ('soft-body', '软体'),
    ('asian-actresses', '亚洲女演员'),
    ('high-sensitivity', '高灵敏度'),
    ('puke', '呕吐'),
    ('scatology', '粪便'),
    ('sokkurisan', '索库里山'),
    ('nipple-slip', '乳房闪烁'),
    ('interview', '面试'),
    ('no-panties', '无裤'),
    ('blonde', '金发女郎'),
    ('dark-skin', '深色皮肤'),
    ('celebrity', '名人'),
    ('swapping', '交换'),
    ('nipple-play', '乳头游戏'),
    ('sex-changefeminization', '性别弯曲/女性化'),
    ('breeding', '选育'),
    ('drunk', '醉'),
    ('tickling', '楠'),
    ('m', 'M'),
    ('anal-sex', '肛交'),
    ('a632acd889', '美丽的女人'),
    ('defecation', '排便'),
    ('campaign-girl', '糖果'),
    ('waitress', '女服务员'),
    ('nose-hook', '鼻钩'),
    ('dark-system', '黑暗的'),
    ('loose-socks', '宽松的袜子'),
    ('b0e982044a', 'アナルセックス(男ノ娘)'),
    ('sumata-non-penetrative', '苏玛塔（非穿透性）'),
    ('abuse', '侮辱'),
    ('nationality-taiwanrussiahalf', '国籍（台湾/俄罗斯/混血）'),
    ('limited-time-sale', '限时促销'),
    ('b660a1357d', '口射'),
    ('d10e314b86', '巨乳キャンペーン'),
    ('mask-mask', '面具'),
    ('mom-friend', '妈妈的朋友'),
    ('beautiful-pussy', '美丽的猫咪'),
    ('cheongsam-dress', '中式服饰'),
    ('futanari', '双成'),
    ('otaku', '御宅族'),
    ('anime-characters', '动漫人物'),
    ('breasts-generic-ungraded', '乳房（通用，未分级）'),
    ('limited-to-fanza-distribution', 'Fanza独家'),
    ('de76af0a33', '2次射精'),
    ('foreigner', '外国人'),
    ('receptionist', '接待员'),
    ('1e15769cb4', 'Delusional Tribe - Emmanuel 40% 折扣促销'),
    ('candle', '蜡烛'),
    ('cheerleader', '啦啦队女孩'),
    ('doll', '玩具娃娃'),
    ('yoga', '瑜伽'),
    ('brown-hair', '棕色头发'),
    ('4aed778d5c', 'Next Group感恩节促销，全场40%折扣'),
    ('417110abc4', '可爱的'),
    ('gag-comedy', '搞笑喜剧'),
    ('tentacles', '触手'),
    ('82688fd853', '20岁'),
    ('grandma', '奶奶'),
    ('companion', '伴侣'),
    ('ae186fcf7f', '洛丽塔类型'),
    ('06bec123a2', '胸部'),
    ('cny', '前偶像'),
    ('73ea7f13a9', '一日拍摄'),
    ('g-1', 'G罩杯'),
    ('a815466d96', '手淫'),
    ('hairstyle-twintailponytailbob', '发型（双马尾/马尾/波波头）'),
    ('bus-tour-guide', '巴士指南'),
    ('sci-fi', '科幻小说'),
    ('shrine-maiden', '巫女'),
    ('martial-artist', '战斗机'),
    ('s', 'S 女人'),
    ('3d', '3D'),
    ('blindfold', '眼罩'),
    ('indies', '印度群岛'),
    ('beauty', '美丽'),
    ('hypnosisbrainwashing', '催眠/洗脑'),
    ('over-16-hours', '16+小时'),
    ('w', 'W形手指人'),
    ('set-product', '套装产品'),
    ('kunoichi', '女野市'),
    ('magical-girl', '魔法少女'),
    ('33a0e9d009-1', '粗硬的头发'),
    ('reprint', '重印'),
    ('716b636399', '额外赠送'),
    ('4k', '4K拍摄'),
    ('9e108af5d0', '没有任何'),
    ('2116ccf696-1', '偶像'),
    ('f-1', 'F罩杯'),
    ('d97496ec3b', '口交'),
    ('av-open-2014-heavyweight', '2014年Av公开赛重量级'),
    ('seasonalholiday', '季节性/节日'),
    ('b30c1a985e', '生的'),
    ('fc43e2da49', '美丽的肌肤'),
    ('3144284b4b', '传教士职位'),
    ('9198b827fe', '西德克'),
    ('confession-of-experience', '体验告白'),
    ('30', '30年代'),
    ('70d2b9a4d3', '小胸'),
    ('e-1', 'E杯'),
    ('neglect', '弃'),
    ('f5627f945b', '伊卡斯游戏'),
    ('b1b332b734', '两次射精'),
    ('firststar40-1', 'マーキュリー・FirstStar・ワー40%オフセール'),
    ('medium-hair', '中型头发'),
    ('tattoo', '纹身'),
    ('av-open-2014-middle-class', '2014年Av Open中级'),
    ('4aa5600cd7', '小胸'),
    ('b48b612c43', '怀孕'),
    ('1ff879de5d', '敏感的'),
    ('av-open-2015-planning-division', '2015年Av公开企划部'),
    ('coprophagy', '食粪行为'),
    ('511ff31f89', '恭喜你成年啦！成年人专享40%折扣！'),
    ('firststar40', 'Mercury、Firststar，40% 折扣促销'),
    ('4ac27f00cf', '高的'),
    ('boyish', '偏干'),
    ('horror', '恐怖'),
    ('dialect', '方言'),
    ('2ee8e88780', '一镜到底'),
    ('19', '19岁'),
    ('ca', '钙'),
    ('ab6c23aea2', '过去 1'),
    ('edging', '埃布利'),
    ('c08a240662-1', 'ディスクオンデマンドセール'),
    ('2de202ecda', '尊享冬季庆典 - 最高可享50%折扣'),
    ('v-cinema', 'V-影院'),
    ('h-1', 'H罩杯'),
    ('6f61b9f992', '天真（幼稚）型'),
    ('40-4', '妄想族・エマニエル40%オフセール'),
    ('40-2', 'プレステージ40%オフセール'),
    ('v', '虚拟主播'),
    ('bondage-1', '束缚'),
    ('curly-hair', '卷发'),
    ('18', '18岁'),
    ('89a5a51891', '全球媒体 40% 折扣促销'),
    ('collaboration-work', '合作作品'),
    ('06ae3252c9', '一半在外面，一半在里面'),
    ('3c4e72db34', 'Ipoke 活动'),
    ('70ecf2ba69', '娃娃脸'),
    ('57f900cfa6', '生哈梅'),
    ('420073d82a', '第二轮'),
    ('72c9b14385', '原始射精'),
    ('de0737b86a', '阴毛'),
    ('027267b1e5', '变态'),
    ('6f4922f455', '18'),
    ('3151a87f89', '吻'),
    ('3dbdbd029d', '曼古里盖什'),
    ('threesome-foursome-1', 'Threesome / Foursome'),
    ('5197f94a8c', '绝佳风格'),
    ('av-open-2015-maniafetish-section', 'Av Open 2015 狂热/恋物癖部分'),
    ('c08a240662', '按需折扣促销'),
    ('high-heels-1', '高跟鞋'),
    ('0262798b1a', '奇帕伊'),
    ('8bc0a4b00d', '3次射精'),
    ('paradise-tv', '天堂电视台'),
    ('av-open-2016-dramadocumentary-category', 'Av Open 2016 剧情/纪录片类'),
    ('gay', '同性恋'),
    ('68ef1e67bd', '真正的奶油派'),
    ('av-open-2016-maniafetish-section', 'Av Open 2016 疯狂/恋物部分'),
    ('af3731b1a3', '大屁股'),
    ('e538d644dd', '连续两次射精'),
    ('285f1d32d0', '阴毛'),
    ('59b6cd8984', 'Prestige 40% 折扣促销'),
    ('20-2', '20岁'),
    ('9eb330fb55', '2 发'),
    ('av-open-2015-smhard', '2015 年 Av Open 小型/硬式'),
    ('6000752b01', '舔乳头'),
    ('40-3', '40年代'),
    ('miniskirt-police', '米尼斯卡波利斯'),
    ('f3de6fe979', '伊卡塞'),
    ('d174f2fa2f', '土豆'),
    ('mgs', 'Mgs独家花絮'),
    ('m-2', '受虐狂'),
    ('gothic-lolita', '哥特洛丽塔'),
    ('40', 'ネクストグループ感謝祭40%オフセール'),
    ('68a853de7e', '萝莉'),
    ('avopen2016', 'Avopen2016 策划部'),
    ('av-open-2018-maniafetish-section', '2018 年 Av 公开赛狂热/恋物癖部分'),
    ('av-open-2016-amateur-division', '2016年Av公开赛业余组'),
    ('981d556942', '美丽的身体'),
    ('29b54e86a8', '大约40'),
    ('firststar40-2', 'マーキュリー・FirstStar・ワー40%オフセール'),
    ('av-open-2015-maiden-division', '2015年Av公开赛青少年组'),
    ('av-open-2016-planning-division', '2016年Av公开企划部'),
    ('7af2301034', '初井'),
    ('168e962cc7', '5次射精'),
    ('360356cc66', '未公开'),
    ('1ac199e19d', '无需分阶段'),
    ('ad615d068e', '难波大师'),
    ('d-1', 'D罩杯'),
    ('princess', '公主'),
    ('92a5bfbda2', 'Nagae Style 40% 折扣促销'),
    ('sex', '晨间性爱'),
    ('60483a8c81', '单反'),
    ('av-open-2015-actress-category', '2015年Av公开赛女演员组'),
    ('bdd6ddecb7', '施肥'),
    ('i-1', 'I罩杯'),
    ('288b949695', '额外赠送'),
    ('e91247059d', '关系'),
    ('19772ca0cb', '车站便当（火车站便当盒）'),
    ('b6e2bac86d-1', '名人'),
    ('av-open-2017-documentary-division', '2017年Av Open纪录片组'),
    ('1c26b087b6', '大屌'),
    ('79591548e5', 'Crystal Video 限时4折优惠'),
    ('63d62e674c', '诺克佐里'),
    ('a009caa7d8', '汗'),
    ('efb70a9ebd', '长的'),
    ('game-live-action', '真人游戏'),
    ('73b3fb2c7b', '情色的声音'),
    ('91438c2572', '乌贼'),
    ('av-open-2016-hard-division', '2016年Av公开赛硬地组'),
    ('b193685f69', '伦雷科米'),
    ('6269f71c84', '连续两次射击'),
    ('d4072c2279-1', '清白的'),
    ('av-open-2015-amateur-division', '2015年Av公开赛业余组'),
    ('fa6c3bd68d', '个人姓名'),
    ('av-open-2016-actress-category', '2016年Av公开赛女演员组'),
    ('9ae6a51d56', '浴室'),
    ('9e5f956fbf', '勃起的阴茎'),
    ('av-open-2017-drama-division', '2017年Av Open戏剧组'),
    ('7644a5ef05', '美男子'),
    ('74045258fb', '打桩机'),
    ('40-1', 'ナガエスタイル40%オフセール'),
    ('a9e3de41ce', '潜望镜'),
    ('e1d1b6803a', '三十岁'),
    ('av-open-2017-mania-division', '2017 年 Av Open Mania 赛区'),
    ('with-benefits-av-baseball', '可用奖金(Avbaseball)'),
    ('eros', '爱神'),
    ('51c0e60d04', '禁忌'),
    ('psycho-thriller', '心理惊悚片'),
    ('11e98d336a', '第二轮'),
    ('20', '20多岁'),
    ('1a84c82331', '连续两次射精'),
    ('9284a916c3', '儿童保育员'),
    ('58a400a704', '多产妇'),
    ('55e867dc09', '加奇'),
    ('c8cd504489', '年轻男子'),
    ('e7a61bc461', '离婚'),
    ('ad7c62202d', '差距'),
    ('fb3e1c40c2', '黑色丝袜'),
    ('a8a35b28c7', '最可爱的'),
    ('5075d717b1', '性吸引力'),
    ('aa5e200bf8', '收紧'),
    ('e171e172a0', '神体'),
    ('4ff0077a46', '成人'),
    ('caffa39254', '双和平'),
    ('7922d155a1', '音乐系学生'),
    ('b6e4df7da5', '张口射精'),
    ('447f9b7430', '魅力四射'),
    ('188ac4f9d0', '性感内衣'),
    ('bb707bbfd7', 'Vibe（那个糟糕的）'),
    ('517f59875f', '全身渔网袜'),
    ('a97cdc722e', '衣领'),
    ('a02753a6b7', '眼罩'),
    ('45f6bdf642', '游泳俱乐部'),
    ('be98be125c', '溅'),
    ('anime', '日本动画片'),
    ('fd8dfe8caa', '小脸'),
    ('68f8697c8c', '厨房'),
    ('bb1ee8eb76', '小阴唇'),
    ('c6ae14637d', '纯的'),
    ('a6dc80113e', '游戏'),
    ('tiktok', '抖音'),
]

MAKER_OPTIONS = [
    ('s-cute', 'S-CUTE'),
    ('fc2', 'FC2'),
    ('heyzo', 'HEYZO'),
    ('1pondo', '1pondo'),
    ('caribbeancom', 'Caribbeancom'),
    ('10musume', '10musume'),
    ('pacopacomama', 'Pacopacomama'),
    ('tokyo-hot', 'Tokyo Hot'),
    ('xxx-av', 'XXX-AV'),
    ('moodys', 'MO Moody&#039;s 12,790个视频 + 关注 已关注'),
    ('sod-create', 'SO Sod Create 12,695个视频 + 关注 已关注'),
    ('madonna', 'MA Madonna 12,219个视频 + 关注 已关注'),
    ('prestige', 'PR Prestige 10,385个视频 + 关注 已关注'),
    ('s1-number-one-style', 'S1 S1 Number One Style 9,038个视频 + 关注 已关注'),
    ('tv', '电视 电视机 8,356个视频 + 关注 已关注'),
    ('km-produce', 'K. K.m. Produce 7,181个视频 + 关注 已关注'),
    ('attackers', 'AT Attackers 6,983个视频 + 关注 已关注'),
    ('idea-pocket', 'ID Idea Pocket 6,842个视频 + 关注 已关注'),
    ('center-village', 'CE Center Village 4,213个视频 + 关注 已关注'),
    ('hunter', 'HU Hunter 4,131个视频 + 关注 已关注'),
    ('glory-quest', 'GL Glory Quest 4,044个视频 + 关注 已关注'),
    ('doc', 'DO Doc 4,042个视频 + 关注 已关注'),
    ('fitch', 'FI Fitch 3,982个视频 + 关注 已关注'),
    ('venus', 'VE Venus 3,862个视频 + 关注 已关注'),
    ('honchu', 'HO Honchu 3,616个视频 + 关注 已关注'),
    ('yessssss', 'YE Yessssss! 3,529个视频 + 关注 已关注'),
    ('fb5491cb59', 'S- S-One 第一风格 3,432个视频 + 关注 已关注'),
    ('premium', 'PR Premium 3,302个视频 + 关注 已关注'),
    ('natural-high', 'NA Natural High 3,286个视频 + 关注 已关注'),
    ('celebrity-friends', 'CE Celebrity Friends 3,261个视频 + 关注 已关注'),
    ('planet-plus', 'PL Planet Plus 3,165个视频 + 关注 已关注'),
    ('ones-factory', 'ON One&#039;s Factory 3,133个视频 + 关注 已关注'),
    ('faleno', 'FA Faleno 3,132个视频 + 关注 已关注'),
    ('takara-video', 'TA Takara Video 3,081个视频 + 关注 已关注'),
    ('prestige-premium', '尊贵 尊贵高级版 3,059个视频 + 关注 已关注'),
    ('kawaii', 'KA Kawaii 2,917个视频 + 关注 已关注'),
    ('e-body', 'E- E-Body 2,909个视频 + 关注 已关注'),
    ('tameike-goro', 'TA Tameike Goro 2,830个视频 + 关注 已关注'),
    ('deeps', 'DE Deeps 2,830个视频 + 关注 已关注'),
    ('crystal-video', 'CR Crystal Video 2,819个视频 + 关注 已关注'),
    ('oppai', 'OP Oppai 2,601个视频 + 关注 已关注'),
    ('first-star', 'FI First Star 2,283个视频 + 关注 已关注'),
    ('im-an-amateur-z', 'I&#039; I&#039;m An Amateur -Z- 2,266个视频 + 关注 已关注'),
    ('energy', 'EN Energy 2,198个视频 + 关注 已关注'),
    ('maximizing', 'MA Maximizing 2,127个视频 + 关注 已关注'),
    ('mercury', 'ME Mercury 2,112个视频 + 关注 已关注'),
    ('alice-japan', 'AL Alice Japan 2,107个视频 + 关注 已关注'),
    ('h4610', 'H4 H4610 1,937个视频 + 关注 已关注'),
    ('ruby', 'RU Ruby 1,923个视频 + 关注 已关注'),
    ('max-a', 'MA Max A 1,921个视频 + 关注 已关注'),
    ('big-mocal', 'BI Big Mocal 1,809个视频 + 关注 已关注'),
    ('hmp', 'HM Hmp 1,801个视频 + 关注 已关注'),
    ('rocket', 'RO Rocket 1,763个视频 + 关注 已关注'),
    ('c0930', 'C0 C0930 1,700个视频 + 关注 已关注'),
    ('h0930', 'H0 H0930 1,674个视频 + 关注 已关注'),
    ('momotaro-video-publishing', 'MO Momotaro Video Publishing 1,645个视频 + 关注 已关注'),
    ('714b15b1cf', '第一 第一颗星 1,631个视频 + 关注 已关注'),
    ('aurora-project-annex', 'AU Aurora Project Annex 1,621个视频 + 关注 已关注'),
    ('avs-collectors', 'AV Avs Collector&#039;s 1,555个视频 + 关注 已关注'),
    ('fa47310ad1', '荡妇 荡妇天堂 1,542个视频 + 关注 已关注'),
    ('innocence', 'IN Innocence 1,522个视频 + 关注 已关注'),
]

CATEGORIES = [
    ("cn/hot", "🔥 热门"),
    ("cn/new", "✨ 最新"),
    ("cn/recent", "🕒 最近"),
    ("cn/censored", "🎯 有码"),
    ("cn/uncensored", "💎 无码"),
    ("cn/uncensored-leaked", "⚠️ 无码泄露"),
    ("cn/all?sort=today", "📈 今日趋势"),
    ("cn/all?sort=week", "📊 本周趋势"),
    ("cn/all?sort=month", "📉 本月趋势"),
    ("filter@@actress", "💃 女演员专区"),
    ("filter@@genre", "🏷️ 类别专区"),
    ("filter@@maker", "🏢 制作商专区"),
    ("cn/series", "🎬 系列专栏"),
    ("cn/tags/siro", "SIRO"),
    ("cn/tags/259luxu", "LUXU"),
    ("cn/tags/200gana", "200GANA"),
    ("cn/tags/prestige-premium", "PRESTIGE"),
    ("cn/tags/230oreco", "ORECO"),
    ("cn/makers/s-cute", "S-CUTE"),
    ("cn/tags/261ara", "ARA"),
    ("cn/tags/390jac", "390JAC"),
    ("cn/makers/fc2", "FC2"),
    ("cn/makers/heyzo", "HEYZO"),
    ("cn/makers/1pondo", "1pondo"),
    ("cn/makers/caribbeancom", "Caribbeancom"),
    ("cn/makers/10musume", "10musume"),
    ("cn/makers/pacopacomama", "Pacopacomama"),
    ("cn/makers/tokyo-hot", "Tokyo Hot"),
    ("cn/makers/xxx-av", "XXX-AV"),
]

TITLE_RE = re.compile(r"<(?:h3|h4|div|a)[^>]*class=[\"'][^\"']*title[^\"']*[\"'][^>]*>([\s\S]*?)</", re.I)
NEXT_A_RE = re.compile(r"</a>\s*<a[^>]+href=[\"']/cn/v/[^\"']+[\"'][^>]*>([\s\S]*?)</a>", re.I)
LINK_RE = re.compile(r"href=[\"'](/cn/v/[^\"']+)[\"']", re.I)
IMG_RE = re.compile(r"<img[^>]+src=[\"'](https?://[^\"']+)[\"']", re.I)
DUR_RE = re.compile(r"class=\"card__dur\">([\s\S]*?)</span>", re.I)
H1_RE = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
POSTER_PARAM_RE = re.compile(r"poster=([^\s&\"']+)")
POSTER_COVER_RE = re.compile(r"url\([\"']?(https?://[^\"')]+cover\.[^\"')]+)[\"']?\)", re.I)
ACTRESS_RE = re.compile(r"<a[^>]+href=[\"']/cn/actresses/[^\"']+[\"'][^>]*>([\s\S]*?)</a>", re.I)
PLAYER_RE = re.compile(r"x-data=\"player\(JSON\.parse\('([\s\S]*?)'\)")
QUOTED_STREAM_RE = re.compile(r"[\"'](https?:\\?/\\?/[^\"']*(?:javplayer|player|embed|\.m3u8)[^\"']*)[\"']")
YEAR_RE = re.compile(r"\b20[12][0-9]\b")
CHIP_RE = re.compile(r"<a[^>]+class=[\"']chip[\"'][^>]+href=[\"']/cn/genres/[^\"']+[\"'][^>]*>([\s\S]*?)</a>", re.I)
VSIDE_RE = re.compile(r"<a[^>]+class=[\"']vside[\"'][^>]+href=[\"'](/cn/v/[^\"']+)[\"'][^>]*>([\s\S]*?)</a>", re.I)
VSIDE_THUMB_RE = re.compile(r"background-image:url\('([^']+)'\)", re.I)
VSIDE_DUR_RE = re.compile(r"class=\"vside__dur\">([\s\S]*?)</span>", re.I)
VSIDE_TITLE_RE = re.compile(r"class=\"vside__title\">([\s\S]*?)</span>", re.I)
M3U8_QUOTED_RE = re.compile(r"[\"'](https?://[^\"']+\.m3u8[^\"']*)[\"']", re.I)
MP4_QUOTED_RE = re.compile(r"[\"'](https?://[^\"']+\.mp4[^\"']*)[\"']", re.I)
EMBED_ID_RE = re.compile(r"^(https?://[^/]+)/e/([a-zA-Z0-9_]+)", re.I)
DIRECT_MEDIA_RE = re.compile(r"\.(m3u8|mp4|flv|mpd)(\?|$)", re.I)
B64_RE = re.compile(r"[\"']([A-Za-z0-9+/=]{100,})[\"']")
ORIGIN_RE = re.compile(r"^(https?://[^/]+)", re.I)


def _unescape_html(s):
    s = str(s or "")
    s = s.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    s = s.replace("&quot;", '"').replace("&#039;", "'").replace("&#39;", "'")
    s = s.replace("&nbsp;", " ")
    return s


def _strip_tags(s):
    return re.sub(r"<[^>]+>", "", str(s or ""))


def _clean_stream_url(u):
    return str(u or "").replace("\\/", "/").replace("\\", "")


def _sanitize_ep_name(name):
    return str(name or "").replace("$", "_").replace("#", "_")


class Spider(BaseSpider):
    def __init__(self):
        self.host = DEFAULT_HOST
        self._custom_host = False
        self._discovered = False

    # ---------- lifecycle ----------

    def init(self, extend=""):
        self.host = DEFAULT_HOST
        self._custom_host = False
        self._discovered = False
        custom = ""
        if isinstance(extend, dict):
            custom = str(extend.get("host") or "").strip()
        elif isinstance(extend, str) and extend.strip():
            text = extend.strip()
            if text.startswith("{"):
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        custom = str(data.get("host") or "").strip()
                except Exception:
                    custom = ""
            else:
                custom = text
        if custom.startswith("http"):
            self.host = custom.rstrip("/")
            self._custom_host = True

    def homeContent(self, filter):
        classes = [{"type_id": cid, "type_name": cname} for cid, cname in CATEGORIES]
        result = {"class": classes}
        if filter:
            filters = {}
            for cid, _cname in CATEGORIES:
                if cid == "filter@@actress":
                    filters[cid] = [self._slug_row("选择女优", "全部女演员", ACTRESS_OPTIONS)] + COMMON_FILTERS
                elif cid == "filter@@genre":
                    filters[cid] = [self._slug_row("选择题材", "全部题材", GENRE_OPTIONS)] + COMMON_FILTERS
                elif cid == "filter@@maker":
                    filters[cid] = [self._slug_row("选择制作商", "全部制作商", MAKER_OPTIONS)] + COMMON_FILTERS
                else:
                    filters[cid] = COMMON_FILTERS
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        text = self._fetch_text("/cn/new")
        items = self._parse_cards(text)[:18]
        return {"list": items}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        extend = extend if isinstance(extend, dict) else {}
        tid = str(tid or "cn/new").strip("/")
        query_parts = []
        if page > 1:
            query_parts.append("page=" + str(page))
        if tid == "filter@@actress":
            slug = str(extend.get("slug") or "").strip()
            target = "/cn/actresses/" + quote(slug, safe="") if slug else "/cn/new"
        elif tid == "filter@@genre":
            slug = str(extend.get("slug") or "").strip()
            target = "/cn/genres/" + quote(slug, safe="") if slug else "/cn/new"
        elif tid == "filter@@maker":
            slug = str(extend.get("slug") or "").strip()
            target = "/cn/makers/" + quote(slug, safe="") if slug else "/cn/new"
        elif "?" in tid:
            parts = tid.split("?")
            target = "/" + parts[0]
            query_parts.append(parts[1])
        else:
            target = "/" + tid
        for key in ("type", "year", "actress"):
            val = extend.get(key)
            if val:
                query_parts.append(key + "=" + quote(str(val), safe=""))
        if query_parts:
            sep = "&" if "?" in target else "?"
            target = target + sep + "&".join(query_parts)
        text = self._fetch_text(target)
        items = self._parse_cards(text)
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
        target = "/cn/search?keyword=" + quote(keyword, safe="") + "&page=" + str(page)
        text = self._fetch_text(target)
        items = self._parse_cards(text)
        return self._page_form(items, page)

    def detailContent(self, ids):
        raw_id = str(ids[0] if ids else "").strip()
        if not raw_id:
            return {"list": []}
        path = raw_id if raw_id.startswith("http") else "/" + raw_id.lstrip("/")
        fetched = self._fetch(path)
        html = fetched["text"]
        if not html:
            return {"list": []}
        host_used = fetched["host"]
        final_url = fetched["final_url"] or (host_used + path)

        h1 = H1_RE.search(html)
        vod_name = _strip_tags(h1.group(1)).strip() if h1 else ""
        if not vod_name:
            vod_name = raw_id.split("/")[-1].upper()

        vod_pic = ""
        pm = POSTER_PARAM_RE.search(html)
        if pm:
            try:
                vod_pic = unquote(pm.group(1))
            except Exception:
                vod_pic = pm.group(1)
        if not vod_pic:
            pm2 = POSTER_COVER_RE.search(html)
            if pm2:
                vod_pic = pm2.group(1).strip()
        clean = re.match(r"^https?://[^\s\"'\\]+", vod_pic)
        if clean:
            vod_pic = clean.group(0)

        actresses = []
        for am in ACTRESS_RE.finditer(html):
            an = _strip_tags(am.group(1)).strip()
            if an and an not in actresses and len(an) < 25:
                actresses.append(an)
        if actresses:
            vod_actor = "、".join(actresses) + "、" + BRAND_ACTOR
        else:
            vod_actor = BRAND_ACTOR

        episodes = self._detail_episodes(html)
        if episodes:
            ep_strs = []
            for ep in episodes:
                env = json.dumps({"playUrl": ep["url"]}, ensure_ascii=False)
                ep_strs.append(ep["name"] + "$" + env)
            main_eps = "#".join(ep_strs)
        else:
            env = json.dumps({"pageUrl": final_url}, ensure_ascii=False)
            main_eps = "正片$" + env

        related = self._parse_related(html, raw_id)
        play_from = LINE_NAME
        play_url = main_eps
        if related:
            rel_strs = []
            for item in related:
                rel_strs.append(_sanitize_ep_name(item["title"]) + "$rel:" + item["id"])
            play_from = LINE_NAME + "$$$" + RELATED_NAME
            play_url = main_eps + "$$$" + "#".join(rel_strs)

        ym = YEAR_RE.search(html)
        vod_year = ym.group(0) if ym else ""
        dm = DUR_RE.search(html)
        dur = dm.group(1).strip() if dm else ""
        vod_remarks = ("蝴蝶影视 · " + dur) if (dur and dur != "0:00") else "蝴蝶影视"

        genres = []
        for gm in CHIP_RE.finditer(html):
            gn = _strip_tags(gm.group(1)).strip()
            if gn and gn not in genres:
                genres.append(gn)

        code = raw_id.split("/")[-1].upper()
        content = self._summary(vod_name, genres, code, related)

        vod = {
            "vod_id": raw_id,
            "vod_name": _unescape_html(vod_name),
            "vod_pic": vod_pic,
            "vod_bg": vod_pic,
            "vod_background": vod_pic,
            "vod_banner": vod_pic,
            "vod_year": vod_year,
            "vod_remarks": vod_remarks,
            "vod_actor": vod_actor,
            "vod_director": BRAND_DIRECTOR,
            "vod_content": content,
            "vod_play_from": play_from,
            "vod_play_url": play_url,
        }
        return {"list": [vod]}

    def playerContent(self, flag, id, vipFlags):
        raw = str(id or "")
        if raw.startswith("rel:"):
            return self._resolve_related(raw[4:])
        play_url = ""
        page_url = ""
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                play_url = str(data.get("playUrl") or "")
                page_url = str(data.get("pageUrl") or "")
        except Exception:
            play_url = raw
        raw_url = _clean_stream_url(play_url or page_url)
        if not raw_url:
            return {"parse": 1, "url": self.host + "/cn", "header": {"User-Agent": UA, "Referer": self.host + "/cn"}}
        headers = {"User-Agent": UA, "Referer": self.host + "/cn"}
        if DIRECT_MEDIA_RE.search(raw_url) or "index.png" in raw_url:
            return {"parse": 0, "url": raw_url, "header": headers}
        if "javplayer.cc" in raw_url or "/e/" in raw_url:
            fetched = self._fetch(raw_url, referer=self.host + "/cn")
            inner = fetched["text"] or ""
            m3 = M3U8_QUOTED_RE.search(inner)
            if m3:
                return {"parse": 0, "url": m3.group(1).replace("\\/", "/"), "header": {"User-Agent": UA, "Referer": raw_url}}
            for mm in MP4_QUOTED_RE.finditer(inner):
                u = mm.group(1)
                if not re.search(r"sample|preview|trailer", u, re.I):
                    return {"parse": 0, "url": u.replace("\\/", "/"), "header": {"User-Agent": UA, "Referer": raw_url}}
            em = EMBED_ID_RE.match(raw_url)
            if em:
                try:
                    q = (raw_url[raw_url.index("?"):] + "&") if "?" in raw_url else "?"
                    api = self._fetch(em.group(1) + "/stream" + q + "id=" + em.group(2), referer=raw_url)
                    data = json.loads(api["text"] or "{}")
                    stream = ""
                    if isinstance(data, dict):
                        media = data.get("media")
                        if isinstance(media, dict):
                            stream = str(media.get("stream") or "")
                    if stream:
                        return {"parse": 0, "url": stream.replace("\\/", "/"), "header": {"User-Agent": UA, "Referer": raw_url}}
                except Exception:
                    pass
        return {"parse": 1, "url": raw_url, "header": headers}

    # ---------- helpers ----------

    def _slug_row(self, name, default_label, pairs):
        values = [{"n": default_label, "v": ""}]
        for v, n in pairs:
            values.append({"n": n, "v": v})
        return {"key": "slug", "name": name, "init": "", "value": values}

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

    def _brand_block(self):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：🦋 蝴蝶影视",
            "当前主站：" + self.host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def _summary(self, vod_name, genres, code, related):
        parts = [self._brand_block()]
        parts.append("标题：" + str(vod_name or ""))
        parts.append("分类：" + "、".join(genres))
        parts.append("片源：" + LINE_NAME)
        parts.append("编号：" + str(code or ""))
        if related:
            titles = [item["title"] for item in related[:6]]
            parts.append("相关推荐：" + "、".join(titles))
        return "\n".join(parts)

    def _main_html(self, html):
        s = str(html or "")
        for kw in ("</header>", "</nav>", "<main", 'class="content"', 'class="grid"'):
            p = s.find(kw)
            if p != -1:
                return s[p:]
        return s

    def _parse_cards(self, html):
        if not html:
            return []
        main = self._main_html(html)
        chunks = main.split('class="card"')
        if len(chunks) <= 1:
            chunks = main.split('class="card ')
        items = []
        seen = set()
        for chunk in chunks[1:]:
            lm = LINK_RE.search(chunk)
            if not lm:
                continue
            vid = lm.group(1).strip()
            if vid in seen:
                continue
            seen.add(vid)
            name = ""
            tm = TITLE_RE.search(chunk)
            if tm:
                name = _strip_tags(tm.group(1)).strip()
            if not name or name == "观看":
                nm = NEXT_A_RE.search(chunk)
                if nm:
                    name = _strip_tags(nm.group(1)).strip()
            if not name or name == "观看":
                name = vid.split("/")[-1].upper()
            picm = IMG_RE.search(chunk)
            pic = picm.group(1).strip() if picm else ""
            dm = DUR_RE.search(chunk)
            dur = dm.group(1).strip() if dm else ""
            remarks = ("蝴蝶影视 · " + dur) if (dur and dur != "0:00") else "蝴蝶影视"
            items.append(
                {
                    "vod_id": vid,
                    "vod_name": _unescape_html(name),
                    "vod_pic": pic,
                    "vod_remarks": remarks,
                    "style": {"type": "rect", "ratio": PIC_RATIO},
                }
            )
        return items

    def _detail_episodes(self, html):
        episodes = []
        pj = PLAYER_RE.search(html)
        if pj:
            try:
                raw = pj.group(1)
                raw = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), raw)
                raw = raw.replace("\\/", "/").replace("\\'", "'")
                eps = json.loads(raw)
                if isinstance(eps, list):
                    for ep in eps:
                        if not isinstance(ep, dict):
                            continue
                        ep_name = str(ep.get("name") or "正片").replace("$", "").replace("#", "").strip() or "正片"
                        ep_url = _clean_stream_url(str(ep.get("url") or "").strip())
                        if ep_url:
                            episodes.append({"name": ep_name, "url": ep_url})
            except Exception:
                episodes = []
        if not episodes:
            for i, mm in enumerate(QUOTED_STREAM_RE.finditer(html)):
                u = _clean_stream_url(mm.group(1))
                if u:
                    episodes.append({"name": "线路 " + str(i + 1), "url": u})
        return episodes

    def _parse_related(self, html, self_id):
        items = []
        seen = set()
        for vm in VSIDE_RE.finditer(html):
            vid = vm.group(1).strip()
            if vid == self_id or vid in seen:
                continue
            seen.add(vid)
            body = vm.group(2)
            tm = VSIDE_TITLE_RE.search(body)
            title = _strip_tags(tm.group(1)).strip() if tm else ""
            if not title:
                title = vid.split("/")[-1].upper()
            items.append({"id": vid, "title": _unescape_html(title)})
        return items

    def _resolve_related(self, vid):
        path = "/" + str(vid).lstrip("/")
        fetched = self._fetch(path)
        html = fetched["text"]
        if html:
            episodes = self._detail_episodes(html)
            if episodes:
                env = json.dumps({"playUrl": episodes[0]["url"]}, ensure_ascii=False)
                return self.playerContent(RELATED_NAME, env, [])
        target = fetched["final_url"] or (self.host + path)
        return {"parse": 1, "url": target, "header": {"User-Agent": UA, "Referer": self.host + "/cn"}}

    # ---------- network ----------

    def _full_url(self, target, host):
        t = str(target or "")
        if t.startswith("//"):
            return "https:" + t
        if t.startswith("/"):
            return host + t
        return t

    def _fetch_once(self, target, referer, host, timeout):
        url = self._full_url(target, host)
        headers = {
            "User-Agent": UA,
            "Referer": referer or (host + "/cn"),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        resp = requests.get(url, headers=headers, timeout=timeout)
        return {"text": resp.text or "", "status": resp.status_code, "final_url": resp.url or url}

    def _fetch(self, target, referer=""):
        host = self.host
        try:
            res = self._fetch_once(target, referer, host, 8)
            if res["status"] >= 400:
                raise Exception("http " + str(res["status"]))
            res["host"] = host
            return res
        except Exception:
            if not self._custom_host:
                winner = self._pick_fastest_host()
                if winner and winner != host:
                    self.host = winner
                    try:
                        res = self._fetch_once(target, referer, winner, 8)
                        res["host"] = winner
                        return res
                    except Exception:
                        pass
            return {"text": "", "status": 0, "final_url": self._full_url(target, host), "host": host}

    def _fetch_text(self, target, referer=""):
        return self._fetch(target, referer)["text"]

    def _extract_nav_hosts(self, html_text):
        for m in B64_RE.finditer(str(html_text or "")):
            raw_b64 = m.group(1)
            try:
                decoded = base64.b64decode(raw_b64).decode("utf-8")
                unquoted = unquote(decoded)
                if "[" in unquoted and "{" in unquoted and SITE_NAME.lower() in unquoted.lower():
                    site_list = json.loads(unquoted)
                    if isinstance(site_list, list):
                        for item in site_list:
                            if not isinstance(item, dict):
                                continue
                            nm = str(item.get("name") or "").strip()
                            desc = str(item.get("desc") or item.get("description") or "")
                            if SITE_NAME.lower() in nm.lower() or SITE_NAME.lower() in desc.lower():
                                hosts = []
                                if item.get("url"):
                                    om = ORIGIN_RE.match(str(item["url"]))
                                    if om:
                                        hosts.append(om.group(1))
                                urls = item.get("urls")
                                if isinstance(urls, list):
                                    for uo in urls:
                                        if isinstance(uo, dict) and uo.get("url"):
                                            om = ORIGIN_RE.match(str(uo["url"]))
                                            if om and om.group(1) not in hosts:
                                                hosts.append(om.group(1))
                                if hosts:
                                    return hosts
            except Exception:
                continue
        return None

    def _fetch_nav_hosts(self):
        headers = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        }
        for nav in NAV_URLS:
            try:
                resp = requests.get(nav, headers=headers, timeout=6)
                hosts = self._extract_nav_hosts(resp.text or "")
                if hosts:
                    return hosts
            except Exception:
                continue
        return None

    def _probe_host(self, host):
        try:
            resp = requests.get(
                host + "/cn",
                headers={"User-Agent": UA, "Referer": host + "/"},
                timeout=5,
            )
            body = resp.text or ""
            if 200 <= resp.status_code < 400 and len(body) > 200:
                return host
        except Exception:
            pass
        return None

    def _pick_fastest_host(self):
        nav_hosts = self._fetch_nav_hosts() or []
        candidates = []
        for h in list(nav_hosts) + [DEFAULT_HOST]:
            hh = str(h or "").strip().rstrip("/")
            if hh and hh.startswith("http") and hh not in candidates:
                candidates.append(hh)
        for cand in candidates[:10]:
            ok = self._probe_host(cand)
            if ok:
                self._discovered = True
                return ok
        return None

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249397746&sig=41bdbd85ddcf6edd
