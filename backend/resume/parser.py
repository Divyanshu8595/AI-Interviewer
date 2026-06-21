import re, fitz, pdfplumber
from docx import Document
MAX_SIZE=20*1024*1024
SKILL_HINTS={'python','typescript','react','next.js','fastapi','sql','sqlite','docker','git','java','c++','aws','linux','flutter'}
def clean_text(text:str)->str: return re.sub(r'\s+',' ', text.replace('\x00',' ')).strip()[:60000]
def extract_text(path:str, filename:str)->str:
    if filename.lower().endswith('.pdf'):
        text=''
        with fitz.open(path) as doc: text='\n'.join(page.get_text() for page in doc)
        if len(text.strip())<100:
            with pdfplumber.open(path) as pdf: text='\n'.join((p.extract_text() or '') for p in pdf.pages)
        return clean_text(text)
    if filename.lower().endswith('.docx'):
        return clean_text('\n'.join(p.text for p in Document(path).paragraphs))
    raise ValueError('Only PDF and DOCX resumes are supported')
def structure_resume(text:str)->dict:
    lines=[l.strip() for l in re.split(r'[\n\r]+| {2,}', text) if l.strip()]
    name=lines[0][:80] if lines else ''
    lower=text.lower(); skills=sorted({s for s in SKILL_HINTS if s in lower})
    def section(title):
        m=re.search(title+r'(.{0,1200})', text, re.I|re.S); return [clean_text(m.group(1))[:800]] if m else []
    return {'name':name,'skills':skills,'projects':section('projects?'),'experience':section('experience'),'education':section('education'),'certifications':section('certifications?')}
