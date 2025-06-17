from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.pdfbase.pdfmetrics import stringWidth
import os
import requests
from io import BytesIO
from PIL import Image


def wrap_text(text, font_name, font_size, max_width):
    words = text.split()
    lines = []
    line = ""
    for word in words:
        test_line = f"{line} {word}".strip()
        width = stringWidth(test_line, font_name, font_size)
        if width <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def generate_faq_pdf(row, filename="robot_faq_final.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    margin = 40

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.drawString(margin, height - margin, row.get("Name", "Robot Name"))

    # Feature bullets (dynamic)
    icon_lines = []
    if row.get("Device Required", "").strip().lower() == "no":
        icon_lines.append("• No Device Required")
    if row.get("Does the device rely on AUDITORY cues for interations and functionality?", "").strip().lower() == "no":
        icon_lines.append("• No Audio Required")
    if row.get("Visual Accessibility", "").strip().lower() == "no":
        icon_lines.append("• No Text/Visual Required")
    
    # Always included for now
    icon_lines.append("• Touch Required")

    # Draw feature bullets
    c.setFont("Helvetica", 10)
    for i, line in enumerate(icon_lines):
        c.drawString(margin, height - margin - 30 - (i * 15), line)

    # Robot image
    image_y = height - margin - 230
    image_url = row.get("Image", None)
    image_path = "robot_temp_img.png"

    if image_url:
        try:
            response = requests.get(image_url, timeout=10)
            image = Image.open(BytesIO(response.content))
            image.save(image_path)
            c.drawImage(image_path, margin, image_y, width=1.6 * inch, height=1.6 * inch, preserveAspectRatio=True)
            c.drawImage(image_path, width - 2.3 * inch - margin, height - margin - 100,
                        width=2.3 * inch, height=1.2 * inch, preserveAspectRatio=True)
            os.remove(image_path)
        except Exception as e:
            print("⚠️ Image load failed:", e)

    right_x = margin + 250
    summary_top_y = height - margin - 130

    # Product Summary
    product_summary = row.get("Description", "This robot teaches coding and sequencing skills.")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(right_x, summary_top_y, "Product Summary")
    c.setFont("Helvetica", 10)
    summary_lines = wrap_text(product_summary, "Helvetica", 10, 250)
    for i, line in enumerate(summary_lines):
        c.drawString(right_x, summary_top_y - 15 - i * 14, line)

    # Footer / additional details
    footer_y = image_y - 20
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, footer_y, "Grade Level:")
    c.drawString(margin + 100, footer_y, str(row.get("Min Grade Level", "N/A")))
    c.drawString(margin, footer_y - 15, "Students Per Device:")
    c.drawString(margin + 100, footer_y - 15, str(row.get("Max Users", "1 - 2")))
    c.drawString(margin, footer_y - 30, "Computer Science Standard(s):")
    c.setFont("Helvetica", 9)
    c.drawString(margin, footer_y - 45, "Washington State CS Standards: Algorithms and Programming")

    def clean_price(val):
        if isinstance(val, float):
            return f"${val:,.2f}"
        s = str(val).replace("$", "").strip()
        try:
            return f"${float(s):,.2f}"
        except:
            return "N/A"

    single_price = clean_price(row.get("Price", "N/A"))
    set_price = clean_price(row.get("Price per Set", "N/A"))

    data = [
        ["Price"],
        ["Single Unit", single_price],
        ["Classroom Set (24 students)", set_price]
    ]
    table = Table(data, colWidths=[2.2 * inch, 2.2 * inch])
    table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.white),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, margin, footer_y - 150)

    # Purchase URL
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, footer_y - 190, "More Information:")
    c.setFillColor(colors.blue)
    c.drawString(margin + 110, footer_y - 190, row.get("Purchase Website", ""))
    c.setFillColor(colors.black)

    c.save()
    return filename
