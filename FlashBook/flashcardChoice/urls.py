from django.urls import path, include
from . import views

urlpatterns = [
    path('<int:folder_id>/',views.flashcard_choice,name='flashcard_choice'),
    path('<int:folder_id>/check_answer/<int:play_time>',views.check_answer,name='check_answer'),
    path('<int:folder_id>/finishChoice/',views.finishChoice,name="finish_choice")
]