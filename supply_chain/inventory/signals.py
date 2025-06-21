# E:\pycharm_pro_project\supply_chain\inventory\signals.py

from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import Purchase, SalesOrder, InventoryLog, Product


@receiver(pre_save, sender=Purchase)
def update_product_on_purchase(sender, instance, **kwargs):
    """处理采购订单状态变化"""
    if instance.pk:  # 确保是更新操作，而不是创建
        try:
            original = Purchase.objects.get(pk=instance.pk)
        except Purchase.DoesNotExist:
            return  # 如果找不到原始记录，直接返回

        # 从未批准到批准状态
        if original.status != 'approved' and instance.status == 'approved':
            # 更新库存
            instance.product.current_stock += instance.quantity
            instance.product.save()

            # 创建库存日志
            InventoryLog.objects.create(
                product=instance.product,
                transaction_type='IN',
                quantity=instance.quantity,
                reference=instance.order_number,
                operator=instance.operator
            )

        # 从批准到取消状态
        elif original.status == 'approved' and instance.status == 'canceled':
            # 恢复库存
            instance.product.current_stock -= instance.quantity
            instance.product.save()

            # 创建库存日志（负向调整）
            InventoryLog.objects.create(
                product=instance.product,
                transaction_type='ADJ',
                quantity=-instance.quantity,
                reference=instance.order_number,
                operator=instance.operator,
                notes=f"采购取消：{instance.rejection_reason}"
            )


@receiver(pre_save, sender=SalesOrder)
def update_product_on_sales(sender, instance, **kwargs):
    """处理销售订单状态变化"""
    if instance.pk:  # 确保是更新操作
        try:
            original = SalesOrder.objects.get(pk=instance.pk)
        except SalesOrder.DoesNotExist:
            return  # 如果找不到原始记录，直接返回

        # 从未批准到批准状态
        if original.status != 'approved' and instance.status == 'approved':
            # 减少库存
            instance.product.current_stock -= instance.quantity
            instance.product.save()

            # 创建库存日志
            InventoryLog.objects.create(
                product=instance.product,
                transaction_type='OUT',
                quantity=-instance.quantity,
                reference=instance.order_number,
                operator=instance.operator
            )

        # 从批准到取消状态
        elif original.status == 'approved' and instance.status == 'canceled':
            # 恢复库存
            instance.product.current_stock += instance.quantity
            instance.product.save()

            # 创建库存日志（正向调整）
            InventoryLog.objects.create(
                product=instance.product,
                transaction_type='ADJ',
                quantity=instance.quantity,
                reference=instance.order_number,
                operator=instance.operator,
                notes=f"销售取消：{instance.rejection_reason}"
            )


@receiver(pre_save, sender=InventoryLog)
def prevent_manual_log_edit(sender, instance, **kwargs):
    """防止手动修改库存日志"""
    if instance.pk:
        raise PermissionError("库存日志不可修改")