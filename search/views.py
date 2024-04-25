from django.shortcuts import render
# from products.models import Product
from cart.models import Product,Category
from django.db.models import Q
from django.views import generic
from typing import Any, Dict, Union, List

# from elasticsearch_dsl import analyzer, tokenizer

# autocomplete_analyzer = analyzer('autocomplete_analyzer',
#             tokenizer=tokenizer('trigram', 'nGram', min_gram=1, max_gram=20),
#             filter=['lowercase']
#         )

def do_search(request):
    category= Category.objects.all()
    products = Product.objects.filter(title__icontains=request.GET['q'])
    return render(request, "cart/product_list.html", {"products": products})
# Create your views here.
from cart.models import (
    Product,
    OrderItem,
    Address,
    Payment,
    Order,
    Category,
    MainCategory,
    StripePayment,
)

class ProductSearchListView(generic.ListView):
    template_name: str = 'cart/product_list.html'

    def get_queryset(self):
        qs = Product.objects.all()
        search = self.request.GET.get('search', None)
        main_category = self.request.GET.get('mainCategory', None)

        if main_category:
            # Filter categories based on MainCategory and use those categories to filter products
            categories = Category.objects.filter(main_category__name__icontains=main_category)
            qs = qs.filter(primary_category__in=categories)
        elif search:
            # Filter products by title or by primary categories that match the search string
            qs = qs.filter(
                Q(title__icontains=search) |
                Q(primary_category__name__icontains=search)
            ).distinct()

        return qs

        

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super(ProductSearchListView, self).get_context_data(**kwargs)
        context.update({"categories": Category.objects.values("name")})
        context.update({"mainCategory":MainCategory.objects.all().order_by('name')})
        return context

__all__ = (
    'ProductSearchListView',)

