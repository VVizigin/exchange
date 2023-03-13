from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .forms import PostForm
from .models import Post, Group, User

POSTS_PER_PAGE = 10


def get_paginator(items_list, request, page_param='page'):
    paginator = Paginator(items_list, POSTS_PER_PAGE)
    page_number = request.GET.get(page_param)
    return paginator.get_page(page_number)


def index(request):
    page_obj = get_paginator(Post.objects.all(), request)
    context = {
        'page_obj': page_obj,
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
    context = {
        "page_obj": page_obj,
        "author": author,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    context = {
        "post": post,
    }
    return render(request, 'posts/post_detail.html', context)


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
