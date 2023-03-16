import shutil
import tempfile

from http import HTTPStatus

from django.test import (
    Client,
    TestCase,
    override_settings
)
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile


from ..models import (
    Comment,
    Group,
    Post,
    User
)

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='TestUserAuthor')
        cls.auth_user = User.objects.create_user(username='TestUserAuth')
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.form_text = 'Введенный в форму текст'
        cls.form_text_replace = 'Отредактированный в форме текст'
        cls.comment_text = 'Текст комментария'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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

    def test_creating_post_with_image(self):
        """Проверяем, пост с картинкой через форму PostForm,
        создаётся запись в базе данных"""
        post_count = Post.objects.count()
        form_data = {
            'text': self.form_text,
            'group': self.group.pk,
            'image': self.uploaded
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

    def test_authorized_user_create_comment(self):
        """Проверка создания комментария авторизированным клиентом."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text=self.form_text,
            author=self.author_user,
        )
        form_data = {
            'text': self.comment_text,
            'post': post.pk
        }
        response = self.auth_client.post(
            reverse(
                'posts_app:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        comment_one = Comment.objects.latest('id')
        self.assertEqual(comment_one.text, self.comment_text)
        self.assertEqual(comment_one.author, self.auth_user)

    def test_guest_user_create_comment(self):
        """Проверка создания комментария авторизированным клиентом."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text=self.form_text,
            author=self.author_user,
        )
        form_data = {
            'text': self.comment_text,
            'post': post.pk
        }
        response = self.guest_client.post(
            reverse(
                'posts_app:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), comments_count)






