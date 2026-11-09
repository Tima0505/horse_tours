import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=50, unique=True, verbose_name="название")),
            ],
            options={"verbose_name": "категория", "verbose_name_plural": "категории", "ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Customer",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=150, verbose_name="ФИО")),
                ("email", models.EmailField(max_length=254, unique=True, verbose_name="email")),
            ],
            options={"verbose_name": "клиент", "verbose_name_plural": "клиенты"},
        ),
        migrations.CreateModel(
            name="Tour",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200, verbose_name="название")),
                ("description", models.TextField(blank=True, verbose_name="описание")),
                ("price", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="цена")),
                ("duration_hours", models.PositiveSmallIntegerField(default=2, verbose_name="длительность (ч)")),
                ("categories", models.ManyToManyField(related_name="tours", to="tours.category", verbose_name="категории")),
            ],
            options={"verbose_name": "тур", "verbose_name_plural": "туры"},
        ),
        migrations.CreateModel(
            name="CustomerProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("phone", models.CharField(max_length=20, verbose_name="телефон")),
                ("riding_experience", models.CharField(
                    choices=[("none", "нет опыта"), ("beginner", "новичок"), ("advanced", "опытный")],
                    default="none", max_length=10, verbose_name="опыт езды")),
                ("customer", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                                  related_name="profile", to="tours.customer",
                                                  verbose_name="клиент")),
            ],
            options={"verbose_name": "профиль клиента", "verbose_name_plural": "профили клиентов"},
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("text", models.TextField(verbose_name="текст")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name="comments", to="tours.customer",
                                               verbose_name="клиент")),
                ("tour", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="comments", to="tours.tour", verbose_name="тур")),
            ],
            options={"verbose_name": "комментарий", "verbose_name_plural": "комментарии",
                     "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField(verbose_name="дата")),
                ("time", models.TimeField(verbose_name="время")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("customer", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                               related_name="bookings", to="tours.customer",
                                               verbose_name="клиент")),
                ("tour", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                           related_name="bookings", to="tours.tour", verbose_name="тур")),
            ],
            options={"verbose_name": "бронирование", "verbose_name_plural": "бронирования"},
        ),
        migrations.AddConstraint(
            model_name="booking",
            constraint=models.UniqueConstraint(fields=("customer", "date", "time"),
                                               name="one_tour_per_customer_slot"),
        ),
    ]
