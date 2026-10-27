from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_verification_pdf(*, claim, verification, observations) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=.7*inch, rightMargin=.7*inch, topMargin=.65*inch)
    styles = getSampleStyleSheet()
    story = [Paragraph("AgriVerify", styles["Title"]), Paragraph("Verification Report", styles["Heading2"]), Spacer(1, 12)]
    estimated = verification.estimated_planting_date.isoformat() if verification.estimated_planting_date else "Not supported by available observations"
    window = f"{verification.estimated_window_start or '—'} to {verification.estimated_window_end or '—'}"
    rows = [
        ["Report ID", verification.id], ["Claim ID", claim.id], ["Field", claim.field_id], ["Crop", claim.field.crop_type],
        ["Reported planting date", claim.reported_planting_date.isoformat()], ["Satellite-derived estimate", estimated],
        ["Estimated planting window", window], ["Discrepancy", f"{verification.discrepancy_days} days" if verification.discrepancy_days is not None else "Not calculated"],
        ["Evidence quality", verification.evidence_quality], ["Verification status", verification.status],
        ["Estimator / policy", f"{verification.estimator_version} / {verification.policy_version}"],
        ["Data provenance", "Synthetic offline demonstration observations" if any(o.is_demo_data for o in observations) else "Earth Engine Sentinel-2 surface reflectance"],
        ["Human reviewer notes", claim.reviewer_notes or "None recorded"], ["Generated", verification.generated_at.isoformat()],
    ]
    table = Table(rows, colWidths=[1.8*inch, 5.1*inch])
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eaf6ef")), ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#102b25")), ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#bcd8cb")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("PADDING", (0, 0), (-1, -1), 7)]))
    story += [table, Spacer(1, 14), Paragraph("Evidence summary", styles["Heading3"]), Paragraph(verification.evidence_summary, styles["BodyText"]), Spacer(1, 10), Paragraph("Limitations", styles["Heading3"]), Paragraph(" ".join(verification.limitations), styles["BodyText"]), Spacer(1, 12), Paragraph("Disclaimer: satellite-based planting-date estimation is probabilistic. It supports, but does not replace, qualified human insurance review. This report does not approve, deny, or determine insurance coverage.", styles["BodyText"])]
    document.build(story)
    return buffer.getvalue()

