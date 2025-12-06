import os
import warnings

from typing import Any
from lib.models import TTS_ENGINES

# Import performance optimizer
try:
    from lib.classes.tts_engines.common.performance_optimizer import performance_optimizer, optimize_inference_context
    from lib.classes.tts_engines.common.utils import setup_performance_environment, cleanup_memory_advanced
    performance_available = True
except ImportError:
    performance_available = False
    warnings.warn("Performance optimizer not available, running without optimizations")

class TTSManager:
    def __init__(self, session:Any)->None:
        self.session = session
        self.engine = False
        if self.session['tts_engine'] in TTS_ENGINES.values():
            if self.session['tts_engine'] == TTS_ENGINES['XTTSv2']:
                from lib.classes.tts_engines.coqui import Coqui
                self.engine = Coqui(self.session)
            elif self.session['tts_engine'] == TTS_ENGINES['BARK']:
                from lib.classes.tts_engines.bark import BarkTTS
                self.engine = BarkTTS(self.session)
            elif self.session['tts_engine'] == TTS_ENGINES['VITS']:
                from lib.classes.tts_engines.vits import VitsTTS
                self.engine = VitsTTS(self.session)
            elif self.session['tts_engine'] == TTS_ENGINES['FAIRSEQ']:
                from lib.classes.tts_engines.fairseq import FairseqTTS
                self.engine = FairseqTTS(self.session)
            elif self.session['tts_engine'] == TTS_ENGINES['TACOTRON2']:
                from lib.classes.tts_engines.tacotron2 import Tacotron2TTS
                self.engine = Tacotron2TTS(self.session)
            elif self.session['tts_engine'] == TTS_ENGINES['YOURTTS']:
                from lib.classes.tts_engines.yourtts import YourTtsTTS
                self.engine = YourTtsTTS(self.session)
            elif self.session['tts_engine'] == TTS_ENGINES['SUPERTONIC']:
                from lib.classes.tts_engines.supertonic import SupertonicTTS
                self.engine = SupertonicTTS(self.session)
            #elif self.session['tts_engine'] in [TTS_ENGINES['NEW_TTS']]:
            #    from lib.classes.tts_engines.new_tts import NewTts
            #    self.engine = NewTts(self.session)
        else:
            print('Other TTS engines coming soon!')

    def convert_sentence2audio(self,sentence_number:int, sentence:str)->bool:
        try:
            if self.session['tts_engine'] in TTS_ENGINES.values():
                return self.engine.convert(sentence_number, sentence)
            else:
                print('Other TTS engines coming soon!')
        except Exception as e:
            error=f'convert_sentence2audio(): {e}'
            raise ValueError(e)

    def setup_performance_optimization(self) -> None:
        """Setup performance optimization for the TTS engine"""
        if performance_available:
            # Setup CUDA environment
            setup_performance_environment()

            # Initialize performance optimizer
            if hasattr(self.engine, 'setup_performance'):
                self.engine.setup_performance()

            print("✅ Performance optimization setup complete")

    def optimize_conversion(self, sentence_number: int, sentence: str) -> bool:
        """Optimized conversion with performance monitoring"""
        if performance_available:
            # Use performance-optimized inference context
            @optimize_inference_context()
            def optimized_convert():
                return self.convert_sentence2audio(sentence_number, sentence)

            return optimized_convert()
        else:
            return self.convert_sentence2audio(sentence_number, sentence)

    def get_performance_status(self) -> dict:
        """Get current performance optimization status"""
        if performance_available:
            return performance_optimizer.get_optimization_status()
        return {"performance_optimization": "disabled"}

    def cleanup_resources(self) -> None:
        """Cleanup resources with advanced memory management"""
        if performance_available:
            cleanup_memory_advanced()
        else:
            if hasattr(self.engine, 'cleanup_memory'):
                self.engine.cleanup_memory()
