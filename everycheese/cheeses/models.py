from django.db import models
from model_utils.models import TimeStampedModel
from autoslug import AutoSlugField
from django_countries.fields import CountryField
from django.urls import reverse
from django.db import models
from model_utils.models import TimeStampedModel
from autoslug import AutoSlugField
from django_countries.fields import CountryField
from django.urls import reverse
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg




class Cheese(TimeStampedModel):
    name = models.CharField("Name of Cheese", max_length=255)
    slug = AutoSlugField("Cheese Address", unique=True, always_update=False, populate_from="name")
    description = models.TextField("Description", blank=True)
    country_of_origin = CountryField("Country of Origin", blank=True)

    class Firmness(models.TextChoices):
        UNSPECIFIED = "unspecified", "Unspecified"
        SOFT = "soft", "Soft"
        SEMI_SOFT = "semi-soft", "Semi-Soft"
        SEMI_HARD = "semi-hard", "Semi-Hard"
        HARD = "hard", "Hard"

    firmness = models.CharField("Firmness", max_length=20,choices=Firmness.choices, default=Firmness.UNSPECIFIED)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL,null=True,on_delete=models.SET_NULL)

    
    @property
    def average_rating(self):
        # Best to calculate in the query.
        # This is easier until we know more:
        ratings = Rating.objects.all().filter(cheese=self)
        
        if not ratings:
            return 0
        
        total = 0
        count = 0

        for r in ratings:
            total += r.i_rating
            count += 1

        if count <= 0:
            return 9
        
        return total // count


    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Return absolute URL to the Cheese Detail page."""
        return reverse('cheeses:detail', kwargs={"slug": self.slug})
    

class Rating(models.Model):

    i_rating = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    cheese = models.ForeignKey(Cheese, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.i_rating}"


