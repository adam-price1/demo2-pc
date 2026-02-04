import os
import json
import shutil
import re
from datetime import datetime

# ========== STATUS LIFECYCLE ==========
# needs_review → classified → organized
# This ensures proper workflow tracking and audit trail
# =======================================

# Folders
raw_docs_folder = "raw_documents"
metadata_folder = "metadata"
policies_folder = "policies"

# Create policies folder if it doesn't exist
os.makedirs(policies_folder, exist_ok=True)

# PHASE 2: Safe Text Cleaning Function
def clean_text(value):
    """
    Safe text cleaning for filenames and folder names
    - Replace spaces with underscores
    - Remove special characters that break paths
    - Keep alphanumeric, underscores, and hyphens only
    """
    if not value:
        return "Unknown"
    value = str(value).strip()
    value = value.replace(' ', '_')
    # Remove any character that's not alphanumeric, underscore, or hyphen
    value = re.sub(r'[^A-Za-z0-9_-]', '', value)
    return value if value else "Unknown"

# PHASE 2: Helper functions
def build_filename(metadata):
    """
    Generate production-clean structured filename from metadata
    Format: {country}_{insurer}_{line}_{product}.pdf
    """
    country = clean_text(metadata.get("country", "Unknown"))
    insurer = clean_text(metadata.get("insurer", "Unknown"))
    line = clean_text(metadata.get("insurance_line", "Unknown"))
    product = clean_text(metadata.get("product_name", "Unknown"))
    
    return f"{country}_{insurer}_{line}_{product}.pdf"

# Check if metadata folder exists
if not os.path.exists(metadata_folder):
    print(f"Error: {metadata_folder} folder not found")
else:
    organized_count = 0
    skipped_count = 0
    total_size = 0

    # Process each metadata file
    for filename in os.listdir(metadata_folder):
        if not filename.lower().endswith('.json'):
            continue
        
        metadata_filepath = os.path.join(metadata_folder, filename)
        
        # Read metadata
        try:
            with open(metadata_filepath, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"❌ Error reading {filename}: {e}")
            continue
        
        # PHASE 2: Safety check - ensure original_filename exists
        original_filename = metadata.get("original_filename")
        if not original_filename:
            print(f"❌ Missing original_filename in metadata: {filename}")
            skipped_count += 1
            continue
        
        # Status lifecycle check: needs_review → classified → organized
        status = metadata.get("status", "unknown")
        if status != "classified":
            print(f"⏭️  Skipped: {original_filename} (status: {status})")
            skipped_count += 1
            continue
        
        # Check if any required field is "Unknown"
        required_fields = ["country", "insurer", "insurance_line", "product_name"]
        has_unknown = False
        
        for field in required_fields:
            if metadata.get(field) == "Unknown":
                print(f"⏭️  Skipped: {original_filename} ({field} is 'Unknown')")
                has_unknown = True
                skipped_count += 1
                break
        
        if has_unknown:
            continue
        
        # PHASE 2: Build folder path with safe text cleaning
        country = clean_text(metadata.get("country", ""))
        insurer = clean_text(metadata.get("insurer", ""))
        insurance_line = clean_text(metadata.get("insurance_line", ""))
        product_name = clean_text(metadata.get("product_name", ""))
        
        folder_path = os.path.join(
            policies_folder,
            country,
            insurer,
            insurance_line,
            product_name
        )
        
        # Create folder structure
        try:
            os.makedirs(folder_path, exist_ok=True)
        except Exception as e:
            print(f"❌ Error creating folder {folder_path}: {e}")
            skipped_count += 1
            continue
        
        # PHASE 2: Get original filename and generate structured name
        generated_filename = build_filename(metadata)
        
        src_filepath = os.path.join(raw_docs_folder, original_filename)
        dst_filepath = os.path.join(folder_path, generated_filename)
        
        try:
            if os.path.exists(src_filepath):
                file_size = os.path.getsize(src_filepath)
                shutil.move(src_filepath, dst_filepath)
                total_size += file_size
                
                print(f"✅ Organized: {original_filename}")
                print(f"   ├─ Renamed to: {generated_filename}")
                print(f"   ├─ Type: {metadata.get('document_type', 'Unknown')}")
                print(f"   ├─ Confidence: {metadata.get('confidence', 'Unknown')}")
                print(f"   └─ Location: {folder_path}/")
                organized_count += 1
                
                # PHASE 2: Update metadata with final status and ISO date format
                metadata["generated_filename"] = generated_filename
                metadata["status"] = "organized"
                metadata["organized_date"] = datetime.now().isoformat()
                
                with open(metadata_filepath, 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                print(f"   📝 Metadata updated (status: organized)\n")
                
            else:
                print(f"❌ Error: {original_filename} (PDF file not found in {raw_docs_folder})")
                skipped_count += 1
        except Exception as e:
            print(f"❌ Error organizing {original_filename}: {e}")
            skipped_count += 1

    # PHASE 2: Production summary
    print("\n" + "="*60)
    print("📊 PHASE 2 ORGANIZATION SUMMARY")
    print("="*60)
    print(f"✅ Organized: {organized_count} files")
    print(f"⏭️  Skipped: {skipped_count} files")
    print(f"📦 Total Size: {total_size / (1024*1024):.2f} MB")
    print(f"📁 Base Path: {policies_folder}/")
    print(f"🔄 Status Lifecycle: needs_review → classified → organized")
    print("="*60 + "\n")

