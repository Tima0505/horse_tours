"""Тесты стартапа «Конные туры».

Проверяются связи (1:1, 1:N, M:N), бизнес-правила и все отправки данных (POST)
в API. Запуск: ``python manage.py test -v 2``.
"""
from datetime import time, timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Booking, Category, Comment, Customer, CustomerProfile, Tour

TODAY = timezone.localdate()
TOMORROW = TODAY + timedelta(days=1)
YESTERDAY = TODAY - timedelta(days=1)


class BaseData:
    """Общие тестовые данные."""

    def make_data(self):
        self.horse = Category.objects.create(name="конный")
        self.walk = Category.objects.create(name="пеший")
        self.moto = Category.objects.create(name="мото")

        self.tour = Tour.objects.create(title="Сон-Куль на лошадях", price=5000)
        self.tour.categories.add(self.horse, self.walk)
        self.tour2 = Tour.objects.create(title="Иссык-Куль на мото", price=7000)
        self.tour2.categories.add(self.moto)

        self.timur = Customer.objects.create(full_name="Тимур", email="timur@example.com")
        self.aida = Customer.objects.create(full_name="Аида", email="aida@example.com")


# ---------------------------------------------------------------- связи
class RelationsTests(BaseData, TestCase):
    def setUp(self):
        self.make_data()

    def test_one_to_one_profile(self):
        profile = CustomerProfile.objects.create(customer=self.timur, phone="+996555123456")
        self.assertEqual(self.timur.profile, profile)

    def test_one_to_one_second_profile_forbidden(self):
        CustomerProfile.objects.create(customer=self.timur, phone="+996555123456")
        with self.assertRaises(IntegrityError):
            CustomerProfile.objects.create(customer=self.timur, phone="+996700000000")

    def test_one_to_many_customer_bookings(self):
        Booking.objects.create(customer=self.timur, tour=self.tour, date=TOMORROW, time=time(9))
        Booking.objects.create(customer=self.timur, tour=self.tour2, date=TOMORROW, time=time(15))
        self.assertEqual(self.timur.bookings.count(), 2)

    def test_many_to_many_tour_categories(self):
        self.assertEqual(set(self.tour.categories.all()), {self.horse, self.walk})
        self.assertIn(self.tour, self.horse.tours.all())
        self.assertIn(self.tour, self.walk.tours.all())

    def test_category_has_many_tours(self):
        tour3 = Tour.objects.create(title="Ала-Арча верхом", price=3000)
        tour3.categories.add(self.horse)
        self.assertEqual(self.horse.tours.count(), 2)


# ---------------------------------------------------------- бизнес-правила (модели)
class BookingRuleModelTests(BaseData, TestCase):
    def setUp(self):
        self.make_data()

    def test_same_customer_same_slot_forbidden(self):
        Booking.objects.create(customer=self.timur, tour=self.tour, date=TOMORROW, time=time(10))
        with self.assertRaises(IntegrityError), transaction.atomic():
            Booking.objects.create(customer=self.timur, tour=self.tour2, date=TOMORROW, time=time(10))

    def test_other_customer_same_slot_allowed(self):
        Booking.objects.create(customer=self.timur, tour=self.tour, date=TOMORROW, time=time(10))
        Booking.objects.create(customer=self.aida, tour=self.tour, date=TOMORROW, time=time(10))
        self.assertEqual(Booking.objects.count(), 2)


class CommentRuleModelTests(BaseData, TestCase):
    def setUp(self):
        self.make_data()

    def test_visited_tour(self):
        Booking.objects.create(customer=self.timur, tour=self.tour, date=YESTERDAY, time=time(10))
        self.assertTrue(Comment.customer_visited_tour(self.timur, self.tour))

    def test_future_booking_is_not_visit(self):
        Booking.objects.create(customer=self.timur, tour=self.tour, date=TOMORROW, time=time(10))
        self.assertFalse(Comment.customer_visited_tour(self.timur, self.tour))


# ------------------------------------------------------------- отправки данных (API)
class CategoryApiTests(BaseData, APITestCase):
    url = reverse("category-list")

    def setUp(self):
        self.make_data()

    def test_create_category(self):
        r = self.client.post(self.url, {"name": "Велосипедный"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r.data["name"], "велосипедный")

    def test_create_category_empty_name(self):
        r = self.client.post(self.url, {"name": "   "}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_category_duplicate(self):
        r = self.client.post(self.url, {"name": "Конный"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class TourApiTests(BaseData, APITestCase):
    url = reverse("tour-list")

    def setUp(self):
        self.make_data()

    def test_create_tour_with_categories(self):
        data = {"title": "Конно-пеший тур", "price": "4500.00",
                "categories": [self.horse.id, self.walk.id]}
        r = self.client.post(self.url, data, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        tour = Tour.objects.get(pk=r.data["id"])
        self.assertEqual(tour.categories.count(), 2)

    def test_create_tour_without_categories(self):
        r = self.client.post(self.url, {"title": "X", "price": "100", "categories": []}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tour_unknown_category(self):
        r = self.client.post(self.url, {"title": "X", "price": "100", "categories": [999]}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tour_negative_price(self):
        data = {"title": "X", "price": "-5", "categories": [self.horse.id]}
        r = self.client.post(self.url, data, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("price", r.data)

    def test_create_tour_zero_duration(self):
        data = {"title": "X", "price": "10", "duration_hours": 0, "categories": [self.horse.id]}
        r = self.client.post(self.url, data, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_tour_missing_title(self):
        r = self.client.post(self.url, {"price": "10", "categories": [self.horse.id]}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_tours_by_category(self):
        r = self.client.get(self.url, {"category": "мото"})
        self.assertEqual([t["title"] for t in r.data], ["Иссык-Куль на мото"])


class CustomerApiTests(BaseData, APITestCase):
    url = reverse("customer-list")

    def setUp(self):
        self.make_data()

    def test_create_customer(self):
        r = self.client.post(self.url, {"full_name": "Бек", "email": "bek@example.com"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_create_customer_bad_email(self):
        r = self.client.post(self.url, {"full_name": "Бек", "email": "not-an-email"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_customer_duplicate_email(self):
        r = self.client.post(self.url, {"full_name": "Тимур 2", "email": "timur@example.com"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class ProfileApiTests(BaseData, APITestCase):
    url = reverse("profile-list")

    def setUp(self):
        self.make_data()

    def test_create_profile(self):
        data = {"customer": self.timur.id, "phone": "+996 555 123 456", "riding_experience": "beginner"}
        r = self.client.post(self.url, data, format="json")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_second_profile_for_same_customer(self):
        CustomerProfile.objects.create(customer=self.timur, phone="+996555123456")
        r = self.client.post(self.url, {"customer": self.timur.id, "phone": "+996700000000"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_phone(self):
        r = self.client.post(self.url, {"customer": self.timur.id, "phone": "abc"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_experience_choice(self):
        data = {"customer": self.timur.id, "phone": "+996555123456", "riding_experience": "pro"}
        r = self.client.post(self.url, data, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class BookingApiTests(BaseData, APITestCase):
    url = reverse("booking-list")

    def setUp(self):
        self.make_data()

    def post(self, customer, tour, date, t):
        return self.client.post(
            self.url,
            {"customer": customer.id, "tour": tour.id, "date": str(date), "time": t},
            format="json",
        )

    def test_buy_tour(self):
        r = self.post(self.timur, self.tour, TOMORROW, "10:00")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_one_tour_per_day_and_time(self):
        """1 человек может купить только 1 тур на определённый день и время."""
        self.post(self.timur, self.tour, TOMORROW, "10:00")
        r = self.post(self.timur, self.tour2, TOMORROW, "10:00")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Booking.objects.filter(customer=self.timur).count(), 1)

    def test_same_tour_twice_same_slot(self):
        self.post(self.timur, self.tour, TOMORROW, "10:00")
        r = self.post(self.timur, self.tour, TOMORROW, "10:00")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_same_customer_other_time_ok(self):
        self.post(self.timur, self.tour, TOMORROW, "10:00")
        r = self.post(self.timur, self.tour2, TOMORROW, "16:00")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_same_customer_other_day_ok(self):
        self.post(self.timur, self.tour, TOMORROW, "10:00")
        r = self.post(self.timur, self.tour, TOMORROW + timedelta(days=1), "10:00")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_other_customer_same_slot_ok(self):
        self.post(self.timur, self.tour, TOMORROW, "10:00")
        r = self.post(self.aida, self.tour, TOMORROW, "10:00")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_past_date_forbidden(self):
        r = self.post(self.timur, self.tour, YESTERDAY, "10:00")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bad_time_format(self):
        r = self.post(self.timur, self.tour, TOMORROW, "25:99")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unknown_tour(self):
        r = self.client.post(self.url, {"customer": self.timur.id, "tour": 999,
                                        "date": str(TOMORROW), "time": "10:00"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_into_busy_slot_forbidden(self):
        self.post(self.timur, self.tour, TOMORROW, "10:00")
        second = self.post(self.timur, self.tour2, TOMORROW, "12:00").data
        r = self.client.patch(reverse("booking-detail", args=[second["id"]]),
                              {"time": "10:00"}, format="json")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


class CommentApiTests(BaseData, APITestCase):
    url = reverse("comment-list")

    def setUp(self):
        self.make_data()
        # Тимур был на туре вчера
        Booking.objects.create(customer=self.timur, tour=self.tour, date=YESTERDAY, time=time(10))

    def post(self, customer, tour, text):
        return self.client.post(self.url, {"customer": customer.id, "tour": tour.id, "text": text},
                                format="json")

    def test_comment_visited_tour(self):
        r = self.post(self.timur, self.tour, "Отличные лошади!")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)

    def test_several_comments_allowed(self):
        """1 человек может оставить несколько комментариев к туру, где был."""
        self.post(self.timur, self.tour, "Первый отзыв")
        r = self.post(self.timur, self.tour, "Второй отзыв")
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.timur.comments.count(), 2)

    def test_comment_not_visited_tour(self):
        r = self.post(self.timur, self.tour2, "Не был, но скажу")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_other_customer_not_visited(self):
        r = self.post(self.aida, self.tour, "Чужой отзыв")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comment_future_booking_not_allowed(self):
        Booking.objects.create(customer=self.aida, tour=self.tour2, date=TOMORROW, time=time(10))
        r = self.post(self.aida, self.tour2, "Ещё не был")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)

    def test_empty_comment(self):
        r = self.post(self.timur, self.tour, "   ")
        self.assertEqual(r.status_code, status.HTTP_400_BAD_REQUEST)


# ------------------------------------------------------------ документация
class AdminDocsTests(TestCase):
    def setUp(self):
        admin = User.objects.create_superuser("admin", "admin@example.com", "pass12345")
        self.client.force_login(admin)

    def test_docs_index(self):
        self.assertEqual(self.client.get("/admin/doc/").status_code, 200)

    def test_model_docs(self):
        r = self.client.get("/admin/doc/models/tours.booking/")
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "1 тур на определённый день")
