import uuid
from pathlib import Path
from io import BytesIO
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy.orm import Session
from app.api.deps import get_current_user
from app.core.config import settings
from app.db.session import get_db
from app.models.profile import Profile
from app.models.preference import PartnerPreference
from app.models.photo import ProfilePhoto
from app.models.user import User
from app.schemas.profile import MatchProfileResponse, PreferenceResponse, PreferenceUpsert, ProfileResponse, ProfileUpsert
from app.services.profile import calculate_age, validate_profile_for_submission
from app.services.matching import calculate_match, compatible_gender, within_stated_preferences

router=APIRouter(prefix="/api/profiles",tags=["Profiles"])
BASE_DIR=Path(__file__).resolve().parents[3]
UPLOAD_DIR=BASE_DIR/"uploads"/"profile_photos"; UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
ALLOWED={"image/jpeg":".jpg","image/png":".png","image/webp":".webp"}
MAX_BYTES=5*1024*1024
MIN_PHOTOS=10
MAX_PHOTOS=20

def get_or_create_profile(db,user_id):
    p=db.query(Profile).filter(Profile.user_id==user_id).first()
    if not p:
        p=Profile(user_id=user_id,status="DRAFT"); db.add(p); db.commit(); db.refresh(p)
    return p

def photos_for(db,user_id):
    return db.query(ProfilePhoto).filter(ProfilePhoto.user_id==user_id).order_by(ProfilePhoto.is_primary.desc(),ProfilePhoto.id.asc()).all()

def photo_url(photo):
    return f"{settings.public_api_url.rstrip('/')}/api/profiles/{photo.user_id}/photos/{photo.id}" if settings.public_api_url else f"/api/profiles/{photo.user_id}/photos/{photo.id}"

def profile_response(db,p):
    data=ProfileResponse.model_validate(p).model_dump()
    photos=photos_for(db,p.user_id)
    primary=next((x for x in photos if x.is_primary), photos[0] if photos else None)
    data["photo_url"]=photo_url(primary) if primary else None
    data["photo_count"]=len(photos)
    return data

def ensure_editable(p):
    if p.status in {"PENDING_REVIEW","ACTIVE","SUSPENDED","BANNED"}:
        raise HTTPException(409,"Profile cannot be edited in its current state")

@router.get("/me",response_model=ProfileResponse)
def get_my_profile(user=Depends(get_current_user),db=Depends(get_db)):
    return profile_response(db,get_or_create_profile(db,user.id))

@router.get("/me/preferences",response_model=PreferenceResponse|None)
def get_preferences(user=Depends(get_current_user),db=Depends(get_db)):
    return db.query(PartnerPreference).filter(PartnerPreference.user_id==user.id).first()

@router.put("/me",response_model=ProfileResponse)
def update_profile(data:ProfileUpsert,user=Depends(get_current_user),db=Depends(get_db)):
    p=get_or_create_profile(db,user.id); ensure_editable(p)
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(p,k,v)
    p.status="DRAFT"; db.commit(); db.refresh(p)
    return profile_response(db,p)

@router.put("/me/preferences",response_model=PreferenceResponse)
def update_preferences(data:PreferenceUpsert,user=Depends(get_current_user),db=Depends(get_db)):
    p=get_or_create_profile(db,user.id); ensure_editable(p)
    if data.min_age is not None and data.max_age is not None and data.min_age>data.max_age: raise HTTPException(422,"Minimum age cannot exceed maximum age")
    if data.min_height_cm is not None and data.max_height_cm is not None and data.min_height_cm>data.max_height_cm: raise HTTPException(422,"Minimum height cannot exceed maximum height")
    pref=db.query(PartnerPreference).filter(PartnerPreference.user_id==user.id).first()
    if not pref: pref=PartnerPreference(user_id=user.id); db.add(pref)
    for k,v in data.model_dump(exclude_unset=True).items(): setattr(pref,k,v)
    db.commit(); db.refresh(pref); return pref

@router.post("/me/complete",response_model=ProfileResponse)
def submit_profile(user=Depends(get_current_user),db=Depends(get_db)):
    p=get_or_create_profile(db,user.id)
    missing=validate_profile_for_submission(p)
    if missing: raise HTTPException(422,{"message":"Complete every required profile field","missing":missing})
    count=db.query(ProfilePhoto).filter(ProfilePhoto.user_id==user.id).count()
    if count<MIN_PHOTOS: raise HTTPException(422,{"message":f"Upload at least {MIN_PHOTOS} photos before submission","photo_count":count,"minimum":MIN_PHOTOS})
    if not user.is_phone_verified: raise HTTPException(403,"Mobile OTP verification is required")
    p.status="PENDING_REVIEW"; p.rejection_reason=None
    db.commit(); db.refresh(p); return profile_response(db,p)

async def save_photo(file,user_id,db):
    if file.content_type not in ALLOWED: raise HTTPException(415,"Only JPG, PNG or WEBP images are allowed")
    raw=await file.read()
    if len(raw)>MAX_BYTES: raise HTTPException(413,"Each image must be 5 MB or smaller")
    try:
        image=Image.open(BytesIO(raw)).convert("RGB"); image.thumbnail((1600,1600))
    except Exception: raise HTTPException(400,"Invalid image")
    filename=f"{user_id}_{uuid.uuid4().hex}.jpg"; path=UPLOAD_DIR/filename
    draw=ImageDraw.Draw(image); text="Matrimony Platform"
    font=ImageFont.load_default(); bbox=draw.textbbox((0,0),text,font=font)
    x=max(10,image.width-(bbox[2]-bbox[0])-20); y=max(10,image.height-(bbox[3]-bbox[1])-20)
    draw.rectangle((x-8,y-5,x+(bbox[2]-bbox[0])+8,y+(bbox[3]-bbox[1])+5),fill=(0,0,0))
    draw.text((x,y),text,fill=(255,255,255),font=font); image.save(path,"JPEG",quality=88,optimize=True)
    count=db.query(ProfilePhoto).filter(ProfilePhoto.user_id==user_id).count()
    if count>=MAX_PHOTOS: path.unlink(missing_ok=True); raise HTTPException(409,f"Maximum {MAX_PHOTOS} photos allowed")
    photo=ProfilePhoto(user_id=user_id,file_path=str(path),original_name=file.filename,is_primary=(count==0))
    db.add(photo)
    p=get_or_create_profile(db,user_id)
    if count==0: p.photo_path=str(path)
    db.commit(); db.refresh(photo)
    return photo

@router.post("/me/photos")
async def upload_photos(files:list[UploadFile]=File(...),user=Depends(get_current_user),db=Depends(get_db)):
    p=get_or_create_profile(db,user.id); ensure_editable(p)
    if not files: raise HTTPException(400,"Select at least one image")
    existing=db.query(ProfilePhoto).filter(ProfilePhoto.user_id==user.id).count()
    if existing+len(files)>MAX_PHOTOS: raise HTTPException(409,f"You can keep maximum {MAX_PHOTOS} photos. Current: {existing}")
    out=[await save_photo(f,user.id,db) for f in files]
    return {"message":f"{len(out)} photo(s) uploaded successfully","photo_count":db.query(ProfilePhoto).filter(ProfilePhoto.user_id==user.id).count(),
            "minimum_required":MIN_PHOTOS,"photos":[{"id":x.id,"url":photo_url(x),"is_primary":x.is_primary} for x in out]}

@router.post("/me/photo")
async def upload_photo_legacy(file:UploadFile=File(...),user=Depends(get_current_user),db=Depends(get_db)):
    return await upload_photos([file],user,db)

@router.get("/me/photos")
def get_my_photos(user=Depends(get_current_user),db=Depends(get_db)):
    return {"photo_count":db.query(ProfilePhoto).filter(ProfilePhoto.user_id==user.id).count(),
            "minimum_required":MIN_PHOTOS,
            "photos":[{"id":p.id,"url":photo_url(p),"is_primary":p.is_primary,"original_name":p.original_name} for p in photos_for(db,user.id)]}

@router.delete("/me/photos/{photo_id}")
def delete_photo(photo_id:int,user=Depends(get_current_user),db=Depends(get_db)):
    p=get_or_create_profile(db,user.id); ensure_editable(p)
    photo=db.query(ProfilePhoto).filter(ProfilePhoto.id==photo_id,ProfilePhoto.user_id==user.id).first()
    if not photo: raise HTTPException(404,"Photo not found")
    was_primary=photo.is_primary; Path(photo.file_path).unlink(missing_ok=True); db.delete(photo); db.flush()
    remaining=photos_for(db,user.id)
    if was_primary and remaining: remaining[0].is_primary=True
    p.photo_path=remaining[0].file_path if remaining else None
    db.commit(); return {"message":"Photo deleted","photo_count":len(remaining)}

@router.get("/{user_id}/photos",response_model=None)
def get_public_photos(user_id:int,user=Depends(get_current_user),db=Depends(get_db)):
    p=db.query(Profile).filter(Profile.user_id==user_id).first()
    if not p: raise HTTPException(404,"Profile not found")
    if user.id!=user_id and user.role!="admin":
        own=db.query(Profile).filter(Profile.user_id==user.id).first()
        if not own or own.status!="ACTIVE" or p.status!="ACTIVE": raise HTTPException(403,"Photo is not publicly available")
    return {"photo_count":db.query(ProfilePhoto).filter(ProfilePhoto.user_id==user_id).count(),
            "photos":[{"id":x.id,"url":photo_url(x),"is_primary":x.is_primary} for x in photos_for(db,user_id)]}

@router.get("/{user_id}/photos/{photo_id}")
def serve_photo(user_id:int,photo_id:int,user=Depends(get_current_user),db=Depends(get_db)):
    p=db.query(Profile).filter(Profile.user_id==user_id).first()
    photo=db.query(ProfilePhoto).filter(ProfilePhoto.id==photo_id,ProfilePhoto.user_id==user_id).first()
    if not p or not photo: raise HTTPException(404,"Photo not found")
    if user.id!=user_id and user.role!="admin":
        own=db.query(Profile).filter(Profile.user_id==user.id).first()
        if not own or own.status!="ACTIVE" or p.status!="ACTIVE": raise HTTPException(403,"Photo is not publicly available")
    path=Path(photo.file_path)
    if not path.exists(): raise HTTPException(404,"Photo file not found")
    return FileResponse(path,media_type="image/jpeg")

@router.get("/{user_id}/photo")
def legacy_primary_photo(user_id:int,user=Depends(get_current_user),db=Depends(get_db)):
    p=db.query(Profile).filter(Profile.user_id==user_id).first()
    if not p: raise HTTPException(404,"Profile not found")
    primary=next(iter([x for x in photos_for(db,user_id) if x.is_primary]),None)
    if not primary: raise HTTPException(404,"Photo not found")
    return serve_photo(user_id,primary.id,user,db)

@router.get("/matches",response_model=list[MatchProfileResponse])
def get_matches(user=Depends(get_current_user),db=Depends(get_db)):
    own=get_or_create_profile(db,user.id)
    if own.status!="ACTIVE": raise HTTPException(403,"Your profile must be approved before matching is available")
    user_pref=db.query(PartnerPreference).filter(PartnerPreference.user_id==user.id).first()
    candidates=db.query(Profile).filter(Profile.status=="ACTIVE",Profile.user_id!=user.id).all()
    results=[]
    for c in candidates:
        if not compatible_gender(own.gender,c.gender): continue
        cp=db.query(PartnerPreference).filter(PartnerPreference.user_id==c.user_id).first()
        score,breakdown=calculate_match(own,c,user_pref,cp)
        results.append({"id":c.id,"user_id":c.user_id,"name":c.name,"gender":c.gender,"date_of_birth":c.date_of_birth,
            "caste":c.caste,"community":c.community,"education":c.education,"degree":c.degree,"profession":c.profession,"income":c.income,
            "height_cm":c.height_cm,"weight_kg":c.weight_kg,"state":c.state,"district":c.district,"city_or_village":c.city_or_village,
            "preferred_location":c.preferred_location,"photo_url":photo_url(next(iter([x for x in photos_for(db,c.user_id) if x.is_primary]),None)) if photos_for(db,c.user_id) else None,
            "status":c.status,"compatibility_score":score,"match_breakdown":breakdown,"relaxed_match":not within_stated_preferences(own,c,user_pref,cp)})
    results.sort(key=lambda x:x["compatibility_score"],reverse=True); return results

@router.get("/{user_id}",response_model=ProfileResponse)
def get_profile(user_id:int,user=Depends(get_current_user),db=Depends(get_db)):
    p=db.query(Profile).filter(Profile.user_id==user_id).first()
    if not p: raise HTTPException(404,"Profile not found")
    if user.id!=user_id and user.role!="admin":
        own=db.query(Profile).filter(Profile.user_id==user.id).first()
        if not own or own.status!="ACTIVE": raise HTTPException(403,"Your profile must be approved before viewing other profiles")
        if p.status!="ACTIVE": raise HTTPException(403,"Profile is not publicly available")
    return profile_response(db,p)

