#!/usr/bin/env python3
"""
PDF Form Filler - Sets button icon image and text field value in a PDF template.
Usage: python generate_pdf.py <template.pdf> <image_file> <text_value> <output.pdf>
"""

import sys
import zlib
from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject, DictionaryObject, NameObject, NumberObject,
    DecodedStreamObject, TextStringObject, ByteStringObject,
    BooleanObject
)
from PIL import Image


def create_image_xobject(image_path):
    """Create a PDF Image XObject from a PNG/JPEG file."""
    img = Image.open(image_path)
    img = img.convert("RGB")
    width, height = img.size

    raw_data = img.tobytes()
    compressed = zlib.compress(raw_data)

    img_stream = DecodedStreamObject()
    img_stream._data = compressed
    img_stream.update({
        NameObject("/Type"): NameObject("/XObject"),
        NameObject("/Subtype"): NameObject("/Image"),
        NameObject("/Width"): NumberObject(width),
        NameObject("/Height"): NumberObject(height),
        NameObject("/ColorSpace"): NameObject("/DeviceRGB"),
        NameObject("/BitsPerComponent"): NumberObject(8),
        NameObject("/Filter"): NameObject("/FlateDecode"),
        NameObject("/Length"): NumberObject(len(compressed)),
    })

    return img_stream, width, height


def fill_pdf(template_path, image_path, text_value, output_path):
    """Fill PDF form with image and text."""
    reader = PdfReader(template_path)
    writer = PdfWriter()
    writer.append(reader)

    # Create image XObject
    img_obj, img_w, img_h = create_image_xobject(image_path)
    img_ref = writer._add_object(img_obj)

    for page in writer.pages:
        if '/Annots' not in page:
            continue
        for annot_ref in page['/Annots']:
            annot = annot_ref.get_object()
            field_name = annot.get('/T', '')

            if field_name == 'image_af_image':
                # Set button icon appearance
                rect = annot['/Rect']
                field_w = float(rect[2]) - float(rect[0])
                field_h = float(rect[3]) - float(rect[1])

                scale_x = field_w / img_w
                scale_y = field_h / img_h
                scale = min(scale_x, scale_y)

                scaled_w = img_w * scale
                scaled_h = img_h * scale
                offset_x = (field_w - scaled_w) / 2
                offset_y = (field_h - scaled_h) / 2

                stream_content = (
                    f"q {scaled_w:.2f} 0 0 {scaled_h:.2f} "
                    f"{offset_x:.2f} {offset_y:.2f} cm /Img Do Q"
                )

                ap_stream = DecodedStreamObject()
                ap_stream._data = stream_content.encode('latin-1')
                ap_stream.update({
                    NameObject("/Type"): NameObject("/XObject"),
                    NameObject("/Subtype"): NameObject("/Form"),
                    NameObject("/BBox"): ArrayObject([
                        NumberObject(0), NumberObject(0),
                        NumberObject(int(field_w)), NumberObject(int(field_h))
                    ]),
                    NameObject("/Resources"): DictionaryObject({
                        NameObject("/XObject"): DictionaryObject({
                            NameObject("/Img"): img_ref
                        })
                    }),
                })

                ap_ref = writer._add_object(ap_stream)
                annot[NameObject("/AP")] = DictionaryObject({
                    NameObject("/N"): ap_ref
                })

            elif field_name == 'text' and text_value:
                # Set text field value
                annot[NameObject("/V")] = TextStringObject(text_value)

    with open(output_path, 'wb') as f:
        writer.write(f)

    print(f"Generated: {output_path}")


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print("Usage: python generate_pdf.py <template.pdf> <image_file> <text_value> <output.pdf>")
        sys.exit(1)

    fill_pdf(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
