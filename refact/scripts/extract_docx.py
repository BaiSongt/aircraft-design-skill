#!/usr/bin/env python3
import zipfile
import xml.etree.ElementTree as ET


def extract_text_from_docx(docx_path):
    """从docx文件中提取文本"""
    text_content = []

    try:
        with zipfile.ZipFile(docx_path, "r") as zip_ref:
            # 读取document.xml
            xml_content = zip_ref.read("word/document.xml")

            # 解析XML
            root = ET.fromstring(xml_content)

            # 定义命名空间
            namespaces = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}

            # 提取段落文本
            for para in root.findall(".//w:p", namespaces):
                para_text = []
                for text_node in para.findall(".//w:t", namespaces):
                    if text_node.text:
                        para_text.append(text_node.text)

                if para_text:
                    text_content.append("".join(para_text))

            # 提取表格
            for table in root.findall(".//w:tbl", namespaces):
                text_content.append("\n[表格开始]")
                for row in table.findall(".//w:tr", namespaces):
                    row_text = []
                    for cell in row.findall(".//w:tc", namespaces):
                        cell_text = []
                        for text_node in cell.findall(".//w:t", namespaces):
                            if text_node.text:
                                cell_text.append(text_node.text)
                        row_text.append("".join(cell_text))
                    text_content.append(" | ".join(row_text))
                text_content.append("[表格结束]\n")

    except Exception as e:
        print(f"解析错误: {e}")
        return []

    return text_content


if __name__ == "__main__":
    docx_path = "/Users/baisongtao/mycode/aircraft-design-skill/docs/飞机设计文件.docx"

    text_content = extract_text_from_docx(docx_path)

    # 输出到文件
    output_path = "/Users/baisongtao/mycode/aircraft-design-skill/docs/飞机设计文件.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(text_content))

    print(f"文档内容已提取到: {output_path}")
    print(f"共提取 {len(text_content)} 行内容")
