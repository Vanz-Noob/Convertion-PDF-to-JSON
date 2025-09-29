# frontend/app.py
import sys
import os
from pathlib import Path
import streamlit as st
import tempfile
import time
import json
import logging

# Fix untuk menambahkan direktori utama ke path Python
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Setelah memperbaiki path, baru import modul backend
from backend.pdf_processor import pdf_to_json, save_uploaded_file, save_json_result

def render_upload_page():
    """Tampilkan halaman upload PDF"""
    st.title("🛒 PDF Invoice Product Extractor")
    st.markdown("Extract products and amounts from your PDF invoice")
    
    uploaded_file = st.file_uploader(
        "Upload your PDF invoice", 
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="collapsed"
    )
    
    # Footer Copyright untuk Halaman Upload
    st.markdown("---") # Garis pemisah
    st.markdown(
        """
        <div style='text-align: center; margin-top: 20px;'>
            <p>© 2025 Renaldi Azhar. All rights reserved.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    return uploaded_file

def render_loading_screen(file_name):
    """Tampilkan layar loading selama pemrosesan"""
    st.title("Processing Your Invoice")
    st.markdown(f"**File:** {file_name}")
    
    with st.spinner("Analyzing invoice data..."):
        # Bar progres simulasi
        progress_bar = st.progress(0)
        for i in range(100):
            time.sleep(0.02) # Delay kecil untuk simulasi
            progress_bar.progress(i + 1)
    
    st.success("✅ Processing completed!")
    time.sleep(0.5) # Jeda kecil sebelum pindah ke hasil

def render_result_page(json_data, file_name, json_path):
    """Tampilkan hasil konversi dan opsi download"""
    st.success("🎉 Products extracted successfully!")
    
    # Ambil data produk dan ringkasan
    products = json_data.get("extracted_products", [])
    summary = json_data.get("summary_values", {})
    num_products = len(products)
    # Hitung total manual dari produk jika summary_values['total'] tidak ditemukan atau None
    total_manual = sum(p['amount_usd'] for p in products) if products else 0
    total_from_pdf = summary.get('total')
    vat_from_pdf = summary.get('vat')
    amount_due_from_pdf = summary.get('amount_due')

    # Tampilkan informasi ringkasan
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Number of Products Found", num_products)
    with col2:
        # Tampilkan Total dari PDF jika ditemukan, jika tidak, hitung manual
        total_display = f"${total_from_pdf:,.2f}" if total_from_pdf is not None else f"${total_manual:,.2f} (Calculated)"
        st.metric("Total (USD)", total_display)
    with col3:
        # Tampilkan Amount Due dari PDF jika ditemukan
        amount_due_display = f"${amount_due_from_pdf:,.2f}" if amount_due_from_pdf is not None else "N/A"
        st.metric("Amount Due (USD)", amount_due_display)

    # Tampilkan VAT jika ditemukan
    if vat_from_pdf is not None:
        st.metric("VAT (USD)", f"${vat_from_pdf:,.2f}")

    # Tampilkan lokasi file yang disimpan
    pdf_saved_path = json_data.get("processing_metadata", {}).get("source_pdf", "N/A")
    st.info(f"📁 PDF saved to: {pdf_saved_path}")
    st.info(f"📁 JSON saved to: {json_path}")
    
    # Tombol download JSON
    json_str = json.dumps(json_data, indent=2, ensure_ascii=False)
    st.download_button(
        label="⬇️ Download Full JSON File",
        data=json_str,
        file_name=f"{os.path.splitext(file_name)[0]}_processed.json",
        mime="application/json",
        use_container_width=True,
        type="primary"
    )
    
    # Preview JSON Produk
    with st.expander("🔍 View Processed Products JSON", expanded=True):
        st.json(products)

    # Tampilkan tabel produk (opsional, bisa banyak)
    if num_products > 0:
        with st.expander(f"📊 View Products Table ({num_products} found)", expanded=False):
            import pandas as pd
            df_products = pd.DataFrame(products)
            st.dataframe(df_products, use_container_width=True)

    # Informasi tambahan
    st.info("""
    ### How to use this JSON:
    - This structured data contains the product names and amounts extracted from your PDF.
    - The 'amount_usd' values are converted to float numbers.
    - Summary values like Total, VAT, and Amount Due are also extracted where possible.
    - You can parse this JSON in your applications or import it into databases/spreadsheets.
    """)
    
    # Footer Copyright untuk Halaman Hasil
    st.markdown("---") # Garis pemisah
    st.markdown(
        """
        <div style='text-align: center; margin-top: 20px;'>
            <p>© 2025 Renaldi Azhar. All rights reserved.</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Tombol kembali ke upload
    if st.button("🔄 Process Another File", use_container_width=True):
        st.session_state.processed = False
        st.session_state.json_data = None
        st.rerun()

def main():
    st.set_page_config(
        page_title="Invoice Product Extractor",
        page_icon="🛒",
        layout="wide"
    )
    
    # Initialize session state
    if 'json_data' not in st.session_state:
        st.session_state.json_data = None
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'file_name' not in st.session_state:
        st.session_state.file_name = ""
    if 'json_path' not in st.session_state:
        st.session_state.json_path = ""
    
    if not st.session_state.processed:
        # Halaman upload
        uploaded_file = render_upload_page()
        
        if uploaded_file is not None:
            # Simpan nama file untuk referensi
            st.session_state.file_name = uploaded_file.name
            
            # Tampilkan loading screen
            render_loading_screen(uploaded_file.name)
            
            try:
                # Simpan file yang diunggah ke folder uploads
                saved_path = save_uploaded_file(uploaded_file, uploaded_file.name)
                
                # Proses PDF menggunakan backend
                json_data = pdf_to_json(saved_path)
                st.session_state.json_data = json_data
                
                # Simpan hasil JSON ke folder results
                json_path = save_json_result(json_data, uploaded_file.name)
                st.session_state.json_path = json_path
                
                st.session_state.processed = True
                st.rerun() # Refresh untuk menampilkan halaman hasil
                
            except Exception as e:
                st.error(f"❌ Error processing file: {str(e)}")
                # import traceback
                # st.error(traceback.format_exc())
                st.stop() # Hentikan eksekusi jika error
    
    else:
        # Halaman hasil
        render_result_page(st.session_state.json_data, st.session_state.file_name, st.session_state.json_path)

if __name__ == "__main__":
    # Atur level logging untuk menyembunyikan log INFO dan DEBUG dari kode Anda
    # Ini TIDAK akan menyembunyikan peringatan NumPy
    logging.basicConfig(level=logging.WARNING) # Atur ke WARNING atau ERROR

    main()