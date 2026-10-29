"""辨证与方案 Agent:规则约束 + 可追溯推理 + (可选)LLM 受约束解释。"""
from __future__ import annotations

from ..knowledge.symptoms import RED_FLAGS, SYMPTOMS
from ..knowledge.syndromes import CONSTITUTIONS, REGIMENS, RULES
from ..llm import LLMClient
from ..schemas import Evidence, Regimen, SyndromeResult, TongueFeatures

EXPLAIN_SYSTEM = (
    "你是一位严谨、温和的中医养生健康助手。请只依据用户提供的【结构化证据】,用通俗中文"
    "写一段不超过180字的体质解读。要求:不下医学诊断,不提及任何药物或治疗,不编造证据中"
    "没有的内容,结尾提醒结果仅供健康管理参考、不适请就医。"
)


def detect_red_flags(symptoms: list[str]) -> list[str]:
    return [RED_FLAGS[s] for s in symptoms if s in RED_FLAGS]


def score_constitutions(
    tongue: TongueFeatures, symptoms: list[str]
) -> tuple[dict[str, float], list[Evidence]]:
    scores = {k: 0.0 for k in CONSTITUTIONS}
    evidence: list[Evidence] = []
    tdict = tongue.model_dump()
    sset = set(symptoms)
    for source, fieldname, value, weights, text in RULES:
        hit = (tdict.get(fieldname) == value) if source == "tongue" else (fieldname in sset)
        if not hit:
            continue
        for k, w in weights.items():
            scores[k] += w
        label = SYMPTOMS.get(fieldname, fieldname) if source == "symptom" else f"{fieldname}={value}"
        evidence.append(Evidence(source=source, text=f"{label}:{text}", weights=weights))
    return scores, evidence


def run_syndrome(
    tongue: TongueFeatures, symptoms: list[str], llm: LLMClient | None = None
) -> SyndromeResult:
    scores, evidence = score_constitutions(tongue, symptoms)
    biased = {k: v for k, v in scores.items() if k != "pinghe"}
    top_key = max(biased, key=biased.get)
    top = biased[top_key]

    if top < 3:
        primary, secondary = "pinghe", []
    else:
        primary = top_key
        secondary = [k for k, v in biased.items() if k != primary and v >= max(3.0, 0.6 * top)]

    balance = round(max(0.0, 100.0 - top * 8), 1)
    result = SyndromeResult(
        scores={k: round(v, 1) for k, v in scores.items()},
        primary=primary,
        primary_zh=CONSTITUTIONS[primary],
        secondary=secondary,
        secondary_zh=[CONSTITUTIONS[k] for k in secondary],
        evidence=evidence,
        regimen=Regimen(**REGIMENS[primary]),
        red_flags=detect_red_flags(symptoms),
        balance_index=balance,
    )
    result.explanation = explain(result, llm)
    return result


def explain(r: SyndromeResult, llm: LLMClient | None) -> str:
    top_ev = sorted(r.evidence, key=lambda e: -e.weights.get(r.primary, 0))[:4]
    ev_text = ";".join(e.text for e in top_ev if e.weights.get(r.primary, 0) > 0) or "整体未见明显偏颇"
    sec = f",兼有{'、'.join(r.secondary_zh)}倾向" if r.secondary_zh else ""
    template = (
        f"综合舌象与问诊信息,您目前偏向【{r.primary_zh}】{sec}。主要依据:{ev_text}。"
        "以上仅供健康管理参考,如有不适请及时就医。"
    )
    if llm and llm.enabled:
        out = llm.chat(
            EXPLAIN_SYSTEM,
            f"体质倾向:{r.primary_zh};兼夹:{r.secondary_zh};结构化证据:{ev_text}",
        )
        if out:
            return out
    return template


FOLLOW_UP = {
    "qixu": ["您是否常觉得说话声音低、爱出虚汗?", "近期是否容易感冒?"],
    "yangxu": ["您是否冬天手脚特别凉、喜喝热水?", "是否有晨起腹泻或夜尿多?"],
    "yinxu": ["您夜间是否有盗汗或口干?", "是否常觉得手心脚心发热?"],
    "tanshi": ["您是否体重偏高、饭后容易困倦?", "大便是否偏黏、不成形?"],
    "shire": ["您是否常有口苦、面部出油或痘痘?", "小便颜色是否偏黄?"],
    "xueyu": ["是否有固定部位的刺痛?", "女性:经期是否有血块或痛经?"],
    "qiyu": ["近期情绪压力是否较大?", "是否常觉胸胁胀闷、爱叹气?"],
    "pinghe": ["近期睡眠与精力如何?"],
}


def follow_up_questions(r: SyndromeResult, asked: list[str]) -> list[str]:
    qs = list(FOLLOW_UP.get(r.primary, []))
    if r.secondary:
        qs += FOLLOW_UP.get(r.secondary[0], [])[:1]
    return qs[:3]
