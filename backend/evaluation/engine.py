def evaluate_answer(question:str, answer:str)->dict:
    words=len(answer.split()); score=min(100, max(35, words*3))
    return {'relevance':score,'technical_understanding':score-5,'communication':min(100,score+5),'confidence':70 if words>20 else 50,'problem_solving':score-3,'notes':'Stored internally for final reporting.'}
