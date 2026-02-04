import os
import requests
from urllib.parse import urlparse

# Create folder if it doesn't exist
os.makedirs("raw_documents", exist_ok=True)

# List of URLs to download
urls = [
    # Add your URLs here
    # "https://example.com/document1.pdf",
    # "https://example.com/document2.pdf",
]

for url in urls:
    try:
        # Extract filename from URL
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # Add .pdf extension if not present
        if not filename.endswith('.pdf'):
            filename += '.pdf'
        
        filepath = os.path.join("raw_documents", filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            print(f"Skipped: {filename} (already exists)")
            continue
        
        # Download the file
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Save the file
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        print(f"Downloaded: {filename}")
    
    except Exception as e:
        print(f"Error downloading {url}: {e}")
