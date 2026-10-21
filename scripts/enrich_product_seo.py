#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich product PDPs with punchy 痛點 / 功效好處 / 適用 / SEO keywords (private site).

Idempotent: replaces existing #pdp-efficacy blocks. No Cap.231 soft wording.
Strong claims OK per Miles 2026-10-21.
"""
from __future__ import annotations

import html as htmlmod
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
PRODUCTS = REPO / "products"
CSS = REPO / "assets" / "site.css"
MARKER_START = "<!-- pdp-efficacy:start -->"
MARKER_END = "<!-- pdp-efficacy:end -->"

# (match_keys, theme_id, label, pains[], benefits[], uses[], kws[], lead)
THEMES: list[tuple] = [
    (
        ["炎必清"],
        "yanbiqing",
        "清熱解毒・強力消炎養生",
        [
            "暗瘡反覆爆發、面油多、下巴囊腫，怎麼擠都消不乾淨？",
            "咽喉乾痛、聲沙、口腔潰瘍，說話飲食都難受？",
            "口乾口苦、體熱濕重、小便黃、脾氣暴躁——典型上火訊號？",
            "熬夜應酬、辛辣油炸後第二天整個人「燒著」的感覺？",
            "換季就喉嚨敏感、容易攞感冒、免疫力明顯下降？",
        ],
        [
            "強力清熱解毒：針對上火、濕熱、暗瘡發炎源頭調理",
            "舒緩咽喉腫痛與口腔不適，令吞嚥、說話更輕鬆",
            "草本配方（穿心蓮、紫錐花、蒲公英、香蜂草）全面清熱涼血",
            "幫助排出體內積熱，改善面油、口臭、體熱煩躁",
            "增強日常抵抗力，換季、熬夜期更穩陣",
            "香港製造口服膠囊，見效節奏清晰，適合持續調理",
        ],
        ["暗瘡炎症", "咽喉腫痛", "口乾口苦上火", "濕熱體質", "熬夜應酬後調理", "換季免疫力下降", "口腔潰瘍"],
        [
            "炎必清", "強力炎必清", "清熱解毒", "消炎", "暗瘡", "咽喉腫痛", "上火", "濕熱",
            "穿心蓮", "紫錐花", "蒲公英", "口臭", "清熱膠囊", "香港炎必清", "盈康炎必清",
            "去火", "涼血", "免疫力", "功效", "邊度買炎必清",
        ],
        "{name}專打上火、暗瘡、咽喉腫痛！清熱解毒草本膠囊，熬夜應酬、濕熱體質人士必備——要消腫、去火、穩免疫，就揀佢。",
    ),
    (
        ["鼻炎"],
        "biyan",
        "鼻敏感剋星・暢通呼吸",
        [
            "一早起身就打噴嚏、流清水鼻涕，面紙用到成疊？",
            "鼻塞到要用口呼吸，睡覺打鼻鼾、晨早頭痛？",
            "換季、冷氣房、塵蟣一嚟就鼻癢難頂？",
            "鼻敏感反覆，滴鼻劑越用越依賴仍未根治困擾？",
            "嗅覺變差、頭痛、影響精神同工作效率？",
        ],
        [
            "強力舒緩鼻敏感：減少鼻塞、流涕、鼻癢、打噴嚏",
            "幫助修復鼻腔舒適環境，令呼吸回復暢順",
            "日常口服防護，減低塵蟣、冷氣、花粉刺激反應",
            "改善因鼻塞引起的睡眠質素與日間精神",
            "溫和不嗜睡，可長期作為鼻部保健方案",
            "換季前開始食，效果更穩——鼻敏感人士口碑之選",
        ],
        ["過敏性鼻炎", "季節性鼻敏感", "鼻塞流鼻水", "打噴嚏鼻癢", "冷氣房鼻不適", "塵蟣過敏", "睡眠鼻塞"],
        [
            "鼻炎素", "鼻敏感", "鼻塞", "流鼻水", "過敏性鼻炎", "換季鼻炎", "打噴嚏",
            "鼻癢", "鼻腔護理", "呼吸道", "抗過敏", "鼻炎治療", "香港鼻敏感", "暢通呼吸",
        ],
        "{name}專治鼻敏感煩惱！針對鼻塞、流涕、打噴嚏，幫你重拾暢通呼吸與安穩睡眠——換季、冷氣房再唔使驚。",
    ),
    (
        ["久咳", "咳丸", "咳調理"],
        "cough",
        "久咳化痰・氣管調理",
        [
            "咳咗幾個禮拜仍未斷尾，日間夜間都響？",
            "痰多難咯、喉嚨痕、一講多兩句就咳？",
            "轉季、冷氣、煙塵一刺激就引發氣管敏感？",
            "夜間咳嗽影響自己同家人睡眠？",
            "止咳糖漿越食越無感覺，想要更徹底調理？",
        ],
        [
            "針對久咳不癒、痰多、氣管敏感作強力調理",
            "潤肺化痰，減少喉嚨痕同連續乾咳",
            "幫助舒緩夜間咳嗽，改善睡眠質素",
            "適合轉季咳嗽、煙塵環境、反覆氣管不適",
            "傳統調理思路＋現代口服方便，見效節奏清晰",
            "可作為家庭常備——一有久咳徵兆即開始調理",
        ],
        ["久咳不癒", "痰多難咯", "夜間咳嗽", "氣管敏感", "轉季咳嗽", "喉嚨痕乾咳", "煙塵刺激咳嗽"],
        [
            "久咳丸", "強力特效久咳丸", "止咳", "化痰", "潤肺", "氣管", "久咳不癒",
            "咳嗽藥", "痰多", "夜間咳", "香港止咳", "尹淑梅久咳", "功效",
        ],
        "{name}專攻久咳痰多！潤肺化痰、舒緩氣管敏感，夜間咳醒、轉季咳嗽人士嘅強力調理選擇。",
    ),
    (
        ["膏布", "貼布", "電氣石"],
        "plaster",
        "外用膏布・深層止痛舒筋",
        [
            "腰酸背痛到企唔直、坐唔穩，成日要扶住腰？",
            "坐骨神經痛由腰放射到腳，行路都艱難？",
            "頸緊膊痛、肩周僵硬，轉頭都痛？",
            "運動扭傷、肌肉酸痛，休息幾日都未好返？",
            "風濕舊患一到落雨潮濕就成身骨痛？",
        ],
        [
            "深層滲透止痛：成分直達肌肉深處，快速紓緩酸痛",
            "針對坐骨神經痛、腰腿痛、頸椎肩周一次貼定",
            "溫熱／清涼雙感，舒筋活絡、鬆開僵硬關節",
            "粘性適中易撕，大面積覆蓋，貼完照常活動",
            "一條根、艾草等經典外用配方，港人口碑之選",
            "久坐、長途駕駛、運動後、長輩護理——隨身常備",
        ],
        ["腰酸背痛", "坐骨神經痛", "頸緊膊痛", "肩周炎", "肌肉扭傷", "風濕骨痛", "運動後痠痛", "落雨骨痛"],
        [
            "坐骨神經膏布", "一條根膏布", "止痛貼", "鎮痛貼", "腰背痛貼", "頸椎貼布",
            "肩周炎", "風濕膏布", "舒筋活絡", "外用貼布", "金門一條根", "滅濕痛膏布",
            "邊度買膏布", "香港膏布", "功效",
        ],
        "{name}外用深層止痛！腰背痛、坐骨痛、頸膊僵硬一貼紓緩——滲透力強、覆蓋大，筋骨痛楚人士必備。",
    ),
    (
        ["骨剌", "骨刺", "風澀", "風痛骨", "骨痛靈", "骨痛"],
        "joint_oral",
        "骨刺關節・風濕克星",
        [
            "關節骨刺壓住神經，手脚麻痹、伸屈困難？",
            "風濕骨痛一到天氣轉涼就發作，痛到瞓唔着？",
            "腰酸背痛、四肢震軟、氣血不通，行路無力？",
            "膝頭、手指關節變形腫痛，扭蓋都費力？",
            "市面風濕藥副作用大，想要天然有效替代？",
        ],
        [
            "強力針對骨刺、關節炎、風濕痛作口服深層調理",
            "促進末梢循環與新陳代謝，減少麻木震軟",
            "舒緩腰腿酸痛、坐骨腰痛、腰椎勞損不適",
            "天然配方思路，避免化學風濕藥刺激腸胃",
            "維持神經肌肉正常機能，令關節更靈活",
            "持續服用，幫助鞏固筋骨、減少復發頻率",
        ],
        ["關節炎", "骨刺壓迫", "風濕骨痛", "四肢麻木", "腰酸背痛", "腰椎勞損", "天氣轉涼發作", "關節腫痛"],
        [
            "風澀骨剌丹", "骨刺丹", "關節炎", "風濕", "骨痛靈", "末梢循環", "筋骨保健",
            "腰腿麻木", "風濕藥", "骨刺治療", "香港關節", "功效", "邊度買骨刺丹",
        ],
        "{name}專剋骨刺風濕！改善關節炎、四肢麻木、腰腿酸痛——促進循環、靈活關節，天氣轉涼都唔驚。",
    ),
    (
        ["坐骨", "腰痛丸", "腰痛油", "通丸", "神徑痛丸", "神經痛丸"],
        "sciatica",
        "坐骨神經・腰腿痛救星",
        [
            "坐骨神經痛由臀部射到腳趾，痛到要歇多次？",
            "久坐辦公室／揸車，一下嚟就腰腿又麻又痛？",
            "腰椎勞損、椎間盤關注，行樓梯無力？",
            "夜間腰腿抽痛，輾轉難眠？",
            "按摩、休息都只係一時，痛楚週而復始？",
        ],
        [
            "專攻坐骨神經痛、腰痛、臀腿放射痛",
            "口服／外用雙線護理，深層紓緩腰腿僵硬",
            "幫助改善氣血不通、麻痹無力感",
            "適合司機、文職久坐、長者腰腿衰退",
            "可搭配膏布、痛油使用，內外夾擊更徹底",
            "持續調理減少復發，重拾活動自由度",
        ],
        ["坐骨神經痛", "慢性腰痛", "臀腿放射痛", "腰椎勞損", "久坐麻痹", "夜間腰腿痛", "椎間盤關注"],
        [
            "坐骨神經痛", "坐骨神經丸", "腰痛丸", "腰腿痛", "坐骨痛油", "腰椎",
            "久坐腰痛", "香港坐骨", "坐骨治療", "功效", "邊度買坐骨丸",
        ],
        "{name}專治坐骨神經痛同腰痛！久坐放射痛、腰腿麻痹——內外調理，幫你行得鬆、坐得穩。",
    ),
    (
        ["痛油", "靈油", "活絡油", "追風", "神油", "破痛", "楓濕"],
        "oil",
        "活絡痛油・即擦即舒緩",
        [
            "肩頸僵硬如石，按摩都揉唔開？",
            "風濕舊患、天氣潮濕就周身骨痛？",
            "運動後肌肉酸脹，第二日抬手都痛？",
            "腰腿抽筋、落枕、扭傷，需要即時外用救援？",
            "想要一支隨身活絡油，痛就擦、方便快捷？",
        ],
        [
            "即擦即感溫熱／清涼，快速打斷酸痛感覺",
            "舒筋活絡、促進局部血液循環",
            "針對風濕痛、肩頸腰腿、運動損傷全面覆蓋",
            "滲透力強，按摩推開後舒適持久",
            "便攜瓶裝，辦公室、出行、家居隨時用",
            "港人經典追風／活絡油思路，效果口碑載道",
        ],
        ["風濕痛", "肩頸僵硬", "腰腿酸痛", "運動扭傷", "落枕", "潮濕天氣骨痛", "肌肉抽筋"],
        [
            "活絡油", "追風油", "坐骨痛油", "風濕油", "肩頸油", "千里追風", "破痛油",
            "外用按摩油", "舒筋活絡", "香港活絡油", "功效", "邊度買活絡油",
        ],
        "{name}即擦即舒緩！風濕、肩頸、腰腿酸痛——活絡滲透、隨身常備，痛楚一嚟就對抗。",
    ),
    (
        ["滅濕痛", "濕痛"],
        "mieshitong",
        "滅濕痛・風濕濕重克星",
        [
            "天氣潮濕就關節腫脹酸痛，如浸喺水裡？",
            "風濕痛反反覆覆，陰雨天特別難頂？",
            "筋骨沉重、晨早僵硬，要活動半日先鬆？",
            "試過無數風濕貼仍覺得「濕氣」散唔到？",
        ],
        [
            "針對風濕濕重、陰雨骨痛作強力外用紓緩",
            "幫助驅散濕滯感，減輕關節酸脹僵硬",
            "膏布／油劑多規格，對應不同痛位覆蓋",
            "適合長者、潮濕季節、舊患反覆人士",
            "貼敷方便，持續使用鞏固舒適感",
        ],
        ["風濕濕重", "陰雨骨痛", "關節腫脹", "晨僵", "潮濕季節發作"],
        [
            "滅濕痛", "風痛膏布", "濕痛", "風濕貼", "潮濕關節痛", "驅濕", "香港風濕", "功效",
        ],
        "{name}專剋濕重風濕！陰雨腫痛、關節沉重——外用強力紓緩，潮濕天都有救。",
    ),
    (
        ["膚特靈", "滴膚", "Difugen", "difugen"],
        "skin",
        "保濕修護・乾肌救星",
        [
            "冷氣房待一日，面同手背乾到甩皮？",
            "入秋轉涼皮膚緊繃刺癢，乳液不夠力？",
            "敏感乾燥、紅斑脫屑，外觀同觸感都差？",
            "隨身補水產品太濕潤或易致粉刺？",
        ],
        [
            "快速補水保濕，即時紓緩乾燥緊繃",
            "強化皮膚屏障，減少脫屑同不適感",
            "噴霧／滴劑便攜，案頭手袋隨時補",
            "適合冷氣族、乾敏肌、換季乾肌",
            "清爽不黏膩，日常可多次使用",
        ],
        ["皮膚極度乾燥", "冷氣房脫屑", "入秋乾肌", "敏感緊繃", "屏障修護"],
        [
            "膚特靈", "滴膚堅", "保濕噴霧", "皮膚乾燥", "修護", "香港保濕", "乾肌", "功效",
        ],
        "{name}乾肌救星！冷氣、換季乾燥脫屑——快速保濕修護，令皮膚回復水潤柔嫩。",
    ),
    (
        ["牛黃", "安宮"],
        "niuhuang",
        "牛黃清熱・傳統急救名方",
        [
            "熱盛心煩、神疲、咽喉暴痛，需要強效清熱？",
            "想家中常備傳統安宮牛黃／牛黃解毒應急？",
            "外感熱症、上火頭痛，普通涼茶不夠力？",
        ],
        [
            "傳統牛黃清熱解毒名方思路，效力強勁",
            "針對熱盛、心煩、咽喉腫痛等急劇不適",
            "多規格可選（丸劑／膠囊），應急與調理皆宜",
            "港人家庭常備之選，關鍵時刻用得着",
            "品質通路可查，WhatsApp 確認批次庫存",
        ],
        ["熱盛心煩", "咽喉暴痛", "清熱應急", "傳統中成藥常備", "外感上火"],
        [
            "安宮牛黃丸", "牛黃解毒", "清熱解毒", "中成藥", "北京安宮", "牛黃", "急救", "功效",
        ],
        "{name}傳統清熱名方！熱盛、心煩、咽喉腫痛——家庭常備，關鍵時刻清熱解毒。",
    ),
    (
        ["靈芝", "腦活", "腦白金"],
        "brain",
        "靈芝腦活・精神抗疲",
        [
            "用腦過度、精神恍惚、記性變差？",
            "加班到夜，第二日頭痛眼乾、專注力歸零？", "中老年擔心腦退化、想主動保健？",
            "睡眠淺、易醒，日間靠咖啡硬撐？",
        ],
        [
            "靈芝＋腦活素思路，全面支援腦部活力",
            "對抗精神疲勞，提升日間專注與清晰度",
            "抗氧化日常，幫助維持長期腦部健康",
            "改善因疲勞引起的睡眠質素波動",
            "適合學生、職場、中老年腦保健人群",
        ],
        ["精神疲勞", "專注力下降", "中老年腦保健", "加班用腦", "睡眠質素差"],
        [
            "靈芝", "腦活素", "腦白金", "腦保健", "抗疲勞", "精神", "香港靈芝", "功效",
        ],
        "{name}醒腦抗疲！靈芝腦活配方——對抗用腦過度、精神恍惚，維持清晰專注。",
    ),
    (
        ["六味", "地黃"],
        "liuwei",
        "六味地黃・滋陰補腎強腰",
        [
            "腰膝酸軟、夜尿多，腎虛訊號明顯？",
            "陰虛內熱、盜汗、头晕耳鳴？",
            "中老年想系統補腎，寧願食經典名方？",
        ],
        [
            "經典六味地黃：滋陰補腎、強健腰膝",
            "改善腰酸、夜尿、陰虛內熱等困擾",
            "大包裝適合長期進補，效果在堅持",
            "港人最熟識補腎方，口碑代代相傳",
        ],
        ["腰膝酸軟", "夜尿頻", "陰虛盜汗", "頭暈耳鳴", "中老年補腎"],
        [
            "六味地黃丸", "補腎", "滋陰", "腰膝酸軟", "夜尿", "地黃丸", "香港補腎", "功效",
        ],
        "{name}滋陰補腎經典！腰膝酸軟、夜尿、陰虛——強腰健腎，中老年進補首選。",
    ),
    (
        ["尿酸"],
        "uric",
        "尿酸調理・護關節代謝",
        [
            "尿酸偏高，擔心大腳趾忽然紅腫熱痛？",
            "應酬飲食多嘌呤，檢查數字節節上升？",
            "家族有痛風史，想提前代謝調理？",
        ],
        [
            "針對尿酸代謝作日常強力調理",
            "幫助維護關節舒適，減少忽然紅腫風險",
            "配合清淡飲食、多喝水，效果加倍",
            "適合應酬多、體檢尿酸高、主動保健人士",
        ],
        ["尿酸偏高", "痛風風險", "嘌呤飲食", "關節紅腫關注", "代謝調理"],
        [
            "尿酸清", "尿酸高", "痛風", "降尿酸", "嘌呤", "香港尿酸", "功效",
        ],
        "{name}專理尿酸！降代謝負擔、護關節——體檢數字高、應酬多嘅人要及早調理。",
    ),
    (
        ["脈通", "通血"],
        "vessel",
        "脈通活血・循環暢通",
        [
            "手脚長期冰冷，披住被都暖唔到？",
            "擔心血管堵塞、胸悶氣短、循環差？",
            "面色暗沉、容易疲倦，血液循環明顯不足？",
        ],
        [
            "促進血液循環，改善手脚冰冷",
            "通脈活絡，支援中老年血管日常保健",
            "幫助提升整體活力與末梢溫暖感",
            "久坐少動、血脂關注人士適合長期服用",
        ],
        ["手脚冰冷", "血液循環差", "血管保健", "胸悶氣短關注", "面色暗沉"],
        [
            "脈通", "通血丸", "血液循環", "活血", "手脚冰冷", "香港脈通", "功效",
        ],
        "{name}暢通血脈！改善手脚冰冷、循環差——活血通絡，溫暖四肢。",
    ),
    (
        ["健齒", "牙"],
        "teeth",
        "健齒護齦・口腔強健",
        [
            "牙齦萎縮鬆動、刷牙易出血？",
            "冷熱酸甜一碰就牙齒酸軟？",
            "口氣持續不佳，影響社交自信？",
        ],
        [
            "強化牙齦組織，幫助牙齒穩固",
            "紓緩牙齒敏感，進食更自在",
            "減少口腔異味，維持清新口氣",
            "由內而外營養口腔，配合刷牙事半功倍",
        ],
        ["牙齦出血鬆動", "牙齒敏感", "口气持久不佳", "牙周保養", "進食酸痛"],
        [
            "健齒靈", "牙齦", "牙齒敏感", "口气", "牙周", "口腔保健", "香港健齒", "功效",
        ],
        "{name}強健牙齦！對抗敏感、出血、口气——由內護齒，笑容更有自信。",
    ),
    (
        ["想睡", "睡眠"],
        "sleep",
        "助眠安神・快速入眠",
        [
            "躺到凌晨仲睜開眼，思緒停唔到？",
            "淺睡多夢、易醒，朝早起來更累？",
            "壓力大、心悸、焦慮影響睡眠節奏？",
        ],
        [
            "幫助快速放鬆入眠，減少輾轉反側",
            "改善淺睡易醒，提升深層休息質素",
            "安神定志，緩和緊張情緒",
            "建議固定睡前服用，建立穩定睡眠節奏",
        ],
        ["失眠入睡難", "多夢易醒", "壓力焦慮", "睡眠質素差", "晝夜顛倒"],
        [
            "想睡就睡", "助眠", "失眠", "安神", "改善睡眠", "香港助眠", "功效",
        ],
        "{name}助你一夜好眠！對抗失眠、多夢易醒——安神放鬆，睡得沉、起得精神。",
    ),
    (
        ["花塔糖"],
        "digest",
        "花塔糖・開胃消滯",
        [
            "小朋友偏食、食慾差，一餐食唔完？",
            "飯後脹氣、消化慢，成日覺得胃積住？",
            "病後、旅遊後胃口全無？",
        ],
        [
            "經典花塔糖開胃健脾，促進消化",
            "改善食慾不振、飯後脹悶",
            "口味親切，小孩長者都易接受",
            "多支裝方便家庭分享、外出攜帶",
        ],
        ["偏食食慾差", "消化不良脹氣", "病後胃口差", "小兒開胃", "健脾消滯"],
        [
            "花塔糖", "開胃", "消化", "健脾", "偏食", "消滯", "香港花塔糖", "功效",
        ],
        "{name}開胃消滯！偏食、脹氣、胃口差——經典口味，大人細路都啱。",
    ),
    (
        ["活絡靈"],
        "huoluo",
        "活絡靈・筋骨靈活",
        [
            "筋骨緊繃、轉側有聲、活動唔開？",
            "風濕關節痛，想内外一齊活絡？",
        ],
        [
            "口服活絡，深層鬆開筋骨僵硬",
            "與外用活絡油互補，內外夾擊",
            "改善天氣轉變引起的酸痛響聲",
            "適合運動恢復、中老年關節保養",
        ],
        ["筋骨僵硬", "風濕關節", "天氣酸痛", "運動恢復"],
        ["活絡靈", "筋骨", "風濕", "關節靈活", "香港活絡", "功效"],
        "{name}活絡筋骨！僵硬酸痛、風濕關節——口服調理，令活動更自如。",
    ),
    (
        ["百痛敵"],
        "baitongdi",
        "百痛敵・周身痛一次對抗",
        [
            "呢度痛完嗰度痛，周身酸痛無特效藥？",
            "風濕、腰腿、肩頸輪流發作，好疲憊？",
        ],
        [
            "綜合針對多處酸痛與風濕不適",
            "一瓶對應多痛點，慳時間慳選擇困難",
            "適合痛點分散、天氣敏感體質",
            "持續服用，全面紓緩日常痛楚負擔",
        ],
        ["周身酸痛", "多處風濕", "腰腿肩頸輪流痛", "天氣敏感痛"],
        ["百痛敵", "周身痛", "風濕痛", "綜合止痛", "香港百痛敵", "功效"],
        "{name}周身痛嘅敵人！多處酸痛、風濕輪流發作——一瓶綜合對抗。",
    ),
    (
        ["健步", "虎潛"],
        "jianbu",
        "健步虎潛・強腰膝穩步履",
        [
            "行路沒力、上樓要歇，腰膝軟弱？",
            "中老年擔心跌倒、筋骨衰退？",
        ],
        [
            "傳統虎潛／健步思路，強健腰膝",
            "提升步行耐力與步履穩定性",
            "大包裝適合長期進補",
            "中老年強筋健骨之選",
        ],
        ["腰膝無力", "步行乏力", "上樓困難", "中老年強筋骨"],
        ["健步虎潛丸", "腰膝", "強筋健骨", "中老年", "步行無力", "功效"],
        "{name}強腰膝、穩步履！行路無力、上樓困難——中老年強筋健骨首選。",
    ),
    (
        ["蕥歡"],
        "fatigue",
        "抗疲勞・回復體力精神",
        [
            "午後眼皮打架、飲咖啡都提唔起？",
            "長期疲勞、壓力大、體力透支？",
        ],
        [
            "快速對抗精神疲勞，回復專注",
            "支援體力，減少透支虛脫感",
            "適合長工時、照顧者、備試人士",
            "日常補充，令狀態更穩定",
        ],
        ["午後昏睡", "慢性疲勞", "體力透支", "壓力大"],
        ["抗疲勞", "提神", "體力", "精神疲勞", "功效"],
        "{name}抗疲提神！午後昏睡、體力透支——幫你回復精神戰鬥力。",
    ),
    (
        ["海狗", "五鞭"],
        "haigou",
        "海狗丸・壯腰補腎填精",
        [
            "腰膝酸軟、腎虛、男性精力不足？",
            "想壯腰補腎，揀傳統海狗／五鞭方？",
        ],
        [
            "傳統海狗五鞭補腎壯腰",
            "針對腰酸、腎虛、精力不足",
            "大包裝持續進補更見效",
            "男性保健經典之選",
        ],
        ["腰膝酸軟腎虛", "男性精力", "壯腰補腎", "中年保健"],
        ["海狗丸", "五鞭海狗", "補腎", "壯腰", "男性保健", "功效"],
        "{name}壯腰補腎！腰酸腎虛、精力不足——傳統海狗方，男性進補之選。",
    ),
    (
        ["九心", "心丹"],
        "heart",
        "九心丹・護心安神",
        [
            "心悸、胸悶、氣短，令你擔心心臟負擔？",
            "中老年想主動護心，日常保健？",
        ],
        [
            "傳統護心思路，日常保養心臟機能",
            "紓緩心悸胸悶關注帶來的不安",
            "適合中老年長期護心方案",
            "依包裝服用，穩妥安心",
        ],
        ["心悸胸悶", "氣短", "中老年護心", "心臟保健"],
        ["九心丹", "護心", "心臟保健", "心悸", "胸悶", "功效"],
        "{name}護心安神！心悸胸悶、氣短關注——日常護心，給心臟多一份守護。",
    ),
]

DEFAULT = (
    "general",
    "盈康養生・對症強效護理",
    [
        "搵嚟搵去都未搵到真正對症嘅產品？",
        "痛楚／不適反覆，影響工作睡眠同生活質素？",
        "想要說明清楚、功效講得明、買得安心？",
    ],
    [
        "對應筋骨、清熱、鼻敏、睡眠、消化等多種養生需求",
        "功效同適用情境本頁寫齊，方便你對號入座",
        "HKTVmall／WhatsApp 雙通路，庫存規格即查",
        "盈康產品線齊全，一次解決你嘅痛點",
    ],
    ["日常養生", "對症護理", "香港保健", "功效查詢"],
    ["盈康", "ykimed", "香港保健", "養生產品", "膏布", "口服膠囊", "功效", "邊度買"],
    "{name}對症強效護理！痛點、功效、適用一次睇晒——選對產品，問題先會真正改善。",
)


def categorize_name(name: str) -> str:
    t = name
    if any(k in t for k in ("滑鼠", "喇叭", "收納袋", "本命佛", "朱砂", "溫度計", "額探", "紅茶")):
        return "周邊家品"
    if ("貼布" in t or "膏布" in t or "電氣石" in t):
        return "膏布外用"
    if any(k in t for k in ("套裝", "組合")) or (("＋" in t or "+" in t) and any(
        k in t for k in ("丸", "油", "膏布", "炎必清", "活絡靈", "痛油")
    )):
        return "套裝優惠"
    if any(k in t for k in ("噴霧", "痛油", "靈油", "活絡油", "神油", "滴膚", "膚特靈", "Difugen")):
        return "噴霧滴劑"
    if re.search(r"\d+\s*ml", t, re.I) and any(k in t for k in ("油", "追風")):
        return "噴霧滴劑"
    return "口服膠囊"


def pick_theme(name: str) -> tuple:
    for keys, tid, label, pains, bens, uses, kws, lead in THEMES:
        if any(k in name for k in keys):
            return tid, label, pains, bens, uses, kws, lead
    cat = categorize_name(name)
    if cat == "膏布外用":
        return pick_theme("膏布專用")
    if cat == "噴霧滴劑":
        return pick_theme("痛油專用")
    if cat == "周邊家品":
        return (
            "peripheral",
            "盈康生活周邊",
            ["需要同養生產品一併選購的生活用品？", "想送禮或家居備用不想分開落單？"],
            ["與盈康健康產品同一客服通路，一次辦妥", "規格清楚，WhatsApp 可即查現貨", "適合家居備用、送禮、出行"],
            ["家居備用", "送禮", "一併選購"],
            ["盈康周邊", "香港養生店", name.replace(" ", "")],
            "{name}——盈康店舖同步周邊，連健康產品一次選購最方便。",
        )
    if cat == "套裝優惠":
        return (
            "bundle",
            "超值套裝・內外夾擊",
            ["單買太麻煩，想一次備齊相關護理？", "痛點需要口服＋外用同時出擊？"],
            [
                "組合相關強效單品，內外夾擊更徹底",
                "慳時間、更抵買，適合家人分享與週期護理",
                "各件依包裝用法，針對同一痛點多角度護理",
                "套裝搜尋熱門：超值、組合、雙效、贈品",
            ],
            ["一次買齊", "內外夾擊", "家人分享", "週期護理"],
            ["套裝", "組合裝", "超值", "盈康套裝", "膏布組合", "功效套裝"],
            "{name}超值組合！痛點一次打盡——口服外用配齊，效果更強、更划算。",
        )
    return DEFAULT


def esc(s: str) -> str:
    return htmlmod.escape(s, quote=True)


def build_efficacy_html(name: str) -> str:
    tid, label, pains, bens, uses, kws, lead = pick_theme(name)
    lead_txt = lead.format(name=name)
    base = re.sub(r"\s*\d+.*$", "", name).strip()
    kw_list: list[str] = []
    for k in [name, base, f"{base}功效", f"{base}好處", f"{base}邊度買", "痛點", "功效", "好處"] + list(kws):
        if k and k not in kw_list:
            kw_list.append(k)
    kw_list = kw_list[:28]
    pains_li = "\n".join(f"          <li>{esc(x)}</li>" for x in pains)
    bens_li = "\n".join(f"          <li>{esc(x)}</li>" for x in bens)
    uses_li = "\n".join(f"          <li>{esc(x)}</li>" for x in uses)
    kw_span = "、".join(esc(k) for k in kw_list)
    return f"""{MARKER_START}
  <div class="lf-section" id="pdp-efficacy" data-theme="{esc(tid)}">
    <h2>痛點・功效・<span class="accent">好處</span></h2>
    <p class="pdp-eff-lead">{esc(lead_txt)}</p>
    <p class="pdp-eff-label">{esc(label)}</p>
    <div class="pdp-eff-grid pdp-eff-grid-3">
      <div class="pdp-eff-col pdp-eff-pain">
        <h3>痛點：你是否正受這些困擾？</h3>
        <ul class="pdp-bullets">
{pains_li}
        </ul>
      </div>
      <div class="pdp-eff-col pdp-eff-benefit">
        <h3>功效／好處（強效重點）</h3>
        <ul class="pdp-bullets">
{bens_li}
        </ul>
      </div>
      <div class="pdp-eff-col pdp-eff-use">
        <h3>適用情境</h3>
        <ul class="pdp-bullets">
{uses_li}
        </ul>
      </div>
    </div>
    <p class="pdp-kw"><strong>相關搜尋關鍵字：</strong>{kw_span}</p>
  </div>
{MARKER_END}
"""


def build_meta(name: str, price: str | None) -> str:
    tid, label, pains, bens, uses, kws, lead = pick_theme(name)
    meta = (
        f"{name} — {label}。"
        f"痛點：{'、'.join(uses[:3])}。"
        f"功效好處：{'、'.join(kws[:5])}。"
        f"盈康・WhatsApp 6222 7238"
    )
    if price:
        meta += f"。{price}"
    meta = re.sub(r"\s+", " ", meta).strip()
    if len(meta) > 165:
        meta = meta[:162].rstrip() + "…"
    return meta


def format_diag_paragraph(raw: str) -> str:
    text = re.sub(r"\s+", " ", raw).strip()
    if len(text) < 40:
        return f"<p>{esc(text)}</p>"
    parts = re.split(r"(?:^|[・‧]\s*|\s*[-–—]\s*|(?<=[。；])\s*)", text)
    parts = [p.strip(" 　;；") for p in parts if p and len(p.strip()) > 1]
    if len(parts) <= 2 and len(text) > 120:
        text2 = text
        for hdr in ("適合範圍", "產品特性", "用法", "注意事項", "特效成份", "特效成分",
                    "服法", "貯藏", "產品核心賣點", "使用方法", "建議服用量", "規格與儲存"):
            text2 = text2.replace(hdr, f"。\n【{hdr}】")
        chunks = [c.strip(" 。") for c in text2.split("。") if c.strip()]
        paras = []
        for c in chunks:
            if c.startswith("【") and "】" in c:
                title, _, rest = c.partition("】")
                title = title[1:]
                if rest.strip():
                    paras.append(f"<p><strong>{esc(title)}</strong> — {esc(rest.strip())}</p>")
                else:
                    paras.append(f"<p><strong>{esc(title)}</strong></p>")
            else:
                paras.append(f"<p>{esc(c)}。</p>")
        return "\n        ".join(paras[:12])
    if len(parts) >= 4:
        items = "".join(f"<li>{esc(p)}</li>" for p in parts[:14])
        return f'<ul class="pdp-bullets">{items}</ul>'
    return f"<p>{esc(text)}</p>"


def extract_price(html: str) -> str | None:
    m = re.search(r'class="price-now">([^<]+)', html)
    if m:
        return m.group(1).strip()
    m = re.search(r"<tr><th>售價</th><td>([^<]+)</td>", html)
    if m:
        return m.group(1).strip()
    return None


def strip_old_efficacy(html: str) -> str:
    html = re.sub(
        rf"\s*{re.escape(MARKER_START)}.*?{re.escape(MARKER_END)}\s*",
        "\n",
        html,
        flags=re.S,
    )
    html = re.sub(
        r'\s*<div class="lf-section" id="pdp-efficacy"[^>]*>.*?</div>\s*',
        "\n",
        html,
        flags=re.S,
    )
    return html


def inject_efficacy(html: str, block: str) -> str:
    html = strip_old_efficacy(html)
    m = re.search(r'<div class="lf-section">\s*\n\s*<h2>您是否有以下', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    m = re.search(r'<div class="lf-section" id="pdp-tabs">', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    m = re.search(r'<div class="lf-section">\s*\n\s*<h2>為什麼需要', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    m = re.search(r'<div class="lf-bottom-cta">', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    return html + "\n" + block


def update_meta(html: str, meta: str) -> str:
    if re.search(r'name="description" content="', html):
        return re.sub(
            r'(<meta name="description" content=")[^"]*(")',
            rf"\1{esc(meta)}\2",
            html,
            count=1,
        )
    return re.sub(
        r"(</title>\s*)",
        rf'\1<meta name="description" content="{esc(meta)}">\n',
        html,
        count=1,
    )


def update_title(html: str, name: str) -> str:
    _, label, *_ = pick_theme(name)
    new_title = f"{name}｜{label}｜功效好處｜盈康"
    if len(new_title) > 48:
        new_title = f"{name}｜{label}｜盈康"
    if len(new_title) > 42:
        new_title = f"{name}｜功效好處｜盈康"
    return re.sub(r"<title>[^<]*</title>", f"<title>{esc(new_title)}</title>", html, count=1)


def enrich_buy_blurb(html: str, name: str) -> str:
    _, _, _, _, _, _, lead = pick_theme(name)
    blurb = lead.format(name=name)
    short = blurb if len(blurb) < 140 else (blurb[:137] + "…")
    if 'class="pdp-buy-blurb"' in html:
        return re.sub(
            r'<p class="pdp-buy-blurb">.*?</p>',
            f'<p class="pdp-buy-blurb">{esc(short)}</p>',
            html,
            count=1,
            flags=re.S,
        )
    pat = r'(<span class="stock">[^<]*</span>\s*)'
    m = re.search(pat, html)
    if not m:
        return html
    return html[: m.end(1)] + f'\n      <p class="pdp-buy-blurb">{esc(short)}</p>' + html[m.end(1) :]


def enrich_diag_text(html: str) -> str:
    def repl2(m):
        h3 = m.group(1)
        pcontent = m.group(2)
        text = re.sub(r"\s+", " ", pcontent).strip()
        if len(text) < 80:
            return m.group(0)
        formatted = format_diag_paragraph(text)
        return f'<div class="diag-text">\n        <h3>{h3}</h3>\n        {formatted}\n      </div>'

    return re.sub(
        r'<div class="diag-text">\s*<h3>([^<]*)</h3>\s*<p>(.*?)</p>\s*</div>',
        repl2,
        html,
        count=1,
        flags=re.S,
    )


def enrich_yanbiqing_tabs(html: str, name: str) -> str:
    if "data-pdp-tabs" not in html:
        return html
    _, _, pains, bens, uses, _, _ = pick_theme(name)
    bullets = bens[:4] + [f"痛點對應：{'、'.join(uses[:3])}"]
    lis = "\n".join(f"          <li>{esc(b)}</li>" for b in bullets)
    return re.sub(
        r'(<div class="pdp-tab-panel is-on" data-panel="intro"[^>]*>\s*<ul class="pdp-bullets">).*?(</ul>)',
        rf"\1\n{lis}\n        \2",
        html,
        count=1,
        flags=re.S,
    )


def ensure_css() -> None:
    css = CSS.read_text(encoding="utf-8")
    block = """
/* ===== PDP efficacy / SEO block (痛點・功效・好處) ===== */
#pdp-efficacy .pdp-eff-lead {
  font-size: 1.08rem; color: #333; line-height: 1.75; max-width: 52em; font-weight: 600;
}
#pdp-efficacy .pdp-eff-label {
  display: inline-block; background: #fff7ef; color: #c45e10;
  font-weight: 800; font-size: 0.85rem; padding: 0.25rem 0.7rem;
  border-radius: 999px; margin: 0.4rem 0 1rem;
}
#pdp-efficacy .pdp-eff-grid {
  display: grid; grid-template-columns: 1fr; gap: 1.2rem;
}
#pdp-efficacy .pdp-eff-grid-3 {
  display: grid; grid-template-columns: 1fr; gap: 1.15rem;
}
@media (min-width: 900px) {
  #pdp-efficacy .pdp-eff-grid-3 { grid-template-columns: 1fr 1fr 1fr; gap: 1.25rem; }
}
@media (min-width: 720px) and (max-width: 899px) {
  #pdp-efficacy .pdp-eff-grid-3 { grid-template-columns: 1fr 1fr; }
}
#pdp-efficacy .pdp-eff-col {
  background: #fffaf5; border: 1px solid #f0d0b0; border-radius: 8px; padding: 1rem 1.05rem;
}
#pdp-efficacy .pdp-eff-benefit {
  background: #fff5eb; border-color: #e87722;
}
#pdp-efficacy .pdp-eff-col h3 {
  margin: 0 0 0.55rem; font-size: 0.98rem; color: #333;
}
#pdp-efficacy .pdp-kw {
  margin-top: 1.15rem; padding: 0.9rem 1rem; background: #f7fafc;
  border-left: 4px solid #3a9bb8; font-size: 0.9rem; line-height: 1.7; color: #555;
}
.pdp-buy-blurb {
  margin-top: 0.85rem; color: #333; line-height: 1.7; font-size: 0.98rem; font-weight: 600;
}
"""
    # replace old block if present
    if "#pdp-efficacy .pdp-eff-lead" in css:
        css = re.sub(
            r"/\* ===== PDP efficacy / SEO block.*?\.pdp-buy-blurb \{[^}]+\}\n",
            block.lstrip() + "\n",
            css,
            count=1,
            flags=re.S,
        )
    else:
        css = css.rstrip() + "\n" + block
    CSS.write_text(css, encoding="utf-8")


def process_file(path: Path) -> bool:
    if path.name == "index.html":
        return False
    html = path.read_text(encoding="utf-8")
    m = re.search(r"<h1>([^<]+)</h1>", html)
    if not m:
        return False
    name = m.group(1).strip()
    price = extract_price(html)
    block = build_efficacy_html(name)
    new = html
    new = update_title(new, name)
    new = update_meta(new, build_meta(name, price))
    new = enrich_buy_blurb(new, name)
    new = enrich_diag_text(new)
    new = enrich_yanbiqing_tabs(new, name)
    new = inject_efficacy(new, block)
    new = re.sub(
        r'(href="[^"]*assets/site\.css)\?v=[^"]*"',
        r'\1?v=20261021f"',
        new,
    )
    # never reintroduce banned brand phrase
    new = new.replace("香港本地品牌", "盈康")
    new = new.replace("香港本地健康品牌", "盈康")
    if new != html:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    ensure_css()
    updated = []
    for path in sorted(PRODUCTS.glob("*.html")):
        if process_file(path):
            updated.append(path.name)
    print(f"updated {len(updated)} pages")
    for n in updated[:6]:
        print(" ", n)
    if len(updated) > 6:
        print(f"  ... +{len(updated)-6} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
