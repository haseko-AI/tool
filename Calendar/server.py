#!/usr/bin/env python3
"""
PDF Form Web Server
- Serves the web form (index.html)
- Receives form data and generates filled PDFs
- Returns the PDF for download

Setup:
  pip install flask pypdf Pillow
  
  Place these files in the same directory:
    server.py       (this file)
    generate_pdf.py (PDF generation logic)
    index.html      (web form)
    TEST.pdf        (PDF template)
    image001.png    (selectable image 1)
    image002.png    (selectable image 2)

Run:
  python server.py

Then open http://localhost:5000 in your browser.
"""

from flask import Flask, request, send_file, send_from_directory
import os
import tempfile
from generate_pdf import fill_pdf

app = Flask(__name__, static_folder='.')

# Configuration
TEMPLATE_PDF = 'TEST.pdf'
IMAGE_DIR = '.'
ALLOWED_IMAGES = {
    'image001.png': '点検・作業員',
    'image002.png': '組合会計部',
}


@app.route('/')
def index():
    """Serve the web form."""
    return send_from_directory('.', 'index.html')


@app.route('/images/<filename>')
def serve_image(filename):
    """Serve image files for preview."""
    if filename in ALLOWED_IMAGES:
        return send_from_directory(IMAGE_DIR, filename)
    return 'Not found', 404


@app.route('/generate', methods=['POST'])
def generate():
    """Generate filled PDF from form data."""
    image_file = request.form.get('image', '')
    text_value = request.form.get('text', '')

    # Validate image selection
    if image_file not in ALLOWED_IMAGES:
        return 'Invalid image selection', 400

    image_path = os.path.join(IMAGE_DIR, image_file)
    if not os.path.exists(image_path):
        return 'Image file not found', 404

    if not os.path.exists(TEMPLATE_PDF):
        return 'PDF template not found', 404

    # Generate PDF to temp file
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        output_path = tmp.name

    try:
        fill_pdf(TEMPLATE_PDF, image_path, text_value, output_path)
        return send_file(
            output_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name='output.pdf'
        )
    finally:
        # Clean up temp file after sending
        if os.path.exists(output_path):
            os.unlink(output_path)


if __name__ == '__main__':
    print("=" * 50)
    print("  PDF Form Server")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5000, debug=True)
