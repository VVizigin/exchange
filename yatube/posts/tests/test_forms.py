from http import HTTPStatus

from django.test import (
    Client,
    TestCase,
)
from django.urls import reverse

from ..models import (
    Group,
    Post,
    User
)


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='TestUserAuthor')
        cls.auth_user = User.objects.create_user(username='TestUserAuth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.form_text = 'Введенный в форму текст'
        cls.form_text_replace = 'Отредактированный в форме текст'

    def setUp(self):
        self.author_client = Client()
        self.guest_client = Client()
        self.auth_client = Client()
        self.author_client.force_login(PostCreateFormTests.author_user)
        self.auth_client.force_login(PostCreateFormTests.auth_user)

    def test_create_with_group_post(self):
        """Валидная форма создает запись в Posts с группой."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.form_text,
            'group': self.group.pk,
        }
        response = self.author_client.post(
            reverse('posts_app:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts_app:profile',
                kwargs={'username': self.author_user.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        check_post = Post.objects.latest('id')
        self.assertEqual(check_post.text, form_data['text'])
        self.assertEqual(check_post.group.id, form_data['group'])
        self.assertEqual(check_post.author, self.author_user)

    def test_create_without_group_post(self):
        """Валидная форма создает запись в Posts без группы."""
        post_count = Post.objects.count()
        form_data = {
            'text': self.form_text,
        }
        response = self.author_client.post(
            reverse('posts_app:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts_app:profile',
                kwargs={'username': self.author_user.username}
            )
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Post.objects.count(), post_count + 1)
        check_post = Post.objects.latest('id')
        self.assertEqual(check_post.text, form_data['text'])
        self.assertEqual(check_post.group, None)
        self.assertEqual(check_post.author, self.author_user)

    def test_author_edit_post(self):
        """Валидная форма изменяет запись в Posts."""
        post = Post.objects.create(
            author=self.author_user,
            text=self.form_text,
            group=self.group,
        )
        form_data = {
            'text': self.form_text_replace,
            'group': self.group.pk,
        }
        response = self.author_client.post(
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
        check_post = Post.objects.get(pk=post.id)
        self.assertEqual(check_post.text, form_data['text'])
        self.assertTrue(check_post.group.id, form_data['group'])
        self.assertTrue(check_post.author, self.author_user)
        self.assertTrue(check_post.pub_date, post.pub_date)

    def test_guest_user_create_post(self):
        """Проверка создания записи не авторизированным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст поста',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts_app:post_create'),
            data=form_data,
            follow=False
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), posts_count)

    def test_guest_user_edit_post(self):
        """Проверка редактирования записи не авторизированным
        пользователем."""
        post = Post.objects.create(
            text=self.form_text,
            author=self.author_user,
        )
        form_data = {
            'text': self.form_text_replace,
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts_app:post_edit', args=[post.id]),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response,
                             f'/auth/login/?next=/posts/{post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        post_one = Post.objects.latest('id')
        self.assertEqual(post_one, post)

    def test_no_author_edit_post(self):
        """При запросе редактирования поста авторизованного пользователя,
        но не автора, пост не будет отредактирован"""
        post = Post.objects.create(
            author=self.author_user,
            text=self.form_text,
        )
        form_data = {
            'text': self.form_text_replace,
            'group': self.group.pk,
        }
        response = self.auth_client.post(
            reverse('posts_app:post_edit', args=[post.id]),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(
                'posts_app:post_detail',
                kwargs={'post_id': post.id}
            )
        )
        check_post = Post.objects.get(pk=post.id)
        self.assertEqual(check_post, post)

