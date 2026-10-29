import pytest
from fastapi.testclient import TestClient

from qivision.api import create_app
from qivision.config import Settings
from qivision.orchestrator import Orchestrator
from qivision.schemas import FeedbackIn, UserProfile
from qivision.storage import Storage

from .conftest import make_tongue_image


@pytest.fixture
def orch():
    s = Settings(db_path=":memory:", analyzer="heuristic", api_key=None,
                 base_url="", llm_model="", vlm_model="", min_blur=5.0)
    return Orchestrator(s, Storage(":memory:"))


def test_full_loop(orch, tongue_bytes):
    p = UserProfile(user_id="u1", age=35)
    r1 = orch.analyze(p, tongue_bytes, ["fatigue"])
    assert r1.status == "ok", r1.quality
    assert r1.syndrome and r1.tongue and r1.products is not None
    assert [s.agent for s in r1.trace][:3] == ["capture", "tongue_vision", "syndrome"]

    fb = orch.feedback(r1.session_id, FeedbackIn(adherence_days=14, satisfaction=4,
                                                 symptom_changes={"fatigue": "better"}))
    assert fb.status == "continue"

    orch.analyze(p, tongue_bytes, ["fatigue"])
    assert orch.trend("u1")["points"].__len__() == 2


def test_bad_image(orch):
    r = orch.analyze(UserProfile(user_id="u2"), b"not-an-image", [])
    assert r.status == "recapture"


def test_referral_on_red_flag(orch, tongue_bytes):
    r = orch.analyze(UserProfile(user_id="u3"), tongue_bytes, ["hemoptysis"])
    assert r.status == "referral"
    assert r.products is None


def test_adverse_reaction(orch, tongue_bytes):
    r = orch.analyze(UserProfile(user_id="u4"), tongue_bytes, [])
    fb = orch.feedback(r.session_id, FeedbackIn(adverse_reaction=True))
    assert fb.status == "stop_and_consult"


def test_api(orch, tongue_bytes):
    c = TestClient(create_app(orch))
    assert c.get("/health").json()["status"] == "ok"
    r = c.post("/v1/sessions/analyze",
               files={"image": ("t.jpg", tongue_bytes, "image/jpeg")},
               data={"user_id": "api-u", "symptoms": "fatigue,cold_limbs", "age": "30"})
    assert r.status_code == 200
    sid = r.json()["session_id"]
    assert c.post(f"/v1/sessions/{sid}/ask", json={"question": "吃什么好?"}).status_code == 200
    assert c.get("/v1/users/api-u/trend").status_code == 200
    assert c.post("/v1/sessions/nope/feedback", json={}).status_code == 404
    assert c.get("/").status_code == 200


def test_synthetic_variants(orch):
    img = make_tongue_image(coat=False)
    assert orch.analyze(UserProfile(user_id="v"), img, []).status in {"ok", "recapture"}
