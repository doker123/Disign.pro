from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.contrib import messages
from .forms import CustomUserCreationForm, DesignRequestForm, ChangeStatusForm
from .models import DesignRequest, Category


def is_admin(user):

    return user.is_staff

class CustomLoginView(LoginView):

    template_name = 'registration/login.html'
    redirect_authenticated_user = True


def register(request):

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация прошла успешно! Добро пожаловать.')

            return redirect('user_dashboard')
        else:

            pass
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

def home(request):

    completed_requests = DesignRequest.objects.filter(status='complited').order_by('-created_at')[:4]
    in_progress_count = DesignRequest.objects.filter(status='in_progress').count()

    return render(request, 'main_app/home.html', {
        'completed_requests': completed_requests,
        'in_progress_count': in_progress_count
    })
@login_required()
def user_dashboard(request):
    user_requests = DesignRequest.objects.filter(user = request.user)
    status_filter = request.GET.get('status')
    if status_filter :
        user_requests = user_requests.filter(status = status_filter)

    return render(request, 'main_app/user_dashboard.html', {'requests': user_requests})
@login_required()
def create_request(request):

    if request.method == 'POST':

        form = DesignRequestForm(request.POST, request.FILES)
        if form.is_valid():
            design_request = form.save(commit=False)
            design_request.user = request.user
            design_request.status = 'new'
            design_request.save()
            messages.success(request, 'Заявка успешно создана.')
            return redirect('user_dashboard')
    else:
        form = DesignRequestForm()

    return render(request, 'main_app/create_request.html', {'form': form})

@login_required
def delete_request(request, request_id):

    design_request = get_object_or_404(DesignRequest, id=request_id, user=request.user)


    if design_request.status in ['completed', 'in_progress']:
        messages.error(request, 'Нельзя удалить заявку, которая уже принята в работу или выполнена.')
        return redirect('user_dashboard')

    if request.method == 'POST':

        design_request.delete()
        messages.success(request, 'Заявка успешно удалена.')
        return redirect('user_dashboard')

    return render(request, "main_app/delete_request.html", {'request': design_request})

@user_passes_test(is_admin)
def admin_dashboard(request):
    all_requests = DesignRequest.objects.all()

    return render(request, 'main_app/admin_dashboard.html', {'requests': all_requests})

@user_passes_test(is_admin)
def change_status(request, request_id):

    design_request = get_object_or_404(DesignRequest, id=request_id)

    if design_request.status in ['in_progress', 'completed']:
        messages.error(request, 'Нельзя изменить статус заявки, которая уже находится в работе или выполнена.')
        return redirect('admin_dashboard')

    if request.method == 'POST':

        form = ChangeStatusForm(request.POST, request.FILES, instance=design_request)
        if form.is_valid():
            form.save()

            messages.success(request, f'Статус заявки "{design_request.title}" изменен на "{design_request.get_status_display()}".')
            return redirect('admin_dashboard')
    else:
        form = ChangeStatusForm(instance=design_request)

    return render(request, 'main_app/change_status.html', {'form': form, 'request_obj': design_request})

@user_passes_test(is_admin)
def manage_categories(request):

    categories = Category.objects.all()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add':
            name = request.POST.get('name')
            if name:
                Category.objects.create(name=name)
                messages.success(request, 'Категория добавлена.')

        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            if cat_id:
                try:
                    category = Category.objects.get(id=cat_id)

                    DesignRequest.objects.filter(category=category).delete()
                    category.delete()
                    messages.success(request, 'Категория и связанные заявки удалены.')
                except Category.DoesNotExist:
                    messages.error(request, 'Категория не найдена.')

    return render(request, 'main_app/manage_categories.html', {'categories': categories})
