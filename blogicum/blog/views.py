from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.shortcuts import get_list_or_404, redirect
from .models import Category, Post, Comment, Location
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import Http404
from django.db.models import Q
from django.http import HttpResponseNotFound
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import PostForm, CommentForm, EditProfileForm
from django.db.models import Exists, OuterRef
User = get_user_model()


def index(request):
    # Оптимизированный запрос с явной проверкой всех условий
    post_list = Post.objects.annotate(
        has_published_category=Exists(
            Category.objects.filter(
                pk=OuterRef('category_id'),
                is_published=True
            )
        ),
        has_published_location=Exists(
            Location.objects.filter(
                pk=OuterRef('location_id'),
                is_published=True
            )
        ),
        has_active_author=Exists(
            User.objects.filter(
                pk=OuterRef('author_id'),
                is_active=True
            )
        )
    ).filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        has_published_category=True,
        has_published_location=True,
        has_active_author=True
    ).select_related('category', 'location', 'author').order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'category', 'location'),
        pk=post_id
    )

    # Проверяем базовые условия видимости
    if not (post.category.is_published and
            post.location.is_published and
            post.author.is_active):
        raise Http404("Пост не найден")

    # Проверяем доступ для неопубликованных/отложенных постов
    if not post.is_published or post.pub_date > timezone.now():
        if not request.user.is_authenticated or request.user != post.author:
            raise Http404("Пост не найден")

    comments = post.comments.filter(is_published=True)
    form = CommentForm()

    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True  # Проверяем, что категория опубликована
    )

    post_list = Post.objects.filter(
        category=category,
        is_published=True,
        pub_date__lte=timezone.now(),
        location__is_published=True
    ).order_by('-pub_date')

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/category.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)

    if request.user == author:
        # Автор видит все свои посты
        post_list = Post.objects.filter(author=author)
    else:
        # Другие видят только опубликованные
        post_list = Post.objects.filter(
            author=author,
            is_published=True,
            pub_date__lte=timezone.now()
        )

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': author,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


class EditProfileView(UpdateView):
    template_name = 'blog/user.html'
    form_class = EditProfileForm
    model = User
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self):
        return self.request.user

    def dispatch(self, request, *args, **kwargs):
        user = self.get_object()
        # Проверяем, является ли пользователь владельцем профиля
        if user != request.user:
            return redirect('blog:index')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CreatePostView(LoginRequiredMixin, CreateView):
    template_name = 'blog/create.html'
    form_class = PostForm
    model = Post

    def form_valid(self, form):
        form.instance.author = self.request.user
        if form.instance.pub_date > timezone.now():
            form.instance.is_published = False
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class EditPostView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/create.html'
    form_class = PostForm
    model = Post

    def get_object(self, queryset=None):
        # Получаем post_id из URL
        post_id = self.kwargs.get('post_id')
        return get_object_or_404(Post, pk=post_id)

    def form_valid(self, form):
        # Проверяем, является ли публикация отложенной
        if form.instance.pub_date > timezone.now():
            form.instance.is_published = False
        return super().form_valid(form)

    def dispatch(self, request, *args, **kwargs):
        post = self.get_object()
        # Проверяем, является ли пользователь автором поста
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.pk})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Убедимся, что автор не может быть изменен через форму
        kwargs['instance'].author = self.request.user
        return kwargs


class DeletePostView(LoginRequiredMixin, DeleteView):
    model = Post
    form_class = PostForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        try:
            obj = super().get_object(queryset)
            if not obj:
                raise Http404("Пост не найден")
            return obj
        except Http404:
            messages.error(self.request, 'Пост не найден')
            raise

    def post(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            if self.object.author != request.user:
                return redirect('blog:post_detail', post_id=self.object.pk)

            self.object.delete()
            return redirect('blog:profile', username=request.user.username)

        except Exception as e:
            return redirect('blog:post_detail', post_id=kwargs.get('post_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(instance=self.object)
        return context

    def dispatch(self, request, *args, **kwargs):
        try:
            post = self.get_object()
            if post.author != request.user:
                return redirect('blog:post_detail', post_id=post.pk)
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            return HttpResponseNotFound()

    def delete(self, request, *args, **kwargs):
        try:
            return super().delete(request, *args, **kwargs)
        except Exception as e:
            return redirect(
                'blog:post_detail',
                post_id=self.kwargs.get('post_id')
            )

    def get_success_url(self):
        messages.success(self.request, 'Пост успешно удалён')
        return reverse(
            'blog:profile',
            kwargs={'username': self.request.user.username}
        )


class CreateCommentView(LoginRequiredMixin, CreateView):
    template_name = 'includes/comments.html'
    form_class = CommentForm
    model = Comment

    def form_valid(self, form):
        post = get_object_or_404(Post, id=self.kwargs['post_id'])
        form.instance.author = self.request.user
        form.instance.post = post
        return super().form_valid(form)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )


class EditCommentView(LoginRequiredMixin, UpdateView):
    template_name = 'blog/comment.html'
    form_class = CommentForm
    model = Comment

    def get_object(self, queryset=None):
        # Получаем и post_id и comment_id из URL
        post_id = self.kwargs.get('post_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, pk=comment_id, post__id=post_id)

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        # Проверяем, является ли пользователь автором комментария
        if comment.author != request.user:
            return redirect('blog:post_detail', pk=comment.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )


class DeleteCommentView(LoginRequiredMixin, DeleteView):
    template_name = 'blog/comment.html'
    model = Comment

    def get_object(self, queryset=None):
        # Получаем и post_id и comment_id из URL
        post_id = self.kwargs.get('post_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, pk=comment_id, post__id=post_id)

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        # Проверяем, является ли пользователь автором комментария
        if comment.author != request.user:
            return redirect('blog:post_detail', pk=comment.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )
