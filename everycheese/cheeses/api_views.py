"""Django REST Framework API views for the CheeseAtlas cheese catalogue."""

import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Cheese, Rating
from .serializers import CheeseDetailSerializer, CheeseSerializer, RatingSerializer

log = logging.getLogger(__name__)


class CheeseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing, retrieving, creating, updating, and deleting cheeses.

    list:   GET  /api/cheeses/            — paginated, filterable catalogue
    create: POST /api/cheeses/            — authenticated users only
    retrieve: GET /api/cheeses/{slug}/   — full detail with embedded ratings
    update/partial_update/destroy: creator or staff only
    rate:   POST /api/cheeses/{slug}/rate/ — upsert calling user's rating
    """

    queryset = Cheese.objects.select_related("creator").prefetch_related(
        "ratings__creator"
    )
    lookup_field = "slug"
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["firmness", "country_of_origin"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "created", "modified"]
    ordering = ["name"]

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CheeseDetailSerializer
        return CheeseSerializer

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
        log.info(
            "API cheese created: %s by %s",
            serializer.instance.name,
            self.request.user.username,
        )

    def get_permissions(self):
        if self.action in ("update", "partial_update", "destroy"):
            from rest_framework.permissions import IsAdminUser

            return [IsAdminUser()]
        return super().get_permissions()

    @action(detail=True, methods=["post"], url_path="rate")
    def rate(self, request, slug=None):
        """Upsert the authenticated user's rating for this cheese."""
        cheese = self.get_object()
        score = request.data.get("score")
        if score is None:
            return Response(
                {"error": "score is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = RatingSerializer(
            data={"score": score, "cheese": cheese.pk}
        )
        serializer.is_valid(raise_exception=True)
        Rating.objects.update_or_create(
            creator=request.user,
            cheese=cheese,
            defaults={"score": serializer.validated_data["score"]},
        )
        return Response(
            {"average": cheese.average_rating},
            status=status.HTTP_200_OK,
        )
