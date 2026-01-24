from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class UsersApiTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("users:register")
        self.token_url = reverse("users:token_obtain_pair")
        self.me_url = reverse("users:manage-user")

    def test_register_user_success(self):
        payload = {"email": "user@example.com", "password": "testpass123"}

        res = self.client.post(self.register_url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_register_user_password_too_short(self):
        payload = {"email": "user@example.com", "password": "1234"}

        res = self.client.post(self.register_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(
            get_user_model().objects.filter(email=payload["email"]).exists()
        )

    def test_create_token_for_user(self):
        user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        payload = {"email": user.email, "password": "testpass123"}

        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_create_token_bad_credentials(self):
        get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        payload = {"email": "user@example.com", "password": "wrongpass"}

        res = self.client.post(self.token_url, payload)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access", res.data)

    def test_me_requires_auth(self):
        res = self.client.get(self.me_url)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_retrieve_me_success(self):
        user = get_user_model().objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.client.force_authenticate(user=user)

        res = self.client.get(self.me_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["email"], user.email)
        self.assertIn("id", res.data)

    def test_update_me_password_hashes(self):
        user = get_user_model().objects.create_user(
            email="user@example.com", password="oldpass123"
        )
        self.client.force_authenticate(user=user)

        payload = {"password": "newpass123"}
        res = self.client.patch(self.me_url, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password("newpass123"))
