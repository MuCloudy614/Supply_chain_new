# E:\pycharm_pro_project\supply_chain\inventory\admin.py

from django.contrib import admin
from django.utils.safestring import mark_safe
from django.db.models import F, Q, Count, Sum
from django.utils.html import format_html
from django.urls import reverse
from .models import Product, Purchase, SalesOrder, InventoryLog, Supplier, Customer


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'phone', 'rating', 'total_orders', 'created_at')
    search_fields = ('name', 'contact', 'phone')
    list_filter = ('rating', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20

    def total_orders(self, obj):
        return obj.purchase_set.count()

    total_orders.short_description = '采购订单数'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            total_orders=Count('purchase')
        )


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact', 'customer_type', 'total_orders', 'total_spending', 'created_at')
    search_fields = ('name', 'contact', 'phone')
    list_filter = ('customer_type', 'created_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20

    def total_orders(self, obj):
        return obj.salesorder_set.count()

    total_orders.short_description = '销售订单数'

    def total_spending(self, obj):
        return f"¥{obj.salesorder_set.aggregate(spent=Sum('total_amount'))['spent'] or 0:.2f}"

    total_spending.short_description = '总消费金额'

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            total_orders=Count('salesorder'),
            total_spending=Sum('salesorder__total_amount')
        )


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'current_stock', 'alert_threshold',
                    'stock_status', 'unit_price', 'location', 'stock_value')
    list_filter = ('category',)
    search_fields = ('name', 'code')
    ordering = ('-current_stock',)
    change_list_template = 'admin/inventory/product_changelist.html'
    list_per_page = 20
    fieldsets = (
        ('基本信息', {
            'fields': ('code', 'name', 'category', 'unit')
        }),
        ('库存信息', {
            'fields': ('current_stock', 'alert_threshold', 'unit_price', 'location')
        }),
        ('其他信息', {
            'fields': ('notes',),
            'classes': ('collapse',)
        })
    )

    def stock_status(self, obj):
        if obj.current_stock == 0:
            return mark_safe('<span style="color:red;font-weight:bold;">缺货</span>')
        elif obj.current_stock < obj.alert_threshold:
            return mark_safe('<span style="color:orange;font-weight:bold;">预警</span>')
        else:
            return mark_safe('<span style="color:green;font-weight:bold;">正常</span>')

    stock_status.short_description = '库存状态'

    def stock_value(self, obj):
        return f"¥{(obj.current_stock * obj.unit_price):.2f}"

    stock_value.short_description = '库存价值'

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        products = Product.objects.all()

        # 计算库存总量和库存预警数量
        extra_context['total_stock'] = products.aggregate(total=Sum('current_stock'))['total']
        extra_context['alert_count'] = products.filter(current_stock__lt=F('alert_threshold')).count()

        # 获取最近的库存变动记录
        extra_context['recent_transactions'] = InventoryLog.objects.select_related('product') \
                                                   .order_by('-created_at')[:10]

        # 库存警告等级
        critical_count = products.filter(current_stock=0).count()
        warning_count = products.filter(current_stock__lt=F('alert_threshold'), current_stock__gt=0).count()
        extra_context['critical_count'] = critical_count
        extra_context['warning_count'] = warning_count

        # 库存价值排名
        extra_context['top_value'] = products.order_by('-current_stock', '-unit_price')[:5]

        return super().changelist_view(request, extra_context)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'supplier_link', 'product_link', 'quantity', 'unit_price',
                    'total_amount', 'status_display', 'created_at', 'approve_action')
    list_filter = ('status', 'created_at', 'supplier')
    search_fields = ('order_number', 'supplier__name', 'product__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20
    actions = ['approve_selected', 'reject_selected']
    readonly_fields = ('total_amount',)

    fields = ('supplier', 'product', 'quantity', 'unit_price', 'total_amount', 'status', 'notes')

    def supplier_link(self, obj):
        url = reverse('admin:inventory_supplier_change', args=[obj.supplier.id])
        return format_html('<a href="{}">{}</a>', url, obj.supplier.name)

    supplier_link.short_description = '供应商'

    def product_link(self, obj):
        url = reverse('admin:inventory_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    product_link.short_description = '产品'

    def status_display(self, obj):
        status_map = {
            'pending': ('待审批', 'orange'),
            'approved': ('已批准', 'green'),
            'rejected': ('已拒绝', 'red'),
            'canceled': ('已取消', 'gray')
        }
        name, color = status_map.get(obj.status, ('未知', 'black'))
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, name)

    status_display.short_description = '状态'

    def approve_action(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:approve_purchase', args=[obj.id])
            reject_url = reverse('admin:reject_purchase', args=[obj.id])
            return format_html(
                '<a href="{}" class="button" style="background:green;color:white;padding:2px 5px;">批准</a>'
                ' <a href="{}" class="button" style="background:red;color:white;padding:2px 5px;">拒绝</a>',
                approve_url, reject_url
            )
        return "-"

    approve_action.short_description = '操作'

    def approve_selected(self, request, queryset):
        updated = 0
        for purchase in queryset.filter(status='pending'):
            if purchase.approve(request.user):
                updated += 1
        self.message_user(request, f"成功批准 {updated} 个采购订单")

    approve_selected.short_description = "批准选中的采购订单"

    def reject_selected(self, request, queryset):
        updated = 0
        for purchase in queryset.filter(status='pending'):
            if purchase.reject(request.user, "批量拒绝"):
                updated += 1
        self.message_user(request, f"成功拒绝 {updated} 个采购订单")

    reject_selected.short_description = "拒绝选中的采购订单"

    # 自定义审批和拒绝视图
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:pk>/', self.approve_purchase, name='approve_purchase'),
            path('reject/<int:pk>/', self.reject_purchase, name='reject_purchase'),
        ]
        return custom_urls + urls

    def approve_purchase(self, request, pk):
        purchase = Purchase.objects.get(pk=pk)
        if purchase.approve(request.user):
            self.message_user(request, f"采购订单 {purchase.order_number} 已成功批准")
        else:
            self.message_user(request, "无法批准该订单", level='error')
        return self.response_post_save_change(request, purchase)

    def reject_purchase(self, request, pk):
        purchase = Purchase.objects.get(pk=pk)
        if purchase.reject(request.user, "管理员手动拒绝"):
            self.message_user(request, f"采购订单 {purchase.order_number} 已拒绝")
        else:
            self.message_user(request, "无法拒绝该订单", level='error')
        return self.response_post_save_change(request, purchase)


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_link', 'product_link', 'quantity', 'discount',
                    'total_amount', 'status_display', 'created_at', 'approve_action')
    list_filter = ('status', 'created_at', 'customer')
    search_fields = ('order_number', 'customer__name', 'product__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20
    actions = ['approve_selected', 'reject_selected']
    readonly_fields = ('total_amount',)

    fields = ('customer', 'product', 'quantity', 'unit_price', 'discount',
              'total_amount', 'shipping_address', 'status', 'notes')

    def customer_link(self, obj):
        url = reverse('admin:inventory_customer_change', args=[obj.customer.id])
        return format_html('<a href="{}">{}</a>', url, obj.customer.name)

    customer_link.short_description = '客户'

    def product_link(self, obj):
        url = reverse('admin:inventory_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    product_link.short_description = '产品'

    def status_display(self, obj):
        status_map = {
            'pending': ('待审批', 'orange'),
            'approved': ('已批准', 'green'),
            'rejected': ('已拒绝', 'red'),
            'canceled': ('已取消', 'gray')
        }
        name, color = status_map.get(obj.status, ('未知', 'black'))
        return format_html('<span style="color:{};font-weight:bold;">{}</span>', color, name)

    status_display.short_description = '状态'

    def approve_action(self, obj):
        if obj.status == 'pending':
            approve_url = reverse('admin:approve_sales', args=[obj.id])
            reject_url = reverse('admin:reject_sales', args=[obj.id])
            return format_html(
                '<a href="{}" class="button" style="background:green;color:white;padding:2px 5px;">批准</a>'
                ' <a href="{}" class="button" style="background:red;color:white;padding:2px 5px;">拒绝</a>',
                approve_url, reject_url
            )
        return "-"

    approve_action.short_description = '操作'

    def approve_selected(self, request, queryset):
        updated = 0
        for so in queryset.filter(status='pending'):
            if so.approve(request.user):
                updated += 1
        self.message_user(request, f"成功批准 {updated} 个销售订单")

    approve_selected.short_description = "批准选中的销售订单"

    def reject_selected(self, request, queryset):
        updated = 0
        for so in queryset.filter(status='pending'):
            if so.reject(request.user, "批量拒绝"):
                updated += 1
        self.message_user(request, f"成功拒绝 {updated} 个销售订单")

    reject_selected.short_description = "拒绝选中的销售订单"

    # 自定义审批和拒绝视图
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:pk>/', self.approve_sales, name='approve_sales'),
            path('reject/<int:pk>/', self.reject_sales, name='reject_sales'),
        ]
        return custom_urls + urls

    def approve_sales(self, request, pk):
        order = SalesOrder.objects.get(pk=pk)
        if order.approve(request.user):
            self.message_user(request, f"销售订单 {order.order_number} 已成功批准")
        else:
            self.message_user(request, "库存不足或订单无法批准", level='error')
        return self.response_post_save_change(request, order)

    def reject_sales(self, request, pk):
        order = SalesOrder.objects.get(pk=pk)
        if order.reject(request.user, "管理员手动拒绝"):
            self.message_user(request, f"销售订单 {order.order_number} 已拒绝")
        else:
            self.message_user(request, "无法拒绝该订单", level='error')
        return self.response_post_save_change(request, order)


@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ('product_link', 'transaction_type_display', 'quantity_with_sign',
                    'reference_link', 'operator', 'created_at')
    list_filter = ('transaction_type', 'created_at')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    search_fields = ('product__name', 'reference')
    list_per_page = 20
    readonly_fields = ('transaction_type', 'product', 'quantity', 'reference', 'operator', 'created_at', 'notes')

    def product_link(self, obj):
        url = reverse('admin:inventory_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    product_link.short_description = '产品'

    def transaction_type_display(self, obj):
        colors = {
            'IN': 'green',
            'OUT': 'red',
            'ADJ': 'orange',
            'TRF': 'blue'
        }
        return format_html(
            '<span style="color:{};font-weight:bold;">{}</span>',
            colors.get(obj.transaction_type, 'black'),
            obj.get_transaction_type_display()
        )

    transaction_type_display.short_description = '交易类型'

    def quantity_with_sign(self, obj):
        sign = '+' if obj.quantity > 0 else ''
        color = 'green' if obj.quantity > 0 else 'red'
        return format_html('<span style="color:{};font-weight:bold;">{}{}</span>', color, sign, obj.quantity)

    quantity_with_sign.short_description = '数量'

    def reference_link(self, obj):
        if isinstance(obj.reference, Purchase):
            url = reverse('admin:inventory_purchase_change', args=[obj.reference.id])
            return format_html('<a href="{}">采购单 #{}</a>', url, obj.reference.order_number)
        elif isinstance(obj.reference, SalesOrder):
            url = reverse('admin:inventory_salesorder_change', args=[obj.reference.id])
            return format_html('<a href="{}">销售单 #{}</a>', url, obj.reference.order_number)
        return obj.reference or "-"

    reference_link.short_description = '参考单据'

    # 禁止添加和修改库存日志
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False