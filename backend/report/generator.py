def build_report(evaluations:list[dict])->dict:
    avg=lambda k: round(sum(e.get(k,0) for e in evaluations)/max(1,len(evaluations)))
    technical=avg('technical_understanding'); communication=avg('communication'); behavioral=avg('confidence'); overall=round((technical+communication+behavioral)/3)
    return {'overall_score':overall,'technical_score':technical,'communication_score':communication,'behavioral_score':behavioral,'strengths':['Clear project explanations','Relevant resume examples'],'weaknesses':['Needs deeper trade-off discussion'],'improvement_areas':['Quantify impact','Structure answers with STAR'],'suggested_topics':['DSA explanations','System design basics'],'summary':'Local mock interview completed with private on-device processing.'}
