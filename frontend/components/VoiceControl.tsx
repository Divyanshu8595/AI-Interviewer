'use client';
import { useRef, useState, useEffect } from 'react';

export default function VoiceControl() {
  const ws = useRef<WebSocket | null>(null);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<{ speaker: string, text: string, evaluation?: any }[]>([]);
  const [status, setStatus] = useState('Idle');

  const connect = () => {
    // Using a hardcoded ID for now, in a real app this would come from props/router
    const interviewId = 1;
    ws.current = new WebSocket(`ws://localhost:8000/interviews/ws/${interviewId}`);

    ws.current.onopen = () => {
      setIsConnected(true);
      setStatus('Connected');
    };

    ws.current.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setMessages(prev => [...prev, data]);

      if (data.audio) {
        const audio = new Audio(`data:audio/wav;base64,${data.audio}`);
        audio.play().catch(err => console.error("Audio playback failed:", err));
      }
    };

    ws.current.onclose = () => {
      setIsConnected(false);
      setStatus('Disconnected');
    };
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (e) => {
        audioChunks.current.push(e.data);
      };

      mediaRecorder.current.onstop = () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        if (ws.current && ws.current.readyState === WebSocket.OPEN) {
          ws.current.send(audioBlob);
        }
      };

      mediaRecorder.current.start();
      setIsRecording(true);
      setStatus('Listening...');
    } catch (err) {
      console.error("Error accessing microphone:", err);
      setStatus('Mic Error');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      setStatus('Processing...');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        {!isConnected ? (
          <button className="px-6 py-2 bg-blue-600 text-white rounded-full font-bold hover:bg-blue-700 transition" onClick={connect}>
            Start Interview
          </button>
        ) : (
          <button
            className={`px-8 py-4 rounded-full font-bold text-white transition-all shadow-lg ${isRecording ? 'bg-red-500 scale-105 animate-pulse' : 'bg-emerald-600 hover:bg-emerald-700'}`}
            onMouseDown={startRecording}
            onMouseUp={stopRecording}
            onTouchStart={startRecording}
            onTouchEnd={stopRecording}
          >
            {isRecording ? 'Release to Send' : 'Push to Talk'}
          </button>
        )}
        <div className="text-sm font-medium text-gray-500">Status: <span className="text-gray-900">{status}</span></div>
      </div>

      <div className="space-y-4 max-h-[500px] overflow-y-auto p-4 border rounded-xl bg-gray-50 shadow-inner">
        {messages.length === 0 && (
          <div className="text-center py-10 text-gray-400">
            Click Start Interview to begin.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.speaker === 'ai' ? 'justify-start' : 'justify-end'}`}>
            <div className={`max-w-[80%] p-4 rounded-2xl shadow-sm ${m.speaker === 'ai' ? 'bg-white border text-gray-800' : 'bg-blue-600 text-white'}`}>
              <div className="text-xs font-bold uppercase tracking-wider mb-1 opacity-50">{m.speaker}</div>
              <div className="text-lg leading-relaxed">{m.text}</div>
              {m.evaluation && (
                <div className="mt-2 pt-2 border-t border-blue-400 text-xs italic">
                  Score: {m.evaluation.relevance}% | {m.evaluation.notes}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
