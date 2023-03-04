from django.urls import path

from . import views

app_name = 'posts_app'

urlpatterns = [
    path('', views.index, name="main"),
    path('group/<slug:slug>/', views.group_list, name="group_list"),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path('posts/<int:post_id>/edit/', views.post_edit, name='post_edit'),
    path('create/', views.post_create, name='post_create'),
]
