# 在 E:\pycharm_pro_project\supply_chain\inventory\reports.py

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle


def generate_stock_report(products, report_date):
    """使用 ReportLab 生成库存报告"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # 添加标题
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Title'],
        fontSize=16,
        spaceAfter=12
    )
    elements.append(Paragraph('库存报告', title_style))
    elements.append(Paragraph(f'报告日期: {report_date}', styles['Normal']))

    # 添加产品表格
    data = [['产品代码', '产品名称', '当前库存', '单位', '库存状态', '库位']]
    for p in products:
        status = '缺货' if p.current_stock == 0 else '预警' if p.current_stock < p.alert_threshold else '正常'
        data.append([p.code, p.name, str(p.current_stock), p.unit, status, p.location or ''])

    t = Table(data, colWidths=[60, 120, 50, 40, 40, 60], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(t)

    # 生成 PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_transaction_report(transactions, report_date):
    """使用 ReportLab 生成交易报告"""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []

    # 添加标题
    styles = getSampleStyleSheet()
    elements.append(Paragraph('交易记录报告', styles['Title']))
    elements.append(Paragraph(f'报告日期: {report_date}', styles['Normal']))

    # 添加交易表格
    data = [['时间', '类型', '产品', '数量', '操作员', '参考单据']]
    for t in transactions:
        ref_text = t.reference if isinstance(t.reference,
                                             str) else f"{type(t.reference).__name__} #{getattr(t.reference, 'id', '')}"
        data.append([
            t.created_at.strftime("%Y-%m-%d %H:%M"),
            t.get_transaction_type_display(),
            t.product.name,
            f"{t.quantity:+d}",
            t.operator,
            ref_text
        ])

    t = Table(data, colWidths=[80, 40, 100, 40, 60, 100], repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (3, 1), (3, -1), 'RIGHT'),
    ]))
    elements.append(t)

    # 生成 PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer