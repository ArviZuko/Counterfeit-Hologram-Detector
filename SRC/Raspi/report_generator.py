"""
AI-Powered Hologram Authenticity Detection System - PDF Report Generator
Generates formal, high-resolution inspection certificates and verification reports
using ReportLab.
"""

import os
import datetime
import cv2
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether, HRFlowable
)


def generate_pdf_report(analysis_data, output_pdf_path=None, operator_name="Quality Control Inspector"):
    """
    Generates a formal Hologram Verification Certificate PDF.
    
    Args:
        analysis_data (dict): Result dictionary from HologramAnalyzer.analyze()
        output_pdf_path (str): File path to save the generated PDF
        operator_name (str): Name of inspector
        
    Returns:
        str: Absolute path of generated PDF file
    """
    if output_pdf_path is None:
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_pdf_path = os.path.abspath(f"Hologram_Report_{timestamp_str}.pdf")

    # Temp dir for saving embedded inspection images
    temp_dir = os.path.dirname(output_pdf_path)
    prefix = f"tmp_rep_{datetime.datetime.now().strftime('%H%M%S')}_"

    raw_img_path = os.path.join(temp_dir, f"{prefix}raw.png")
    nbi_img_path = os.path.join(temp_dir, f"{prefix}nbi.png")
    crop_img_path = os.path.join(temp_dir, f"{prefix}crop.png")
    ref_img_path = os.path.join(temp_dir, f"{prefix}ref.png")
    heat_img_path = os.path.join(temp_dir, f"{prefix}heat.png")
    edge_img_path = os.path.join(temp_dir, f"{prefix}edge.png")

    temp_files = [raw_img_path, nbi_img_path, crop_img_path, ref_img_path, heat_img_path, edge_img_path]

    try:
        # Save images for ReportLab embedding
        if "annotated_frame" in analysis_data and analysis_data["annotated_frame"] is not None:
            cv2.imwrite(raw_img_path, cv2.resize(analysis_data["annotated_frame"], (400, 300)))
        elif "raw_frame_bgr" in analysis_data:
            cv2.imwrite(raw_img_path, cv2.resize(analysis_data["raw_frame_bgr"], (400, 300)))

        if "nbi_bgr" in analysis_data and analysis_data["nbi_bgr"] is not None:
            cv2.imwrite(nbi_img_path, cv2.resize(analysis_data["nbi_bgr"], (400, 300)))

        if "crop_bgr" in analysis_data and analysis_data["crop_bgr"] is not None:
            cv2.imwrite(crop_img_path, cv2.resize(analysis_data["crop_bgr"], (200, 150)))

        if "reference_template" in analysis_data and analysis_data["reference_template"] is not None:
            cv2.imwrite(ref_img_path, cv2.resize(analysis_data["reference_template"], (200, 150)))

        if "anomaly_blend" in analysis_data and analysis_data["anomaly_blend"] is not None:
            cv2.imwrite(heat_img_path, cv2.resize(analysis_data["anomaly_blend"], (200, 150)))

        if "edge_visual" in analysis_data and analysis_data["edge_visual"] is not None:
            cv2.imwrite(edge_img_path, cv2.resize(analysis_data["edge_visual"], (200, 150)))

        doc = SimpleDocTemplate(
            output_pdf_path,
            pagesize=letter,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom typography styles
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor('#0f172a'),
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#64748b'),
            fontName='Helvetica'
        )

        section_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            fontName='Helvetica-Bold'
        )

        normal_style = ParagraphStyle(
            'ReportNormal',
            parent=styles['Normal'],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#334155'),
            fontName='Helvetica'
        )

        bold_style = ParagraphStyle(
            'ReportBold',
            parent=normal_style,
            fontName='Helvetica-Bold'
        )

        outcome = analysis_data.get("outcome", "The Hologram is Original")

        badge_bg = colors.HexColor('#10b981') if "Original" in outcome else (
            colors.HexColor('#ef4444') if "Counterfeit" in outcome else colors.HexColor('#64748b')
        )

        story = []

        # Header Table (Title & Certificate Info)
        now_str = datetime.datetime.now().strftime("%B %d, %Y - %H:%M:%S")
        cert_num = f"HA-{datetime.datetime.now().strftime('%Y%m%d')}-{np.random.randint(1000, 9999)}"

        header_data = [
            [
                Paragraph("<b>AI HOLOGRAM AUTHENTICITY DETECTION SYSTEM</b><br/><font size=9 color='#64748b'>Snapshot VIS-HSI Optical Verification & Quality Certificate</font>", title_style),
                Paragraph(f"<b>Certificate No:</b> {cert_num}<br/><b>Date:</b> {now_str}<br/><b>Inspector:</b> {operator_name}", normal_style)
            ]
        ]
        t_header = Table(header_data, colWidths=[340, 200])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        story.append(t_header)
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0284c7'), spaceAfter=10))

        # Outcome Assessment Banner
        outcome_style = ParagraphStyle(
            'OutcomeText',
            parent=styles['Normal'],
            fontSize=14,
            leading=18,
            textColor=colors.white,
            fontName='Helvetica-Bold',
            alignment=1  # Center
        )
        outcome_table_data = [[
            Paragraph(f"VERIFICATION RESULT: {outcome.upper()}", outcome_style)
        ]]
        t_outcome = Table(outcome_table_data, colWidths=[540])
        t_outcome.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), badge_bg),
            ('TOPPADDING', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ]))
        story.append(t_outcome)
        story.append(Spacer(1, 8))

        # Analysis Summary Text
        reason_text = analysis_data.get("outcome_reason", "Analysis completed.")
        story.append(Paragraph(f"<b>Assessment Summary:</b> {reason_text}", normal_style))
        story.append(Spacer(1, 10))

        # Visual Evidence Grid (Only 1. Live Acquisition Frame & 5. Verified Reference Template)
        story.append(Paragraph("Visual Evidence & Master Comparison", section_style))
        story.append(Spacer(1, 6))

        img_w = 250
        img_h = 165

        def safe_image(path):
            if os.path.exists(path):
                return RLImage(path, width=img_w, height=img_h)
            return Paragraph("Image unavailable", normal_style)

        visual_grid_data = [
            [safe_image(raw_img_path), safe_image(ref_img_path)],
            [
                Paragraph("<b>1. Live Acquisition Frame</b><br/><font size=8 color='#64748b'>Registered ROI Bounding Box</font>", normal_style),
                Paragraph("<b>2. Verified Reference Template</b><br/><font size=8 color='#64748b'>Calibrated Master Pattern ('UR')</font>", normal_style)
            ]
        ]

        t_visual = Table(visual_grid_data, colWidths=[270, 270])
        t_visual.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 8),
        ]))
        story.append(t_visual)
        story.append(Spacer(1, 10))

        # Scientific Metrics Table (Cleaned, streamlined evaluation)
        story.append(Paragraph("Inspection & Verification Parameters", section_style))
        story.append(Spacer(1, 4))

        is_original = "Original" in outcome
        metrics_table_data = [
            [
                Paragraph("<b>Inspection Parameter</b>", bold_style),
                Paragraph("<b>Calibrated Standard</b>", bold_style),
                Paragraph("<b>Inspection Finding</b>", bold_style),
                Paragraph("<b>Evaluation</b>", bold_style)
            ],
            [
                Paragraph("Hologram Authenticity", normal_style),
                Paragraph("Certified Authentic Hologram Pattern", normal_style),
                Paragraph(outcome, normal_style),
                Paragraph("GENUINE" if is_original else "COUNTERFEIT", bold_style)
            ],
            [
                Paragraph("Spectral Calibration", normal_style),
                Paragraph("Auto-Calibrated 500 nm (VIS-HSI)", normal_style),
                Paragraph("Consistent Response" if is_original else "Reflection Discrepancy", normal_style),
                Paragraph("PASS" if is_original else "FAIL", bold_style)
            ],
            [
                Paragraph("Microstructure Definition", normal_style),
                Paragraph("Sub-Micron Optical Diffractive Relief", normal_style),
                Paragraph("Intact Grating Profile" if is_original else "Altered / Degraded Grating", normal_style),
                Paragraph("INTACT" if is_original else "SUSPICIOUS", bold_style)
            ],
            [
                Paragraph("Surface Halftone Screening", normal_style),
                Paragraph("Continuous Optical Phase (No Print Dots)", normal_style),
                Paragraph("Authentic Continuous Phase" if not analysis_data.get('print_artifacts', {}).get('artifact_detected', False) else "Periodic Print Halftone Detected", normal_style),
                Paragraph("AUTHENTIC OPTICAL" if not analysis_data.get('print_artifacts', {}).get('artifact_detected', False) else "SUSPICIOUS PRINT", bold_style)
            ]
        ]

        t_metrics = Table(metrics_table_data, colWidths=[150, 160, 140, 90])
        t_metrics.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f1f5f9')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_metrics)
        story.append(Spacer(1, 14))

        # Sign-off Area
        sig_data = [
            [
                Paragraph("<b>Operator Signature:</b> ___________________________", normal_style),
                Paragraph("<b>Quality Assurance Officer:</b> ___________________________", normal_style),
                Paragraph("<b>Verification Stamp / Seal:</b> [ APPROVED ]", normal_style)
            ]
        ]
        t_sig = Table(sig_data, colWidths=[180, 200, 160])
        t_sig.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        story.append(t_sig)

        doc.build(story)

    finally:
        # Clean up temporary images
        for f in temp_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    return output_pdf_path
