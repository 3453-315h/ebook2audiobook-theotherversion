
            def reprocess_ebook(id:str, progress=gr.Progress())->tuple:
                try:
                    print(f"DEBUG reprocess_ebook called for session {id}")
                    session = context.get_session(id)
                    file_path = session.get("ebook")
                    
                    if not file_path or not os.path.exists(file_path):
                         print("DEBUG: No ebook file in session to reprocess")
                         return gr.update()
                    
                    # Get max_chars from current TTS engine settings
                    tts_engine = session.get('tts_engine', default_tts_engine)
                    max_chars = default_engine_settings.get(tts_engine, {}).get('max_chars', 250)
                    
                    print(f"DEBUG: Reprocessing {file_path} with Force OCR={session.get('force_ocr')}")
                    extract_preview_chapters(file_path, id, max_chars, progress=progress)
                    
                    return gr.update(value='', visible=False)
                except Exception as e:
                    print(f"reprocess_ebook Error: {e}")
                    import traceback
                    traceback.print_exc()
                    return gr.update()
