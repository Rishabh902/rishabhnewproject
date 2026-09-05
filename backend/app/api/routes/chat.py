from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.rate_limit import limiter
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.chat import Message
from app.models.match import Match
from app.models.profile import Profile
from app.models.user import User
from app.models.payment import Subscription
from app.services.phase5 import create_notification
from app.services.plans import get_plan_for_score, get_plan
from datetime import datetime, timezone

router = APIRouter(prefix="/api/chat", tags=["Chat"])


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


def _profile_name(db: Session, user_id: int) -> str:
    p = db.query(Profile).filter(Profile.user_id == user_id).first()
    return p.name if p and p.name else "Member"


def _profile_photo(db: Session, user_id: int) -> str | None:
    p = db.query(Profile).filter(Profile.user_id == user_id).first()
    return f"/api/profiles/{user_id}/photo" if p and p.photo_path else None


def _get_participant_match(match_id: int, user_id: int, db: Session) -> Match:
    """Chat only exists between two people whose interest was mutually
    accepted -- there is no way to reach a conversation you are not part
    of, since a Match row is the only thing a conversation ID maps to."""
    match = db.get(Match, match_id)
    if not match or user_id not in (match.user_one_id, match.user_two_id):
        raise HTTPException(404, "Conversation not found")
    return match


def _other_user(match: Match, user_id: int) -> int:
    return match.user_two_id if match.user_one_id == user_id else match.user_one_id


def _conversation_summary(db: Session, match: Match, user_id: int) -> dict:
    other_id = _other_user(match, user_id)
    last_message = (
        db.query(Message).filter(Message.match_id == match.id).order_by(Message.created_at.desc()).first()
    )
    unread_count = (
        db.query(Message)
        .filter(Message.match_id == match.id, Message.sender_id != user_id, Message.is_read == False)
        .count()
    )
    return {
        "id": match.id,
        "other_user_id": other_id,
        "other_user_name": _profile_name(db, other_id),
        "other_user_photo_url": _profile_photo(db, other_id),
        "last_message": last_message.content if last_message else None,
        "last_message_at": last_message.created_at if last_message else match.created_at,
        "unread_count": unread_count,
    }


@router.get("/conversations")
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    matches = (
        db.query(Match)
        .filter((Match.user_one_id == user.id) | (Match.user_two_id == user.id))
        .all()
    )
    summaries = [_conversation_summary(db, m, user.id) for m in matches]
    summaries.sort(key=lambda c: c["last_message_at"], reverse=True)
    return summaries


@router.get("/conversations/{match_id}")
def get_conversation(match_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = _get_participant_match(match_id, user.id, db)
    return _conversation_summary(db, match, user.id)


@router.get("/conversations/{match_id}/messages")
def get_messages(match_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _get_participant_match(match_id, user.id, db)
    return (
        db.query(Message)
        .filter(Message.match_id == match_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@router.post("/conversations/{match_id}/messages", status_code=201)
@limiter.limit("60/minute")
def send_message(request: Request, match_id: int, data: SendMessageRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = _get_participant_match(match_id, user.id, db)

    # Determine required plan based on match score
    required_plan_code = get_plan_for_score(match.score)

    # Check if user has an active subscription for that plan
    now = datetime.now(timezone.utc)
    sub = (
        db.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.plan_code == required_plan_code,
            Subscription.is_active == True,
            Subscription.start_date <= now,
            Subscription.end_date > now,
        )
        .first()
    )

    if not sub:
        plan = get_plan(required_plan_code) or {}
        raise HTTPException(
            status_code=402,
            detail={
                "message": "Subscription required to start chat for this match.",
                "required_plan": required_plan_code,
                "price_inr": plan.get("price_inr"),
            },
        )

    message = Message(match_id=match.id, sender_id=user.id, content=data.content.strip())
    db.add(message)
    create_notification(
        db, _other_user(match, user.id), "NEW_MESSAGE", "New message",
        f"{_profile_name(db, user.id)} sent you a message.", {"match_id": match.id, "user_id": user.id},
    )
    db.commit()
    db.refresh(message)
    return message


@router.post("/conversations/{match_id}/read")
def mark_conversation_read(match_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    match = _get_participant_match(match_id, user.id, db)
    db.query(Message).filter(
        Message.match_id == match.id,
        Message.sender_id != user.id,
        Message.is_read == False,
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return {"message": "Marked read"}
