from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm, DesignRequestForm, ChangeStatusForm
from .models import DesignRequest, Category

# --- Вспомогательная функция для проверки прав администратора ---
def is_admin(user):
    """
    Проверяет, является ли пользователь администратором (staff).
    """
    return user.is_staff

# --- Класс-представление для кастомного входа ---
class CustomLoginView(LoginView):
    """
    Кастомное представление для страницы входа.
    """
    template_name = 'registration/login.html'
    redirect_authenticated_user = True

# --- Представление для регистрации ---
def register(request):
    """
    Представление для регистрации нового пользователя.
    Доступно всем, включая гостей.
    """
    if request.method == 'POST': # Если форма отправлена (POST)
        form = CustomUserCreationForm(request.POST) # Создаем форму с данными из POST
        if form.is_valid(): # Проверяем, прошла ли форма валидацию
            user = form.save() # Сохраняем нового пользователя в базу данных
            login(request, user) # Автоматически входим под только что созданным пользователем
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать.')

            return redirect('user_dashboard')
        else:

            pass
    else:
        form = CustomUserCreationForm() # Создаем пустую форму

    # Отображаем шаблон регистрации с формой (пустой или с ошибками)
    return render(request, 'registration/register.html', {'form': form})

# --- Представление для главной страницы ---
def home(request):
    """
    Представление для главной страницы.
    """
    completed_requests = DesignRequest.objects.filter(status='completed').order_by('-created_at')[:4]
    in_progress_count = DesignRequest.objects.filter(status='in_progress').count()

    return render(request, 'main_app/home.html', {
        'completed_requests': completed_requests,
        'in_progress_count': in_progress_count
    })

def user_dashboard(request):
    user_requests = DesignRequest.objects.filter(user = request.user)
    status_filter = request.GET.get('status')
    if status_filter :
        user_requests = user_requests.filter(status = status_filter)

    return render(request, 'main_app/user_dashboard.html', {'requests': user_requests})

def create_request(request):
    """
    Представление для создания новой заявки на дизайн.
    """
    if request.method == 'POST': # Проверяем, был ли отправлен POST-запрос (форма отправлена)
        # Создаем форму с данными из POST и файлами из FILES (для изображения)
        form = DesignRequestForm(request.POST, request.FILES)
        if form.is_valid(): # Проверяем, прошла ли форма валидацию
            # Создаем объект заявки, но пока не сохраняем в базу (commit=False)
            design_request = form.save(commit=False)
            # Привязываем заявку к текущему пользователю
            design_request.user = request.user
            # Устанавливаем начальный статус "Новая"
            design_request.status = 'new'
            # Теперь сохраняем объект в базу данных
            design_request.save()
            # Добавляем сообщение об успешном создании
            messages.success(request, 'Заявка успешно создана.')
            # Перенаправляем пользователя на его личный кабинет
            return redirect('user_dashboard')
    else: # Если запрос GET (пользователь заходит на страницу создания)
        form = DesignRequestForm() # Создаем пустую форму

    # Отображаем шаблон создания заявки с формой (пустой или с ошибками)
    return render(request, 'main_app/create_request.html', {'form': form})