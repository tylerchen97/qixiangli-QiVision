from qivision.agents.product import run_product_match
from qivision.agents.syndrome import run_syndrome
from qivision.schemas import TongueFeatures, UserProfile


def _syn(primary_tongue=None, symptoms=None):
    t = primary_tongue or TongueFeatures(body_color="purple")
    return run_syndrome(t, symptoms or ["stabbing_pain", "dark_complexion"])


def test_anticoagulant_excluded():
    syn = _syn()
    assert syn.primary == "xueyu"
    res = run_product_match(syn, UserProfile(user_id="u", age=40, medications=["华法林"]))
    assert all(m.product_id != "QXL-006" for m in res.matches)
    assert any(e.product_id == "QXL-006" for e in res.excluded)


def test_normal_user_gets_match():
    res = run_product_match(_syn(), UserProfile(user_id="u", age=40))
    assert res.matches and res.matches[0].product_id == "QXL-006"


def test_pregnancy_excluded():
    res = run_product_match(_syn(), UserProfile(user_id="u", age=30, pregnant=True))
    assert not res.matches
