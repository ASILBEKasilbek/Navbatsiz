from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.validators import MinLengthValidator, MinValueValidator


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Region(TimestampedModel):
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        unique=True,
        verbose_name="Hudud nomi"
    )
    slug = models.SlugField(max_length=120, unique=True, blank=True, help_text="URL uchun qisqa nom")

    class Meta:
        verbose_name = "Hudud"
        verbose_name_plural = "Hududlar"
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(TimestampedModel):
    name = models.CharField(
        max_length=100,
        validators=[MinLengthValidator(2)],
        unique=True,
        verbose_name="Kategoriya nomi"
    )
    slug = models.SlugField(max_length=120, unique=True, blank=True, help_text="URL uchun qisqa nom")
    description = models.TextField(blank=True, verbose_name="Kategoriya tavsifi")

    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"
        ordering = ['name']

    def __str__(self):
        return self.name


class Organization(TimestampedModel):
    name = models.CharField(
        max_length=200,
        validators=[MinLengthValidator(3)],
        verbose_name="Tashkilot nomi"
    )
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name='organizations',
        verbose_name="Hudud"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='organizations',
        verbose_name="Kategoriya"
    )
    address = models.TextField(verbose_name="Manzil")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, verbose_name="Email")
    working_hours = models.CharField(max_length=100, blank=True, verbose_name="Ish vaqti")
    location = models.CharField(
        max_length=100,
        blank=True,
        help_text="Geo-lokatsiya (masalan, kenglik va uzunlik)",
        verbose_name="Joylashuv"
    )

    class Meta:
        verbose_name = "Tashkilot"
        verbose_name_plural = "Tashkilotlar"
        ordering = ['name']
        unique_together = ['name', 'region']

    def __str__(self):
        return f"{self.name} ({self.region})"


class TimeSlot(TimestampedModel):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='time_slots',
        verbose_name="Tashkilot"
    )
    start_time = models.DateTimeField(verbose_name="Boshlanish vaqti")
    duration = models.PositiveIntegerField(
        default=15,
        validators=[MinValueValidator(5)],
        help_text="Vaqt oralig‘i (daqiqalarda)",
        verbose_name="Davomiylik"
    )
    is_booked = models.BooleanField(default=False, verbose_name="Band qilinganmi")
    max_bookings = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        help_text="Ushbu vaqt oralig‘ida nechta navbat band qilinishi mumkin",
        verbose_name="Maksimal navbatlar"
    )
    current_bookings = models.PositiveIntegerField(default=0, verbose_name="Joriy navbatlar")

    class Meta:
        verbose_name = "Vaqt oralig‘i"
        verbose_name_plural = "Vaqt oralig‘lari"
        ordering = ['start_time']
        unique_together = ['organization', 'start_time']

    def __str__(self):
        return f"{self.organization} - {self.start_time.strftime('%Y-%m-%d %H:%M')}"

    def is_available(self):
        return not self.is_booked and self.current_bookings < self.max_bookings


class Booking(TimestampedModel):
    STATUS_CHOICES = [
        ('pending', 'Kutmoqda'),
        ('confirmed', 'Tasdiqlangan'),
        ('cancelled', 'Bekor qilingan'),
        ('completed', 'Yakunlangan'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Foydalanuvchi"
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='bookings',
        verbose_name="Vaqt oralig‘i"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Holati"
    )
    booking_code = models.CharField(
        max_length=50,
        unique=True,
        blank=True,
        verbose_name="Navbat kodi"
    )
    notes = models.TextField(blank=True, verbose_name="Qaydlar")

    class Meta:
        verbose_name = "Navbat"
        verbose_name_plural = "Navbatlar"
        ordering = ['-created_at']
        unique_together = ['user', 'time_slot']

    def __str__(self):
        return f"{self.user.username} - {self.time_slot}"

    def save(self, *args, **kwargs):
        if not self.booking_code:
            self.booking_code = f"NAV-{timezone.now().strftime('%Y%m%d%H%M%S')}-{self.user.id}"
        super().save(*args, **kwargs)


class Profile(TimestampedModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=100, blank=True, verbose_name="Ism")
    last_name = models.CharField(max_length=100, blank=True, verbose_name="Familiya")
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Telefon raqami")

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profillar"

    def __str__(self):
        return f"{self.user.username} profili"