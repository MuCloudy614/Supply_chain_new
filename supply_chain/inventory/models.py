from django.db import models
from django.core.exceptions import ValidationError


class Product(models.Model):
    CATEGORY_CHOICES = [
        ('RM', '原材料'),
        ('FP', '成品'),
        ('SF', '办公用品'),
    ]

    name = models.CharField('产品名称', max_length=100)
    code = models.CharField('产品编号', max_length=20, unique=True)
    category = models.CharField('分类', max_length=2, choices=CATEGORY_CHOICES)
    current_stock = models.PositiveIntegerField('当前库存', default=0)
    alert_threshold = models.PositiveIntegerField('库存预警值', default=10)

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def stock_status(self):
        if self.current_stock == 0:
            return '<span style="color:red;">缺货</span>'
        elif self.current_stock < self.alert_threshold:
            return '<span style="color:orange;">预警</span>'
        return '<span style="color:green;">正常</span>'

    class Meta:
        permissions = [
            ("export_product", "导出产品数据"),
            ("manage_product", "管理产品库存"),
        ]


class Purchase(models.Model):
    order_number = models.CharField('采购单号', max_length=50, unique=True)
    supplier = models.CharField('供应商', max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='产品')
    quantity = models.PositiveIntegerField('数量')
    created_at = models.DateTimeField('入库日期', auto_now_add=True)
    operator = models.CharField('操作员', max_length=50)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("采购数量必须大于0")

    class Meta:
        permissions = [
            ("approve_purchase", "审批采购订单"),
        ]


class SalesOrder(models.Model):
    order_number = models.CharField('订单号', max_length=50, unique=True)
    customer = models.CharField('客户', max_length=100)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, verbose_name='产品')
    quantity = models.PositiveIntegerField('数量')
    created_at = models.DateTimeField('出库日期', auto_now_add=True)
    operator = models.CharField('操作员', max_length=50)

    def clean(self):
        if self.quantity <= 0:
            raise ValidationError("销售数量必须大于0")
        if self.product.current_stock < self.quantity:
            raise ValidationError(
                f"库存不足！当前库存：{self.product.current_stock}"
            )

    class Meta:
        permissions = [
            ("approve_sales", "审批销售订单"),
        ]


class InventoryLog(models.Model):
    TRANSACTION_TYPE = [
        ('IN', '采购入库'),
        ('OUT', '销售出库'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    transaction_type = models.CharField('类型', max_length=3, choices=TRANSACTION_TYPE)
    quantity = models.IntegerField('变动数量')
    reference = models.CharField('关联单据', max_length=50)
    operator = models.CharField('操作员', max_length=50)
    created_at = models.DateTimeField('操作时间', auto_now_add=True)

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.quantity}"