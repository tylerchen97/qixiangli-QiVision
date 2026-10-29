"""产品匹配 Agent:体质→产品打分 + 禁忌/过敏/药物相互作用检查,并给出匹配与排除理由。"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from ..knowledge.syndromes import CONSTITUTIONS
from ..schemas import ExcludedProduct, ProductMatch, ProductResult, SyndromeResult, UserProfile

PRODUCTS_PATH = Path(__file__).resolve().parent.parent / "knowledge" / "products.json"


@lru_cache(maxsize=1)
def load_products(path: str = str(PRODUCTS_PATH)) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["products"]


def _contains_any(haystack: list[str], needles: list[str]) -> str | None:
    for h in haystack:
        for n in needles:
            if n and (n.lower() in h.lower() or h.lower() in n.lower()):
                return n
    return None


def check_safety(p: dict, profile: UserProfile) -> tuple[str | None, list[str]]:
    """返回 (排除原因|None, 提醒列表)。"""
    if profile.pregnant and not p.get("pregnancy_safe", False):
        return "孕期/哺乳期暂不推荐", []
    if profile.age is not None and profile.age < p.get("min_age", 0):
        return f"适用年龄不低于{p['min_age']}岁", []
    hit = _contains_any(profile.allergies, p.get("allergens", []) + p.get("ingredients", []))
    if hit:
        return f"与过敏信息冲突({hit})", []
    hit = _contains_any(profile.medications, p.get("avoid_medication_keywords", []))
    if hit:
        return f"可能与正在使用的药物相互作用({hit}),请先咨询医生", []
    cautions: list[str] = []
    if p.get("caution_text"):
        cautions.append(p["caution_text"])
    if _contains_any(profile.conditions, p.get("caution_conditions", [])):
        cautions.append("您填写的健康状况与本产品有注意事项,建议使用前咨询医生")
    return None, cautions


def run_product_match(
    syndrome: SyndromeResult, profile: UserProfile, top_k: int = 3
) -> ProductResult:
    matches: list[ProductMatch] = []
    excluded: list[ExcludedProduct] = []
    for p in load_products():
        cons = p.get("constitutions", [])
        score = 0.0
        reasons: list[str] = []
        if syndrome.primary in cons:
            score += 3
            reasons.append(f"针对主要体质倾向【{CONSTITUTIONS[syndrome.primary]}】")
        for s in syndrome.secondary:
            if s in cons:
                score += 1.5
                reasons.append(f"兼顾兼夹倾向【{CONSTITUTIONS[s]}】")
        if score == 0:
            continue
        reason, cautions = check_safety(p, profile)
        if reason:
            excluded.append(ExcludedProduct(product_id=p["id"], name=p["name"], reason=reason))
            continue
        reasons.append(f"核心成分:{'、'.join(p.get('ingredients', []))}")
        matches.append(
            ProductMatch(
                product_id=p["id"], name=p["name"], form=p["form"],
                reasons=reasons, cautions=cautions, score=score,
            )
        )
    matches.sort(key=lambda m: -m.score)
    return ProductResult(matches=matches[:top_k], excluded=excluded)
