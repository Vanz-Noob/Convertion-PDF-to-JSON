# PDF Invoice Product and Summary Extractor

A Python-based web application built with Streamlit that extracts product details and summary values (Total, VAT, Amount Due) from PDF invoices. The extracted data is presented in a structured JSON format and can be downloaded.

## Features

*   **Upload PDF:** Upload a PDF invoice file through a user-friendly Streamlit interface.
*   **Table Extraction:** Extracts tables from the PDF using `pdfplumber`.
*   **Header Recognition:** Identifies the main product table based on "Description" and "Amount (USD)" headers.
*   **Multi-Page Tables:** Continues reading data rows from subsequent pages if the header is found on the first page.
*   **Data Processing:** Converts "Amount (USD)" values to floats and treats "Description" values as product names.
*   **Summary Extraction:** Attempts to extract Total, VAT, and Amount Due values from the PDF text.
*   **JSON Output:** Generates a structured JSON file containing the extracted products and summary values.
*   **Download Results:** Download the generated JSON file.
*   **Preview Data:** View the extracted products and summary information on the web interface.
*   **Copyright Footer:** Displays "© 2025 Renaldi Azhar. All rights reserved." on all pages.

## Prerequisites

*   Python 3.8 or higher
*   pip (Python package installer)

## Installation

1.  **Clone or Download the Repository:**
    ```bash
    git clone <url-repositori-anda>
    cd <nama-direktori-repositori>
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    *   On Windows:
        ```bash
        venv\Scripts\activate
        ```
    *   On macOS/Linux:
        ```bash
        source venv/bin/activate
        ```

4.  **Install Dependencies:**
    ```bash
    pip install streamlit pdfplumber pandas
    ```
    *Note: You might encounter NumPy warnings on Windows. It's recommended to follow the NumPy installation troubleshooting steps if the application crashes.*

## Usage

1.  **Ensure your virtual environment is activated.**
2.  **Navigate to the project directory (where `frontend/app.py` is located).**
3.  **Run the Streamlit application:**
    ```bash
    streamlit run frontend/app.py
    ```
4.  **Open your web browser and go to the URL displayed in the terminal (usually `http://localhost:8501`).**
5.  **Upload your PDF invoice file.**
6.  **Wait for the processing to complete.**
7.  **View the extracted products and summary values.**
8.  **Download the resulting JSON file if needed.**

## Project Structure
