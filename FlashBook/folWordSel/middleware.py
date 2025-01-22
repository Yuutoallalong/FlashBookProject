from django.utils import timezone
from homepage.models import PublicGame

class CloseExpiredGamesMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # ตรวจสอบเกมที่หมดเวลาและปิดสถานะเกม
        now = timezone.now()
        expired_games = PublicGame.objects.filter(end_time__lte=now, status='OPEN')
        expired_games.update(status='FINISHED')  # อัปเดตสถานะเกมให้เป็น FINISHED

        # ต่อไปจะให้ Django ทำงานตามปกติ
        response = self.get_response(request)
        return response
