from qivision.agents.syndrome import detect_red_flags, run_syndrome
from qivision.schemas import TongueFeatures


def test_yinxu_pattern():
    t = TongueFeatures(body_color="crimson", coat_color="none", coat_thickness="none",
                       moisture="dry", cracks=True)
    r = run_syndrome(t, ["night_sweat", "dry_mouth"])
    assert r.primary == "yinxu"
    assert r.balance_index < 100
    assert any("盗汗" in e.text for e in r.evidence)


def test_qixu_pattern():
    t = TongueFeatures(body_color="pale", teeth_marks=True, shape="swollen")
    r = run_syndrome(t, ["fatigue", "spontaneous_sweat"])
    assert r.primary == "qixu"


def test_balanced():
    t = TongueFeatures(body_color="light_red", coat_color="white", coat_thickness="thin")
    r = run_syndrome(t, [])
    assert r.primary == "pinghe"
    assert r.balance_index == 100.0


def test_red_flag():
    assert detect_red_flags(["fatigue", "hemoptysis"]) == ["咳血"]
