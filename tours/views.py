"""API-представления стартапа «Конные туры» (Django REST Framework)."""
from rest_framework import viewsets

from .models import Booking, Category, Comment, Customer, CustomerProfile, Tour
from .serializers import (
    BookingSerializer,
    CategorySerializer,
    CommentSerializer,
    CustomerProfileSerializer,
    CustomerSerializer,
    TourSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD для :model:`tours.Category` — ``/api/categories/``."""

    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class TourViewSet(viewsets.ModelViewSet):
    """CRUD для :model:`tours.Tour` — ``/api/tours/``.

    Фильтр по категории: ``/api/tours/?category=конный``.
    """

    serializer_class = TourSerializer

    def get_queryset(self):
        qs = Tour.objects.prefetch_related("categories")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(categories__name=category.lower())
        return qs


class CustomerViewSet(viewsets.ModelViewSet):
    """CRUD для :model:`tours.Customer` — ``/api/customers/``."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class CustomerProfileViewSet(viewsets.ModelViewSet):
    """CRUD для :model:`tours.CustomerProfile` (1 к 1) — ``/api/profiles/``."""

    queryset = CustomerProfile.objects.select_related("customer")
    serializer_class = CustomerProfileSerializer


class BookingViewSet(viewsets.ModelViewSet):
    """Покупка туров :model:`tours.Booking` — ``/api/bookings/``."""

    queryset = Booking.objects.select_related("customer", "tour")
    serializer_class = BookingSerializer


class CommentViewSet(viewsets.ModelViewSet):
    """Отзывы о турах :model:`tours.Comment` — ``/api/comments/``."""

    queryset = Comment.objects.select_related("customer", "tour")
    serializer_class = CommentSerializer
