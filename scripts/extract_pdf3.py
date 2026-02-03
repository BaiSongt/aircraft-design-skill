#!/usr/bin/env python3
import subprocess
import os

def extract_pdf_with_pdftotext(pdf_path):
    """使用pdftotext工具提取PDF文本"""
    try:
        output_path = pdf_path.replace('.pdf', '.txt')
        result = subprocess.run(['pdftotext', pdf_path, output_path], 
                          capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # 读取提取的文本
            with open(output_path, 'r', encoding='utf-8') as f:
                text = f.read()
            return text, output_path
        else:
            print(f"Error: pdftotext failed with return code {result.returncode}")
            print(f"stderr: {result.stderr}")
            return None, None
    except FileNotFoundError:
        print("Error: pdftotext command not found")
        return None, None
    except Exception as e:
        print(f"Error: {e}")
        return None, None

if __name__ == '__main__':
    pdf_files = [
        '/Users/baisongtao/mycode/aircraft-design-skill/docs/book/250938.pdf',
        '/Users/baisongtao/mycode/aircraft-design-skill/docs/book/ae_405.pdf',
        '/Users/baisongtao/mycode/aircraft-design-skill/docs/book/AircraftDynamicsModel.pdf'
    ]
    
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            print(f"Processing: {pdf_path}")
            text, output_path = extract_pdf_with_pdftotext(pdf_path)
            
            if text is not None:
                print(f"Extracted to: {output_path}")
                print(f"Text length: {len(text)} characters")
            else:
                print(f"Failed to extract: {pdf_path}")
        else:
            print(f"File not found: {pdf_path}")
    
    print("\nAll PDFs processed!")
