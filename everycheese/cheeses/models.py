"""
Cheese models for the EveryCheese application.

Author: Sai Saketh Gooty Kase
"""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse

from autoslug import AutoSlugField
from django_countries.fields import CountryField
from model_utils.models import TimeStampedModel


class Cheese(TimeStampedModel):
    """
    Represents a cheese in the EveryCheese index.

    Stores descriptive metadata, geographic origin, and texture firmness.
    Ratings are stored separately in the Rating model and aggregated at
    the database level for optimal query performance.
    """

    name = models.CharField("Name of Cheese", max_length=255)
    slug = AutoSlugField(
        "Cheese Address",
        unique=True,
        always_update=False,
        populate_from="name",
    )
    description = models.TextField("Description", blank=True)
    country_of_origin = CountryField("Country of Origin", blank=True)

    class Firmness(models.TextChoices):
        UNSPECIFIED = "unspecified", "Unspecified"
        SOFT = "soft", "Soft"
        SEMI_SOFT = "semi-soft", "Semi-Soft"
        SEMI_HARD = "semi-hard", "Semi-Hard"
        HARD = "hard", "Hard"

    firmness = models.CharField(
        "Firmness",
        max_length=20,
        choices=Firmness.choices,
        default=Firmness.UNSPECIFIED,
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cheeses",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Cheese"
        verbose_name_plural = "Cheeses"

    @property
    def average_rating(self) -> float:
        """
        Return the average rating for this cheese, aggregated at the DB level.

        Returns 0.0 when no ratings exist yet.
        """
        result = self.ratings.aggregate(avg=Avg("score"))
        return round(result["avg"] or 0.0, 1)

    def __str__(self) -> str:
        return self.name

    def get_absolute_url(self) -> str:
        """Return absolute URL to the Cheese Detail page."""
        return reverse("cheeses:detail", kwargs={"slug": self.slug})


class Rating(models.Model):
    """
    Stores a single user's rating for a specific cheese.

    One rating per (user, cheese) pair is enforced via unique_together.
    """

    score = models.PositiveSmallIntegerField(
        "Score",
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="ratings",
    )
    cheese = models.ForeignKey(
        Cheese,
        null=True,
        on_delete=models.SET_NULL,
        related_name="ratings",
    )

    class Meta:
        unique_together = [("creator", "cheese")]
        verbose_name = "Rating"
        verbose_name_plural = "Ratings"

    def __str__(self) -> str:
        return f"{self.cheese} — {self.score}/5 by {self.creator}"
