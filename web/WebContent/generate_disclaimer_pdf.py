#!/usr/bin/env python3
"""
Generate a PDF disclaimer document suitable for YouTube display.
"""

try:
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    from reportlab.lib.colors import HexColor, black, red
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("ReportLab not available. Install with: pip install reportlab")

def create_disclaimer_pdf(output_filename="Trading_Disclaimer.pdf", use_landscape=False):
    """Create a professional PDF disclaimer document.
    
    Args:
        output_filename: Name of the output PDF file
        use_landscape: If True, creates landscape format (better for YouTube display)
    """
    
    if not REPORTLAB_AVAILABLE:
        print("Please install reportlab: pip install reportlab")
        return
    
    # Choose page size
    pagesize = landscape(letter) if use_landscape else letter
    
    # Create PDF document (reduced margins to fit on one page)
    # Even smaller margins for landscape (more horizontal space)
    if use_landscape:
        margin = 0.4*inch
    else:
        margin = 0.5*inch
    
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=pagesize,
        rightMargin=margin,
        leftMargin=margin,
        topMargin=margin,
        bottomMargin=margin
    )
    
    # Container for the 'Flowable' objects
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    # Custom styles (reduced sizes to fit on one page)
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor=HexColor('#FF0000'),
        spaceAfter=8,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=10,
        textColor=HexColor('#000000'),
        spaceAfter=3,
        spaceBefore=5,
        fontName='Helvetica-Bold',
        leftIndent=0
    )
    
    warning_style = ParagraphStyle(
        'Warning',
        parent=styles['Normal'],
        fontSize=9,
        textColor=HexColor('#CC0000'),
        spaceAfter=5,
        spaceBefore=5,
        fontName='Helvetica-Bold',
        backColor=HexColor('#FFE5E5'),
        borderPadding=5,
        leftIndent=10,
        rightIndent=10
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#000000'),
        spaceAfter=4,
        alignment=TA_JUSTIFY,
        leading=9.5
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontSize=8,
        textColor=HexColor('#000000'),
        spaceAfter=2,
        leftIndent=15,
        bulletIndent=12,
        leading=9.5
    )
    
    # Title
    story.append(Paragraph("⚠️ IMPORTANT TRADING DISCLAIMER ⚠️", title_style))
    story.append(Spacer(1, 0.08*inch))
    
    # Main disclaimer
    story.append(Paragraph(
        "<b>NOT FINANCIAL ADVICE:</b> I am not a certified financial advisor, "
        "registered investment advisor, or licensed financial professional. "
        "The trading signals, analysis, and information shared are for informational "
        "and educational purposes only.",
        warning_style
    ))
    story.append(Spacer(1, 0.06*inch))
    
    # Seek Professional Advice
    story.append(Paragraph("<b>Seek Professional Advice:</b>", heading_style))
    story.append(Paragraph(
        "Before making any investment decisions, you should consult with a qualified "
        "financial advisor, accountant, or other professional who can provide advice "
        "tailored to your individual circumstances, risk tolerance, and financial goals.",
        body_style
    ))
    story.append(Spacer(1, 0.05*inch))
    
    # Cryptocurrency Volatility
    story.append(Paragraph("<b>Cryptocurrency & Asset Volatility:</b>", heading_style))
    story.append(Paragraph(
        "Cryptocurrencies and other traded assets are among the most volatile investments "
        "in the world. Prices can experience extreme fluctuations and may decline by 99% "
        "or more. You could lose your entire investment. Stock and ETF prices also "
        "fluctuate and can result in significant losses.",
        body_style
    ))
    story.append(Spacer(1, 0.05*inch))
    
    # SEC & CFTC Disclaimers
    story.append(Paragraph("<b>SEC & CFTC Disclaimers:</b>", heading_style))
    disclaimers = [
        "Past performance does not guarantee future results.",
        "All investments carry risk of loss, including the potential loss of principal.",
        "Cryptocurrency markets are largely unregulated and may be subject to manipulation.",
        "Trading cryptocurrencies and other assets involves substantial risk of loss and is not suitable for all investors.",
        "You should only invest money you can afford to lose.",
        "No investment strategy can guarantee profits or protect against losses."
    ]
    
    for item in disclaimers:
        story.append(Paragraph(f"• {item}", bullet_style))
    
    story.append(Spacer(1, 0.05*inch))
    
    # Risk Management
    story.append(Paragraph("<b>Risk Management:</b>", heading_style))
    story.append(Paragraph(
        "Manage your risk accordingly. Never invest more than you can afford to lose. "
        "Use proper position sizing, stop-loss orders, and risk management techniques. "
        "Diversify your portfolio and never put all your capital into a single trade or asset.",
        body_style
    ))
    story.append(Spacer(1, 0.05*inch))
    
    # Security Warnings
    story.append(Paragraph("<b>Security Warnings:</b>", heading_style))
    security_items = [
        "<b>Hold Your Own Keys:</b> Always maintain control of your private keys and seed phrases. Never share them with anyone, including this channel, website, or any service.",
        "<b>Website Permissions:</b> Be extremely careful when granting websites or applications permission to access your cryptocurrency wallets or funds. Only connect to trusted, verified services.",
        "<b>Phishing Scams:</b> Be vigilant against phishing scams. Always verify website URLs, never click suspicious links, and never enter your private keys or seed phrases on any website.",
        "<b>No Liability:</b> This channel, website, and its operators are not responsible for any losses, damages, or security breaches that may occur from using the information displayed here."
    ]
    
    for item in security_items:
        story.append(Paragraph(item, body_style))
        story.append(Spacer(1, 0.03*inch))
    
    story.append(Spacer(1, 0.05*inch))
    
    # No Guarantees
    story.append(Paragraph("<b>No Guarantees:</b>", heading_style))
    story.append(Paragraph(
        "Trading signals, analysis, and strategies are not guarantees of profit. "
        "Market conditions can change rapidly, and past signals or performance do not "
        "predict future results. Every trade carries risk, and losses are always possible.",
        body_style
    ))
    story.append(Spacer(1, 0.06*inch))
    
    # Final Warning
    story.append(Paragraph(
        "<b>YOU ARE SOLELY RESPONSIBLE FOR ALL TRADING AND INVESTMENT DECISIONS YOU MAKE.</b>",
        warning_style
    ))
    story.append(Spacer(1, 0.05*inch))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=7,
        textColor=HexColor('#666666'),
        alignment=TA_CENTER,
        fontStyle='italic'
    )
    
    story.append(Spacer(1, 0.04*inch))
    story.append(Paragraph(
        "This disclaimer applies to all content, videos, and communications from this channel.",
        footer_style
    ))
    story.append(Paragraph(
        "Last Updated: " + __import__('datetime').datetime.now().strftime('%B %d, %Y'),
        footer_style
    ))
    
    # Build PDF
    doc.build(story)
    print(f"✓ PDF created successfully: {output_filename}")

if __name__ == "__main__":
    import sys
    output_file = sys.argv[1] if len(sys.argv) > 1 else "Trading_Disclaimer.pdf"
    landscape_mode = "--landscape" in sys.argv or "-l" in sys.argv
    create_disclaimer_pdf(output_file, use_landscape=landscape_mode)

