import json, logging, os, tempfile
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.database.models import Answer, Interview, Question, Report, Resume, get_db, init_db
from backend.resume.parser import MAX_SIZE, extract_text, structure_resume
from backend.resume.vector_store import index_resume, retrieve
from backend.interview.engine import generate_question
from backend.evaluation.engine import evaluate_answer
from backend.report.generator import build_report
logging.basicConfig(level=logging.INFO); app=FastAPI(title='Local AI Interviewer')
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:3000'], allow_methods=['*'], allow_headers=['*'])
@app.on_event('startup')
def startup(): init_db(); os.makedirs('uploads', exist_ok=True)
@app.get('/health')
def health(): return {'ok':True,'local_only':True}
@app.post('/resumes/upload')
async def upload_resume(file:UploadFile=File(...), db:Session=Depends(get_db)):
    if not file.filename.lower().endswith(('.pdf','.docx')): raise HTTPException(400,'Only PDF and DOCX allowed')
    data=await file.read(MAX_SIZE+1)
    if len(data)>MAX_SIZE: raise HTTPException(413,'Resume must be 20MB or smaller')
    suffix=os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as tmp: tmp.write(data); path=tmp.name
    text=extract_text(path,file.filename); structured=structure_resume(text)
    resume=Resume(filename=file.filename, raw_text=text, structured=structured); db.add(resume); db.commit(); db.refresh(resume); index_resume(resume.id, structured)
    return {'resume_id':resume.id,'structured':structured}
@app.post('/interviews')
async def create_interview(resume_id:int=Form(...), company:str=Form(...), role:str=Form(...), difficulty:str=Form('Intermediate'), db:Session=Depends(get_db)):
    interview=Interview(resume_id=resume_id,company=company,role=role,difficulty=difficulty,memory={'asked_questions':[],'answers':[],'covered_topics':[],'strengths':[],'weaknesses':[]}); db.add(interview); db.commit(); db.refresh(interview); return {'interview_id':interview.id}
@app.websocket('/interviews/ws/{interview_id}')
async def interview_ws(ws:WebSocket, interview_id:str):
    await ws.accept(); memory={'asked_questions':[],'answers':[],'covered_topics':[],'strengths':[],'weaknesses':[]}; question='Tell me about your most relevant project.'; await ws.send_text(json.dumps({'speaker':'ai','text':question}))
    while True:
        msg=json.loads(await ws.receive_text()); answer=msg.get('text',''); memory['answers'].append(answer); evaluation=evaluate_answer(question, answer); next_q=await generate_question(memory,[answer],'Target Company','Target Role','Intermediate'); memory['asked_questions'].append(next_q); await ws.send_text(json.dumps({'speaker':'user','text':answer,'evaluation_stored':bool(evaluation)})); await ws.send_text(json.dumps({'speaker':'ai','text':next_q})); question=next_q
@app.post('/reports/{interview_id}')
def report(interview_id:int, db:Session=Depends(get_db)):
    content=build_report([]); r=Report(interview_id=interview_id,content=content,overall_score=content['overall_score']); db.add(r); db.commit(); return content
