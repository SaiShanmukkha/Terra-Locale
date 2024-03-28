from django.shortcuts import render
from cart.models import Product,Category
from django.db.models import Q
from django.views import generic
from typing import Any, Dict, Union, List


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
        cs=Category.objects.all()
        
        main_category=self.request.GET.get('mainCategory',None)
        search = self.request.GET.get('search', None)
        print("sarch keword",search)

        
        print("vaues",qs.filter(Q(slug__icontains=search)))
        if not main_category:
            if not search:
                return qs
            return qs.filter(
                Q(title__icontains=search) |Q(secondary_categories__name__icontains=search)|
                Q(primary_category__name__icontains=search)|Q(primary_category__in = cs.filter(Q(main_category__name__icontains=search)))#|
               # Q( "multi_match",query=search,fields=['title', ], fuzziness='auto',))
               ).distinct()
        return qs.filter(primary_category__in = cs.filter(Q(main_category__name=main_category)))
        
        

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super(ProductSearchListView, self).get_context_data(**kwargs)
        context.update({"categories": Category.objects.values("name")})
        context.update({"mainCategory":MainCategory.objects.all().order_by('name')})
        return context

__all__ = (
    'ProductSearchListView',)

