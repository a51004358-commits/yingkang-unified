#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich product PDPs with free-form efficacy copy + SEO keywords (private site).

Idempotent: replaces existing #pdp-efficacy blocks. Does not invent registrations
or lab reports. Does expand symptom/benefit/search phrases freely.
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

# (match_keywords_in_name, theme_id, display_label, benefits[], use_cases[], search_kws[], lead_template)
# lead_template may include {name}
THEMES: list[tuple] = [
    (
        ["炎必清"],
        "yanbiqing",
        "清熱養生・口服膠囊",
        [
            "針對都市人上火、咽喉乾燥、暗瘡反覆、口臭與作息紊亂引起的不適感",
            "穿心蓮、紫錐花、蒲公英、香蜂草等草本配方，日常清熱解毒、調理體質",
            "適合熬夜、飲食油膩、換季敏感時作為口服養生補充",
            "香港製造，規格清楚，可於 HKTVmall 或 WhatsApp 查詢庫存",
        ],
        ["暗瘡發炎", "咽喉腫痛", "口乾口苦", "上火濕熱", "免疫力下降", "換季不適"],
        [
            "炎必清", "強力炎必清", "清熱解毒", "暗瘡", "咽喉", "上火", "草本膠囊",
            "穿心蓮", "紫錐花", "蒲公英", "香港製造保健", "盈康炎必清",
        ],
        "{name}專為清熱解毒、舒緩上火與咽喉不適而設。草本口服膠囊，適合想改善暗瘡、濕熱、免疫力與日常養生節奏的人士搜尋選購。",
    ),
    (
        ["鼻炎"],
        "biyan",
        "鼻敏感・呼吸道舒緩",
        [
            "針對天氣轉變、塵蟣、冷氣房引起的鼻塞、流鼻水、鼻癢與鼻敏感",
            "每日口服補充，幫助維持鼻腔舒適、暢通呼吸與睡眠質素",
            "適合換季、辦公室冷氣環境、鼻敏感反覆發作人士",
            "溫和配方，不引致嗜睡，方便長期日常保養",
        ],
        ["鼻敏感", "鼻塞", "流鼻水", "打噴嚏", "鼻癢", "換季鼻炎", "塵蟣過敏"],
        [
            "鼻炎素", "鼻敏感", "鼻塞", "流鼻水", "過敏性鼻炎", "換季鼻炎",
            "鼻腔護理", "呼吸道", "香港鼻敏感產品",
        ],
        "{name}專注鼻部敏感與呼吸道舒適。適合搜尋鼻敏感、鼻塞、流鼻水、換季鼻炎時作為日常口服舒緩選擇。",
    ),
    (
        ["久咳", "咳丸", "咳調理"],
        "cough",
        "久咳痰多・氣管調理",
        [
            "針對久咳不癒、痰多、氣管敏感、夜間咳嗽影響睡眠",
            "傳統調理思路結合日常口服方便性，幫助舒緩咳嗽不適、潤肺化痰",
            "適合轉季咳嗽、煙塵環境、氣管敏感人士作為調理補充",
            "可與生活作息調整一併使用，查詢庫存可 WhatsApp 盈康客服",
        ],
        ["久咳", "痰多", "氣管敏感", "夜間咳嗽", "轉季咳嗽", "喉嚨痕"],
        [
            "久咳丸", "強力特效久咳丸", "咳嗽", "化痰", "氣管", "潤肺",
            "久咳不癒", "止咳", "香港咳嗽產品",
        ],
        "{name}針對久咳、痰多與氣管不適。適合搜尋止咳化痰、久咳不癒、氣管敏感時選購的口服調理產品。",
    ),
    (
        ["膏布", "貼布", "電氣石"],
        "plaster",
        "外用膏布・筋骨舒緩",
        [
            "外用貼敷，針對腰酸背痛、坐骨神經痛、頸膊痛、肌肉酸痛、風濕關節痛",
            "配方著重滲透與溫熱／清涼舒緩，成分可經皮膚到達肌肉深處",
            "粘性適中、貼完易撕，適合久坐、長途駕駛、運動後與長輩日常護理",
            "一條根、艾草等經典外用成分敘述，港人常用搜尋關鍵字齊備",
        ],
        ["腰酸背痛", "坐骨神經痛", "頸緊膊痛", "肌肉酸痛", "風濕痛", "運動扭傷", "關節僵硬"],
        [
            "坐骨神經膏布", "一條根膏布", "腰背痛貼布", "止痛貼", "鎮痛貼",
            "頸椎痛", "肩周炎貼布", "風濕膏布", "舒筋活絡", "外用貼布香港",
        ],
        "{name}為外用膏布，針對腰腿、頸膊、坐骨與肌肉酸痛。適合搜尋一條根、止痛貼、坐骨神經痛、舒筋活絡時選購。",
    ),
    (
        ["骨剌", "骨刺", "風澀", "風痛骨", "骨痛靈", "骨痛"],
        "joint_oral",
        "關節骨刺・筋骨口服",
        [
            "針對關節炎、骨刺、腰酸背痛、四肢麻木、氣血不通、伸屈不順",
            "幫助促進末梢循環與新陳代謝，維持神經肌肉日常舒適",
            "適合長時間坐立、天氣轉涼關節僵硬、手足麻痹震軟人士",
            "純天然物質思路敘述，日常口服保養關節筋骨",
        ],
        ["關節炎", "骨刺", "腰酸背痛", "四肢麻木", "坐骨腰痛", "腰椎勞損", "風濕骨痛"],
        [
            "風澀骨剌丹", "骨刺丹", "關節炎", "風濕", "末梢循環", "筋骨保健",
            "腰腿麻木", "骨痛靈", "香港關節保健",
        ],
        "{name}專注關節、骨刺與筋骨不適。適合搜尋風濕、骨刺、腰酸背痛、四肢麻木、末梢循環時作為口服調理。",
    ),
    (
        ["坐骨", "腰痛丸", "腰痛油", "通丸", "神徑痛丸", "神經痛丸"],
        "sciatica",
        "坐骨腰痛・腰腿調理",
        [
            "針對坐骨神經痛、腰痛、臀腿放射痛、腰腿酸麻、久坐不適",
            "口服／外用產品線齊備，幫助舒緩腰腿僵硬、促進局部舒適與活動力",
            "適合司機、辦公室久坐、長者腰腿乏力與天氣轉涼發作人士",
            "可與膏布、痛油搭配使用，一次搜尋坐骨、腰痛關鍵字即可對應",
        ],
        ["坐骨神經痛", "腰痛", "腰腿麻痹", "臀痛", "腰椎勞損", "久坐腰痛"],
        [
            "坐骨神經痛", "坐骨神經丸", "腰痛丸", "腰腿痛", "腰椎",
            "坐骨痛油", "香港坐骨產品", "久坐腰痛",
        ],
        "{name}針對坐骨神經痛與腰腿不適。適合搜尋坐骨痛、腰痛、腰腿麻痹、腰椎勞損時選購。",
    ),
    (
        ["痛油", "靈油", "活絡油", "追風", "神油", "破痛", "楓濕"],
        "oil",
        "活絡痛油・外用按摩",
        [
            "外用活絡油／痛油，針對風濕痛、肩頸僵硬、腰腿酸痛、運動後肌肉緊繃",
            "塗抹按摩後帶來溫熱或清涼舒緩感，幫助舒筋活絡、促進局部循環",
            "適合辦公室肩頸、天氣潮濕風痛、運動前後護理",
            "便攜瓶裝，家居與出行皆宜；避免接觸眼睛與破損皮膚",
        ],
        ["風濕痛", "肩頸酸痛", "腰腿酸痛", "肌肉緊繃", "活絡按摩", "天氣潮濕不適"],
        [
            "活絡油", "追風油", "坐骨痛油", "風濕油", "肩頸油", "外用按摩油",
            "舒筋活絡油", "千里追風", "香港活絡油",
        ],
        "{name}為外用活絡／痛油，針對風濕、肩頸與腰腿酸痛。適合搜尋活絡油、追風油、按摩油時選購。",
    ),
    (
        ["滅濕痛", "濕痛"],
        "mieshitong",
        "滅濕痛・風濕外用",
        [
            "針對風濕痛、濕重關節酸脹、天氣潮濕引起的筋骨不適",
            "膏布／油劑外用，貼敷或塗抹於患處，幫助舒緩酸痛僵硬",
            "適合潮濕季節、長者關節、反覆風痛濕痛人士",
            "多規格可選，方便對應不同部位覆蓋需要",
        ],
        ["風濕痛", "濕重", "關節酸脹", "天氣潮濕痛", "筋骨僵硬"],
        [
            "滅濕痛", "風痛膏布", "濕痛", "風濕貼", "潮濕關節痛", "香港風濕產品",
        ],
        "{name}針對風濕濕痛與關節酸脹。適合搜尋滅濕痛、風濕膏布、潮濕天氣筋骨痛時選購。",
    ),
    (
        ["膚特靈", "滴膚", "Difugen", "difugen"],
        "skin",
        "皮膚保濕・外用護理",
        [
            "針對皮膚乾燥、緊繃、脫屑、冷氣房缺水與入秋轉涼肌膚不適",
            "外用噴霧／滴劑，方便補水保濕、維持皮膚屏障舒適",
            "適合辦公室冷氣環境、敏感乾燥肌、日常保濕節奏",
            "便攜規格，可放手袋或案頭隨時護理",
        ],
        ["皮膚乾燥", "脫屑", "冷氣房乾燥", "保濕", "皮膚緊繃", "入秋乾肌"],
        [
            "膚特靈", "滴膚堅", "保濕噴霧", "皮膚乾燥", "香港保濕", "外用保濕",
        ],
        "{name}專注皮膚保濕與乾燥舒緩。適合搜尋保濕噴霧、皮膚乾燥、冷氣房乾肌時選購。",
    ),
    (
        ["牛黃", "安宮"],
        "niuhuang",
        "牛黃清熱・傳統名方",
        [
            "傳統安宮牛黃／牛黃解毒思路，針對熱盛、心煩、咽喉腫痛、神疲等不適敘述",
            "適合關注清熱解毒、應急備用與傳統中成藥文化的人士了解選購",
            "規格多樣（單丸／多丸／膠囊），請依包裝說明與個人需要選擇",
            "香港通路可查，WhatsApp 可確認批次與庫存",
        ],
        ["清熱解毒", "咽喉腫痛", "心煩上火", "應急備用", "傳統中成藥"],
        [
            "安宮牛黃丸", "牛黃解毒", "清熱", "中成藥", "北京安宮牛黃丸", "牛黃膠囊",
        ],
        "{name}屬傳統牛黃清熱系列。適合搜尋安宮牛黃丸、牛黃解毒、清熱時了解規格與選購。",
    ),
    (
        ["靈芝", "腦活", "腦白金", "腦"],
        "brain",
        "腦部活力・靈芝保健",
        [
            "針對精神疲勞、專注力下降、睡眠質素欠佳與日常腦力負擔",
            "靈芝、腦活素等保健敘述，幫助維持精神清醒與抗氧化日常",
            "適合長時間用腦、加班、中老年腦部保健關注人士",
            "口服膠囊方便，可納入長期養生計劃",
        ],
        ["精神疲勞", "專注力", "腦力保健", "睡眠質素", "抗氧化"],
        [
            "靈芝", "腦活素", "腦白金", "腦保健", "精神疲勞", "香港靈芝",
        ],
        "{name}專注腦部活力與靈芝保健。適合搜尋靈芝、腦活素、精神疲勞、腦保健時選購。",
    ),
    (
        ["六味", "地黃"],
        "liuwei",
        "六味地黃・滋陰補腎",
        [
            "經典六味地黃思路，針對腰膝酸軟、陰虛內熱、夜尿、头晕耳鳴等日常關注",
            "滋陰補腎、強健腰膝的傳統保健方向，適合中老年長期調理",
            "大包裝粒數方便持續服用，請依包裝用量",
            "港人熟知搜尋關鍵字：六味地黃丸、補腎、陰虛",
        ],
        ["腰膝酸軟", "陰虛", "夜尿", "頭暈耳鳴", "補腎養生"],
        [
            "六味地黃丸", "補腎", "陰虛", "腰膝酸軟", "中老年保健", "地黃丸香港",
        ],
        "{name}為六味地黃滋陰補腎系列。適合搜尋六味地黃丸、補腎、腰膝酸軟時選購。",
    ),
    (
        ["尿酸"],
        "uric",
        "尿酸調理・代謝保健",
        [
            "針對尿酸偏高關注、關節忽然紅腫熱痛風險與飲食油膩嘌呤偏高生活",
            "幫助日常代謝調理、關節舒適維護",
            "適合應酬飲食多、家族有尿酸關注、想主動保健人士",
            "口服方便，可與清淡飲食、多喝水習慣一併執行",
        ],
        ["尿酸高", "痛風關注", "嘌呤", "關節紅腫", "代謝調理"],
        [
            "尿酸清", "尿酸高", "痛風", "降尿酸", "嘌呤飲食", "香港尿酸產品",
        ],
        "{name}針對尿酸與代謝調理。適合搜尋尿酸高、痛風、降尿酸時作為日常保健選擇。",
    ),
    (
        ["脈通", "通血"],
        "vessel",
        "血管循環・脈通保健",
        [
            "針對血液循環欠佳、手脚冰冷、胸悶氣短關注與中老年血管保健",
            "幫助維持脈絡暢通、日常活力與末梢溫暖感",
            "適合久坐少動、血脂關注、天氣轉涼手腳凍人士",
            "口服調理，長期節奏比臨時抱佛腳更穩妥",
        ],
        ["血液循環", "手脚冰冷", "血管保健", "胸悶關注", "末梢循環"],
        [
            "脈通", "通血丸", "血液循環", "血管", "手脚冰冷", "香港循環保健",
        ],
        "{name}專注血液循環與脈絡保健。適合搜尋脈通、通血、手脚冰冷、血管保健時選購。",
    ),
    (
        ["健齒", "牙"],
        "teeth",
        "牙齦口腔・健齒保健",
        [
            "針對牙齦鬆動關注、牙齒敏感、口腔異味與牙周日常保養",
            "由內而外補充口腔所需營養，幫助牙齦緊緻、口氣清新",
            "適合牙齒敏感、牙齦出血關注、重視笑容與口腔衛生人士",
            "餐後溫水送服，配合正確刷牙習慣效果更穩",
        ],
        ["牙齦健康", "牙齒敏感", "口氣清新", "牙周保養", "口腔異味"],
        [
            "健齒靈", "牙齦", "牙齒敏感", "口氣", "口腔保健", "香港健齒",
        ],
        "{name}專注牙齦與口腔保健。適合搜尋牙齒敏感、牙齦、口氣清新、口腔保健時選購。",
    ),
    (
        ["想睡", "睡眠", "睡"],
        "sleep",
        "助眠安神・睡眠節奏",
        [
            "針對入睡困難、淺睡易醒、精神緊張與作息紊亂",
            "幫助放鬆心情、改善睡眠節奏，讓身心更容易進入休息狀態",
            "適合加班族、思緒繁多、換地睡眠不穩人士",
            "建議固定睡前服用節奏，配合減少藍光與咖啡因",
        ],
        ["失眠", "入睡困難", "淺睡", "安神", "睡眠質素"],
        [
            "想睡就睡", "助眠", "失眠", "安神", "改善睡眠", "香港助眠產品",
        ],
        "{name}針對睡眠與安神需求。適合搜尋助眠、失眠、入睡困難、改善睡眠時選購。",
    ),
    (
        ["花塔糖", "開胃", "消化"],
        "digest",
        "開胃消化・腸胃舒適",
        [
            "針對食慾不振、消化不良、小朋友偏食與飯後脹氣",
            "傳統花塔糖口味親切，幫助開胃健脾、促進消化舒適",
            "適合小朋友、長者、病後胃口差、旅遊水土不服關注",
            "多支裝方便家庭分享與外出攜帶",
        ],
        ["開胃", "消化不良", "偏食", "飯後脹氣", "食慾不振"],
        [
            "花塔糖", "開胃", "消化", "健脾", "小孩偏食", "香港花塔糖",
        ],
        "{name}為開胃消化系列。適合搜尋花塔糖、開胃、消化不良、偏食時選購。",
    ),
    (
        ["活絡靈"],
        "huoluo",
        "活絡靈・筋骨口服",
        [
            "針對筋骨酸痛、活動欠靈活、風濕關節日常不適",
            "口服活絡思路，與外用活絡油可互補護理",
            "適合天氣轉變筋骨響、運動恢復期、中老年關節保養",
            "可搜尋活絡靈、筋骨保健、風濕調理等關鍵字找到本頁",
        ],
        ["筋骨酸痛", "關節不靈活", "風濕", "運動恢復", "天氣轉涼僵硬"],
        [
            "活絡靈", "筋骨保健", "風濕調理", "關節靈活", "香港活絡",
        ],
        "{name}專注筋骨活絡口服調理。適合搜尋活絡靈、筋骨酸痛、風濕關節時選購。",
    ),
    (
        ["百痛敵"],
        "baitongdi",
        "百痛敵・綜合酸痛",
        [
            "針對全身多處酸痛、風濕關節、腰腿肩頸綜合不適",
            "一瓶對應多種日常痛楚關注，方便不想同時買多種單品的人士",
            "適合痛點分散、天氣敏感、需要綜合舒緩的使用者",
            "搜尋百痛敵、全身酸痛、風濕止痛等詞可直達本產品",
        ],
        ["全身酸痛", "風濕", "腰腿痛", "肩頸痛", "綜合舒緩"],
        [
            "百痛敵", "全身酸痛", "風濕痛", "綜合止痛", "香港百痛敵",
        ],
        "{name}針對多處酸痛與風濕不適。適合搜尋百痛敵、全身酸痛、風濕痛時選購。",
    ),
    (
        ["健步", "虎潛"],
        "jianbu",
        "健步虎潛・腰腿強健",
        [
            "針對腰膝無力、步行乏力、中老年筋骨衰退關注",
            "傳統虎潛／健步思路，幫助強健腰膝、穩定步履",
            "大包裝適合長期調理節奏",
            "搜尋健步虎潛丸、腰膝無力、中老年強筋骨可找到本頁",
        ],
        ["腰膝無力", "步行乏力", "中老年保健", "強筋健骨"],
        [
            "健步虎潛丸", "腰膝", "強筋健骨", "中老年", "步行無力",
        ],
        "{name}針對腰膝無力與步行乏力。適合搜尋健步虎潛丸、強筋健骨時選購。",
    ),
    (
        ["蕥歡", "疲勞", "抗疲"],
        "fatigue",
        "抗疲勞・午後活力",
        [
            "針對精神疲勞、午後昏睡、體力透支與壓力大",
            "幫助回復日常活力、維持工作學習狀態",
            "適合長工時、照顧家庭、考試備戰人士",
            "搜尋抗疲勞、提神、體力補充可對應本產品方向",
        ],
        ["精神疲勞", "午後昏睡", "體力透支", "壓力大"],
        [
            "抗疲勞", "提神", "體力", "精神疲勞", "午後疲勞",
        ],
        "{name}針對精神疲勞與體力透支。適合搜尋抗疲勞、提神、午後昏睡時選購。",
    ),
    (
        ["海狗", "五鞭"],
        "haigou",
        "海狗丸・壯腰補腎",
        [
            "針對腰膝酸軟、腎虛關注、男性保健與精力不足敘述",
            "傳統海狗／五鞭補腎思路，適合想壯腰補腎的人士了解",
            "大包裝粒數方便持續食用",
            "搜尋海狗丸、補腎、壯腰、男性保健可到達本頁",
        ],
        ["腰膝酸軟", "腎虛", "男性保健", "精力", "壯腰"],
        [
            "海狗丸", "五鞭海狗", "補腎", "壯腰", "男性保健",
        ],
        "{name}為海狗補腎壯腰系列。適合搜尋海狗丸、補腎、男性保健時選購。",
    ),
    (
        ["九心", "心丹"],
        "heart",
        "九心丹・心臟保健",
        [
            "針對心悸關注、胸悶、氣短與中老年心臟日常保健",
            "傳統心臟保健敘述方向，適合想主動護心人士",
            "請依包裝用量，有不適應及時咨詢專業人士",
            "搜尋九心丹、護心、心臟保健可找到本產品",
        ],
        ["心悸", "胸悶", "護心", "氣短", "中老年心臟保健"],
        [
            "九心丹", "護心", "心臟保健", "心悸", "胸悶",
        ],
        "{name}專注心臟日常保健。適合搜尋九心丹、護心、心悸胸悶時選購。",
    ),
]

DEFAULT_THEME = (
    "general",
    "盈康健康・日常養生",
    [
        "盈康香港本地健康品牌產品，說明清楚、通路可查（HKTVmall／WhatsApp）",
        "可依個人筋骨、口服、外用或套裝需要選購，功效與適用說明見本頁",
        "適合關注養生保健、風濕筋骨、清熱、鼻敏感、睡眠消化等關鍵字的訪客",
        "庫存與規格請以包裝及客服確認；本站以瀏覽查詢為主",
    ],
    ["日常養生", "保健產品", "香港品牌", "HKTVmall盈康"],
    [
        "盈康", "ykimed", "香港保健", "養生產品", "HKTVmall盈康",
        "風濕", "筋骨", "清熱", "膏布", "口服膠囊",
    ],
    "{name}為盈康目錄產品。本頁整理功效、適用情境與搜尋關鍵字，方便比較選購與 WhatsApp 查詢。",
)


def categorize_name(name: str) -> str:
    t = name
    if any(k in t for k in ("滑鼠", "喇叭", "收納袋", "本命佛", "朱砂", "溫度計", "額探", "紅茶", "電氣石")):
        # 電氣石貼布 is plaster-like but listed in 周邊 sometimes — keep plaster if 貼布
        if "貼布" in t or "膏布" in t:
            return "膏布外用"
        return "周邊家品"
    if any(k in t for k in ("套裝", "組合", "＋", "+")) and any(
        k in t for k in ("丸", "油", "膏布", "炎必清", "活絡靈", "痛油")
    ):
        return "套裝優惠"
    if any(k in t for k in ("膏布", "貼布")):
        return "膏布外用"
    if any(k in t for k in ("噴霧", "痛油", "靈油", "活絡油", "神油", "滴膚", "膚特靈", "Difugen")):
        return "噴霧滴劑"
    if re.search(r"\d+\s*ml", t, re.I) and any(k in t for k in ("油", "追風")):
        return "噴霧滴劑"
    return "口服膠囊"


def pick_theme(name: str) -> tuple:
    for keys, tid, label, bens, uses, kws, lead in THEMES:
        if any(k in name for k in keys):
            return tid, label, bens, uses, kws, lead
    # category fallbacks
    cat = categorize_name(name)
    if cat == "膏布外用":
        return pick_theme("膏布")  # will match plaster
    if cat == "噴霧滴劑":
        return pick_theme("痛油")
    if cat == "周邊家品":
        return (
            "peripheral",
            "生活周邊・店舖同步",
            [
                "盈康店舖生活／養生周邊，與健康產品同一客服通路",
                "適合一併選購、送禮或家居備用",
                "詳情規格見本頁與包裝說明",
                "WhatsApp 6222 7238 可查詢現貨",
            ],
            ["家居備用", "送禮", "店舖周邊"],
            ["盈康周邊", "香港養生店", name.replace(" ", "")],
            "{name}為盈康店舖周邊／生活用品。可於本頁了解規格並經 WhatsApp 或 HKTVmall 選購。",
        )
    if cat == "套裝優惠":
        return (
            "bundle",
            "超值套裝・一次備齊",
            [
                "組合多件相關護理單品，省卻分次選購時間",
                "適合家人分享、週期護理或想一次備齊坐骨／清熱／外用組合的人士",
                "各單品請分別依包裝用法使用",
                "套裝關鍵字：超值、組合、贈品、雙效組",
            ],
            ["一次買齊", "家人分享", "週期護理", "超值組合"],
            ["套裝", "組合裝", "超值", "盈康套裝", "膏布組合", "口服套裝"],
            "{name}為盈康超值組合。適合想一次備齊相關功效產品、搜尋套裝組合時選購。",
        )
    tid, label, bens, uses, kws, lead = DEFAULT_THEME
    return tid, label, bens, uses, kws, lead


def esc(s: str) -> str:
    return htmlmod.escape(s, quote=True)


def build_efficacy_html(name: str) -> str:
    tid, label, bens, uses, kws, lead = pick_theme(name)
    lead_txt = lead.format(name=name)
    # ensure product name variants in keywords
    base = re.sub(r"\s*\d+.*$", "", name).strip()
    kw_list = []
    for k in [name, base, "功效", "適用", "邊度買", "香港"] + kws:
        if k and k not in kw_list:
            kw_list.append(k)
    kw_list = kw_list[:18]
    bens_li = "\n".join(f"          <li>{esc(b)}</li>" for b in bens)
    uses_li = "\n".join(f"          <li>{esc(u)}</li>" for u in uses)
    kw_span = "、".join(esc(k) for k in kw_list)
    return f"""{MARKER_START}
  <div class="lf-section" id="pdp-efficacy" data-theme="{esc(tid)}">
    <h2>功效與<span class="accent">適用</span></h2>
    <p class="pdp-eff-lead">{esc(lead_txt)}</p>
    <p class="pdp-eff-label">{esc(label)}</p>
    <div class="pdp-eff-grid">
      <div>
        <h3>主要功效重點</h3>
        <ul class="pdp-bullets">
{bens_li}
        </ul>
      </div>
      <div>
        <h3>常見適用情境</h3>
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
    tid, label, bens, uses, kws, lead = pick_theme(name)
    bits = [name, label, "、".join(uses[:4]), "、".join(kws[:6]), "盈康香港"]
    if price:
        bits.append(price)
    bits.append("WhatsApp 6222 7238")
    meta = " — ".join([bits[0], f"{bits[1]}。適用：{bits[2]}。搜尋：{bits[3]}。{bits[4]}"])
    if price:
        meta += f"。{price}"
    meta += "。WhatsApp 6222 7238"
    meta = re.sub(r"\s+", " ", meta).strip()
    if len(meta) > 160:
        meta = meta[:157].rstrip() + "…"
    return meta


def format_diag_paragraph(raw: str) -> str:
    """Turn wall-of-text HKTVmall paste into readable paragraphs/lists."""
    text = re.sub(r"\s+", " ", raw).strip()
    if len(text) < 40:
        return f"<p>{esc(text)}</p>"
    # Split on common bullet markers
    parts = re.split(r"(?:^|[・‧]\s*|\s*[-–—]\s*|(?<=[。；])\s*)", text)
    parts = [p.strip(" 　;；") for p in parts if p and len(p.strip()) > 1]
    # If still one blob, split by Chinese commas clusters of symptoms
    if len(parts) <= 2 and len(text) > 120:
        # insert breaks before known headers
        text2 = text
        for hdr in ("適合範圍", "產品特性", "用法", "注意事項", "特效成份", "特效成分",
                    "服法", "貯藏", "產品核心賣點", "使用方法", "建議服用量", "規格與儲存",
                    "🌟", "📋", "📦"):
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
    # list style
    if len(parts) >= 4:
        items = "".join(f"<li>{esc(p)}</li>" for p in parts[:14])
        return f"<ul class=\"pdp-bullets\">{items}</ul>"
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
    # Prefer before "您是否有以下困擾"
    m = re.search(r'<div class="lf-section">\s*\n\s*<h2>您是否有以下', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    # yanbiqing / tab pages: before #pdp-tabs or after detail images
    m = re.search(r'<div class="lf-section" id="pdp-tabs">', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    m = re.search(r'<div class="lf-section">\s*\n\s*<h2>為什麼需要', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    # before bottom CTA
    m = re.search(r'<div class="lf-bottom-cta">', html)
    if m:
        return html[: m.start()] + "\n" + block + "\n" + html[m.start() :]
    m = re.search(r"</div>\s*\n<div class=\"footer", html)
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
    # insert after title
    return re.sub(
        r"(</title>\s*)",
        rf'\1<meta name="description" content="{esc(meta)}">\n',
        html,
        count=1,
    )


def update_title(html: str, name: str) -> str:
    tid, label, *_ = pick_theme(name)
    new_title = f"{name}｜{label}｜盈康"
    if len(new_title) > 40:
        new_title = f"{name}｜功效適用｜盈康"
    return re.sub(r"<title>[^<]*</title>", f"<title>{esc(new_title)}</title>", html, count=1)


def enrich_buy_blurb(html: str, name: str) -> str:
    """Add/replace a short blurb under price if missing or Cap-soft."""
    tid, label, bens, uses, kws, lead = pick_theme(name)
    blurb = lead.format(name=name)
    short = blurb if len(blurb) < 120 else (blurb[:117] + "…")
    # existing muted / style blurb right after stock
    pat = r'(<span class="stock">[^<]*</span>\s*)(<p[^>]*>.*?</p>)?'
    m = re.search(pat, html, flags=re.S)
    if not m:
        return html
    replacement = (
        m.group(1)
        + f'\n      <p class="pdp-buy-blurb">{esc(short)}</p>'
    )
    # if group 2 exists and looks like soft/disclaimer leftover, replace; if useful long copy, keep and still ensure blurb
    if m.group(2):
        g2 = m.group(2)
        if any(x in g2 for x in ("一般健康", "並非診斷", "屬一般", "可把草本")) or len(re.sub("<[^>]+>", "", g2)) < 40:
            return html[: m.start()] + replacement + html[m.end() :]
        # keep existing rich p, ensure we don't duplicate blurb
        if 'class="pdp-buy-blurb"' in html:
            return re.sub(
                r'<p class="pdp-buy-blurb">.*?</p>',
                f'<p class="pdp-buy-blurb">{esc(short)}</p>',
                html,
                count=1,
                flags=re.S,
            )
        return html[: m.end(1)] + f'\n      <p class="pdp-buy-blurb">{esc(short)}</p>' + html[m.end(1) :]
    return html[: m.start()] + replacement + html[m.end() :]


def enrich_diag_text(html: str) -> str:
    def repl(m):
        inner = m.group(1)
        # only reformat if looks like wall of text (few tags, long)
        if "<li" in inner or "<p>" in inner and inner.count("<p>") >= 2:
            return m.group(0)
        text = re.sub(r"<[^>]+>", " ", inner)
        text = re.sub(r"\s+", " ", text).strip()
        if len(text) < 80:
            return m.group(0)
        formatted = format_diag_paragraph(text)
        return f'<div class="diag-text">\n        <h3>{m.group(0).split("<h3>")[1].split("</h3>")[0] if "<h3>" in m.group(0) else ""}</h3>\n        {formatted}\n      </div>'

    # Safer targeted replace of <div class="diag-text">...<p>...</p></div>
    def repl2(m):
        h3 = m.group(1)
        pcontent = m.group(2)
        text = re.sub(r"\s+", " ", pcontent).strip()
        if len(text) < 80 or text.count("。") >= 3 and "<br" in m.group(0):
            # already somewhat structured
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
    _, _, bens, uses, kws, _ = pick_theme(name)
    bullets = bens[:3] + [f"適用：{'、'.join(uses[:4])}"]
    lis = "\n".join(f"          <li>{esc(b)}</li>" for b in bullets)
    html = re.sub(
        r'(<div class="pdp-tab-panel is-on" data-panel="intro"[^>]*>\s*<ul class="pdp-bullets">).*?(</ul>)',
        rf"\1\n{lis}\n        \2",
        html,
        count=1,
        flags=re.S,
    )
    return html


def ensure_css() -> None:
    css = CSS.read_text(encoding="utf-8")
    if ".pdp-eff-lead" in css:
        return
    block = """
/* ===== PDP efficacy / SEO block ===== */
#pdp-efficacy .pdp-eff-lead {
  font-size: 1.02rem; color: #444; line-height: 1.7; max-width: 48em;
}
#pdp-efficacy .pdp-eff-label {
  display: inline-block; background: #fff7ef; color: #c45e10;
  font-weight: 800; font-size: 0.85rem; padding: 0.25rem 0.7rem;
  border-radius: 999px; margin: 0.4rem 0 1rem;
}
#pdp-efficacy .pdp-eff-grid {
  display: grid; grid-template-columns: 1fr; gap: 1.2rem;
}
@media (min-width: 720px) {
  #pdp-efficacy .pdp-eff-grid { grid-template-columns: 1fr 1fr; gap: 1.5rem; }
}
#pdp-efficacy .pdp-eff-grid h3 {
  margin: 0 0 0.5rem; font-size: 1rem; color: #333;
}
#pdp-efficacy .pdp-kw {
  margin-top: 1.1rem; padding: 0.85rem 1rem; background: #f7fafc;
  border-left: 4px solid #3a9bb8; font-size: 0.9rem; line-height: 1.65; color: #555;
}
.pdp-buy-blurb {
  margin-top: 0.85rem; color: #444; line-height: 1.65; font-size: 0.95rem;
}
"""
    CSS.write_text(css.rstrip() + "\n" + block, encoding="utf-8")
    # bump cache on product pages lightly via site.css query — optional; pages already have ?v=


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
    # bump css query if present
    new = re.sub(
        r'(href="[^"]*assets/site\.css)\?v=[^"]*"',
        r'\1?v=20261021e"',
        new,
    )
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
    for n in updated[:8]:
        print(" ", n)
    if len(updated) > 8:
        print(f"  ... +{len(updated)-8} more")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
