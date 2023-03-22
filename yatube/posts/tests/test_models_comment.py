from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Post, Group, Comment

User = get_user_model()


class CommentModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.comment = Comment.objects.create(
            text='Комментарий для поста',
            author=cls.user,
        )

    # def test_verbose_name(self):
    #     """verbose_name в полях совпадает с ожидаемым."""
    #     post = CommentModelTest.post
    #     field_verboses = {
    #         'post': 'Пост',
    #         'text': 'Комментарий',
    #         'created': 'Комментарий создан',
    #         'author': 'Автор комментария',
    #     }
    #     for field, expected_value in field_verboses.items():
    #         with self.subTest(field=field):
    #             self.assertEqual(
    #                 post._meta.get_field(field).verbose_name,
    #                 expected_value)

        # post = models.ForeignKey(
        #     Post,
        #     on_delete=models.CASCADE,
        #     related_name='comments',
        #     verbose_name='Пост',
        #     help_text='Пост, к которому относится комментарий',
        # )
