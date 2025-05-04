# Create your views here.
from django.views.generic import CreateView, View
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from users.forms import CustomUserCreationForm


class SignUp(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('blog:index')
    template_name = 'registration/registration_form.html'


class SignIn(LoginView):
    template_name = 'registration/login.html'  # ваш шаблон входа
    redirect_authenticated_user = True  # редирект если уже авторизован
    success_url = reverse_lazy('blog:index')


class LoggedOut(View):
    def get(self, request):
        # Перенаправляем на страницу подтверждения
        logout(request)
        messages.success(request, 'Вы успешно вышли из системы')
        return redirect('logout_confirm')
