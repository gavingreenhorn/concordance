from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.shortcuts import reverse
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class PostsURLTests(TestCase):
    """create required test objects"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='nutcase')
        cls.user_random = User.objects.create_user(username='homie')
        cls.group = Group.objects.create(
            title='test title',
            description='test description',
            slug='test-group',
        )
        cls.post = Post.objects.create(
            text='for URL tests',
            author=cls.user_author,
            group=cls.group,
        )
        cls.FAKE_ADDRESS = '/wind/howling'
        cls.CUSTOM_404 = 'core/404.html'
        cls.INDEX = reverse('posts:index')
        cls.CREATE = reverse('posts:post_create')
        cls.DETAIL = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.EDIT = reverse(
            'posts:post_edit',
            kwargs={'pk': cls.post.pk}
        )
        cls.GROUP = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.PROFILE = reverse(
            'posts:profile',
            kwargs={'username': cls.user_author.username}
        )

    def setUp(self):
        """evaluate test urls"""
        self.auth_client = Client()
        self.author_client = Client()
        self.auth_client.force_login(self.user_random)
        self.author_client.force_login(self.user_author)

    @classmethod
    def tearDownClass(cls):
        cache.clear()
        super().tearDownClass()

    def test_urls_guest_access(self):
        """test if unauthenticated user has access to the pages"""
        self.expected_codes = [
            (self.INDEX, self.client, HTTPStatus.OK),
            (self.GROUP, self.client, HTTPStatus.OK),
            (self.CREATE, self.client, HTTPStatus.FOUND),
            (self.CREATE, self.auth_client, HTTPStatus.OK),
            (self.EDIT, self.client, HTTPStatus.FOUND),
            (self.EDIT, self.auth_client, HTTPStatus.FOUND),
            (self.EDIT, self.author_client, HTTPStatus.OK),
            (self.PROFILE, self.client, HTTPStatus.OK),
            (self.DETAIL, self.client, HTTPStatus.OK)
        ]
        for url, client, code in self.expected_codes:
            with self.subTest(client=client, address=url):
                response = client.get(url)
                self.assertEqual(response.status_code, code)

    def test_edit_redirect(self):
        """test if non-author authenticated user is redirected"""
        response = self.auth_client.get(self.EDIT, follow=True)
        self.assertRedirects(
            response,
            self.DETAIL,
            status_code=HTTPStatus.FOUND
        )

    def test_urls_author_access(self):
        """test post author's access to edit"""
        response = self.author_client.get(self.EDIT)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """test if correct templates are used to render requests"""
        self.expected_templates = {
            self.INDEX: 'posts/index.html',
            self.GROUP: 'posts/group_list.html',
            self.CREATE: 'posts/post_form.html',
            self.EDIT: 'posts/post_form.html',
            self.PROFILE: 'posts/profile.html',
            self.DETAIL: 'posts/post_detail.html',
            self.FAKE_ADDRESS: self.CUSTOM_404,
        }
        for address, template in self.expected_templates.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
