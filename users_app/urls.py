from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),       
    path('auth', views.index, name='index'),
    path('register', views.register, name='register'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('profile/<int:user_id>', views.profile, name='profile'),
    path('profile/edit', views.edit_profile, name='edit_profile'),
    path('user/follow/<int:user_id>', views.follow_user, name='follow_user'),
    path('developers', views.developers, name='developers'),
    path('about', views.about, name='about'),
]