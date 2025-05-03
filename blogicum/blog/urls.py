from django.urls import path
from . import views
app_name = 'blog'


urlpatterns = [
    path('', views.index, name='index'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path(
        'posts/create/',
        views.CreatePostView.as_view(),
        name='create_post'
    ),
    path(
        'posts/<int:post_id>/edit/',
        views.EditPostView.as_view(),
        name='edit_post'
    ),
    path(
        'posts/<int:post_id>/delete/',
        views.DeletePostView.as_view(),
        name='delete_post'
    ),
    path(
        'posts/<int:post_id>/comment/',
        views.CreateCommentView.as_view(),
        name='add_comment'
    ),
    path(
        'posts/<int:post_id>/edit_comment/<int:comment_id>/',
        views.EditCommentView.as_view(),
        name='edit_comment'
    ),
    path(
        'posts/<int:post_id>/delete_comment/<int:comment_id>/',
        views.DeleteCommentView.as_view(),
        name='delete_comment'
    ),
    path(
        'profile/edit/',
        views.EditProfileView.as_view(),
        name='edit_profile'
    ),
    path(
        'profile/<str:username>/',
        views.profile,
        name='profile'
    ),
    path(
        'category/<slug:category_slug>/',
        views.category_posts,
        name='category_posts'
    ),
]
