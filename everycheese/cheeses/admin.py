"""Admin configuration for the CheeseAtlas cheese catalogue."""

from django.contrib import admin
from django.db.models import Avg
from django.utils.html import format_html

from .models import Cheese, Rating


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ("cheese", "creator", "score", "star_display")
    list_filter = ("score",)
    raw_id_fields = ("creator", "cheese")
    search_fields = ("cheese__name", "creator__username")

    def star_display(self, obj: Rating) -> str:
        filled = "★" * obj.score
        empty = "☆" * (5 - obj.score)
        return format_html(
            '<span style="color:#E8A838; font-size:1.1rem;">{}</span>'
            '<span style="color:#ccc;">{}</span>',
            filled,
            empty,
        )

    star_display.short_description = "Stars"


class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    fields = ("creator", "score")
    raw_id_fields = ("creator",)
    readonly_fields = ()


@admin.register(Cheese)
class CheeseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "country_of_origin",
        "firmness",
        "creator",
        "avg_rating_display",
        "created",
        "modified",
    )
    list_filter = ("firmness", "country_of_origin")
    search_fields = ("name", "description", "creator__username")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("slug", "created", "modified", "avg_rating_display")
    raw_id_fields = ("creator",)
    date_hierarchy = "created"
    ordering = ("name",)
    inlines = [RatingInline]

    fieldsets = (
        (
            "Cheese Details",
            {
                "fields": (
                    "name",
                    "slug",
                    "description",
                    "firmness",
                    "country_of_origin",
                )
            },
        ),
        (
            "Ownership & Timestamps",
            {
                "fields": ("creator", "created", "modified", "avg_rating_display"),
                "classes": ("collapse",),
            },
        ),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return (
            qs.annotate(_avg=Avg("ratings__score")).select_related("creator")
        )

    def avg_rating_display(self, obj: Cheese) -> str:
        avg = getattr(obj, "_avg", None)
        if avg is None:
            avg = obj.average_rating
        filled = int(round(avg or 0))
        stars = "★" * filled + "☆" * (5 - filled)
        return format_html(
            '<span style="color:#E8A838;">{}</span> ({:.1f})',
            stars,
            avg or 0.0,
        )

    avg_rating_display.short_description = "Avg Rating"
    avg_rating_display.admin_order_field = "_avg"
