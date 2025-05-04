from django.views.generic import (
    CreateView, DeleteView, UpdateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.shortcuts import redirect
from .models import Category, Post, Comment
from django.urls import reverse
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import Http404
from django.http import HttpResponseNotFound
from django.contrib import messages
from django.contrib.auth import get_user_model
from .forms import PostForm, CommentForm, EditProfileForm
User = get_user_model()


def index(request):
    post_list = Post.objects.filter(
        is_published=True,
        pub_date__lte=timezone.now(),
        category__is_published=True,
        location__is_published=True,
        author__is_active=True
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

    if request.user != post.author:
        if not (
            post.is_published
            and post.pub_date <= timezone.now()
            and post.category.is_published
            and post.location.is_published
            and post.author.is_active
        ):
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
        is_published=True
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
        post_list = Post.objects.filter(author=author)
    else:
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
        if not request.user.is_authenticated:
            return redirect('login')

        user = self.get_object()
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
    pk_url_kwarg = 'post_id'

    def get_object(self, queryset=None):
        post = get_object_or_404(Post, pk=self.kwargs.get('post_id'))
        return post

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
        if 'instance' in kwargs:
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

    def post(self, request, **kwargs):
        try:
            self.object = self.get_object()
            if self.object.author != request.user:
                return redirect('blog:post_detail', post_id=self.object.pk)

            self.object.delete()
            return redirect('blog:profile', username=request.user.username)

        except Exception:
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
        except Exception:
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
            return redirect('blog:post_detail', post_id=comment.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )


class DeleteCommentView(LoginRequiredMixin, DeleteView):
    template_name = 'blog/comment.html'
    model = Comment
    pk_url_kwarg = 'comment_id'

    def get_object(self, queryset=None):
        # Получаем и post_id и comment_id из URL
        post_id = self.kwargs.get('post_id')
        comment_id = self.kwargs.get('comment_id')
        return get_object_or_404(Comment, pk=comment_id, post__id=post_id)

    def dispatch(self, request, *args, **kwargs):
        comment = self.get_object()
        # Проверяем, является ли пользователь автором комментария
        if comment.author != request.user:
            return redirect('blog:post_detail', post_id=comment.post.pk)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Удаляем форму из контекста, если она есть
        context.pop('form', None)
        return context

    def get_success_url(self):
        return reverse(
            'blog:post_detail',
            kwargs={'post_id': self.object.post.id}
        )
