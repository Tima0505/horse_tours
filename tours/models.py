"""Модели стартапа «Конные туры».

Связи между таблицами:

* **1 к 1** — :model:`tours.Customer` ↔ :model:`tours.CustomerProfile`
  (у каждого клиента ровно один профиль).
* **1 ко многим** — :model:`tours.Customer` → :model:`tours.Booking`,
  :model:`tours.Customer` → :model:`tours.Comment`,
  :model:`tours.Tour` → :model:`tours.Booking`,
  :model:`tours.Tour` → :model:`tours.Comment`.
* **Многие ко многим** — :model:`tours.Tour` ↔ :model:`tours.Category`
  (тур может быть одновременно «конный» и «пеший»).
"""
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Category(models.Model):
    """Категория тура, например «конный», «пеший» или «мото».

    Связана с :model:`tours.Tour` отношением многие ко многим.
    """

    name = models.CharField("название", max_length=50, unique=True)

    class Meta:
        verbose_name = "категория"
        verbose_name_plural = "категории"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Tour(models.Model):
    """Тур, который можно купить.

    * ``categories`` — связь **многие ко многим** с :model:`tours.Category`.
    * Бронирования — :model:`tours.Booking` (1 ко многим).
    * Отзывы — :model:`tours.Comment` (1 ко многим).
    """

    title = models.CharField("название", max_length=200)
    description = models.TextField("описание", blank=True)
    price = models.DecimalField("цена", max_digits=10, decimal_places=2)
    duration_hours = models.PositiveSmallIntegerField("длительность (ч)", default=2)
    categories = models.ManyToManyField(
        Category, related_name="tours", verbose_name="категории"
    )

    class Meta:
        verbose_name = "тур"
        verbose_name_plural = "туры"

    def clean(self):
        if self.price is not None and self.price <= 0:
            raise ValidationError({"price": "Цена должна быть больше нуля."})

    def __str__(self):
        return self.title


class Customer(models.Model):
    """Клиент (человек, покупающий туры).

    * Профиль — :model:`tours.CustomerProfile` (1 к 1).
    * Бронирования — :model:`tours.Booking` (1 ко многим).
    * Комментарии — :model:`tours.Comment` (1 ко многим).
    """

    full_name = models.CharField("ФИО", max_length=150)
    email = models.EmailField("email", unique=True)

    class Meta:
        verbose_name = "клиент"
        verbose_name_plural = "клиенты"

    def __str__(self):
        return self.full_name


class CustomerProfile(models.Model):
    """Профиль клиента — связь **1 к 1** с :model:`tours.Customer`.

    Хранит данные, нужные инструктору: телефон и опыт верховой езды.
    """

    class Experience(models.TextChoices):
        NONE = "none", "нет опыта"
        BEGINNER = "beginner", "новичок"
        ADVANCED = "advanced", "опытный"

    customer = models.OneToOneField(
        Customer, on_delete=models.CASCADE, related_name="profile", verbose_name="клиент"
    )
    phone = models.CharField("телефон", max_length=20)
    riding_experience = models.CharField(
        "опыт езды", max_length=10, choices=Experience.choices, default=Experience.NONE
    )

    class Meta:
        verbose_name = "профиль клиента"
        verbose_name_plural = "профили клиентов"

    def __str__(self):
        return f"Профиль {self.customer}"


class Booking(models.Model):
    """Покупка тура клиентом на конкретный день и время.

    Правило: **1 человек может купить только 1 тур на определённый день и
    время** — обеспечивается ограничением ``one_tour_per_customer_slot``
    по полям (customer, date, time).
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="bookings", verbose_name="клиент"
    )
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="bookings", verbose_name="тур"
    )
    date = models.DateField("дата")
    time = models.TimeField("время")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "бронирование"
        verbose_name_plural = "бронирования"
        constraints = [
            models.UniqueConstraint(
                fields=["customer", "date", "time"],
                name="one_tour_per_customer_slot",
            )
        ]

    def __str__(self):
        return f"{self.customer} — {self.tour} ({self.date} {self.time})"


class Comment(models.Model):
    """Комментарий клиента к туру.

    Правило: **1 человек может оставить несколько комментариев, но только к
    турам, в которых он был** — т.е. есть :model:`tours.Booking` этого тура
    с датой не позже сегодняшней.
    """

    customer = models.ForeignKey(
        Customer, on_delete=models.CASCADE, related_name="comments", verbose_name="клиент"
    )
    tour = models.ForeignKey(
        Tour, on_delete=models.CASCADE, related_name="comments", verbose_name="тур"
    )
    text = models.TextField("текст")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "комментарий"
        verbose_name_plural = "комментарии"
        ordering = ["-created_at"]

    @staticmethod
    def customer_visited_tour(customer, tour):
        """Был ли клиент на туре (бронирование с датой ≤ сегодня)."""
        return Booking.objects.filter(
            customer=customer, tour=tour, date__lte=timezone.localdate()
        ).exists()

    def clean(self):
        if not self.customer_visited_tour(self.customer, self.tour):
            raise ValidationError("Комментировать можно только туры, в которых вы были.")

    def __str__(self):
        return f"{self.customer} о «{self.tour}»"
