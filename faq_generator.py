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
    lines, line = [], ""
    for word in words:
        test_line = f"{line} {word}".strip()
        if stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines

def clean_price(val):
    if isinstance(val, float):
        return f"${val:,.2f}"
    s = str(val).replace("$", "").strip()
    try:
        return f"${float(s):,.2f}"
    except:
        return "N/A"

def generate_faq_pdf(row, filename="auto_glance.pdf"):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    margin = 40

    # --- Title ---
    c.setFont("Helvetica-Bold", 20)
    c.drawString(margin, height - margin, row.get("Name", "Robot Name"))

    # --- Robot Image ---
    image_url = row.get("Image", "")
    image_path = "robot_temp_img.png"
    if image_url:
        try:
            img_data = requests.get(image_url, timeout=10).content
            img = Image.open(BytesIO(img_data))
            img.save(image_path)
            c.drawImage(
                image_path,
                margin,
                height - 250,
                width=2 * inch,
                height=2 * inch,
                preserveAspectRatio=True
            )
            os.remove(image_path)
        except Exception as e:
            print("⚠️ Image failed to load:", e)

    # --- Product Summary ---
    summary = row.get("Description", "No summary available.")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 2.2 * inch, height - 90, "Product Summary")
    c.setFont("Helvetica", 10)
    lines = wrap_text(summary, "Helvetica", 10, width - margin * 2 - 2.2 * inch)
    for i, line in enumerate(lines):
        c.drawString(margin + 2.2 * inch, height - 105 - (i * 14), line)

    y_cursor = height - 270

    # --- Power Table ---
    power_data = [
        ["Rechargeable", "Batteries Needed"],
        [row.get("Rechargeable", "N/A"), row.get("Batteries", "N/A")]
    ]
    power_table = Table(power_data, colWidths=[2.5 * inch] * 2)
    power_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    power_table.wrapOn(c, width, height)
    power_table.drawOn(c, margin, y_cursor)

    # --- Compatibility Table ---
    y_cursor -= 60
    comp_data = [
        ["Device Required", "Visual Cues", "Auditory Cues"],
        [
            row.get("Device Required", "N/A"),
            row.get("Visual Accessibility", "N/A"),
            row.get("Does the device rely on AUDITORY cues for interations and functionality?", "N/A")
        ]
    ]
    comp_table = Table(comp_data, colWidths=[1.8 * inch] * 3)
    comp_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    comp_table.wrapOn(c, width, height)
    comp_table.drawOn(c, margin, y_cursor)

    # --- Age/Grade Table ---
    y_cursor -= 60
    age_data = [
        ["Min Grade Level", "Max Users"],
        [row.get("Min Grade Level", "N/A"), row.get("Max Users", "N/A")]
    ]
    age_table = Table(age_data, colWidths=[2.5 * inch] * 2)
    age_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    age_table.wrapOn(c, width, height)
    age_table.drawOn(c, margin, y_cursor)

    # --- Price Table ---
    y_cursor -= 60
    price_data = [
        ["Single Unit", "Classroom Set"],
        [
            clean_price(row.get("Price", "N/A")),
            clean_price(row.get("Price per Set", "N/A"))
        ]
    ]
    price_table = Table(price_data, colWidths=[2.5 * inch] * 2)
    price_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold')
    ]))
    price_table.wrapOn(c, width, height)
    price_table.drawOn(c, margin, y_cursor)

    # --- Purchase Link ---
    y_cursor -= 60
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin, y_cursor, "More Info / Buy:")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.blue)
    c.drawString(margin + 90, y_cursor, row.get("Purchase Website", ""))
    c.setFillColor(colors.black)

    c.save()
    return filename
