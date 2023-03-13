from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()
str_length = 15


class Post(models.Model):
    text = models.TextField(
        help_text="Текст поста",
        verbose_name="Введите текст поста",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Укажите дату публикации",
        help_text="Дата поста",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
        help_text="Автор поста",
    )

    group = models.ForeignKey(
        'Group',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        help_text="Выбрать группу",
        verbose_name='Группа'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date',)
        verbose_name = "Пост"
        verbose_name_plural = "Посты"

    def __str__(self):
        return self.text[:str_length]


class Group(models.Model):
    title = models.CharField(
        max_length=200,
        verbose_name="Название группы"
    )
    slug = models.SlugField(
        unique=True,
        verbose_name="ID группы"
    )
    description = models.TextField(
        verbose_name="Описание группы"
    )

    class Meta:
        ordering = ('title',)
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title
