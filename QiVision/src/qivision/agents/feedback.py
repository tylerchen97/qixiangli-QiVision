"""反馈与追踪 Agent:收集使用反馈、判断是否调整/停用/复拍,并做纵向趋势分析。"""
from __future__ import annotations

from ..schemas import FeedbackIn, FeedbackOut


def compute_trend(history: list[dict]) -> dict | None:
    """history: 按时间升序的 [{created_at, primary, balance_index, scores}]。"""
    if not history:
        return None
    points = [
        {"created_at": h["created_at"], "primary": h["primary"], "balance_index": h["balance_index"]}
        for h in history
    ]
    out: dict = {"points": points}
    if len(history) >= 2:
        prev, cur = history[-2], history[-1]
        delta = round(cur["balance_index"] - prev["balance_index"], 1)
        out["delta_balance_index"] = delta
        out["direction"] = "improving" if delta > 2 else ("declining" if delta < -2 else "stable")
        out["constitution_changed"] = prev["primary"] != cur["primary"]
    return out


def run_feedback(fb: FeedbackIn, trend: dict | None) -> FeedbackOut:
    advice: list[str] = []
    if fb.adverse_reaction:
        return FeedbackOut(
            status="stop_and_consult",
            advice=["请立即停止使用相关产品,如症状明显或持续请及时就医。", "我们已记录您的反馈,用于产品安全评估。"],
            trend=trend,
        )

    better = sum(1 for v in fb.symptom_changes.values() if v == "better")
    worse = sum(1 for v in fb.symptom_changes.values() if v == "worse")

    if worse > better:
        advice += ["部分症状加重,建议暂停当前方案并重新拍摄舌象评估。", "若不适持续,请咨询执业中医师。"]
        status = "recapture"
    elif fb.adherence_days < 7:
        advice += ["调理需要一定周期,建议坚持至少2周后再复拍对比。"]
        status = "continue"
    elif better > 0 and fb.satisfaction >= 3:
        advice += ["整体向好,建议继续当前方案,并在2-4周后复拍对比。"]
        status = "continue"
    else:
        advice += ["改善不明显,建议复拍舌象并补充问诊,我们将据此调整方案。"]
        status = "adjust"

    if trend and trend.get("direction") == "declining":
        advice.append("趋势显示平衡指数下降,请留意作息饮食并考虑复诊。")
    if trend and trend.get("direction") == "improving":
        advice.append("平衡指数有所上升,保持当前习惯。")
    return FeedbackOut(status=status, advice=advice, trend=trend)
