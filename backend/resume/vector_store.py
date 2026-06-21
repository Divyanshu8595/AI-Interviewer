import chromadb
from chromadb.utils import embedding_functions
client=chromadb.PersistentClient(path='./data/chroma')
ef=embedding_functions.SentenceTransformerEmbeddingFunction(model_name='sentence-transformers/all-MiniLM-L6-v2')
def index_resume(resume_id:int, structured:dict):
    col=client.get_or_create_collection('resume_chunks', embedding_function=ef)
    docs=[]
    for key in ('skills','projects','experience'):
        val=structured.get(key) or []
        docs.append(f"{key}: {', '.join(val) if isinstance(val,list) else val}")
    col.upsert(ids=[f'{resume_id}-{i}' for i in range(len(docs))], documents=docs, metadatas=[{'resume_id':resume_id}]*len(docs))
def retrieve(resume_id:int, query:str, n:int=3):
    col=client.get_or_create_collection('resume_chunks', embedding_function=ef)
    return col.query(query_texts=[query], n_results=n, where={'resume_id':resume_id}).get('documents',[[]])[0]
