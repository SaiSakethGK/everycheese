from typing import Any
from django.views.generic import ListView, DetailView, DeleteView, TemplateView, UpdateView
from .models import Cheese
from django.urls import reverse_lazy
import logging
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import Cheese, Rating
from django.views.generic import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
import logging  # Import the logging module

log = logging.getLogger(__name__)

class CheeseListView(ListView):
    model = Cheese

class CheeseDetailView(DetailView):
    model = Cheese

class CheeseCreateView(LoginRequiredMixin, CreateView):
    model = Cheese
    fields = ['name', 'description', 'firmness',
                'country_of_origin']
    def form_valid(self, form):
        form.instance.creator = self.request.user
        return super().form_valid(form)

class CheeseDeleteView(DeleteView):
    model = Cheese
    template_name ='cheeses/cheese_delete.html'
    success_url = reverse_lazy('cheeses:list')

class ConfirmCheeseDeleteView(TemplateView):
    template_name = 'cheeses/cheese_delete.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cheese'] = Cheese.objects.get(slug=self.kwargs['slug'])
        return context
    
class CheeseUpdateView(LoginRequiredMixin, UpdateView):
    model = Cheese
    fields = [
    'name',
    'description',
    'firmness',
    'country_of_origin'
    ]
    
    action = "Update"

    def get_context_data(self, **kwargs):
        ctx = super(CheeseUpdateView, self).get_context_data(**kwargs)
        _slug = self.kwargs.get("slug")
        ch = Cheese.objects.all().filter(slug = _slug).first()

        if ch ==None:
            ctx["rating"] =0
            return
        r = Rating.objects.all().filter(creator = self.request.user, cheese = ch).first()

        if r != None:
            ctx["rating"] = r.i_rating
        else:
            ctx["rating"] = 0
        return ctx
    def form_valid(self, form):
        # Get the cheese being updated
        cheese = self.object

        # Get or create the rating for the current user and cheese
        rating, created = Rating.objects.get_or_create(creator=self.request.user, cheese=cheese)

        # Update the rating value based on the form data
        rating.i_rating = int(self.request.POST.get('rating'))  # Safely retrieve the rating value
        rating.save()

        return super().form_valid(form)