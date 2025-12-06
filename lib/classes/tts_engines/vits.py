import os
import tempfile
print("DEBUG: LOADED VITS FROM", __file__)
import regex as re
import torch
import torchaudio
import threading
import numpy as np
import subprocess
import shutil
import uuid
from typing import Any
from pathlib import Path
from huggingface_hub import hf_hub_download

from lib.classes.vram_detector import VRAMDetector
from lib.classes.tts_engines.common.utils import cleanup_memory, loaded_tts_size_gb
from lib.classes.tts_engines.common.audio_filters import detect_gender, trim_audio, normalize_audio, is_audio_data_valid
from lib import *
from lib.models import TTS_ENGINES, default_engine_settings, models, TTS_VOICE_CONVERSION, default_vc_model

lock = threading.Lock()

class VitsTTS:
    def __init__(self, session: Any):
        try:
            self.session = session
            self.cache_dir = tts_dir
            self.engine = None
            self.tts_key = self.session['model_cache']
            self.tts_zs_key = default_vc_model.rsplit('/', 1)[-1]
            self.engine_zs = None
            self.sentences_total_time = 0.0
            self.sentence_idx = 1
            self.params = {
                'samplerate': models[self.session['tts_engine']][self.session['fine_tuned']]['samplerate'],
                'semitones': {}
            }
            self.vtt_path = os.path.join(self.session['process_dir'], Path(self.session['final_name']).stem + '.vtt')
            self.resampler_cache = {}
            self.audio_segments = []
            self._load_engine()
            self._load_engine_zs()
        except Exception as e:
            error = f'__init__() error: {e}'
            print(error)

    def _load_api(self, key: str, model_path: str, device: str) -> Any:
        global lock
        try:
            with lock:
                from TTS.api import TTS as TTSEngine
                engine = loaded_tts.get(key, False)
                if not engine:
                    engine = TTSEngine(model_path)
                if engine:
                    vram_dict = VRAMDetector().detect_vram(self.session['device'])
                    self.session['free_vram_gb'] = vram_dict.get('free_vram_gb', 0)
                    models_loaded_size_gb = loaded_tts_size_gb(loaded_tts)
                    if self.session['free_vram_gb'] > models_loaded_size_gb:
                        loaded_tts[key] = engine
                return engine
        except Exception as e:
            error = f"_load_api() error: {e}"
            print(error)
            return None

    def _load_engine(self) -> None:
        try:
            msg = f"Loading VITS {self.tts_key} model, please be patient..."
            print(msg)
            cleanup_memory()
            self.engine = loaded_tts.get(self.tts_key, False)

            if not self.engine:
                if self.session['custom_model'] is not None:
                    # Custom model implementation
                    msg = f"Loading VITS custom model..."
                    print(msg)
                    try:
                        # Extract custom model files
                        custom_model_path = self.session['custom_model']
                        required_files = default_engine_settings[TTS_ENGINES['VITS']]['files']

                        # Validate custom model structure
                        model_valid = True
                        missing_files = []
                        for file_pattern in required_files:
                            check_path = os.path.join(custom_model_path, file_pattern)
                            if not os.path.exists(check_path):
                                missing_files.append(file_pattern)
                                model_valid = False

                        if not model_valid:
                            error = f"Custom VITS model missing required files: {missing_files}"
                            print(error)
                            # Fall back to built-in model
                            iso_dir = language_tts[self.session['tts_engine']][self.session['language']]
                            sub_dict = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                            sub = next((key for key, lang_list in sub_dict.items() if iso_dir in lang_list), None)
                            if sub is not None:
                                self.params['samplerate'] = models[TTS_ENGINES['VITS']][self.session['fine_tuned']]['samplerate'][sub]
                                model_path = models[self.session['tts_engine']][self.session['fine_tuned']]['repo'].replace("[lang_iso1]", iso_dir).replace("[xxx]", sub)
                                self.tts_key = model_path
                                self.engine = self._load_api(self.tts_key, model_path, self.session['device'])
                            else:
                                msg = f"VITS checkpoint for {self.session['language']} not found!"
                                print(msg)
                        else:
                            # Use custom model files
                            # Find the model file (handle different naming conventions)
                            model_file = None
                            for root, dirs, files in os.walk(custom_model_path):
                                for file in files:
                                    if file.endswith('.pth') or file.endswith('.pt'):
                                        model_file = os.path.join(root, file)
                                        break
                                if model_file:
                                    break

                            if model_file:
                                model_path = os.path.dirname(model_file)
                                self.tts_key = f"{self.session['tts_engine']}-custom-{os.path.basename(custom_model_path)}"
                                self.engine = self._load_api(self.tts_key, model_path, self.session['device'])
                                if not self.engine:
                                    error = f"Failed to load custom VITS model from {model_path}"
                                    print(error)
                                    # Fall back to built-in model
                                    iso_dir = language_tts[self.session['tts_engine']][self.session['language']]
                                    sub_dict = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                                    sub = next((key for key, lang_list in sub_dict.items() if iso_dir in lang_list), None)
                                    if sub is not None:
                                        self.params['samplerate'] = models[TTS_ENGINES['VITS']][self.session['fine_tuned']]['samplerate'][sub]
                                        model_path = models[self.session['tts_engine']][self.session['fine_tuned']]['repo'].replace("[lang_iso1]", iso_dir).replace("[xxx]", sub)
                                        self.tts_key = model_path
                                        self.engine = self._load_api(self.tts_key, model_path, self.session['device'])
                                    else:
                                        msg = f"VITS checkpoint for {self.session['language']} not found!"
                                        print(msg)
                            else:
                                error = f"Could not find model file in custom VITS model"
                                print(error)
                                # Fall back to built-in model
                                iso_dir = language_tts[self.session['tts_engine']][self.session['language']]
                                sub_dict = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                                sub = next((key for key, lang_list in sub_dict.items() if iso_dir in lang_list), None)
                                if sub is not None:
                                    self.params['samplerate'] = models[TTS_ENGINES['VITS']][self.session['fine_tuned']]['samplerate'][sub]
                                    model_path = models[self.session['tts_engine']][self.session['fine_tuned']]['repo'].replace("[lang_iso1]", iso_dir).replace("[xxx]", sub)
                                    self.tts_key = model_path
                                    self.engine = self._load_api(self.tts_key, model_path, self.session['device'])
                                else:
                                    msg = f"VITS checkpoint for {self.session['language']} not found!"
                                    print(msg)
                    except Exception as e:
                        error = f"Custom VITS model loading error: {e}"
                        print(error)
                        # Fall back to built-in model
                        iso_dir = language_tts[self.session['tts_engine']][self.session['language']]
                        sub_dict = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                        sub = next((key for key, lang_list in sub_dict.items() if iso_dir in lang_list), None)
                        if sub is not None:
                            self.params['samplerate'] = models[TTS_ENGINES['VITS']][self.session['fine_tuned']]['samplerate'][sub]
                            model_path = models[self.session['tts_engine']][self.session['fine_tuned']]['repo'].replace("[lang_iso1]", iso_dir).replace("[xxx]", sub)
                            self.tts_key = model_path
                            self.engine = self._load_api(self.tts_key, model_path, self.session['device'])
                        else:
                            msg = f"VITS checkpoint for {self.session['language']} not found!"
                            print(msg)
                else:
                    # Built-in model implementation
                    iso_dir = language_tts[self.session['tts_engine']][self.session['language']]
                    sub_dict = models[self.session['tts_engine']][self.session['fine_tuned']]['sub']
                    sub = next((key for key, lang_list in sub_dict.items() if iso_dir in lang_list), None)

                    if sub is not None:
                        self.params['samplerate'] = models[TTS_ENGINES['VITS']][self.session['fine_tuned']]['samplerate'][sub]
                        model_path = models[self.session['tts_engine']][self.session['fine_tuned']]['repo'].replace("[lang_iso1]", iso_dir).replace("[xxx]", sub)
                        self.tts_key = model_path
                        self.engine = self._load_api(self.tts_key, model_path, self.session['device'])
                    else:
                        msg = f"VITS checkpoint for {self.session['language']} not found!"
                        print(msg)

            if self.engine:
                msg = f'VITS {self.tts_key} Loaded!'
                print(msg)
        except Exception as e:
            error = f'_load_engine() error: {e}'
            print(error)

    def _load_engine_zs(self) -> Any:
        try:
            msg = f"Loading ZeroShot {self.tts_zs_key} model, please be patient..."
            print(msg)
            cleanup_memory()
            self.engine_zs = loaded_tts.get(self.tts_zs_key, False)
            if not self.engine_zs:
                self.engine_zs = self._load_api(self.tts_zs_key, default_vc_model, self.session['device'])
            if self.engine_zs:
                self.session['model_zs_cache'] = self.tts_zs_key
                msg = f'ZeroShot {self.tts_zs_key} Loaded!'
                print(msg)
        except Exception as e:
            error = f'_load_engine_zs() error: {e}'
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

    def _resample_wav(self, wav_path: str, expected_sr: int) -> str:
        waveform, orig_sr = torchaudio.load(wav_path)
        if orig_sr == expected_sr and waveform.size(0) == 1:
            return wav_path
        if waveform.size(0) > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if orig_sr != expected_sr:
            resampler = self._get_resampler(orig_sr, expected_sr)
            waveform = resampler(waveform)
        wav_tensor = waveform.squeeze(0)
        wav_numpy = wav_tensor.cpu().numpy()
        os.makedirs(tmp_dir, exist_ok=True)
        tmp_fh = tempfile.NamedTemporaryFile(dir=tmp_dir, suffix=".wav", delete=False)
        tmp_path = tmp_fh.name
        tmp_fh.close()
        import soundfile as sf
        sf.write(tmp_path, wav_numpy, expected_sr, subtype="PCM_16")
        return tmp_path

    def convert(self, sentence_index: int, sentence: str) -> bool:
        try:
            speaker = None
            audio_sentence = False
            settings = self.params
            settings['voice_path'] = (
                self.session['voice'] if self.session['voice'] is not None
                else models[self.session['tts_engine']][self.session['fine_tuned']]['voice']
            )

            if self.engine:
                self.engine.to(self.session['device'])
                final_sentence_file = os.path.join(self.session['chapters_dir_sentences'], f'{sentence_index}.{default_audio_proc_format}')

                if sentence == TTS_SML['break']:
                    silence_time = int(np.random.uniform(0.3, 0.6) * 100) / 100
                    break_tensor = torch.zeros(1, int(settings['samplerate'] * silence_time))
                    self.audio_segments.append(break_tensor.clone())
                    return True
                elif not sentence.replace('—', '').strip() or sentence == TTS_SML['pause']:
                    silence_time = int(np.random.uniform(1.0, 1.8) * 100) / 100
                    pause_tensor = torch.zeros(1, int(settings['samplerate'] * silence_time))
                    self.audio_segments.append(pause_tensor.clone())
                    return True
                else:
                    if sentence.endswith("'"):
                        sentence = sentence[:-1]

                    trim_audio_buffer = 0.004
                    sentence += '—' if sentence[-1].isalnum() else ''

                    speaker_argument = {}
                    if self.session['language'] == 'eng' and 'vctk/vits' in models[self.session['tts_engine']]['internal']['sub']:
                        if (self.session['language'] in models[self.session['tts_engine']]['internal']['sub']['vctk/vits'] or
                            self.session['language_iso1'] in models[self.session['tts_engine']]['internal']['sub']['vctk/vits']):
                            speaker_argument = {"speaker": 'p262'}
                    elif self.session['language'] == 'cat' and 'custom/vits' in models[self.session['tts_engine']]['internal']['sub']:
                        if (self.session['language'] in models[self.session['tts_engine']]['internal']['sub']['custom/vits'] or
                            self.session['language_iso1'] in models[self.session['tts_engine']]['internal']['sub']['custom/vits']):
                            speaker_argument = {"speaker": '09901'}

                    if settings['voice_path'] is not None:
                        proc_dir = os.path.join(self.session['voice_dir'], 'proc')
                        os.makedirs(proc_dir, exist_ok=True)
                        tmp_in_wav = os.path.join(proc_dir, f"{uuid.uuid4()}.wav")
                        tmp_out_wav = os.path.join(proc_dir, f"{uuid.uuid4()}.wav")

                        with torch.no_grad():
                            self.engine.tts_to_file(
                                text=sentence,
                                file_path=tmp_in_wav,
                                **speaker_argument
                            )

                        if settings['voice_path'] in settings['semitones'].keys():
                            semitones = settings['semitones'][settings['voice_path']]
                        elif os.path.exists(settings['voice_path']):
                            voice_path_gender = detect_gender(settings['voice_path'])
                            voice_builtin_gender = detect_gender(tmp_in_wav)
                            msg = f"Cloned voice seems to be {voice_path_gender}\nBuiltin voice seems to be {voice_builtin_gender}"
                            print(msg)
                            if voice_builtin_gender != voice_path_gender:
                                semitones = -4 if voice_path_gender == 'male' else 4
                                msg = f"Adapting builtin voice frequencies from the clone voice..."
                                print(msg)
                            else:
                                semitones = 0
                            settings['semitones'][settings['voice_path']] = semitones
                        else:
                            semitones = 0

                        if semitones > 0:
                            try:
                                cmd = [
                                    shutil.which('sox'), tmp_in_wav,
                                    "-r", str(settings['samplerate']), tmp_out_wav,
                                    "pitch", str(semitones * 100)
                                ]
                                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                                error = f"Subprocess error: {e}"
                                print(error)
                                return False
                        else:
                            tmp_out_wav = tmp_in_wav

                        if self.engine_zs:
                            settings['samplerate'] = TTS_VOICE_CONVERSION[self.tts_zs_key]['samplerate']
                            source_wav = self._resample_wav(tmp_out_wav, settings['samplerate'])
                            target_wav = self._resample_wav(settings['voice_path'], settings['samplerate'])
                            audio_sentence = self.engine_zs.voice_conversion(
                                source_wav=source_wav,
                                target_wav=target_wav
                            )
                        else:
                            error = f'Engine {self.tts_zs_key} is None'
                            print(error)
                            return False

                        if os.path.exists(tmp_in_wav):
                            os.remove(tmp_in_wav)
                        if os.path.exists(tmp_out_wav):
                            os.remove(tmp_out_wav)
                        if os.path.exists(source_wav):
                            os.remove(source_wav)
                    else:
                        with torch.no_grad():
                            audio_sentence = self.engine.tts(
                                text=sentence,
                                **speaker_argument
                            )

                    if is_audio_data_valid(audio_sentence):
                        sourceTensor = self._tensor_type(audio_sentence)
                        audio_tensor = sourceTensor.clone().detach().unsqueeze(0).cpu()

                        if sentence[-1].isalnum() or sentence[-1] == '—':
                            audio_tensor = trim_audio(audio_tensor.squeeze(), settings['samplerate'], 0.001, trim_audio_buffer).unsqueeze(0)

                        if audio_tensor is not None and audio_tensor.numel() > 0:
                            self.audio_segments.append(audio_tensor)
                            if not re.search(r'\w$', sentence, flags=re.UNICODE) and sentence[-1] != '—':
                                silence_time = int(np.random.uniform(0.3, 0.6) * 100) / 100
                                break_tensor = torch.zeros(1, int(settings['samplerate'] * silence_time))
                                self.audio_segments.append(break_tensor.clone())

                            if self.audio_segments:
                                audio_tensor = torch.cat(self.audio_segments, dim=-1)
                                start_time = self.sentences_total_time
                                duration = round((audio_tensor.shape[-1] / settings['samplerate']), 2)
                                end_time = start_time + duration
                                self.sentences_total_time = end_time

                                sentence_obj = {
                                    "start": start_time,
                                    "end": end_time,
                                    "text": sentence,
                                    "resume_check": self.sentence_idx
                                }

                                from lib.classes.tts_engines.common.utils import append_sentence2vtt
                                self.sentence_idx = append_sentence2vtt(sentence_obj, self.vtt_path)

                                if self.sentence_idx:
                                    torchaudio.save(final_sentence_file, audio_tensor, settings['samplerate'], format=default_audio_proc_format)
                                    del audio_tensor
                                    cleanup_memory()

                            self.audio_segments = []
                            if os.path.exists(final_sentence_file):
                                return True
                            else:
                                error = f"Cannot create {final_sentence_file}"
                                print(error)
                                return False
                    else:
                        error = f"audio_sentence not valid"
                        print(error)
                        return False
            else:
                error = f"VITS engine could not be loaded!"
                print(error)
                return False
        except Exception as e:
            error = f'VitsTTS.convert(): {e}'
            raise ValueError(e)
            return False