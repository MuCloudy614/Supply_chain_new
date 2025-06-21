# E:\pycharm_pro_project\supply_chain\inventory\serializers.py

from rest_framework import serializers
from .models import Product, Purchase, SalesOrder


class ProductSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField(source='get_stock_status_display')

    class Meta:
        model = Product
        fields = '__all__'
        extra_kwargs = {
            'alert_threshold': {'min_value': 0},
            'unit_price': {'min_value': 0}
        }


class PurchaseSerializer(serializers.ModelSerializer):
    supplier_name = serializers.ReadOnlyField(source='supplier.name')
    product_name = serializers.ReadOnlyField(source='product.name')
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = Purchase
        fields = '__all__'
        read_only_fields = ['total_amount', 'approved_by', 'approved_at']
        extra_kwargs = {
            'quantity': {'min_value': 1}
        }


class SalesOrderSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source='customer.name')
    product_name = serializers.ReadOnlyField(source='product.name')
    status_display = serializers.ReadOnlyField(source='get_status_display')

    class Meta:
        model = SalesOrder
        fields = '__all__'
        read_only_fields = ['total_amount', 'approved_by', 'approved_at']
        extra_kwargs = {
            'quantity': {'min_value': 1},
            'discount': {'min_value': 0, 'max_value': 100}
        }