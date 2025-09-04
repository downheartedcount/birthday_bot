from services.hr_storage import HR_IDS


def is_hr(obj):
    if hasattr(obj, "from_user"):
        user_id = obj.from_user.id
    else:
        user_id = obj.id
    return user_id in HR_IDS
