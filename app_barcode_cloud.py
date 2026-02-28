import streamlit as st
import streamlit.components.v1 as components
import cv2
from PIL import Image
import requests
import re
import isbnlib
import time

import numpy as np
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

from pydantic import BaseModel

# Custom imports - ensure these files are in your directory
from book_details import get_sim_book_details, get_traditional_book_details

# ---- INITIALIZATION ----
load_dotenv(os.path.join(os.getcwd(), ".env"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ---- SIDEBAR ----
def setup_sidebar():
    with st.sidebar:
        st.title("📚 Book Scanner AI")
        st.markdown("Use AI to recognize ISBNs and retrieve cataloging data.")
        st.divider()
        st.markdown("### 🛠️ Capabilities")
        st.write("Scan a barcode with your USB scanner to retrieve data.")
        st.write("✅ **Dewey AI:** LLM")
        st.markdown("### Supported books languages")
        st.write("✅ **English**")
        st.write("✅ **Traditional Chinese**")
        st.write("✅ **Simplified Chinese**")
        st.divider()
        st.caption("👤 **Author:** Jiyu Yang (Thales Yang)")
        st.caption("📧 **Support:** [thales.yang.dev@gmail.com](mailto:thales.yang.dev@gmail.com)")
        st.caption("🚀 *Powered by LLMs*")

setup_sidebar()

def st_copy_to_clipboard(text):
    """Injects a button and JS to copy text to clipboard."""
    # Escape single quotes for JS
    escaped_text = text.replace("'", "\\'")
    copy_js = f"""
        <script>
        function copyToClipboard() {{
            const text = '{escaped_text}';
            navigator.clipboard.writeText(text).then(() => {{
                parent.postMessage({{type: 'copy-success'}}, '*');
            }});
        }}
        </script>
        <button onclick="copyToClipboard()" style="
            background-color: #ff4b4b;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
        ">
            📋 Copy
        </button>
    """
    components.html(copy_js, height=50)

if "last_meta" not in st.session_state:
    st.session_state.last_meta = None

# ---- MAIN UI ----
st.title("Book Scanner AI")

def handle_scan():
    raw_input = st.session_state.barcode_input
    if raw_input:
        # Clean the input
        isbn = re.sub(r"[^\dX]", "", raw_input.strip())
        if isbnlib.is_isbn10(isbn) or isbnlib.is_isbn13(isbn):
            st.session_state.last_isbn = isbn
        else:
            st.error(f"Invalid ISBN: {isbn}")
        
        # Clear the input box for the next scan
        st.session_state.barcode_input = ""

st.text_input(
    "Ready to scan...", 
    key="barcode_input", 
    on_change=handle_scan, 
    placeholder="Scan barcode here...",
    help="The cursor will automatically stay here for continuous scanning."
)

def find_isbn(text):
    if not text: return None
    clean = re.sub(r"[A-Za-z]", "", text).replace(" ", "")
    pattern = r"(?:7[89]\-?\d{1,5}\-?\d{1,7}\-?\d{1,7}\-?[\dX])|(?:\d{9}[\dX])"
    matches = re.findall(pattern, clean)
    for candidate in matches:
        candidate = candidate.replace("-", "")
        if not candidate.startswith('9'):
            candidate = "9"+ candidate
        if isbnlib.is_isbn10(candidate) or isbnlib.is_isbn13(candidate):
            return candidate
    return None

# 1. Define the schema
class DeweyResponse(BaseModel):
    ddc: str  # This will be our Dewey number or "Unknown"

def lookup_dewey_v2(isbn, title, author):
    # 2. Use a System Message for clear rules
    system_prompt = (
        "You are a professional library cataloger. "
        "Return the most accurate Dewey Decimal Classification (DDC) number "
        "for the provided book. If you cannot determine it, return 'Unknown'."
    )
    
    user_prompt = f"ISBN: {isbn}, Title: {title}, Author: {author}"

    # 3. Use 'response_format' with 'strict=True'
    completion = openai_client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format=DeweyResponse,
    )

    # 4. Access the parsed object directly
    return completion.choices[0].message.parsed.ddc

def lookup_dewey(isbn, title, author):
    prompt = f"Determine the Dewey Decimal Classification (DDC) for: ISBN: {isbn}, Title: {title}, Author: {author}. Return ONLY the number or 'Unknown'."
    res = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return res.choices[0].message.content.strip()

def get_en_book_details_from_isbn(isbn):
    url = f"https://openlibrary.org/api/books?bibkeys=ISBN:{isbn}&format=json&jscmd=data"
    try:
        response = requests.get(url, timeout=5)
        data = response.json()
        key = f"ISBN:{isbn}"

        if key in data:
            title = data[key].get("title", None)
            author = None
            publisher = None
            publish_date = None

            authors = data[key].get("authors", [])
            if authors:
                author = authors[0].get("name")

            publishers = data[key].get("publishers", [])
            if publishers:
                publisher = publishers[0].get("name")

            publish_date = data[key].get("publish_date", None)

            return {"title": title, "author": author, "publisher": publisher, "publish_date": publish_date}
    except:
        pass
    return None

if "last_isbn" in st.session_state and st.session_state.last_isbn:
    # Clean the input (some scanners add prefixes/suffixes)
    isbn = st.session_state.last_isbn
    st.success(f"ISBN Detected: {isbn}")
    
    meta = None
    with st.spinner(f"🔍 Processing {isbn}..."):
        # Priority 1: English (OpenLibrary)
        res_en_book = get_en_book_details_from_isbn(isbn)
        if res_en_book:
            meta = {
                "ISBN": isbn,
                "Author": res_en_book["author"],
                "Title": res_en_book["title"],
                "Publisher": res_en_book["publisher"],
                "Publish_date": res_en_book["publish_date"],
                "Dewey": lookup_dewey_v2(isbn, res_en_book["title"], res_en_book["author"])
            }
        
        # Priority 2: Traditional Chinese
        if not meta:
            res_trad = get_traditional_book_details(isbn)
            if res_trad and res_trad.get("author") != "Unknown":
                meta = {
                    "ISBN": isbn,
                    "Author": res_trad["author"],
                    "Title": res_trad["title"],
                    "Publisher": res_trad["publisher"],
                    "Publish_date": res_trad["publish_date"],
                    "Dewey": lookup_dewey_v2(isbn, res_trad["title"], res_trad["author"])
                }

        # Priority 3: Simplified Chinese
        if not meta:
            res_sim = get_sim_book_details(isbn)
            if res_sim and res_sim.get("author") != "Unknown":
                meta = {
                    "ISBN": isbn,
                    "Author": res_sim["author"],
                    "Title": res_sim["title"],
                    "Publisher": res_sim["publisher"],
                    "Publish_date": res_sim["publish_date"],
                    "Dewey": lookup_dewey_v2(isbn, res_sim["title"], res_sim["author"])
                }

        if meta:
            st.json(meta)
            st.session_state.last_meta = meta
        else:
            st.warning("No book information found in any database.")

    # Clear the last_isbn so it doesn't re-run the API call on every refresh
    st.session_state.last_isbn = None

# ---- THE COPY SECTION ----
if st.session_state.last_meta:
    m = st.session_state.last_meta
    st.success(f"Scanned: {m['Title']}")
    
    # Create a Tab-Separated string (Google Sheets standard for pasting into rows)
    # Format: Title [TAB] Author [TAB] ISBN [TAB] Publisher [TAB] Dewey
    sheet_row = f"{m['Title']}\t{m['Author']}\t{m['ISBN']}\t{m['Publisher']}\t{m['Dewey']}\t{m['Publish_date']}"

    # Show the data and the copy button
    col1, col2 = st.columns([3, 1])
    with col1:
        st.code(sheet_row, language=None)
    with col2:
        st_copy_to_clipboard(sheet_row)