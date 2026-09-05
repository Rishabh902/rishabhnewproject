from __future__ import annotations

from difflib import SequenceMatcher

from app.models.preference import PartnerPreference
from app.models.profile import Profile
from app.services.profile import calculate_age


# Every dimension is a ranking signal, not a hard rejection rule, so a
# profile is never hidden outright just because one field doesn't line up
# with a stated preference -- it simply scores lower on that dimension.
WEIGHTS = {
    "location": 25,
    "profession": 20,
    "qualification": 15,
    "degree": 10,
    "age": 15,
    "height": 15,
    "location_detail": 5,
}


def normalize(value: str | None) -> str:
    if not value:
        return ""
    return " ".join(value.lower().replace(",", " ").split())


def similarity(left: str | None, right: str | None) -> float:
    """Explainable text similarity used by the matching engine."""
    a, b = normalize(left), normalize(right)
    if not a or not b:
        return 0.0
    if a == b or a in b or b in a:
        return 1.0
    tokens_a, tokens_b = set(a.split()), set(b.split())
    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b) if tokens_a | tokens_b else 0
    sequence = SequenceMatcher(None, a, b).ratio()
    return max(jaccard, sequence * 0.8)


def compatible_gender(user_gender: str | None, candidate_gender: str | None) -> bool:
    """The only hard filter left: matrimony profiles are matched across genders."""
    if not user_gender or not candidate_gender:
        return True
    a, b = normalize(user_gender), normalize(candidate_gender)
    if a in {"male", "m", "man"}:
        return b in {"female", "f", "woman"}
    if a in {"female", "f", "woman"}:
        return b in {"male", "m", "man"}
    return True


def _range_fit(value: float | None, min_value: float | None, max_value: float | None, tolerance: float) -> float:
    """1.0 when inside [min, max] (or when no preference was set at all),
    decaying linearly to 0.0 once ``value`` is ``tolerance`` units past the
    edge of the range. Used so an age/height preference nudges ranking
    instead of deleting a candidate outright."""
    if min_value is None and max_value is None:
        return 1.0
    if value is None:
        return 0.5
    if min_value is not None and value < min_value:
        gap = min_value - value
    elif max_value is not None and value > max_value:
        gap = value - max_value
    else:
        return 1.0
    if tolerance <= 0:
        return 0.0
    return max(0.0, 1 - (gap / tolerance))


def mutual_age_fit(
    user_profile: Profile,
    candidate: Profile,
    user_preference: PartnerPreference | None,
    candidate_preference: PartnerPreference | None,
) -> float:
    candidate_age = calculate_age(candidate.date_of_birth) if candidate.date_of_birth else None
    user_age = calculate_age(user_profile.date_of_birth) if user_profile.date_of_birth else None
    fit_for_user = _range_fit(
        candidate_age,
        user_preference.min_age if user_preference else None,
        user_preference.max_age if user_preference else None,
        tolerance=8,
    )
    fit_for_candidate = _range_fit(
        user_age,
        candidate_preference.min_age if candidate_preference else None,
        candidate_preference.max_age if candidate_preference else None,
        tolerance=8,
    )
    return (fit_for_user + fit_for_candidate) / 2


def mutual_height_fit(
    user_profile: Profile,
    candidate: Profile,
    user_preference: PartnerPreference | None,
    candidate_preference: PartnerPreference | None,
) -> float:
    fit_for_user = _range_fit(
        candidate.height_cm,
        user_preference.min_height_cm if user_preference else None,
        user_preference.max_height_cm if user_preference else None,
        tolerance=15,
    )
    fit_for_candidate = _range_fit(
        user_profile.height_cm,
        candidate_preference.min_height_cm if candidate_preference else None,
        candidate_preference.max_height_cm if candidate_preference else None,
        tolerance=15,
    )
    return (fit_for_user + fit_for_candidate) / 2


def within_stated_preferences(
    user_profile: Profile,
    candidate: Profile,
    user_preference: PartnerPreference | None,
    candidate_preference: PartnerPreference | None,
) -> bool:
    """Informational only (not a filter): True if the pair sits fully inside
    both sides' stated age/height range, for a UI hint -- never used to hide
    a profile from the results."""
    return (
        mutual_age_fit(user_profile, candidate, user_preference, candidate_preference) >= 1.0
        and mutual_height_fit(user_profile, candidate, user_preference, candidate_preference) >= 1.0
    )


def calculate_match(
    user_profile: Profile,
    candidate: Profile,
    user_preference: PartnerPreference | None,
    candidate_preference: PartnerPreference | None,
) -> tuple[int, dict[str, int]]:
    """Return an explainable 0-100 recommendation score.

    Location 25%, profession 20%, qualification 20%, age 15%, height 20%.
    Every dimension is scored, never used to reject a candidate outright --
    a mismatch on one axis just lowers that slice of the score, so everyone
    of a compatible gender and ACTIVE status is ranked and shown.
    """
    location_user = max(
        similarity(user_profile.preferred_location, candidate.preferred_location),
        similarity(user_preference.location if user_preference else None, candidate.preferred_location),
        similarity(user_profile.preferred_location, candidate_preference.location if candidate_preference else None),
    )

    profession_user = max(
        similarity(user_profile.profession, candidate.profession),
        similarity(user_preference.profession if user_preference else None, candidate.profession),
        similarity(user_profile.profession, candidate_preference.profession if candidate_preference else None),
    )

    qualification_user = max(
        similarity(user_profile.education, candidate.education),
        similarity(user_preference.education if user_preference else None, candidate.education),
        similarity(user_profile.education, candidate_preference.education if candidate_preference else None),
    )

    age_fit = mutual_age_fit(user_profile, candidate, user_preference, candidate_preference)
    height_fit = mutual_height_fit(user_profile, candidate, user_preference, candidate_preference)

    degree_user = max(
        similarity(user_profile.degree, candidate.degree),
        similarity(user_preference.education if user_preference else None, candidate.degree),
        similarity(user_profile.degree, candidate_preference.education if candidate_preference else None),
    )
    detailed_location = max(
        similarity(user_profile.state, candidate.state),
        similarity(user_profile.district, candidate.district),
        similarity(user_profile.city_or_village, candidate.city_or_village),
    )
    breakdown = {
        "location": round(location_user * WEIGHTS["location"]),
        "profession": round(profession_user * WEIGHTS["profession"]),
        "qualification": round(qualification_user * WEIGHTS["qualification"]),
        "degree": round(degree_user * WEIGHTS["degree"]),
        "age": round(age_fit * WEIGHTS["age"]),
        "height": round(height_fit * WEIGHTS["height"]),
        "location_detail": round(detailed_location * WEIGHTS["location_detail"]),
    }
    score = min(100, sum(breakdown.values()))
    return score, breakdown
