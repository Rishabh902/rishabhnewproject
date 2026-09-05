PLANS = {
    "AI_DISCOVERY": {
        "name": "AI Discovery",
        "price_inr": 49.0,
        "duration_days": 30,
        "max_match_score": 50,
        "features": [
            "AI profile matching",
            "Access matches up to 50% compatibility",
            "Basic compatibility insights",
            "30 days validity",
        ],
    },
    "AI_SMART": {
        "name": "AI Smart Match",
        "price_inr": 199.0,
        "duration_days": 30,
        "max_match_score": 75,
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