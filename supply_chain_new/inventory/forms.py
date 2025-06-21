# E:\pycharm_pro_project\supply_chain\inventory\forms.py

from django import forms
from .models import Purchase, SalesOrder, InventoryLog


class PurchaseApprovalForm(forms.ModelForm):
    ACTION_CHOICES = [
        ('approve', '批准'),
        ('reject', '拒绝'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect,
        label='审批操作'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='拒绝原因'
    )

    class Meta:
        model = Purchase
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加只读字段展示订单详情
        self.fields['order_number'] = forms.CharField(
            initial=self.instance.order_number,
            disabled=True,
            label='采购单号'
        )
        self.fields['supplier'] = forms.CharField(
            initial=self.instance.supplier.name if self.instance.supplier else '',
            disabled=True,
            label='供应商'
        )
        self.fields['product'] = forms.CharField(
            initial=self.instance.product.name,
            disabled=True,
            label='产品'
        )
        self.fields['quantity'] = forms.IntegerField(
            initial=self.instance.quantity,
            disabled=True,
            label='数量'
        )


class SalesApprovalForm(forms.ModelForm):
    ACTION_CHOICES = [
        ('approve', '批准'),
        ('reject', '拒绝'),
    ]

    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.RadioSelect,
        label='审批操作'
    )
    reason = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}),
        required=False,
        label='拒绝原因'
    )

    class Meta:
        model = SalesOrder
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加只读字段展示订单详情
        self.fields['order_number'] = forms.CharField(
            initial=self.instance.order_number,
            disabled=True,
            label='销售单号'
        )
        self.fields['customer'] = forms.CharField(
            initial=self.instance.customer.name if self.instance.customer else '',
            disabled=True,
            label='客户'
        )
        self.fields['product'] = forms.CharField(
            initial=self.instance.product.name,
            disabled=True,
            label='产品'
        )
        self.fields['quantity'] = forms.IntegerField(
            initial=self.instance.quantity,
            disabled=True,
            label='数量'
        )
        self.fields['current_stock'] = forms.IntegerField(
            initial=self.instance.product.current_stock,
            disabled=True,
            label='当前库存'
        )


class LowStockReportForm(forms.Form):
    include_critical = forms.BooleanField(
        label='包含缺货产品',
        initial=True,
        required=False
    )
    include_warning = forms.BooleanField(
        label='包含库存预警产品',
        initial=True,
        required=False
    )
    sort_by = forms.ChoiceField(
        label='排序方式',
        choices=[
            ('stock', '库存数量'),
            ('value', '库存价值'),
            ('name', '产品名称')
        ],
        initial='stock'
    )


class TransactionReportForm(forms.Form):
    start_date = forms.DateField(
        label='开始日期',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    end_date = forms.DateField(
        label='结束日期',
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    transaction_type = forms.ChoiceField(
        label='交易类型',
        choices=[('', '所有类型')] + InventoryLog.TRANSACTION_TYPE,
        required=False
    )