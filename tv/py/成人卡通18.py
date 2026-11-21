# -*- coding: utf-8 -*-
# 成人卡通 - FongMi/TVBox Python spider, converted from the Hamo JS plugin (com.butterfly.cartoonporno)
import base64
import json
import re
from urllib.parse import quote, unquote

import requests

from base.spider import Spider as BaseSpider

DEFAULT_HOST = "https://www.cartoonporno.cc"
NAV_URLS = ["https://x99dh.cc", "https://x99dh.one", "https://x99dh.net", "https://x99dh.lat"]
MIRROR_POOL = ["https://www.cartoonporno.cc", "https://cartoonporno.cc"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
BRAND_ACTOR = "🦋 TG群: @tvshare23"
BRAND_DIRECTOR = "🦋 蝴蝶影视"
BRAND_NAME = "蝴蝶影视"
SITE_NAME = "成人卡通"
LINE_NAME = "🦋 蝴蝶专线"
PAGE_SIZE = 50

SECTION_DEFS = [
    ("videos", "全部视频", "全量746个分类", "全部"),
    ("sec_3d", "3D精选", "3D及CG分类", "全部3D"),
    ("sec_anime", "二次元动漫", "动漫二次元分类", "全部动漫"),
    ("sec_char", "同人角色", "专属同人角色", "全部同人角色"),
    ("sec_physique", "体态风情", "体貌特征分类", "全部体态"),
    ("sec_roleplay", "角色扮演", "职业角色分类", "全部角色扮演"),
    ("sec_scenes", "情境玩法", "情境与玩法分类", "全部情境玩法"),
]

SECTION_DEFAULT_ROUTE = {
    "videos": "videos",
    "sec_3d": "categories/217/3d",
    "sec_anime": "categories/231/anime",
    "sec_char": "categories/117/tifa-lockhart",
    "sec_physique": "categories/268/big-tits",
    "sec_roleplay": "categories/730/uniform",
    "sec_scenes": "categories/679/storyline",
}

KW_3D = ["3d", "sfm", "blender", "overwatch", "resident-evil", "final-fantasy", "dead-or-alive", "nier", "zelda", "fortnite", "league-of-legends", "warcraft", "sims"]
KW_ANIME = ["hentai", "anime", "manga", "dragon-ball", "naruto", "one-piece", "bleach", "demon-slayer", "one-punch-man", "pokemon", "dxd", "sao", "azur-lane", "kill-la-kill"]
KW_CHAR = ["tifa", "android-18", "nami", "ahri", "hinata", "yorha", "sakura", "d.va", "lara", "ada-wong", "jill", "tsunade", "zero-two", "nezuko", "wonder-woman", "harley", "bulma", "asuna", "aerith", "samus", "yennefer", "ciri", "bowsette", "raven", "mercy", "shinobu", "sombra", "atago", "corrin"]
KW_PHYSIQUE = ["petite", "tits", "ass", "legs", "cock", "pussy", "bbw", "thick", "skinny", "fat", "brunette", "blonde", "redhead", "shaved", "hairy", "big-", "small-", "tall", "muscular"]
KW_ROLEPLAY = ["uniform", "student", "maid", "nurse", "teacher", "secretary", "stewardess", "police", "bunny", "housewife", "stepmom", "milf", "nun", "model", "babysitter", "doctor", "slave", "costume"]

ALL_CATS = [
    ("3D性感", "categories/217/3d"),
    ("动漫色情", "categories/447/hentai"),
    ("娇小性感", "categories/583/petite"),
    ("3D卡通诱惑", "categories/218/3d-cartoon"),
    ("扶她激情", "categories/407/futanari"),
    ("浴缸暧昧", "categories/250/bath"),
    ("无码直击", "categories/725/uncensored"),
    ("欲火焚身", "categories/458/horny"),
    ("老爹角色", "categories/352/daddy"),
    ("漫画风情", "categories/197/manga"),
    ("动漫诱惑", "categories/231/anime"),
    ("处女初体验", "categories/739/virgin"),
    ("叔叔禁忌", "categories/726/uncle"),
    ("制服诱惑", "categories/730/uniform"),
    ("捆绑调教", "categories/254/bdsm"),
    ("Angels", "categories/183/angels"),
    ("精灵宝可梦", "categories/94/pokemon"),
    ("疯狂性爱", "categories/337/crazy"),
    ("迪士尼风", "categories/33/disney"),
    ("青春少女", "categories/700/teen"),
    ("丝袜诱惑", "categories/678/stockings"),
    ("学生妹子", "categories/684/student"),
    ("可爱小骚", "categories/222/adorable"),
    ("手动快感", "categories/444/handjob"),
    ("奴隶调教", "categories/658/slave"),
    ("巨屌猛男", "categories/266/big-cock"),
    ("Giants", "categories/170/giants"),
    ("大屌", "categories/321/cock"),
    ("病人角色", "categories/579/patient"),
    ("小穴", "categories/605/pussy"),
    ("孕妇", "categories/595/pregnant"),
    ("群交狂欢", "categories/569/orgy"),
    ("毛绒性癖", "categories/406/furry"),
    ("后庭猛插", "categories/235/assfucking"),
    ("肥胖身材", "categories/384/fat"),
    ("非亲妹妹", "categories/549/not-sister"),
    ("青春肉体", "categories/761/young"),
    ("巨乳诱惑", "categories/268/big-tits"),
    ("Animations", "categories/185/animations"),
    ("亚洲风情", "categories/233/asian"),
    ("双重插入", "categories/365/double-penetration"),
    ("家庭乱伦", "categories/5/family"),
    ("性爱游戏", "categories/409/game"),
    ("舔屁眼", "categories/620/rimjob"),
    ("修长美腿", "categories/493/legs"),
    ("继母诱惑", "categories/13/stepmom"),
    ("可爱妹子", "categories/351/cute"),
    ("成熟风韵", "categories/514/mature"),
    ("丰满胸部", "categories/708/tits"),
    ("口交快感", "categories/276/blowjob"),
    ("体内射精", "categories/338/creampie"),
    ("性感妈咪", "categories/530/mommy"),
    ("生化危机", "categories/46/resident-evil"),
    ("性感诱惑", "categories/643/sexy"),
    ("激烈做爱", "categories/404/fucking"),
    ("非亲儿子", "categories/550/not-son"),
    ("奶奶风韵", "categories/431/grandmother"),
    ("绝色美女", "categories/257/beautiful"),
    ("家庭主妇", "categories/461/housewife"),
    ("舔弄快感", "categories/496/lick"),
    ("老男人魅力", "categories/563/old-man"),
    ("激烈硬核", "categories/445/hardcore"),
    ("老奶奶欲", "categories/432/granny"),
    ("禁忌刺激", "categories/692/taboo"),
    ("后门快感", "categories/229/anal"),
    ("情人激情", "categories/503/lover"),
    ("赤裸诱惑", "categories/538/naked"),
    ("学生妹", "categories/632/schoolgirl"),
    ("粗暴干法", "categories/624/rough"),
    ("医生扮演", "categories/361/doctor"),
    ("医院情欲", "categories/459/hospital"),
    ("自制激情", "categories/454/homemade"),
    ("34号规则", "categories/69/rule-34"),
    ("满口快感", "categories/533/mouthful"),
    ("性感熟女", "categories/519/milf"),
    ("激情四射", "categories/578/passionate"),
    ("淫水直流", "categories/370/dripping"),
    ("户外野性", "categories/571/outdoor"),
    ("紧致身材", "categories/706/tight"),
    ("第一次体验", "categories/391/first-time"),
    ("哥特风情", "categories/429/goth"),
    ("朋友开房", "categories/403/friend"),
    ("美胸晃动", "categories/282/boobs"),
    ("酒店私密", "categories/460/hotel"),
    ("健身性爱", "categories/394/fitness"),
    ("圣诞性感", "categories/309/christmas"),
    ("震动快感", "categories/737/vibrator"),
    ("偷窥刺激", "categories/740/voyeur"),
    ("One Piece", "categories/162/one-piece"),
    ("娇小胸部", "categories/663/small-tits"),
    ("老板调戏", "categories/285/boss"),
    ("健身房欲", "categories/435/gym"),
    ("乳汁喷射", "categories/521/milk"),
    ("气球性感", "categories/245/balloon"),
    ("警察制服", "categories/589/police"),
    ("老师诱惑", "categories/699/teacher"),
    ("露肉挑逗", "categories/395/flashing"),
    ("潮吹高潮", "categories/676/squirting"),
    ("成熟女士", "categories/486/lady"),
    ("短裙撩人", "categories/656/skirt"),
    ("纹身诱惑", "categories/697/tattoo"),
    ("液体狂欢", "categories/499/liquid-lunch"),
    ("热吻缠绵", "categories/483/kissing"),
    ("渔网装诱惑", "categories/392/fishnets"),
    ("私人空间", "categories/599/private"),
    ("多汁诱人", "categories/479/juicy"),
    ("短发辣妹", "categories/647/short-hair"),
    ("丰满身材", "categories/350/curvy"),
    ("劳拉·克劳馥", "categories/29/lara-croft"),
    ("两女一男", "categories/388/ffm"),
    ("全裸诱惑", "categories/551/nude"),
    ("换妻狂欢", "categories/690/swingers"),
    ("完整影片", "categories/405/full-movie"),
    ("湿滑小穴", "categories/747/wet-pussy"),
    ("私处特写", "categories/258/beaver"),
    ("新娘诱惑", "categories/290/bride"),
    ("打屁股戏", "categories/671/spanking"),
    ("色情诱惑", "categories/376/erotic"),
    ("射精", "categories/343/cum"),
    ("人妖风情", "categories/718/transsexual"),
    ("面部射精", "categories/381/facial"),
    ("私处特写", "categories/736/vagina"),
    ("角色扮演", "categories/621/roleplay"),
    ("大臀翘臀", "categories/263/big-ass"),
    ("口交窒息", "categories/408/gagging"),
    ("紧窄小穴", "categories/707/tight-pussy"),
    ("现场秀", "categories/10/show"),
    ("偷窥", "categories/743/watching"),
    ("捆绑束缚", "categories/280/bondage"),
    ("性爱机器", "categories/505/machine"),
    ("宝贝性感", "categories/242/babe"),
    ("熟女猎手", "categories/332/cougar"),
    ("黑人辣妹", "categories/274/black"),
    ("Demons", "categories/180/demons"),
    ("顺从调戏", "categories/687/submissive"),
    ("沙滩风情", "categories/255/beach"),
    ("极端玩法", "categories/380/extreme"),
    ("怪物奇趣", "categories/531/monster"),
    ("婚礼性爱", "categories/745/wedding"),
    ("Fictional Characters", "categories/174/fictional-characters"),
    ("假阳具戏", "categories/680/strapon"),
    ("女主支配", "categories/386/femdom"),
    ("泳池激情", "categories/591/pool"),
    ("色情明星", "categories/592/pornstar"),
    ("侧身热辣", "categories/651/sideways"),
    ("纤细腰肢", "categories/664/small-waist"),
    ("精选合集", "categories/329/compilation"),
    ("吞精诱惑", "categories/689/swallow"),
    ("邻家女孩", "categories/419/girl-next-door"),
    ("伪娘诱惑", "categories/206/femboy"),
    ("女同性恋", "categories/494/lesbian"),
    ("眼镜诱惑", "categories/423/glasses"),
    ("自慰高潮", "categories/513/masturbation"),
    ("纤瘦尤物", "categories/655/skinny"),
    ("绿帽癖", "categories/341/cuckold"),
    ("老熟风韵", "categories/561/old"),
    ("群交狂欢", "categories/410/gangbang"),
    ("黑肤辣妹", "categories/372/ebony"),
    ("偷情", "categories/305/cheating"),
    ("人妻", "categories/751/wife"),
    ("意外性爱", "categories/221/accident"),
    ("人妖魅惑", "categories/487/ladyboy"),
    ("自慰快感", "categories/476/jerking-off"),
    ("比基尼性感", "categories/270/bikini"),
    ("人妖魅惑", "categories/646/shemale"),
    ("日本风情", "categories/474/japanese"),
    ("搞笑模仿", "categories/576/parody"),
    ("翘臀诱惑", "categories/234/ass"),
    ("高潮爆发", "categories/568/orgasm"),
    ("淘气挑逗", "categories/542/naughty"),
    ("大学风骚", "categories/324/college"),
    ("跨种族激情", "categories/470/interracial"),
    ("公共场所", "categories/601/public"),
    ("巨根震撼", "categories/532/monster-cock"),
    ("羞辱快感", "categories/463/humiliation"),
    ("伪娘", "categories/3/sissy"),
    ("后入式", "categories/362/doggystyle"),
    ("老少配对", "categories/562/old-and-young"),
    ("机器人性爱", "categories/19/robot"),
    ("异装癖", "categories/339/crossdressing"),
    ("模拟人生", "categories/23/sims"),
    ("张开诱惑", "categories/411/gaping"),
    ("漫画风", "categories/327/comic"),
    ("深喉口交", "categories/354/deepthroat"),
    ("窒息快感", "categories/308/choking"),
    ("黑人大屌", "categories/264/big-black-cock"),
    ("修女禁忌", "categories/553/nun"),
    ("精灵诱惑", "categories/192/elf"),
    ("传教士体位", "categories/524/missionary"),
    ("森林野战", "categories/402/forest"),
    ("情趣玩具", "categories/716/toys"),
    ("复古风情", "categories/616/retro"),
    ("内射阴道", "categories/345/cum-in-pussy"),
    ("口交快感", "categories/567/oral"),
    ("男同热恋", "categories/414/gay"),
    ("源代码动画", "categories/68/sfm"),
    ("拳交", "categories/393/fisting"),
    ("外星人奇遇", "categories/225/alien"),
    ("口交快感", "categories/688/sucking"),
    ("感官享受", "categories/640/sensual"),
    ("手指插入", "categories/390/fingering"),
    ("呻吟销魂", "categories/527/moaning"),
    ("纯真诱惑", "categories/466/innocent"),
    ("黑发辣妹", "categories/291/brunette"),
    ("性感女仆", "categories/506/maid"),
    ("复古情色", "categories/738/vintage"),
    ("性感装扮", "categories/572/outfit"),
    ("邻居诱惑", "categories/544/neighbors"),
    ("红发辣妹", "categories/613/redhead"),
    ("多毛诱惑", "categories/441/hairy"),
    ("保姆诱惑", "categories/243/babysitter"),
    ("美国老爸", "categories/21/american-dad"),
    ("第一人称视角", "categories/594/pov"),
    ("多人狂欢", "categories/434/group"),
    ("乡村野战", "categories/333/country"),
    ("色情按摩", "categories/510/massage"),
    ("圆润翘臀", "categories/293/bubble-butt"),
    ("性幻想", "categories/382/fantasy"),
    ("一对一", "categories/11/1on1"),
    ("变态玩法", "categories/482/kinky"),
    ("多人颜射", "categories/294/bukkake"),
    ("水族性感", "categories/26/aqua"),
    ("巨大震撼", "categories/462/huge"),
    ("书呆子性感", "categories/545/nerd"),
    ("护士诱惑", "categories/554/nurse"),
    ("双性恋混战", "categories/273/bisexual"),
    ("乳头挑逗", "categories/547/nipples"),
    ("双人玩法", "categories/364/double"),
    ("已婚偷情", "categories/508/married"),
    ("分享激情", "categories/644/share"),
    ("支配调教", "categories/363/domination"),
    ("浪漫氛围", "categories/622/romantic"),
    ("指导调教", "categories/468/instruction"),
    ("放荡骚货", "categories/661/slut"),
    ("凌乱狂野", "categories/660/sloppy"),
    ("舔阴", "categories/348/cunilingus"),
    ("湿润诱惑", "categories/746/wet"),
    ("丰满尤物", "categories/253/bbw"),
    ("骑乘快感", "categories/619/riding"),
    ("真实体验", "categories/612/reality"),
    ("太空激情", "categories/54/space"),
    ("独秀自慰", "categories/669/solo"),
    ("乳交快感", "categories/709/titty-fuck"),
    ("女上位", "categories/336/cowgirl"),
    ("阴唇特写", "categories/606/pussy-lips"),
    ("足部恋", "categories/385/feet"),
    ("迷你短裙", "categories/522/miniskirt"),
    ("节日狂欢", "categories/452/holiday"),
    ("性工作者", "categories/600/prostitute"),
    ("胸上射精", "categories/347/cum-on-tits"),
    ("内裤诱惑", "categories/574/panties"),
    ("特殊癖好", "categories/387/fetish"),
    ("办公室激情", "categories/559/office"),
    ("舔阴狂热", "categories/534/muff-diving"),
    ("老公偷情", "categories/465/husband"),
    ("脸上射精", "categories/346/cum-on-face"),
    ("车震", "categories/299/car"),
    ("古铜肌肤", "categories/695/tanned"),
    ("尖叫高潮", "categories/635/screaming"),
    ("光滑无毛", "categories/645/shaved"),
    ("暗室口交", "categories/424/gloryhole"),
    ("尼龙性感", "categories/556/nylon"),
    ("全能戏剧", "categories/76/total-drama"),
    ("拉伸挑逗", "categories/682/stretching"),
    ("乳胶紧身", "categories/489/latex"),
    ("菊花紧致", "categories/236/asshole"),
    ("沐浴性感", "categories/251/bathing"),
    ("性感内衣", "categories/497/lingerie"),
    ("男友偷欢", "categories/288/boyfriend"),
    ("漂亮妹子", "categories/596/pretty"),
    ("拍打刺激", "categories/657/slap"),
    ("大胸妹", "categories/1/oppai"),
    ("连裤袜性感", "categories/575/pantyhose"),
    ("厕所偷情", "categories/711/toilet"),
    ("龙珠", "categories/52/dragon-ball"),
    ("快速干炮", "categories/608/quickie"),
    ("监狱风", "categories/598/prison"),
    ("天然美胸", "categories/540/natural-tits"),
    ("春野樱", "categories/125/sakura-haruno"),
    ("角色扮演", "categories/331/costumes"),
    ("街头激情", "categories/681/street"),
    ("丰满阴部", "categories/267/big-pussy"),
    ("肌肉猛男", "categories/535/muscular"),
    ("教室激情", "categories/316/classroom"),
    ("勾引挑逗", "categories/637/seduction"),
    ("臀部游戏", "categories/237/assplay"),
    ("厨房激情", "categories/484/kitchen"),
    ("派对狂热", "categories/577/party"),
    ("透视诱惑", "categories/638/see-through"),
    ("女生接吻", "categories/421/girls-kissing"),
    ("农场激情", "categories/610/ranch"),
    ("守望先锋", "categories/44/overwatch"),
    ("上班偷欢", "categories/240/at-work"),
    ("假阳具", "categories/358/dildo"),
    ("自慰指导", "categories/477/jerk-off-instructions"),
    ("情侣性爱", "categories/334/couple"),
    ("小公主", "categories/597/princess"),
    ("男男热恋", "categories/204/yaoi"),
    ("风骚婊子", "categories/750/whore"),
    ("搅拌机动画", "categories/67/blender-animation"),
    ("床上缠绵", "categories/259/bed"),
    ("内衣诱惑", "categories/728/underwear"),
    ("League of Legends", "categories/164/league-of-legends"),
    ("张开诱惑", "categories/674/spreading"),
    ("丰满肉感", "categories/208/thick"),
    ("紧身裤诱惑", "categories/492/leggings"),
    ("秘书诱惑", "categories/636/secretary"),
    ("运动型男", "categories/239/athletic"),
    ("万圣节欲", "categories/442/halloween"),
    ("放屁癖", "categories/383/farting"),
    ("Heroes", "categories/158/heroes"),
    ("拉丁辣妹", "categories/490/latina"),
    ("DC漫画", "categories/40/dc-comics"),
    ("卧室激情", "categories/260/bedroom"),
    ("软色挑逗", "categories/668/softcore"),
    ("高跟性感", "categories/446/heels"),
    ("敏感小豆", "categories/317/clit"),
    ("性爱打斗", "categories/389/fight"),
    ("瑜伽性爱", "categories/760/yoga"),
    ("完美身材", "categories/581/perfect-body"),
    ("前戏挑逗", "categories/401/foreplay"),
    ("情绪化妹子", "categories/374/emo"),
    ("小腹诱惑", "categories/262/belly"),
    ("无毛诱惑", "categories/438/hairless"),
    ("舌头挑逗", "categories/712/tongue"),
    ("Marvel", "categories/161/marvel"),
    ("饱满诱惑", "categories/602/puffy"),
    ("最终幻想", "categories/66/final-fantasy"),
    ("下垂奶子", "categories/627/saggy-tits"),
    ("食物性戏", "categories/399/food"),
    ("女友私密", "categories/417/girlfriend"),
    ("捆绑快感", "categories/705/tied-up"),
    ("火影激情", "categories/198/naruto"),
    ("偷窥刺激", "categories/675/spying"),
    ("小巧阳具", "categories/662/small-cock"),
    ("Succubus", "categories/179/succubus"),
    ("Villains", "categories/167/villains"),
    ("男主支配", "categories/507/maledom"),
    ("浴室偷情", "categories/252/bathroom"),
    ("死或生", "categories/50/dead-or-alive"),
    ("D.Va", "categories/124/d.va"),
    ("脱衣诱惑", "categories/683/striptease"),
    ("蒂法·洛克哈特", "categories/117/tifa-lockhart"),
    ("女女激情", "categories/420/girl-on-girl"),
    ("传奇故事", "categories/70/legend"),
    ("性感模特", "categories/528/model"),
    ("被骗上床", "categories/720/tricked"),
    ("访谈挑逗", "categories/471/interview"),
    ("女王驾到", "categories/202/queen"),
    ("金发尤物", "categories/275/blonde"),
    ("大嘴骚货", "categories/4/big-mouth"),
    ("抖臀挑逗", "categories/238/ass-shaking"),
    ("牛仔热辣", "categories/475/jeans"),
    ("高个子", "categories/693/tall"),
    ("阳具挑逗", "categories/580/penis"),
    ("健身性爱", "categories/752/workout"),
    ("乳头穿孔", "categories/585/pierced-nipples"),
    ("身体穿孔", "categories/586/piercing"),
    ("神奇女侠", "categories/31/wonder-woman"),
    ("安全套play", "categories/330/condom"),
    ("粪便癖好", "categories/211/scat"),
    ("害羞挑逗", "categories/649/shy"),
    ("网络摄像头", "categories/744/webcam"),
    ("丰满肉感", "categories/310/chubby"),
    ("偷拍刺激", "categories/448/hidden"),
    ("七大罪", "categories/88/seven-deadly-sins"),
    ("娜美", "categories/128/nami"),
    ("热舞诱惑", "categories/353/dancing"),
    ("柔体性感", "categories/397/flexible"),
    ("性瘾狂热", "categories/557/nympho"),
    ("手铐诱惑", "categories/443/handcuffs"),
    ("鞭打调教", "categories/749/whipping"),
    ("兔女郎", "categories/295/bunny"),
    ("阿狸", "categories/126/ahri"),
    ("日向雏田", "categories/131/hinata-hyuga"),
    ("淫荡刺激", "categories/539/nasty"),
    ("香蕉挑逗", "categories/246/banana"),
    ("黄瓜自慰", "categories/342/cucumber"),
    ("修剪私处", "categories/721/trimmed-pussy"),
    ("被剥削", "categories/379/exploited"),
    ("69互玩", "categories/219/69"),
    ("性爱竞赛", "categories/328/competition"),
    ("猛男干将", "categories/195/fuckerman"),
    ("塞尔达传说", "categories/71/the-legend-of-zelda"),
    ("超级马里奥", "categories/84/super-mario"),
    ("情妇调教", "categories/525/mistress"),
    ("南方公园", "categories/22/south-park"),
    ("兽人狂热", "categories/14/orcs"),
    ("意外暴露", "categories/566/oops"),
    ("走错洞了", "categories/756/wrong-hole"),
    ("天使", "categories/136/mercy"),
    ("抖奶诱惑", "categories/287/bouncing-boobs"),
    ("星球大战", "categories/38/star-wars"),
    ("蒙面刺激", "categories/509/masked"),
    ("我的英雄学院", "categories/73/my-hero-academia"),
    ("The Incredibles", "categories/177/the-incredibles"),
    ("另类玩法", "categories/227/alternative"),
    ("人妖诱惑", "categories/9/trap"),
    ("碧蓝航线", "categories/60/azur-lane"),
    ("射精高潮", "categories/478/jizz"),
    ("强迫play", "categories/7/forced"),
    ("亲爱的弗兰克斯", "categories/48/darling-in-the-franxx"),
    ("零二", "categories/132/zero-two"),
    ("Sonic", "categories/176/sonic"),
    ("啦啦队长", "categories/306/cheerleader"),
    ("长发诱惑", "categories/500/long-hair"),
    ("名人色情", "categories/36/famous"),
    ("性感女神", "categories/426/goddess"),
    ("按摩浴缸", "categories/473/jacuzzi"),
    ("Dragons", "categories/182/dragons"),
    ("挺翘诱人", "categories/582/perky"),
    ("互动性爱", "categories/469/interactive"),
    ("这个美好的世界", "categories/62/konosuba"),
    ("少年泰坦", "categories/80/teen-titans"),
    ("游艇激情", "categories/759/yacht"),
    ("女尊男卑", "categories/302/cfnm"),
    ("雨中狂热", "categories/55/rain"),
    ("放松一下", "categories/614/relax"),
    ("粗暴性爱", "categories/292/brutal"),
    ("猛烈抽插", "categories/369/drilled"),
    ("裙底风光", "categories/734/upskirt"),
    ("入室盗贼", "categories/296/burglar"),
    ("体操性感", "categories/436/gymnast"),
    ("木乃伊性感", "categories/12/mummy"),
    ("交叉磨蹭", "categories/633/scissoring"),
    ("捆绑包裹", "categories/753/wrapped-bondage"),
    ("少年骇客", "categories/77/ben-10"),
    ("沙滩野战", "categories/256/beach-sex"),
    ("一拳超人", "categories/81/one-punch-man"),
    ("龙卷（恐怖龙卷）", "categories/112/tatsumaki-(tornado-of-terror)"),
    ("银河战士", "categories/61/metroid"),
    ("月下狂欢", "categories/200/moon"),
    ("傻白甜骚货", "categories/271/bimbo"),
    ("两男一女", "categories/526/mmf"),
    ("丧尸激情", "categories/16/zombie"),
    ("Death", "categories/172/death"),
    ("镜前激情", "categories/523/mirror"),
    ("水手装诱惑", "categories/628/sailor"),
    ("主人调教", "categories/512/master"),
    ("街头勾引", "categories/456/hooker"),
    ("走运艳遇", "categories/504/lucky"),
    ("脱衣挑逗", "categories/729/undressing"),
    ("刀剑神域", "categories/64/sword-art-online-(sao)"),
    ("臣服快感", "categories/686/submission"),
    ("涂油滑腻", "categories/560/oiled"),
    ("出租车激情", "categories/698/taxi"),
    ("布尔玛", "categories/138/bulma"),
    ("自然野性", "categories/541/nature"),
    ("丁字裤诱惑", "categories/704/thong"),
    ("摔跤性爱", "categories/754/wrestling"),
    ("火焰纹章", "categories/86/fire-emblem"),
    ("惊艳性感", "categories/228/amazing"),
    ("名人艳照", "categories/301/celebrity"),
    ("死神", "categories/85/bleach"),
    ("运动热辣", "categories/673/sport"),
    ("摩擦挑逗", "categories/433/grinding"),
    ("大学风骚", "categories/731/university"),
    ("鬼灭之刃", "categories/83/demon-slayer"),
    ("胡蝶忍", "categories/105/shinobu-kocho"),
    ("斯普拉遁", "categories/82/splatoon"),
    ("Griffins", "categories/186/griffins"),
    ("斩服少女", "categories/87/kill-la-kill"),
    ("龙子杀生丸", "categories/99/ryuko-matoi"),
    ("玛丽·萝丝", "categories/135/marie-rose"),
    ("牙套妹子", "categories/289/braces"),
    ("修长玉腿", "categories/501/long-legs"),
    ("影院偷欢", "categories/313/cinema"),
    ("晒痕性感", "categories/694/tan-lines"),
    ("丑女反差", "categories/724/ugly"),
    ("复仇性爱", "categories/617/revenge"),
    ("酒吧激情", "categories/247/bar"),
    ("同学情欲", "categories/315/classmate"),
    ("性感魅力", "categories/422/glamour"),
    ("亲密接触", "categories/472/intimate"),
    ("阿姨风骚", "categories/241/aunt"),
    ("受罚调教", "categories/603/punished"),
    ("X战警", "categories/79/x-men"),
    ("瑞克和莫蒂荒唐", "categories/212/rick-and-morty"),
    ("摆姿势", "categories/593/posing"),
    ("尼尔机械纪元", "categories/45/nier-automata"),
    ("哺乳诱惑", "categories/485/lactating"),
    ("怪诞小镇", "categories/43/gravity-falls"),
    ("正义联盟", "categories/25/justice-league"),
    ("书呆子骚气", "categories/283/bookworm"),
    ("紧身短裤", "categories/648/shorts"),
    ("鲍赛特", "categories/109/bowsette"),
    ("性感裙装", "categories/368/dress"),
    ("祢豆子", "categories/110/nezuko"),
    ("Clowns", "categories/171/clowns"),
    ("小丑扮演", "categories/320/clown"),
    ("醉酒性爱", "categories/371/drunk"),
    ("瑞雯", "categories/113/raven"),
    ("堡垒之夜", "categories/65/fortnite"),
    ("野狼欲望", "categories/216/wolf"),
    ("沙漠热浪", "categories/59/sand"),
    ("老女人风情", "categories/564/old-woman"),
    ("东方风情", "categories/570/oriental"),
    ("Family Guy", "categories/152/family-guy"),
    ("意外翻车", "categories/427/goes-wrong"),
    ("列车激情", "categories/717/train"),
    ("兽人狂野", "categories/205/yiff"),
    ("Erza Scarlet", "categories/143/erza-scarlet"),
    ("肿胀私处", "categories/691/swollen-pussy"),
    ("史酷比风", "categories/6/scooby-doo"),
    ("阿卡丽KDA", "categories/107/akali-kda"),
    ("超人幻想", "categories/17/superman"),
    ("Avengers", "categories/165/avengers"),
    ("异国风情", "categories/400/foreign"),
    ("手套性感", "categories/425/gloves"),
    ("自舔快感", "categories/639/self-sucking"),
    ("磨豆腐快感", "categories/719/tribbing"),
    ("熟睡偷窥", "categories/659/sleeping"),
    ("双胞胎诱惑", "categories/723/twins"),
    ("瓶子挑逗", "categories/286/bottle"),
    ("阳光下的刺激", "categories/56/sunny"),
    ("萨姆斯·艾兰", "categories/141/samus-aran"),
    ("哈莉奎茵性感", "categories/207/harley-quinn"),
    ("爱丽丝·盖恩斯巴勒", "categories/114/aerith-gainsborough"),
    ("阿凡达风", "categories/39/avatar"),
    ("科拉传奇", "categories/75/korra"),
    ("蝙蝠侠幻想", "categories/30/batman"),
    ("冒险时光", "categories/74/adventure-time"),
    ("克莱尔·雷德菲尔德", "categories/120/claire-redfield"),
    ("红白黑黄", "categories/49/rwby"),
    ("露西·哈特菲莉亚", "categories/106/lucy-heartfilia"),
    ("Fairytale", "categories/173/fairytale"),
    ("头套玩法", "categories/455/hood"),
    ("纲手", "categories/121/tsunade"),
    ("卷发妹", "categories/349/curly"),
    ("Titans", "categories/169/titans"),
    ("Spider Man", "categories/154/spider-man"),
    ("Metal", "categories/189/metal"),
    ("脱衣诱惑", "categories/318/clothes-off"),
    ("黄金雨癖", "categories/428/golden-shower"),
    ("生日狂欢", "categories/272/birthday"),
    ("女上男下", "categories/418/girl-fucks-guy"),
    ("按摩女郎", "categories/511/masseuse"),
    ("长靴诱惑", "categories/284/boots"),
    ("街头搭讪", "categories/584/pickup"),
    ("霞", "categories/137/kasumi"),
    ("Valkyrie", "categories/178/valkyrie"),
    ("超级英雄", "categories/32/superhero"),
    ("结城明日奈", "categories/119/asuna-yuuki"),
    ("裸体主义者", "categories/552/nudist"),
    ("花园性爱", "categories/412/garden"),
    ("Ladybug", "categories/187/ladybug"),
    ("史莱姆诱惑", "categories/58/slime"),
    ("跪地诱惑", "categories/565/on-her-knees"),
    ("巧克力涂身", "categories/307/chocolate"),
    ("表亲禁忌", "categories/335/cousin"),
    ("野兽交", "categories/37/beast"),
    ("吉尔·瓦伦丁", "categories/122/jill-valentine"),
    ("Green Lanterns", "categories/184/green-lanterns"),
    ("哈利波特魔法欲", "categories/203/harry-potter"),
    ("恶魔高校", "categories/63/high-school-dxd"),
    ("Akeno Himejima", "categories/142/akeno-himejima"),
    ("无性爱挑逗", "categories/548/no-sex"),
    ("香黛", "categories/51/shantae"),
    ("笼子play", "categories/298/cage"),
    ("真实感", "categories/2/realistic"),
    ("星火", "categories/98/starfire"),
    ("Superpowers", "categories/153/superpowers"),
    ("真人快打", "categories/35/mortal-combat"),
    ("巨乳幻想", "categories/41/kyonyuu-fantasy"),
    ("性感脚趾", "categories/710/toes"),
    ("皮革性感", "categories/491/leather"),
    ("芭蕾舞女郎", "categories/244/ballerina"),
    ("忍者神龟", "categories/92/turtles-ninja"),
    ("富豪玩法", "categories/618/rich"),
    ("极品少女", "categories/757/xs-girls"),
    ("羞辱玩法", "categories/360/disgrace"),
    ("Pony", "categories/160/pony"),
    ("露比·罗丝", "categories/134/ruby-rose"),
    ("两女一男", "categories/517/mff"),
    ("双马尾萌系", "categories/587/pigtails"),
    ("丑闻曝光", "categories/630/scandal"),
    ("Professor", "categories/150/professor"),
    ("全洞开发", "categories/226/all-holes"),
    ("18号安卓", "categories/116/android-18"),
    ("屋顶激战", "categories/623/rooftop-sex"),
    ("雪地激情", "categories/667/snow"),
    ("凌乱性爱", "categories/516/messy"),
    ("大胸诱惑", "categories/457/hooters"),
    ("丰满大胸", "categories/515/melons"),
    ("湿身T恤", "categories/748/wet-t-shirt"),
    ("上空诱惑", "categories/713/topless"),
    ("独家内容", "categories/377/exclusive"),
    ("纤细美男", "categories/722/twink"),
    ("紧身弹力", "categories/670/spandex"),
    ("超女诱惑", "categories/18/superwoman"),
    ("电梯激情", "categories/373/elevator"),
    ("阿拉伯之夜", "categories/27/arabian-nights"),
    ("马尾俏皮", "categories/590/ponytail"),
    ("多彩性爱", "categories/325/colorful"),
    ("马兽癖", "categories/8/horse"),
    ("兔女郎热舞", "categories/194/rabbit"),
    ("兔子玩具", "categories/609/rabbit-toy"),
    ("军装激情", "categories/232/army"),
    ("Hulk", "categories/156/hulk"),
    ("未来世界", "categories/53/future"),
    ("时尚性感", "categories/685/stylish"),
    ("猛男诱惑", "categories/464/hunk"),
    ("插入刺激", "categories/467/insertion"),
    ("机车辣妹", "categories/269/biker"),
    ("辛普森风", "categories/20/simpsons"),
    ("丰满肉感", "categories/588/plump"),
    ("Deadpool", "categories/151/deadpool"),
    ("淫荡脏污", "categories/359/dirty"),
    ("爷爷性爱", "categories/430/grandfather"),
    ("音乐助兴", "categories/536/music"),
    ("拉头发戏", "categories/439/hair-pulling"),
    ("梦中情人", "categories/367/dream-girl"),
    ("口红诱惑", "categories/498/lipstick"),
    ("赤脚诱惑", "categories/248/barefoot"),
    ("美人鱼诱惑", "categories/28/mermaid"),
    ("橡胶情趣", "categories/625/rubber"),
    ("经典老片", "categories/314/classic"),
    ("尿布癖", "categories/357/diaper"),
    ("艾达·王", "categories/129/ada-wong"),
    ("剧情性爱", "categories/679/storyline"),
    ("自慰快感", "categories/741/wanking"),
    ("游客艳遇", "categories/715/tourist"),
    ("维奥莱特·帕尔", "categories/104/violet-parr"),
    ("狼人狂暴", "categories/215/werewolf"),
    ("怪异刺激", "categories/210/weird"),
    ("井上织姬", "categories/103/orihime-inoue"),
    ("奇幻仙境", "categories/196/wonderland"),
    ("未来家庭", "categories/72/futurama"),
    ("Bender", "categories/145/bender"),
    ("香烟挑逗", "categories/312/cigarette"),
    ("抽烟性感", "categories/665/smoking"),
    ("Evils", "categories/181/evils"),
    ("布莱克·贝拉多娜", "categories/123/blake-belladonna"),
    ("送货小哥", "categories/355/delivery-boy"),
    ("疼痛快感", "categories/573/pain"),
    ("变性美女", "categories/702/tgirl"),
    ("汤姆与杰瑞", "categories/90/tom-and-jerry"),
    ("Universal Pictures", "categories/163/universal-pictures"),
    ("丛林野性", "categories/481/jungle"),
    ("黛米", "categories/118/demi"),
    ("互相自慰", "categories/537/mutual-masturbation"),
    ("公交车", "categories/297/bus"),
    ("黑影", "categories/133/sombra"),
    ("尼尔2B型", "categories/127/yorha-no-2-type-b"),
    ("Philip J Fry", "categories/147/philip-j-fry"),
    ("贫民区风", "categories/415/ghetto"),
    ("船上激情", "categories/277/boat"),
    ("贴身热舞", "categories/488/lap-dance"),
    ("淫荡骚气", "categories/611/raunchy"),
    ("瞳", "categories/115/hitomi"),
    ("Warcraft", "categories/191/warcraft"),
    ("甜蜜糖果", "categories/209/candy"),
    ("摩登原始人", "categories/24/flintstones"),
    ("吊带性感", "categories/413/garter-belt"),
    ("小穴拉伸", "categories/607/pussy-stretching"),
    ("屁股被干爆", "categories/356/destroyed-ass"),
    ("双阴插入", "categories/366/double-vaginal"),
    ("前女友", "categories/378/ex-girlfriend"),
    ("街头流浪", "categories/453/homeless"),
    ("嬉皮风骚", "categories/449/hippy"),
    ("努鲁按摩", "categories/555/nuru-massage"),
    ("教堂禁忌", "categories/311/church"),
    ("性爱告白", "categories/642/sex-confessions"),
    ("猫咪打架", "categories/300/catfight"),
    ("德克斯特", "categories/93/dexter"),
    ("吉普赛风", "categories/437/gypsy"),
    ("娇小身材", "categories/518/midget"),
    ("军装诱惑", "categories/520/military"),
    ("肉棒崇拜", "categories/323/cock-worship"),
    ("愤怒性爱", "categories/230/angry"),
    ("发型性感", "categories/440/hairstyle"),
    ("女主支配", "categories/495/lezdom"),
    ("弓箭手激情", "categories/213/archer"),
    ("Ayane", "categories/144/ayane"),
    ("朋克风", "categories/604/punk"),
    ("衣服撕裂", "categories/319/clothes-ripped"),
    ("真空吸力", "categories/735/vacuum"),
    ("强势猛干", "categories/223/aggressive"),
    ("窒息快感", "categories/666/smother"),
    ("肌肉猛男", "categories/278/bodybuilder"),
    ("空姐制服", "categories/677/stewardess"),
    ("Twisted", "categories/188/twisted"),
    ("抓痕刺激", "categories/634/scratches"),
    ("Guardians of the Galaxy", "categories/166/guardians-of-the-galaxy"),
    ("高雄", "categories/100/takao"),
    ("肥胖诱惑", "categories/558/obese"),
    ("Cosmo Boy", "categories/168/cosmo-boy"),
    ("希尔达", "categories/78/hilda"),
    ("地下室私密", "categories/249/basement"),
    ("Soldiers", "categories/190/soldiers"),
    ("超大尺寸", "categories/758/xxl"),
    ("哭泣快感", "categories/340/crying"),
    ("搞笑性感", "categories/654/silly"),
    ("巫师", "categories/47/the-witcher"),
    ("希里", "categories/130/ciri"),
    ("金·波塞尔", "categories/101/kim-possible"),
    ("Minions", "categories/175/minions"),
    ("缎面性感", "categories/629/satin"),
    ("空中性爱", "categories/398/flight"),
    ("老鼠癖", "categories/34/mouse"),
    ("跳动巨乳", "categories/480/jumping-tits"),
    ("恶魔诱惑", "categories/214/deamons"),
    ("紧张刺激", "categories/546/nervous"),
    ("美少女战士", "categories/201/sailor-moon"),
    ("大恶司女战士猎手", "categories/42/daiakuji-the-xena-buster"),
    ("窥阴器趣", "categories/672/speculum"),
    ("施虐快感", "categories/626/sadism"),
    ("灌肠玩法", "categories/375/enema"),
    ("水下激情", "categories/727/underwater"),
    ("硅胶丰满", "categories/652/silicone"),
    ("叶妮芙", "categories/139/yennefer"),
    ("搞笑色情", "categories/326/comedy"),
    ("皱纹熟女", "categories/755/wrinkled"),
    ("Leela", "categories/146/leela"),
    ("修理工诱惑", "categories/615/repairman"),
    ("射后放屁", "categories/344/cum-farting"),
    ("精准挑逗", "categories/696/targeted"),
    ("妈妈与少年", "categories/529/mom-and-boy"),
    ("Amy Wong", "categories/148/amy-wong"),
    ("大阴蒂诱惑", "categories/265/big-clit"),
    ("仓库偷情", "categories/742/warehouse"),
    ("诗乃（朝田诗乃）", "categories/96/sinon-(asada-shino)"),
    ("三星小助手Sam", "categories/111/samsung-sam"),
    ("平胸诱惑", "categories/396/flat-chested"),
    ("海绵宝宝", "categories/89/sponge-bob"),
    ("布雷默顿", "categories/108/bremerton"),
    ("废弃老屋激情", "categories/220/abandoned-house"),
    ("外星飞船", "categories/57/ufo"),
    ("丝滑诱惑", "categories/653/silk"),
    ("阴茎环", "categories/322/cock-ring"),
    ("啤酒助兴", "categories/261/beer"),
    ("爱宕", "categories/140/atago"),
    ("骷髅魅影", "categories/193/skeleton"),
    ("捆绑紧缚", "categories/451/hogtied"),
    ("身体彩绘", "categories/279/body-painting"),
    ("触手怪戏", "categories/701/tentacle"),
    ("性爱狂欢", "categories/641/sex"),
    ("科琳", "categories/102/corrin"),
    ("学生弟弟", "categories/631/schoolboy"),
    ("小偷被抓", "categories/703/thief-caught"),
    ("机场偷情", "categories/224/airport"),
    ("Other Planet", "categories/157/other-planet"),
    ("Iron Man", "categories/155/iron-man"),
    ("梅林", "categories/95/merlin"),
    ("佩罗娜", "categories/97/perona"),
    ("长指甲性感", "categories/502/long-nails"),
]

HEADER_RE = re.compile(r"<header[\s\S]*?</header>", re.I)
NAV_RE = re.compile(r"<nav[\s\S]*?</nav>", re.I)
FOOTER_RE = re.compile(r"<footer[\s\S]*?</footer>", re.I)
ITEM_START_RE = re.compile(r'<div class="item">')
DATA_S_RE = re.compile(r"data-s=[\"']([^\"']+)[\"']")
DATA_I_RE = re.compile(r"data-i=[\"']([^\"']+)[\"']")
DATA_U_RE = re.compile(r"data-u=[\"']([^\"']+)[\"']")
DATA_Q_RE = re.compile(r"data-q=[\"']([^\"']+)[\"']")
A_HREF_RE = re.compile(r"<a[^>]+href=[\"']([^\"']+)[\"']")
IMG_TAG_RE = re.compile(r"(<img[^>]+>)")
DATA_VID_RE = re.compile(r"data-vid=[\"'](\d+)[\"']")
V_PATH_RE = re.compile(r"/v/(\d+)/")
TITLE_ATTR_RE = re.compile(r"title=[\"']([^\"']+)[\"']")
ALT_RE = re.compile(r"alt=[\"']([^\"']*)[\"']")
A_TEXT_RE = re.compile(r"<a[^>]*>([\s\S]*?)</a>")
DATA_SRC_RE = re.compile(r"data-src=[\"']([^\"']+)[\"']")
DATA_ORIGINAL_RE = re.compile(r"data-original=[\"']([^\"']+)[\"']")
SRC_RE = re.compile(r"src=[\"']([^\"']+)[\"']")
DURATION_RE = re.compile(r"(?:class=[\"'][^\"']*(?:duration|time|length)[^\"']*[\"'][^>]*>|>)\s*(\d{1,2}:\d{2}(?::\d{2})?)\s*<")
TAG_RE = re.compile(r"<[^>]+>")
H1_RE = re.compile(r"<h1[^>]*>([\s\S]*?)</h1>", re.I)
VIDEO_POSTER_RE = re.compile(r"<video[^>]+poster=[\"']([^\"']+)[\"']")
OG_IMAGE_RE = re.compile(r"og:image[\"'][^>]+content=[\"']([^\"']+)[\"']")
GENRE_RE = re.compile(r"href=[\"'][^\"']*/categories/\d+/[^\"']*[\"'][^>]*>([^<]{1,40})</a>")
ISO_DURATION_RE = re.compile(r"\"duration\":\s*\"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?\"")
SOURCE_SRC_RE = re.compile(r"<source[^>]+src=[\"']([^\"']+)[\"']", re.I)
VIDEO_SRC_RE = re.compile(r"<video[^>]+src=[\"']([^\"']+)[\"']", re.I)
MP4_QUOTED_RE = re.compile(r"[\"'](https?://[^\"']+\.mp4[^\"']*)[\"']", re.I)
M3U8_QUOTED_RE = re.compile(r"[\"'](https?://[^\"']+\.m3u8[^\"']*)[\"']", re.I)
ORIGIN_RE = re.compile(r"^(https?://[^/?#]+)", re.I)
B64_RE = re.compile(r"[\"']([A-Za-z0-9+/=]{100,})[\"']")
NAV_HREF_RE = re.compile(r"href=[\"'](https?://[^\"'/?#]+)[^\"']*[\"']", re.I)


def strip_tags(s):
    return TAG_RE.sub("", str(s or ""))


def clean_text(s):
    t = strip_tags(s)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def first_match(text, pattern):
    m = pattern.search(str(text or ""))
    return m.group(1) if m else ""


def extract_origin(url):
    m = ORIGIN_RE.match(str(url or ""))
    return m.group(1).rstrip("/") if m else ""


def decode_b64_utf8(b64_str):
    if not b64_str:
        return ""
    clean = re.sub(r"\s+", "", str(b64_str))
    try:
        return base64.b64decode(clean).decode("utf-8")
    except Exception:
        return ""


def collect_candidate_base_urls(item):
    urls = []
    if not isinstance(item, dict):
        return urls
    raw_list = []
    for key in ("url", "link", "href", "directUrl", "bestUrl"):
        if item.get(key):
            raw_list.append(str(item.get(key)))
    sub = item.get("urls")
    if isinstance(sub, list):
        for u_obj in sub:
            if isinstance(u_obj, str):
                raw_list.append(u_obj)
            elif isinstance(u_obj, dict):
                if u_obj.get("url"):
                    raw_list.append(str(u_obj.get("url")))
                if u_obj.get("href"):
                    raw_list.append(str(u_obj.get("href")))
    for raw in raw_list:
        base = extract_origin(raw)
        if base and base not in urls:
            urls.append(base)
    return urls


def kw_hit(kw_list, route_low, name_low):
    for kw in kw_list:
        if kw in route_low or kw in name_low:
            return True
    return False


def bucket_of(route, cname):
    rl = str(route).lower()
    nl = str(cname).lower()
    if kw_hit(KW_3D, rl, nl):
        return "sec_3d"
    if kw_hit(KW_CHAR, rl, nl):
        return "sec_char"
    if kw_hit(KW_ANIME, rl, nl):
        return "sec_anime"
    if kw_hit(KW_PHYSIQUE, rl, nl):
        return "sec_physique"
    if kw_hit(KW_ROLEPLAY, rl, nl):
        return "sec_roleplay"
    return "sec_scenes"


class Spider(BaseSpider):
    def __init__(self):
        super().__init__()
        self.host = DEFAULT_HOST
        self.custom_host = ""
        self._discovered = ""

    def getName(self):
        return SITE_NAME

    def init(self, extend=""):
        custom = ""
        ext = extend
        if isinstance(ext, str) and ext.strip():
            text = ext.strip()
            if text.startswith("http"):
                custom = text
            else:
                try:
                    data = json.loads(text)
                    if isinstance(data, dict):
                        custom = str(data.get("host") or "")
                except Exception:
                    pass
        elif isinstance(ext, dict):
            custom = str(ext.get("host") or "")
        custom = custom.strip()
        if custom.startswith("http"):
            self.custom_host = custom.rstrip("/")
            self.host = self.custom_host

    def isVideoFormat(self, url):
        return False

    def manualVideoCheck(self):
        return False

    # ---------- host discovery / auto heal ----------

    def _page_headers(self, host):
        return {
            "User-Agent": UA,
            "Referer": host + "/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }

    def _check_host_alive(self, base_url):
        clean_base = str(base_url or "").rstrip("/")
        if not clean_base:
            return ""
        target = clean_base + "/videos?hl=zh"
        headers = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        }
        try:
            resp = requests.get(target, headers=headers, timeout=7)
            html = resp.text if resp is not None else ""
            st = resp.status_code if resp is not None else 0
            if (st == 0 or (200 <= st < 400)) and 'class="item"' in html:
                return extract_origin(resp.url) or clean_base
        except Exception:
            if target.startswith("https://"):
                try:
                    resp2 = requests.get("http://" + target[8:], headers=headers, timeout=7)
                    html2 = resp2.text if resp2 is not None else ""
                    st2 = resp2.status_code if resp2 is not None else 0
                    if (st2 == 0 or (200 <= st2 < 400)) and 'class="item"' in html2:
                        return extract_origin(resp2.url) or clean_base
                except Exception:
                    pass
        return ""

    def _refresh_host(self, force=False):
        if self.custom_host:
            return self.custom_host
        if self._discovered and not force:
            return self._discovered
        headers = {
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        for nav in NAV_URLS:
            text = ""
            try:
                resp = requests.get(nav, headers=headers, timeout=6)
                if resp is not None and resp.text:
                    text = resp.text
            except Exception:
                continue
            if not text:
                continue
            for m in B64_RE.finditer(text):
                decoded = decode_b64_utf8(m.group(1))
                if not decoded:
                    continue
                unquoted = decoded
                if "%5B" in decoded or "%7B" in decoded:
                    try:
                        unquoted = unquote(decoded)
                    except Exception:
                        pass
                if "[" in unquoted and ("cartoonporno" in unquoted.lower() or "动漫卡通" in unquoted):
                    try:
                        site_list = json.loads(unquoted)
                    except Exception:
                        continue
                    if not isinstance(site_list, list):
                        continue
                    for item in site_list:
                        if not isinstance(item, dict):
                            continue
                        name = str(item.get("name") or item.get("title") or "").strip().lower()
                        desc = str(item.get("desc") or item.get("description") or "").strip()
                        if "cartoonporno" in name or "免费精品动漫卡通视频" in desc:
                            for cand in collect_candidate_base_urls(item):
                                alive = self._check_host_alive(cand)
                                if alive:
                                    self._discovered = alive
                                    return alive
            card_idx = text.lower().find("cartoonporno")
            if card_idx != -1:
                snippet = text[max(0, card_idx - 100):card_idx + 500]
                for hm in NAV_HREF_RE.finditer(snippet):
                    cand = extract_origin(hm.group(1))
                    if cand and "x99dh" not in cand:
                        alive = self._check_host_alive(cand)
                        if alive:
                            self._discovered = alive
                            return alive
        for mirror in MIRROR_POOL:
            alive = self._check_host_alive(mirror)
            if alive:
                self._discovered = alive
                return alive
        alive = self._check_host_alive(DEFAULT_HOST)
        if alive:
            self._discovered = alive
            return alive
        self._discovered = DEFAULT_HOST
        return DEFAULT_HOST

    def _current_host(self):
        if self.custom_host:
            return self.custom_host
        if self._discovered:
            return self._discovered
        return DEFAULT_HOST

    # ---------- fetch ----------

    def _abs_url(self, raw, host):
        u = str(raw or "").strip().replace("&amp;", "&")
        if not u:
            return ""
        if u.startswith("//"):
            return "https:" + u
        if u.startswith("/"):
            return host + u
        if u.startswith("http"):
            return u
        return host + "/" + u

    def _image_address(self, raw_pic, host):
        absolute = self._abs_url(raw_pic, host)
        if not absolute:
            return ""
        return absolute + "@Referer=" + quote(host + "/", safe="") + "&User-Agent=" + quote(UA, safe="")

    def _fetch(self, path, retry=True):
        if self.custom_host:
            host = self.custom_host
        elif self._discovered:
            host = self._discovered
        else:
            host = self._refresh_host()
        full_url = self._abs_url(path, host)
        headers = self._page_headers(host)
        resp = None
        try:
            resp = requests.get(full_url, headers=headers, timeout=8)
        except Exception:
            resp = None
        if resp is not None:
            if resp.status_code >= 400 and retry and not self.custom_host:
                new_host = self._refresh_host(force=True)
                if new_host and new_host != host:
                    return self._fetch(path, retry=False)
            if resp.text:
                return (resp.text, extract_origin(resp.url) or host)
        if full_url.startswith("https://"):
            try:
                resp2 = requests.get("http://" + full_url[8:], headers=headers, timeout=8)
                if resp2 is not None and 200 <= resp2.status_code < 400 and resp2.text:
                    return (resp2.text, extract_origin(resp2.url) or host)
            except Exception:
                pass
        if retry and not self.custom_host:
            new_host = self._refresh_host(force=True)
            if new_host and new_host != host:
                return self._fetch(path, retry=False)
        return ("", host)

    # ---------- cards ----------

    def _parse_cards(self, html, host):
        clean = HEADER_RE.sub("", str(html or ""))
        clean = NAV_RE.sub("", clean)
        clean = FOOTER_RE.sub("", clean)
        starts = [m.start() for m in ITEM_START_RE.finditer(clean)]
        items = []
        seen = set()
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(clean)
            block = clean[start:end]
            data_s = first_match(block, DATA_S_RE)
            data_i = first_match(block, DATA_I_RE)
            data_u = first_match(block, DATA_U_RE)
            data_q = first_match(block, DATA_Q_RE)
            detail_path = ""
            if data_s and data_i:
                detail_path = data_s + data_i + data_u + data_q
            else:
                href = first_match(block, A_HREF_RE)
                if href and "/v/" in href:
                    absolute = self._abs_url(href, host)
                    detail_path = absolute[len(host):] if absolute.startswith(host) else absolute
            img_tag = first_match(block, IMG_TAG_RE) or block
            vid = data_i or first_match(img_tag, DATA_VID_RE) or first_match(detail_path, V_PATH_RE)
            if not vid or not detail_path or vid in seen:
                continue
            seen.add(vid)
            title = first_match(block, TITLE_ATTR_RE)
            if not title:
                title = first_match(img_tag, ALT_RE)
            if not title:
                for am in A_TEXT_RE.finditer(block):
                    ct = clean_text(am.group(1))
                    if len(ct) > 2:
                        title = ct
                        break
            if not title:
                title = "视频 " + vid
            pic = first_match(img_tag, DATA_SRC_RE)
            if not pic or "zero.png" in pic:
                pic = first_match(img_tag, DATA_ORIGINAL_RE)
            if not pic or "zero.png" in pic:
                pic = first_match(img_tag, SRC_RE)
            if "zero.png" in pic or ".svg" in pic:
                pic = ""
            duration = first_match(block, DURATION_RE)
            remarks = (BRAND_NAME + " | " + duration) if duration else BRAND_NAME
            vod = {
                "vod_id": vid + "@@" + quote(detail_path, safe="") + "@@" + quote(title, safe=""),
                "vod_name": title,
                "vod_pic": self._image_address(pic, host),
                "vod_remarks": remarks,
                "style": {"type": "rect", "ratio": 1.78},
            }
            items.append({"vid": vid, "path": detail_path, "title": title, "vod": vod})
        return items

    # ---------- detail helpers ----------

    def _extract_genres(self, html):
        h1 = H1_RE.search(str(html or ""))
        if not h1:
            return []
        seg = str(html)[h1.start():h1.start() + 7000]
        genres = []
        seen = set()
        for m in GENRE_RE.finditer(seg):
            name = clean_text(m.group(1))
            if name and name not in seen:
                seen.add(name)
                genres.append(name)
                if len(genres) >= 10:
                    break
        return genres

    def _iso_duration(self, html):
        m = ISO_DURATION_RE.search(str(html or ""))
        if not m:
            return ""
        hh = int(m.group(1)) if m.group(1) else 0
        mm = int(m.group(2)) if m.group(2) else 0
        ss = int(m.group(3)) if m.group(3) else 0
        sec_str = ("0" + str(ss)) if ss < 10 else str(ss)
        if hh > 0:
            min_str = ("0" + str(mm)) if mm < 10 else str(mm)
            return str(hh) + ":" + min_str + ":" + sec_str
        return str(mm) + ":" + sec_str

    def _is_bad_stream(self, cand):
        low = str(cand or "").lower()
        return "p320-180.mp4" in low or "preview" in low or "sample" in low

    def _extract_stream(self, html, host):
        text = str(html or "")
        for pattern in (SOURCE_SRC_RE, VIDEO_SRC_RE, MP4_QUOTED_RE, M3U8_QUOTED_RE):
            for m in pattern.finditer(text):
                cand = m.group(1).strip() if m.group(1) else ""
                if cand and not self._is_bad_stream(cand):
                    return self._abs_url(cand, host)
        return ""

    # ---------- home / category / search ----------

    def _section_options(self, section_id, all_label):
        options = [{"n": all_label, "v": ""}]
        for cname, route in ALL_CATS:
            if section_id == "videos":
                options.append({"n": cname, "v": route})
                continue
            if bucket_of(route, cname) == section_id:
                options.append({"n": cname, "v": route})
        return options

    def homeContent(self, filter):
        classes = [{"type_id": sid, "type_name": sname} for sid, sname, _fname, _all in SECTION_DEFS]
        result = {"class": classes}
        if filter:
            filters = {}
            for sid, _sname, filter_name, all_label in SECTION_DEFS:
                filters[sid] = [
                    {"key": "s", "name": "排序", "init": "",
                     "value": [{"n": "最受欢迎", "v": ""}, {"n": "最新发布", "v": "n"}]},
                    {"key": "cat", "name": filter_name, "init": "",
                     "value": self._section_options(sid, all_label)},
                ]
            result["filters"] = filters
        return result

    def homeVideoContent(self):
        text, host = self._fetch("/videos?hl=zh")
        cards = self._parse_cards(text, host) if text else []
        return {"list": [c["vod"] for c in cards[:18]]}

    def _page_form(self, vods, page):
        if vods:
            return {"list": vods, "page": page, "pagecount": page + 1,
                    "limit": PAGE_SIZE, "total": (page + 1) * PAGE_SIZE}
        return {"list": [], "page": page, "pagecount": page,
                "limit": PAGE_SIZE, "total": 0}

    def categoryContent(self, tid, pg, filter, extend):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        ext = extend if isinstance(extend, dict) else {}
        chosen_cat = str(ext.get("cat") or "").strip("/")
        if chosen_cat:
            route = chosen_cat
        elif tid in SECTION_DEFAULT_ROUTE:
            route = SECTION_DEFAULT_ROUTE[tid]
        else:
            route = str(tid or "").strip("/")
        if route == "videos":
            path = "/videos?hl=zh"
        else:
            path = "/" + route + "?hl=zh"
        s_val = ext.get("s")
        if s_val:
            path = path + "&s=" + quote(str(s_val), safe="")
        if page > 1:
            path = path + "&p=" + str(page)
        text, host = self._fetch(path)
        cards = self._parse_cards(text, host) if text else []
        return self._page_form([c["vod"] for c in cards], page)

    def searchContent(self, key, quick, pg="1"):
        try:
            page = int(pg)
        except Exception:
            page = 1
        if page < 1:
            page = 1
        if page > 1:
            return self._page_form([], page)
        keyword = str(key or "")
        path = "/search?q=" + quote(keyword, safe="") + "&hl=zh"
        text, host = self._fetch(path)
        cards = self._parse_cards(text, host) if text else []
        return self._page_form([c["vod"] for c in cards], page)

    # ---------- detail ----------

    def _brand_block(self, host):
        lines = [
            "🦋 " + SITE_NAME + "官方交流群：@tvshare23",
            "导演：" + BRAND_DIRECTOR,
            "当前主站：" + host,
            "━" * 28,
            "━" * 7,
        ]
        return "\n".join(lines)

    def detailContent(self, ids):
        raw = str(ids[0]) if ids else ""
        parts = raw.split("@@")
        vid = parts[0] if parts else ""
        detail_path = unquote(parts[1]) if len(parts) > 1 else ""
        ref_title = unquote(parts[2]) if len(parts) > 2 else ""
        if not detail_path:
            detail_path = "/v/" + vid + "/"
        text, host = self._fetch(detail_path)
        if not text:
            return {"list": []}
        h1 = H1_RE.search(text)
        title = clean_text(h1.group(1)) if h1 else ""
        if not title:
            title = ref_title
        if not title:
            title = vid
        poster_raw = first_match(text, VIDEO_POSTER_RE)
        if not poster_raw:
            poster_raw = first_match(text, OG_IMAGE_RE)
        poster = self._image_address(poster_raw, host)
        genres = self._extract_genres(text)
        duration = self._iso_duration(text)

        episode_strs = []
        first_name = title.replace("$", "_").replace("#", "_")
        episode_strs.append(first_name + "$" + json.dumps({"path": detail_path}, ensure_ascii=False))
        rel_titles = []
        related = self._parse_cards(text, host)
        for card in related:
            if card["vid"] == vid:
                continue
            if len(episode_strs) >= 20:
                break
            ep_name = card["title"].replace("$", "_").replace("#", "_")
            episode_strs.append(ep_name + "$" + json.dumps({"path": card["path"]}, ensure_ascii=False))
            rel_titles.append(card["title"])

        fallback = [
            "标题：" + title,
            "分类：" + "、".join(genres),
            "片源：" + LINE_NAME,
            "编号：" + vid,
        ]
        if rel_titles:
            fallback.append("相关推荐：" + "、".join(rel_titles[:6]))
        content = self._brand_block(host) + "\n" + "\n".join(fallback)

        vod = {
            "vod_id": vid,
            "vod_name": title,
            "vod_pic": poster,
            "vod_bg": poster,
            "vod_background": poster,
            "vod_banner": poster,
            "vod_actor": BRAND_ACTOR,
            "vod_director": BRAND_DIRECTOR,
            "vod_remarks": (BRAND_NAME + " | " + duration) if duration else BRAND_NAME,
            "vod_content": content,
            "vod_play_from": LINE_NAME,
            "vod_play_url": "#".join(episode_strs),
        }
        return {"list": [vod]}

    # ---------- player ----------

    def playerContent(self, flag, pid, vipFlags):
        host = self._current_host()
        headers = {"User-Agent": UA, "Referer": host + "/"}
        data = None
        try:
            parsed = json.loads(pid)
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = None
        if data is not None and data.get("path"):
            path = str(data.get("path"))
            text, eff_host = self._fetch(path)
            if text:
                stream = self._extract_stream(text, eff_host)
                if stream:
                    final_url = stream
                    try:
                        r = requests.get(stream, headers={"User-Agent": UA, "Referer": eff_host + "/", "Range": "bytes=0-0"}, timeout=8)
                        if r is not None and r.url and str(r.url) != stream and str(r.url).startswith("http"):
                            final_url = str(r.url)
                    except Exception:
                        pass
                    return {"parse": 0, "url": final_url,
                            "header": {"User-Agent": UA, "Referer": eff_host + "/"}}
            return {"parse": 1, "url": self._abs_url(path, eff_host if text else host),
                    "header": headers}
        if isinstance(pid, str) and pid.startswith("http"):
            return {"parse": 0, "url": pid, "header": headers}
        return {"parse": 1, "url": host + "/", "header": headers}

# --- System Signature ---
#‍​​‌‌​‌‌​​​‌‌​​​​​​‌‌​​​‌​​‌‌​​​‌​​‌‌​​​​​​‌‌​‌‌‌​​‌‌​​​​​​‌‌​​​‌​​‌‌​‌​​​​‌‌​‌‌‌‍
# Source: https://sub.lytvs.top/trap?token=tk_cecf4b5f&t=1795249509215&sig=3f1bb515edd9cc78
