import os, shutil, subprocess, tempfile, logging
from faster_whisper import WhisperModel

class VoicePipeline:
    def __init__(self, model_size="tiny", device="cpu", compute_type="int8"):
        try:
            self.whisper_model = WhisperModel(model_size, device=device, compute_type=compute_type)
        except Exception as e:
            logging.error(f"Failed to load Whisper model: {e}")
            self.whisper_model = None

    def transcribe(self, audio_path: str) -> str:
        if not self.whisper_model:
            return "[STT Error: Model not loaded]"
        segments, _ = self.whisper_model.transcribe(audio_path, beam_size=5)
        return " ".join([segment.text for segment in segments]).strip()

    def synthesize(self, text: str, voice_model_path: str = None) -> bytes:
        """
        Uses Piper TTS to synthesize speech.
        If voice_model_path is provided, uses that specific model.
        """
        piper_path = shutil.which('piper')
        if not piper_path:
            logging.warning("Piper executable not found in PATH.")
            return b''

        # Default voice if none provided
        if not voice_model_path:
            # We assume a default model might be in a known location or just hope piper has a default
            # For local portability, we'll try to find a .onnx file in a 'models' directory
            voice_model_path = "models/en_US-lessac-medium.onnx"

        if not os.path.exists(voice_model_path):
            logging.warning(f"Voice model {voice_model_path} not found.")
            # Fallback: run piper without explicit model if it's configured globally,
            # but usually piper needs a model.

        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as out:
            temp_name = out.name

        try:
            cmd = [piper_path, '--model', voice_model_path, '--output_file', temp_name]
            subprocess.run(cmd, input=text.encode(), timeout=10, check=True, capture_output=True)
            with open(temp_name, 'rb') as f:
                return f.read()
        except Exception as e:
            logging.error(f"TTS Synthesis failed: {e}")
            return b''
        finally:
            if os.path.exists(temp_name):
                os.remove(temp_name)

voice_pipeline = VoicePipeline()
