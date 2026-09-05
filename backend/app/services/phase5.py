from sqlalchemy.orm import Session
from app.models.match import Match
from app.models.notification import Notification
from app.models.profile import Profile
from app.services.matching import calculate_match
from app.models.preference import PartnerPreference


def canonical_pair(a: int, b: int) -> tuple[int, int]:
    return (a, b) if a < b else (b, a)


def create_notification(
    db: Session,
    recipient_id: int,
    type_: str,
    title: str,
    message: str,
    payload: dict | None = None,
) -> Notification:
    item = Notification(
        recipient_id=recipient_id,
        type=type_,
        title=title,
        message=message,
        payload=payload,
        is_read=False,
    )
    db.add(item)
    return item


def get_or_create_match(db: Session, user_a: int, user_b: int, score: int | None = None) -> tuple[Match, bool]:
    one, two = canonical_pair(user_a, user_b)
    match = (
        db.query(Match)
        .filter(Match.user_one_id == one, Match.user_two_id == two)
        .first()
    )
    if match:
        if score is not None:
            match.score = score
        return match, False
    match = Match(user_one_id=one, user_two_id=two, score=score, source="INTEREST_ACCEPTED")
    db.add(match)
    db.flush()
    return match, True


def calculate_pair_score(db: Session, user_a: int, user_b: int) -> int | None:
    profile_a = db.query(Profile).filter(Profile.user_id == user_a).first()
    profile_b = db.query(Profile).filter(Profile.user_id == user_b).first()
    if not profile_a or not profile_b:
        return None
    pref_a = db.query(PartnerPreference).filter(PartnerPreference.user_id == user_a).first()
    pref_b = db.query(PartnerPreference).filter(PartnerPreference.user_id == user_b).first()
    score, _ = calculate_match(profile_a, profile_b, pref_a, pref_b)
    return score
