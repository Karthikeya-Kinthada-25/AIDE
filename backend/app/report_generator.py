from pathlib import Path
from io import BytesIO
from datetime import datetime

from PIL import Image as PILImage

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
    KeepTogether,
)
from reportlab.pdfbase.pdfmetrics import stringWidth
from app.report_manipulation import (
    build_manipulation_report_section
)


# =========================================================
# AIDE FORENSIC REPORT GENERATOR
# =========================================================

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 16 * mm
RIGHT_MARGIN = 16 * mm
TOP_MARGIN = 18 * mm
BOTTOM_MARGIN = 16 * mm

CONTENT_WIDTH = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN


# =========================================================
# SAFE VALUE HELPERS
# =========================================================

def safe(value, default="N/A"):
    if value is None:
        return default

    if isinstance(value, str) and not value.strip():
        return default

    return value


def fmt_number(value, digits=4):
    if value is None:
        return "N/A"

    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def fmt_percent(value):
    if value is None:
        return "N/A"

    try:
        return f"{float(value) * 100:.2f}%"
    except (TypeError, ValueError):
        return str(value)


def get_nested(data, *keys, default=None):
    current = data

    for key in keys:
        if not isinstance(current, dict):
            return default

        current = current.get(key)

        if current is None:
            return default

    return current


# =========================================================
# IMAGE PREPARATION
# =========================================================

def prepare_image_for_pdf(
    image_path,
    max_width,
    max_height,
    jpeg_quality=88
):
    """
    Resize an image in memory while preserving its aspect ratio.

    This prevents very large source images from making the PDF
    unnecessarily large.
    """

    if not image_path:
        return None

    image_path = Path(image_path)

    if not image_path.exists():
        return None

    try:
        with PILImage.open(image_path) as img:

            img = img.convert("RGB")

            original_width, original_height = img.size

            if original_width <= 0 or original_height <= 0:
                return None

            scale = min(
                max_width / original_width,
                max_height / original_height,
                1.0
            )

            new_width = max(
                1,
                int(original_width * scale)
            )

            new_height = max(
                1,
                int(original_height * scale)
            )

            if scale < 1.0:
                img = img.resize(
                    (new_width, new_height),
                    PILImage.Resampling.LANCZOS
                )

            buffer = BytesIO()

            img.save(
                buffer,
                format="JPEG",
                quality=jpeg_quality,
                optimize=True
            )

            buffer.seek(0)

            return buffer

    except Exception:
        return None


def add_image(
    story,
    image_path,
    max_width,
    max_height,
    caption=None
):
    """
    Add a correctly oriented, aspect-ratio-preserving image.
    """

    prepared = prepare_image_for_pdf(
        image_path,
        max_width,
        max_height
    )

    if prepared is None:
        return

    try:
        img = PILImage.open(prepared)

        width_px, height_px = img.size

        if width_px <= 0 or height_px <= 0:
            return

        ratio = width_px / height_px

        display_width = max_width
        display_height = display_width / ratio

        if display_height > max_height:
            display_height = max_height
            display_width = display_height * ratio

        pdf_image = Image(
            prepared,
            width=display_width,
            height=display_height
        )

        pdf_image.hAlign = "CENTER"

        story.append(pdf_image)

        if caption:
            story.append(
                Paragraph(
                    caption,
                    styles["image_caption"]
                )
            )

        story.append(
            Spacer(1, 4 * mm)
        )

    except Exception:
        return


# =========================================================
# STYLES
# =========================================================

styles = getSampleStyleSheet()


styles.add(
    ParagraphStyle(
        name="ReportTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=23,
        leading=27,
        alignment=TA_CENTER,
        spaceAfter=5 * mm,
        textColor=colors.HexColor("#172033"),
    )
)


styles.add(
    ParagraphStyle(
        name="ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#596579"),
        spaceAfter=7 * mm,
    )
)


styles.add(
    ParagraphStyle(
        name="SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#172033"),
        spaceBefore=4 * mm,
        spaceAfter=3 * mm,
        keepWithNext=True,
    )
)


styles.add(
    ParagraphStyle(
        name="SubHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#26344A"),
        spaceBefore=2.5 * mm,
        spaceAfter=2 * mm,
        keepWithNext=True,
    )
)


styles.add(
    ParagraphStyle(
        name="BodyCompact",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12,
        textColor=colors.HexColor("#303A4A"),
        spaceAfter=2.5 * mm,
    )
)


styles.add(
    ParagraphStyle(
        name="SmallText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10,
        textColor=colors.HexColor("#4B5565"),
    )
)


styles.add(
    ParagraphStyle(
        name="TableText",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.7,
        leading=9.5,
        textColor=colors.HexColor("#263244"),
    )
)


styles.add(
    ParagraphStyle(
        name="TableTextBold",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=7.7,
        leading=9.5,
        textColor=colors.HexColor("#172033"),
    )
)


styles.add(
    ParagraphStyle(
        name="ImageCaption",
        parent=styles["BodyText"],
        fontName="Helvetica-Oblique",
        fontSize=7.5,
        leading=9,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#667085"),
        spaceBefore=1 * mm,
        spaceAfter=3 * mm,
    )
)


styles.add(
    ParagraphStyle(
        name="CoverLabel",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#667085"),
    )
)


styles.add(
    ParagraphStyle(
        name="Score",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#172033"),
    )
)


styles.add(
    ParagraphStyle(
        name="ScoreLabel",
        parent=styles["BodyText"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#596579"),
    )
)


styles.add(
    ParagraphStyle(
        name="Warning",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#664D03"),
    )
)


styles.add(
    ParagraphStyle(
        name="Conclusion",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#263244"),
    )
)


# =========================================================
# TABLE HELPERS
# =========================================================

def p(text, style="TableText"):
    return Paragraph(str(safe(text)), styles[style])


def create_two_column_table(rows):
    table_data = []

    for key, value in rows:
        table_data.append(
            [
                p(key, "TableTextBold"),
                p(value, "TableText"),
            ]
        )

    table = Table(
        table_data,
        colWidths=[
            CONTENT_WIDTH * 0.31,
            CONTENT_WIDTH * 0.69
        ],
        repeatRows=0,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#F2F4F7"),
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, -1),
                    colors.white,
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D0D5DD"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#E4E7EC"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


def create_data_table(headers, rows, widths=None):
    data = [
        [
            p(header, "TableTextBold")
            for header in headers
        ]
    ]

    for row in rows:
        data.append(
            [
                p(value, "TableText")
                for value in row
            ]
        )

    if widths is None:
        widths = [
            CONTENT_WIDTH / len(headers)
        ] * len(headers)

    table = Table(
        data,
        colWidths=widths,
        repeatRows=1,
        hAlign="LEFT",
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#E9EEF5"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#172033"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#C7CDD6"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#E1E5EA"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
            ]
        )
    )

    return table


# =========================================================
# SECTION / BOX HELPERS
# =========================================================

def section_heading(number, title):
    return Paragraph(
        f"{number}. {title}",
        styles["SectionHeading"]
    )


def info_box(title, body, background="#F8FAFC"):
    data = [
        [
            Paragraph(
                f"<b>{title}</b>",
                styles["TableTextBold"]
            )
        ],
        [
            Paragraph(
                body,
                styles["BodyCompact"]
            )
        ]
    ]

    table = Table(
        data,
        colWidths=[CONTENT_WIDTH],
        hAlign="LEFT"
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor(background),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D0D5DD"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    3,
                ),
            ]
        )
    )

    return table


# =========================================================
# HEADER / FOOTER
# =========================================================

def draw_header_footer(canvas, doc):

    canvas.saveState()

    # Header
    canvas.setStrokeColor(
        colors.HexColor("#D0D5DD")
    )

    canvas.setLineWidth(0.5)

    canvas.line(
        LEFT_MARGIN,
        PAGE_HEIGHT - 11 * mm,
        PAGE_WIDTH - RIGHT_MARGIN,
        PAGE_HEIGHT - 11 * mm
    )

    canvas.setFont(
        "Helvetica-Bold",
        7.5
    )

    canvas.setFillColor(
        colors.HexColor("#475467")
    )

    canvas.drawString(
        LEFT_MARGIN,
        PAGE_HEIGHT - 8 * mm,
        "AIDE"
    )

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        PAGE_HEIGHT - 8 * mm,
        "Digital Image Evidence Forensic Report"
    )

    # Footer
    canvas.line(
        LEFT_MARGIN,
        10 * mm,
        PAGE_WIDTH - RIGHT_MARGIN,
        10 * mm
    )

    canvas.setFont(
        "Helvetica",
        7
    )

    canvas.setFillColor(
        colors.HexColor("#667085")
    )

    canvas.drawString(
        LEFT_MARGIN,
        6.5 * mm,
        "AIDE · Prototype forensic decision-support system"
    )

    canvas.drawRightString(
        PAGE_WIDTH - RIGHT_MARGIN,
        6.5 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# =========================================================
# COVER PAGE
# =========================================================

def build_cover(
    story,
    evidence_filename,
    analysis_data
):

    story.append(
        Spacer(1, 25 * mm)
    )

    story.append(
        Paragraph(
            "AIDE",
            styles["ReportTitle"]
        )
    )

    story.append(
        Paragraph(
            "AI-Based Digital Image Evidence<br/>"
            "Integrity &amp; Tampering Detection Platform",
            styles["ReportSubtitle"]
        )
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    story.append(
        Paragraph(
            "FORENSIC ANALYSIS REPORT",
            styles["ReportTitle"]
        )
    )

    story.append(
        Spacer(1, 10 * mm)
    )

    database = (
        analysis_data.get("database", {})
        if isinstance(analysis_data, dict)
        else {}
    )

    evidence_id = database.get(
        "evidence_id",
        "N/A"
    )

    generated_time = datetime.now().strftime(
        "%d %B %Y, %H:%M:%S"
    )

    cover_rows = [
        [
            p("Evidence ID", "TableTextBold"),
            p(evidence_id),
        ],
        [
            p("Evidence Filename", "TableTextBold"),
            p(evidence_filename),
        ],
        [
            p("Report Generated", "TableTextBold"),
            p(generated_time),
        ],
        [
            p("Platform", "TableTextBold"),
            p("AIDE Digital Forensics"),
        ],
    ]

    table = Table(
        cover_rows,
        colWidths=[
            CONTENT_WIDTH * 0.34,
            CONTENT_WIDTH * 0.66
        ],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.HexColor("#E9EEF5"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#C7CDD6"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#E1E5EA"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    7,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.append(table)

    story.append(
        Spacer(1, 18 * mm)
    )

    story.append(
        Paragraph(
            "This report summarizes the results produced by the "
            "current AIDE forensic analysis pipeline.",
            styles["BodyCompact"]
        )
    )

    story.append(
        Paragraph(
            "The measurements and AI outputs are intended as "
            "forensic decision-support indicators and must not "
            "be interpreted as a definitive legal or forensic "
            "determination.",
            styles["Warning"]
        )
    )

    story.append(
        PageBreak()
    )


# =========================================================
# MAIN REPORT
# =========================================================

def generate_forensic_report(
    report_path,
    evidence_filename,
    analysis_data,
    original_image_path,
    ela_image_path=None,
    localization_image_path=None,
    manipulation_analysis=None
):
    """
    Generate the complete AIDE forensic PDF report.

    Parameters:
        report_path:
            Destination PDF path.

        evidence_filename:
            Uploaded/stored evidence filename.

        analysis_data:
            Complete analysis response from AIDE backend.

        original_image_path:
            Path to original uploaded image.

        ela_image_path:
            Optional ELA visualization.

        localization_image_path:
            Optional suspicious-region visualization.
    """

    report_path = Path(report_path)

    report_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    if not isinstance(analysis_data, dict):
        analysis_data = {}

    # =====================================================
    # Extract data
    # =====================================================

    analysis = analysis_data.get(
        "analysis",
        {}
    )

    forensic = analysis_data.get(
        "forensic_analysis",
        {}
    )

    image_info = analysis.get(
        "image",
        {}
    )

    metadata = analysis.get(
        "metadata",
        {}
    )

    metadata_status = analysis.get(
        "metadata_status",
        "Not available"
    )

    ela = forensic.get(
        "ela",
        {}
    )

    features = forensic.get(
        "features",
        {}
    )

    fusion = forensic.get(
        "fusion",
        {}
    )

    ai_detection = forensic.get(
        "ai_detection",
        {}
    )

    evidence_fusion = forensic.get(
        "evidence_fusion",
        {}
    )

    localization = analysis_data.get(
        "localization",
        {}
    )

    manipulation_analysis = (
        manipulation_analysis
        if manipulation_analysis is not None
        else analysis_data.get(
            "manipulation_type",
            {}
        )
    )

    database = analysis_data.get(
        "database",
        {}
    )

    # Some backend versions may store localization inside
    # forensic_analysis.
    if not localization:
        localization = forensic.get(
            "localization",
            {}
        )

    # =====================================================
    # Document
    # =====================================================

    doc = SimpleDocTemplate(
        str(report_path),
        pagesize=A4,
        rightMargin=RIGHT_MARGIN,
        leftMargin=LEFT_MARGIN,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title="AIDE Forensic Analysis Report",
        author="AIDE",
        subject="Digital Image Evidence Forensic Analysis",
        creator="AIDE Digital Forensics Platform",
        allowSplitting=1,
    )

    story = []

    # =====================================================
    # COVER
    # =====================================================

    build_cover(
        story,
        evidence_filename,
        analysis_data
    )

    # =====================================================
    # 1. EVIDENCE INFORMATION
    # =====================================================

    story.append(
        section_heading(
            1,
            "Evidence Information"
        )
    )

    evidence_rows = [
        (
            "Filename",
            evidence_filename
        ),
        (
            "Format",
            image_info.get(
                "format",
                "N/A"
            )
        ),
        (
            "Resolution",
            (
                f"{image_info.get('width', 'N/A')} × "
                f"{image_info.get('height', 'N/A')} pixels"
            )
        ),
        (
            "Image Mode",
            image_info.get(
                "mode",
                "N/A"
            )
        ),
        (
            "File Size",
            (
                f"{image_info.get('file_size_bytes', 'N/A')} "
                f"bytes"
            )
        ),
        (
            "Megapixels",
            image_info.get(
                "megapixels",
                "N/A"
            )
        ),
    ]

    story.append(
        create_two_column_table(
            evidence_rows
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        Paragraph(
            "Original Evidence Image",
            styles["SubHeading"]
        )
    )

    add_image(
        story,
        original_image_path,
        CONTENT_WIDTH,
        78 * mm,
        "Original uploaded evidence image"
    )

    # =====================================================
    # 2. METADATA
    # =====================================================

    story.append(
        section_heading(
            2,
            "Metadata Analysis"
        )
    )

    story.append(
        Paragraph(
            f"<b>Metadata Status:</b> "
            f"{safe(metadata_status)}",
            styles["BodyCompact"]
        )
    )

    metadata_rows = []

    if isinstance(metadata, dict):
        for key, value in metadata.items():

            if isinstance(value, dict):
                value = str(value)

            if isinstance(value, list):
                value = ", ".join(
                    str(item)
                    for item in value
                )

            metadata_rows.append(
                (
                    str(key).replace("_", " ").title(),
                    str(value)
                )
            )

    if metadata_rows:
        story.append(
            create_two_column_table(
                metadata_rows
            )
        )
    else:
        story.append(
            info_box(
                "Metadata Observation",
                "No EXIF metadata was detected in the analyzed image.",
                "#F8FAFC"
            )
        )

    # =====================================================
    # 3. ELA
    # =====================================================

    story.append(
        section_heading(
            3,
            "Error Level Analysis"
        )
    )

    ela_rows = [
        (
            "Analysis Type",
            ela.get(
                "analysis_type",
                "Error Level Analysis"
            )
        ),
        (
            "Compression Quality",
            ela.get(
                "compression_quality",
                "N/A"
            )
        ),
        (
            "Mean Error",
            fmt_number(
                ela.get("mean_error")
            )
        ),
        (
            "Maximum Error",
            fmt_number(
                ela.get("maximum_error")
            )
        ),
        (
            "Standard Deviation",
            fmt_number(
                ela.get("standard_deviation")
            )
        ),
        (
            "Visualization",
            ela.get(
                "visualization",
                "ELA heatmap"
            )
        ),
    ]

    story.append(
        create_two_column_table(
            ela_rows
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    if ela_image_path:
        story.append(
            Paragraph(
                "ELA Visualization",
                styles["SubHeading"]
            )
        )

        add_image(
            story,
            ela_image_path,
            CONTENT_WIDTH,
            72 * mm,
            "Error Level Analysis heatmap"
        )

    story.append(
        info_box(
            "ELA Interpretation",
            "ELA is a JPEG compression-based supporting forensic "
            "technique. Regions showing different error behaviour "
            "may warrant further examination, but ELA alone does "
            "not establish that an image has been manipulated.",
            "#FFF8E7"
        )
    )

    # =====================================================
    # 4. TRADITIONAL FORENSIC FEATURES
    # =====================================================

    story.append(
        section_heading(
            4,
            "Traditional Forensic Features"
        )
    )

    noise = (
        features.get(
            "noise",
            {}
        )
        if isinstance(features, dict)
        else {}
    )

    feature_rows = [
        (
            "Entropy",
            fmt_number(
                features.get("entropy")
            )
        ),
        (
            "Noise Mean",
            fmt_number(
                noise.get("mean")
            )
        ),
        (
            "Noise Standard Deviation",
            fmt_number(
                noise.get("standard_deviation")
            )
        ),
        (
            "Edge Density",
            fmt_number(
                features.get("edge_density")
            )
        ),
        (
            "Laplacian Variance",
            fmt_number(
                features.get("laplacian_variance")
            )
        ),
    ]

    story.append(
        create_two_column_table(
            feature_rows
        )
    )

    # =====================================================
    # 5. FORENSIC CONSISTENCY
    # =====================================================

    story.append(
        section_heading(
            5,
            "Prototype Forensic Consistency"
        )
    )

    consistency_score = fusion.get(
        "score",
        "N/A"
    )

    assessment = fusion.get(
        "assessment",
        {}
    )

    indicators = fusion.get(
        "indicators",
        {}
    )

    consistency_data = [
        [
            Paragraph(
                "Prototype Forensic Consistency",
                styles["ScoreLabel"]
            )
        ],
        [
            Paragraph(
                str(
                    consistency_score
                ),
                styles["Score"]
            )
        ],
        [
            Paragraph(
                safe(
                    assessment.get(
                        "level",
                        "N/A"
                    )
                ),
                styles["ScoreLabel"]
            )
        ],
    ]

    score_table = Table(
        consistency_data,
        colWidths=[
            CONTENT_WIDTH * 0.45
        ],
        hAlign="CENTER"
    )

    score_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F2F4F7"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#C7CDD6"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5,
                ),
            ]
        )
    )

    story.append(score_table)

    story.append(
        Spacer(1, 3 * mm)
    )

    indicator_rows = []

    for key, value in indicators.items():
        indicator_rows.append(
            [
                str(key).replace(
                    "_",
                    " "
                ).title(),
                fmt_number(
                    value,
                    2
                )
            ]
        )

    if indicator_rows:
        story.append(
            create_data_table(
                [
                    "Indicator",
                    "Value"
                ],
                indicator_rows,
                [
                    CONTENT_WIDTH * 0.65,
                    CONTENT_WIDTH * 0.35
                ]
            )
        )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        info_box(
            "Important Interpretation",
            safe(
                fusion.get(
                    "warning",
                    "This is a prototype forensic consistency index "
                    "and is not a validated probability of authenticity "
                    "or tampering."
                )
            ),
            "#FFF8E7"
        )
    )

    # =====================================================
    # 6. AI DETECTION
    # =====================================================

    story.append(
        section_heading(
            6,
            "AI Tampering Detection"
        )
    )

    ai_rows = [
        (
            "Model",
            ai_detection.get(
                "model",
                "N/A"
            )
        ),
        (
            "Device",
            ai_detection.get(
                "device",
                "N/A"
            )
        ),
        (
            "Prediction",
            ai_detection.get(
                "prediction",
                "N/A"
            )
        ),
        (
            "Original Probability",
            fmt_percent(
                ai_detection.get(
                    "original_probability"
                )
            )
        ),
        (
            "Tampered Probability",
            fmt_percent(
                ai_detection.get(
                    "tampered_probability"
                )
            )
        ),
        (
            "Checkpoint Epoch",
            ai_detection.get(
                "checkpoint_epoch",
                "N/A"
            )
        ),
        (
            "Validation F1",
            ai_detection.get(
                "validation_f1",
                "N/A"
            )
        ),
    ]

    story.append(
        create_two_column_table(
            ai_rows
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    story.append(
        info_box(
            "AI Interpretation",
            safe(
                ai_detection.get(
                    "warning",
                    "AI prediction is a model-based forensic "
                    "indication and is not a definitive forensic verdict."
                )
            ),
            "#FFF8E7"
        )
    )

    # =========================================================
    # MANIPULATION-TYPE INDICATION
    # =========================================================

    if manipulation_analysis:

      story.extend(
        build_manipulation_report_section(
            manipulation_analysis=(
                manipulation_analysis
            ),
            section_heading_style=styles["SectionHeading"],
            body_style=styles["BodyCompact"],
            warning_style=styles["Warning"],
         )
       )

      story.append(
        Spacer(
            1,
            8,
        )
      )
    # =====================================================
    # 7. EVIDENCE FUSION
    # =====================================================

    story.append(
        section_heading(
            7,
            "AI + Forensic Evidence Fusion"
        )
    )

    ai_evidence = evidence_fusion.get(
        "ai_evidence",
        {}
    )

    forensic_evidence = evidence_fusion.get(
        "forensic_evidence",
        {}
    )

    fusion_rows = [
        (
            "AI Prediction",
            ai_evidence.get(
                "prediction",
                "N/A"
            )
        ),
        (
            "AI Original Probability",
            fmt_percent(
                ai_evidence.get(
                    "original_probability"
                )
            )
        ),
        (
            "AI Tampered Probability",
            fmt_percent(
                ai_evidence.get(
                    "tampered_probability"
                )
            )
        ),
        (
            "Forensic Consistency Score",
            forensic_evidence.get(
                "consistency_score",
                "N/A"
            )
        ),
        (
            "Forensic Assessment",
            forensic_evidence.get(
                "assessment_level",
                "N/A"
            )
        ),
        (
            "Evidence Relationship",
            evidence_fusion.get(
                "evidence_relationship",
                "N/A"
            )
        ),
        (
            "Review Status",
            evidence_fusion.get(
                "review_status",
                "N/A"
            )
        ),
    ]

    story.append(
        create_two_column_table(
            fusion_rows
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    combined_assessment = evidence_fusion.get(
        "combined_assessment"
    )

    if combined_assessment:
        story.append(
            info_box(
                "Combined Assessment",
                str(combined_assessment),
                "#F8FAFC"
            )
        )

    fusion_warning = evidence_fusion.get(
        "warning"
    )

    if fusion_warning:
        story.append(
            Spacer(1, 2 * mm)
        )

        story.append(
            info_box(
                "Forensic Caution",
                str(fusion_warning),
                "#FFF8E7"
            )
        )

    # =====================================================
    # 8. SUSPICIOUS REGION LOCALIZATION
    # =====================================================

    story.append(
        section_heading(
            8,
            "Suspicious Region Localization"
        )
    )

    localization_rows = [
        (
            "Status",
            localization.get(
                "status",
                "N/A"
            )
        ),
        (
            "Method",
            localization.get(
                "method",
                "ELA-derived high-difference region analysis"
            )
        ),
        (
            "Threshold",
            localization.get(
                "threshold",
                "N/A"
            )
        ),
        (
            "Candidate Regions",
            localization.get(
                "candidate_regions",
                "N/A"
            )
        ),
        (
            "Rejected Large Regions",
            localization.get(
                "rejected_large_regions",
                "N/A"
            )
        ),
        (
            "Mean Difference",
            fmt_number(
                localization.get(
                    "mean_difference"
                )
            )
        ),
        (
            "Maximum Difference",
            fmt_number(
                localization.get(
                    "maximum_difference"
                )
            )
        ),
        (
            "Difference Standard Deviation",
            fmt_number(
                localization.get(
                    "difference_std"
                )
            )
        ),
    ]

    story.append(
        create_two_column_table(
            localization_rows
        )
    )

    story.append(
        Spacer(1, 3 * mm)
    )

    if localization_image_path:
        story.append(
            Paragraph(
                "Localization Visualization",
                styles["SubHeading"]
            )
        )

        add_image(
            story,
            localization_image_path,
            CONTENT_WIDTH,
            72 * mm,
            "ELA-derived candidate suspicious regions"
        )

    regions = localization.get(
        "regions",
        []
    )

    if isinstance(regions, list) and regions:

        story.append(
            Paragraph(
                "Candidate Region Details",
                styles["SubHeading"]
            )
        )

        region_rows = []

        for index, region in enumerate(
            regions,
            start=1
        ):

            region_rows.append(
                [
                    index,
                    region.get("x", "N/A"),
                    region.get("y", "N/A"),
                    region.get("width", "N/A"),
                    region.get("height", "N/A"),
                    fmt_number(
                        region.get("area"),
                        1
                    ),
                ]
            )

        story.append(
            create_data_table(
                [
                    "Region",
                    "X",
                    "Y",
                    "Width",
                    "Height",
                    "Area"
                ],
                region_rows,
                [
                    CONTENT_WIDTH * 0.12,
                    CONTENT_WIDTH * 0.13,
                    CONTENT_WIDTH * 0.13,
                    CONTENT_WIDTH * 0.18,
                    CONTENT_WIDTH * 0.18,
                    CONTENT_WIDTH * 0.26,
                ]
            )
        )

    localization_warning = localization.get(
        "warning"
    )

    if localization_warning:
        story.append(
            Spacer(1, 3 * mm)
        )

        story.append(
            info_box(
                "Localization Interpretation",
                str(localization_warning),
                "#FFF8E7"
            )
        )

    # =====================================================
    # 9. DATABASE RECORD
    # =====================================================

    story.append(
        section_heading(
            9,
            "Evidence Record"
        )
    )

    database_rows = [
        (
            "Database Status",
            database.get(
                "status",
                "N/A"
            )
        ),
        (
            "Evidence ID",
            database.get(
                "evidence_id",
                "N/A"
            )
        ),
        (
            "Database Operation",
            database.get(
                "operation",
                "N/A"
            )
        ),
    ]

    story.append(
        create_two_column_table(
            database_rows
        )
    )

    # =====================================================
    # 10. PRELIMINARY CONCLUSION
    # =====================================================

    story.append(
        section_heading(
            10,
            "Preliminary Conclusion"
        )
    )

    prediction = safe(
        ai_detection.get(
            "prediction",
            "N/A"
        )
    )

    consistency_level = safe(
        assessment.get(
            "level",
            "N/A"
        )
    )

    conclusion_text = (
        f"The current AIDE analysis produced an AI model "
        f"indication of <b>{prediction}</b>. The traditional "
        f"forensic indicators produced a prototype consistency "
        f"assessment of <b>{consistency_level}</b> with a "
        f"consistency score of <b>{safe(consistency_score)}</b>. "
        f"These outputs should be interpreted together with the "
        f"ELA visualization, image statistics, metadata findings "
        f"and suspicious-region candidates."
    )

    story.append(
        info_box(
            "Analysis Summary",
            conclusion_text,
            "#F8FAFC"
        )
    )

    # =====================================================
    # 11. LIMITATIONS
    # =====================================================

    story.append(
        section_heading(
            11,
            "Limitations and Forensic Disclaimer"
        )
    )

    limitations = [
        "The AI output is a model-based forensic indication.",
        "The prototype forensic consistency index is not a validated probability of authenticity or tampering.",
        "ELA is primarily applicable to JPEG compression analysis and is a supporting forensic technique.",
        "Suspicious-region localization identifies candidate regions requiring further examination; it does not prove manipulation.",
        "The current AI model should not be treated as production-ready forensic evidence.",
        "The report does not constitute a legal conclusion or definitive forensic determination.",
        "A qualified forensic examiner should review the original evidence and all supporting results before drawing conclusions.",
    ]

    for item in limitations:

        story.append(
            Paragraph(
                f"• {item}",
                styles["BodyCompact"]
            )
        )

    story.append(
        Spacer(1, 2 * mm)
    )

    story.append(
        info_box(
            "Final Forensic Notice",
            "This document is generated automatically by the AIDE "
            "prototype platform. Its results are intended for "
            "academic demonstration, research and forensic "
            "decision-support purposes. Independent expert "
            "verification is required before any evidentiary, "
            "legal or investigative conclusion is made.",
            "#FFF8E7"
        )
    )

    # =====================================================
    # BUILD PDF
    # =====================================================

    doc.build(
        story,
        onFirstPage=draw_header_footer,
        onLaterPages=draw_header_footer
    )

    return report_path