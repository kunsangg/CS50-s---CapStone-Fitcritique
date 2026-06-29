from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('chat/', views.chat_view, name='chat'),
    path('chat/<int:session_id>/', views.chat_view, name='chat_session'),
    path('history/', views.history_view, name='history'),
    path('saved/', views.saved_view, name='saved'),
    path('profile/', views.profile_view, name='profile'),
    
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/sessions/', views.api_sessions, name='api_sessions'),
    path('api/sessions/<int:session_id>/', views.api_session_detail, name='api_session_detail'),
    path('api/sessions/<int:session_id>/save/', views.api_save_look, name='api_save_look'),
]
