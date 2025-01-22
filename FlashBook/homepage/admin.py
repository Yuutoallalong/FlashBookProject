from django.contrib import admin
from homepage.models import *

# Register your models here.

admin.site.register(User)
admin.site.register(Folder)
admin.site.register(Word)
admin.site.register(Highscore)
admin.site.register(PublicGame)
admin.site.register(GamePlayer)
