# E:\pycharm_pro_project\supply_chain\inventory\models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from .managers import ProductManager, InventoryLogManager, PurchaseManager, SalesOrderManager


class Supplier(models.Model):
    name = models.CharField('供应商名称', max_length=100, unique=True)
    contact = models.CharField('联系人', max_length=50)
    phone = models.CharField('电话', max_length=20)
    email = models.EmailField('邮箱', blank=True)
    address = models.TextField('地址', blank=True)
    rating = models.PositiveIntegerField('评级', default=3,
                                         help_text='1-5分，5分为最佳')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.name


class Customer(models.Model):
    name = models.CharField('客户名称', max_length=100, unique=True)
    contact = models.CharField('联系人', max_length=50)
    phone = models.CharField('电话', max_length=20)
    email = models.EmailField('邮箱', blank=True)
    address = models.TextField('地址', blank=True)
    customer_type = models.CharField('客户类型', max_length=20,
                                     choices=[('RETAIL', '零售'), ('WHOLESALE', '批发'), ('VIP', 'VIP客户')],
                                     default='RETAIL')
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('RM', '原材料'),
        ('FP', '成品'),
        ('SF', '办公用品'),
    ]

    UNIT_CHOICES = [
        ('PCS', '件'),
        ('KG', '千克'),
        ('M', '米'),
        ('BOX', '箱'),
    ]

    name = models.CharField('产品名称', max_length=100)
    code = models.CharField('产品编号', max_length=20, unique=True)
    category = models.CharField('分类', max_length=2, choices=CATEGORY_CHOICES)
    unit = models.CharField('单位', max_length=5, choices=UNIT_CHOICES, default='PCS')
    unit_price = models.DecimalField('单价', max_digits=10, decimal_places=2, default=0.0)
    current_stock = models.PositiveIntegerField('当前库存', default=0)
    alert_threshold = models.PositiveIntegerField('库存预警值', default=10)
    location = models.CharField('库位', max_length=20, blank=True, help_text='仓储位置')
    notes = models.TextField('备注', blank=True)

    objects = ProductManager()

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def stock_status(self):
        if self.current_stock == 0:
            return '<span style="color:red;">缺货</span>'
        elif self.current_stock < self.alert_threshold:
            return '<span style="color:orange;">预警</span>'
        return '<span style="color:green;">正常</span>'

    @property
    def stock_status_display(self):
        if self.current_stock == 0:
            return '缺货'
        elif self.current_stock < self.alert_threshold:
            return '预警'
        return '正常'

    @property
    def stock_status_class(self):
        if self.current_stock == 0:
            return 'table-danger'
        elif self.current_stock < self.alert_threshold:
            return 'table-warning'
        return ''

    def stock_value(self):
        return self.current_stock * self.unit_price

    class Meta:
        permissions = [
            ("export_product", "导出产品数据"),
            ("manage_product", "管理产品库存"),
        ]
        ordering = ['code']


class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('canceled', '已取消'),
    ]

    order_number = models.CharField('采购单号', max_length=50, unique=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL,
                                 null=True, verbose_name='供应商')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='产品')

    # 所有数值字段添加默认值
    quantity = models.PositiveIntegerField('数量', default=0)
    unit_price = models.DecimalField('采购单价', max_digits=10, decimal_places=2, default=0.0)
    total_amount = models.DecimalField('总金额', max_digits=12, decimal_places=2, blank=True, default=0.0)
    expected_date = models.DateField('预计到货日期', default=timezone.now)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    operator = models.CharField('操作员', max_length=50)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.CharField('审批人', max_length=50, blank=True, null=True)
    approved_at = models.DateTimeField('审批时间', blank=True, null=True)
    rejection_reason = models.TextField('拒绝原因', blank=True)
    objects = PurchaseManager()

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("采购数量必须大于0")

        if self.pk and self.status == 'approved':
            original = Purchase.objects.get(pk=self.pk)
            if original.status == 'approved' and self.status != 'approved':
                raise ValidationError("已审批订单不可修改状态")

    def save(self, *args, **kwargs):
        self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def approve(self, user):
        if self.status == 'pending':
            self.status = 'approved'
            self.approved_by = user.username
            self.approved_at = timezone.now()
            self.rejection_reason = ''
            self.save()
            return True
        return False

    def reject(self, user, reason=""):
        if self.status == 'pending':
            self.status = 'rejected'
            self.approved_by = user.username
            self.approved_at = timezone.now()
            self.rejection_reason = reason
            self.save()
            return True
        return False

    def cancel(self, user, reason=""):
        if self.status in ['pending', 'approved']:
            self.status = 'canceled'
            self.approved_by = user.username
            self.approved_at = timezone.now()
            self.rejection_reason = reason
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.order_number} - {self.product.name}"


class SalesOrder(models.Model):
    STATUS_CHOICES = [
        ('pending', '待审批'),
        ('approved', '已批准'),
        ('rejected', '已拒绝'),
        ('shipped', '已发货'),
        ('canceled', '已取消'),
    ]

    order_number = models.CharField('订单号', max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL,
                                 null=True, verbose_name='客户')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='产品')

    # 所有数值字段添加默认值
    quantity = models.PositiveIntegerField('数量', default=0)
    unit_price = models.DecimalField('销售单价', max_digits=10, decimal_places=2, default=0.0)
    discount = models.DecimalField('折扣率', max_digits=4, decimal_places=2, default=0.0)
    total_amount = models.DecimalField('总金额', max_digits=12, decimal_places=2, blank=True, default=0.0)

    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    operator = models.CharField('操作员', max_length=50)
    status = models.CharField('状态', max_length=10, choices=STATUS_CHOICES, default='pending')
    approved_by = models.CharField('审批人', max_length=50, blank=True, null=True)
    approved_at = models.DateTimeField('审批时间', blank=True, null=True)
    rejection_reason = models.TextField('拒绝原因', blank=True)
    shipping_address = models.TextField('配送地址', blank=True)
    expected_date = models.DateField('要求交付日期', null=True, blank=True, default=timezone.now)

    objects = SalesOrderManager()

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("销售数量必须大于0")

        if self.pk and self.status == 'approved':
            original = SalesOrder.objects.get(pk=self.pk)
            if original.status == 'approved' and self.status != 'approved':
                raise ValidationError("已审批订单不可修改状态")

    def save(self, *args, **kwargs):
        discounted_price = self.unit_price * (1 - self.discount / 100)
        self.total_amount = self.quantity * discounted_price
        super().save(*args, **kwargs)

    def approve(self, user):
        if self.status == 'pending':
            if self.product.current_stock < self.quantity:
                return False
            self.status = 'approved'
            self.approved_by = user.username
            self.approved_at = timezone.now()
            self.rejection_reason = ''
            self.save()
            return True
        return False

    def reject(self, user, reason=""):
        if self.status == 'pending':
            self.status = 'rejected'
            self.approved_by = user.username
            self.approved_at = timezone.now()
            self.rejection_reason = reason
            self.save()
            return True
        return False

    def ship(self, user):
        if self.status == 'approved':
            self.status = 'shipped'
            self.approved_by = user.username
            self.approved_at = timezone.now()
            self.save()
            return True
        return False

    def __str__(self):
        return f"{self.order_number} - {self.product.name}"


class InventoryLog(models.Model):
    TRANSACTION_TYPE = [
        ('IN', '采购入库'),
        ('OUT', '销售出库'),
        ('ADJ', '库存调整'),
        ('TRF', '仓库转移'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField('类型', max_length=3, choices=TRANSACTION_TYPE)
    quantity = models.IntegerField('变动数量')
    reference = models.CharField('关联单据', max_length=50)
    operator = models.CharField('操作员', max_length=50)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)
    notes = models.TextField('备注', blank=True)
    location_from = models.CharField('源库位', max_length=20, blank=True)
    location_to = models.CharField('目标库位', max_length=20, blank=True)

    objects = InventoryLogManager()

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.quantity}"