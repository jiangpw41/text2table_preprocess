def read_docx(file_path ):
    from docx import Document 
    doc = Document(file_path)  
    full_text = []  
    for para in doc.paragraphs:  
        full_text.append(para.text)  
    return '\n'.join(full_text)