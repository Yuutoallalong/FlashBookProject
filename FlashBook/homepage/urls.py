from django.urls import path
from homepage import views
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('',views.homepage,name='homepage'),
    path('about/',views.about,name='about'),
    path('register/', views.register, name='register'),
    path('login/', views.login_views, name='login'),
    path('logout/', views.logout_views, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='passwReset.html'), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='passwResetDone.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='passwResetConfirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='passwResetComplete.html'), name='password_reset_complete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)