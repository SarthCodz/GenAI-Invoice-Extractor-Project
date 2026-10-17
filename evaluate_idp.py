import os
import glob
import json
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()

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

EXTRACTION_INSTRUCTION = (
    "You are an invoice data extraction assistant. "
    "Extract only the vendor name, model name, count of pieces, and total amount exactly as they appear in the document. "
    "If a field is missing, use an empty string or 0. Do not guess values that are not present."
)

def extract_with_retry(file_path, max_retries=3):
    mime_type = "application/pdf" if file_path.lower().endswith('.pdf') else "text/plain"
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    file_part = types.Part.from_bytes(data=file_bytes, mime_type=mime_type)
    
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[file_part],
                config=types.GenerateContentConfig(
                    system_instruction=EXTRACTION_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=INVOICE_SCHEMA
                )
            )
            return json.loads(response.text)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            # Exponential backoff with random jitter (1s, 2s, 4s...)
            wait_time = (2 ** attempt) + random.uniform(0, 1)
            time.sleep(wait_time)

def run_evaluation(invoices_dir="test_invoices", labels_dir="labels"):
    invoice_files = glob.glob(os.path.join(invoices_dir, "*.*"))
    invoice_files = [f for f in invoice_files if not os.path.basename(f).startswith(".")]

    total_fields = 0
    correct_fields = 0
    results = []

    print(f"Starting IDP evaluation on {len(invoice_files)} sample invoices...\n")

    for file_path in invoice_files:
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        label_file = os.path.join(labels_dir, f"{base_name}.json")

        if not os.path.exists(label_file):
            continue

        with open(label_file, "r", encoding="utf-8") as f:
            ground_truth = json.load(f)

        try:
            extracted = extract_with_retry(file_path)
        except Exception as e:
            print(f"❌ API Error on {base_name}: {e}")
            continue

        file_total = 0
        file_correct = 0

        # Vendor matching
        gt_vendor = str(ground_truth.get("vendor", "")).strip().lower()
        ex_vendor = str(extracted.get("vendor", "")).strip().lower()
        file_total += 1
        if gt_vendor == ex_vendor:
            file_correct += 1

        # Items matching
        gt_items = ground_truth.get("items", [])
        ex_items = extracted.get("items", [])

        for i, gt_item in enumerate(gt_items):
            ex_item = ex_items[i] if i < len(ex_items) else {}
            
            for field in ["model_name", "count", "total_amount"]:
                file_total += 1
                gt_val = str(gt_item.get(field, "")).strip().lower()
                ex_val = str(ex_item.get(field, "")).strip().lower()
                if gt_val == ex_val:
                    file_correct += 1

        total_fields += file_total
        correct_fields += file_correct
        acc = (file_correct / file_total * 100) if file_total > 0 else 0
        print(f"✅ {base_name}: {file_correct}/{file_total} fields matched ({acc:.1f}%)")

        results.append({"filename": base_name, "accuracy": acc})

    overall_accuracy = (correct_fields / total_fields * 100) if total_fields > 0 else 0
    
    print("\n==========================================")
    print("📊 OVERALL IDP BENCHMARK RESULTS FOR RESUME:")
    print(f"   - Total Files Processed: {len(results)}")
    print(f"   - Total Data Fields Checked: {total_fields}")
    print(f"   - Correctly Extracted Fields: {correct_fields}")
    print(f"   - Field Extraction Accuracy: {overall_accuracy:.2f}%")
    print("==========================================")

if __name__ == "__main__":
    run_evaluation()