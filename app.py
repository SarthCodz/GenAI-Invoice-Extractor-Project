#import features from the required libraries
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
import json
import datetime 
import os
import csv

#Setting Up UI for the IDP Application
st.set_page_config(page_title="Vendor Invoice Extractor", page_icon=":receipt:", layout="centered")
st.title("Vendor Invoice Extractor")
st.caption("Upload a vendor invoice (PDF or text) to extract structured data.")
st.divider()

#Looks for Gemini API Key and creates a client object to interact with the API
load_dotenv()
client = genai.Client()

# FIXED SCHEMA — Trimmed down to only the requested base fields-->Response is generated in same manner
INVOICE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vendor": {"type": "STRING"},
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "model_name": {"type": "STRING"},
                    "count": {"type": "INTEGER"},
                    "total_amount": {"type": "NUMBER"},
                },
                "required": ["model_name", "count", "total_amount"],
            },
        },
    },
    "required": ["vendor", "items"],
}

#Instructions for the AI prompt
EXTRACTION_INSTRUCTION = (
    "You are an invoice data extraction assistant. "
    "Extract only the vendor name, model name, count of pieces, and total amount exactly as they appear in the document. "
    "If a field is missing, use an empty string or 0. Do not guess values that are not present."
)

#Content generation by AI based on schema and instructions in JSON format
def extract_invoice(file_bytes, mime_type):
    config = types.GenerateContentConfig(
        system_instruction=EXTRACTION_INSTRUCTION,
        response_mime_type="application/json",
        response_schema=INVOICE_SCHEMA
    )
#Content sent to the API for processing 
    file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[file_part],
        config=config
    )
#Converts returned JSON string into a Python dictionary for further processing
    return json.loads(response.text)

#Function to save extracted data into a CSV file for record-keeping
def save_to_csv(data):
    file_exists = os.path.isfile("extracted_invoices.csv")

    with open("extracted_invoices.csv", "a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(["timestamp", "vendor", "model_name", "count", "total_amount"])

        for item in data["items"]:
            timestamp = datetime.now().isoformat()
            mod_name = item["model_name"]
            count = item["count"]
            tot = item["total_amount"]
            writer.writerow([timestamp, data["vendor"], mod_name, count, tot])


#File Handling and UI for file upload and extraction
uploaded_file = st.file_uploader("Upload vendor invoice", type=["txt", "pdf"])

if uploaded_file is not None:
    if st.button("Extract Invoice Data"):
        with st.spinner("Extracting..."):
            file_bytes = uploaded_file.read()
            mime_type = uploaded_file.type or "text/plain"
            st.session_state["extracted"] = extract_invoice(file_bytes, mime_type)

if "extracted" in st.session_state:
    data = st.session_state["extracted"]
    st.subheader("Extracted Data Schema Output")
    
    # Displays the clean JSON output in the UI
    st.json(data)
    #Button to save data into CSV file for record-keeping
    if st.button("Save Record"):
        save_to_csv(data)
        st.success("Saved to extracted_invoices.csv")