from django.urls import path
from . import views

urlpatterns = [
    path('<int:folder_id>/',views.flashcard,name='flashcard'),
    path('<int:folder_id>/correct/<int:playtime>',views.correct_answer,name="correct_answer"),
    path('<int:folder_id>/wrong',views.wrong_answer,name="wrong_answer"),
    path('<int:folder_id>/next_word/<int:playtime>',views.next_word,name="next_word"),
    path('<int:folder_id>/next_word/finish/',views.finish,name="finish")
]
