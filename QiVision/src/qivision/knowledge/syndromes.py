"""体质/证型规则库(可追溯):每条规则=观察→证型权重→中医依据文本。

注意:这是 MVP 规则基线,权重需由中医专家审定与临床数据校准后才可用于正式场景。
"""
from __future__ import annotations

CONSTITUTIONS: dict[str, str] = {
    "pinghe": "平和质",
    "qixu": "气虚质",
    "yangxu": "阳虚质",
    "yinxu": "阴虚质",
    "tanshi": "痰湿质",
    "shire": "湿热质",
    "xueyu": "血瘀质",
    "qiyu": "气郁质",
}

# (source, field, value, {constitution: weight}, 依据)
RULES: list[tuple[str, str, object, dict[str, float], str]] = [
    # ---- 舌质颜色 ----
    ("tongue", "body_color", "pale", {"qixu": 2, "yangxu": 2}, "舌淡,多见于气血不足或阳气偏虚"),
    ("tongue", "body_color", "light_red", {"pinghe": 2}, "舌淡红,为气血调和之象"),
    ("tongue", "body_color", "red", {"yinxu": 2, "shire": 1}, "舌红,多主热,可见阴虚内热或湿热"),
    ("tongue", "body_color", "crimson", {"yinxu": 3, "shire": 1}, "舌绛红,热象明显,常见阴虚火旺"),
    ("tongue", "body_color", "purple", {"xueyu": 3, "yangxu": 1}, "舌紫暗,多主血行不畅或寒凝"),
    # ---- 舌苔 ----
    ("tongue", "coat_color", "yellow", {"shire": 3}, "苔黄,多主热、湿热"),
    ("tongue", "coat_color", "white", {"pinghe": 1}, "薄白苔属常见"),
    ("tongue", "coat_color", "gray_black", {"yangxu": 1, "shire": 1}, "苔灰黑,寒热皆可见,需结合问诊"),
    ("tongue", "coat_thickness", "thick", {"tanshi": 2, "shire": 1}, "苔厚腻,多为痰湿内蕴或湿热"),
    ("tongue", "coat_thickness", "none", {"yinxu": 2}, "少苔或无苔,多见阴津不足"),
    # ---- 舌形 / 津液 ----
    ("tongue", "teeth_marks", True, {"qixu": 2, "tanshi": 2}, "舌边齿痕,多为脾虚湿盛"),
    ("tongue", "shape", "swollen", {"tanshi": 2, "yangxu": 1, "qixu": 1}, "舌体胖大,多为脾虚痰湿或阳虚"),
    ("tongue", "shape", "thin", {"yinxu": 1}, "舌体瘦薄,多见阴血不足"),
    ("tongue", "cracks", True, {"yinxu": 2}, "舌面裂纹,多见阴津亏虚"),
    ("tongue", "moisture", "dry", {"yinxu": 2}, "舌面干燥,津液不足"),
    ("tongue", "moisture", "moist", {"yangxu": 1, "tanshi": 1}, "舌面水滑,多为水湿或阳虚"),
    # ---- 问诊症状 ----
    ("symptom", "fatigue", True, {"qixu": 2}, "乏力为气虚常见表现"),
    ("symptom", "shortness_of_breath", True, {"qixu": 2}, "气短懒言属肺脾气虚"),
    ("symptom", "spontaneous_sweat", True, {"qixu": 2}, "动则汗出为气虚不固"),
    ("symptom", "cold_limbs", True, {"yangxu": 3}, "手足不温为阳虚"),
    ("symptom", "fear_cold", True, {"yangxu": 2}, "畏寒喜热为阳气不足"),
    ("symptom", "night_sweat", True, {"yinxu": 3}, "盗汗多为阴虚内热"),
    ("symptom", "dry_mouth", True, {"yinxu": 2}, "口干咽燥为阴津不足"),
    ("symptom", "hot_palms_soles", True, {"yinxu": 3}, "五心烦热为阴虚"),
    ("symptom", "heavy_body", True, {"tanshi": 2}, "身重困倦为湿困"),
    ("symptom", "bloating", True, {"tanshi": 1, "qiyu": 1}, "腹胀可见脾虚湿阻或气滞"),
    ("symptom", "greasy_face", True, {"tanshi": 2, "shire": 1}, "面油多为痰湿或湿热"),
    ("symptom", "bitter_taste", True, {"shire": 2}, "口苦口黏为湿热"),
    ("symptom", "irritable", True, {"qiyu": 2}, "情绪烦躁为肝气不舒"),
    ("symptom", "sigh", True, {"qiyu": 2}, "善太息为气机郁滞"),
    ("symptom", "stabbing_pain", True, {"xueyu": 3}, "固定刺痛为血瘀"),
    ("symptom", "dark_complexion", True, {"xueyu": 2}, "面色晦暗为瘀血内阻"),
    ("symptom", "easy_bruising", True, {"xueyu": 2}, "易瘀青提示血行不畅"),
    ("symptom", "poor_sleep", True, {"yinxu": 1, "qiyu": 1}, "失眠可见阴虚或气郁"),
    ("symptom", "loose_stool", True, {"qixu": 1, "yangxu": 1, "tanshi": 1}, "便溏多为脾虚湿盛"),
    ("symptom", "constipation", True, {"yinxu": 1, "shire": 1}, "便干可见阴津不足或湿热"),
]

REGIMENS: dict[str, dict[str, list[str]]] = {
    "pinghe": {
        "diet": ["饮食均衡,五谷杂粮搭配", "四季顺时而食"],
        "lifestyle": ["作息规律,23点前入睡"],
        "exercise": ["保持每周3-5次中等强度运动"],
        "avoid": ["暴饮暴食、长期熬夜"],
    },
    "qixu": {
        "diet": ["山药、小米、红枣、鸡肉等健脾益气食材"],
        "lifestyle": ["避免过度劳累,保证充足睡眠"],
        "exercise": ["散步、八段锦、太极等柔缓运动,循序渐进"],
        "avoid": ["过度节食、剧烈大汗运动"],
    },
    "yangxu": {
        "diet": ["生姜、羊肉、韭菜、核桃等温阳食材(适量)"],
        "lifestyle": ["注意腰腹、足部保暖,避免久处空调冷风"],
        "exercise": ["晴天晨起或午后快走、八段锦,微微出汗即可"],
        "avoid": ["生冷冰饮、寒凉水果过量"],
    },
    "yinxu": {
        "diet": ["百合、银耳、梨、麦冬、玉竹等滋阴润燥食材"],
        "lifestyle": ["避免熬夜,睡前放松、减少咖啡因"],
        "exercise": ["瑜伽、太极、游泳等低强度运动,避免大汗"],
        "avoid": ["辛辣烧烤、煎炸、酗酒"],
    },
    "tanshi": {
        "diet": ["薏苡仁、赤小豆、冬瓜、陈皮、茯苓等健脾祛湿食材"],
        "lifestyle": ["控制体重,避免久坐,居处保持干燥通风"],
        "exercise": ["快走、慢跑、游泳等有氧运动,每周4次以上"],
        "avoid": ["肥甘厚味、甜食、夜宵"],
    },
    "shire": {
        "diet": ["绿豆、苦瓜、冬瓜、菊花、薏苡仁等清热利湿食材"],
        "lifestyle": ["保持皮肤清洁,作息规律,避免潮湿闷热环境"],
        "exercise": ["中长跑、游泳、球类等,以出汗排湿"],
        "avoid": ["辛辣油腻、烟酒"],
    },
    "xueyu": {
        "diet": ["山楂、黑木耳、玫瑰花、橘皮等行气活血食材(服用抗凝药者须先咨询医生)"],
        "lifestyle": ["避免久坐不动,注意保暖,保持心情舒畅"],
        "exercise": ["舒缓有氧运动、八段锦、拉伸,促进血液循环"],
        "avoid": ["寒凉冷饮、久坐久卧"],
    },
    "qiyu": {
        "diet": ["玫瑰花、陈皮、佛手、柑橘类等理气食材"],
        "lifestyle": ["多社交与户外活动,学习情绪疏导,必要时寻求心理支持"],
        "exercise": ["慢跑、舞蹈、团体运动、深呼吸练习"],
        "avoid": ["长期压抑情绪、独处过久"],
    },
}
