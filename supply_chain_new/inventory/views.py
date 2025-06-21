# E:\pycharm_pro_project\supply_chain_new\inventory\views.py

from django.views.generic import TemplateView, ListView, DetailView, UpdateView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views import View
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from .models import Product, Purchase, SalesOrder, Supplier, Customer, InventoryLog
from .forms import PurchaseApprovalForm, SalesApprovalForm, LowStockReportForm, TransactionReportForm
from .reports import generate_stock_report, generate_transaction_report
from django.utils import timezone
from datetime import timedelta
from django.db.models import F
from rest_framework import viewsets, permissions, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .serializers import ProductSerializer, PurchaseSerializer, SalesOrderSerializer


class DashboardView(LoginRequiredMixin, TemplateView):
    """库存仪表盘"""
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        products = Product.objects.all()
        context['total_stock'] = sum(p.current_stock for p in products)
        context['alert_count'] = products.filter(
            current_stock__lt=F('alert_threshold')
        ).count()
        context['total_value'] = sum(p.current_stock * p.unit_price for p in products)
        context['recent_logs'] = InventoryLog.objects.all().order_by('-created_at')[:10]
        context['pending_purchases'] = Purchase.objects.filter(status='pending').count()
        context['pending_sales'] = SalesOrder.objects.filter(status='pending').count()
        context['low_stock_products'] = products.filter(
            current_stock__lt=F('alert_threshold')
        ).order_by('current_stock')[:5]
        return context


class ProductListView(LoginRequiredMixin, ListView):
    """产品列表"""
    model = Product
    template_name = 'inventory/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category=category)
        low_stock = self.request.GET.get('low_stock')
        if low_stock == 'true':
            queryset = queryset.filter(current_stock__lt=F('alert_threshold'))
        return queryset.order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Product.CATEGORY_CHOICES
        context['low_stock'] = self.request.GET.get('low_stock') == 'true'
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    """产品详情"""
    model = Product
    template_name = 'inventory/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['logs'] = InventoryLog.objects.filter(
            product=self.object
        ).order_by('-created_at')[:20]
        return context


class SupplierListView(LoginRequiredMixin, ListView):
    """供应商列表"""
    model = Supplier
    template_name = 'inventory/supplier_list.html'  # 修复的模板路径
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_queryset(self):
        return Supplier.objects.all().order_by('name')


class SupplierDetailView(LoginRequiredMixin, DetailView):
    """供应商详情"""
    model = Supplier
    template_name = 'inventory/supplier_detail.html'  # 修复的模板路径
    context_object_name = 'supplier'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supplier = self.get_object()
        context['supplier_products'] = supplier.products.all()
        context['purchase_count'] = Purchase.objects.filter(supplier=supplier).count()

        # 计算总采购金额
        total_amount = 0
        for purchase in Purchase.objects.filter(supplier=supplier):
            total_amount += purchase.quantity * purchase.product.unit_price
        context['total_purchase_amount'] = total_amount

        # 模拟平均交货时间（实际应用应从采购单中计算）
        context['avg_delivery_time'] = 5.5
        return context


class CustomerListView(LoginRequiredMixin, ListView):
    """客户列表"""
    model = Customer
    template_name = 'inventory/customer_list.html'
    context_object_name = 'customers'
    paginate_by = 20

    def get_queryset(self):
        return Customer.objects.all().order_by('name')


class CustomerDetailView(LoginRequiredMixin, DetailView):
    """客户详情"""
    model = Customer
    template_name = 'inventory/customer_detail.html'
    context_object_name = 'customer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        customer = self.get_object()

        # 获取最近5个订单
        context['recent_orders'] = SalesOrder.objects.filter(
            customer=customer
        ).order_by('-created_at')[:5]

        # 计算总订单数和总金额
        orders = SalesOrder.objects.filter(customer=customer)
        context['order_count'] = orders.count()

        total_amount = 0
        for order in orders:
            total_amount += order.total_amount
        context['total_amount'] = total_amount

        # 计算平均订单金额
        context['avg_order_value'] = total_amount / context['order_count'] if context['order_count'] > 0 else 0

        return context


class PurchaseApprovalView(PermissionRequiredMixin, ListView):
    """待审批采购订单列表"""
    permission_required = 'inventory.approve_purchase'
    model = Purchase
    template_name = 'inventory/purchase_approval.html'
    context_object_name = 'purchases'
    paginate_by = 10

    def get_queryset(self):
        return Purchase.objects.filter(status='pending').order_by('created_at')


class PurchaseApproveView(PermissionRequiredMixin, UpdateView):
    """审批采购订单"""
    permission_required = 'inventory.approve_purchase'
    model = Purchase
    form_class = PurchaseApprovalForm
    template_name = 'inventory/approve_form.html'
    success_url = reverse_lazy('inventory:purchase_approval')

    def form_valid(self, form):
        action = form.cleaned_data['action']
        reason = form.cleaned_data.get('reason', '')

        if action == 'approve':
            if self.object.approve(self.request.user):
                messages.success(self.request, f"采购订单 {self.object.order_number} 已批准")
            else:
                messages.error(self.request, f"采购订单 {self.object.order_number} 审批失败")
        else:
            if self.object.reject(self.request.user, reason):
                messages.warning(self.request, f"采购订单 {self.object.order_number} 已拒绝")
            else:
                messages.error(self.request, f"采购订单 {self.object.order_number} 拒绝失败")

        return super().form_valid(form)


class SalesApprovalView(PermissionRequiredMixin, ListView):
    """待审批销售订单列表"""
    permission_required = 'inventory.approve_sales'
    model = SalesOrder
    template_name = 'inventory/sales_approval.html'
    context_object_name = 'orders'
    paginate_by = 10

    def get_queryset(self):
        return SalesOrder.objects.filter(status='pending').order_by('created_at')


class SalesApproveView(PermissionRequiredMixin, UpdateView):
    """审批销售订单"""
    permission_required = 'inventory.approve_sales'
    model = SalesOrder
    form_class = SalesApprovalForm
    template_name = 'inventory/approve_form.html'
    success_url = reverse_lazy('inventory:sales_approval')

    def form_valid(self, form):
        action = form.cleaned_data['action']
        reason = form.cleaned_data.get('reason', '')

        if action == 'approve':
            if self.object.approve(self.request.user):
                messages.success(self.request, f"销售订单 {self.object.order_number} 已批准")
            else:
                messages.error(self.request, f"销售订单 {self.object.order_number} 审批失败（库存不足）")
        else:
            if self.object.reject(self.request.user, reason):
                messages.warning(self.request, f"销售订单 {self.object.order_number} 已拒绝")
            else:
                messages.error(self.request, f"销售订单 {self.object.order_number} 拒绝失败")

        return super().form_valid(form)


class LowStockReportView(LoginRequiredMixin, FormView):
    """低库存报表生成"""
    template_name = 'inventory/low_stock_report.html'
    form_class = LowStockReportForm

    def form_valid(self, form):
        # 生成报表
        data = form.cleaned_data

        # 获取符合条件的低库存产品
        products = Product.objects.all()

        if data['include_critical']:
            products = products.filter(current_stock=0)
        elif data['include_warning']:
            products = products.filter(current_stock__gt=0, current_stock__lt=F('alert_threshold'))

        # 生成 PDF
        pdf_buffer = generate_stock_report(products, timezone.now().date())

        # 返回文件响应
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        filename = f"低库存报告_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class TransactionReportView(LoginRequiredMixin, FormView):
    """交易历史报表生成"""
    template_name = 'inventory/transaction_report.html'
    form_class = TransactionReportForm

    def form_valid(self, form):
        # 生成报表
        data = form.cleaned_data

        # 获取交易记录
        transactions = InventoryLog.objects.all()

        if data['start_date']:
            transactions = transactions.filter(created_at__date__gte=data['start_date'])

        if data['end_date']:
            transactions = transactions.filter(created_at__date__lte=data['end_date'])

        if data['transaction_type']:
            transactions = transactions.filter(transaction_type=data['transaction_type'])

        # 生成 PDF
        pdf_buffer = generate_transaction_report(transactions, timezone.now().date())

        # 返回文件响应
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        filename = f"交易报告_{timezone.now().strftime('%Y%m%d')}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class PDFReportView(LoginRequiredMixin, View):
    """生成PDF格式报告"""

    def get(self, request, report_type):
        if not request.user.has_perm('inventory.export_product'):
            raise PermissionDenied("您没有导出权限")

        if report_type == 'stock':
            # 获取所有产品
            products = Product.objects.all()
            # 生成报告
            pdf_buffer = generate_stock_report(products, timezone.now().date())
            filename = f"库存报告_{timezone.now().strftime('%Y%m%d')}.pdf"
            content_type = 'application/pdf'
        elif report_type == 'transaction':
            # 默认过去30天交易
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
            # 获取交易记录
            transactions = InventoryLog.objects.filter(
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            )
            # 生成报告
            pdf_buffer = generate_transaction_report(transactions, timezone.now().date())
            filename = f"交易报告_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.pdf"
            content_type = 'application/pdf'
        else:
            return HttpResponse("无效的报告类型", status=400)

        # 创建响应
        response = HttpResponse(pdf_buffer.getvalue(), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


# ===================================================
# REST API 视图集
# ===================================================

class ProductViewSet(viewsets.ModelViewSet):
    """
    API 端点，允许查看和编辑产品
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name', 'category']
    ordering_fields = ['current_stock', 'unit_price', 'alert_threshold']
    ordering = ['code']


class PurchaseViewSet(viewsets.ModelViewSet):
    """
    API 端点，允许查看和编辑采购订单
    """
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'supplier', 'product']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']


class SalesOrderViewSet(viewsets.ModelViewSet):
    """
    API 端点，允许查看和编辑销售订单
    """
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['status', 'customer', 'product']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']