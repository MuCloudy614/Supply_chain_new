from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Product, Purchase, SalesOrder, InventoryLog


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'current_stock', 'stock_status')
    list_filter = ('category',)
    search_fields = ('name', 'code')
    ordering = ('-current_stock',)
    change_list_template = 'admin/inventory/product_changelist.html'  # 重要！

    def stock_status(self, obj):
        return mark_safe(obj.stock_status)

    stock_status.short_description = '库存状态'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        products = Product.objects.all()

        # 统计信息
        extra_context['total_stock'] = sum(p.current_stock for p in products)
        extra_context['alert_count'] = sum(1 for p in products if p.current_stock < p.alert_threshold)
        extra_context['recent_transactions'] = InventoryLog.objects.order_by('-created_at')[:5]

        return super().changelist_view(request, extra_context)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.has_perm('inventory.manage_product'):
            # 普通用户只能看到非预警产品
            return qs.filter(current_stock__gt=0)
        return qs


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier', 'product', 'quantity', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'product', 'quantity', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product', 'transaction_type', 'quantity', 'reference', 'created_at')
    list_filter = ('transaction_type',)
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

    def has_add_permission(self, request):
        return False  # 禁止手动添加

    def has_change_permission(self, request, obj=None):
        return False  # 禁止修改