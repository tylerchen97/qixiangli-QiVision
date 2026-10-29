"""问诊症状字典:key -> 中文标签。红旗症状命中时系统建议就医,不推荐产品。"""

SYMPTOMS: dict[str, str] = {
    "fatigue": "容易疲劳乏力",
    "shortness_of_breath": "气短懒言",
    "spontaneous_sweat": "稍动即出汗",
    "cold_limbs": "手脚冰凉",
    "fear_cold": "怕冷、喜热饮",
    "night_sweat": "盗汗",
    "dry_mouth": "口干咽燥",
    "hot_palms_soles": "手足心热",
    "heavy_body": "身体困重",
    "bloating": "腹胀、食后胀满",
    "greasy_face": "面部油腻",
    "bitter_taste": "口苦口黏",
    "irritable": "情绪烦躁易怒",
    "sigh": "爱叹气、胸闷",
    "stabbing_pain": "固定刺痛",
    "dark_complexion": "面色晦暗、有瘀斑",
    "easy_bruising": "易有瘀青",
    "poor_sleep": "睡眠不佳",
    "loose_stool": "大便偏稀溏",
    "constipation": "大便干结",
}

RED_FLAGS: dict[str, str] = {
    "chest_pain": "胸痛/胸闷剧烈",
    "hemoptysis": "咳血",
    "blood_in_stool": "便血或黑便",
    "persistent_fever": "持续发热",
    "unexplained_weight_loss": "不明原因体重明显下降",
    "severe_abdominal_pain": "剧烈腹痛",
    "dyspnea": "明显呼吸困难",
}
