PLANS = {
    "AI_DISCOVERY": {
        "name": "AI Discovery",
        "price_inr": 49.0,
        "duration_days": 30,
        "max_match_score": 49,
        "features": [
            "AI profile matching",
            "Access matches up to 49% compatibility",
            "Basic compatibility insights",
            "30 days validity",
        ],
    },
    "AI_SMART": {
        "name": "AI Smart Match",
        "price_inr": 149.0,
        "duration_days": 30,
        "max_match_score": 74,
        "features": [
            "Everything in AI Discovery",
            "Access matches up to 75% compatibility",
            "Advanced compatibility insights",
            "Higher match visibility",
            "30 days validity",
        ],
    },
    "AI_PREMIUM": {
        "name": "AI Premium Match",
        "price_inr": 499.0,
        "duration_days": 30,
        "max_match_score": 100,
        "features": [
            "Everything in AI Smart Match",
            "Access matches up to 100% compatibility when available",
            "Highest compatibility recommendations",
            "Priority match visibility",
            "30 days validity",
        ],
    },
}


def get_plan(code: str) -> dict | None:
    if not code:
        return None

    return PLANS.get(code.strip().upper())


def get_all_plans() -> list[dict]:
    return [
        {
            "code": code,
            **plan,
        }
        for code, plan in PLANS.items()
    ]


def get_plan_for_score(score: int | None) -> str:
    """Map an integer match score (0-100) to a plan code.

    Rules:
      - score is None or < 50 -> AI_DISCOVERY
      - 50 <= score <= 74 -> AI_SMART
      - score >= 75 -> AI_PREMIUM

    Returns plan code string.
    """
    try:
        if score is None:
            s = 0
        else:
            s = int(score)
    except (TypeError, ValueError):
        s = 0

    if s < 50:
        return "AI_DISCOVERY"
    if 50 <= s <= 74:
        return "AI_SMART"
    return "AI_PREMIUM"
