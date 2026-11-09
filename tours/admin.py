from django.contrib import admin

from .models import Booking, Category, Comment, Customer, CustomerProfile, Tour


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["full_name", "email"]
    inlines = [CustomerProfileInline]


@admin.register(Tour)
class TourAdmin(admin.ModelAdmin):
    list_display = ["title", "price", "duration_hours"]
    filter_horizontal = ["categories"]


admin.site.register(Category)
admin.site.register(Booking)
admin.site.register(Comment)
