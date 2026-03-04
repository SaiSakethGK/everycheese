"""DRF serializers for the CheeseAtlas cheese catalogue."""

from rest_framework import serializers

from .models import Cheese, Rating


class RatingSerializer(serializers.ModelSerializer):
    creator_username = serializers.ReadOnlyField(source="creator.username")

    class Meta:
        model = Rating
        fields = ["id", "score", "creator_username", "cheese"]
        read_only_fields = ["id", "creator_username"]

    def validate_score(self, value: int) -> int:
        if not 1 <= value <= 5:
            raise serializers.ValidationError(
                "Score must be between 1 and 5."
            )
        return value


class CheeseSerializer(serializers.ModelSerializer):
    creator_username = serializers.ReadOnlyField(
        source="creator.username", default=None
    )
    average_rating = serializers.FloatField(read_only=True)
    url = serializers.HyperlinkedIdentityField(
        view_name="api:cheese-detail", lookup_field="slug"
    )

    class Meta:
        model = Cheese
        fields = [
            "url",
            "id",
            "name",
            "slug",
            "description",
            "country_of_origin",
            "firmness",
            "creator_username",
            "average_rating",
            "created",
            "modified",
        ]
        read_only_fields = [
            "id",
            "slug",
            "creator_username",
            "average_rating",
            "created",
            "modified",
        ]


class CheeseDetailSerializer(CheeseSerializer):
    """Extended serializer that embeds per-cheese ratings."""

    ratings = RatingSerializer(many=True, read_only=True)

    class Meta(CheeseSerializer.Meta):
        fields = CheeseSerializer.Meta.fields + ["ratings"]
