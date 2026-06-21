import shutil, subprocess, tempfile
class VoicePipeline:
    def __init__(self): self.whisper_model=None
    def transcribe_placeholder(self, text:str)->str: return text.strip()
    def synthesize(self, text:str, voice:str='female')->bytes:
        if not shutil.which('piper'): return b''
        with tempfile.NamedTemporaryFile(suffix='.wav') as out:
            subprocess.run(['piper','--output_file',out.name],input=text.encode(),timeout=2,check=False)
            return out.read()
voice_pipeline=VoicePipeline()
