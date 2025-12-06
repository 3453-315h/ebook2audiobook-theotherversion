"""
Translation Service for ebook2audiobook
Uses deep-translator library for online translation with multiple backend support
"""

import os
from typing import Optional, Tuple, List, Dict
from langdetect import detect, LangDetectException

# deep-translator supports multiple backends
try:
    from deep_translator import GoogleTranslator, MyMemoryTranslator
    DEEP_TRANSLATOR_AVAILABLE = True
except ImportError:
    DEEP_TRANSLATOR_AVAILABLE = False
    print("Warning: deep-translator not installed. Translation features disabled.")

# Import ArgosTranslator
try:
    from lib.classes.argos_translator import ArgosTranslator
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False
    print("Warning: ArgosTranslator modules not found.")


# Language mapping for deep-translator (ISO 639-1 codes)
SUPPORTED_LANGUAGES = {
    'en': 'English',
    'nl': 'Dutch',
    'de': 'German',
    'fr': 'French',
    'es': 'Spanish',
    'it': 'Italian',
    'pt': 'Portuguese',
    'ru': 'Russian',
    'zh-CN': 'Chinese (Simplified)',
    'zh-TW': 'Chinese (Traditional)',
    'ja': 'Japanese',
    'ko': 'Korean',
    'ar': 'Arabic',
    'hi': 'Hindi',
    'tr': 'Turkish',
    'pl': 'Polish',
    'sv': 'Swedish',
    'da': 'Danish',
    'no': 'Norwegian',
    'fi': 'Finnish',
    'el': 'Greek',
    'he': 'Hebrew',
    'hu': 'Hungarian',
    'cs': 'Czech',
    'ro': 'Romanian',
    'uk': 'Ukrainian',
    'bg': 'Bulgarian',
    'sr': 'Serbian',
    'id': 'Indonesian',
    'vi': 'Vietnamese',
    'th': 'Thai',
    'bn': 'Bengali',
}


class TranslationService:
    """Service class for translating text using online translation APIs"""
    
    def __init__(self, service: str = 'google'):
        """
        Initialize translation service
        
        Args:
            service: Translation backend - 'google', 'mymemory', or 'argos'
        """
        self.service = service
        self.max_chunk_size = 4500  # Google Translate limit per request
        self.argos = None
        
        if not DEEP_TRANSLATOR_AVAILABLE and service in ['google', 'mymemory']:
            raise ImportError("deep-translator library is not installed. Run: pip install deep-translator")
            
        if service == 'argos':
            if not ARGOS_AVAILABLE:
                raise ImportError("ArgosTranslator modules not found.")
            try:
                self.argos = ArgosTranslator()
                print("ArgosTranslator initialized.")
            except Exception as e:
                print(f"Failed to initialize ArgosTranslator: {e}")
    
    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the input text
        
        Args:
            text: Input text to detect language from
            
        Returns:
            Tuple of (language_code, confidence)
        """
        try:
            # Use first 1000 chars for faster detection
            sample = text[:1000] if len(text) > 1000 else text
            lang = detect(sample)
            return lang, 0.9  # langdetect doesn't provide confidence
        except LangDetectException:
            return 'en', 0.5  # Default to English if detection fails
    
    def get_supported_languages(self, service: Optional[str] = None) -> Dict[str, str]:
        """Get dictionary of supported languages based on service"""
        svc = service if service else self.service
        
        if svc == 'argos' and self.argos:
            # Argos supported targets depend on the installed packages and available downloads
            # For simplicity, we can fetch all potential targets from ArgosTranslator
            try:
                # This is a bit complex as Argos has source-dependent targets
                # We will just return a generic list or maybe just English to X for now
                # Or better, let the UI handle the dynamic list via a separate call
                # For now, let's return the intersection of our map and what Argos supports generally
                return SUPPORTED_LANGUAGES.copy() # Placeholder, we might need a specific map
            except:
                return SUPPORTED_LANGUAGES.copy()
        
        return SUPPORTED_LANGUAGES.copy()
    
    def _chunk_text(self, text: str) -> List[str]:
        """
        Split text into chunks that fit within API limits
        Tries to split on sentence boundaries
        """
        if len(text) <= self.max_chunk_size:
            return [text]
        
        chunks = []
        current_chunk = ""
        
        # Split by sentences (roughly)
        sentences = text.replace('\n', ' \n ').split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) + 2 <= self.max_chunk_size:
                current_chunk += sentence + '. '
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + '. '
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def translate(self, text: str, source_lang: str, target_lang: str, 
                  progress_callback: Optional[callable] = None) -> Tuple[bool, str, str]:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., 'en', 'nl')
            target_lang: Target language code
            progress_callback: Optional callback function(progress: float, message: str)
            
        Returns:
            Tuple of (success: bool, translated_text: str, error_message: str)
        """
        if self.service == 'google' and not DEEP_TRANSLATOR_AVAILABLE:
            return False, "", "Translation library not available"
        
        if source_lang == target_lang:
            return True, text, ""
        
        try:
            # Create translator instance
            uploaded_model = False
            
            if self.service == 'argos':
                if not self.argos:
                    return False, "", "ArgosTranslator not initialized"
                
                # Argos logic
                print(f"Translating via Argos: {source_lang} -> {target_lang}")
                error, success = self.argos.start(source_lang, target_lang)
                if not success:
                    return False, "", f"Argos setup failed: {error}"
                
                # Argos processes text directly, but might need chunking if too large?
                # Usually offline models handle sentences.
                # Let's chunk anyway to be safe and provide progress
                chunks = self._chunk_text(text)
                total_chunks = len(chunks)
                translated_chunks = []
                
                for i, chunk in enumerate(chunks):
                    if progress_callback:
                        progress = (i / total_chunks) * 100
                        progress_callback(progress, f"Translating chunk {i+1}/{total_chunks}...")
                    
                    trans, status = self.argos.process(chunk)
                    if status:
                        translated_chunks.append(trans)
                    else:
                        print(f"Chunk translation failed: {trans}")
                        translated_chunks.append(chunk) # Fallback to original
                
                translated_text = ' '.join(translated_chunks)
                return True, translated_text, ""

            elif self.service == 'google':
                translator = GoogleTranslator(source=source_lang, target=target_lang)
            elif self.service == 'mymemory':
                translator = MyMemoryTranslator(source=source_lang, target=target_lang)
            else:
                return False, "", f"Unknown translation service: {self.service}"
            
            # Chunk text for large documents (Online services)
            chunks = self._chunk_text(text)
            total_chunks = len(chunks)
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                if progress_callback:
                    progress = (i / total_chunks) * 100
                    progress_callback(progress, f"Translating chunk {i+1}/{total_chunks}...")
                
                # Translate chunk
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            
            if progress_callback:
                progress_callback(100, "Translation complete!")
            
            # Join translated chunks
            translated_text = ' '.join(translated_chunks)
            
            return True, translated_text, ""
            
        except Exception as e:
            error_msg = f"Translation error: {str(e)}"
            print(error_msg)
            return False, "", error_msg
    
    def translate_file(self, file_path: str, target_lang: str, output_path: Optional[str] = None,
                       progress_callback: Optional[callable] = None) -> Tuple[bool, str, str]:
        """
        Translate a text file
        
        Args:
            file_path: Path to input file
            target_lang: Target language code
            output_path: Optional output file path (defaults to input_translated.txt)
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (success: bool, output_path: str, error_message: str)
        """
        try:
            # Read input file
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Detect source language
            source_lang, _ = self.detect_language(text)
            
            # Translate
            success, translated_text, error = self.translate(
                text, source_lang, target_lang, progress_callback
            )
            
            if not success:
                return False, "", error
            
            # Determine output path
            if output_path is None:
                base, ext = os.path.splitext(file_path)
                output_path = f"{base}_translated{ext}"
            
            # Write translated file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(translated_text)
            
            return True, output_path, ""
            
        except Exception as e:
            error_msg = f"File translation error: {str(e)}"
            print(error_msg)
            return False, "", error_msg


def get_translation_languages() -> List[Tuple[str, str]]:
    """Get list of supported languages for UI dropdown"""
    return [(name, code) for code, name in sorted(SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])]


def translate_document(session: dict, target_lang: str, service: str = 'google',
                       progress_callback: Optional[callable] = None) -> Tuple[bool, str, str]:
    """
    Translate the uploaded document in the session
    
    Args:
        session: Session dictionary containing file info
        target_lang: Target language code
        service: Translation service to use
        progress_callback: Optional progress callback
        
    Returns:
        Tuple of (success: bool, translated_file_path: str, error_message: str)
    """
    try:
        print(f"translate_document called: target={target_lang}, service={service}")
        print(f"Session keys: {list(session.keys())}")
        
        translator = TranslationService(service=service)
        
        # Find the input file from session
        input_file = None
        
        # Priority 1: Check txt_file (processed text)
        if 'txt_file' in session and session['txt_file'] and os.path.exists(session['txt_file']):
            input_file = session['txt_file']
            print(f"Using txt_file: {input_file}")
        
        # Priority 2: Check ebook (uploaded file) for txt files
        elif 'ebook' in session and session['ebook'] and isinstance(session['ebook'], str):
            ebook_path = session['ebook']
            if os.path.exists(ebook_path) and ebook_path.lower().endswith('.txt'):
                input_file = ebook_path
                print(f"Using ebook (txt): {input_file}")
        
        # Priority 3: Check chapters_dir
        elif 'chapters_dir' in session and session['chapters_dir']:
            chapters_dir = session['chapters_dir']
            if os.path.exists(chapters_dir):
                txt_files = [f for f in os.listdir(chapters_dir) if f.endswith('.txt')]
                if txt_files:
                    input_file = os.path.join(chapters_dir, txt_files[0])
                    print(f"Using chapters_dir: {input_file}")
        
        if not input_file:
            print(f"No text file found. session['txt_file']={session.get('txt_file')}, session['ebook']={session.get('ebook')}")
            return False, "", "No text file found in session. Please upload a .txt file."
        
        # Create translated file path
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_translated_{target_lang}{ext}"
        
        print(f"Translating {input_file} -> {output_file}")
        
        # Translate
        success, output_path, error = translator.translate_file(
            input_file, target_lang, output_file, progress_callback
        )
        
        if success:
            print(f"Translation successful: {output_path}")
            # Store original file reference
            session['original_txt_file'] = session.get('txt_file', input_file)
            session['original_ebook'] = session.get('ebook', input_file)
            
            # Store the ROOT ebook (the very first one uploaded) and never overwrite it
            # This allows us to match the frontend file input (which stays as the original)
            # to the current translated file in the session
            if 'root_ebook' not in session:
                session['root_ebook'] = session.get('ebook', input_file)
            
            # Update session with translated file
            # Update session with translated file
            session['txt_file'] = output_path
            session['ebook'] = output_path  # Also update ebook so workflow uses translated file
            session['translation_target_lang'] = target_lang
            
            # Re-extract chapters from the translated file so audio uses translated text
            try:
                from lib.functions import extract_preview_chapters
                session_id = session.get('id')
                if session_id:
                    result = extract_preview_chapters(output_path, session_id)
                    if result:
                        print(f"Re-extracted {len(result)} chapters from translated file")
                    else:
                        print("Warning: Could not re-extract chapters from translated file")
            except Exception as e:
                print(f"Warning: Failed to re-extract chapters: {e}")
            
        return success, output_path, error
        
    except Exception as e:
        error_msg = f"Document translation error: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return False, "", error_msg
