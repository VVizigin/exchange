from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post, User


class PostTests(TestCase):
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

    def test_pages_uses_correct_template(self):
        """Проверяем, что URL-адрес использует соответствующий шаблон."""
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
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        """Шаблон главной страницы сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts_app:main'))
        post_info = response.context.get('page_obj')[0]
        self.assertEqual(post_info, self.post)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        url = reverse(
            'posts_app:group_list', kwargs={'slug': self.group.slug}
        )
        response = self.authorized_client.get(url)
        post_info = response.context.get('page_obj')[0]
        self.assertEqual(post_info, self.post)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        url = reverse(
            'posts_app:profile',
            kwargs={'username': PostTests.author_user}
        )
        response = self.authorized_client_author.get(url)
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
        response = self.authorized_client_author.get(url)
        post_info = response.context.get('post')
        self.assertEqual(post_info, self.post)

    def test_edit_post_show_correct_context(self):
        """Шаблон редактирования поста create_post сформирован
        с правильным контекстом.
        """
        url = reverse('posts_app:post_edit', kwargs={'post_id': self.post.pk})
        response = self.authorized_client_author.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_correct_context(self):
        """Шаблон создания поста create_post сформирован
        с правильным контекстом.
        """
        url = reverse('posts_app:post_create')
        response = self.authorized_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_create_post_show_home_group_list_profile_pages(self):
        """Созданный пост отобразился на главной, на странице группы,
        в профиле пользователя.
        """
        urls = (
            reverse('posts_app:main'),
            reverse('posts_app:group_list', kwargs={'slug': self.group.slug}),
            reverse(
                'posts_app:profile',
                kwargs={'username': self.author_user.username}
            ),
        )
        for url in urls:
            response = self.authorized_client_author.get(url)
            post_info = response.context.get('page_obj')[0]
            # self.assertEqual(post_info, self.post)
            self.assertIn(self.post, response.context['page_obj'], post_info)

    def test_post_not_another_group(self):
        """Созданный пост не попал в группу, для которой не был
        предназначен"""
        another_group = Group.objects.create(
            title='Дополнительная тестовая группа',
            slug='test-another-slug',
            description='Тестовое описание дополнительной группы',
        )
        response = self.authorized_client.get(
            reverse('posts_app:group_list',
                    kwargs={'slug': another_group.slug})
        )
        # self.assertEqual(len(response.context['page_obj']), 0)
        self.assertNotIn(self.post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        count_posts = 13
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
            for i in range(count_posts)
        ]
        Post.objects.bulk_create(cls.posts)

    def test_first_page_contains_ten_records(self):
        """Проверяем количество постов на страницах Main, group_list, profile
        равно 10."""
        posts_per_first_page = 10
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
            self.assertEqual(amount_posts, posts_per_first_page)

    def test_second_page_contains_three_records(self):
        """На страницах main, group_list, profile должно быть по три поста."""
        posts_per_second_page = 3
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
            self.assertEqual(amount_posts, posts_per_second_page)
