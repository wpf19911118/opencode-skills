#!/usr/bin/env python3
"""
Advanced PDF Reader Tool - Extract text and images from PDF files
支持文本提取、目录识别、PDF转图片功能

Usage:
    python pdf_reader.py <pdf_file> [start_page] [end_page] [-o output.txt]
    python pdf_reader.py <pdf_file> --toc                    # 仅提取目录
    python pdf_reader.py <pdf_file> --images <output_dir>    # 提取所有图片
    python pdf_reader.py <pdf_file> --page-image <page> <output.png>  # 转换单页为图片
"""

import sys
import os
import re
from pathlib import Path

try:
    from pypdf import PdfReader
    import fitz  # PyMuPDF for image extraction
except ImportError:
    print("Installing required packages...")
    os.system("pip install pypdf PyMuPDF pillow")
    from pypdf import PdfReader
    import fitz


class PDFReader:
    def __init__(self, pdf_path):
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        self.pdf_path = pdf_path
        self.reader = PdfReader(pdf_path)
        self.total_pages = len(self.reader.pages)
        self.doc = fitz.open(pdf_path)  # For image extraction

    def extract_toc(self):
        """Extract Table of Contents from PDF."""
        toc = []
        try:
            toc_list = self.reader.toc
            if toc_list:
                for item in toc_list:
                    level, title, page_num = item
                    toc.append({
                        'level': level,
                        'title': title,
                        'page': page_num
                    })
        except Exception as e:
            print(f"TOC extraction failed: {e}, trying alternative method...")
            toc = self._extract_toc_alternative()

        return toc

    def _extract_toc_alternative(self):
        """Alternative TOC extraction using text pattern matching."""
        toc = []
        for page_num in range(min(5, self.total_pages)):  # Search first 5 pages
            page = self.reader.pages[page_num]
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    line = line.strip()
                    # Match common TOC patterns
                    if re.match(r'^\d+\.?\s+\S', line) or re.match(r'^Chapter\s+\d+', line, re.I):
                        toc.append({
                            'level': 1,
                            'title': line,
                            'page': page_num + 1
                        })
        return toc

    def extract_text(self, start_page=1, end_page=None):
        """Extract text from specified page range."""
        end_page = end_page or self.total_pages
        text_parts = []

        for page_num in range(start_page - 1, min(end_page, self.total_pages)):
            page = self.reader.pages[page_num]
            text = page.extract_text()
            if text:
                header = f"\n{'='*80}\n--- Page {page_num + 1} ---\n{'='*80}\n\n"
                text_parts.append(header + text)
                print(f"[OK] Extracted page {page_num + 1}")

        return "\n".join(text_parts)

    def extract_all_text(self):
        """Extract all text from PDF."""
        return self.extract_text(1, self.total_pages)

    def extract_images(self, output_dir, pages=None):
        """Extract all images from PDF to specified directory."""
        os.makedirs(output_dir, exist_ok=True)
        image_count = 0

        pages = pages or range(len(self.doc))

        for page_num in pages:
            if page_num >= len(self.doc):
                break
            page = self.doc[page_num]
            images = page.get_images(full=True)

            for img_index, img in enumerate(images):
                xref = img[0]
                base_image = self.doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                output_path = os.path.join(
                    output_dir,
                    f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
                )

                with open(output_path, "wb") as f:
                    f.write(image_bytes)
                image_count += 1
                print(f"[OK] Saved: {output_path}")

        return image_count

    def page_to_image(self, page_num, output_path, zoom=2.0):
        """Convert a single page to image."""
        page = self.doc[page_num - 1]  # 0-indexed
        mat = fitz.Matrix(zoom, zoom)  # Zoom factor
        pix = page.get_pixmap(matrix=mat)

        os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
        pix.save(output_path)
        print(f"[OK] Saved page {page_num} as image: {output_path}")
        return output_path

    def pages_to_images(self, start_page=1, end_page=None, output_dir="pdf_images", zoom=2.0):
        """Convert multiple pages to images."""
        os.makedirs(output_dir, exist_ok=True)
        end_page = end_page or self.total_pages

        for page_num in range(start_page, end_page + 1):
            output_path = os.path.join(output_dir, f"page_{page_num:04d}.png")
            self.page_to_image(page_num, output_path, zoom)

        return output_dir


def main():
    # Check for help first
    if len(sys.argv) < 2 or '--help' in sys.argv or '-h' in sys.argv:
        print_help()
        sys.exit(0)

    pdf_path = sys.argv[1]

    # Check if file exists
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found: {pdf_path}")
        print("Use 'python pdf_reader.py --help' for usage information.")
        sys.exit(1)

    pdf_reader = PDFReader(pdf_path)

    # Parse commands - help already checked above

    if '--toc' in sys.argv:
        # Extract Table of Contents
        print(f"[INFO] Extracting TOC from {pdf_path}...")
        toc = pdf_reader.extract_toc()
        print("\n" + "="*60)
        print("TABLE OF CONTENTS")
        print("="*60)
        for item in toc:
            indent = "  " * (item['level'] - 1)
            print(f"{indent}{item['title']} ... Page {item['page']}")
        return

    if '--images' in sys.argv:
        # Extract all images
        idx = sys.argv.index('--images')
        output_dir = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "pdf_images"
        print(f"[INFO] Extracting images to {output_dir}...")
        count = pdf_reader.extract_images(output_dir)
        print(f"\n[INFO] Total images extracted: {count}")
        return

    if '--page-image' in sys.argv:
        # Convert page to image
        idx = sys.argv.index('--page-image')
        page_num = int(sys.argv[idx + 1])
        output_path = sys.argv[idx + 2] if idx + 2 < len(sys.argv) else f"page_{page_num}.png"
        pdf_reader.page_to_image(page_num, output_path)
        return

    if '--all-images' in sys.argv:
        # Convert all pages to images
        idx = sys.argv.index('--all-images')
        output_dir = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "pdf_images"
        print(f"[INFO] Converting all pages to images in {output_dir}...")
        pdf_reader.pages_to_images(1, None, output_dir)
        return

    # Default: Extract text
    start_page = 1
    end_page = None
    output_file = None

    args = sys.argv[2:]
    if args:
        if args[0].isdigit():
            start_page = int(args[0])
        if len(args) > 1 and args[1].isdigit():
            end_page = int(args[1])

    if '-o' in args:
        idx = args.index('-o')
        output_file = args[idx + 1]

    print(f"[INFO] PDF has {pdf_reader.total_pages} pages")
    print(f"[INFO] Extracting pages {start_page} to {end_page or pdf_reader.total_pages}")

    text = pdf_reader.extract_text(start_page, end_page)

    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\n[INFO] Text saved to: {output_file}")

    sys.stdout.reconfigure(encoding='utf-8')
    print("\n" + "="*80)
    print(text)


def print_help():
    print("""
Advanced PDF Reader Tool
========================

Usage:
    python pdf_reader.py <pdf_file> [start_page] [end_page] [-o output.txt]
    python pdf_reader.py <pdf_file> --toc
    python pdf_reader.py <pdf_file> --images <output_dir>
    python pdf_reader.py <pdf_file> --page-image <page_num> <output.png>
    python pdf_reader.py <pdf_file> --all-images <output_dir>

Commands:
    <pdf_file>               PDF file path (required)
    [start_page] [end_page]  Page range to extract (default: 1 to end)
    -o <file>                Save output to file

Special Commands:
    --toc                    Extract Table of Contents
    --images <dir>           Extract all embedded images
    --page-image <n> <file>  Convert page n to image
    --all-images <dir>       Convert all pages to images

Examples:
    python pdf_reader.py paper.pdf 1 10 -o output.txt
    python pdf_reader.py paper.pdf --toc
    python pdf_reader.py paper.pdf --page-image 1 page1.png
    python pdf_reader.py paper.pdf --all-images ./images
""")


if __name__ == "__main__":
    main()
