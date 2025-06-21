from django.db import models
from django.db.models import F, Q, Sum
from django.db.models.functions import Coalesce


class ProductManager(models.Manager):
    def with_low_stock(self, threshold=None):
        """获取库存低于警戒线的产品"""
        if threshold is None:
            # 如果没有指定阈值，使用每个产品自己的警戒值
            return self.filter(current_stock__lt=F('alert_threshold'))
        else:
            # 使用指定阈值过滤
            return self.filter(current_stock__lt=threshold)

    def stock_value_analysis(self):
        """分析库存价值 - 按类别分组"""
        return self.values('category').annotate(
            total_value=Sum(F('current_stock') * F('unit_price')),
            avg_value=Coalesce(Sum(F('current_stock') * F('unit_price')), 0) / Coalesce(Sum('current_stock'), 1)
        )


class InventoryLogManager(models.Manager):
    def log_transaction(self, product, transaction_type, quantity, operator, reference=None, notes=None):
        """记录库存交易日志"""
        log = self.create(
            product=product,
            transaction_type=transaction_type,
            quantity=quantity,
            operator=operator,
            reference=reference,
            notes=notes
        )
        # 更新产品库存
        if transaction_type == 'IN':
            product.current_stock += quantity
        elif transaction_type == 'OUT':
            product.current_stock -= quantity
        product.save()
        return log

    def recent_transactions(self, days=7):
        """获取最近N天的库存变动记录"""
        from django.utils import timezone
        return self.filter(created_at__gte=timezone.now() - timezone.timedelta(days=days))


class PurchaseManager(models.Manager):
    def pending_approval(self):
        """获取待批准的采购订单"""
        return self.filter(status='pending')

    def by_supplier(self, supplier_id):
        """按供应商获取采购订单"""
        return self.filter(supplier__id=supplier_id).order_by('-created_at')


class SalesOrderManager(models.Manager):
    def pending_approval(self):
        """获取待批准的销售订单"""
        return self.filter(status='pending')

    def recent_sales(self, days=30):
        """获取最近N天的销售订单"""
        from django.utils import timezone
        return self.filter(
            status='approved',
            created_at__gte=timezone.now() - timezone.timedelta(days=days)
        )