"""Сериализаторы — здесь проверяются все входящие данные (POST/PUT)."""
from django.utils import timezone
from rest_framework import serializers

from .models import Booking, Category, Comment, Customer, CustomerProfile, Tour


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]

    def validate_name(self, value):
        value = value.strip().lower()
        if not value:
            raise serializers.ValidationError("Название категории не может быть пустым.")
        if Category.objects.filter(name=value).exclude(pk=getattr(self.instance, "pk", None)).exists():
            raise serializers.ValidationError("Такая категория уже существует.")
        return value


class TourSerializer(serializers.ModelSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), many=True, allow_empty=False
    )

    class Meta:
        model = Tour
        fields = ["id", "title", "description", "price", "duration_hours", "categories"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Цена должна быть больше нуля.")
        return value

    def validate_duration_hours(self, value):
        if value == 0:
            raise serializers.ValidationError("Длительность должна быть больше нуля.")
        return value


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id", "full_name", "email"]


class CustomerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ["id", "customer", "phone", "riding_experience"]

    def validate_phone(self, value):
        digits = value.replace("+", "").replace(" ", "").replace("-", "")
        if not digits.isdigit() or not 9 <= len(digits) <= 15:
            raise serializers.ValidationError("Некорректный номер телефона.")
        return value


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ["id", "customer", "tour", "date", "time", "created_at"]
        read_only_fields = ["created_at"]
        # Проверку уникальности (customer, date, time) делаем сами в validate(),
        # чтобы вернуть понятное сообщение.
        validators = []

    def validate_date(self, value):
        if value < timezone.localdate():
            raise serializers.ValidationError("Нельзя купить тур на прошедшую дату.")
        return value

    def validate(self, attrs):
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        date = attrs.get("date", getattr(self.instance, "date", None))
        time = attrs.get("time", getattr(self.instance, "time", None))
        clash = Booking.objects.filter(customer=customer, date=date, time=time)
        if self.instance:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise serializers.ValidationError(
                "Один человек может купить только один тур на определённый день и время."
            )
        return attrs


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["id", "customer", "tour", "text", "created_at"]
        read_only_fields = ["created_at"]

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Комментарий не может быть пустым.")
        return value.strip()

    def validate(self, attrs):
        customer = attrs.get("customer", getattr(self.instance, "customer", None))
        tour = attrs.get("tour", getattr(self.instance, "tour", None))
        if not Comment.customer_visited_tour(customer, tour):
            raise serializers.ValidationError(
                "Комментировать можно только туры, в которых вы были."
            )
        return attrs
