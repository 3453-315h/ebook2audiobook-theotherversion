#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Base TTS Engine Class for ebook2audiobook
Provides common functionality to reduce code duplication across TTS engines
"""

import os
import torch
import torchaudio
import threading
import numpy as np
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from enum import Enum
from pathlib import Path
from abc import ABC, abstractmethod

# Import custom exceptions and utilities
from lib.classes.exceptions import (
    TTSEngineError, AudioProcessingError, FileOperationError,
    ValidationError, MemoryError, ErrorSeverity, ExceptionHandler
)
from lib.classes.error_reporter import report_error
from lib.classes.memory_manager import (
    MemoryStrategy, optimize_function, optimize_batch_processing,
    torch_optimized, start_memory_monitoring, stop_memory_monitoring
)
from lib.classes.tts_engines.common.utils import (
    cleanup_memory, cleanup_memory_advanced, is_audio_data_valid,
    append_sentence2vtt, loaded_tts_size_gb
)
from lib.classes.tts_engines.common.audio_filters import (
    detect_gender, trim_audio, normalize_audio
)
from lib import (
    default_engine_settings, models, TTS_ENGINES, language_tts,
    default_audio_proc_format, default_audio_proc_samplerate, TTS_SML
)

# Configure logging for TTS engines
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class TTSEngineStatus(Enum):
    """Enumeration for TTS engine status"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    PROCESSING = "processing"
    ERROR = "error"
    CLEANUP = "cleanup"

class BaseTTSEngine(ABC):
    """
    Base TTS Engine class providing common functionality
    All TTS engines should inherit from this class to reduce code duplication
    """

    def __init__(self, session: Any, engine_name: str):
        """
        Initialize the base TTS engine
        """
        try:
            # Validate session
            if not session or not isinstance(session, dict):
                raise ValidationError(
                    message="Invalid session provided to TTS engine",
                    context={'engine_name': engine_name, 'session': session}
                )

            # Set up basic attributes
            self.session = session
            self.engine_name = engine_name
            self.status = TTSEngineStatus.UNINITIALIZED
            self.engine = None
            self.tts_key = self._get_tts_key()
            self.speakers_path = None
            self.sentences_total_time = 0.0
            self.sentence_idx = 1
            self.params = self._get_default_params()
            self.vtt_path = self._get_vtt_path()
            self.resampler_cache = {}
            self.audio_segments = []
            self.memory_strategy = MemoryStrategy.BALANCED

            # Initialize memory monitoring
            self._initialize_memory_management()

            # Set status to initializing
            self.status = TTSEngineStatus.INITIALIZING

            # Log initialization
            logging.info(f"Initializing {engine_name} TTS engine with key: {self.tts_key}")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': engine_name,
                'function': '__init__'
            })
            raise TTSEngineError(
                message=f"Failed to initialize {engine_name} TTS engine",
                engine_name=engine_name,
                severity=ErrorSeverity.CRITICAL,
                original_exception=e
            )

    def _get_tts_key(self) -> str:
        """Get the TTS cache key for this engine"""
        try:
            return f"{self.session['tts_engine']}-{self.session['fine_tuned']}"
        except KeyError as e:
            raise ValidationError(
                message="Missing required session keys for TTS key generation",
                context={'missing_key': str(e), 'engine_name': self.engine_name}
            )

    def _get_default_params(self) -> Dict[str, Any]:
        """Get default parameters for the TTS engine"""
        try:
            # Get engine-specific parameters
            engine_params = {
                'samplerate': models[self.session['tts_engine']][self.session['fine_tuned']]['samplerate'],
                'device': self.session['device']
            }

            # Add engine-specific parameters
            if self.session['tts_engine'] == TTS_ENGINES['BARK']:
                engine_params.update({
                    'text_temp': default_engine_settings[TTS_ENGINES['BARK']]['text_temp'],
                    'waveform_temp': default_engine_settings[TTS_ENGINES['BARK']]['waveform_temp']
                })
            elif self.session['tts_engine'] == TTS_ENGINES['XTTSv2']:
                engine_params.update({
                    'temperature': default_engine_settings[TTS_ENGINES['XTTSv2']]['temperature'],
                    'length_penalty': default_engine_settings[TTS_ENGINES['XTTSv2']]['length_penalty'],
                    'repetition_penalty': default_engine_settings[TTS_ENGINES['XTTSv2']]['repetition_penalty'],
                    'top_k': default_engine_settings[TTS_ENGINES['XTTSv2']]['top_k'],
                    'top_p': default_engine_settings[TTS_ENGINES['XTTSv2']]['top_p'],
                    'speed': default_engine_settings[TTS_ENGINES['XTTSv2']]['speed'],
                    'enable_text_splitting': default_engine_settings[TTS_ENGINES['XTTSv2']]['enable_text_splitting']
                })

            return engine_params

        except Exception as e:
            raise TTSEngineError(
                message=f"Failed to get default parameters for {self.engine_name}",
                engine_name=self.engine_name,
                original_exception=e
            )

    def _get_vtt_path(self) -> str:
        """Get the path for VTT (WebVTT) file"""
        try:
            vtt_filename = f"{Path(self.session['final_name']).stem}.vtt"
            return os.path.join(self.session['process_dir'], vtt_filename)
        except KeyError as e:
            raise ValidationError(
                message="Missing required session keys for VTT path",
                context={'missing_key': str(e), 'engine_name': self.engine_name}
            )

    def _initialize_memory_management(self) -> None:
        """Initialize memory management for the TTS engine"""
        try:
            # Start memory monitoring
            start_memory_monitoring(interval=10.0)

            # Set memory strategy based on available resources
            self._set_memory_strategy()

            logging.info(f"Memory management initialized for {self.engine_name}")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_initialize_memory_management'
            })

    def _set_memory_strategy(self) -> None:
        """Set memory strategy based on available resources"""
        try:
            # Get available VRAM/GPU memory
            free_vram_gb = self.session.get('free_vram_gb', 0)

            # Set strategy based on available resources
            if free_vram_gb < 4.0:
                self.memory_strategy = MemoryStrategy.CONSERVATIVE
            elif free_vram_gb < 8.0:
                self.memory_strategy = MemoryStrategy.BALANCED
            else:
                self.memory_strategy = MemoryStrategy.AGGRESSIVE

            logging.info(f"Set memory strategy to {self.memory_strategy.value} for {self.engine_name}")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_set_memory_strategy'
            })

    @abstractmethod
    def _load_engine(self) -> None:
        """Load the TTS engine (to be implemented by subclasses)"""
        pass

    @abstractmethod
    def _load_checkpoint(self, **kwargs: Any) -> Any:
        """Load engine checkpoint (to be implemented by subclasses)"""
        pass

    def _validate_session(self) -> None:
        """Validate the session has required parameters"""
        try:
            required_keys = [
                'tts_engine', 'fine_tuned', 'device', 'language',
                'session_dir', 'process_dir', 'final_name'
            ]

            missing_keys = [key for key in required_keys if key not in self.session]

            if missing_keys:
                raise ValidationError(
                    message=f"Missing required session keys: {missing_keys}",
                    context={'engine_name': self.engine_name, 'missing_keys': missing_keys}
                )

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_validate_session'
            })
            raise

    def _setup_directories(self) -> None:
        """Setup required directories for the TTS engine"""
        try:
            # Create VTT directory if needed
            vtt_dir = os.path.dirname(self.vtt_path)
            os.makedirs(vtt_dir, exist_ok=True)

            # Create other required directories
            required_dirs = [
                self.session['chapters_dir'],
                self.session['chapters_dir_sentences']
            ]

            for dir_path in required_dirs:
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_setup_directories'
            })
            raise FileOperationError(
                message=f"Failed to setup directories for {self.engine_name}",
                original_exception=e,
                context={'engine_name': self.engine_name}
            )

    def _tensor_type(self, audio_data: Any) -> torch.Tensor:
        """Convert audio data to tensor type"""
        try:
            if isinstance(audio_data, torch.Tensor):
                return audio_data
            elif isinstance(audio_data, np.ndarray):
                return torch.from_numpy(audio_data).float()
            elif isinstance(audio_data, list):
                return torch.tensor(audio_data, dtype=torch.float32)
            else:
                raise TypeError(f"Unsupported type for audio_data: {type(audio_data)}")
        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_tensor_type'
            })
            raise AudioProcessingError(
                message=f"Failed to convert audio data to tensor",
                original_exception=e,
                context={'engine_name': self.engine_name}
            )

    def _get_resampler(self, orig_sr: int, target_sr: int) -> torchaudio.transforms.Resample:
        """Get or create a resampler for the given sample rates"""
        try:
            key = (orig_sr, target_sr)
            if key not in self.resampler_cache:
                self.resampler_cache[key] = torchaudio.transforms.Resample(
                    orig_freq=orig_sr, new_freq=target_sr
                )
            return self.resampler_cache[key]
        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_get_resampler'
            })
            raise AudioProcessingError(
                message=f"Failed to create resampler for {orig_sr}Hz -> {target_sr}Hz",
                original_exception=e,
                context={'engine_name': self.engine_name}
            )

    def _resample_wav(self, wav_path: str, expected_sr: int) -> str:
        """Resample WAV file to expected sample rate"""
        try:
            waveform, orig_sr = torchaudio.load(wav_path)

            if orig_sr == expected_sr and waveform.size(0) == 1:
                return wav_path

            if waveform.size(0) > 1:
                waveform = waveform.mean(dim=0, keepdim=True)

            if orig_sr != expected_sr:
                resampler = self._get_resampler(orig_sr, expected_sr)
                waveform = resampler(waveform)

            # Save resampled audio to temp file
            temp_dir = os.path.join(self.session['process_dir'], 'tmp')
            os.makedirs(temp_dir, exist_ok=True)

            temp_path = os.path.join(temp_dir, f"resampled_{os.path.basename(wav_path)}")
            torchaudio.save(temp_path, waveform, expected_sr, format='wav')

            return temp_path

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_resample_wav'
            })
            raise AudioProcessingError(
                message=f"Failed to resample WAV file: {wav_path}",
                original_exception=e,
                context={'engine_name': self.engine_name}
            )

    def _check_speaker_compatibility(self, voice_path: str, speaker: str) -> bool:
        """Check if speaker is compatible with the TTS engine"""
        try:
            # Check if voice path exists
            if not voice_path or not os.path.exists(voice_path):
                return False

            # Check if speaker is in built-in voices
            if (self.session['tts_engine'] in default_engine_settings and
                speaker in default_engine_settings[self.session['tts_engine']]['voices']):
                return True

            # Additional engine-specific checks can be added by subclasses
            return self._engine_specific_speaker_check(voice_path, speaker)

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_check_speaker_compatibility'
            })
            return False

    def _engine_specific_speaker_check(self, voice_path: str, speaker: str) -> bool:
        """Engine-specific speaker compatibility check (to be overridden by subclasses)"""
        return True

    def _get_fine_tuned_params(self) -> Dict[str, Any]:
        """Get fine-tuned parameters from session"""
        try:
            fine_tuned_params = {}

            # Common parameters
            if 'xtts_temperature' in self.session:
                fine_tuned_params['temperature'] = float(self.session['xtts_temperature'])
            if 'xtts_length_penalty' in self.session:
                fine_tuned_params['length_penalty'] = float(self.session['xtts_length_penalty'])
            if 'xtts_repetition_penalty' in self.session:
                fine_tuned_params['repetition_penalty'] = float(self.session['xtts_repetition_penalty'])

            # Engine-specific parameters
            if self.session['tts_engine'] == TTS_ENGINES['BARK']:
                if 'bark_text_temp' in self.session:
                    fine_tuned_params['text_temp'] = float(self.session['bark_text_temp'])
                if 'bark_waveform_temp' in self.session:
                    fine_tuned_params['waveform_temp'] = float(self.session['bark_waveform_temp'])

            return fine_tuned_params

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_get_fine_tuned_params'
            })
            return {}

    def _handle_special_sentences(self, sentence: str) -> Optional[torch.Tensor]:
        """Handle special sentence types (break, pause)"""
        try:
            if sentence == TTS_SML['break']:
                silence_time = np.random.uniform(0.3, 0.6)
                break_tensor = torch.zeros(1, int(self.params['samplerate'] * silence_time))
                return break_tensor
            elif not sentence.replace('—', '').strip() or sentence == TTS_SML['pause']:
                silence_time = np.random.uniform(1.0, 1.8)
                pause_tensor = torch.zeros(1, int(self.params['samplerate'] * silence_time))
                return pause_tensor
            return None
        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_handle_special_sentences'
            })
            return None

    def _process_audio_tensor(self, audio_tensor: torch.Tensor, sentence: str) -> torch.Tensor:
        """Process audio tensor with trimming and cleanup"""
        try:
            # Trim audio if needed
            if sentence and (sentence[-1].isalnum() or sentence[-1] == '—'):
                trim_audio_buffer = 0.002
                audio_tensor = trim_audio(
                    audio_tensor.squeeze(),
                    self.params['samplerate'],
                    0.001,
                    trim_audio_buffer
                ).unsqueeze(0)

            # Validate audio tensor
            if audio_tensor is None or audio_tensor.numel() == 0:
                raise AudioProcessingError(
                    message="Audio tensor is empty after processing",
                    context={'sentence': sentence, 'engine_name': self.engine_name}
                )

            return audio_tensor

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_process_audio_tensor'
            })
            raise

    def _save_audio_file(self, audio_tensor: torch.Tensor, sentence_index: int) -> str:
        """Save audio tensor to file"""
        try:
            final_sentence_file = os.path.join(
                self.session['chapters_dir_sentences'],
                f'{sentence_index}.{default_audio_proc_format}'
            )

            # Save audio file
            torchaudio.save(
                final_sentence_file,
                audio_tensor,
                self.params['samplerate'],
                format=default_audio_proc_format
            )

            # Verify file was created
            if not os.path.exists(final_sentence_file):
                raise FileOperationError(
                    message=f"Audio file was not created: {final_sentence_file}",
                    context={'engine_name': self.engine_name}
                )

            return final_sentence_file

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_save_audio_file'
            })
            raise

    def _update_vtt_file(self, sentence_obj: Dict[str, Any]) -> int:
        """Update VTT file with sentence information"""
        try:
            self.sentence_idx = append_sentence2vtt(sentence_obj, self.vtt_path)
            return self.sentence_idx
        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_update_vtt_file'
            })
            return 0

    def _cleanup_audio_resources(self) -> None:
        """Clean up audio resources and memory"""
        try:
            # Clear audio segments
            self.audio_segments = []

            # Clean up memory
            cleanup_memory_advanced()

            # Force garbage collection
            gc.collect()

            # Clean up CUDA if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.ipc_collect()

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_cleanup_audio_resources'
            })

    def _validate_audio_sentence(self, audio_sentence: Any) -> bool:
        """Validate audio sentence data"""
        try:
            if not is_audio_data_valid(audio_sentence):
                raise AudioProcessingError(
                    message="Invalid audio sentence data",
                    context={'engine_name': self.engine_name}
                )
            return True
        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_validate_audio_sentence'
            })
            return False

    def _get_speaker_info(self, voice_path: str) -> Tuple[str, str]:
        """Get speaker information from voice path"""
        try:
            if not voice_path:
                return None, None

            speaker = os.path.splitext(os.path.basename(voice_path))[0].replace('.wav', '')

            # Determine speaker directory
            if speaker in default_engine_settings[self.session['tts_engine']]['voices'].keys():
                speaker_dir = default_engine_settings[self.session['tts_engine']]['speakers_path']
            else:
                speaker_dir = os.path.join(os.path.dirname(voice_path), self.session['tts_engine'].lower())

            return speaker, speaker_dir

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_get_speaker_info'
            })
            return None, None

    def _initialize_engine(self) -> None:
        """Initialize the TTS engine with proper error handling"""
        try:
            # Validate session
            self._validate_session()

            # Setup directories
            self._setup_directories()

            # Load the engine
            self._load_engine()

            # Set status to ready
            self.status = TTSEngineStatus.READY

            logging.info(f"{self.engine_name} engine initialized successfully")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_initialize_engine'
            })
            self.status = TTSEngineStatus.ERROR
            raise TTSEngineError(
                message=f"Failed to initialize {self.engine_name} engine",
                engine_name=self.engine_name,
                severity=ErrorSeverity.CRITICAL,
                original_exception=e
            )

    @abstractmethod
    def convert(self, sentence_index: int, sentence: str) -> bool:
        """Convert sentence to audio (to be implemented by subclasses)"""
        pass

    def _common_convert_logic(self, sentence_index: int, sentence: str) -> bool:
        """Common convert logic shared by all TTS engines"""
        try:
            # Validate input
            if not sentence or not isinstance(sentence, str):
                raise ValidationError(
                    message="Invalid sentence input",
                    context={'sentence_index': sentence_index, 'sentence': sentence}
                )

            # Check if engine is ready
            if self.status != TTSEngineStatus.READY:
                raise TTSEngineError(
                    message=f"{self.engine_name} engine is not ready",
                    engine_name=self.engine_name,
                    severity=ErrorSeverity.HIGH
                )

            # Handle special sentences
            special_tensor = self._handle_special_sentences(sentence)
            if special_tensor is not None:
                self.audio_segments.append(special_tensor.clone())
                return True

            # Set status to processing
            self.status = TTSEngineStatus.PROCESSING

            return False  # Continue with engine-specific processing

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_common_convert_logic'
            })
            self.status = TTSEngineStatus.ERROR
            raise

    def _finalize_convert(self, audio_tensor: torch.Tensor, sentence: str, sentence_index: int) -> bool:
        """Finalize the convert process with common logic"""
        try:
            # Process audio tensor
            audio_tensor = self._process_audio_tensor(audio_tensor, sentence)

            # Add to audio segments
            self.audio_segments.append(audio_tensor)

            # Add optional break if sentence doesn't end with punctuation
            if not sentence.replace('—', '').strip() and not re.search(r'\w$', sentence, flags=re.UNICODE):
                silence_time = np.random.uniform(0.3, 0.6)
                break_tensor = torch.zeros(1, int(self.params['samplerate'] * silence_time))
                self.audio_segments.append(break_tensor.clone())

            # Combine audio segments
            if self.audio_segments:
                audio_tensor = torch.cat(self.audio_segments, dim=-1)
                start_time = self.sentences_total_time
                duration = round((audio_tensor.shape[-1] / self.params['samplerate']), 2)
                end_time = start_time + duration
                self.sentences_total_time = end_time

                # Create sentence metadata
                sentence_obj = {
                    "start": start_time,
                    "end": end_time,
                    "text": sentence,
                    "resume_check": self.sentence_idx
                }

                # Update VTT file
                self._update_vtt_file(sentence_obj)

                # Save audio file
                final_sentence_file = self._save_audio_file(audio_tensor, sentence_index)

                # Cleanup resources
                self._cleanup_audio_resources()

                # Verify file was created
                if os.path.exists(final_sentence_file):
                    return True

            return False

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': '_finalize_convert'
            })
            self.status = TTSEngineStatus.ERROR
            return False

    def cleanup(self) -> None:
        """Clean up resources and shutdown the engine"""
        try:
            self.status = TTSEngineStatus.CLEANUP

            # Clean up audio resources
            self._cleanup_audio_resources()

            # Clean up engine if it exists
            if self.engine:
                if hasattr(self.engine, 'cleanup'):
                    self.engine.cleanup()
                del self.engine
                self.engine = None

            # Stop memory monitoring
            stop_memory_monitoring()

            self.status = TTSEngineStatus.UNINITIALIZED

            logging.info(f"{self.engine_name} engine cleaned up successfully")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'engine_name': self.engine_name,
                'function': 'cleanup'
            })
            self.status = TTSEngineStatus.ERROR

    def get_status(self) -> TTSEngineStatus:
        """Get current engine status"""
        return self.status

    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        from lib.classes.memory_manager import get_current_memory_usage
        return get_current_memory_usage()

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get memory optimization statistics"""
        from lib.classes.memory_manager import get_memory_optimization_stats
        return get_memory_optimization_stats(self.memory_strategy)

    def __del__(self):
        """Destructor to ensure proper cleanup"""
        try:
            if hasattr(self, 'status') and self.status != TTSEngineStatus.UNINITIALIZED:
                self.cleanup()
        except Exception:
            pass  # Don't raise exceptions in destructor

# Shared utility functions for TTS engines
def get_common_tts_parameters(session: Any, engine_name: str) -> Dict[str, Any]:
    """Get common TTS parameters across all engines"""
    try:
        common_params = {
            'samplerate': models[session['tts_engine']][session['fine_tuned']]['samplerate'],
            'device': session['device'],
            'language': session['language'],
            'output_format': session.get('output_format', 'm4b')
        }

        # Add engine-specific parameters
        if engine_name == TTS_ENGINES['BARK']:
            common_params.update({
                'text_temp': default_engine_settings[TTS_ENGINES['BARK']]['text_temp'],
                'waveform_temp': default_engine_settings[TTS_ENGINES['BARK']]['waveform_temp']
            })
        elif engine_name == TTS_ENGINES['XTTSv2']:
            common_params.update({
                'temperature': default_engine_settings[TTS_ENGINES['XTTSv2']]['temperature'],
                'length_penalty': default_engine_settings[TTS_ENGINES['XTTSv2']]['length_penalty'],
                'repetition_penalty': default_engine_settings[TTS_ENGINES['XTTSv2']]['repetition_penalty']
            })

        return common_params

    except Exception as e:
        ExceptionHandler.handle_exception(e, {
            'function': 'get_common_tts_parameters',
            'engine_name': engine_name
        })
        return {}

def validate_tts_session(session: Any, engine_name: str) -> None:
    """Validate TTS session has required parameters"""
    try:
        required_keys = [
            'tts_engine', 'fine_tuned', 'device', 'language',
            'session_dir', 'process_dir', 'final_name',
            'chapters_dir', 'chapters_dir_sentences'
        ]

        missing_keys = [key for key in required_keys if key not in session]

        if missing_keys:
            raise ValidationError(
                message=f"Missing required session keys for {engine_name}: {missing_keys}",
                context={'engine_name': engine_name, 'missing_keys': missing_keys}
            )

    except Exception as e:
        ExceptionHandler.handle_exception(e, {
            'function': 'validate_tts_session',
            'engine_name': engine_name
        })
        raise

def setup_tts_directories(session: Any, engine_name: str) -> None:
    """Setup required directories for TTS processing"""
    try:
        # Create main directories
        required_dirs = [
            session['chapters_dir'],
            session['chapters_dir_sentences'],
            os.path.dirname(session['vtt_path']) if 'vtt_path' in session else None
        ]

        for dir_path in required_dirs:
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)

        logging.info(f"Directories setup for {engine_name} TTS engine")

    except Exception as e:
        ExceptionHandler.handle_exception(e, {
            'function': 'setup_tts_directories',
            'engine_name': engine_name
        })
        raise FileOperationError(
            message=f"Failed to setup directories for {engine_name} TTS engine",
            context={'engine_name': engine_name}
        )

# Global TTS engine registry
tts_engine_registry = {}

def register_tts_engine(engine_name: str, engine_class: type) -> None:
    """Register a TTS engine class"""
    tts_engine_registry[engine_name] = engine_class

def get_tts_engine(engine_name: str, session: Any) -> BaseTTSEngine:
    """Get an instance of a TTS engine"""
    try:
        if engine_name not in tts_engine_registry:
            raise TTSEngineError(
                message=f"TTS engine {engine_name} is not registered",
                engine_name=engine_name,
                severity=ErrorSeverity.CRITICAL
            )

        engine_class = tts_engine_registry[engine_name]
        return engine_class(session)

    except Exception as e:
        ExceptionHandler.handle_exception(e, {
            'function': 'get_tts_engine',
            'engine_name': engine_name
        })
        raise