# backend/pdf_processor.py

import pdfplumber
import json
import os
import re
import logging # Import logging
from datetime import datetime

# Konfigurasi logging (opsional, bisa disesuaikan)
# logging.basicConfig(level=logging.INFO) # Jika Anda ingin log tetap muncul
# logging.basicConfig(level=logging.WARNING) # Ini akan menyembunyikan INFO, hanya menampilkan WARNING ke atas

def save_uploaded_file(uploaded_file, filename):
    """
    Fungsi untuk menyimpan file yang diunggah ke folder 'uploads'.
    """
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, filename)
    # Streamlit's UploadedFile memiliki metode getbuffer untuk mendapatkan bytes
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def save_json_result(json_data, original_filename):
    """
    Fungsi untuk menyimpan hasil JSON ke folder 'results'.
    """
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    # Ganti ekstensi .pdf dengan .json
    json_filename = f"{os.path.splitext(original_filename)[0]}_processed.json"
    file_path = os.path.join(results_dir, json_filename)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)
    return file_path

def _extract_summary_values(pdf_path):
    """
    Mencoba mengekstrak nilai Total, VAT, dan Amount Due dari teks PDF.
    Ini adalah fungsi dasar dan mungkin perlu disesuaikan lebih lanjut
    tergantung format spesifik PDF Anda.

    Args:
        pdf_path (str): Jalur ke file PDF.

    Returns:
        dict: Dictionary dengan kunci 'total', 'vat', 'amount_due', default ke None.
    """
    total = None
    vat = None
    amount_due = None

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if not text:
                    continue

                total_match = re.search(r'Total\s*(?:\([^\)]*\))?\s*[:\-]?\s*\$?([0-9,]+\.[0-9]{2})', text, re.IGNORECASE)
                if total_match:
                    total_str = total_match.group(1).replace(',', '')
                    total = float(total_str)

                vat_match = re.search(r'(?:VAT|Tax)\s*(?:Amount)?\s*[:\-]?\s*\$?([0-9,]+\.[0-9]{2})', text, re.IGNORECASE)
                if vat_match:
                    vat_str = vat_match.group(1).replace(',', '')
                    vat = float(vat_str)

                amount_due_match = re.search(r'(?:Amount\s+)?Due\s*[:\-]?\s*\$?([0-9,]+\.[0-9]{2})', text, re.IGNORECASE)
                if amount_due_match:
                    amount_due_str = amount_due_match.group(1).replace(',', '')
                    amount_due = float(amount_due_str)

                if total is not None and vat is not None and amount_due is not None:
                    break

    except Exception as e:
        logging.warning(f"Error extracting summary values: {e}") # Gunakan logging.warning

    return {
        "total": total,
        "vat": vat,
        "amount_due": amount_due
    }


def _process_table_data(tables_data):
    """
    Memproses daftar tabel yang diekstrak, menganggap tabel setelah tabel pertama
    sebagai kelanjutan data dari tabel pertama (tanpa header).

    Args:
        tables_data (list): Output dari pdfplumber.extract_tables().

    Returns:
        list: Daftar dictionary dengan kunci 'product_name' dan 'amount_usd'.
    """
    products = []
    desc_col_idx = None
    amount_col_idx = None
    header_found = False

    for table_info in tables_data: # Perbaikan: ganti tables_ menjadi tables_data
        table_rows = table_info['data']
        if not table_rows:
            continue

        if not header_found:
            headers = table_rows[0] if table_rows else []
            for i, header in enumerate(headers):
                header_str = str(header).strip() if header is not None else ""
                if header_str.lower() == 'description':
                    desc_col_idx = i
                elif header_str.lower() == 'amount (usd)':
                    amount_col_idx = i

            if desc_col_idx is not None and amount_col_idx is not None:
                header_found = True
                logging.info(f"Found 'Description' and 'Amount (USD)' headers in table on page {table_info['page_number']}.") # Gunakan logging.info
                start_row_idx = 1
            else:
                logging.info(f"Headers not found in table on page {table_info['page_number']}. Continuing search...") # Gunakan logging.info
                continue
        else:
            start_row_idx = 0

        for row in table_rows[start_row_idx:]:
            if len(row) <= max(desc_col_idx, amount_col_idx):
                continue

            product_name = row[desc_col_idx]
            amount_str = row[amount_col_idx]

            try:
                clean_amount_str = re.sub(r'[^\d.-]', '', str(amount_str))
                is_negative = clean_amount_str.startswith('(') and clean_amount_str.endswith(')')
                if is_negative:
                    clean_amount_str = '-' + clean_amount_str[1:-1]
                amount_usd = float(clean_amount_str)
            except (ValueError, TypeError):
                continue

            if product_name is None:
                product_name = ""
            else:
                product_name = str(product_name).strip()

            products.append({
                "product_name": product_name,
                "amount_usd": amount_usd
            })

    if not header_found:
        logging.warning("Could not find 'Description' and 'Amount (USD)' headers in any table in the PDF.") # Gunakan logging.warning

    return products


def pdf_to_json(pdf_path):
    """
    Mengekstrak tabel dan nilai ringkasan dari file PDF,
    dan mengembalikan data sebagai dictionary yang siap dikonversi ke JSON.

    Args:
        pdf_path (str): Jalur ke file PDF yang diunggah dan disimpan.

    Returns:
        dict: Dictionary berisi 'extracted_products', 'summary_values', dan 'processing_metadata'.
    """
    all_tables_data = []
    processing_metadata = {
        "source_pdf": pdf_path,
        "extraction_method": "pdfplumber",
        "timestamp": datetime.now().isoformat()
    }

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                tables_on_page = page.extract_tables()
                if tables_on_page:
                    for i, table in enumerate(tables_on_page):
                        all_tables_data.append({
                            "page_number": page_num + 1,
                            "table_index_on_page": i,
                            "data": table
                        })

    except FileNotFoundError:
        raise FileNotFoundError(f"File PDF tidak ditemukan di: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error processing PDF with pdfplumber: {e}")

    products = _process_table_data(all_tables_data)
    summary_values = _extract_summary_values(pdf_path)

    result = {
        "extracted_products": products,
        "summary_values": summary_values,
        "raw_extracted_tables": all_tables_data,
        "processing_metadata": processing_metadata
    }

    return result

# Anda bisa menambahkan fungsi-fungsi pembantu lainnya di sini jika diperlukan