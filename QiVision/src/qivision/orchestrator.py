"""编排层:把多个 Agent 串成「识别—方案—产品—反馈」闭环,并记录可追溯的执行轨迹。"""
from __future__ import annotations

import time
import uuid

from .agents import feedback as fb_agent
from .agents import product as product_agent
from .agents import syndrome as syndrome_agent
from .agents.capture import assess_quality, decode_image, segment_tongue
from .agents.tongue_vision import HeuristicAnalyzer, TongueAnalyzer, VLMAnalyzer
from .config import Settings, get_settings
from .knowledge.symptoms import RED_FLAGS, SYMPTOMS
from .llm import LLMClient
from .schemas import (AgentStep, AnalysisResult, FeedbackIn, FeedbackOut, QualityReport,
                      UserProfile)
from .storage import Storage

ASK_SYSTEM = (
    "你是 QiVision 望衡 的中医养生健康助手。仅依据给定的会话结果回答用户追问,"
    "不做医学诊断,不推荐药物,不编造信息;涉及疾病或用药请建议咨询执业医师。回答简洁、通俗。"
)


class Orchestrator:
    def __init__(self, settings: Settings | None = None, storage: Storage | None = None):
        self.settings = settings or get_settings()
        self.llm = LLMClient(self.settings)
        self.storage = storage or Storage(self.settings.db_path)
        heuristic = HeuristicAnalyzer()
        self.analyzer: TongueAnalyzer = (
            VLMAnalyzer(self.llm, heuristic)
            if self.settings.analyzer == "vlm" and self.llm.enabled
            else heuristic
        )

    # ------------------------------------------------------------------ 主流程
    def analyze(self, profile: UserProfile, image: bytes, symptoms: list[str]) -> AnalysisResult:
        sid = uuid.uuid4().hex[:12]
        trace: list[AgentStep] = []
        symptoms = [s for s in symptoms if s in SYMPTOMS or s in RED_FLAGS]

        def step(name: str, t0: float, summary: str) -> None:
            trace.append(AgentStep(agent=name, summary=summary, duration_ms=int((time.time() - t0) * 1000)))

        # 1) 采集引导 Agent
        t0 = time.time()
        try:
            img = decode_image(image)
        except ValueError as e:
            quality = QualityReport(ok=False, issues=[str(e)], tips=["请重新上传清晰的舌象照片"])
            step("capture", t0, "图片无法解码")
            return self._finish(AnalysisResult(session_id=sid, status="recapture", quality=quality,
                                               trace=trace), profile)
        mask = segment_tongue(img)
        quality = assess_quality(img, mask, self.settings.min_blur)
        step("capture", t0, "质量合格" if quality.ok else f"需重拍: {'、'.join(quality.issues)}")
        if not quality.ok or mask is None:
            return self._finish(AnalysisResult(session_id=sid, status="recapture", quality=quality,
                                               trace=trace), profile)

        # 2) 舌象分析 Agent
        t0 = time.time()
        tongue = self.analyzer.analyze(img, mask, image)
        step("tongue_vision", t0, f"{tongue.analyzer}: 舌质{tongue.body_color}/苔{tongue.coat_color}")

        # 3) 辨证与方案 Agent
        t0 = time.time()
        syn = syndrome_agent.run_syndrome(tongue, symptoms, self.llm)
        step("syndrome", t0, f"主体质倾向: {syn.primary_zh}")

        if syn.red_flags:
            step("safety", time.time(), f"命中红旗症状: {'、'.join(syn.red_flags)},建议就医")
            return self._finish(AnalysisResult(
                session_id=sid, status="referral", quality=quality, tongue=tongue,
                syndrome=syn, trace=trace), profile)

        # 4) 产品匹配 Agent
        t0 = time.time()
        products = product_agent.run_product_match(syn, profile)
        step("product", t0, f"匹配{len(products.matches)}个,排除{len(products.excluded)}个")

        qs = syndrome_agent.follow_up_questions(syn, symptoms)
        return self._finish(AnalysisResult(
            session_id=sid, status="ok", quality=quality, tongue=tongue, syndrome=syn,
            products=products, follow_up_questions=qs, trace=trace), profile)

    def _finish(self, result: AnalysisResult, profile: UserProfile) -> AnalysisResult:
        self.storage.save_session(result.session_id, profile.user_id, profile.model_dump(),
                                  result.model_dump())
        return result

    # ------------------------------------------------------------------ 反馈闭环
    def feedback(self, session_id: str, fb: FeedbackIn) -> FeedbackOut:
        sess = self.storage.get_session(session_id)
        if not sess:
            raise KeyError(session_id)
        self.storage.save_feedback(session_id, fb.model_dump())
        trend = self.trend(sess["user_id"])
        return fb_agent.run_feedback(fb, trend)

    def trend(self, user_id: str) -> dict | None:
        return fb_agent.compute_trend(self.storage.user_history(user_id))

    # ------------------------------------------------------------------ 追问
    def ask(self, session_id: str, question: str) -> str:
        sess = self.storage.get_session(session_id)
        if not sess:
            raise KeyError(session_id)
        syn = sess["result"].get("syndrome")
        if not syn:
            return "本次会话尚未生成辨证结果,请先重新拍摄舌象。"
        ctx = (f"体质倾向:{syn['primary_zh']};兼夹:{syn['secondary_zh']};"
               f"依据:{[e['text'] for e in syn['evidence']][:6]};"
               f"调理:{syn['regimen']}")
        out = self.llm.chat(ASK_SYSTEM, f"【会话结果】{ctx}\n【用户问题】{question}")
        if out:
            return out
        return (f"目前偏向【{syn['primary_zh']}】。{syn['explanation']}"
                "(未配置大模型,暂只能提供上述结构化解读。)")
