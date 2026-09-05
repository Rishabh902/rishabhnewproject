from datetime import date

def calculate_age(dob: date) -> int:
    from datetime import date as Date
    today = Date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

REQUIRED_FIELDS = (
    "name","gender","date_of_birth","caste","education","degree","profession",
    "income","height_cm","weight_kg","state","district","city_or_village",
    "permanent_address","preferred_location","family_details"
)

def validate_profile_for_submission(profile):
    missing=[field for field in REQUIRED_FIELDS if getattr(profile,field,None) in (None,"")]
    if missing: return missing
    if profile.date_of_birth and calculate_age(profile.date_of_birth)<18:
        return ["date_of_birth (user must be 18 or older)"]
    return []
