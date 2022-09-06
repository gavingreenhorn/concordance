from django.urls import path, include
from rest_framework import routers
from rest_framework.authtoken import views
from djoser.views import UserViewSet
from rest_framework_simplejwt.views import TokenObtainSlidingView, TokenRefreshSlidingView

from api.views import PostsViewset, GroupsViewset, CommentsViewset, FollowViewSet

app_name = 'api'

v1_router = routers.DefaultRouter()
v1_router.register(r'users', UserViewSet, basename='users')
v1_router.register(r'posts', PostsViewset, basename='posts')
v1_router.register(r'groups', GroupsViewset, basename='groups')
v1_router.register(
    r'posts/(?P<post_id>\d+)/comments',
    CommentsViewset,
    basename='comments'
)
v1_router.register(
    r'follow',
    FollowViewSet,
    basename='follow'
)

urlpatterns = [
    path('v1/', include(v1_router.urls)),
    path('token/get/', TokenObtainSlidingView.as_view(), name='jwt-get'),
    path('token/refresh/', TokenRefreshSlidingView.as_view(), name='jwt-refresh')
]
