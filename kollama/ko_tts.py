'''from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from IPython.display import Audio
import torch
import numpy as np
from kss import split_sentences 

class KoTextToSpeechService:
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = device
        self.model = preload_models()

    def synthesize(self, text: str):
        """
        input : text 
        output : sound
        """
        audio_array = generate_audio(text)
        return SAMPLE_RATE, audio_array

    def long_form_synthesize(self, text: str):
        """
        long text
        """
        pieces = []
        sentences = split_sentences(text)

        #combine
        for sent in sentences:
            sample_rate, audio_array = self.synthesize(sent)
            pieces.append(audio_array)

        return SAMPLE_RATE, np.concatenate(pieces)'''
    


from bark import SAMPLE_RATE, generate_audio, preload_models
from scipy.io.wavfile import write as write_wav
from IPython.display import Audio
import torch
import numpy as np
from kss import split_sentences 
import random

class KoTextToSpeechService:
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu", seed: int = 42):
        self.device = device
        self.model = preload_models()
        self.seed = seed 

    def synthesize(self, text: str, seed: int = 42):
        """
        input : text 
        output : sound
        """
        if seed is None:
            seed = self.seed
        random.seed(seed)
        torch.manual_seed(seed)
        audio_array = generate_audio(text)
        return SAMPLE_RATE, audio_array

    '''def long_form_synthesize(self, text: str, seed: int = 42):
        """
        long text
        """
        pieces = []
        sentences = split_sentences(text)

        for sent in sentences:
            sample_rate, audio_array = self.synthesize(sent, seed)
            pieces.append(audio_array)

        return SAMPLE_RATE, np.concatenate(pieces)'''