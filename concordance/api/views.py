from django.shortcuts import get_object_or_404
from rest_framework import viewsets, filters, mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import LimitOffsetPagination

from posts.models import Post, Group
from api.serializers import PostSerializer, GroupSerializer, CommentSerializer, FollowSerializer
from api.permissions import IsAuthorOrReadOnly


class PostsViewset(viewsets.ModelViewSet):
    """All posts."""
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = LimitOffsetPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ['author__username']

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class GroupsViewset(viewsets.ReadOnlyModelViewSet):
    """All groups."""
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class CommentsViewset(viewsets.ModelViewSet):
    """All comments related to specified post."""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_post(self):
        return get_object_or_404(
            Post.objects.all(),
            id=self.kwargs.get('post_id')
        )

    def get_queryset(self):
        return self.get_post().comments

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, post=self.get_post())

    def perform_update(self, serializer):
        serializer.save(author=self.request.user, post=self.get_post())

class FollowViewSet(
        mixins.CreateModelMixin, 
        mixins.ListModelMixin,
        viewsets.GenericViewSet):
    serializer_class = FollowSerializer 
    permission_classes = [IsAuthenticated] 
    filter_backends = [filters.SearchFilter] 
    search_fields = ['following__username'] 

    def get_queryset(self): 
        return self.request.user.following.all() 

    def perform_create(self, serializer): 
        serializer.save(user=self.request.user)
        
