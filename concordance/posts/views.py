from django.db import IntegrityError
from django.contrib import messages
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.shortcuts import render, reverse, redirect
from django.contrib.auth.decorators import login_required
from django.core.cache import cache

from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm
from .utils import get_page_obj


def index(request):
    page_num = request.GET.get('page')
    page_obj = cache.get_or_set(
        f'page-{page_num}',
        get_page_obj(Post.objects.all(), page_num),
        timeout=20)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/post_form.html'

    def get_success_url(self):
        return reverse(
            'posts:profile',
            kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class PostUpdateView(UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'posts/post_form.html'

    def get_success_url(self):
        obj = self.get_object()
        return reverse(
            'posts:post_detail',
            kwargs={'post_id': obj.id}
        )

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if not request.user.is_authenticated:
            return redirect(reverse('users:login'))
        elif not obj.author == request.user:
            return redirect(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': obj.id}
                )
            )
        return super().dispatch(request, *args, **kwargs)


def group_posts(request, slug):
    com_group = get_object_or_404(Group, slug=slug)
    page_num = request.GET.get('page')
    page_obj = get_page_obj(com_group.posts.all(), page_num)
    context = {
        'title': com_group.title,
        'description': com_group.description,
        'page_obj': page_obj,
        'group_name': com_group.title
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    following = (
        request.user.is_authenticated
        and User.objects.filter(following__author=author).exists()
    )
    page_num = request.GET.get('page')
    page_obj = get_page_obj(
        Post.objects.filter(author_id=author.id),
        page_num
    )
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': post.comments.all(),
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def follow_index(request):
    page_num = request.GET.get('page')
    page_obj = get_page_obj(
        Post.objects.filter(author__following__user=request.user),
        page_num)
    context = {
        'title': 'Подписки',
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    try:
        follow = Follow.objects.create(user=request.user, author=author)
    except IntegrityError:
        messages.warning(request, 'Вы не можете подписаться на самого себя!')
    else:
        follow.save()
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    follow = Follow.objects.filter(user=request.user, author=author)
    follow.delete()
    return redirect('posts:profile', username=username)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)
