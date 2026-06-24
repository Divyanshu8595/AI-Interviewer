import base64, json, logging, os, tempfile
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from backend.database.models import Answer, Interview, Question, Report, Resume, SessionLocal, get_db, init_db
from backend.resume.parser import MAX_SIZE, extract_text, structure_resume
from backend.resume.vector_store import index_resume, retrieve
from backend.interview.engine import generate_question
from backend.evaluation.engine import evaluate_answer
from backend.report.generator import build_report
from backend.voice.pipeline import voice_pipeline
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
async def interview_ws(ws: WebSocket, interview_id: int):
    await ws.accept()
    db = SessionLocal()
    try:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            await ws.close(code=4004)
            return
        resume = db.query(Resume).filter(Resume.id == interview.resume_id).first()
        memory = interview.memory or {'asked_questions':[],'answers':[],'covered_topics':[],'strengths':[],'weaknesses':[]}

        initial_q = "Tell me about your most relevant project."
        q_obj = Question(interview_id=interview.id, text=initial_q, category='Introduction')
        db.add(q_obj); db.commit(); db.refresh(q_obj)

        memory['asked_questions'].append(initial_q)
        interview.memory = memory
        db.commit()

        await ws.send_text(json.dumps({'speaker': 'ai', 'text': initial_q}))
        current_q_id = q_obj.id
        current_q_text = initial_q

        while True:
            data = await ws.receive()
            if "bytes" in data:
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
                    f.write(data["bytes"])
                    f_path = f.name
                user_text = voice_pipeline.transcribe(f_path)
                os.remove(f_path)
            elif "text" in data:
                msg = json.loads(data["text"])
                user_text = msg.get('text', '')
            else:
                continue

            evaluation = await evaluate_answer(current_q_text, user_text)
            ans_obj = Answer(question_id=current_q_id, transcript=user_text, evaluation=evaluation, score=evaluation.get('relevance', 0))
            db.add(ans_obj); db.commit()

            context = retrieve(resume.id, user_text)
            next_q = await generate_question(memory, context, interview.company, interview.role, interview.difficulty)

            next_q_obj = Question(interview_id=interview.id, text=next_q, category='Technical')
            db.add(next_q_obj); db.commit(); db.refresh(next_q_obj)

            memory['answers'].append(user_text)
            memory['asked_questions'].append(next_q)
            interview.memory = memory
            db.add(interview); db.commit()

            await ws.send_text(json.dumps({'speaker': 'user', 'text': user_text, 'evaluation': evaluation}))

            # Generate AI Audio
            audio_response = voice_pipeline.synthesize(next_q)
            if audio_response:
                await ws.send_text(json.dumps({
                    'speaker': 'ai',
                    'text': next_q,
                    'audio': base64.b64encode(audio_response).decode('utf-8')
                }))
            else:
                await ws.send_text(json.dumps({'speaker': 'ai', 'text': next_q}))

            current_q_id = next_q_obj.id
            current_q_text = next_q
    except Exception as e:
        logging.error(f"WebSocket error: {e}")
    finally:
        db.close()

@app.post('/reports/{interview_id}')
def report(interview_id:int, db:Session=Depends(get_db)):
    questions = db.query(Question).filter(Question.interview_id == interview_id).all()
    q_ids = [q.id for q in questions]
    answers = db.query(Answer).filter(Answer.question_id.in_(q_ids)).all()
    evaluations = [a.evaluation for a in answers if a.evaluation]
    content=build_report(evaluations); r=Report(interview_id=interview_id,content=content,overall_score=content['overall_score']); db.add(r); db.commit(); return content
