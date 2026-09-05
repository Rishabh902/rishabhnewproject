from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.rate_limit import limiter
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.models.profile import Profile
from app.models.preference import PartnerPreference
from app.models.interest import Interest
from app.models.match import Match
from app.models.shortlist import Shortlist
from app.models.notification import Notification
from app.schemas.phase5 import (
    InterestCreate, InterestResponse, MatchResponse,
    ShortlistCreate, ShortlistResponse, NotificationResponse,
)
from app.services.phase5 import create_notification, get_or_create_match, calculate_pair_score

router = APIRouter(prefix="/api", tags=["Phase 5"])


def require_active_profile(db: Session, user_id: int) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile or profile.status != "ACTIVE":
        raise HTTPException(403, "Your profile must be approved before using this feature")
    return profile


def active_target(db: Session, user_id: int) -> Profile:
    profile = db.query(Profile).filter(Profile.user_id == user_id).first()
    if not profile or profile.status != "ACTIVE":
        raise HTTPException(404, "Active profile not found")
    return profile


def profile_name(db: Session, user_id: int) -> str:
    p = db.query(Profile).filter(Profile.user_id == user_id).first()
    return p.name if p and p.name else "Member"


def photo_url(db: Session, user_id: int) -> str | None:
    p = db.query(Profile).filter(Profile.user_id == user_id).first()
    return f"/api/profiles/{user_id}/photo" if p and p.photo_path else None


def interest_out(db: Session, item: Interest, viewer_id: int) -> dict:
    other = item.receiver_id if item.sender_id == viewer_id else item.sender_id
    return {
        "id": item.id,
        "sender_id": item.sender_id,
        "receiver_id": item.receiver_id,
        "status": item.status,
        "created_at": item.created_at,
        "updated_at": item.updated_at,
        "other_user_name": profile_name(db, other),
        "other_user_photo_url": photo_url(db, other),
    }


def match_out(db: Session, item: Match, viewer_id: int) -> dict:
    other = item.user_two_id if item.user_one_id == viewer_id else item.user_one_id
    return {
        "id": item.id,
        "user_one_id": item.user_one_id,
        "user_two_id": item.user_two_id,
        "score": item.score,
        "source": item.source,
        "created_at": item.created_at,
        "other_user_id": other,
        "other_user_name": profile_name(db, other),
        "other_user_photo_url": photo_url(db, other),
    }


def shortlist_out(db: Session, item: Shortlist) -> dict:
    return {
        "id": item.id,
        "user_id": item.user_id,
        "profile_user_id": item.profile_user_id,
        "created_at": item.created_at,
        "profile_name": profile_name(db, item.profile_user_id),
        "profile_photo_url": photo_url(db, item.profile_user_id),
    }


@router.post("/interests", response_model=InterestResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def send_interest(request: Request, data: InterestCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    if data.receiver_id == user.id:
        raise HTTPException(400, "You cannot send interest to yourself")
    active_target(db, data.receiver_id)

    existing = (
        db.query(Interest)
        .filter(Interest.sender_id == user.id, Interest.receiver_id == data.receiver_id)
        .first()
    )
    if existing:
        if existing.status == "REJECTED":
            existing.status = "PENDING"
            db.commit()
            db.refresh(existing)
        elif existing.status == "WITHDRAWN":
            existing.status = "PENDING"
            db.commit()
            db.refresh(existing)
        else:
            raise HTTPException(409, f"Interest already exists with status {existing.status}")
        return interest_out(db, existing, user.id)

    reverse = (
        db.query(Interest)
        .filter(Interest.sender_id == data.receiver_id, Interest.receiver_id == user.id)
        .first()
    )
    if reverse and reverse.status == "PENDING":
        score = calculate_pair_score(db, user.id, data.receiver_id)
        match, created = get_or_create_match(db, user.id, data.receiver_id, score)
        reverse.status = "ACCEPTED"
        if created:
            create_notification(db, user.id, "MATCH_CREATED", "New match", f"You matched with {profile_name(db, data.receiver_id)}.", {"match_id": match.id, "user_id": data.receiver_id})
            create_notification(db, data.receiver_id, "MATCH_CREATED", "New match", f"You matched with {profile_name(db, user.id)}.", {"match_id": match.id, "user_id": user.id})
        db.commit()
        db.refresh(reverse)
        return interest_out(db, reverse, user.id)

    item = Interest(sender_id=user.id, receiver_id=data.receiver_id, status="PENDING")
    db.add(item)
    db.flush()
    create_notification(
        db, data.receiver_id, "INTEREST_RECEIVED", "New interest received",
        f"{profile_name(db, user.id)} sent you an interest.", {"interest_id": item.id, "user_id": user.id},
    )
    db.commit()
    db.refresh(item)
    return interest_out(db, item, user.id)


@router.get("/interests/sent", response_model=list[InterestResponse])
def sent_interests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    items = db.query(Interest).filter(Interest.sender_id == user.id).order_by(Interest.created_at.desc()).all()
    return [interest_out(db, x, user.id) for x in items]


@router.get("/interests/received", response_model=list[InterestResponse])
def received_interests(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    items = db.query(Interest).filter(Interest.receiver_id == user.id).order_by(Interest.created_at.desc()).all()
    return [interest_out(db, x, user.id) for x in items]


@router.post("/interests/{interest_id}/accept", response_model=InterestResponse)
def accept_interest(interest_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    item = db.get(Interest, interest_id)
    if not item or item.receiver_id != user.id:
        raise HTTPException(404, "Interest not found")
    if item.status != "PENDING":
        raise HTTPException(409, f"Interest is already {item.status}")

    score = calculate_pair_score(db, item.sender_id, item.receiver_id)
    match, created = get_or_create_match(db, item.sender_id, item.receiver_id, score)
    item.status = "ACCEPTED"
    if created:
        create_notification(db, item.sender_id, "INTEREST_ACCEPTED", "Interest accepted", f"{profile_name(db, user.id)} accepted your interest.", {"interest_id": item.id, "match_id": match.id, "user_id": user.id})
        create_notification(db, user.id, "MATCH_CREATED", "New match", f"You matched with {profile_name(db, item.sender_id)}.", {"interest_id": item.id, "match_id": match.id, "user_id": item.sender_id})
        create_notification(db, item.sender_id, "MATCH_CREATED", "New match", f"You matched with {profile_name(db, user.id)}.", {"interest_id": item.id, "match_id": match.id, "user_id": user.id})
    db.commit()
    db.refresh(item)
    return interest_out(db, item, user.id)


@router.post("/interests/{interest_id}/reject", response_model=InterestResponse)
def reject_interest(interest_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    item = db.get(Interest, interest_id)
    if not item or item.receiver_id != user.id:
        raise HTTPException(404, "Interest not found")
    if item.status != "PENDING":
        raise HTTPException(409, f"Interest is already {item.status}")
    item.status = "REJECTED"
    create_notification(db, item.sender_id, "INTEREST_REJECTED", "Interest update", f"{profile_name(db, user.id)} declined your interest.", {"interest_id": item.id, "user_id": user.id})
    db.commit()
    db.refresh(item)
    return interest_out(db, item, user.id)


@router.delete("/interests/{interest_id}")
def withdraw_interest(interest_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    item = db.get(Interest, interest_id)
    if not item or item.sender_id != user.id:
        raise HTTPException(404, "Interest not found")
    if item.status != "PENDING":
        raise HTTPException(409, "Only pending interests can be withdrawn")
    item.status = "WITHDRAWN"
    db.commit()
    return {"message": "Interest withdrawn"}


@router.get("/matches", response_model=list[MatchResponse])
def get_matches(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    items = db.query(Match).filter((Match.user_one_id == user.id) | (Match.user_two_id == user.id)).order_by(Match.created_at.desc()).all()
    return [match_out(db, x, user.id) for x in items]


@router.get("/matches/{user_id}", response_model=list[MatchResponse])
def get_user_matches(user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if user_id != user.id and user.role != "admin":
        raise HTTPException(403, "You can only view your own matches")
    require_active_profile(db, user_id)
    items = db.query(Match).filter((Match.user_one_id == user_id) | (Match.user_two_id == user_id)).order_by(Match.created_at.desc()).all()
    return [match_out(db, x, user_id) for x in items]


@router.post("/shortlists", response_model=ShortlistResponse, status_code=status.HTTP_201_CREATED)
def add_shortlist(data: ShortlistCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    if data.profile_user_id == user.id:
        raise HTTPException(400, "You cannot shortlist yourself")
    active_target(db, data.profile_user_id)
    item = db.query(Shortlist).filter(Shortlist.user_id == user.id, Shortlist.profile_user_id == data.profile_user_id).first()
    if item:
        raise HTTPException(409, "Profile is already shortlisted")
    item = Shortlist(user_id=user.id, profile_user_id=data.profile_user_id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return shortlist_out(db, item)


@router.get("/shortlists", response_model=list[ShortlistResponse])
def get_shortlists(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    items = db.query(Shortlist).filter(Shortlist.user_id == user.id).order_by(Shortlist.created_at.desc()).all()
    return [shortlist_out(db, x) for x in items]


@router.delete("/shortlists/{profile_user_id}")
def remove_shortlist(profile_user_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_active_profile(db, user.id)
    item = db.query(Shortlist).filter(Shortlist.user_id == user.id, Shortlist.profile_user_id == profile_user_id).first()
    if not item:
        raise HTTPException(404, "Shortlist entry not found")
    db.delete(item)
    db.commit()
    return {"message": "Profile removed from shortlist"}


@router.get("/notifications", response_model=list[NotificationResponse])
def get_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Notification).filter(Notification.recipient_id == user.id).order_by(Notification.created_at.desc()).limit(100).all()
    return items


@router.post("/notifications/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(Notification, notification_id)
    if not item or item.recipient_id != user.id:
        raise HTTPException(404, "Notification not found")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return item


@router.delete("/notifications/{notification_id}")
def delete_notification(notification_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(Notification, notification_id)
    if not item or item.recipient_id != user.id:
        raise HTTPException(404, "Notification not found")
    db.delete(item)
    db.commit()
    return {"message": "Notification deleted"}
