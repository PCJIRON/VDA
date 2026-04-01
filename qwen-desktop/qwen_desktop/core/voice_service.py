"""
Voice Recording and Speech-to-Text Service.
Uses SpeechRecognition library for STT and pyttsx3 for offline TTS.
"""

import threading
import logging
from typing import Optional, Callable
from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr
import pyttsx3

logger = logging.getLogger(__name__)


# -- Text-To-Speech Worker --
class TTSWorker(QThread):
    """Background thread to play Text-to-Speech asynchronously."""
    finished = pyqtSignal()
    
    def __init__(self, text: str):
        super().__init__()
        self.text = text
        
    def run(self):
        try:
            engine = pyttsx3.init()
            # Set properties if needed (speed, voice)
            engine.setProperty("rate", 160)
            engine.say(self.text)
            engine.runAndWait()
        except Exception as e:
            logger.error(f"TTS Error: {e}")
        finally:
            self.finished.emit()


# -- Speech-To-Text Worker --
class VoiceRecorder(QThread):
    """Background thread for continuous recording audio and performing STT."""
    
    transcription_ready = pyqtSignal(str)
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 3000
        self.recognizer.dynamic_energy_threshold = True
    
    def run(self):
        """Main recording loop - runs continuously in separate thread."""
        try:
            self.is_recording = True
            logger.info("Starting recording thread loop...")
            self.recording_started.emit()
            
            with sr.Microphone() as source:
                logger.info("?? Calibrating mic...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Loop continuously until toggled off
                while self.is_recording:
                    logger.info("?? Listening...")
                    audio = None
                    try:
                        # short timeout so loop can break faster if is_recording becomes False
                        audio = self.recognizer.listen(
                            source,
                            timeout=2,
                            phrase_time_limit=15
                        )
                    except sr.WaitTimeoutError:
                        continue # No speech yet, loop again
                    except sr.RequestError as e:
                        if self.is_recording:
                            self.error_occurred.emit(f"Recording error: {str(e)}")
                        continue
                    
                    if audio and self.is_recording:
                        self._transcribe_audio(audio)
                        
        except Exception as e:
            logger.error(f"Microphone access error: {str(e)}")
            self.error_occurred.emit(f"Microphone not available: {str(e)}")
            
        finally:
            self.is_recording = False
            self.recording_stopped.emit()
    
    def _transcribe_audio(self, audio_data):
        try:
            logger.info("?? Transcribing with Google Speech Recognition...")
            transcription = self.recognizer.recognize_google(audio_data)
            if transcription and self.is_recording:
                logger.info(f"? Transcription: {transcription}")
                self.transcription_ready.emit(transcription)
        except sr.UnknownValueError:
            # Silent fallback if nothing was heard clearly
            pass
        except sr.RequestError as e:
            logger.warning(f"?? Google service unavailable: {str(e)}")
            self.error_occurred.emit(f"Speech service unavailable. Please check internet connection.")
        except Exception as e:
            self.error_occurred.emit(f"Transcription error: {str(e)}")

class VoiceService:
    """Manager for voice recording and transcription."""
    
    def __init__(self):
        self.recorder: Optional[VoiceRecorder] = None
        self.tts_worker: Optional[TTSWorker] = None
        self.is_recording = False
        
    def speak(self, text: str):
        """Speak text in background without UI blocking."""
        self.tts_worker = TTSWorker(text)
        self.tts_worker.start()
    
    def start_recording(self) -> bool:
        if self.is_recording:
            return False
            
        # Check mic
        try:
            with sr.Microphone():
                pass
        except Exception as e:
            logger.error(f"Microphone not available: {str(e)}")
            return False
            
        self.recorder = VoiceRecorder()
        self.is_recording = True
        self.recorder.start()
        return True
    
    def stop_recording(self):
        if self.recorder and self.recorder.isRunning():
            self.recorder.is_recording = False
        self.is_recording = False
    
    def get_recorder(self) -> Optional[VoiceRecorder]:
        return self.recorder

