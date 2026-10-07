from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
)


def _safe_text(value, default="—"):
    """
    Safely convert a value into report-friendly text.
    """

    if value is None:
        return default

    if isinstance(value, str):
        return value

    return str(value)


def _create_table(
    data,
    col_widths,
):
    """
    Create a consistent AIDE report table.
    """

    table = Table(
        data,
        colWidths=col_widths,
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
                    colors.HexColor("#202020"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white,
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, -1),
                    "Helvetica",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#B0B0B0"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
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

    return table


def build_manipulation_report_section(
    manipulation_analysis,
    section_heading_style=None,
    body_style=None,
    warning_style=None,
):
    """
    Build the Manipulation-Type Indication section
    for the AIDE forensic PDF.

    Parameters
    ----------
    manipulation_analysis : dict
        Output from classify_manipulation_type()

    section_heading_style :
        Existing ReportLab heading style from report_generator.py.

    body_style :
        Existing ReportLab body style.

    warning_style :
        Existing ReportLab warning style.

    Returns
    -------
    list
        ReportLab flowables.
    """

    elements = []

    if not manipulation_analysis:
        return elements

    if section_heading_style is None:

        section_heading_style = ParagraphStyle(
            "ManipulationSectionHeading",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            spaceBefore=12,
            spaceAfter=8,
            textColor=colors.HexColor("#202020"),
        )

    if body_style is None:

        body_style = ParagraphStyle(
            "ManipulationBody",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            spaceAfter=5,
            textColor=colors.HexColor("#303030"),
        )

    if warning_style is None:

        warning_style = ParagraphStyle(
            "ManipulationWarning",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            spaceBefore=4,
            spaceAfter=4,
            leftIndent=6,
            rightIndent=6,
            textColor=colors.HexColor("#444444"),
            backColor=colors.HexColor("#F2F2F2"),
            borderColor=colors.HexColor("#BBBBBB"),
            borderWidth=0.5,
            borderPadding=6,
        )

    # =====================================================
    # SECTION HEADING
    # =====================================================

    elements.append(
        Paragraph(
            "Manipulation-Type Indication",
            section_heading_style,
        )
    )

    elements.append(
        Spacer(
            1,
            4,
        )
    )

    # =====================================================
    # PRIMARY INDICATION
    # =====================================================

    primary_indication = _safe_text(
        manipulation_analysis.get(
            "primary_indication"
        ),
        "Not Available",
    )

    primary_score = _safe_text(
        manipulation_analysis.get(
            "primary_score"
        ),
        "—",
    )

    elements.append(
        Paragraph(
            f"<b>Primary Indication:</b> "
            f"{primary_indication}",
            body_style,
        )
    )

    elements.append(
        Paragraph(
            f"<b>Primary Indication Score:</b> "
            f"{primary_score}",
            body_style,
        )
    )

    # =====================================================
    # INDICATION SCORES
    # =====================================================

    scores = manipulation_analysis.get(
        "scores",
        {},
    )

    if scores:

        elements.append(
            Spacer(
                1,
                6,
            )
        )

        table_data = [
            [
                "Forensic Indicator",
                "Score",
            ]
        ]

        preferred_order = [
            "Object-Removal Indication",
            "Splicing Indication",
            "Copy-Move Indication",
            "Compression Inconsistency",
        ]

        used = set()

        for name in preferred_order:

            if name in scores:

                table_data.append(
                    [
                        name,
                        _safe_text(
                            scores.get(name)
                        ),
                    ]
                )

                used.add(name)

        # Add any additional indicators
        # without losing them.

        for name, score in scores.items():

            if name not in used:

                table_data.append(
                    [
                        _safe_text(name),
                        _safe_text(score),
                    ]
                )

        score_table = _create_table(
            table_data,
            [
                330,
                100,
            ],
        )

        elements.append(
            score_table
        )

    # =====================================================
    # COPY-MOVE ANALYSIS
    # =====================================================

    copy_move = manipulation_analysis.get(
        "copy_move_analysis",
        {},
    )

    if copy_move:

        elements.append(
            Spacer(
                1,
                8,
            )
        )

        elements.append(
            Paragraph(
                "<b>Copy-Move Analysis</b>",
                body_style,
            )
        )

        copy_move_data = [
            [
                "Measurement",
                "Value",
            ],
            [
                "Keypoints Examined",
                _safe_text(
                    copy_move.get(
                        "keypoints"
                    )
                ),
            ],
            [
                "Matched Pairs",
                _safe_text(
                    copy_move.get(
                        "matched_pairs"
                    )
                ),
            ],
            [
                "Copy-Move Score",
                _safe_text(
                    copy_move.get(
                        "score"
                    )
                ),
            ],
        ]

        copy_move_table = _create_table(
            copy_move_data,
            [
                330,
                100,
            ],
        )

        elements.append(
            copy_move_table
        )

    # =====================================================
    # COPY-MOVE MESSAGE
    # =====================================================

    copy_move_message = copy_move.get(
        "message"
    )

    if copy_move_message:

        elements.append(
            Spacer(
                1,
                5,
            )
        )

        elements.append(
            Paragraph(
                _safe_text(
                    copy_move_message
                ),
                body_style,
            )
        )

    # =====================================================
    # WARNING / INTERPRETATION
    # =====================================================

    warning = manipulation_analysis.get(
        "warning"
    )

    if warning:

        elements.append(
            Spacer(
                1,
                8,
            )
        )

        elements.append(
            Paragraph(
                "<b>Interpretation:</b> "
                + _safe_text(warning),
                warning_style,
            )
        )

    # =====================================================
    # ANALYSIS TYPE
    # =====================================================

    analysis_type = manipulation_analysis.get(
        "analysis_type"
    )

    if analysis_type:

        elements.append(
            Spacer(
                1,
                5,
            )
        )

        elements.append(
            Paragraph(
                "<b>Analysis Method:</b> "
                + _safe_text(
                    analysis_type
                ),
                body_style,
            )
        )

    return elements