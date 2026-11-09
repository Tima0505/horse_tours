from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("categories", views.CategoryViewSet, basename="category")
router.register("tours", views.TourViewSet, basename="tour")
router.register("customers", views.CustomerViewSet, basename="customer")
router.register("profiles", views.CustomerProfileViewSet, basename="profile")
router.register("bookings", views.BookingViewSet, basename="booking")
router.register("comments", views.CommentViewSet, basename="comment")

urlpatterns = router.urls
