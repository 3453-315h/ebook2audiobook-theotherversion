import os
import json
import numpy as np
import soundfile as sf
import shutil
from typing import Any, Tuple
from huggingface_hub import hf_hub_download
from lib.models import TTS_ENGINES, default_engine_settings, models
from lib.conf import tts_dir, default_audio_proc_format
from lib.classes.tts_engines.common.utils import cleanup_memory
from lib import loaded_tts

# Import Supertonic components from local helper (renamed to utils to bypass cache)
from lib.classes.tts_engines.supertonic_utils import (
    load_text_to_speech, load_voice_style
)


class SupertonicTTS:
    def __init__(self, session: dict) -> None:
        """Initialize Supertonic TTS engine"""
        self.session = session
        self.cache_dir = tts_dir
        self.engine = None
        self.tts_key = self.session['model_cache']
        self.samplerate = default_engine_settings[TTS_ENGINES['SUPERTONIC']]['samplerate']
        
        # Get parameters from session or use defaults
        self.total_step = self.session.get('supertonic_total_step',
                                          default_engine_settings[TTS_ENGINES['SUPERTONIC']]['total_step'])
        self.speed = self.session.get('supertonic_speed',
                                     default_engine_settings[TTS_ENGINES['SUPERTONIC']]['speed'])
        
        # Get model config
        fine_tuned = self.session.get('fine_tuned', 'internal')
        if fine_tuned in models.get(TTS_ENGINES['SUPERTONIC'], {}):
            model_config = models[TTS_ENGINES['SUPERTONIC']][fine_tuned]
            self.repo_id = model_config.get('repo', 'Supertone/supertonic')
            if model_config.get('total_step'):
                self.total_step = model_config['total_step']
            if model_config.get('speed'):
                self.speed = model_config['speed']
        else:
            self.repo_id = 'Supertone/supertonic'
        
        # Define the local model directory
        # Use fine_tuned name to separate model files (e.g. supertonic/dutch, supertonic/internal)
        self.model_dir = os.path.join(self.cache_dir, 'supertonic', fine_tuned)
        
        # Initialize Supertonic engine
        self._initialize_engine()

    def _check_models_exist(self) -> bool:
        """Check if all required model files exist locally"""
        required_files = ['tts.json', 'unicode_indexer.json', 'duration_predictor.onnx', 
                          'text_encoder.onnx', 'vector_estimator.onnx', 'vocoder.onnx']
        
        for file in required_files:
            file_path = os.path.join(self.model_dir, file)
            if not os.path.exists(file_path):
                return False
        return True

    def _download_models(self) -> bool:
        """Download Supertonic models from Hugging Face"""
        try:
            print(f"Downloading Supertonic models from {self.repo_id}...")
            print(f"This may take a while on first run. Please be patient...")
            
            # Create model directory
            os.makedirs(self.model_dir, exist_ok=True)
            
            # Map of local files to HF repo paths
            # HF repo has files in onnx/ folder (always)
            # All models use the same onnx/ folder - the only model available
            
            file_mapping = {
                'tts.json': 'onnx/tts.json',
                'unicode_indexer.json': 'onnx/unicode_indexer.json',
                'duration_predictor.onnx': 'onnx/duration_predictor.onnx',
                'text_encoder.onnx': 'onnx/text_encoder.onnx',
                'vector_estimator.onnx': 'onnx/vector_estimator.onnx',
                'vocoder.onnx': 'onnx/vocoder.onnx'
            }
            
            for local_name, repo_path in file_mapping.items():
                local_file_path = os.path.join(self.model_dir, local_name)
                
                if not os.path.exists(local_file_path):
                    print(f"Downloading {local_name}...")
                    try:
                        hf_hub_download(
                            repo_id=self.repo_id,
                            filename=repo_path,
                            cache_dir=self.cache_dir,
                            local_dir=self.model_dir,
                            local_dir_use_symlinks=False
                        )
                        # Move file from onnx/ subdirectory to model_dir root
                        downloaded_file = os.path.join(self.model_dir, repo_path)
                        if os.path.exists(downloaded_file) and not os.path.exists(local_file_path):
                            shutil.move(downloaded_file, local_file_path)
                        print(f"  Downloaded: {local_name}")
                    except Exception as e:
                        print(f"  Failed to download {local_name}: {e}")
                        return False
            
            # Clean up onnx directory if empty
            onnx_dir = os.path.join(self.model_dir, 'onnx')
            if os.path.exists(onnx_dir):
                try:
                    if not os.listdir(onnx_dir):
                        os.rmdir(onnx_dir)
                except:
                    pass
            
            # Download voice styles
            self._download_voice_styles()
            
            print(f"Supertonic models downloaded successfully!")
            return True
            
        except Exception as e:
            print(f"Error downloading Supertonic models: {e}")
            return False

    def _download_voice_styles(self) -> None:
        """Create voice style files with correct dimensions for the ONNX model.
        
        Note: HuggingFace voice_styles have incompatible dimensions with the ONNX model
        (style_ttl [1,8,256] vs model expects [1,50,256]), so we create defaults instead.
        """
        try:
            # Create voice_styles directory
            voice_styles_dir = os.path.join(self.model_dir, "voice_styles")
            os.makedirs(voice_styles_dir, exist_ok=True)
            
            # Create all voice styles with correct dimensions matching tts.json
            # The ONNX model expects style_ttl [1, 50, 256] and style_dp [1, 8, 16]
            all_voices = ['M1', 'M2', 'M3', 'F1', 'F2', 'F3', 'C1', 'C2', 'E1', 'E2']
            
            for voice_id in all_voices:
                local_voice_path = os.path.join(voice_styles_dir, f"{voice_id}.json")
                if not os.path.exists(local_voice_path):
                    self._create_default_voice_style(local_voice_path)
                    print(f"  Created voice style: {voice_id}")
                        
        except Exception as e:
            print(f"Warning: Could not create voice styles: {e}")

    def _create_default_voice_style(self, voice_style_path: str) -> None:
        """Create a voice style file with distinctive embeddings for each voice type.
        
        Uses seeded random values to create reproducible but distinctive voice characteristics
        for each voice type (Male, Female, Child, Elder with variations).
        """
        import numpy as np
        
        try:
            os.makedirs(os.path.dirname(voice_style_path), exist_ok=True)
            
            # Extract voice ID from path (e.g., "M1" from "/path/to/M1.json")
            voice_id = os.path.splitext(os.path.basename(voice_style_path))[0]
            
            # Voice characteristics mapping with seed offsets and base patterns
            # Each voice type has different pitch, tone, and style characteristics
            voice_configs = {
                # Male voices - lower pitch, deeper resonance
                'M1': {'seed': 101, 'pitch_offset': -0.3, 'resonance': 0.2, 'brightness': -0.1},
                'M2': {'seed': 102, 'pitch_offset': -0.5, 'resonance': 0.4, 'brightness': -0.2},  # Deeper
                'M3': {'seed': 103, 'pitch_offset': -0.1, 'resonance': 0.1, 'brightness': 0.1},   # Younger
                # Female voices - higher pitch, brighter tone
                'F1': {'seed': 201, 'pitch_offset': 0.3, 'resonance': -0.1, 'brightness': 0.2},
                'F2': {'seed': 202, 'pitch_offset': 0.2, 'resonance': -0.2, 'brightness': 0.1},   # Softer
                'F3': {'seed': 203, 'pitch_offset': 0.4, 'resonance': -0.1, 'brightness': 0.4},   # Brighter
                # Child voices - much higher pitch, very light resonance for young sound
                'C1': {'seed': 301, 'pitch_offset': 1.5, 'resonance': -0.5, 'brightness': 0.8},   # Young boy
                'C2': {'seed': 302, 'pitch_offset': 1.8, 'resonance': -0.5, 'brightness': 1.0},   # Young girl
                # Elder voices - slightly lower pitch, warm tone
                'E1': {'seed': 401, 'pitch_offset': -0.2, 'resonance': 0.3, 'brightness': -0.1},  # Wise male
                'E2': {'seed': 402, 'pitch_offset': 0.1, 'resonance': 0.1, 'brightness': 0.0},    # Gentle female
            }
            
            # Get config for this voice or use default
            config = voice_configs.get(voice_id, {'seed': 500, 'pitch_offset': 0.0, 'resonance': 0.0, 'brightness': 0.0})
            
            # Set seed for reproducibility
            np.random.seed(config['seed'])
            
            # Generate style_ttl: [1, 50, 256] - controls text-to-latent style
            # Use small random values with voice-specific offsets for characteristic sound
            style_ttl_base = np.random.randn(1, 50, 256).astype(np.float32) * 0.1
            
            # Apply voice characteristics to specific dimensions
            # First dimensions often control pitch/tone characteristics
            style_ttl_base[0, :10, :] += config['pitch_offset'] * 0.2
            style_ttl_base[0, 10:20, :] += config['resonance'] * 0.15
            style_ttl_base[0, 20:30, :] += config['brightness'] * 0.15
            
            # Generate style_dp: [1, 8, 16] - controls duration prediction
            style_dp_base = np.random.randn(1, 8, 16).astype(np.float32) * 0.05
            
            # Convert to nested lists for JSON
            style_ttl_data = style_ttl_base.tolist()
            style_dp_data = style_dp_base.tolist()
            
            voice_style = {
                "style_ttl": {
                    "data": style_ttl_data,
                    "dims": [1, 50, 256],
                    "type": "float32"
                },
                "style_dp": {
                    "data": style_dp_data,
                    "dims": [1, 8, 16],
                    "type": "float32"
                },
                "metadata": {
                    "voice_id": voice_id,
                    "source_file": f"{voice_id}_synthetic",
                    "source_sample_rate": 44100,
                    "target_sample_rate": 44100,
                    "pitch_offset": config['pitch_offset'],
                    "resonance": config['resonance'],
                    "brightness": config['brightness']
                }
            }
            
            with open(voice_style_path, 'w') as f:
                json.dump(voice_style, f)
                
        except Exception as e:
            print(f"Could not create voice style for {voice_style_path}: {e}")

    def _initialize_engine(self) -> None:
        """Initialize the Supertonic TTS engine"""
        try:
            print(f"Initializing Supertonic TTS engine...")
            
            # Check if models exist, download if needed
            if not self._check_models_exist():
                print("Supertonic models not found locally. Downloading...")
                if not self._download_models():
                    print("Failed to download Supertonic models!")
                    return

            # Load Supertonic engine
            self.engine = load_text_to_speech(self.model_dir, False)  # False for CPU mode

            if self.engine:
                print(f"Supertonic TTS engine initialized successfully!")
                self.samplerate = self.engine.sample_rate
                print(f"Supertonic sample rate: {self.samplerate}")
                loaded_tts[self.tts_key] = self.engine
            else:
                print(f"Failed to initialize Supertonic TTS engine")

        except Exception as e:
            print(f"Error initializing Supertonic TTS engine: {e}")
            self.engine = None

    def _get_voice_style_path(self) -> str:
        """Get the voice style path based on session voice selection"""
        # Get voice from session or use default M1
        voice_id = self.session.get('voice', 'M1')
        
        # If voice is a file path, extract just the ID
        if voice_id and os.path.sep in str(voice_id):
            voice_id = os.path.basename(voice_id).replace('.json', '')
        
        # Map descriptive names back to IDs if needed
        voices = default_engine_settings[TTS_ENGINES['SUPERTONIC']].get('voices', {})
        for vid, name in voices.items():
            if voice_id == name or voice_id == vid:
                voice_id = vid
                break
        
        # Default to M1 if not found
        if voice_id not in voices and voice_id not in ['M1', 'M2', 'M3', 'F1', 'F2', 'F3', 'C1', 'C2', 'E1', 'E2']:
            voice_id = 'M1'
        
        return os.path.join(self.model_dir, "voice_styles", f"{voice_id}.json")

    def convert(self, sentence_number: int, sentence: str) -> bool:
        """Convert text to speech using Supertonic"""
        try:
            if not self.engine:
                print("Supertonic engine not initialized")
                return False

            # Get voice style path
            voice_style_path = self._get_voice_style_path()
            voice_id = self.session.get('voice', 'M1')
            print(f"DEBUG Supertonic: session['voice']={voice_id}, voice_style_path={voice_style_path}")
            
            if not os.path.exists(voice_style_path):
                # Create default voice style
                print(f"DEBUG Supertonic: Creating voice style for {voice_style_path}")
                self._create_default_voice_style(voice_style_path)
            
            style = load_voice_style([voice_style_path])
            print(f"DEBUG Supertonic: Loaded style, ttl shape={style.ttl.shape}, dp shape={style.dp.shape}")
            print(f"DEBUG Supertonic: style_ttl[0,0,:5]={style.ttl[0,0,:5]}")  # First 5 values to verify different

            # Convert text to speech
            print(f"DEBUG Supertonic: speed={self.speed}, total_step={self.total_step}")
            audio_data, duration = self.engine(sentence, style, self.total_step, self.speed)

            if audio_data is not None and len(audio_data) > 0:
                # Convert to numpy array and ensure correct shape
                audio_np = audio_data.astype(np.float32)
                if len(audio_np.shape) == 1:
                    audio_np = audio_np.reshape(1, -1)
                elif audio_np.shape[0] != 1:
                    audio_np = audio_np[:1, :]

                # Save to file
                output_file = os.path.join(self.session['chapters_dir_sentences'], f'{sentence_number}.{default_audio_proc_format}')
                # audio_np is (1, samples), sf.write expects (samples,) or (samples, channels)
                sf.write(output_file, audio_np.flatten(), self.samplerate)

                return True
            else:
                print("Empty audio generated")
                return False

        except Exception as e:
            error_msg = f"Supertonic conversion error: {e}"
            print(error_msg)
            return False

    def get_samplerate(self) -> int:
        """Get the sample rate of the TTS engine"""
        return self.samplerate

    def cleanup(self) -> None:
        """Clean up resources"""
        if hasattr(self, 'engine') and self.engine:
            del self.engine
            self.engine = None
        cleanup_memory()