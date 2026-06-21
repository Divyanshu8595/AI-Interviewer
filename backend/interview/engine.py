import httpx, json
OLLAMA_URL='http://localhost:11434/api/generate'; MODEL='gemma3:1b'
def safe_context(text:str)->str: return text.replace('ignore previous','[removed]').replace('system prompt','[removed]')[:3000]
async def generate_question(memory:dict, resume_context:list[str], company:str, role:str, difficulty:str)->str:
    prompt=f"You are a concise interviewer. Use only this sanitized resume context: {safe_context(' '.join(resume_context))}. Company={company}, role={role}, difficulty={difficulty}. Asked={memory.get('asked_questions',[])}. Ask exactly one natural, non-repeated interview question."
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r=await c.post(OLLAMA_URL,json={'model':MODEL,'prompt':prompt,'stream':False,'options':{'num_ctx':2048,'num_predict':80}}); return r.json().get('response','').strip() or fallback(role)
    except Exception: return fallback(role)
def fallback(role:str)->str: return f"Tell me about a project from your resume that best demonstrates your readiness for a {role} role."
