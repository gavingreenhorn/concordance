from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

User = get_user_model()


class UsersURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_random = User.objects.create_user(username='homie')
        cls.guest_client = Client()
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user_random)
        cls.uid64 = urlsafe_base64_encode(force_bytes(cls.user_random))
        cls.token = default_token_generator.make_token(cls.user_random)

    def setUp(self):
        """evaluate test urls"""
        self.urls = {
            '/auth/signup': 'users/signup.html',
            '/auth/logout': 'users/logged_out.html',
            '/auth/login': 'users/login.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/password_reset/done': 'users/password_reset_done.html',
            f'/reset/{self.uid64}/{self.token}/':
                'users/password_reset_confirm.html',
            '/auth/reset/done': 'users/password_reset_complete.html',
            '/auth/password_change': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
        }

    def test_get_signup(self):
        response = self.guest_client.get('/auth/signup/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_get_login(self):
        response = self.guest_client.get('/auth/login/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
