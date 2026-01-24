from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.timezone import now
from rest_framework import status
from rest_framework.test import APITestCase

from books.models import Book
from borrowings.models import Borrowing


class BorrowingsApiTests(APITestCase):
    def setUp(self):
        self.list_url = reverse("borrowings:borrowings-list")

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

    def test_create_borrowing_decreases_inventory_and_sets_borrow_date(self):
        user = self._create_user()
        book = self._create_book(inventory=2)
        self.client.force_authenticate(user=user)

        payload = {
            "book_id": book.id,
            "expected_return_date": now().date() + timedelta(days=3),
        }
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        book.refresh_from_db()
        self.assertEqual(book.inventory, 1)

        borrowing = Borrowing.objects.get(user=user, book=book)
        self.assertEqual(borrowing.user, user)
        self.assertEqual(borrowing.book, book)
        self.assertEqual(borrowing.borrow_date, now().date())

    def test_create_borrowing_expected_return_date_must_be_future(self):
        user = self._create_user()
        book = self._create_book(inventory=2)
        self.client.force_authenticate(user=user)

        payload = {"book_id": book.id, "expected_return_date": now().date()}
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("expected_return_date", res.data)

    def test_create_borrowing_out_of_stock(self):
        user = self._create_user()
        book = self._create_book(inventory=0)
        self.client.force_authenticate(user=user)

        payload = {
            "book_id": book.id,
            "expected_return_date": now().date() + timedelta(days=2),
        }
        res = self.client.post(self.list_url, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("book_id", res.data)

    def test_list_borrowings_user_sees_only_own(self):
        user1 = self._create_user(email="u1@example.com")
        user2 = self._create_user(email="u2@example.com")
        book = self._create_book(inventory=5)

        Borrowing.objects.create(
            user=user1,
            book=book,
            borrow_date=now().date(),
            expected_return_date=now().date() + timedelta(days=3),
        )
        Borrowing.objects.create(
            user=user2,
            book=book,
            borrow_date=now().date(),
            expected_return_date=now().date() + timedelta(days=3),
        )

        self.client.force_authenticate(user=user1)
        res = self.client.get(self.list_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["user"], user1.id)

    def test_list_borrowings_staff_sees_all_and_can_filter_by_user_id(self):
        staff = self._create_user(email="staff@example.com", is_staff=True)
        user1 = self._create_user(email="u1@example.com")
        user2 = self._create_user(email="u2@example.com")
        book = self._create_book(inventory=5)

        b1 = Borrowing.objects.create(
            user=user1,
            book=book,
            borrow_date=now().date(),
            expected_return_date=now().date() + timedelta(days=3),
        )
        Borrowing.objects.create(
            user=user2,
            book=book,
            borrow_date=now().date(),
            expected_return_date=now().date() + timedelta(days=3),
        )

        self.client.force_authenticate(user=staff)

        res_all = self.client.get(self.list_url)
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_all.data), 2)

        res_filtered = self.client.get(self.list_url, {"user_id": user1.id})
        self.assertEqual(res_filtered.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_filtered.data), 1)
        self.assertEqual(res_filtered.data[0]["id"], b1.id)

    def test_filter_is_active_true_false(self):
        staff = self._create_user(email="staff@example.com", is_staff=True)
        user = self._create_user(email="u1@example.com")
        book = self._create_book(inventory=5)

        active = Borrowing.objects.create(
            user=user,
            book=book,
            borrow_date=now().date(),
            expected_return_date=now().date() + timedelta(days=3),
            actual_return_date=None,
        )
        returned = Borrowing.objects.create(
            user=user,
            book=book,
            borrow_date=now().date(),
            expected_return_date=now().date() + timedelta(days=3),
            actual_return_date=now().date(),
        )

        self.client.force_authenticate(user=staff)

        res_active = self.client.get(self.list_url, {"is_active": "true"})
        self.assertEqual(res_active.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in res_active.data], [active.id])

        res_returned = self.client.get(self.list_url, {"is_active": "false"})
        self.assertEqual(res_returned.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in res_returned.data], [returned.id])

    def test_retrieve_borrowing_uses_detail_serializer_fields(self):
        staff = self._create_user(email="staff@example.com", is_staff=True)
        user = self._create_user(email="u1@example.com")
        book = self._create_book(title="X", daily_fee="3.25", inventory=5)

        borrowing = Borrowing.objects.create(
            user=user,
            book=book,
            borrow_date=now().date(),
            expected_return_date=now().date() + timedelta(days=3),
        )

        self.client.force_authenticate(user=staff)
        detail_url = reverse("borrowings:borrowings-detail", args=[borrowing.id])

        res = self.client.get(detail_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("book_title", res.data)
        self.assertIn("book_daily_fee", res.data)
        self.assertIn("user_email", res.data)
        self.assertEqual(res.data["book_title"], "X")
        self.assertEqual(res.data["user_email"], user.email)
