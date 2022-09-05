from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken import views

from api.views import PostsViewsSet, GroupsViewsSet, CommentsViewsSet


app_name = 'api'

v1_router = routers.DefaultRouter()
v1_router.register(r'posts', PostsViewsSet, basename='posts')
v1_router.register(r'groups', GroupsViewsSet, basename='groups')
v1_router.register(
    r'posts/(?P<post_id>\d+)/comments',
    CommentsViewsSet,
    basename='comments'
)

urlpatterns = [
    path('v1/api-token-auth/', views.obtain_auth_token),
    path('v1/', include(v1_router.urls)),
]
