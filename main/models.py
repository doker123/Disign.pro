from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
import os


# Валидатор размера файла.
def validate_file_size(value):
    filesize = value.size
    if filesize > 2 * 1024 * 1024:
        raise ValidationError("Размер не должен превышать 2 МБ.")
# Валидатор размера и разширения.
def validate_image_extension_and_size(value):
    validate_file_size(value)
    valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    ext = os.path.splitext(value.name)[1].lower()
    if ext not in valid_extensions:
        raise ValidationError(f'Недопустимый формат файла. Разрешены {", ".join(valid_extensions)}')

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    def __str__(self):
        return self.name

    class Meta:
        verbose_name= 'Категория'
        verbose_name_plural = "Категории"

class DesignRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'Принято'),
        ('complited', 'Выполнено'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    title = models.CharField(max_length=200, null=False, blank=False, verbose_name='Заголовок')
    description = models.TextField(null=False, blank=False, verbose_name='Описание')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    plan_image = models.ImageField(upload_to='plan_img/', validators=[validate_image_extension_and_size])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)

    design_image = models.ImageField(upload_to='design_img/', validators=[validate_image_extension_and_size], blank=True, null=True)
    admin_comment = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name = 'Заявка на дизайн'
        verbose_name_plural = "Заявки на дизайн"
        ordering = ['-created_at']