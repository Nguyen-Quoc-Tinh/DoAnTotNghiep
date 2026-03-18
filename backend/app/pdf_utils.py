from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


FONT_NAME = "Helvetica"
FONT_BOLD_NAME = "Helvetica-Bold"

FEATURE_BASE_NAMES = [
    "Radius",
    "Texture",
    "Perimeter",
    "Area",
    "Smoothness",
    "Compactness",
    "Concavity",
    "Concave Points",
    "Symmetry",
    "Fractal Dimension",
]

FEATURE_GROUP_LAYOUT = [
    ("MEAN", 0, 10),
    ("STANDARD ERROR", 10, 20),
    ("WORST", 20, 30),
]


def _register_font() -> str:
    global FONT_NAME, FONT_BOLD_NAME

    if FONT_NAME != "Helvetica":
        return FONT_NAME

    # Ưu tiên font hỗ trợ tiếng Việt đầy đủ
    candidates = [
        (Path("C:/Windows/Fonts/arialuni.ttf"), None),               # Arial Unicode MS
        (Path("C:/Windows/Fonts/arial.ttf"), Path("C:/Windows/Fonts/arialbd.ttf")),  # Arial + Bold
        (Path("C:/Windows/Fonts/times.ttf"),  Path("C:/Windows/Fonts/timesbd.ttf")), # Times New Roman
        (Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
         Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")),
        (Path("/Library/Fonts/Arial Unicode.ttf"), None),
    ]

    for regular, bold in candidates:
        if regular.exists():
            pdfmetrics.registerFont(TTFont("VietFont", str(regular)))
            FONT_NAME = "VietFont"
            if bold and bold.exists():
                pdfmetrics.registerFont(TTFont("VietFont-Bold", str(bold)))
                FONT_BOLD_NAME = "VietFont-Bold"
            else:
                FONT_BOLD_NAME = "VietFont"
            break

    return FONT_NAME


def _stringify(value) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float):
        return f"{value:.4f}"
    if isinstance(value, list):
        return ", ".join(_stringify(item) for item in value)
    if isinstance(value, dict):
        return "; ".join(f"{key}: {_stringify(item)}" for key, item in value.items())
    return str(value)


def _to_multiline_text(value) -> str:
    """Convert long text blocks to HTML-safe lines for ReportLab Paragraph."""
    text = escape(_stringify(value))
    return text.replace("; ", "<br/>").replace(", ", "<br/>")


def _is_30_features_payload(input_data: dict) -> bool:
    features = input_data.get("features")
    return isinstance(features, list) and len(features) == 30


def _build_grouped_feature_tables(features, label_style, table_cell_style):
    story_part = []
    for group_label, start, end in FEATURE_GROUP_LAYOUT:
        group_values = features[start:end]
        group_heading = Paragraph(f"<b>{escape(group_label)}</b>", label_style)
        story_part.append(group_heading)
        story_part.append(Spacer(1, 4))

        first_labels = [Paragraph(f"<b>{name}</b>", table_cell_style) for name in FEATURE_BASE_NAMES[:5]]
        second_labels = [Paragraph(f"<b>{name}</b>", table_cell_style) for name in FEATURE_BASE_NAMES[5:]]

        first_values = [Paragraph(escape(_stringify(v)), table_cell_style) for v in group_values[:5]]
        second_values = [Paragraph(escape(_stringify(v)), table_cell_style) for v in group_values[5:]]

        table_rows = [
            first_labels,
            first_values,
            second_labels,
            second_values,
        ]

        group_table = Table(table_rows, colWidths=[32 * mm, 32 * mm, 32 * mm, 32 * mm, 32 * mm])
        group_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, -1), FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#111827")),
                    ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f5f3ff"), colors.white]),
                    ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c4b5fd")),
                    ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#ddd6fe")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("PADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        story_part.append(group_table)
        story_part.append(Spacer(1, 10))

    return story_part


def build_diagnosis_pdf(record: dict, username: str) -> bytes:
    font_name = _register_font()
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PdfTitle",
        parent=styles["Title"],
        fontName=font_name,
        textColor=colors.HexColor("#7c3aed"),
        fontSize=20,
        leading=24,
        spaceAfter=12,
    )
    body_style = ParagraphStyle(
        "PdfBody",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
    )
    heading_style = ParagraphStyle(
        "PdfHeading",
        parent=styles["Heading2"],
        fontName=FONT_BOLD_NAME,
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#111827"),
        spaceBefore=8,
        spaceAfter=8,
    )
    label_style = ParagraphStyle(
        "PdfLabel",
        parent=styles["BodyText"],
        fontName=FONT_BOLD_NAME,
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#5b21b6"),
    )
    table_cell_style = ParagraphStyle(
        "PdfTableCell",
        parent=styles["BodyText"],
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#111827"),
        wordWrap="CJK",
    )

    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    diagnosis_label = "Sinh hóa" if record["diagnosis_type"] == "biochemical" else "Hình ảnh y khoa"
    prediction_label = "Lành tính" if record["prediction"] == "benign" else "Ác tính"
    prediction_color = colors.HexColor("#166534") if record["prediction"] == "benign" else colors.HexColor("#991b1b")

    summary_rows = [
        [Paragraph("<b>Trường</b>", label_style), Paragraph("<b>Giá trị</b>", label_style)],
        ["Mã hồ sơ", record.get("record_code") or f"HS-{str(record.get('_id', ''))[-8:].upper()}"],
        ["Người dùng", username],
        ["Loại chẩn đoán", diagnosis_label],
        ["Kết quả", prediction_label],
        ["Độ tin cậy", f"{record['confidence'] * 100:.2f}%"],
        ["Thời gian", record["created_at"].strftime("%d/%m/%Y %H:%M:%S")],
    ]

    if record.get("file_name"):
        summary_rows.append(["Tên tệp", record["file_name"]])

    if record.get("probabilities"):
        prob = record["probabilities"]
        prob_text = (
            f"Lành tính: {prob.get('benign', prob.get('Benign', '?')):.2%}  |  "
            f"Ác tính: {prob.get('malignant', prob.get('Malignant', '?')):.2%}"
            if isinstance(prob, dict) and all(isinstance(v, float) for v in prob.values())
            else _stringify(prob)
        )
        summary_rows.append(["Phân bố xác suất", prob_text])

    story = [
        Paragraph("Báo Cáo Chẩn Đoán Ung Thư Vú", title_style),
        Paragraph(
            "Tài liệu này tổng hợp kết quả chẩn đoán và được sinh từ hệ thống hỗ trợ quyết định lâm sàng.",
            body_style,
        ),
        Spacer(1, 10),
    ]

    summary_table = Table(summary_rows, colWidths=[50 * mm, 110 * mm])
    summary_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), font_name),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                # Data rows alternating
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
                ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#111827")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#c4b5fd")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#ddd6fe")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # Dữ liệu đầu vào
    input_data = record.get("input_data", {})
    if input_data:
        story.append(Paragraph("Dữ liệu đầu vào", heading_style))
        if isinstance(input_data, dict) and _is_30_features_payload(input_data):
            story.extend(_build_grouped_feature_tables(input_data["features"], label_style, table_cell_style))
        elif isinstance(input_data, dict):
            input_rows = [[Paragraph("<b>Đặc trưng</b>", label_style), Paragraph("<b>Giá trị</b>", label_style)]]
            for k, v in input_data.items():
                input_rows.append(
                    [
                        Paragraph(escape(str(k)), table_cell_style),
                        Paragraph(_to_multiline_text(v), table_cell_style),
                    ]
                )
            input_table = Table(input_rows, colWidths=[80 * mm, 80 * mm])
            input_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c4b5fd")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#ddd6fe")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(input_table)
        else:
            fallback_rows = [
                [Paragraph("<b>Đặc trưng</b>", label_style), Paragraph("<b>Giá trị</b>", label_style)],
                [Paragraph("Dữ liệu", table_cell_style), Paragraph(_to_multiline_text(input_data), table_cell_style)],
            ]
            fallback_table = Table(fallback_rows, colWidths=[80 * mm, 80 * mm])
            fallback_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c4b5fd")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#ddd6fe")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(fallback_table)

    if record.get("explanation"):
        story.append(Spacer(1, 10))
        story.append(Paragraph("Giải thích bổ sung", heading_style))
        expl = record["explanation"]
        if isinstance(expl, dict):
            expl_rows = [[Paragraph("<b>Đặc trưng</b>", label_style), Paragraph("<b>Đóng góp (SHAP)</b>", label_style)]]
            for k, v in expl.items():
                expl_rows.append(
                    [
                        Paragraph(escape(str(k)), table_cell_style),
                        Paragraph(_to_multiline_text(v), table_cell_style),
                    ]
                )
            expl_table = Table(expl_rows, colWidths=[80 * mm, 80 * mm])
            expl_table.setStyle(
                TableStyle(
                    [
                        ("FONTNAME", (0, 0), (-1, -1), font_name),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#7c3aed")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f3ff")]),
                        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c4b5fd")),
                        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#ddd6fe")),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]
                )
            )
            story.append(expl_table)
        else:
            story.append(Paragraph(escape(_stringify(expl)), body_style))

    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "<b>⚠ Khuyến nghị:</b> Kết quả này chỉ mang tính hỗ trợ và không thay thế chẩn đoán lâm sàng. "
            "Cần được đối chiếu với thăm khám chuyên khoa và các xét nghiệm lâm sàng phù hợp.",
            body_style,
        )
    )

    document.build(story)
    return pdf_buffer.getvalue()