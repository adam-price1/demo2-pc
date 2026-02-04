import os
import json
from datetime import date
import re

# ========== STATUS LIFECYCLE ==========
# needs_review → classified → organized
# This ensures proper workflow tracking and audit trail
# =======================================

# Create metadata folder if it doesn't exist
os.makedirs("metadata", exist_ok=True)

# Get today's date
today = date.today().isoformat()

# PHASE 2.5: Known Insurer Dictionary (NZ, AU, UK)
KNOWN_INSURERS = [
    'AMI',
    'AA Insurance',
    'State Insurance',
    'Tower',
    'AIA',
    'Southern Cross',
    'Vero',
    'FMG',
    'NZI',
    'NRMA',
    'Suncorp',
    'AXA',
    'Aviva',
    'Direct Line',
    'Bupa',
    'QBE',
    'Argis',
    'BIA',
    'Castle',
    'Allianz',
    'IAG'
]

# PHASE 2.5: Safe Text Cleaning Function
def clean_text(value):
    """
    Safe text cleaning for filenames and folder names
    """
    if not value:
        return "Unknown"
    value = str(value).strip()
    value = value.replace(' ', '_')
    value = re.sub(r'[^A-Za-z0-9_-]', '', value)
    return value if value else "Unknown"

# ===== FIX 1: INSURER DETECTION (TOP OF DOCUMENT ONLY) =====
def detect_insurer(text):
    """
    Only check first 2000 chars (cover page).
    Prevents legal fine-print from hijacking classification.
    """
    first_section = text[:2000].upper()
    
    for insurer in KNOWN_INSURERS:
        if insurer.upper() in first_section:
            return insurer
    
    return "Unknown"

# ===== FIX 2: IMPROVED INSURANCE LINE DETECTION =====
def detect_line(text):
    """
    Selective line detection with priority order.
    Checks most specific types first.
    """
    t = text.lower()
    
    # Check in priority order (most specific first)
    if any(word in t for word in ["professional indemnity", "pi insurance", "professional liability", "accountants liability"]):
        return "Professional Indemnity"
    
    if any(word in t for word in ["farm insurance", "agricultural", "farming", "rural property"]):
        return "Farm"
    
    if any(word in t for word in ["landlord", "rental property", "investment property", "residential landlord"]):
        return "Landlord"
    
    if any(word in t for word in ["construction", "builders indemnity", "contract works", "building project"]):
        return "Construction"
    
    if any(word in t for word in ["car insurance", "motor", "vehicle insurance", "auto insurance"]):
        return "Motor"
    
    if any(word in t for word in ["life insurance", "life cover", "life protection"]):
        return "Life"
    
    if any(word in t for word in ["health insurance", "medical insurance", "health cover"]):
        return "Health"
    
    if any(word in t for word in ["home insurance", "contents insurance", "house insurance", "home & contents"]):
        return "Home & Contents"
    
    if any(word in t for word in ["travel insurance", "trip insurance", "travel cover"]):
        return "Travel"
    
    return "Unknown"

# ===== FIX 3: PRODUCT NAME FROM TITLE TEXT =====
def detect_product_name(text):
    """
    Extract product name from title-like text in top 30 lines.
    Looks for lines that contain policy-related keywords.
    """
    lines = text.split('\n')[:30]  # Top of document only
    
    for line in lines:
        trimmed = line.strip()
        # Look for title-like text: reasonable length, contains insurance keywords
        if 10 < len(trimmed) < 100 and not trimmed.startswith('www'):
            if any(keyword in trimmed.lower() for keyword in ['policy', 'insurance', 'wording', 'cover']):
                return trimmed
    
    return "General Policy"

def detect_country(text):
    """Detect country from text"""
    t = text.lower()
    
    if any(word in t for word in ["new zealand", "nz ", " nz", "auckland", "wellington"]):
        return "New Zealand"
    if any(word in t for word in ["australia", " au ", "sydney", "melbourne"]):
        return "Australia"
    if any(word in t for word in ["united kingdom", "uk ", " uk", "england", "scotland"]):
        return "United Kingdom"
    
    return "Unknown"

def build_filename(meta):
    """
    Production-clean filename builder with safe text cleaning
    """
    country = clean_text(meta['country'])
    insurer = clean_text(meta['insurer'])
    line = clean_text(meta['insurance_line'])
    product = clean_text(meta['product_name'])
    
    return f"{country}_{insurer}_{line}_{product}.pdf"

# Scan raw_documents folder
raw_docs_folder = "raw_documents"

if not os.path.exists(raw_docs_folder):
    print(f"Error: {raw_docs_folder} folder not found")
else:
    file_count = 0
    
    for filename in os.listdir(raw_docs_folder):
        filepath = os.path.join(raw_docs_folder, filename)
        
        # Only process PDF files
        if not filename.lower().endswith('.pdf') or not os.path.isfile(filepath):
            continue
        
        file_count += 1
        
        # PHASE 2.5: Mock text extraction (simulate diverse policy types)
        # In production, use PyPDF2 or pdfplumber to extract actual text
        mock_texts = [
            f"""Professional Indemnity Insurance Policy
            BIA Accountants
            This policy provides professional liability cover for accountants.
            Professional indemnity insurance with accountant specific covers.
            {filename}""",
            
            f"""Farm Extra Insurance
            Argis Insurance
            Agricultural and farming insurance policy.
            Covers farm buildings, rural property, and agricultural equipment.
            {filename}""",
            
            f"""Residential Landlord Policy
            Castle Insurance
            Landlord and rental property insurance.
            Investment property landlord cover for residential properties.
            {filename}""",
            
            f"""Construction Indemnity Cover
            AMI Building
            Contract works and builders indemnity.
            Construction and building project insurance protection.
            {filename}""",
            
            f"""Car Insurance – Policy Wording
            AMI Limited
            Motor vehicle insurance policy for New Zealand.
            Car insurance with comprehensive vehicle cover options.
            {filename}"""
        ]
        
        # Rotate through mock texts
        mock_text = mock_texts[file_count % len(mock_texts)]
        
        # PHASE 2.5: Detect with selective logic (fixes applied)
        country = detect_country(mock_text)
        insurer = detect_insurer(mock_text)  # FIX 1: Top 2000 chars only
        line = detect_line(mock_text)  # FIX 2: Priority-ordered detection
        product = detect_product_name(mock_text)  # FIX 3: Title text extraction
        
        # Determine document type
        document_type = "Policy Wording" if "Wording" in product else "Policy Document"
        
        # High confidence if all fields populated
        is_high_confidence = (country != "Unknown" and insurer != "Unknown" and line != "Unknown")
        confidence = "High" if is_high_confidence else "Medium"
        
        # Generate structured filename
        generated_filename = build_filename({
            'country': country,
            'insurer': insurer,
            'insurance_line': line,
            'product_name': product
        })
        
        # PHASE 2.5: Production-clean metadata structure
        metadata = {
            "original_filename": filename,
            "generated_filename": generated_filename,
            "country": country,
            "insurer": insurer,
            "insurance_line": line,
            "product_name": product,
            "document_type": document_type,
            "source_url": "local_upload",
            "download_date": today,
            "confidence": confidence,
            "status": "needs_review",  # Status lifecycle starts here
            "created_at": date.today().isoformat()
        }
        
        # Create JSON filename
        json_filename = os.path.splitext(filename)[0] + ".json"
        json_filepath = os.path.join("metadata", json_filename)
        
        # Write JSON file
        with open(json_filepath, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Created: {json_filename}")
        print(f"   ├─ Country: {country}")
        print(f"   ├─ Insurer: {insurer}")
        print(f"   ├─ Line: {line}")
        print(f"   ├─ Product: {product}")
        print(f"   ├─ Type: {document_type}")
        print(f"   ├─ Confidence: {confidence}")
        print(f"   └─ Generated: {generated_filename}\n")
