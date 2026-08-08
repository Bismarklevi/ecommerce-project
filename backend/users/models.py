from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=32, blank=True)
    default_shipping_address = models.TextField(blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self) -> str:
        return self.get_full_name() or self.username


class Address(models.Model):
    """A saved shipping address for a customer. Orders never point back at these --
    Order.shipping_address is a frozen text snapshot taken at checkout time (see
    app.models.Order) -- so editing or deleting a saved Address here can never
    rewrite the shipping details of a past order."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=50, blank=True, help_text="e.g. Home, Office")
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=32, blank=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True, help_text="State/Region/Province")
    country = models.CharField(max_length=100, default="Ghana")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_default", "-created_at"]

    def __str__(self) -> str:
        return f"{self.label or 'Address'} — {self.full_name} ({self.user.username})"

    def save(self, *args, **kwargs):
        # Enforce "at most one default address per user" at the model layer so it
        # holds regardless of which serializer/view path writes the record.
        super().save(*args, **kwargs)
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)

