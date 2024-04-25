import datetime
import json
from logging import getLogger
from typing import Any, Dict, Union, List
from django.http import HttpResponseRedirect

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import (JsonResponse, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect)
from django.shortcuts import (get_object_or_404, reverse, redirect)
from django.utils import timezone
from django.views import generic
from django.views.decorators.csrf import csrf_exempt

from .forms import (
    AddToCartForm,
    AddressForm,
    StripePaymentForm,
    ProfileSearchForm,
)
from .models import (
    Product,
    OrderItem,
    Address,
    Payment,
    Order,
    Category,
    MainCategory,
    StripePayment,
)
from .utils import get_or_set_order_session

logger = getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


class ProductListView(generic.ListView):
    template_name: str = 'cart/product_list.html'

    def get_queryset(self):
        qs = Product.objects.all()
        cs=Category.objects.all()
        
        main_category=self.request.GET.get('mainCategory',None)
        # category = self.request.GET.get('category', None)

        print("vaues",cs.filter(Q(main_category__name=main_category)))
        if not main_category:
            # if not category:
            return qs
        return qs.filter(
            Q(primary_category__name=main_category)
        ).distinct()
        return qs.filter(primary_category__in = cs.filter(Q(main_category__name=main_category)))
        
        

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super(ProductListView, self).get_context_data(**kwargs)
        # context.update({"categories": Category.objects.values("name")})
        context.update({"mainCategory":MainCategory.objects.all().order_by('name')})
        return context

class ProductSearchListView(generic.ListView):
    template_name: str = 'cart/product_list.html'

    def get_queryset(self):
        qs = Product.objects.all()
        cs=Category.objects.all()
        main_category=self.request.GET.get('mainCategory',None)
        search1 = self.request.GET.get('search', None)
        print("sarch keword",search1)
        print("sarch keword",search1)
        print("vaues",qs.filter(Q(slug__icontains=search1)))
        if not main_category:
            if not search1:
                return qs
            return qs.filter(
                Q(title__icontains=search1) |
                Q(primary_category__name__icontains=search1)|Q(primary_category__in = cs.filter(Q(main_category__name__icontains=search1)))#|
               # Q( "multi_match",query=search,fields=['title', ], fuzziness='auto',))
               ).distinct()
        return qs.filter(primary_category__in = cs.filter(Q(main_category__name=main_category)))
        
        

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super(ProductSearchListView, self).get_context_data(**kwargs)
        # context.update({"categories": Category.objects.values("name")})
        context.update({"mainCategory":MainCategory.objects.all().order_by('-id')})
        return context


class ProductDetailView(generic.FormView):
    template_name: str = 'cart/product_detail.html'
    form_class = AddToCartForm

    def get_object(self):
        return get_object_or_404(Product, slug=self.kwargs["slug"])

    def get_success_url(self) -> str:
        return reverse("cart:summary")

    def get_form_kwargs(self):
        kwargs = super(ProductDetailView, self).get_form_kwargs()
        kwargs["product_id"] = self.get_object().id
        return kwargs

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        product = self.get_object()

        item_filter = order.items.filter(
            product=product,
            # colour=form.cleaned_data['colour'],
            # size=form.cleaned_data['size'],
        )
        if not item_filter.exists():
            new_item = form.save(commit=False)
            new_item.product = product
            new_item.order = order
            new_item.save()
        else:
            item = item_filter.first()
            item.quantity += int(form.cleaned_data['quantity'])
            item.save()

        return super(ProductDetailView, self).form_valid(form)

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super(ProductDetailView, self).get_context_data(**kwargs)
        context['product'] = self.get_object()
        return context


class CartView(generic.TemplateView):
    template_name: str = "cart/cart.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super(CartView, self).get_context_data(**kwargs)
        context["order"] = get_or_set_order_session(self.request)
        return context


class IncreaseQuantityView(generic.View):
    @staticmethod
    def get(request, *args, **kwargs) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect]:
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.quantity += 1
        order_item.save(update_fields=['quantity', ])
        return redirect("cart:summary")


class DecreaseQuantityView(generic.View):
    @staticmethod
    def get(request, *args, **kwargs) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect]:
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        if order_item.quantity <= 1:
            order_item.delete()
        else:
            order_item.quantity -= 1
            order_item.save(update_fields=['quantity', ])
        return redirect("cart:summary")


class RemoveFromCartView(generic.View):
    @staticmethod
    def get(request, *args, **kwargs) -> Union[HttpResponsePermanentRedirect, HttpResponseRedirect]:
        order_item = get_object_or_404(OrderItem, id=kwargs['pk'])
        order_item.delete()
        return redirect("cart:summary")


class CheckoutView(generic.FormView):
    template_name: str = 'cart/checkout.html'
    form_class = AddressForm
   
    # Do something for authenticated users.
    def get_success_url(self) -> str:
        return reverse("cart:payment")

    def form_valid(self, form):
        order = get_or_set_order_session(self.request)
        selected_shipping_address = form.cleaned_data.get(
            'selected_shipping_address'
        )
        selected_billing_address = form.cleaned_data.get(
            'selected_billing_address'
        )
        if self.request.user.is_authenticated:
            if selected_shipping_address:
                order.shipping_address = selected_shipping_address
            else:
                address = Address.objects.create(
                    address_type=Address.SHIPPING_ADDRESS_TYPE,
                    user=self.request.user,
                    address_line_1=form.cleaned_data['shipping_address_line_1'],
                    address_line_2=form.cleaned_data['shipping_address_line_2'],
                    zip_code=form.cleaned_data['shipping_zip_code'],
                    city=form.cleaned_data['shipping_city'],
                )
                order.shipping_address = address

            if selected_billing_address:
                order.billing_address = selected_billing_address
            else:
                address = Address.objects.create(
                    address_type=Address.BILLING_ADDRESS_TYPE,
                    user=self.request.user,
                    address_line_1=form.cleaned_data['billing_address_line_1'],
                    address_line_2=form.cleaned_data['billing_address_line_2'],
                    zip_code=form.cleaned_data['billing_zip_code'],
                    city=form.cleaned_data['billing_city'],
                )
                order.billing_address = address

            order.save()
            messages.info(self.request, "You have successfully added your addresses")
            return super(CheckoutView, self).form_valid(form)
        else:
            return super(CheckoutView, self)

    def get_form_kwargs(self) -> Dict[str, Any]:
        if self.request.user.is_authenticated:
            kwargs = super(CheckoutView, self).get_form_kwargs()
            kwargs["user_id"] = self.request.user.id
            return kwargs

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        if self.request.user.is_authenticated:
            context = super(CheckoutView, self).get_context_data(**kwargs)
            context["order"] = get_or_set_order_session(self.request)
            return context


class PaymentView(generic.TemplateView):
    template_name: str = 'cart/payment.html'

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super(PaymentView, self).get_context_data(**kwargs)
        context["STRIPE_PUBLIC_KEY"] = settings.STRIPE_PUBLIC_KEY
        context['order'] = get_or_set_order_session(self.request)
        context['CALLBACK_URL'] = self.request.build_absolute_uri(
            location=reverse("cart:thank-you")
        )
        return context


class StripePaymentView(generic.FormView):
    template_name: str = 'cart/stripe_payment.html'
    form_class = StripePaymentForm

    def get_success_url(self) -> str:
        ConfirmOrderView()
        return reverse("cart:thank-you")

    def form_valid(self, form):
        payment_method = form.cleaned_data["selectedCard"]
        if payment_method != "newCard":
            try:
                order = get_or_set_order_session(self.request)
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(order.get_raw_total()),
                    currency='usd',
                    customer=self.request.user.customer.stripe_customer_id,
                    payment_method=payment_method,
                    off_session=True,
                    confirm=True,
                )
                print("stripe ")
                payment_record, _ = StripePayment.objects.get_or_create(
                    order=order,
                )
                payment_record.payment_intent_id = payment_intent["id"]
                payment_record.amount = order.get_total()
                payment_record.save(update_fields=['payment_intent_id', 'amount', ])
            except stripe.error.CardError as e:
                err = e.error
                # Error code will be authentication_required if authentication is needed
                logger.debug("Code is: %s" % err.code)
                stripe.PaymentIntent.retrieve(err.payment_intent['id'])
                messages.warning(self.request, "Code is: %s" % err.code)
            return super(StripePaymentView, self).form_valid(form)
        else:
            return super(StripePaymentView, self)
        

    def get_context_data(self, **kwargs):
        user = self.request.user
        if not user.customer.stripe_customer_id:
            stripe_customer = stripe.Customer.create(email=user.email)
            user.customer.stripe_customer_id = stripe_customer["id"]
            user.customer.save(update_fields=['stripe_customer_id'], )

        order = get_or_set_order_session(self.request)

        payment_intent = stripe.PaymentIntent.create(
            amount=int(order.get_raw_total()),
            currency='usd',
            customer=user.customer.stripe_customer_id,
        )

        payment_record, _ = StripePayment.objects.get_or_create(order=order, )
        payment_record.payment_intent_id = payment_intent["id"],
        payment_record.amount = order.get_total()
        payment_record.save(update_fields=['amount', 'payment_intent_id', ])

        cards = stripe.PaymentMethod.list(
            customer=user.customer.stripe_customer_id,
            type="card",
        )
        payment_methods: List[Dict[str, Any]] = [{
            "last4": card["card"]["last4"],
            "brand": card["card"]["brand"],
            "exp_month": card["card"]["exp_month"],
            "exp_year": card["card"]["exp_year"],
            "pm_id": card["id"]
        } for card in cards]
        context = super(StripePaymentView, self).get_context_data(**kwargs)
        context["STRIPE_PUBLIC_KEY"] = settings.STRIPE_PUBLIC_KEY
        context["client_secret"] = payment_intent["client_secret"]
        context["payment_methods"] = payment_methods
        return context


class ConfirmOrderView(generic.View):
    @staticmethod
    def post(request, *args, **kwargs) -> JsonResponse:
        order = get_or_set_order_session(request)
        body = json.loads(request.body)
        Payment.objects.create(
            order=order,
            successful=True,
            raw_response=json.dumps(body),
            amount=float(body["purchase_units"][0]["amount"]["value"]),
            payment_method=StripePayment,
        )
        order.ordered = True
        order.ordered_date = datetime.date.today()
        order.save(update_fields=['ordered', 'ordered_date', ])
        order = Order.objects.create()
        request.session['order_id'] = order.id
        return JsonResponse({"data": "Success"})


class ThankYouView(generic.TemplateView):
    template_name: str = 'cart/thanks.html'


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    template_name: str = 'order.html'
    queryset = Order.objects.all()
    context_object_name: str = 'order'


def rating(request):
    star=int(request.GET.get('rating'))
    user = request.user
    orderspk=request.GET.get('order_id')
    productId = int(request.GET.get('product_id')) # here
    product = Product.objects.get(id=productId)
    product.rating=(product.rating+star)/2
    product.save()

    return HttpResponseRedirect(reverse('cart:order-detail', args=[orderspk]))

@csrf_exempt
def stripe_webhook_view(request):
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        logger.debug(event)
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object  # contains a stripe.PaymentIntent
        stripe_payment = StripePayment.objects.get(
            payment_intent_id=payment_intent["id"],
        )
        stripe_payment.successful = True
        stripe_payment.save()
        order = stripe_payment.order
        order.ordered = True
        order.ordered_date = timezone.now()
        order.save()
    else:
        # Unexpected event type
        return HttpResponse(status=400)

    return HttpResponse(status=200)



__all__ = (
    'ProductListView',
    'ProductDetailView',
    'CartView',
    'IncreaseQuantityView',
    'DecreaseQuantityView',
    'RemoveFromCartView',
    'CheckoutView',
    'PaymentView',
    'StripePaymentView',
    'ConfirmOrderView',
    'ThankYouView',
    'OrderDetailView',
    'ProductSearchListView',
    'stripe_webhook_view',
)
