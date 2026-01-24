from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book


class BooksApiTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("books:book-list")

    def _create_user(
        self, email="user@example.com", password="testpass123", is_staff=False
    ):
        return get_user_model().objects.create_user(
            email=email, password=password, is_staff=is_staff
        )

    def _create_book(self, **kwargs):
        defaults = {
            "title": "Test Book",
            "author": "Test Author",
            "cover": "HARD",
            "inventory": 3,
            "daily_fee": "10.50",
        }
        defaults.update(kwargs)
        return Book.objects.create(**defaults)

    def test_books_list_requires_auth_even_for_safe_methods(self):
        self._create_book()

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_can_read_books_list(self):
        self._create_book()
        user = self._create_user()
        self.client.force_authenticate(user=user)

        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_user_cannot_create_book(self):
        user = self._create_user()
        self.client.force_authenticate(user=user)

        payload = {
            "title": "New Book",
            "author": "New Author",
            "cover": "SOFT",
            "inventory": 5,
            "daily_fee": "7.00",
        }
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_staff_can_create_update_delete_book(self):
        staff = self._create_user(email="staff@example.com", is_staff=True)
        self.client.force_authenticate(user=staff)

        create_payload = {
            "title": "Admin Book",
            "author": "Admin Author",
            "cover": "HARD",
            "inventory": 10,
            "daily_fee": "12.00",
        }
        res = self.client.post(self.list_url, create_payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        book_id = res.data["id"]

        detail_url = reverse("books:book-detail", args=[book_id])

        patch_res = self.client.patch(detail_url, {"inventory": 9})
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertEqual(patch_res.data["inventory"], 9)

        delete_res = self.client.delete(detail_url)
        self.assertEqual(delete_res.status_code, status.HTTP_204_NO_CONTENT)
