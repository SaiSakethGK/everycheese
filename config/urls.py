"""Root URL configuration for CheeseAtlas."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models import Avg
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

from everycheese.cheeses.models import Cheese, Rating


class HomeView(TemplateView):
    """Home page view that injects live catalogue statistics."""

    template_name = "pages/home.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        User = get_user_model()
        ctx["stats"] = {
            "cheese_count": Cheese.objects.count(),
            "rating_count": Rating.objects.count(),
            "country_count": (
                Cheese.objects.exclude(country_of_origin="")
                .values("country_of_origin")
                .distinct()
                .count()
            ),
            "contributor_count": (
                User.objects.filter(cheeses__isnull=False).distinct().count()
            ),
        }
        ctx["featured"] = (
            Cheese.objects.annotate(avg=Avg("ratings__score"))
            .filter(avg__isnull=False)
            .order_by("-avg")[:6]
        )
        return ctx


urlpatterns = [
    path(
        "",
        HomeView.as_view(),
        name="home",
    ),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    path(
        "cheeses/",
        include("everycheese.cheeses.urls", namespace="cheeses"),
    ),
    path(
        "api/v1/",
        include("everycheese.cheeses.api_urls", namespace="api"),
    ),
    # Django Admin
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/",
        include("everycheese.users.urls", namespace="users"),
    ),
    path("accounts/", include("allauth.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [
            path("__debug__/", include(debug_toolbar.urls))
        ] + urlpatterns
