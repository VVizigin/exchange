import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='TestUserAuth')
        cls.author_user = User.objects.create_user(username='TestUserAuthor')
        cls.unfollow_user = User.objects.create_user(
            username='TestUserUnfollow')
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
        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        # cls.follower = User.objects.create(
        #     username=cls.auth_user.username
        #     author=
        # )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(self.auth_user)
        self.author_client = Client()
        self.author_client.force_login(self.author_user)
        self.unfollow_client = Client()
        self.unfollow_client.force_login(self.unfollow_user)

    def test_pages_uses_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
        cache.clear()
        page_names_templates = {
            reverse('posts_app:main'): 'posts/index.html',
            reverse(
                'posts_app:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts_app:profile', kwargs={
                    'username': self.author_user.username
                }
            ): 'posts/profile.html',
            reverse(
                'posts_app:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts_app:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/post_create.html',
            reverse('posts_app:post_create'): 'posts/post_create.html',
        }
        for reverse_name, template in page_names_templates.items():
            with self.subTest(template=template):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        cache.clear()
        response = self.auth_client.get(reverse('posts_app:main'))
        post_info = response.context.get('page_obj')[0]
        self.assertEqual(post_info, self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        url = reverse(
            'posts_app:group_list', kwargs={'slug': self.group.slug}
        )
        response = self.auth_client.get(url)
        post_info = response.context.get('page_obj')[0]
        self.assertEqual(post_info, self.post)
        group_info = response.context.get('group')
        self.assertEqual(group_info, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url = reverse(
            'posts_app:profile',
            kwargs={'username': PostTests.author_user}
        )
        response = self.author_client.get(url)
        post_info = response.context.get('page_obj')[0]
        self.assertEqual(post_info, self.post)
        author_info = response.context.get('author')
        self.assertEqual(author_info, self.author_user)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        url = reverse(
            'posts_app:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        response = self.author_client.get(url)
        post_info = response.context.get('post')
        self.assertEqual(post_info, self.post)

    def test_edit_post_show_correct_context(self):
        """Шаблон редактирования поста create_post сформирован
        с правильным контекстом.
        """
        url = reverse('posts_app:post_edit', kwargs={'post_id': self.post.pk})
        response = self.author_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context.get('is_edit'))

    def test_create_post_show_correct_context(self):
        """Шаблон создания поста create_post сформирован
        с правильным контекстом.
        """
        url = reverse('posts_app:post_create')
        response = self.auth_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)
        self.assertFalse(response.context.get('is_edit'))

    def test_create_post_show_home_group_list_profile_pages(self):
        """Созданный пост отобразился на главной, на странице группы,
        в профиле пользователя.
        """
        cache.clear()
        urls = (
            reverse('posts_app:main'),
            reverse('posts_app:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts_app:profile',
                kwargs={'username': self.author_user.username}
            ),
        )
        for url in urls:
            response = self.author_client.get(url)
            self.assertIn(self.post, response.context['page_obj'])

    def test_post_not_another_group(self):
        """Созданный пост не попал в группу, для которой не был
        предназначен"""
        another_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-another-slug',
            description='Тестовое описание дополнительной группы',
        )
        response = self.auth_client.get(
            reverse('posts_app:group_list',
                    kwargs={'slug': another_group.slug})
        )
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_index_page_cache(self):
        """ Кеширование posts_app:main работатет. """
        cache.clear()
        post = Post.objects.create(
            text='Тестовый пост',
            author=self.author_user,
            group=self.group
        )
        content_add = self.auth_client.get(
            reverse('posts_app:main')).content
        post.delete()
        content_delete = self.auth_client.get(
            reverse('posts_app:main')).content
        self.assertEqual(content_add, content_delete)
        cache.clear()
        content_cache_clear = self.auth_client.get(
            reverse('posts_app:main')).content
        self.assertNotEqual(content_add, content_cache_clear)

    def test_follow_on_user(self):
        """Проверка подписки на пользователя."""
        count_follow = Follow.objects.count()
        response = self.auth_client.post(
            reverse('posts_app:profile_follow',
                    args=[self.author_user.username]),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.author_user.id)
        self.assertEqual(follow.user_id, self.auth_user.id)

    def test_unfollow_on_user(self):
        """Проверка отписки от пользователя."""
        count_follow = Follow.objects.count()
        response = self.auth_client.post(
            reverse('posts_app:profile_follow',
                    args=[self.author_user.username]),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        follow = Follow.objects.all().latest('id')
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.assertEqual(follow.author_id, self.author_user.id)
        self.assertEqual(follow.user_id, self.auth_user.id)
        response = self.auth_client.post(
            reverse('posts_app:profile_unfollow',
                    args=[self.author_user.username]),
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Follow.objects.count(), count_follow)

    def test_posts_views_follow_correct_context(self):
        """ Проверка контекста для posts_app:follow_main.
        """
        cache.clear()
        Follow.objects.create(
            user=self.auth_user,
            author=self.author_user
        )
        response = self.auth_client.get(reverse('posts_app:follow_main'))
        self.assertEqual(len(response.context.get('page_obj')), 1)
        post_info = response.context.get('page_obj')[0]
        self.assertEqual(post_info, self.post)
        response = self.unfollow_client.get(reverse('posts_app:follow_main'))
        self.assertEqual(len(response.context.get('page_obj')), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.count_posts = 13
        cls.posts_per_first_page = 10
        cls.posts_per_second_page = 3
        super().setUpClass()
        cls.author_user = User.objects.create_user(username='TestUserAuthor')
        cls.auth_user = User.objects.create_user(username='TestUserAuth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.posts = [
            Post(
                author=cls.author_user,
                text=f'Тестовый пост {i}',
                group=cls.group,
            )
            for i in range(cls.count_posts)
        ]
        Post.objects.bulk_create(cls.posts)

    def test_first_page_contains_ten_records(self):
        cache.clear()
        """Проверяем количество постов на страницах Main, group_list, profile
        равно 10."""
        urls = (
            reverse('posts_app:main'),
            reverse('posts_app:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts_app:profile',
                kwargs={'username': self.author_user.username}
            ),
        )
        for url in urls:
            response = self.client.get(url)
            amount_posts = len(response.context.get('page_obj').object_list)
            self.assertEqual(amount_posts, self.posts_per_first_page)

    def test_second_page_contains_three_records(self):
        """На страницах main, group_list, profile должно быть по три поста."""
        urls = (
            reverse('posts_app:main') + '?page=2',
            reverse(
                'posts_app:group_list', kwargs={'slug': self.group.slug}
            ) + '?page=2',
            reverse(
                'posts_app:profile',
                kwargs={'username': self.author_user.username}
            ) + '?page=2',
        )
        for url in urls:
            response = self.client.get(url)
            amount_posts = len(response.context.get('page_obj').object_list)
            self.assertEqual(amount_posts, self.posts_per_second_page)
