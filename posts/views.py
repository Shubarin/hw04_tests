from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from yatube.settings import RECORDS_ON_THE_PAGE

from .forms import PostForm
from .models import Group, Post, User


def index(request):
    posts = Post.objects.all()
    paginator = Paginator(posts, RECORDS_ON_THE_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "paginator": paginator,
        "page": page
    }
    return render(request, "index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    posts = group.posts.all()
    paginator = Paginator(posts, RECORDS_ON_THE_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "paginator": paginator,
        "group": group,
        "page": page
    }
    return render(request, "group.html", context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(reverse("posts:index"))

    return render(request, "new_post.html", {"form": form})


def profile(request, username):
    user = get_object_or_404(User.objects, username=username)
    posts = user.posts.all()
    # Вместо использования len() добавил ещё один запрос к БД
    # Но мне кажется здесь эффективнее было бы получить len(posts),
    # Чем делать повторный запрос к БД...
    user_post_count = user.posts.all().count()
    paginator = Paginator(posts, RECORDS_ON_THE_PAGE)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    context = {
        "paginator": paginator,
        "profile_user": user,
        "user_post_count": user_post_count,
        "page": page
    }
    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post.objects, id=post_id, author__username=username)
    user = post.author
    user_post_count = Post.objects.filter(author=user).count()
    context = {
        "profile_user": user,
        "user_post_count": user_post_count,
        "post": post,
    }

    return render(request, "post.html", context)


def post_edit(request, username, post_id):
    current_user = request.user
    post = get_object_or_404(Post.objects, id=post_id,
                             author__username=username)
    post_author_user = post.author
    if current_user != post_author_user:
        return redirect("posts:index")

    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect(reverse("posts:post", kwargs={"username": username,
                                                      "post_id": post_id}))

    return render(request, "new_post.html", {"form": form,
                                             "action_text": 'Редактировать',
                                             "post": post})
