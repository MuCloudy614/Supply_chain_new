from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Purchase, SalesOrder, InventoryLog, Product


@receiver(post_save, sender=Purchase)
def handle_purchase(sender, instance, created, **kwargs):
    if created:
        # 更新产品库存
        product = instance.product
        product.current_stock += instance.quantity
        product.save()

        # 创建库存日志
        InventoryLog.objects.create(
            product=product,
            transaction_type='IN',
            quantity=instance.quantity,
            reference=instance.order_number,
            operator=instance.operator
        )


@receiver(post_save, sender=SalesOrder)
def handle_sales(sender, instance, created, **kwargs):
    if created:
        # 更新产品库存
        product = instance.product
        product.current_stock -= instance.quantity
        product.save()

        # 创建库存日志
        InventoryLog.objects.create(
            product=product,
            transaction_type='OUT',
            quantity=-instance.quantity,
            reference=instance.order_number,
            operator=instance.operator
        )