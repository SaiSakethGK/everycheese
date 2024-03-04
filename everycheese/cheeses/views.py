from typing import Any
from django.views.generic import ListView, DetailView, DeleteView, TemplateView
from .models import Cheese
from django.urls import reverse_lazy
import logging
from django.views.generic import CreateView


log = logging.getLogger(__name__)


class CheeseListView(ListView):
    model = Cheese
    
    def get_context_data(self, **kwargs: Any):
        log.info("Hello World")
        context = super().get_context_data(**kwargs)
        context['my_new_ch_list']=Cheese.objects.all()
        
        return context


class CheeseDetailView(DetailView):
    model = Cheese


class CheeseCreateView(CreateView):
    model = Cheese
    fields = [
        'name',
        'description',
        'firmness',
        'country_of_origin',
    ]


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
 
