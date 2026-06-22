import httpx, json, logging

OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'gemma2:2b'

async def evaluate_answer(question: str, answer: str) -> dict:
    # Heuristic fallback
    words = len(answer.split())
    base_score = min(95, max(40, words * 2))
    fallback_eval = {
        'relevance': base_score,
        'technical_understanding': max(0, base_score - 10),
        'communication': min(100, base_score + 5),
        'confidence': 70 if words > 25 else 50,
        'problem_solving': max(0, base_score - 5),
        'notes': 'Heuristic evaluation used as fallback.'
    }

    prompt = f"""Evaluate this interview answer based on the question.
Question: {question}
Answer: {answer}

Provide a JSON object with:
- relevance (0-100)
- technical_understanding (0-100)
- communication (0-100)
- confidence (0-100)
- problem_solving (0-100)
- notes (brief feedback)

JSON:"""

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(OLLAMA_URL, json={
                'model': MODEL,
                'prompt': prompt,
                'stream': False,
                'format': 'json',
                'options': {'num_predict': 200, 'temperature': 0.1}
            })
            result = json.loads(r.json().get('response', '{}'))
            if all(k in result for k in ['relevance', 'technical_understanding']):
                return result
    except Exception as e:
        logging.error(f"LLM Evaluation failed: {e}")

    return fallback_eval
