"""
Views for the EveryCheese cheese catalogue.

Author: Sai Saketh Gooty Kase
"""

import json
import logging

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Avg, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    UpdateView,
)

from .models import Cheese, Rating

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------


class CreatorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Allow access only to the cheese's creator."""

    def test_func(self) -> bool:
        cheese = get_object_or_404(Cheese, slug=self.kwargs["slug"])
        return (
            cheese.creator == self.request.user
            or self.request.user.is_staff
        )


# ---------------------------------------------------------------------------
# Cheese CRUD views
# ---------------------------------------------------------------------------


class CheeseListView(ListView):
    """Paginated, searchable list of all cheeses."""

    model = Cheese
    paginate_by = 12

    def get_queryset(self):
        qs = (
            Cheese.objects.select_related("creator")
            .annotate(avg_score=Avg("ratings__score"))
            .order_by("name")
        )
        query = self.request.GET.get("q", "").strip()
        firmness = self.request.GET.get("firmness", "").strip()
        if query:
            qs = qs.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )
        if firmness:
            qs = qs.filter(firmness=firmness)
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["query"] = self.request.GET.get("q", "")
        ctx["selected_firmness"] = self.request.GET.get("firmness", "")
        ctx["firmness_choices"] = Cheese.Firmness.choices
        return ctx


class CheeseDetailView(DetailView):
    """Cheese detail with aggregated rating and current-user's rating."""

    model = Cheese

    def get_queryset(self):
        return Cheese.objects.select_related("creator").annotate(
            avg_score=Avg("ratings__score")
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        ctx["user_rating"] = 0
        if user.is_authenticated:
            rating = Rating.objects.filter(
                creator=user, cheese=self.object
            ).first()
            ctx["user_rating"] = rating.score if rating else 0
        ctx["rating_range"] = range(1, 6)
        return ctx


class CheeseCreateView(LoginRequiredMixin, CreateView):
    """Create a new cheese entry. Only accessible to authenticated users."""

    model = Cheese
    fields = ["name", "description", "firmness", "country_of_origin"]
    action = "Add"

    def form_valid(self, form):
        form.instance.creator = self.request.user
        messages.success(
            self.request,
            f'"{form.instance.name}" has been added to the index!',
        )
        log.info(
            "Cheese created: %s by %s",
            form.instance.name,
            self.request.user.username,
        )
        return super().form_valid(form)


class CheeseUpdateView(CreatorRequiredMixin, UpdateView):
    """
    Update cheese details. Restricted to the original creator or staff.
    Also persists the user's rating on the same POST.
    """

    model = Cheese
    fields = ["name", "description", "firmness", "country_of_origin"]
    action = "Update"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        rating = Rating.objects.filter(
            creator=self.request.user, cheese=self.object
        ).first()
        ctx["user_rating"] = rating.score if rating else 0
        ctx["rating_range"] = range(1, 6)
        return ctx

    def form_valid(self, form):
        raw = self.request.POST.get("rating", "0")
        try:
            score = max(0, min(5, int(raw)))
        except (TypeError, ValueError):
            score = 0

        if score > 0:
            Rating.objects.update_or_create(
                creator=self.request.user,
                cheese=self.object,
                defaults={"score": score},
            )
        messages.success(self.request, "Cheese updated successfully.")
        return super().form_valid(form)


class CheeseDeleteView(CreatorRequiredMixin, DeleteView):
    """Delete a cheese. Restricted to creator or staff only."""

    model = Cheese
    success_url = reverse_lazy("cheeses:list")

    def form_valid(self, form):
        name = self.object.name
        messages.success(self.request, f'"{name}" has been removed.')
        log.info(
            "Cheese deleted: %s by %s",
            name,
            self.request.user.username,
        )
        return super().form_valid(form)


# ---------------------------------------------------------------------------
# AJAX rating endpoint
# ---------------------------------------------------------------------------


class RateCheeseView(LoginRequiredMixin, View):
    """
    Accept a POST with {"score": 1-5} and upsert the rating.
    Returns JSON with the new average.
    """

    def post(self, request, slug: str):
        cheese = get_object_or_404(Cheese, slug=slug)
        try:
            payload = json.loads(request.body)
            score = int(payload.get("score", 0))
        except (json.JSONDecodeError, TypeError, ValueError):
            return JsonResponse(
                {"error": "Invalid payload. Expected {'score': 1-5}."},
                status=400,
            )

        if not 1 <= score <= 5:
            return JsonResponse(
                {"error": "Score must be between 1 and 5."},
                status=400,
            )

        Rating.objects.update_or_create(
            creator=request.user,
            cheese=cheese,
            defaults={"score": score},
        )

        new_avg = cheese.average_rating
        log.debug(
            "Rating upserted: cheese=%s user=%s score=%d avg=%.1f",
            cheese.slug,
            request.user.username,
            score,
            new_avg,
        )
        return JsonResponse(
            {"average": new_avg, "user_score": score}, status=200
        )
