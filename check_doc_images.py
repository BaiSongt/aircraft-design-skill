import os
import re
import sys

def check_images(markdown_file):
    if not os.path.exists(markdown_file):
        print(f"Error: File {markdown_file} not found.")
        return False

    with open(markdown_file, 'r') as f:
        content = f.read()

    # Regex to find images: ![alt text](path/to/image)
    # Also handles optional title: ![alt text](path/to/image "title")
    image_pattern = re.compile(r'!\[.*?\]\((.*?)(?:\s+".*?")?\)')
    
    matches = image_pattern.findall(content)
    
    print(f"Checking images in {markdown_file}...")
    
    missing_count = 0
    found_count = 0
    
    for img_path in matches:
        # Resolve relative paths
        # Assume paths are relative to the markdown file location
        base_dir = os.path.dirname(os.path.abspath(markdown_file))
        full_path = os.path.join(base_dir, img_path)
        
        if os.path.exists(full_path):
            print(f"[OK] {img_path}")
            found_count += 1
        else:
            print(f"[MISSING] {img_path}")
            missing_count += 1
            
    print("-" * 30)
    print(f"Summary: Found {found_count}, Missing {missing_count}")
    
    return missing_count == 0

if __name__ == "__main__":
    md_file = "technical_roadmap_report.md"
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
        
    success = check_images(md_file)
    sys.exit(0 if success else 1)
