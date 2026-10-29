from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BodyColor = Literal["pale", "light_red", "red", "crimson", "purple"]
CoatColor = Literal["none", "white", "yellow", "gray_black"]
CoatThickness = Literal["none", "thin", "thick"]
Moisture = Literal["dry", "normal", "moist"]
Shape = Literal["normal", "swollen", "thin"]


class UserProfile(BaseModel):
    user_id: str
    age: int | None = None
    sex: Literal["male", "female", "other"] | None = None
    pregnant: bool = False
    allergies: list[str] = Field(default_factory=list)
    medications: list[str] = Field(default_factory=list)
    conditions: list[str] = Field(default_factory=list)


class QualityReport(BaseModel):
    ok: bool
    blur_score: float = 0.0
    brightness: float = 0.0
    tongue_area_ratio: float = 0.0
    issues: list[str] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)


class TongueFeatures(BaseModel):
    body_color: BodyColor = "light_red"
    coat_color: CoatColor = "white"
    coat_thickness: CoatThickness = "thin"
    moisture: Moisture = "normal"
    shape: Shape = "normal"
    teeth_marks: bool = False
    cracks: bool = False
    confidence: float = 0.0
    analyzer: str = "unknown"


class Evidence(BaseModel):
    source: Literal["tongue", "symptom"]
    text: str
    weights: dict[str, float]


class Regimen(BaseModel):
    diet: list[str]
    lifestyle: list[str]
    exercise: list[str]
    avoid: list[str]


class SyndromeResult(BaseModel):
    scores: dict[str, float]
    primary: str
    primary_zh: str
    secondary: list[str] = Field(default_factory=list)
    secondary_zh: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    regimen: Regimen | None = None
    red_flags: list[str] = Field(default_factory=list)
    balance_index: float = 100.0
    explanation: str = ""


class ProductMatch(BaseModel):
    product_id: str
    name: str
    form: str
    reasons: list[str]
    cautions: list[str] = Field(default_factory=list)
    score: float


class ExcludedProduct(BaseModel):
    product_id: str
    name: str
    reason: str


class ProductResult(BaseModel):
    matches: list[ProductMatch] = Field(default_factory=list)
    excluded: list[ExcludedProduct] = Field(default_factory=list)


class AgentStep(BaseModel):
    agent: str
    summary: str
    duration_ms: int


class AnalysisResult(BaseModel):
    session_id: str
    status: Literal["ok", "recapture", "referral"]
    quality: QualityReport
    tongue: TongueFeatures | None = None
    syndrome: SyndromeResult | None = None
    products: ProductResult | None = None
    follow_up_questions: list[str] = Field(default_factory=list)
    trace: list[AgentStep] = Field(default_factory=list)
    disclaimer: str = (
        "QiVision 为健康管理与中医调理的辅助决策工具,结果不构成医疗诊断或治疗建议;"
        "如有不适请及时就医,并以执业医师意见为准。"
    )


class FeedbackIn(BaseModel):
    adherence_days: int = Field(0, ge=0, le=365)
    satisfaction: int = Field(3, ge=1, le=5)
    symptom_changes: dict[str, Literal["better", "same", "worse"]] = Field(default_factory=dict)
    adverse_reaction: bool = False
    note: str = ""


class FeedbackOut(BaseModel):
    status: Literal["continue", "adjust", "stop_and_consult", "recapture"]
    advice: list[str]
    trend: dict | None = None
