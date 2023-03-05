from http import HTTPStatus

from django.test import (
    Client,
    TestCase
)
from django.urls import reverse

from ..forms import PostForm
from ..models import (
    Group,
    Post,
    User
)


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='TestUserAuth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.form_text = 'Введенный в форму текст'
        cls.form_text_replace = 'Отредактированный в форме текст'

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.auth_user)

    def test_create_with_group_post(self):
        """Валидная форма создает запись в Posts с группой."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.form_text,
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts_app:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts_app:profile',
                kwargs={'username': self.auth_user.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        check_post = Post.objects.latest('id')
        self.assertTrue(check_post.text, self.form_text)
        self.assertTrue(check_post.group, self.group)
        self.assertTrue(check_post.author, self.auth_user)

    def test_create_without_group_post(self):
        """Валидная форма создает запись в Posts без группы."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.form_text,
        }
        response = self.authorized_client.post(
            reverse('posts_app:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts_app:profile',
                kwargs={'username': self.auth_user.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        check_post = Post.objects.latest('id')
        self.assertTrue(check_post.text, self.form_text)
        self.assertTrue(check_post.group, False)
        self.assertTrue(check_post.author, self.auth_user)

    def test_author_edit_post(self):
        """Валидная форма изменяет запись в Posts."""
        post = Post.objects.create(
            author=self.auth_user,
            text=self.form_text,
            group=self.group,
        )
        form_data = {
            'text': self.form_text_replace,
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts_app:post_edit', args=[post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts_app:post_detail', kwargs={'post_id': post.id}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        check_post = Post.objects.latest('id')
        self.assertEqual(check_post.text, self.form_text_replace)
        self.assertTrue(check_post.group, self.group)
        self.assertTrue(check_post.author, self.auth_user)
