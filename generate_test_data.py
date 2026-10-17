import json
import os

# Diverse dummy vendors and items for realistic variation
vendors = [
    "TechCorp Supplies", 
    "Global Hardware Inc.", 
    "Apex Systems", 
    "ByteWave Solutions", 
    "Nexus Parts Co."
]
models = [
    "Alpha-X Router", 
    "Beta-Core Switch", 
    "Gamma-Drive SSD", 
    "Delta-Node Cable", 
    "Omega-Display Panel"
]

os.makedirs("test_invoices", exist_ok=True)
os.makedirs("labels", exist_ok=True)

print("Generating 20 diverse test invoice datasets...")

for i in range(1, 21):
    invoice_id = f"invoice_{i:03d}"
    vendor = vendors[i % len(vendors)]
    model_name = models[i % len(models)]
    count = (i * 3) % 12 + 1
    unit_price = 45.50 + (i * 8.25)
    total_amount = round(count * unit_price, 2)
    
    # Text format matching your invoice structure
    invoice_text = f"""
    INVOICE #{1000 + i}
    Vendor: {vendor}
    Date: 2026-10-{i%28 + 1:02d}
    
    Line Items:
    - {model_name} | Quantity: {count} | Total Amount: ${total_amount}
    
    Terms: Net 30. Thank you for your business!
    """
    
    # Ground truth JSON label matching your INVOICE_SCHEMA
    label_data = {
        "vendor": vendor,
        "items": [
            {
                "model_name": model_name,
                "count": count,
                "total_amount": total_amount
            }
        ]
    }
    
    # Save text invoice and JSON label
    with open(f"test_invoices/{invoice_id}.txt", "w", encoding="utf-8") as f:
        f.write(invoice_text.strip())
        
    with open(f"labels/{invoice_id}.json", "w", encoding="utf-8") as f:
        json.dump(label_data, f, indent=4)

print("Successfully generated 20 test invoices and labels!")