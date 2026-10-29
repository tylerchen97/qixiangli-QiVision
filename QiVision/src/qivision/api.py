from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from . import __version__
from .agents.capture import CAPTURE_GUIDE
from .knowledge.symptoms import RED_FLAGS, SYMPTOMS
from .orchestrator import Orchestrator
from .schemas import AnalysisResult, FeedbackIn, FeedbackOut, UserProfile

MAX_IMAGE_BYTES = 8 * 1024 * 1024
WEB_DIR = Path(__file__).parent / "web"


class AskIn(BaseModel):
    question: str


def _split(s: str) -> list[str]:
    return [x.strip() for x in s.replace("\uff0c", ",").split(",") if x.strip()]


def create_app(orchestrator: Orchestrator | None = None) -> FastAPI:
    app = FastAPI(title="QiVision 望衡", version=__version__,
                  description="以智能望诊,洞察体质平衡 —— 智能舌诊与中医辨证 Agent")
    orch = orchestrator or Orchestrator()

    @app.get("/health")
    def health():
        return {"status": "ok", "version": __version__, "analyzer": orch.analyzer.name,
                "llm_enabled": orch.llm.enabled}

    @app.get("/")
    def index():
        return FileResponse(WEB_DIR / "index.html")

    @app.get("/v1/capture-guide")
    def capture_guide():
        return {"guide": CAPTURE_GUIDE}

    @app.get("/v1/symptoms")
    def symptoms():
        return {"symptoms": SYMPTOMS, "red_flags": RED_FLAGS}

    @app.post("/v1/sessions/analyze", response_model=AnalysisResult)
    async def analyze(
        image: UploadFile = File(...),
        user_id: str = Form(...),
        symptoms: str = Form(""),
        age: int | None = Form(None),
        sex: str | None = Form(None),
        pregnant: bool = Form(False),
        allergies: str = Form(""),
        medications: str = Form(""),
        conditions: str = Form(""),
    ):
        data = await image.read()
        if not data or len(data) > MAX_IMAGE_BYTES:
            raise HTTPException(400, "图片为空或超过 8MB")
        try:
            profile = UserProfile(user_id=user_id, age=age, sex=sex or None, pregnant=pregnant,
                                  allergies=_split(allergies), medications=_split(medications),
                                  conditions=_split(conditions))
        except Exception as e:
            raise HTTPException(422, str(e))
        return orch.analyze(profile, data, _split(symptoms))

    @app.post("/v1/sessions/{session_id}/feedback", response_model=FeedbackOut)
    def feedback(session_id: str, body: FeedbackIn):
        try:
            return orch.feedback(session_id, body)
        except KeyError:
            raise HTTPException(404, "会话不存在")

    @app.post("/v1/sessions/{session_id}/ask")
    def ask(session_id: str, body: AskIn):
        try:
            return {"answer": orch.ask(session_id, body.question)}
        except KeyError:
            raise HTTPException(404, "会话不存在")

    @app.get("/v1/users/{user_id}/trend")
    def trend(user_id: str):
        t = orch.trend(user_id)
        if t is None:
            raise HTTPException(404, "暂无历史记录")
        return t

    return app


app = create_app()
