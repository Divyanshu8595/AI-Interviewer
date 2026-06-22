import httpx, json
OLLAMA_URL='http://localhost:11434/api/generate'; MODEL='gemma2:2b'
def safe_context(text:str)->str: return text.replace('ignore previous','[removed]').replace('system prompt','[removed]')[:3000]
async def generate_question(memory:dict, resume_context:list[str], company:str, role:str, difficulty:str)->str:
    history = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(memory.get('asked_questions', []), memory.get('answers', []))])

    prompt = f"""You are an expert technical interviewer at {company} interviewing a candidate for a {role} role (Difficulty: {difficulty}).

    Candidate Resume Context:
    {safe_context(' '.join(resume_context))}

    Conversation History:
    {history}

    Your goal is to ask the NEXT interview question.
    - If the conversation just started, ask an introductory question about their background.
    - If they just answered a question, follow up on their answer or move to a new relevant topic from their resume.
    - Be professional, concise, and natural.
    - DO NOT repeat questions already asked: {memory.get('asked_questions', [])}
    - Ask exactly ONE question.

    Question:"""

    try:
        async with httpx.AsyncClient(timeout=15) as c:
            r = await c.post(OLLAMA_URL, json={
                'model': MODEL,
                'prompt': prompt,
                'stream': False,
                'options': {
                    'num_ctx': 4096,
                    'num_predict': 128,
                    'temperature': 0.7
                }
            })
            response = r.json().get('response', '').strip()
            # Clean up response if it includes "Question:" prefix or similar
            response = response.split("Question:")[-1].strip()
            return response or fallback(role)
    except Exception:
        return fallback(role)
def fallback(role:str)->str: return f"Tell me about a project from your resume that best demonstrates your readiness for a {role} role."
