from rest_framework import serializers

from books.models import Book
from borrowings.models import Borrowing
from users.models import User


class BorrowingSerializer(serializers.ModelSerializer):
    book = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all())
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book",
            "user",
        )


class BorrowingDetailSerializer(BorrowingSerializer):
    book_title = serializers.CharField(source="book.title", read_only=True)
    book_daily_fee = serializers.DecimalField(
        source="book.daily_fee", max_digits=10, decimal_places=2, read_only=True
    )
    user_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Borrowing
        fields = (
            "id",
            "borrow_date",
            "expected_return_date",
            "actual_return_date",
            "book_title",
            "book_daily_fee",
            "user_email",
        )
