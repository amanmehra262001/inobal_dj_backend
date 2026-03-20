from django.contrib import admin

from .models import Nominations, NominationForm, NominationFormField


class NominationFormFieldInline(admin.TabularInline):
    model = NominationFormField
    extra = 1
    fields = (
        "order",
        "key",
        "label",
        "field_type",
        "required",
        "options",
        "help_text",
    )
    show_change_link = True


@admin.register(NominationForm)
class NominationFormAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name", "description")
    readonly_fields = ("created_at", "updated_at")
    inlines = [NominationFormFieldInline]


@admin.register(Nominations)
class NominationsAdmin(admin.ModelAdmin):
    list_display = ("id", "form", "created_at", "updated_at")
    list_filter = ("form",)
    search_fields = ("id",)
    readonly_fields = ("created_at", "updated_at")

from django.contrib import admin

# Register your models here.
