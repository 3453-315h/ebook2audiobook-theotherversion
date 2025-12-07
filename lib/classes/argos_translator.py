import os
import tempfile
import argostranslate.package
import argostranslate.translate

from iso639 import Lang
from lib.conf import models_dir
from lib.lang import language_mapping

# NOTE: source_lang and target_lang must be iso639-1 (2 letters)

class ArgosTranslator:
    def __init__(self,neural_machine:str="argostranslate"):
        self.neural_machine=neural_machine
        self.translation=None
        self.install_cached_models()

    def install_cached_models(self):
        """
        Check /app/argos_cache for .argosmodel files and install them if not already installed.
        This allows pre-downloaded models to be used.
        """
        cache_dir = "/app/argos_cache"
        if not os.path.isdir(cache_dir):
            return

        # Simple flag to avoid repeated checks if instantiated multiple times
        if getattr(self, '_cached_models_checked', False):
            return

        print(f"[DEBUG] Argos: Checking for cached models in {cache_dir}...")
        try:
            # We don't want to reinstall if already installed.
            # But argostranslate doesn't make it easy to map file -> package without opening it.
            # However, install_from_path handles this gracefully usually.
            # Let's verify package availability first to save time.
            
            argostranslate.package.update_package_index() # Ensure index is ready (local or remote)
            installed_packages = argostranslate.package.get_installed_packages()
            installed_tags = {f"{p.from_code}->{p.to_code}" for p in installed_packages}

            model_files = [f for f in os.listdir(cache_dir) if f.endswith('.argosmodel')]
            if not model_files:
                print(f"[DEBUG] Argos: No cached models found.")
                self._cached_models_checked = True
                return

            print(f"[DEBUG] Argos: Found {len(model_files)} cached model files.")
            
            count_installed = 0
            for filename in model_files:
                filepath = os.path.join(cache_dir, filename)
                # Optimization: Try to guess language from filename if it follows standard naming
                # e.g. translate-en_de-1.9.argosmodel
                try:
                    # Very naive check to skip likely installed ones?
                    # "translate-en_de" -> "en->de"
                    if "translate-" in filename:
                        parts = filename.split('-')[1].split('_') # en, de
                        if len(parts) >= 2:
                            src = parts[0]
                            tgt = parts[1].split('.')[0] # de (?)
                            if f"{src}->{tgt}" in installed_tags:
                                # skipping...
                                continue
                except:
                   pass

                print(f"[DEBUG] Argos: Installing cached model: {filename}")
                try:
                    argostranslate.package.install_from_path(filepath)
                    count_installed += 1
                except Exception as e:
                    print(f"[ERROR] Argos: Failed to install {filename}: {e}")
            
            if count_installed > 0:
                 print(f"[DEBUG] Argos: Successfully installed {count_installed} cached models.")
            else:
                 print(f"[DEBUG] Argos: No new models installed from cache.")

        except Exception as e:
            print(f"[ERROR] Argos: Error during cache installation: {e}")
        
        self._cached_models_checked = True
        
    def get_language_iso3(self,lang_iso1:str)->str:
        lang=lang_iso1
        try:
            lang_dict=Lang(lang_iso1)
            if lang_dict:
                lang=lang_dict.pt3
        except Exception:
            pass
        return lang

    def get_all_sources_lang(self)->list[str]:
        available_packages=argostranslate.package.get_available_packages()
        return sorted(set(pkg.from_code for pkg in available_packages))

    def get_all_targets_lang(self,source_lang:str)->list[tuple[str,str]]:
        available_packages=argostranslate.package.get_available_packages()
        list_iso1=sorted(set(pkg.to_code for pkg in available_packages if pkg.from_code==source_lang))
        language_translate_mapping={}
        for iso1 in list_iso1:
            try:
                iso3=self.get_language_iso3(iso1)
                if iso3 in language_mapping:
                    language_translate_mapping[iso3]=dict(language_mapping[iso3])
                    language_translate_mapping[iso3]["iso1"]=iso1
            except KeyError:
                pass
        language_translate_options=[
            (
                f"{details['name']} - {details['native_name']}" if details['name']!=details['native_name'] else details['name'],
                lang
            )
            for lang,details in language_translate_mapping.items()
        ]
        return language_translate_options
        
    def get_all_target_packages(self,source_lang:str)->list:
        available_packages=argostranslate.package.get_available_packages()
        return [pkg for pkg in available_packages if pkg.from_code==source_lang]

    def is_package_installed(self,source_lang:str,target_lang:str)->bool:
        try:
            installed_languages=argostranslate.translate.get_installed_languages()
            source_language=next((lang for lang in installed_languages if lang.code==source_lang),None)
            target_language=next((lang for lang in installed_languages if lang.code==target_lang),None)
            return source_language is not None and target_language is not None
        except Exception as e:
            error=f'is_package_installed() error: {e}'
            return False

    def download_and_install_argos_package(self,source_lang:str,target_lang:str)->tuple[str|None,bool]:
        try:
            print(f"[DEBUG] Argos: Updating package index...")
            argostranslate.package.update_package_index()
            print(f"[DEBUG] Argos: Package index updated.")
            
            if self.is_package_installed(source_lang,target_lang):
                print(f"Package for translation from {source_lang} to {target_lang} is already installed.")
                return None,True
                
            print(f"[DEBUG] Argos: Looking for package {source_lang} -> {target_lang}")
            available_packages=self.get_all_target_packages(source_lang)
            print(f"[DEBUG] Argos: Found {len(available_packages)} available packages for source {source_lang}")
            for pkg in available_packages:
                print(f"[DEBUG] Argos: Available package: {pkg.from_code} -> {pkg.to_code}")
                
            target_package=None
            for pkg in available_packages:
                if pkg.from_code==source_lang and pkg.to_code==target_lang:
                    target_package=pkg
                    break
            if target_package:
                #tmp_dir = os.path.join(session['process_dir'], "tmp")
                #os.makedirs(tmp_dir, exist_ok=True)
                #with tempfile.TemporaryDirectory(dir=tmp_dir) as tmpdirname:
                with tempfile.TemporaryDirectory() as tmpdirname:
                    print(f"Downloading package for translation from {source_lang} to {target_lang}...")
                    package_path=target_package.download()
                    argostranslate.package.install_from_path(package_path)
                    print(f"Package installed for translation from {source_lang} to {target_lang}")
                    return None,True
            else:
                msg=f"No available package found for translation from {source_lang} to {target_lang}."
                print(f"[ERROR] {msg}")
                return msg,False
        except Exception as e:
            error=f'download_and_install_argos_package() error: {e}'
            return error,False

    def process(self,text:str)->tuple[str,bool]:
        try:
            return self.translation.translate(text),True
        except Exception as e:
            error=f'AgrosTranslator.process() error: {e}'
            return error,False

    def start(self,source_lang:str,target_lang:str)->tuple[str|None,bool]:
        try:
            if self.neural_machine!="argostranslate":
                error=f"Neural machine '{self.neural_machine}' is not supported."
                return error,False
            status=True
            if not self.is_package_installed(source_lang,target_lang):
                error,status=self.download_and_install_argos_package(source_lang,target_lang)
            if status:
                installed_languages=argostranslate.translate.get_installed_languages()
                source_language=next((lang for lang in installed_languages if lang.code==source_lang),None)
                target_language=next((lang for lang in installed_languages if lang.code==target_lang),None)
                if not source_language or not target_language:
                    error=f"Translation languages not installed: {source_lang} to {target_lang}"
                    return error,False
                self.translation=source_language.get_translation(target_language)
                return None,True
            return error,status
        except Exception as e:
            error=f'AgrosTranslator.process() error: {e}'
            return error,False