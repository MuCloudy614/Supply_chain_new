# E:\pycharm_pro_project\supply_chain\inventory\api.py

from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import F
from .models import Product, InventoryLog, Purchase, SalesOrder
from .serializers import ProductSerializer, InventoryLogSerializer, PurchaseSerializer, SalesOrderSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['category', 'current_stock']

    def get_queryset(self):
        queryset = super().get_queryset()

        # 添加自定义过滤参数
        low_stock = self.request.query_params.get('low_stock')
        if low_stock and low_stock.lower() == 'true':
            queryset = queryset.filter(current_stock__lt=F('alert_threshold'))

        critical = self.request.query_params.get('critical')
        if critical and critical.lower() == 'true':
            queryset = queryset.filter(current_stock=0)

        return queryset

    @action(detail=True, methods=['get'])
    def logs(self, request, pk=None):
        """获取产品的库存日志"""
        product = self.get_object()
        logs = InventoryLog.objects.filter(product=product).order_by('-created_at')[:100]
        serializer = InventoryLogSerializer(logs, many=True)
        return Response(serializer.data)


class InventoryLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = InventoryLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['transaction_type', 'operator']

    def get_queryset(self):
        # 根据产品ID过滤日志
        product_id = self.kwargs.get('product_pk')
        if product_id:
            return InventoryLog.objects.filter(product_id=product_id)
        return InventoryLog.objects.all()


class PurchaseViewSet(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # 状态过滤
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # 供应商过滤
        supplier = self.request.query_params.get('supplier')
        if supplier:
            queryset = queryset.filter(supplier_id=supplier)

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批采购订单"""
        purchase = self.get_object()
        if purchase.approve(request.user):
            return Response({'status': 'approved'})
        return Response(
            {'error': '无法审批订单'},
            status=status.HTTP_400_BAD_REQUEST
        )


class SalesOrderViewSet(viewsets.ModelViewSet):
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        # 状态过滤
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # 客户过滤
        customer = self.request.query_params.get('customer')
        if customer:
            queryset = queryset.filter(customer_id=customer)

        return queryset

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """审批销售订单"""
        order = self.get_object()
        if order.approve(request.user):
            return Response({'status': 'approved'})
        return Response(
            {'error': '无法审批订单（库存不足）'},
            status=status.HTTP_400_BAD_REQUEST
        )