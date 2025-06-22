
写的不太好，各位大佬轻点喷qaq

是一个基于Web技术开发的​​全栈供应链管理系统​​，覆盖了采购管理、库存控制、销售跟踪等核心供应链流程，通过自动化工作流和实时数据分析提升企业运营效率

核心功能

模块	           主要功能	                          创新点
​​采购管理​​	  供应商管理、采购订单、审批流程	      自动库存更新+供应商评估
​​库存控制​​	  实时库存跟踪、低库存预警、调拨管理	  双警戒线预警+库存日志
​​销售管理​​	  客户管理、销售订单、销售审批	        客户等级分类+历史数据分析
​​报表分析​​	  库存报告、交易历史、经营分析	        多格式导出(Excel/PDF)+图表可视化

​​
架构

前端
​​框架​​: Django Templates + Bootstrap 5
​​交互​​: jQuery + HTMX
​​图表​​: Chart.js
​​样式​​: Font Awesome 图标库

后端

​​核心框架​​	 Django 4.2
​​数据库​​	   SQLite (开发) / PostgreSQL (生产)
​​API服务​​	 Django REST Framework
​​任务队列​​	 Celery + Redis
​​身份认证​​	 Django Auth + JWT
​​报表生成​​	 ReportLab + xhtml2pdf

架构图

客户端 (浏览器)
   ↑↓ HTTP/HTTPS
Django应用服务器
   ↑↓ ORM
数据库 (SQLite/PostgreSQL)
   ↑↓ 异步通信
任务队列 (Celery)
