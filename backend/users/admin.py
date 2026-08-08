from django.contrib import admin
from unfold.admin import ModelAdmin
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from .models import Address, User


@admin.register(Address)
class AddressAdmin(ModelAdmin):
    list_display = ("user", "label", "full_name", "city", "country", "is_default")
    list_filter = ("country", "is_default")
    search_fields = ("full_name", "city", "user__username", "user__email")


@admin.register(User)
class UserAdmin(ModelAdmin):
    model = User
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm
    list_display = ("username", "email", "first_name", "last_name", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "email")}),
        ("Profile", {"fields": ("phone_number", "default_shipping_address")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active", "is_staff", "is_superuser", "groups", "user_permissions",
                ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2"),
            },
        ),
    )
