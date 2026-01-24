from django.utils.timezone import now
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


class BorrowingCreateSerializer(serializers.ModelSerializer):
    book_id = serializers.PrimaryKeyRelatedField(
        queryset=Book.objects.all(), source="book"
    )

    class Meta:
        model = Borrowing
        fields = ("book_id", "expected_return_date")

    def validate_expected_return_date(self, value):
        if value <= now().date():
            raise serializers.ValidationError(
                "expected_return_date must be in the future"
            )
        return value

    def validate(self, attrs):
        book = attrs["book"]
        if book.inventory <= 0:
            raise serializers.ValidationError({"book_id": "This book is out of stock"})
        return attrs

    def create(self, validated_data):
        request = self.context["request"]

        borrowing = Borrowing.objects.create(
            user=request.user, borrow_date=now().date(), **validated_data
        )

        book = borrowing.book
        book.inventory -= 1
        book.save(update_fields=("inventory",))

        return borrowing
