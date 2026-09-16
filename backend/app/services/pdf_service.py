"""
Professional PDF Generation Service for Sales AI Business Proposals.

Generates an enterprise-grade, multi-page business proposal PDF formatted
specifically for client sharing, with client email header and bottom recipient block.
"""

import io
import re
import xml.sax.saxutils
from datetime import datetime
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and display running headers,
    running footers, and accurate total page counts ("Page X of Y").
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))

        company_name = getattr(self, "doc_company_name", "Enterprise Client")
        ref_id = getattr(self, "doc_ref_id", "PROPOSAL")
        recipient_email = getattr(self, "doc_recipient_email", "")

        # Running header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(
                45,
                11 * 72 - 32,
                f"Business Proposal  |  {company_name}",
            )
            self.drawRightString(
                8.5 * 72 - 45,
                11 * 72 - 32,
                "Confidential",
            )
            self.setStrokeColor(colors.HexColor("#e2e8f0"))
            self.setLineWidth(0.5)
            self.line(45, 11 * 72 - 36, 8.5 * 72 - 45, 11 * 72 - 36)

        # Running footer (all pages)
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(45, 38, 8.5 * 72 - 45, 38)

        # Left footer: Reference
        footer_left = f"Ref: {ref_id}"
        if recipient_email:
            footer_left += f"  |  Recipient: {recipient_email}"
        self.drawString(45, 26, footer_left)

        # Center footer: Page X of Y
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * 72 - 45, 26, page_str)

        self.restoreState()


def _escape(text: Any) -> str:
    """Safely escape text for ReportLab Paragraph XML parser."""
    if text is None:
        return ""
    s = str(text)
    return xml.sax.saxutils.escape(s)


def _clean_markdown_to_plain(text: str) -> str:
    """Strip complex markdown formatting to readable text."""
    if not text:
        return ""
    # Strip markdown headers, bold, italics, code
    t = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)
    t = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\*(.*?)\*", r"<i>\1</i>", t)
    t = re.sub(r"`(.*?)`", r"\1", t)
    return t.strip()


def sanitize_pdf_filename(company_name: str, date_str: Optional[str] = None) -> str:
    """Generate a clean, sanitized PDF filename."""
    clean_company = re.sub(r"[^a-zA-Z0-9_\-]", "_", company_name or "Client")
    clean_company = re.sub(r"_+", "_", clean_company).strip("_")
    if not clean_company:
        clean_company = "Client"
    if not date_str:
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
    return f"Proposal_{clean_company}_{date_str}.pdf"


def build_proposal_pdf_bytes(
    lead: Any,
    proposal_data: Dict[str, Any],
    client_email: Optional[str] = None,
    reviewer_data: Optional[Dict[str, Any]] = None,
) -> bytes:
    """
    Generate a professional business proposal PDF.

    Includes:
    - Top header: BUSINESS PROPOSAL, Prepared For, Recipient Email, Date
    - Full proposal sections (Executive Summary, Requirements, Solution, Roadmap, Pricing, SLA, Next Actions, etc.)
    - Bottom block: Proposal Recipient email & instructions
    """
    buffer = io.BytesIO()

    # Document setup: standard letter with 45pt (0.62 in) margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=48,
        bottomMargin=48,
    )

    company = getattr(lead, "company_name", None) or "Valued Client"
    recipient = (
        client_email
        or getattr(lead, "email", None)
        or f"contact@{re.sub(r'[^a-zA-Z0-9]', '', company).lower() or 'enterprise'}.com"
    )
    current_date = datetime.utcnow().strftime("%B %d, %Y")
    lead_id = str(getattr(lead, "id", "PROPOSAL-01"))
    ref_code = lead_id[:8].upper()

    # Define color scheme
    c_primary = colors.HexColor("#1e293b")   # Slate 800 (Dark Corporate)
    c_secondary = colors.HexColor("#334155") # Slate 700
    c_accent = colors.HexColor("#2563eb")    # Royal Blue
    c_bg_light = colors.HexColor("#f8fafc")  # Off white slate
    c_border = colors.HexColor("#cbd5e1")    # Slate 300
    c_text = colors.HexColor("#0f172a")      # Slate 900

    styles = getSampleStyleSheet()

    # Custom typography styles
    style_main_title = ParagraphStyle(
        "ProposalMainTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=c_primary,
        spaceAfter=14,
        alignment=TA_LEFT,
    )

    style_meta_label = ParagraphStyle(
        "MetaLabel",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#475569"),
    )

    style_meta_val = ParagraphStyle(
        "MetaValue",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=c_text,
    )

    style_meta_val_bold = ParagraphStyle(
        "MetaValueBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=c_accent,
    )

    style_h1 = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=c_primary,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True,
    )

    style_body = ParagraphStyle(
        "ProposalBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14.5,
        textColor=c_text,
        alignment=TA_LEFT,
        spaceAfter=8,
    )

    style_bullet = ParagraphStyle(
        "ProposalBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=c_secondary,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=c_text,
    )

    style_table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=12,
        textColor=c_primary,
    )

    style_callout_title = ParagraphStyle(
        "CalloutTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=c_primary,
        spaceAfter=3,
    )

    style_callout_body = ParagraphStyle(
        "CalloutBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
    )

    story: List[Any] = []

    # =========================================================================
    # 1. TOP HEADER (Exact User Specification)
    # =========================================================================
    story.append(Paragraph("BUSINESS PROPOSAL", style_main_title))
    story.append(Spacer(1, 4))

    # Meta information box
    header_table_data = [
        [
            Paragraph("Prepared For:", style_meta_label),
            Paragraph(f"<b>{_escape(company)}</b>", style_meta_val),
            Paragraph("Date:", style_meta_label),
            Paragraph(_escape(current_date), style_meta_val),
        ],
        [
            Paragraph("Recipient Email:", style_meta_label),
            Paragraph(f"<b>{_escape(recipient)}</b>", style_meta_val_bold),
            Paragraph("Proposal Ref:", style_meta_label),
            Paragraph(_escape(ref_code), style_meta_val),
        ],
    ]

    header_table = Table(
        header_table_data,
        colWidths=[1.3 * inch, 2.7 * inch, 1.1 * inch, 1.8 * inch],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), c_bg_light),
                ("BOX", (0, 0), (-1, -1), 1, c_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    story.append(header_table)
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1, color=c_border, spaceBefore=0, spaceAfter=14))

    # =========================================================================
    # 2. EXECUTIVE SUMMARY
    # =========================================================================
    story.append(Paragraph("1. Executive Summary", style_h1))
    exec_summary = proposal_data.get("executive_summary") or (
        f"This strategic business proposal has been specifically customized for {company} "
        "to deliver an end-to-end, automated enterprise solution that drives operational "
        "efficiency, reduces processing overhead, and accelerates high-value outcomes."
    )
    story.append(Paragraph(_clean_markdown_to_plain(_escape(exec_summary)), style_body))
    story.append(Spacer(1, 6))

    # =========================================================================
    # 3. REQUIREMENTS & OBJECTIVES
    # =========================================================================
    reqs = proposal_data.get("customer_requirements") or proposal_data.get("requirements") or []
    if reqs:
        story.append(Paragraph("2. Customer Requirements & Scope", style_h1))
        for r in reqs:
            clean_r = _clean_markdown_to_plain(_escape(r))
            story.append(Paragraph(f"• &nbsp; {clean_r}", style_bullet))
        story.append(Spacer(1, 6))

    # =========================================================================
    # 4. PROPOSED SOLUTION & ARCHITECTURE
    # =========================================================================
    proposed_sol = proposal_data.get("proposed_solution") or proposal_data.get("technical_approach") or ""
    if proposed_sol:
        story.append(Paragraph("3. Proposed Solution Architecture", style_h1))
        # Split into readable paragraphs
        paragraphs = proposed_sol.split("\n\n")
        for p_text in paragraphs:
            if p_text.strip():
                clean_p = _clean_markdown_to_plain(_escape(p_text))
                story.append(Paragraph(clean_p, style_body))
        story.append(Spacer(1, 6))

    # Matched Products / Catalog groundings
    products = proposal_data.get("matched_products") or []
    if products:
        story.append(Paragraph("Matched Solution Components", style_callout_title))
        for prod in products:
            if isinstance(prod, dict):
                p_name = prod.get("name") or prod.get("product_name") or "Component"
                p_desc = prod.get("description") or prod.get("fit_reason") or ""
                story.append(Paragraph(f"• &nbsp; <b>{_escape(p_name)}:</b> {_escape(p_desc)}", style_bullet))
            elif isinstance(prod, str):
                story.append(Paragraph(f"• &nbsp; {_escape(prod)}", style_bullet))
        story.append(Spacer(1, 8))

    # =========================================================================
    # 5. IMPLEMENTATION ROADMAP & TIMELINE
    # =========================================================================
    roadmap = proposal_data.get("implementation_roadmap") or []
    total_timeline = proposal_data.get("total_implementation_timeline") or "2-4 Weeks"

    story.append(Paragraph("4. Implementation Plan & Timeline", style_h1))
    story.append(Paragraph(f"<b>Estimated Timeline to Full Deployment:</b> {_escape(total_timeline)}", style_body))

    if roadmap and isinstance(roadmap, list):
        table_rows = [
            [
                Paragraph("Phase", style_table_header),
                Paragraph("Duration", style_table_header),
                Paragraph("Key Deliverables & Activities", style_table_header),
            ]
        ]
        for item in roadmap:
            if isinstance(item, dict):
                phase = item.get("phase", "Phase")
                duration = item.get("duration", "TBD")
                acts = item.get("activities", [])
                if isinstance(acts, list):
                    acts_text = ", ".join(acts)
                else:
                    acts_text = str(acts)
                table_rows.append(
                    [
                        Paragraph(_escape(phase), style_table_cell_bold),
                        Paragraph(_escape(duration), style_table_cell),
                        Paragraph(_escape(acts_text), style_table_cell),
                    ]
                )
        if len(table_rows) > 1:
            roadmap_table = Table(table_rows, colWidths=[1.6 * inch, 1.3 * inch, 4.0 * inch])
            roadmap_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("TOPPADDING", (0, 0), (-1, -1), 5),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                        ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                    ]
                )
            )
            story.append(roadmap_table)
            story.append(Spacer(1, 10))

    # =========================================================================
    # 6. COMMERCIAL & PRICING MODEL
    # =========================================================================
    pricing = proposal_data.get("pricing_proposal") or proposal_data.get("pricing") or {}
    story.append(Paragraph("5. Commercial Terms & Investment Model", style_h1))

    if isinstance(pricing, dict) and pricing:
        price_rows = [
            [
                Paragraph("Commercial Component", style_table_header),
                Paragraph("Investment / Estimated Tier", style_table_header),
            ]
        ]
        for k, v in pricing.items():
            label = k.replace("_", " ").title()
            price_rows.append(
                [
                    Paragraph(_escape(label), style_table_cell_bold),
                    Paragraph(_escape(str(v)), style_table_cell),
                ]
            )
        price_table = Table(price_rows, colWidths=[3.5 * inch, 3.4 * inch])
        price_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), c_primary),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, c_bg_light]),
                    ("GRID", (0, 0), (-1, -1), 0.5, c_border),
                ]
            )
        )
        story.append(price_table)
        story.append(Spacer(1, 10))
    elif isinstance(pricing, str) and pricing.strip():
        story.append(Paragraph(_escape(pricing), style_body))
        story.append(Spacer(1, 8))

    # =========================================================================
    # 7. BUSINESS BENEFITS & SUPPORT SLA
    # =========================================================================
    benefits = proposal_data.get("business_benefits") or proposal_data.get("benefits") or []
    if benefits:
        story.append(Paragraph("6. Key Business Benefits & Value Proposition", style_h1))
        for b in benefits:
            story.append(Paragraph(f"✓ &nbsp; {_escape(b)}", style_bullet))
        story.append(Spacer(1, 8))

    sla = proposal_data.get("support_service_levels") or {}
    if isinstance(sla, dict) and sla:
        story.append(Paragraph("7. Support & Service Level Agreement (SLA)", style_h1))
        for k, v in sla.items():
            label = k.replace("_", " ").title()
            story.append(Paragraph(f"• &nbsp; <b>{_escape(label)}:</b> {_escape(str(v))}", style_bullet))
        story.append(Spacer(1, 8))

    # =========================================================================
    # 8. QA REVIEW & RECOMMENDED NEXT ACTIONS (When Available)
    # =========================================================================
    rev_data = reviewer_data or getattr(lead, "reviewer_result", None) or proposal_data.get("reviewer_result")
    next_steps = []
    if isinstance(rev_data, dict):
        next_steps = rev_data.get("recommended_next_steps") or rev_data.get("next_steps") or []
    if not next_steps:
        next_steps = proposal_data.get("recommended_next_steps") or proposal_data.get("next_steps") or []

    if next_steps and isinstance(next_steps, list):
        story.append(Paragraph("8. Recommended Next Actions & Next Steps", style_h1))
        for step in next_steps:
            clean_step = _clean_markdown_to_plain(_escape(str(step)))
            story.append(Paragraph(f"• &nbsp; {clean_step}", style_bullet))
        story.append(Spacer(1, 8))

    # Optional QA verification highlights if present
    if isinstance(rev_data, dict):
        claim_vers = rev_data.get("claim_verification")
        if claim_vers and isinstance(claim_vers, list):
            story.append(Paragraph("Quality Assurance & Catalog Grounding", style_callout_title))
            for cv in claim_vers[:4]:
                if isinstance(cv, dict):
                    claim_text = cv.get("claim", "")
                    src = cv.get("source", "Knowledge Base")
                else:
                    claim_text = str(cv)
                    src = "Knowledge Base"
                story.append(Paragraph(f"✓ &nbsp; <b>Verified:</b> {_escape(claim_text)} ({_escape(src)})", style_bullet))
            story.append(Spacer(1, 8))

    # =========================================================================
    # 9. TERMS & CONDITIONS
    # =========================================================================
    story.append(Paragraph("9. Terms, Conditions & Engagement Authorization", style_h1))
    terms_text = (
        "1. This proposal remains valid for 30 days from the date of issuance.<br/>"
        "2. Deployment schedule commences upon joint milestone sign-off and environment readiness.<br/>"
        "3. Standard enterprise SLA and security guarantees apply to all provisioned infrastructure."
    )
    story.append(Paragraph(terms_text, style_body))
    story.append(Spacer(1, 12))

    # =========================================================================
    # 9. BOTTOM RECIPIENT BLOCK (Exact User Specification)
    # =========================================================================
    bottom_block_data = [
        [
            Paragraph("<b>Proposal Recipient:</b>", style_callout_title),
        ],
        [
            Paragraph(f"<b>{_escape(recipient)}</b>", style_meta_val_bold),
        ],
        [
            Paragraph(
                "Please send this proposal PDF to the recipient email address above.",
                style_callout_body,
            ),
        ],
    ]
    bottom_block = Table(bottom_block_data, colWidths=[6.9 * inch])
    bottom_block.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )

    story.append(KeepTogether([bottom_block]))

    # Canvas helper
    class ConfiguredCanvas(NumberedCanvas):
        pass

    ConfiguredCanvas.doc_company_name = company
    ConfiguredCanvas.doc_ref_id = ref_code
    ConfiguredCanvas.doc_recipient_email = recipient

    doc.build(story, canvasmaker=ConfiguredCanvas)
    return buffer.getvalue()
