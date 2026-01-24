from rest_framework import viewsets

from books.permissions import IsOwnerOrReadOnly
from borrowings.models import Borrowing
from borrowings.serializers import BorrowingDetailSerializer, BorrowingSerializer


class BorrowingViewSet(viewsets.ModelViewSet):
    queryset = Borrowing.objects.all()
    permission_classes = (IsOwnerOrReadOnly,)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return BorrowingDetailSerializer
        return BorrowingSerializer
