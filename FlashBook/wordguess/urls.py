from django.urls import path
from . import views

urlpatterns = [
    path('<int:folder_id>/', views.word_guess_view, name='word_guess'),
]