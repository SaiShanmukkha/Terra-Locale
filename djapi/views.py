from django.http import JsonResponse
from cart.models import Product
from .serializers import ProductSerializer
from rest_framework.parsers import JSONParser
from .serializers import ProductSerializer
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def product_list(request):
    """
    List all products, or create a new product.
    """
    if request.method == 'GET':
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)
        return JsonResponse(serializer.data, safe=False)  # Use safe=False to allow non-dict objects

    elif request.method == 'POST':
        data = JSONParser().parse(request)
        serializer = ProductSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            # Return the serialized data of the newly created product
            return JsonResponse(serializer.data, status=201, safe=False)
        return JsonResponse(serializer.errors, status=400)
