from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
import textwrap
from PyPDF2 import PdfReader
import re

import os
from flask import Flask, render_template, request, send_file
app=Flask(__name__)
# Constants
PAGE_WIDTH, PAGE_HEIGHT = A4
LEFT_MARGIN = 70
TOP_MARGIN = 50
BOTTOM_MARGIN = 50
RIGHT_MARGIN = 50
BASE_LINE_SPACING_FACTOR = 1.1
# Update the default font path
DEFAULT_FONT_PATH = "fonts/Peax Handwritinglight.ttf"

# Register the default font
pdfmetrics.registerFont(TTFont("HandFont", DEFAULT_FONT_PATH))

# Register additional fonts (replace with your actual font files and names)
ADDITIONAL_FONTS = {
    "Another font1":"fonts/I Love Glitter.ttf",
    "Another font2":"fonts/Sacramento-Regular.ttf",
    "Another font3":"fonts/Whitenice.ttf",
    "Another font4":"fonts/Barokah Signature by Alifinart Studio.ttf "
}

for font_name, font_path in ADDITIONAL_FONTS.items():
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
    except Exception as e:
        print(f"Error registering font '{font_name}' from '{font_path}': {e}")

def wrap_text(text, font_name, font_size, max_width):
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.strip().split()
        if not words:
            lines.append("")
            continue

        line = ""
        for word in words:
            test_line = f"{line} {word}".strip()
            if pdfmetrics.stringWidth(test_line, font_name, font_size) < max_width:
                line = test_line
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines
def is_likely_heading(line):
    if '(' in line and ')' in line:
        return False
    words = line.strip().split()
    if words and words[0].endswith(':'):
        return True
    keywords = ["Introduction", "Summary", "Conclusion", "Chapter", "Section", "APPENDIX"]
    if line.isupper():
        return True
    if line.istitle() and len(line.split()) <= 5: # Limit title-cased headings to a few words
        return True
    for keyword in keywords:
        if line.lower().startswith(keyword.lower()): # Case-insensitive check
            return True
    if re.match(r"^\d+\.\s", line): # Check for numbered headings (e.g., "1. Introduction")
        return True
    if re.match(r"^[A-Z]\.\s", line): # Check for lettered headings (e.g., "A. Background")
        return True
    return False

def draw_lines(canvas_obj, lines, font_name, font_size, start_x, start_y, line_spacing, ink_color, heading_color):
    y = start_y
    font_obj = pdfmetrics.getFont(font_name)
    line_height = font_obj.face.ascent * font_size / 1000.0
    descender = font_obj.face.descent * font_size / 1000.0
    ascent = font_obj.face.ascent * font_size / 1000.0
    y_ruled_line = y # The ruled line will be at the current baseline

    current_y = y
    for line in lines:
        if current_y < BOTTOM_MARGIN + line_height:
            canvas_obj.showPage()
            current_y = PAGE_HEIGHT - TOP_MARGIN
            y_ruled_line = current_y

        # Draw ruled line (at the current baseline)
        canvas_obj.setStrokeColor(HexColor("#A9A9A9")) # Or your preferred dark color
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(LEFT_MARGIN, y_ruled_line, PAGE_WIDTH - RIGHT_MARGIN, y_ruled_line)

        # Draw margin line (red)
        canvas_obj.setStrokeColor(HexColor("#FF6666"))
        canvas_obj.setLineWidth(2)
        canvas_obj.line(LEFT_MARGIN - 15, 0, LEFT_MARGIN - 15, PAGE_HEIGHT)

        # Detect headings and style
        
        is_heading = is_likely_heading(line)
        current_font_size = font_size + 2 if is_heading else font_size
        canvas_obj.setFont(font_name, current_font_size)
        text_width = pdfmetrics.stringWidth(line, font_name, current_font_size)
        canvas_obj.setFillColor(HexColor(heading_color if is_heading else ink_color))
        canvas_obj.drawString(start_x, current_y, line) # Draw at the current y (baseline)
        if is_heading:
            canvas_obj.line(start_x, current_y - 4, start_x + text_width, current_y - 4)

        current_y -= line_spacing
        y_ruled_line -= line_spacing # Move the next ruled line down

    return current_y

def create_handwritten_pdf(text, font_size=28, font_name="HandFont", ink_color="#1A237E", heading_color="#000000"):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    usable_width = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
    current_y = PAGE_HEIGHT - TOP_MARGIN
    c.setFont(font_name, font_size)

    paragraphs = text.split("\n\n")

    for paragraph in paragraphs:
        lines = wrap_text(paragraph, font_name, font_size, usable_width)
        line_spacing = font_size * BASE_LINE_SPACING_FACTOR

        current_y = draw_lines(c, lines, font_name, font_size, LEFT_MARGIN, current_y, line_spacing, ink_color, heading_color)
        current_y -= font_size * BASE_LINE_SPACING_FACTOR / 2

        if current_y < BOTTOM_MARGIN:
            c.showPage()
            c.setFont(font_name, font_size)
            current_y = PAGE_HEIGHT - TOP_MARGIN

    c.save()
    buffer.seek(0)
    return buffer

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/convert', methods=['POST'])
def convert():
    pdf_file = request.files.get('file')
    if not pdf_file:
        return "No file uploaded", 400

    pdf_reader = PdfReader(pdf_file)
    full_text = ""
    for page in pdf_reader.pages:
        full_text += page.extract_text() + "\n\n"

    font_size = int(request.form.get("font_size", 32))
    selected_font = request.form.get("font_name", "HandFont") # Get selected font, default to HandFont

    pdf_bytes = create_handwritten_pdf(full_text, font_size=font_size, font_name=selected_font)

    return send_file(
        pdf_bytes,
        mimetype='application/pdf',
        download_name='handwritten_notes.pdf',
        as_attachment=True
    )

if __name__ == '__main__':
    # app.run(debug=True
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)