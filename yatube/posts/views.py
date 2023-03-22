from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow

POSTS_PER_PAGE = 10


def get_paginator(items_list, request, page_param='page'):
    paginator = Paginator(items_list, POSTS_PER_PAGE)
    page_number = request.GET.get(page_param)
    return paginator.get_page(page_number)


def index(request):
    page_obj = get_paginator(Post.objects.all(), request)
    context = {
        'page_obj': page_obj,
        'index': True
    }
    return render(request, 'posts/index.html', context)


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    page_obj = get_paginator(group.posts.all(), request)

    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    page_obj = get_paginator(author.posts.all(), request)
    following = request.user.is_authenticated and Follow.objects.filter(
            author=author,
            user=request.user
        ).exists()
    context = {
        'page_obj': page_obj,
        "author": author,
        "following": following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    comments = post.comments.all()
    form = CommentForm()
    context = {
        "post": post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts_app:post_detail', post_id=post_id)


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect("posts_app:post_detail", post_id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect("posts_app:post_detail", post_id=post_id)
    context = {
        "form": form,
        "is_edit": is_edit,
    }
    return render(request, 'posts/post_create.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts_app:profile', request.user)
    context = {"form": form}
    return render(request, 'posts/post_create.html', context)


@login_required
def follow_index(request):
    page_obj = get_paginator(Post.objects.filter(
        author__following__user=request.user), request)
    context = {
        'page_obj': page_obj,
        'follow': True
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author
        )
    return redirect('posts_app:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts_app:profile', author.username)
