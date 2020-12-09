from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render, redirect

from .models import Group, Post, User
from .forms import PostForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "paginator": paginator,
        "page": page
    }
    return render(request, "index.html", context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
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
        return redirect("posts:index")

    return render(request, "new_post.html", {"form": form})


def profile(request, username):
    user = get_object_or_404(User.objects, username=username)
    posts_list = Post.objects.filter(author=user)
    user_post_count = len(posts_list)
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        "paginator": paginator,
        "profile_user": user,
        "user_post_count": user_post_count,
        "page": page
    }
    return render(request, 'profile.html', context)


def post_view(request, username, post_id):
    user = get_object_or_404(User.objects, username=username)
    post = Post.objects.get(id__exact=post_id)
    user_post_count = Post.objects.filter(author=user).count()
    context = {
        'profile_user': user,
        'user_post_count': user_post_count,
        'post': post,
    }

    return render(request, 'post.html', context)


def post_edit(request, username, post_id):
    # тут тело функции. Не забудьте проверить,
    # что текущий пользователь — это автор записи.
    # В качестве шаблона страницы редактирования укажите шаблон создания новой записи
    # который вы создали раньше (вы могли назвать шаблон иначе)
    current_user = request.user
    post_author_user = get_object_or_404(User.objects, username=username)
    post = Post.objects.get(id__exact=post_id)
    if current_user != post_author_user:
        return redirect("posts:index")

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect(f"/{username}/{post_id}/")
    else:
        form = PostForm(instance=post)

    return render(request, 'new_post.html', {'form': form,
                                             'action_text': 'Редактировать',
                                             'post': post})
