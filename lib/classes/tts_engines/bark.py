import os
import torch
import torchaudio
import threading
import numpy as np
from typing import Any
from pathlib import Path
from huggingface_hub import hf_hub_download

from lib.classes.vram_detector import VRAMDetector
from lib.classes.tts_engines.common.utils import cleanup_memory, loaded_tts_size_gb
from lib.classes.tts_engines.common.audio_filters import detect_gender, trim_audio, normalize_audio, is_audio_data_valid
from lib import *
from lib.models import TTS_ENGINES, default_engine_settings, models

lock = threading.Lock()

class BarkTTS:
    def __init__(self, session: Any):
        try:
            # Import exception handling
            from lib.classes.exceptions import TTSEngineError, ExceptionHandler, ErrorSeverity, FileOperationError

            self.session = session
            self.cache_dir = tts_dir
            self.engine = None
            self.tts_key = self.session['model_cache']
            self.speakers_path = None
            self.sentences_total_time = 0.0
            self.sentence_idx = 1

            # Validate session parameters
            if not self.session:
                raise TTSEngineError(
                    message="Session cannot be None",
                    engine_name="BARK",
                    severity=ErrorSeverity.CRITICAL
                )

            # Set up parameters with validation
            try:
                self.params = {
                    'samplerate': models[self.session['tts_engine']][self.session['fine_tuned']]['samplerate'],
                    'text_temp': default_engine_settings[TTS_ENGINES['BARK']]['text_temp'],
                    'waveform_temp': default_engine_settings[TTS_ENGINES['BARK']]['waveform_temp']
                }
            except (KeyError, TypeError) as e:
                raise TTSEngineError(
                    message="Invalid configuration for BARK engine parameters",
                    engine_name="BARK",
                    severity=ErrorSeverity.HIGH,
                    original_exception=e
                )

            # Set up paths with validation
            try:
                self.vtt_path = os.path.join(self.session['process_dir'], Path(self.session['final_name']).stem + '.vtt')
                os.makedirs(os.path.dirname(self.vtt_path), exist_ok=True)
            except Exception as e:
                raise FileOperationError(
                    message="Failed to create VTT file directory",
                    original_exception=e,
                    context={'path': self.vtt_path}
                )

            self.resampler_cache = {}
            self.audio_segments = []

            # Load engine with proper error handling
            self._load_engine()

        except TTSEngineError:
            # Re-raise as it's already properly formatted
            raise
        except FileOperationError:
            # Re-raise as it's already properly formatted
            raise
        except Exception as e:
            # Handle any other initialization errors
            TTSEngineError(
                message="BARK engine initialization failed",
                engine_name="BARK",
                severity=ErrorSeverity.CRITICAL,
                original_exception=e,
                context={'session_id': getattr(self.session, 'id', 'unknown')}
            )

    def _load_checkpoint(self, **kwargs: Any) -> Any:
        global lock
        try:
            with lock:
                from TTS.tts.configs.bark_config import BarkConfig
                from TTS.tts.models.bark import Bark

                key = kwargs.get('key')
                engine = loaded_tts.get(key, False)
                if not engine:
                    checkpoint_dir = kwargs.get('checkpoint_dir')
                    if not checkpoint_dir or not os.path.exists(checkpoint_dir):
                        error = f'Missing or invalid checkpoint_dir: {checkpoint_dir}'
                        raise FileNotFoundError(error)

                    config = BarkConfig()
                    config.CACHE_DIR = self.cache_dir
                    config.USE_SMALLER_MODELS = True if os.environ['SUNO_USE_SMALL_MODELS'] == 'True' else False

                    engine = Bark.init_from_config(config)
                    engine.load_checkpoint(
                        config,
                        checkpoint_dir=checkpoint_dir,
                        eval=True
                    )

                if engine:
                    vram_dict = VRAMDetector().detect_vram(self.session['device'])
                    self.session['free_vram_gb'] = vram_dict.get('free_vram_gb', 0)
                    models_loaded_size_gb = loaded_tts_size_gb(loaded_tts)
                    if self.session['free_vram_gb'] > models_loaded_size_gb:
                        loaded_tts[key] = engine
                return engine
        except Exception as e:
            error = f'_load_checkpoint() error: {e}'
            print(error)
            return None

    def _load_engine(self) -> None:
        try:
            msg = f"Loading BARK {self.tts_key} model, please be patient..."
            print(msg)
            cleanup_memory()
            self.engine = loaded_tts.get(self.tts_key, False)

            if not self.engine:
                if self.session['custom_model'] is not None:
                    # Custom model implementation
                    msg = f"Loading BARK custom model..."
                    print(msg)
                    try:
                        # Extract custom model files
                        custom_model_path = self.session['custom_model']
                        required_files = default_engine_settings[TTS_ENGINES['BARK']]['files']

                        # Validate custom model structure
                        model_valid = True
                        missing_files = []
                        for file_pattern in required_files:
                            # Handle different file extensions
                            if file_pattern.endswith('.pt'):
                                possible_files = [
                                    file_pattern,
                                    file_pattern.replace('.pt', '_fp16.pt'),
                                    file_pattern.replace('.pt', '_fp32.pt')
                                ]
                                found = False
                                for possible_file in possible_files:
                                    check_path = os.path.join(custom_model_path, possible_file)
                                    if os.path.exists(check_path):
                                        found = True
                                        break
                                if not found:
                                    missing_files.append(file_pattern)
                                    model_valid = False
                            else:
                                check_path = os.path.join(custom_model_path, file_pattern)
                                if not os.path.exists(check_path):
                                    missing_files.append(file_pattern)
                                    model_valid = False

                        if not model_valid:
                            error = f"Custom BARK model missing required files: {missing_files}"
                            print(error)
                            # Fall back to built-in model
                            hf_repo = models[self.session['tts_engine']][self.session['fine_tuned']]['repo']
                            hf_sub = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                            text_model_path = hf_hub_download(
                                repo_id=hf_repo,
                                filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][0]}",
                                cache_dir=self.cache_dir
                            )
                            coarse_model_path = hf_hub_download(
                                repo_id=hf_repo,
                                filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][1]}",
                                cache_dir=self.cache_dir
                            )
                            fine_model_path = hf_hub_download(
                                repo_id=hf_repo,
                                filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][2]}",
                                cache_dir=self.cache_dir
                            )
                            checkpoint_dir = os.path.dirname(text_model_path)
                        else:
                            # Use custom model files
                            text_model_path = None
                            coarse_model_path = None
                            fine_model_path = None

                            # Find the actual model files (handle different naming conventions)
                            for root, dirs, files in os.walk(custom_model_path):
                                for file in files:
                                    if file.startswith('text') and file.endswith('.pt'):
                                        text_model_path = os.path.join(root, file)
                                    elif file.startswith('coarse') and file.endswith('.pt'):
                                        coarse_model_path = os.path.join(root, file)
                                    elif file.startswith('fine') and file.endswith('.pt'):
                                        fine_model_path = os.path.join(root, file)

                            if text_model_path and coarse_model_path and fine_model_path:
                                checkpoint_dir = os.path.dirname(text_model_path)
                                self.tts_key = f"{self.session['tts_engine']}-custom-{os.path.basename(custom_model_path)}"
                                self.engine = self._load_checkpoint(
                                    tts_engine=self.session['tts_engine'],
                                    key=self.tts_key,
                                    checkpoint_dir=checkpoint_dir,
                                    device=self.session['device']
                                )
                                if not self.engine:
                                    error = f"Failed to load custom BARK model from {checkpoint_dir}"
                                    print(error)
                                    # Fall back to built-in model
                                    hf_repo = models[self.session['tts_engine']][self.session['fine_tuned']]['repo']
                                    hf_sub = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                                    text_model_path = hf_hub_download(
                                        repo_id=hf_repo,
                                        filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][0]}",
                                        cache_dir=self.cache_dir
                                    )
                                    coarse_model_path = hf_hub_download(
                                        repo_id=hf_repo,
                                        filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][1]}",
                                        cache_dir=self.cache_dir
                                    )
                                    fine_model_path = hf_hub_download(
                                        repo_id=hf_repo,
                                        filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][2]}",
                                        cache_dir=self.cache_dir
                                    )
                                    checkpoint_dir = os.path.dirname(text_model_path)
                                    self.engine = self._load_checkpoint(
                                        tts_engine=self.session['tts_engine'],
                                        key=self.tts_key,
                                        checkpoint_dir=checkpoint_dir,
                                        device=self.session['device']
                                    )
                            else:
                                error = f"Could not find required model files in custom BARK model"
                                print(error)
                                # Fall back to built-in model
                                hf_repo = models[self.session['tts_engine']][self.session['fine_tuned']]['repo']
                                hf_sub = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                                text_model_path = hf_hub_download(
                                    repo_id=hf_repo,
                                    filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][0]}",
                                    cache_dir=self.cache_dir
                                )
                                coarse_model_path = hf_hub_download(
                                    repo_id=hf_repo,
                                    filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][1]}",
                                    cache_dir=self.cache_dir
                                )
                                fine_model_path = hf_hub_download(
                                    repo_id=hf_repo,
                                    filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][2]}",
                                    cache_dir=self.cache_dir
                                )
                                checkpoint_dir = os.path.dirname(text_model_path)
                                self.engine = self._load_checkpoint(
                                    tts_engine=self.session['tts_engine'],
                                    key=self.tts_key,
                                    checkpoint_dir=checkpoint_dir,
                                    device=self.session['device']
                                )
                    except Exception as e:
                        error = f"Custom BARK model loading error: {e}"
                        print(error)
                        # Fall back to built-in model
                        hf_repo = models[self.session['tts_engine']][self.session['fine_tuned']]['repo']
                        hf_sub = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                        text_model_path = hf_hub_download(
                            repo_id=hf_repo,
                            filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][0]}",
                            cache_dir=self.cache_dir
                        )
                        coarse_model_path = hf_hub_download(
                            repo_id=hf_repo,
                            filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][1]}",
                            cache_dir=self.cache_dir
                        )
                        fine_model_path = hf_hub_download(
                            repo_id=hf_repo,
                            filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][2]}",
                            cache_dir=self.cache_dir
                        )
                        checkpoint_dir = os.path.dirname(text_model_path)
                        self.engine = self._load_checkpoint(
                            tts_engine=self.session['tts_engine'],
                            key=self.tts_key,
                            checkpoint_dir=checkpoint_dir,
                            device=self.session['device']
                        )
                else:
                    # Built-in model implementation
                    hf_repo = models[self.session['tts_engine']][self.session['fine_tuned']]['repo']
                    hf_sub = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                    text_model_path = hf_hub_download(
                        repo_id=hf_repo,
                        filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][0]}",
                        cache_dir=self.cache_dir
                    )
                    coarse_model_path = hf_hub_download(
                        repo_id=hf_repo,
                        filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][1]}",
                        cache_dir=self.cache_dir
                    )
                    fine_model_path = hf_hub_download(
                        repo_id=hf_repo,
                        filename=f"{hf_sub}{models[self.session['tts_engine']][self.session['fine_tuned']]['files'][2]}",
                        cache_dir=self.cache_dir
                    )
                    checkpoint_dir = os.path.dirname(text_model_path)
                    self.engine = self._load_checkpoint(
                        tts_engine=self.session['tts_engine'],
                        key=self.tts_key,
                        checkpoint_dir=checkpoint_dir,
                        device=self.session['device']
                    )

            if self.engine:
                msg = f'BARK {self.tts_key} Loaded!'
                print(msg)
        except Exception as e:
            error = f'_load_engine() error: {e}'
            print(error)

    def _tensor_type(self, audio_data: Any) -> torch.Tensor:
        if isinstance(audio_data, torch.Tensor):
            return audio_data
        elif isinstance(audio_data, np.ndarray):
            return torch.from_numpy(audio_data).float()
        elif isinstance(audio_data, list):
            return torch.tensor(audio_data, dtype=torch.float32)
        else:
            raise TypeError(f"Unsupported type for audio_data: {type(audio_data)}")

    def _get_resampler(self, orig_sr: int, target_sr: int) -> torchaudio.transforms.Resample:
        key = (orig_sr, target_sr)
        if key not in self.resampler_cache:
            self.resampler_cache[key] = torchaudio.transforms.Resample(
                orig_freq=orig_sr, new_freq=target_sr
            )
        return self.resampler_cache[key]

    def _check_bark_speaker(self, voice_path: str, speaker: str) -> bool:
        try:
            if self.session['language'] in language_tts[TTS_ENGINES['BARK']].keys():
                pth_voice_dir = os.path.join(default_engine_settings[TTS_ENGINES['BARK']]['speakers_path'], speaker)
                pth_voice_file = os.path.join(pth_voice_dir, f'{speaker}.pth')
                if os.path.exists(pth_voice_file):
                    return True
                else:
                    os.makedirs(pth_voice_dir, exist_ok=True)
                    default_text_file = os.path.join(voices_dir, self.session['language'], 'default.txt')
                    if os.path.exists(default_text_file):
                        default_text = Path(default_text_file).read_text(encoding="utf-8")
                        fine_tuned_params = {
                            'text_temp': float(self.session.get('bark_text_temp', self.params['text_temp'])),
                            'waveform_temp': float(self.session.get('bark_waveform_temp', self.params['waveform_temp']))
                        }
                        with torch.no_grad():
                            result = self.engine.synthesize(
                                default_text,
                                speaker_wav=voice_path,
                                speaker=speaker,
                                voice_dir=pth_voice_dir,
                                **fine_tuned_params
                            )
                        del result
                        return True
            return True
        except Exception as e:
            error = f'_check_bark_speaker() error: {e}'
            print(error)
            return False

    def convert(self, sentence_index: int, sentence: str) -> bool:
        try:
            # Import specific exceptions
            from lib.classes.exceptions import TTSEngineError, AudioProcessingError, FileOperationError, ProcessingError, ExceptionHandler, ErrorSeverity, ValidationError

            # Validate input parameters
            if not sentence or not isinstance(sentence, str):
                raise ValidationError(
                    message="Invalid sentence input for BARK conversion",
                    context={'sentence_index': sentence_index, 'sentence': sentence}
                )

            if not self.engine:
                raise TTSEngineError(
                    message="BARK engine is not initialized",
                    engine_name="BARK",
                    severity=ErrorSeverity.CRITICAL
                )

            speaker = None
            audio_sentence = False
            settings = self.params

            # Set up voice path with validation
            try:
                settings['voice_path'] = (
                    self.session['voice'] if self.session['voice'] is not None
                    else models[self.session['tts_engine']][self.session['fine_tuned']]['voice']
                )
            except (KeyError, TypeError) as e:
                raise TTSEngineError(
                    message="Failed to determine voice path for BARK engine",
                    engine_name="BARK",
                    original_exception=e
                )

            # Handle speaker setup
            if settings['voice_path'] is not None:
                try:
                    speaker = re.sub(r'\.wav$', '', os.path.basename(settings['voice_path']))
                    if (settings['voice_path'] not in default_engine_settings[TTS_ENGINES['BARK']]['voices'].keys() and
                        self.session['custom_model_dir'] not in settings['voice_path']):
                        if not self._check_bark_speaker(settings['voice_path'], speaker):
                            raise TTSEngineError(
                                message=f"Could not create BARK speaker for voice in {self.session['language']}",
                                engine_name="BARK",
                                severity=ErrorSeverity.HIGH
                            )
                except Exception as e:
                    raise TTSEngineError(
                        message="Failed to set up BARK speaker",
                        engine_name="BARK",
                        original_exception=e
                    )

            # Set up engine and device
            try:
                self.engine.to(self.session['device'])
            except Exception as e:
                raise TTSEngineError(
                    message="Failed to move BARK engine to target device",
                    engine_name="BARK",
                    original_exception=e,
                    context={'device': self.session['device']}
                )

            final_sentence_file = os.path.join(self.session['chapters_dir_sentences'], f'{sentence_index}.{default_audio_proc_format}')

            # Handle special sentence types (break/pause)
            if sentence == TTS_SML['break']:
                try:
                    silence_time = int(np.random.uniform(0.3, 0.6) * 100) / 100
                    break_tensor = torch.zeros(1, int(settings['samplerate'] * silence_time))
                    self.audio_segments.append(break_tensor.clone())
                    return True
                except Exception as e:
                    raise AudioProcessingError(
                        message="Failed to create break audio tensor",
                        original_exception=e
                    )

            elif not sentence.replace('—', '').strip() or sentence == TTS_SML['pause']:
                try:
                    silence_time = int(np.random.uniform(1.0, 1.8) * 100) / 100
                    pause_tensor = torch.zeros(1, int(settings['samplerate'] * silence_time))
                    self.audio_segments.append(pause_tensor.clone())
                    return True
                except Exception as e:
                    raise AudioProcessingError(
                        message="Failed to create pause audio tensor",
                        original_exception=e
                    )

            # Process regular sentences
            try:
                # Pre-process sentence
                if sentence.endswith("'"):
                    sentence = sentence[:-1]

                trim_audio_buffer = 0.002
                sentence += '…' if sentence[-1].isalnum() else ''

                # Determine speaker directory
                if speaker in default_engine_settings[self.session['tts_engine']]['voices'].keys():
                    bark_dir = default_engine_settings[self.session['tts_engine']]['speakers_path']
                else:
                    bark_dir = os.path.join(os.path.dirname(settings['voice_path']), 'bark')

                pth_voice_dir = os.path.join(bark_dir, speaker)
                pth_voice_file = os.path.join(bark_dir, speaker, f'{speaker}.pth')

                # Set up fine-tuned parameters
                fine_tuned_params = {
                    'text_temp': float(self.session.get('bark_text_temp', settings['text_temp'])),
                    'waveform_temp': float(self.session.get('bark_waveform_temp', settings['waveform_temp']))
                }

                # Synthesize audio with BARK engine
                with torch.no_grad():
                    result = self.engine.synthesize(
                        sentence,
                        speaker=speaker,
                        voice_dir=pth_voice_dir,
                        **fine_tuned_params
                    )

                # Process audio result
                audio_sentence = result.get('wav')
                if not is_audio_data_valid(audio_sentence):
                    raise AudioProcessingError(
                        message="BARK engine produced invalid audio data",
                        context={'sentence': sentence, 'speaker': speaker}
                    )

                # Convert and process audio tensor
                audio_sentence = audio_sentence.tolist()
                sourceTensor = self._tensor_type(audio_sentence)
                audio_tensor = sourceTensor.clone().detach().unsqueeze(0).cpu()

                # Apply audio trimming if needed
                if sentence[-1].isalnum() or sentence[-1] == '—':
                    audio_tensor = trim_audio(audio_tensor.squeeze(), settings['samplerate'], 0.001, trim_audio_buffer).unsqueeze(0)

                # Validate audio tensor
                if audio_tensor is None or audio_tensor.numel() == 0:
                    raise AudioProcessingError(
                        message="Audio tensor is empty after processing",
                        context={'sentence_length': len(sentence)}
                    )

                # Add audio to segments
                self.audio_segments.append(audio_tensor)

                # Add optional break if sentence doesn't end with punctuation
                if not re.search(r'\w$', sentence, flags=re.UNICODE) and sentence[-1] != '—':
                    silence_time = int(np.random.uniform(0.3, 0.6) * 100) / 100
                    break_tensor = torch.zeros(1, int(settings['samplerate'] * silence_time))
                    self.audio_segments.append(break_tensor.clone())

                # Combine audio segments
                if self.audio_segments:
                    audio_tensor = torch.cat(self.audio_segments, dim=-1)
                    start_time = self.sentences_total_time
                    duration = round((audio_tensor.shape[-1] / settings['samplerate']), 2)
                    end_time = start_time + duration
                    self.sentences_total_time = end_time

                    # Create sentence metadata
                    sentence_obj = {
                        "start": start_time,
                        "end": end_time,
                        "text": sentence,
                        "resume_check": self.sentence_idx
                    }

                    # Add to VTT file
                    from lib.classes.tts_engines.common.utils import append_sentence2vtt
                    self.sentence_idx = append_sentence2vtt(sentence_obj, self.vtt_path)

                    if self.sentence_idx:
                        # Save audio file
                        try:
                            torchaudio.save(final_sentence_file, audio_tensor, settings['samplerate'], format=default_audio_proc_format)
                        except Exception as e:
                            raise FileOperationError(
                                message=f"Failed to save audio file: {final_sentence_file}",
                                original_exception=e,
                                context={'format': default_audio_proc_format}
                            )

                        # Clean up memory
                        del audio_tensor
                        cleanup_memory()

                    # Reset segments for next sentence
                    self.audio_segments = []

                    # Verify file was created
                    if not os.path.exists(final_sentence_file):
                        raise FileOperationError(
                            message=f"Audio file was not created: {final_sentence_file}",
                            context={'expected_size': audio_tensor.shape}
                        )

                    return True

            except AudioProcessingError:
                raise  # Re-raise as already properly formatted
            except FileOperationError:
                raise  # Re-raise as already properly formatted
            except Exception as e:
                raise AudioProcessingError(
                    message="Unexpected error during BARK audio processing",
                    original_exception=e,
                    context={'sentence': sentence[:50] + '...' if len(sentence) > 50 else sentence}
                )

        except TTSEngineError:
            raise  # Re-raise as already properly formatted
        except AudioProcessingError:
            raise  # Re-raise as already properly formatted
        except FileOperationError:
            raise  # Re-raise as already properly formatted
        except ValidationError as e:
            raise  # Re-raise as already properly formatted
        except Exception as e:
            # Handle any other unexpected errors in convert method
            TTSEngineError(
                message="Unexpected error in BARK convert method",
                engine_name="BARK",
                severity=ErrorSeverity.CRITICAL,
                original_exception=e,
                context={
                    'sentence_index': sentence_index,
                    'sentence_length': len(sentence) if sentence else 0,
                    'speaker': speaker
                }
            )
            return False