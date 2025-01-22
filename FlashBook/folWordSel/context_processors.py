from datetime import date
from homepage.models import User

def check_in_today(request):
    # ตรวจสอบว่าผู้ใช้ล็อกอินหรือยัง
    if request.session.get('user_id'):
        user = User.objects.get(user_id=request.session.get('user_id'))
        today = date.today()
        # ตรวจสอบว่า user ได้เช็คอินในวันนี้หรือไม่
        is_checked_in_today = user.last_check_in == today
        card_color_is_hash = user.card_color.startswith('#') if user.card_color else False
        return {'is_checked_in_today': is_checked_in_today,'user': user, 'card_color_is_hash': card_color_is_hash}
    return {'is_checked_in_today': False}
