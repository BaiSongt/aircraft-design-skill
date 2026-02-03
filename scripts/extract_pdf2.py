#!/usr/bin/env python3
import sys
try:
    import fitz  # PyMuPDF
    import os

    def extract_text_from_pdf(pdf_path):
        """从PDF文件中提取文本"""
        text_content = []
        
        try:
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            
            for page_num in range(num_pages):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_content.append(f"=== Page {page_num + 1} ===\n{text}")
            
            doc.close()
                
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return []
        
        return text_content

    if __name__ == '__main__':
        pdf_files = [
            '/Users/baisongtao/mycode/aircraft-design-skill/docs/book/250938.pdf',
            '/Users/baisongtao/mycode/aircraft-design-skill/docs/book/ae_405.pdf',
            '/Users/baisongtao/mycode/aircraft-design-skill/docs/book/AircraftDynamicsModel.pdf'
        ]
        
        for pdf_path in pdf_files:
            if os.path.exists(pdf_path):
                print(f"Processing: {pdf_path}")
                text_content = extract_text_from_pdf(pdf_path)
                
                # 输出到文件
                base_name = os.path.basename(pdf_path)
                output_path = pdf_path.replace('.pdf', '.txt')
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(text_content))
                
                print(f"Extracted {len(text_content)} pages to: {output_path}")
            else:
                print(f"File not found: {pdf_path}")
        
        print("\nAll PDFs processed successfully!")

except ImportError:
    print("Error: PyMuPDF module not installed")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
