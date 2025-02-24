import time
import threading
import numpy as np
import whisper
import sounddevice as sd
import wave
from queue import Queue
from rich.console import Console
from langchain.chains import LLMChain #ConversationChain
from langchain.prompts import PromptTemplate
from langchain_community.llms import Ollama
from ko_tts import KoTextToSpeechService
import os
from scipy.io import wavfile

# model 한번만 로드
global_stt_model = whisper.load_model("medium", device="cuda")
global_llm_chain = None

def initialize_llm_chain():
    global global_llm_chain
    if global_llm_chain is None:
        template = """{input}에 대해 친구처럼 편안하고 자연스럽게 대답해줘."""

        PROMPT = PromptTemplate(input_variables=["input"], template=template)
        global_llm_chain = LLMChain(
            prompt=PROMPT,
            verbose=False,
            #llm = Ollama(model='ollama-ko-bloosm')
            llm=Ollama(model='ollama-ko-suneun-bloosm'),
        )

class Assistant:
    def __init__(self):
        self.console = Console()
        self.stt = global_stt_model 
        self.tts = KoTextToSpeechService()

        initialize_llm_chain()
        self.chain = global_llm_chain

    def transcribe(self, audio_np: np.ndarray) -> str:
        result = self.stt.transcribe(audio_np, fp16=False)  # Set fp16=True if using a GPU
        text = result["text"].strip()
        return text

    def get_llm_response(self, text: str) -> str:
        response = self.chain.predict(input=text)
        if response.startswith("Assistant:"):
            response = response[len("Assistant:") :].strip()
        return response

    def save_audio_to_wav(self, sample_rate, audio_array, filename):
        wavfile.write(filename, sample_rate, (audio_array * 32767).astype(np.int16))
        self.console.print(f"[green]Audio saved to {filename}")

    def run(self):
        self.console.print("[cyan]Assistant started! Press Ctrl+C to exit.")

        try:
            audio_file_path = '/home/mines/Desktop/chat/output.wav'
            if os.path.exists(audio_file_path):
                sample_rate, audio_np = wavfile.read(audio_file_path)
                audio_np = audio_np.astype(np.float32) / 32768.0

                if audio_np.size > 0:
                    with self.console.status('Transcribing...', spinner='earth'):
                        text = self.transcribe(audio_np)
                    self.console.print(f"[yellow]You : {text}")

                    with self.console.status('Generating response...', spinner='earth'):
                        response = self.get_llm_response(text)
                        self.console.print(f"[yellow]Robot : {response}")
                        sample_rate, audio_array = self.tts.synthesize(response)

                    output_wav_path = '/home/mines/Desktop/chat/response.wav'
                    self.save_audio_to_wav(sample_rate, audio_array, output_wav_path)
                else:
                    self.console.print('[red]No audio data found in the file.')

            else:
                self.console.print(f"[red]Audio file not found at {audio_file_path}")

        except KeyboardInterrupt:
            self.console.print('\n[red]Finish')

        self.console.print("[blue]Session END")

if __name__ == "__main__":
    assistant = Assistant()
    assistant.run()
