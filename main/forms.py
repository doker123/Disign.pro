from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from .models import DesignRequest, Category

class CustomUserCreationForm(UserCreationForm):
    """
    Форма регистрации нового пользователя с дополнительной валидацией полей.
    """
    # Поле для ввода ФИО, не связанное с моделью User
    full_name = forms.CharField(
        max_length=254,
        label="ФИО",
        help_text="Введите ваше полное имя на кириллице (Фамилия Имя Отчество)."
    )
    # Поле для согласия, не связанное с моделью User
    agree_to_terms = forms.BooleanField(
        required=True,
        label="Согласие на обработку персональных данных",
        error_messages={'required': 'Вы должны согласиться с обработкой персональных данных.'}
    )

    class Meta:
        model = User

        fields = ("username", "email", "password1", "password2")
        help_texts = {
            'username': "Только латинские буквы и дефисы.",
            'email': "Введите действительный адрес электронной почты.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        self.fields['username'].widget.attrs.update({'placeholder': 'Введите логин'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Введите email'})
        self.fields['password1'].widget.attrs.update({'placeholder': 'Введите пароль'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Повторите пароль'})

        self.fields['full_name'].widget.attrs.update({'placeholder': 'Введите Фамилию Имя Отчество'})

    def clean_username(self):
        """
        Проверяет уникальность логина и формат (только латиница, цифры, подчёркивание, дефис).
        """
        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():
            raise ValidationError("Пользователь с таким логином уже существует.")

        pattern = r'^[a-zA-Z0-9_-]+$'
        if not re.fullmatch(pattern, username):
            raise ValidationError(
                "Логин должен содержать только латинские буквы, цифры, подчёркивание (_) или дефис (-).")

        return username

    def clean_email(self):
        """
        Проверяет уникальность email.
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return email

    def clean_password2(self):
        """
        Проверяет, совпадают ли введенные пароли.
        """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("Пароли не совпадают.")
        return password2

    def clean_full_name(self):
        """
        Проверяет, что ФИО содержит как минимум 2 слова (например, Имя и Фамилия).
        """
        full_name = self.cleaned_data.get('full_name')
        parts = full_name.strip().split()
        if len(parts) < 2:
            raise ValidationError("Пожалуйста, введите как минимум имя и фамилию.")
        # Проверим, что все части являются валидными (не пустые и состоят из разрешенных символов)
        for part in parts:
            if not part: # Проверка на пустую строку (например, двойной пробел)
                raise ValidationError("ФИО содержит недопустимые символы или лишние пробелы.")
        return full_name

    def save(self, commit=True):
        """
        Сохраняет пользователя, разбивая full_name на first_name и last_name.
        """
        user = super().save(commit=False)
        full_name = self.cleaned_data["full_name"]
        name_parts = full_name.strip().split()


        if len(name_parts) >= 2:
            user.first_name = name_parts[1]
            user.last_name = name_parts[0]
            # Если есть отчество (и его нужно сохранить, например, вместе с фамилией)
            if len(name_parts) > 2:
                user.last_name = f"{name_parts[0]} {name_parts[2]}"

        else:
            # Если вдруг не прошла валидация выше и пришло меньше 2 частей, хотя по логике не должно
            user.first_name = ""
            user.last_name = ""

        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class DesignRequestForm(forms.ModelForm):
    """
    Форма для создания новой заявки на дизайн.
    Все поля обязательны для заполнения.
    """
    class Meta:
        model = DesignRequest
        fields = ['title', 'description', 'category', 'plan_image']
        labels = {
            'title': 'Название заявки',
            'description': 'Описание',
            'category': 'Категория',
            'plan_image': 'Фото или план помещения (jpg, jpeg, png, bmp, до 2Мб)',
        }
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Введите подробное описание помещения и пожеланий к дизайну...'
            }),
            'title': forms.TextInput(attrs={
                'placeholder': 'Краткое название заявки'
            }),
        }

    def __init__(self, *args, **kwargs):
        """
        Инициализирует форму, устанавливая все поля как обязательные.
        """
        super().__init__(*args, **kwargs)
        # Устанавливаем все поля как обязательные
        for field_name in self.fields:
            self.fields[field_name].required = True


class ChangeStatusForm(forms.ModelForm):
    """
    Форма для изменения статуса заявки администратором.
    """
    class Meta:
        model = DesignRequest
        fields = ['status', 'design_image', 'admin_comment']
        labels = {
            'status': 'Новый статус',
            'design_image': 'Изображение дизайна (требуется для статуса "Выполнено")',
            'admin_comment': 'Комментарий (требуется для статуса "Принято в работу")',
        }
        widgets = {
            'admin_comment': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Введите комментарий для пользователя...'
            }),
        }

    def clean(self):
        """
        Дополнительная валидация формы при сохранении.
        Проверяет, что при смене статуса на 'completed' загружено изображение дизайна,
        а при смене на 'in_progress' введен комментарий.
        """
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        design_image = cleaned_data.get('design_image')
        admin_comment = cleaned_data.get('admin_comment')

        if status == 'complited' and not design_image:
            self.add_error('design_image', 'Для статуса "Выполнено" необходимо прикрепить изображение дизайна.')
        if status == 'in_progress' and not admin_comment:
            self.add_error('admin_comment', 'Для статуса "Принято в работу" необходимо указать комментарий.')

        return cleaned_data

    def __init__(self, *args, **kwargs):
        """
        Инициализирует форму.
        Устанавливает начальные значения виджетов и ограничения на выбор статуса.
        """
        super().__init__(*args, **kwargs)
        # Сделаем поля design_image и admin_comment необязательными по умолчанию,
        # валидация в clean() определит, когда они обязательны.
        self.fields['design_image'].required = False
        self.fields['admin_comment'].required = False


class CategoryForm(forms.ModelForm):
    """
    Форма для создания/редактирования категории заявки.
    Используется администратором.
    """
    class Meta:
        model = Category
        fields = ['name']
        labels = {
            'name': 'Название категории',
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Введите название категории, например, 3D-дизайн'
            }),
        }

    def clean_name(self):
        """
        Проверяет уникальность названия категории.
        """
        name = self.cleaned_data.get('name')
        if Category.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
             raise ValidationError("Категория с таким названием уже существует.")
        return name