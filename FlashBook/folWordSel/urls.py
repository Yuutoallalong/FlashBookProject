from django.urls import path
from folWordSel import views
from flashcard import views as fviews
from wordguess import views as wviews
from flashcardChoice import views as fcviews

urlpatterns = [
    path('',views.folder_view,name='folder'),
    path('add_folder/',views.add_folder,name='add_folder'),
    path('<int:folder_id>',views.word_view,name='word'),
    path('<int:folder_id>/select_game/',views.select_game_view,name='select_game'),
    path('<int:folder_id>/edit_folder',views.edit_folder,name='edit_folder'),
    path('<int:folder_id>/add_word',views.add_word,name='add_word'),
    path('<int:folder_id>/edit_word/<int:word_id>',views.edit_word,name='edit_word'),
    path('search_folder',views.search_folder,name='search_folder'),
    path('<int:folder_id>/search_word',views.search_word,name='search_word'),
    # path('selectGame/', views.select_game_view, name='select_game'),
    path('<int:folder_id>/select_game/timeSet', views.time_set_view, name='time_set'),
    path('<int:folder_id>/select_game/timeSet/flashcard', fviews.flashcard, name='flashcard'),
    path('<int:folder_id>/select_game/timeSet/flashcardChoice', fcviews.flashcard_choice, name='flashcard_choice'),
    path('<int:folder_id>/select_game/modeSet/', views.mode_set_view, name='mode_set'),
    path('<int:folder_id>/select_game/modeSet/wordguess', wviews.word_guess_view, name='wordguess'),
    path('score/', views.score, name='score'),
    path('reward/', views.reward, name='reward'),
    path('community/', views.community, name='community'),
    path('check_in/', views.check_in, name='check_in'),
    path('redeem_reward/<int:reward_id>/', views.redeem_reward, name='redeem_reward'),
    path('add_public_game/', views.add_public_game, name='add_public_game'),
    path('join_game/<int:game_id>/', views.join_game, name='join_game'),
    path('<int:folder_id>/correct/<int:playtime>',fviews.correct_answer,name="correct_answer_fws"),
    path('<int:folder_id>/check_answer/<int:play_time>',fcviews.check_answer,name='check_answer_fws'),
    #path('upload_flashcards/<int:folder_id>/', views.upload_flashcards, name='upload_flashcards')
    path('folder/<int:folder_id>/upload_flashcards/', views.upload_flashcards, name='upload_flashcards')
]
