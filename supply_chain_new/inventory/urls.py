# E:\pycharm_pro_project\supply_chain_new\inventory\urls.py

from django.urls import path, include
from . import views
from rest_framework.routers import DefaultRouter

# 注册应用命名空间
app_name = 'inventory'

# 创建路由器并注册视图集
router = DefaultRouter()
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'purchases', views.PurchaseViewSet, basename='purchase')
router.register(r'salesorders', views.SalesOrderViewSet, basename='salesorder')

urlpatterns = [
    # 仪表盘
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # 产品相关路由
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),

    # 供应商相关路由
    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/<int:pk>/', views.SupplierDetailView.as_view(), name='supplier_detail'),

    # 客户相关路由
    path('customers/', views.CustomerListView.as_view(), name='customer_list'),
    path('customers/<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),

    # 采购订单相关路由
    path('purchase/approval/', views.PurchaseApprovalView.as_view(), name='purchase_approval'),
    path('purchase/approve/<int:pk>/', views.PurchaseApproveView.as_view(), name='purchase_approve'),

    # 销售订单相关路由
    path('sales/approval/', views.SalesApprovalView.as_view(), name='sales_approval'),
    path('sales/approve/<int:pk>/', views.SalesApproveView.as_view(), name='sales_approve'),

    # 报表相关路由
    path('reports/low-stock/', views.LowStockReportView.as_view(), name='low_stock_report'),
    path('reports/transaction/', views.TransactionReportView.as_view(), name='transaction_report'),
    path('reports/pdf/<str:report_type>/', views.PDFReportView.as_view(), name='pdf_report'),

    # API 路由
    path('api/', include(router.urls)),
]