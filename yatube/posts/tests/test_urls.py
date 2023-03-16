from http import HTTPStatus

from django.test import (
    TestCase,
    Client
)
from django.core.cache import cache

from ..models import (
    Post,
    Group,
    User
)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth_user = User.objects.create_user(username='TestUserAuth')
        cls.author_user = User.objects.create_user(username='TestUserAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author_user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.auth_user)
        self.authorized_client_author.force_login(self.author_user)

    def test_homepage(self):
        """Проверяем работу сайта."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """Проверяем, запрос к несуществующей странице."""
        response = self.guest_client.get('/page_404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_availability_check_for_guest(self):
        """Страница доступна любому пользователю."""
        url_names = (
            '/',
            '/group/test-slug/',
            f'/profile/{self.author_user.username}/',
            f'/posts/{self.post.pk}/',
        )
        for address in url_names:
            with self.subTest():
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_create_availability_check_for_auth_user(self):
        """Страница доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_create_non_availability_check_for_guest_user(self):
        """Страница недоступна гостю."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_url_edit_availability_check_for_author(self):
        """Страница доступна автору."""
        response = self.authorized_client_author.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_edit_non_availability_check_for_auth(self):
        """Страница недоступна авторизованному пользователю, но не автору."""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.pk}/')

    def test_url_edit_non_availability_check_for_guest(self):
        """Страница недоступна гостю."""
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.pk}/edit/')

    def test_urls_uses_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
        cache.clear()
        templates_url_names = [
            {
                'template': 'posts/index.html',
                'url': '/'
            },
            {'template': 'posts/group_list.html',
                'url': f'/group/{self.group.slug}/'},
            {'template': 'posts/group_list.html',
             'url': f'/group/{self.group.slug}/'},
            {'template': 'posts/profile.html',
             'url': f'/profile/{self.author_user.username}/'},
            {'template': 'posts/post_detail.html',
             'url': f'/posts/{self.post.pk}/'},
            {'template': 'posts/post_create.html',
             'url': '/create/'},
            {'template': 'posts/post_create.html',
             'url': f'/posts/{self.post.pk}/edit/'},
        ]
        for item in templates_url_names:
            with self.subTest(address=item['url']):
                response = self.authorized_client_author.get(item['url'])
                self.assertTemplateUsed(response, item['template'])
