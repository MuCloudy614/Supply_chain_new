# E:\pycharm_pro_project\supply_chain\inventory\querysets.py

from django.db import models
from django.db.models import F, Case, When, Value
from django.utils import timezone
from datetime import timedelta


class ProductQuerySet(models.QuerySet):
    def low_stock(self):
        """获取库存低于预警值的产品"""
        return self.filter(current_stock__lt=F('alert_threshold'))

    def critical_stock(self):
        """获取库存量为0的产品"""
        return self.filter(current_stock=0)

    def with_status(self):
        """添加库存状态注解"""
        return self.annotate(
            status=Case(
                When(current_stock=0, then=Value('缺货')),
                When(current_stock__lt=F('alert_threshold'), then=Value('预警')),
                default=Value('正常'),
                output_field=models.CharField()
            ),
            status_class=Case(
                When(current_stock=0, then=Value('text-danger')),
                When(current_stock__lt=F('alert_threshold'), then=Value('text-warning')),
                default=Value('text-success'),
                output_field=models.CharField()
            )
        )


class InventoryLogQuerySet(models.QuerySet):
    def recent(self, days=30, limit=50):
        """获取最近days天的日志记录"""
        return self.filter(
            created_at__gte=timezone.now() - timedelta(days=days)
        ).order_by('-created_at')[:limit]


class PurchaseQuerySet(models.QuerySet):
    def pending_approval(self):
        """待审批的采购订单"""
        return self.filter(status='pending')

    def recently_approved(self):
        """最近批准的订单"""
        return self.filter(status='approved').order_by('-approved_at')[:10]


class SalesOrderQuerySet(models.QuerySet):
    def pending_approval(self):
        """待审批的销售订单"""
        return self.filter(status='pending')

    def recently_approved(self):
        """最近批准的订单"""
        return self.filter(status='approved').order_by('-approved_at')[:10]