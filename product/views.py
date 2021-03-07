import json

from django.views     import View
from django.http      import JsonResponse
from django.db.models import Q, Min, Avg

from .models          import Product, Image, Size, ProductSize 
from order.models     import Ask, Bid, OrderStatus, ExpirationType

ORDER_STATUS_CURRENT   = 'current'
ORDER_STATUS_HISTORY   = 'history'

class ProductDetailView(View):
    def get(self, request, product_id):
        if not Product.objects.filter(id=product_id).exists():
            return JsonResponse({'message':'PAGE_NOT_FOUND'}, status=404)

        product       = Product.objects.get(id=product_id)
        product_sizes = product.productsize_set.all()
        sizes         = Size.objects.filter(productsize__product__id=product.id)

        results = {
                'product_name'   : product.name,
                'product_ticker' : product.ticker_number,
                'color'          : product.color,
                'description'    : product.description,
                'retail_price'   : product.retail_price,
                'release_date'   : product.release_date.strftime('%Y-%m-%d'),
                'style'          : product.model_number,
                'image_url'      : [product_image.image_url for product_image in product.image_set.all()]
                }
        results['sizes'] = [
                {
                    'size_id'                 : product_size.size_id,
                    'size_name'               : Size.objects.get(id=product_size.size_id).name,
                    'last_sale'               : int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).last().price) \
                                                if product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).exists() else 0,
                    'price_change'            : int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).order_by('-matched_at')[0].price) \
                                                - int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).order_by('-matched_at')[1].price) \
                                                if product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY) else 0,
                    
                    'price_change_percentage' : int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).order_by('-matched_at')[0].price) \
                                                - int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).order_by('-matched_at')[1].price) \
                                                if product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY) else 0,
                    'lowest_ask'              : int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_CURRENT).order_by('price').first().price) \
                                                if product_size.ask_set.filter(order_status__name=ORDER_STATUS_CURRENT) else 0,
                    'highest_bid'             : int(product_size.bid_set.filter(order_status__name=ORDER_STATUS_CURRENT).order_by('-price').first().price) \
                                                if product_size.bid_set.filter(order_status__name=ORDER_STATUS_CURRENT) else 0,
                    'total_sales'             : product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).count(),
                    'price_premium'           : int(100 * (int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).last().price) - int(product.retail_price)) \
                                                / int(product.retail_price)) if product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).last() else 0,
                    'average_sale_price'      : int(product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).aggregate(total=Avg('price'))['total']) \
                                                if product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY).exists() else 0,
                    'sales_history':   
                    [
                        {
                            'sale_price'     : int(ask.price),
                            'date_time'      : ask.matched_at.strftime('%Y-%m-%d')
                            }
                        for ask in product_size.ask_set.filter(order_status__name=ORDER_STATUS_HISTORY)]
                } for product_size in product_sizes]
        return JsonResponse({'results': results}, status=200)