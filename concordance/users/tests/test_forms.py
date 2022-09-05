from django.test import TestCase, Client
from django import forms
from django.shortcuts import reverse
from django.contrib.auth import get_user_model

from ..forms import CreationForm


User = get_user_model()


class TestSignupForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SIGNUP = reverse('users:signup')
        cls.PASSWORD = 'myawesomepassword01'
        cls.EXPECTED_FIELDS = {
            'first_name': forms.CharField,
            'last_name': forms.CharField,
            'username': forms.CharField,
            'email': forms.EmailField,
            'password1': forms.CharField,
            'password2': forms.CharField,
        }
        cls.EXPECTED_HTML = {
            'first_name': ('<input type="text" name="first_name" '
                           'maxlength="30" id="id_first_name">'),
            'last_name': ('<input type="text" name="last_name" '
                          'maxlength="150" id="id_last_name">'),
            'username': ('<input type="text" name="username" maxlength="150" '
                         'autofocus required id="id_username">'),
            'email': ('<input type="email" name="email" '
                      'maxlength="254" id="id_email">'),
            'password1': ('<input type="password" name="password1" '
                          'required id="id_password1">'),
            'password2': ('<input type="password" name="password2" '
                          'required id="id_password2">'),
        }
        cls.DATA_TO_POST = {
            'first_name': 'Spazz',
            'last_name': 'Maticus',
            'username': 'ThatSpazz',
            'email': 'thatspazz@sadboyz.com',
            'password1': cls.PASSWORD,
            'password2': cls.PASSWORD,
        }

    @staticmethod
    def create_user(test_client):
        test_client.post(
            path=TestSignupForm.SIGNUP,
            data=TestSignupForm.DATA_TO_POST
        )

    def setUp(self):
        self.form = CreationForm()
        self.test_client = Client()

    def test_expected_fields_present(self):
        """test if the fields are present"""
        for field in self.EXPECTED_FIELDS:
            with self.subTest(field_name=field):
                self.assertIn(field, self.form.fields)

    def test_field_types(self):
        """test if the fields are of correct types"""
        for field_name, field_type in self.EXPECTED_FIELDS.items():
            with self.subTest(field_name=field_name):
                field = self.form.fields.get(field_name)
                self.assertIsInstance(field, field_type)

    def test_create_form_is_rendered(self):
        """test if the fields are rendered correctly"""
        for field, html in self.EXPECTED_HTML.items():
            with self.subTest(field_name=field):
                self.assertInHTML(html, str(self.form))

    def test_count_increment(self):
        """test if user objects count is incremented"""
        self.user_count = User.objects.count()
        TestSignupForm.create_user(self.test_client)
        self.assertEqual(User.objects.count(), self.user_count + 1)

    def test_correct_fields(self):
        """test if new user object is created correctly"""
        TestSignupForm.create_user(self.test_client)
        new_user = User.objects.last()
        for field, value in self.DATA_TO_POST.items():
            if not field.startswith('password'):
                with self.subTest(field=field):
                    self.assertEqual(getattr(new_user, field), value)
        self.assertTrue(new_user.check_password(self.PASSWORD))
