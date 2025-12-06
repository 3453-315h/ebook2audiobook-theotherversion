from __future__ import annotations
import os
import shutil
from lib.functions import *
from lib.classes.translator import get_translation_languages
import tempfile

def update_gr_save_session(session, state_update):
    return gr.update(), gr.update(), gr.update()

def clear_event(session):
    pass

def build_interface(args:dict)->gr.Blocks:
    try:
        script_mode = args['script_mode']
        is_gui_process = args['is_gui_process']
        is_gui_shared = args['share']
        title = 'Ebook2Audiobook'
        gr_glassmask_msg = 'Initialization, please wait...'
        ebook_src = None
        gr_session = None
        gr_state_update = None
        gr_save_session = None
        gr_audiobook_list = None
        language_options = [
            (
                f"{details['name']} - {details['native_name']}" if details['name'] != details['native_name'] else details['name'],
                lang
            )
            for lang, details in language_mapping.items()
        ]
        voice_options = []
        tts_engine_options = []
        custom_model_options = []
        fine_tuned_options = []
        audiobook_options = []
        options_output_split_hours = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
        
        src_label_file = 'Upload File'
        src_label_dir = 'Select a Directory'
        
        visible_gr_tab_xtts_params = interface_component_options['gr_tab_xtts_params']
        visible_gr_tab_bark_params = interface_component_options['gr_tab_bark_params']
        visible_gr_group_custom_model = interface_component_options['gr_group_custom_model']
        visible_gr_group_voice_file = interface_component_options['gr_group_voice_file']

        theme = gr.themes.Origin(
            primary_hue='green',
            secondary_hue='amber',
            neutral_hue='gray',
            radius_size='lg',
            font_mono=['JetBrains Mono', 'monospace', 'Consolas', 'Menlo', 'Liberation Mono']
        )

        header_css = '''
            <style>
                /* Global Scrollbar Customization */
                /* The entire scrollbar */
                ::-webkit-scrollbar {
                    width: 6px !important;
                    height: 6px !important;
                    cursor: pointer !important;;
                }
                /* The scrollbar track (background) */
                ::-webkit-scrollbar-track {
                    background: none transparent !important;
                    border-radius: 6px !important;
                }
                /* The scrollbar thumb (scroll handle) */
                ::-webkit-scrollbar-thumb {
                    background: #c09340 !important;
                    border-radius: 6px !important;
                }
                /* The scrollbar thumb on hover */
                ::-webkit-scrollbar-thumb:hover {
                    background: #ff8c00 !important;
                }
                /* Firefox scrollbar styling */
                html {
                    scrollbar-width: thin !important;
                    scrollbar-color: #c09340 none !important;
                }
                button div.wrap span {
                    display: none !important;
                }
                button div.wrap::after {
                    content: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%231E90FF' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4'/><polyline points='17 8 12 3 7 8'/><line x1='12' y1='3' x2='12' y2='15'/></svg>") !important;
                    width: 24px !important;
                    height: 24px !important;
                    display: inline-block !important;
                    vertical-align: middle !important;
                }
                body:has(#gr_convert_btn:disabled) table.file-preview button.label-clear-button {
                    display: none !important;
                }
                span[data-testid="block-info"] {
                    font-size: 12px !important;
                }
                /////////////////////
                .wrap-inner {
                    border: 1px solid #666666;
                }
                .selected {
                    color: var(--secondary-500) !important;
                    text-shadow: 0.3px 0.3px 0.3px #303030;
                }
                .overflow-menu {
                    display: none !important;
                }
                .gr-glass-mask {
                    z-index: 9999 !important;
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important; 
                    height: 100vh !important;
                    background: rgba(0,0,0,0.5) !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    font-size: 1.2rem !important;
                    color: #ffffff !important;
                    text-align: center !important;
                    border: none !important;
                    opacity: 1;
                    pointer-events: all !important;
                }
                .gr-glass-mask.hide {
                    animation: fadeOut 2s ease-out 2s forwards !important;
                }
                .small-btn{
                    background: var(--block-background-fill) !important;
                    font-size: 22px !important;
                    width: 60px !important;
                    height: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                .small-btn:hover {
                    background: var(--button-primary-background-fill-hover) !important;
                    font-size: 28px !important;
                }
                .small-btn-red{
                    background: var(--block-background-fill) !important;
                    font-size: 22px !important;
                    width: 60px !important;
                    height: 60px !important;
                    margin: 0 !important;
                    padding: 0 !important;
                }
                .small-btn-red:hover {
                    background-color: #ff5050 !important;
                    font-size: 28px !important;
                }
                .small-btn:active, .small-btn-red:active {
                    background: var(--body-text-color) !important;
                    font-size: 30px !important;
                    color: var(--body-background-fill) !important;
                }
                .file-preview-holder {
                    height: 116px !important;
                    overflow: auto !important;
                }
                .progress-bar.svelte-ls20lj {
                    background: var(--secondary-500) !important;
                }
                .file-preview-holder {
                    height: auto !important;
                    min-height: 0 !important;
                    max-height: none !important;
                    position: relative !important;
                }
                .progress-text {
                    position: absolute !important;
                    top: -20px !important;
                    left: 0 !important;
                    width: 100% !important;
                    text-align: center !important;
                    z-index: 999 !important;
                    font-weight: bold !important;
                    color: var(--body-text-color) !important;
                    text-shadow: 1px 1px 2px black !important;
                    pointer-events: none !important;
                }
                ///////////////////
                .gr-tab {
                    padding: 0 3px 0 3px !important;
                    margin: 0 !important;
                    border: none !important;
                }
                .gr-col {
                    padding: 0 6px 0 6px !important;
                    margin: 0 !important;
                    border: none !important;
                }
                .gr-group-main > div {
                    background: none !important;
                    border-radius: var(--radius-md) !important;
                }
                .gr-group > div {
                    background: none !important;
                    padding: 0 !important;
                    margin: 0 !important;
                    border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md) !important;
                }
                .gr-group-sides-padded{
                    background: none !important;
                    margin: 0 var(--size-2) 0 var(--size-2)!important;;
                    border-radius: 0 var(--radius-md) var(--radius-md) var(--radius-md) !important;
                }
                .gr-group-convert-btn{
                    margin: var(--size-2) !important;;
                    border-radius: var(--radius-md) !important;
                }
                .gr-label textarea[data-testid="textbox"]{
                    padding: 0 0 0 3px !important;
                    margin: 0 !important;
                    text-align: left !important;
                    font-weight: normal !important;
                    height: auto !important;
                    font-size: 12px !important;
                    border: none !important;
                    overflow-y: hidden !important;
                    line-height: 12px !important;
                }
                .gr-markdown p {
                    margin-top: 8px !important;
                    width: 90px !important;
                    padding: 0 !important;
                    border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
                    background: var(--block-background-fill) !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    text-align: center !important;
                }
                .gr-markdown-span {
                    margin-top: 8px !important;
                    width: 90px !important;
                    padding: 0 !important;
                    border-radius: var(--radius-md) var(--radius-md) 0 0 !important;
                    background: var(--block-background-fill) !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    text-align: center !important;            
                }
                .gr-markdown-output-split-hours {
                    overflow: hidden !important;
                    background: var(--block-background-fill) !important;
                    border-radius: 0 !important; 
                    font-size: 12px !important;
                    text-align: center !important;
                    vertical-align: middle !important;
                    padding-top: 4px !important;
                    padding-bottom: 4px !important;
                    white-space: nowrap !important;
                }
                .gr-voice-player {
                    margin: 0 !important;
                    padding: 0 !important;
                    width: 60px !important;
                    height: 60px !important;
                    background: var(--block-background-fill) !important;
                }
                .play-pause-button:hover svg {
                    fill: #ffab00 !important;
                    stroke: #ffab00 !important;
                    transform: scale(1.2) !important;
                }
                .gr-convert-btn {
                    font-size: 30px !important;
                    min-height: 70px !important;
                    height: 100% !important;
                }
                ////////////////////
                #gr_ebook_file, #gr_custom_model_file, #gr_voice_file {
                    height: 130px !important;
                    min-height: 130px !important;
                    max-height: 130px !important;
                    display: flex  !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
                #gr_ebook_file label, #gr_custom_model_file label, #gr_voice_file label {
                    background: none !important;
                    border: none !important;
                }
                #gr_audiobook_player label {
                    display: none !important;
                }
                #gr_ebook_file button>div, #gr_custom_model_file button>div, #gr_voice_file button>div {
                    font-size: 12px !important;
                }
                #gr_ebook_file .empty, #gr_custom_model_file .empty, #gr_voice_file .empty,
                #gr_ebook_file .wrap, #gr_custom_model_file .wrap, #gr_voice_file .wrap {
                    height: 100% !important;
                    min-height: 100px !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                }
                #gr_custom_model_file [aria-label="Clear"], #gr_voice_file [aria-label="Clear"] {
                    display: none !important;
                }               
                #gr_fine_tuned_list {
                    height: 95px !important;
                }
                #gr_voice_list {
                    height: 60px !important;
                }
                #gr_output_format_list {
                    height: 103px !important;
                }
                #gr_row_output_split_hours {
                    border-radius: 0 !important;
                }
                #gr_progress .progress-bar {
                    background: #ff7b00 !important;
                }
                #gr_audiobook_sentence textarea{
                    margin: auto !important;
                    text-align: center !important;
                }
                #gr_session textarea, #gr_progress textarea {
                    overflow: hidden !important;
                    overflow-y: auto !important;
                    scrollbar-width: none !important;
                }
                #gr_session textarea::-webkit-scrollbar, #gr_progress textarea::-webkit-scrollbar {
                    display: none !important; 
                }
                #gr_ebook_mode span[data-testid="block-info"],
                #gr_language span[data-testid="block-info"],
                #gr_voice_list span[data-testid="block-info"],
                #gr_device span[data-testid="block-info"],
                #gr_tts_engine_list span[data-testid="block-info"],
                #gr_output_split_hours span[data-testid="block-info"],
                #gr_session span[data-testid="block-info"],
                #gr_custom_model_list span[data-testid="block-info"],
                #gr_audiobook_sentence span[data-testid="block-info"],
                #gr_audiobook_list span[data-testid="block-info"],
                #gr_progress span[data-testid="block-info"]{
                    display: none !important;
                }
                #gr_row_ebook_mode { align-items: center !important; }
                #gr_chapters_preview {
                    align-self: center !important; 
                    overflow: visible !important;
                    padding: 20px 0 20px 10px !important;
                }
                #gr_group_output_split {
                    border-radius: 0 !important;
                }
                #gr_tts_rating {
                    overflow: hidden !important;
                }
                #gr_row_voice_player, #gr_row_custom_model_list, #gr_row_audiobook_list {
                    height: 60px !important;
                }
                #gr_audiobook_player :is(.volume, .empty, .source-selection, .control-wrapper, .settings-wrapper, label) {
                    display: none !important;
                }
                #gr_audiobook_files label[data-testid="block-label"] {
                    display: none !important;
                }
                #gr_audiobook_player audio {
                    width: 100% !important;
                    padding-top: 10px !important;
                    padding-bottom: 10px !important;
                    border-radius: 0px !important;
                    background-color: #ebedf0 !important;
                    color: #ffffff !important;
                }
                #gr_audiobook_player audio::-webkit-media-controls-panel {
                    width: 100% !important;
                    padding-top: 10px !important;
                    padding-bottom: 10px !important;
                    border-radius: 0px !important;
                    background-color: #ebedf0 !important;
                    color: #ffffff !important;
                }
                #gr_voice_player_hidden {
                    z-index: -100 !important;
                    position: absolute !important;
                    overflow: hidden !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    width: 60px !important;
                    height: 60px !important;
                }
                #gr_state_update, #gr_restore_session, #gr_save_session,
                #gr_audiobook_vtt, #gr_playback_time {
                    display: none !important;
                }
                ///////////
                .fade-in {
                    animation: fadeIn 1s ease-in !important;
                    display: inline-block !important;
                }
                @keyframes fadeIn {
                    from {
                        opacity: 0;
                        visibility: visible !important;
                    }
                    to {
                        opacity: 1;
                    }
                }
                @keyframes fadeOut {
                    from {
                        opacity: 1;
                    }
                    to {
                        opacity: 0;
                        visibility: hidden;
                        pointer-events: none;
                    }
                }
                //////////
                #custom-gr-modal-container,
                #custom-gr-modal-container .gr-modal {
                    position: fixed !important;
                }
                .hide-elem {
                    z-index: -1 !important;
                    position: absolute !important;
                    top: 0 !important;
                    left: 0 !important;
                }
                .gr-modal {
                    position: fixed !important;
                    top: 0 !important; left: 0 !important;
                    width: 100% !important; height: 100% !important;
                    background-color: rgba(0, 0, 0, 0.5) !important;
                    z-index: 9999 !important;
                    display: flex !important;
                    justify-content: center !important;
                    align-items: center !important;
                }
                .gr-modal-content {
                    background-color: #333 !important;
                    padding: 20px !important;
                    border-radius: 9px !important;
                    text-align: center !important;
                    max-width: 300px !important;
                    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.5) !important;
                    border: 2px solid #FFA500 !important;
                    color: white !important;
                    position: relative !important;
                }
                .confirm-buttons {
                    display: flex !important;
                    justify-content: space-evenly !important;
                    margin-top: 20px !important;
                }
                .confirm-buttons button {
                    padding: 10px 20px !important;
                    border: none !important;
                    border-radius: 6px !important;
                    font-size: 16px !important;
                    cursor: pointer !important;
                }
                .button-green { background-color: #28a745 !important; color: white !important; }
                .button-green:hover { background-color: #34d058 !important; }
                .button-red  { background-color: #dc3545 !important; color: white !important; }
                .button-red:hover  { background-color: #ff6f71 !important; }
                .button-green:active, .button-red:active {
                    background: var(--body-text-color) !important;
                    color: var(--body-background-fill) !important;
                }
                .spinner {
                    margin: 15px auto !important;
                    border: 4px solid rgba(255, 255, 255, 0.2) !important;
                    border-top: 4px solid #FFA500 !important;
                    border-radius: 50% !important;
                    width: 30px !important;
                    height: 30px !important;
                    animation: spin 1s linear infinite !important;
                }
                @keyframes spin {
                    0% { transform: rotate(0deg); }
                    100% { transform: rotate(360deg); }
                }
                #gr_chapter_editor_overlay {
                    position: fixed !important;
                    top: 50% !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    width: 90% !important;
                    max-width: 700px !important;
                    height: 80vh !important;
                    z-index: 10000 !important;
                    background-color: #0b0f19 !important;
                    padding: 0 !important;
                    box-sizing: border-box !important;
                    overflow: hidden !important;
                    border: 1px solid #374151 !important;
                    border-radius: 12px !important;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4) !important;
                }
                
                /* Native Gradio Modal Group Styles */
                #gr_chapter_editor_group {
                    position: fixed !important;
                    top: 50% !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    width: 90% !important;
                    max-width: 900px !important;
                    height: 85vh !important;
                    z-index: 10000 !important;
                    background-color: #0b0f19 !important;
                    padding: 24px !important;
                    box-sizing: border-box !important;
                    overflow: auto !important;
                    border: 1px solid #374151 !important;
                    border-radius: 12px !important;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
                }
                
                /* Translation Overlay Styles */
                #gr_translation_overlay {
                    position: fixed !important;
                    top: 0 !important;
                    left: 0 !important;
                    width: 100vw !important;
                    height: 100vh !important;
                    z-index: 10001 !important;
                    background: transparent !important;
                    pointer-events: none !important;
                }
                
                .translation-overlay-backdrop {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100vw;
                    height: 100vh;
                    background: rgba(0, 0, 0, 0.7);
                    z-index: 10001;
                    pointer-events: auto;
                }
                
                .translation-overlay-content {
                    position: fixed;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    width: 90%;
                    max-width: 600px;
                    max-height: 85vh;
                    background-color: #0b0f19;
                    padding: 28px;
                    box-sizing: border-box;
                    overflow: auto;
                    border: 1px solid #374151;
                    border-radius: 12px;
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5), 0 10px 10px -5px rgba(0, 0, 0, 0.4);
                    z-index: 10002;
                    pointer-events: auto;
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                }
                
                .translation-overlay-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    border-bottom: 1px solid #374151;
                    padding-bottom: 12px;
                    margin-bottom: 8px;
                }
                
                .translation-overlay-title {
                    font-size: 1.25rem;
                    font-weight: 600;
                    color: #f9fafb;
                    margin: 0;
                }
                
                .translation-overlay-close {
                    background: transparent;
                    border: none;
                    color: #9ca3af;
                    font-size: 1.5rem;
                    cursor: pointer;
                    padding: 4px 8px;
                    border-radius: 4px;
                }
                
                .translation-overlay-close:hover {
                    background: #1f2937;
                    color: #f9fafb;
                }
                
                .translation-form-group {
                    display: flex;
                    flex-direction: column;
                    gap: 8px;
                }
                
                .translation-form-label {
                    font-size: 0.875rem;
                    font-weight: 500;
                    color: #d1d5db;
                }
                
                .translation-form-select {
                    padding: 10px 12px;
                    background: #1f2937;
                    border: 1px solid #374151;
                    border-radius: 8px;
                    color: #f9fafb;
                    font-size: 0.9rem;
                }
                
                .translation-form-select:focus {
                    outline: none;
                    border-color: #3b82f6;
                }
                
                .translation-detected-lang {
                    padding: 12px;
                    background: #1f2937;
                    border-radius: 8px;
                    color: #9ca3af;
                    font-size: 0.875rem;
                }
                
                .translation-progress {
                    padding: 12px;
                    background: #1f2937;
                    border-radius: 8px;
                    text-align: center;
                }
                
                .translation-progress-bar {
                    height: 6px;
                    background: #374151;
                    border-radius: 3px;
                    margin-top: 8px;
                    overflow: hidden;
                }
                
                .translation-progress-fill {
                    height: 100%;
                    background: linear-gradient(90deg, #3b82f6, #8b5cf6);
                    transition: width 0.3s ease;
                }
                
                .translation-btn-row {
                    display: flex;
                    gap: 12px;
                    margin-top: 8px;
                }
                
                .translation-btn {
                    flex: 1;
                    padding: 12px 16px;
                    border-radius: 8px;
                    border: none;
                    font-size: 0.9rem;
                    font-weight: 500;
                    cursor: pointer;
                    transition: all 0.2s ease;
                }
                
                .translation-btn-primary {
                    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
                    color: white;
                }
                
                .translation-btn-primary:hover {
                    transform: translateY(-1px);
                    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
                }
                
                .translation-btn-secondary {
                    background: #374151;
                    color: #d1d5db;
                }
                
                .translation-btn-secondary:hover {
                    background: #4b5563;
                }
            </style>
            </style>
            <style>
                /* Performance Optimization UI Elements */
                .performance-status {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    padding: 8px 12px;
                    border-radius: 6px;
                    font-size: 12px;
                    font-weight: bold;
                    margin: 4px 0;
                    transition: all 0.3s ease;
                }

                .performance-status.enabled {
                    background: linear-gradient(135deg, #4CAF50, #8BC34A);
                    color: white;
                    box-shadow: 0 2px 4px rgba(76, 175, 80, 0.3);
                }

                .performance-status.disabled {
                    background: linear-gradient(135deg, #F44336, #E57373);
                    color: white;
                    box-shadow: 0 2px 4px rgba(244, 67, 54, 0.3);
                }

                .performance-icon {
                    margin-right: 8px;
                    font-size: 14px;
                }

                .performance-metrics {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 8px;
                    margin-top: 8px;
                    justify-content: center;
                }

                .metric-item {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 10px;
                    backdrop-filter: blur(4px);
                }

                .performance-modal {
                    background: rgba(0, 0, 0, 0.8);
                    border: 2px solid #FFA500;
                    border-radius: 12px;
                    padding: 20px;
                    max-width: 500px;
                    box-shadow: 0 8px 16px rgba(255, 165, 0, 0.3);
                }

                .performance-chart {
                    width: 100%;
                    height: 200px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    margin: 12px 0;
                    position: relative;
                }

                .memory-gauge {
                    width: 100%;
                    height: 150px;
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 8px;
                    margin: 12px 0;
                    position: relative;
                    overflow: hidden;
                }

                .gauge-fill {
                    height: 100%;
                    width: 0%;
                    background: linear-gradient(90deg, #4CAF50, #FFEB3B, #F44336);
                    transition: width 0.5s ease;
                    position: relative;
                }

                .gauge-label {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    color: white;
                    font-weight: bold;
                    text-shadow: 0 0 4px rgba(0, 0, 0, 0.5);
                }

                .optimization-toggle {
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                    margin: 12px 0;
                }

                .toggle-switch {
                    position: relative;
                    display: inline-block;
                    width: 60px;
                    height: 30px;
                }

                .toggle-switch input {
                    opacity: 0;
                    width: 0;
                    height: 0;
                }

                .slider {
                    position: absolute;
                    cursor: pointer;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background-color: #ccc;
                    transition: .4s;
                    border-radius: 30px;
                }

                .slider:before {
                    position: absolute;
                    content: "";
                    height: 22px;
                    width: 22px;
                    left: 4px;
                    bottom: 4px;
                    background-color: white;
                    transition: .4s;
                    border-radius: 50%;
                }

                input:checked + .slider {
                    background-color: #4CAF50;
                }

                input:checked + .slider:before {
                    transform: translateX(30px);
                }

                .advanced-settings-panel {
                    background: rgba(0, 0, 0, 0.7);
                    border: 1px solid #FFA500;
                    border-radius: 8px;
                    padding: 12px;
                    margin: 8px 0;
                }

                .setting-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin: 6px 0;
                    padding: 4px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }

                .setting-label {
                    font-size: 12px;
                    color: #FFF;
                }

                .setting-value {
                    font-size: 12px;
                    color: #FFEB3B;
                    font-family: monospace;
                }

                .validation-error {
                    color: #FF5252;
                    font-size: 12px;
                    margin: 4px 0;
                    animation: shake 0.3s;
                }

                @keyframes shake {
                    0%, 100% { transform: translateX(0); }
                    20%, 60% { transform: translateX(-3px); }
                    40%, 80% { transform: translateX(3px); }
                }

                .validation-success {
                    color: #4CAF50;
                    font-size: 12px;
                    margin: 4px 0;
                }

                .progress-enhancer {
                    position: relative;
                    height: 4px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 2px;
                    overflow: hidden;
                }

                .progress-enhancer::after {
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
                    animation: shine 2s infinite;
                }

                @keyframes shine {
                    0% { left: -100%; }
                    100% { left: 100%; }
                }
            </style>
        '''
        
        # JavaScript for translation overlay (passed via js parameter)
        header_js = """
        function() {
            // Global translation overlay functions
            window.closeTranslationOverlay = function() {
                console.log('closeTranslationOverlay called');
                var overlay = document.getElementById('gr_translation_overlay');
                if (overlay) {
                    overlay.style.display = 'none';
                    console.log('Overlay hidden');
                }
            };
            
            window.startTranslation = function() {
                console.log('startTranslation called');
                var targetLang = document.getElementById('translation_target_lang');
                var service = document.getElementById('translation_service');
                
                if (!targetLang || !service) {
                    console.log('Translation inputs not found');
                    return;
                }
                
                var targetLangValue = targetLang.value;
                var serviceValue = service.value;
                console.log('Target:', targetLangValue, 'Service:', serviceValue);
                
                // Show progress
                var progressEl = document.getElementById('translation_progress');
                var statusEl = document.getElementById('translation_status');
                var startBtn = document.getElementById('start_translation_btn');
                
                if (progressEl) progressEl.style.display = 'block';
                if (statusEl) statusEl.textContent = 'Starting translation...';
                if (startBtn) startBtn.disabled = true;
                
                // Set hidden Gradio component values - service change triggers the translation
                var targetInput = document.querySelector('#gr_translation_target_lang input, #gr_translation_target_lang textarea');
                var serviceInput = document.querySelector('#gr_translation_service input, #gr_translation_service textarea');
                
                console.log('targetInput:', targetInput, 'serviceInput:', serviceInput);
                
                // First set target lang (this won't trigger anything)
                if (targetInput) {
                    targetInput.value = targetLangValue;
                    targetInput.dispatchEvent(new Event('input', {bubbles: true}));
                    console.log('Set target lang:', targetLangValue);
                }
                
                // Close overlay after a short delay
                setTimeout(function() {
                    window.closeTranslationOverlay();
                    
                    // Then set service (this WILL trigger the translation via .change() handler)
                    if (serviceInput) {
                        // Append timestamp to make it unique and trigger change
                        serviceInput.value = serviceValue + '_' + Date.now();
                        serviceInput.dispatchEvent(new Event('input', {bubbles: true}));
                        serviceInput.dispatchEvent(new Event('change', {bubbles: true}));
                        console.log('Set service with trigger:', serviceValue);
                    }
                }, 200);
            };
            
            console.log('Translation functions registered');
            
            // Inject Cancel Job Button into Settings
            window.injectCancelButton = function() {
                var headings = document.querySelectorAll('h2, h3, h4, span, div'); 
                var screenStudioAnchor = null;
                
                // Strategy 1: Look for "Screen Studio" text (loose match for BETA badge)
                for (var i = 0; i < headings.length; i++) {
                    var el = headings[i];
                    if (el.textContent && el.textContent.includes('Screen Studio')) {
                        // Prioritize headers or short labels to avoid description text
                        if (el.tagName.match(/^H\d/) || el.textContent.length < 40) {
                             screenStudioAnchor = el;
                             break;
                        }
                    }
                }
                
                // Strategy 2: Fallback to "Start Recording" button if header not found
                if (!screenStudioAnchor) {
                     var buttons = document.querySelectorAll('button');
                     for (var j = 0; j < buttons.length; j++) {
                         if (buttons[j].textContent.includes('Start Recording')) {
                             screenStudioAnchor = buttons[j];
                             break;
                         }
                     }
                }

                if (screenStudioAnchor) {
                    // Try to find the section container
                    var section = screenStudioAnchor.closest('div.setting, section, .settings-section');
                    if (!section) section = screenStudioAnchor.parentElement; 
                    if (!section) section = screenStudioAnchor; // Last resort
                    
                    if (section && !document.getElementById('injected_cancel_job_btn')) {
                        console.log('Found Screen Studio section, injecting Cancel button');
                        var btnContainer = document.createElement('div');
                        btnContainer.style.marginTop = '20px';
                        btnContainer.style.padding = '15px';
                        btnContainer.style.borderTop = '1px solid var(--border-color-primary, #e5e7eb)';
                        btnContainer.style.display = 'flex';
                        btnContainer.style.justifyContent = 'flex-end'; // Align right or center
                        
                        var btn = document.createElement('button');
                        btn.id = 'injected_cancel_job_btn';
                        btn.textContent = '🛑 Cancel Current Job';
                        btn.style.backgroundColor = '#ef4444'; // Red
                        btn.style.color = 'white';
                        btn.style.padding = '10px 20px';
                        btn.style.borderRadius = '6px';
                        btn.style.border = 'none';
                        btn.style.fontWeight = 'bold';
                        btn.style.cursor = 'pointer';
                        btn.style.width = '100%';
                        btn.style.fontSize = '14px';
                        btn.style.transition = 'all 0.2s';
                        btn.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
                        
                        btn.onmouseover = function() { btn.style.backgroundColor = '#dc2626'; btn.style.transform = 'translateY(-1px)'; };
                        btn.onmouseout = function() { btn.style.backgroundColor = '#ef4444'; btn.style.transform = 'translateY(0)'; };
                        
                        btn.onclick = function() {
                            var hiddenBtn = document.getElementById('gr_cancel_job_btn');
                            if (hiddenBtn) {
                                hiddenBtn.click();
                                btn.textContent = '⏳ Requesting Cancellation...';
                                btn.disabled = true;
                                btn.style.backgroundColor = '#6b7280';
                                setTimeout(function() { 
                                    btn.textContent = '🛑 Cancel Current Job'; 
                                    btn.disabled = false;
                                    btn.style.backgroundColor = '#ef4444';
                                }, 3000);
                            } else {
                                console.error('Hidden cancel button not found');
                            }
                        };
                        
                        btnContainer.appendChild(btn);
                        
                        // Insert AFTER the section container to appear "underneath"
                        if (section.parentNode) {
                             if (section.nextSibling) {
                                section.parentNode.insertBefore(btnContainer, section.nextSibling);
                            } else {
                                section.parentNode.appendChild(btnContainer);
                            }
                        }
                    }
                }
            };
            
            // Run injection check periodically
            setInterval(window.injectCancelButton, 800);
        }
        """

        
        chapter_editor_css = """
    #chapter-editor-content {
        --bg-color: #0b0f19;
        --text-color: #e5e7eb;
        --border-color: #374151;
        --input-bg: #1f2937;
        --accent-color: #10b981;
        --accent-hover: #059669;
        --danger-color: #ef4444;
        font-family: 'JetBrains Mono', monospace;
        background-color: var(--bg-color);
        color: var(--text-color);
        display: flex;
        flex-direction: column;
        height: 100%;
        max-height: 80vh;
        box-sizing: border-box;
        padding: 20px;
    }

    .editor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px;
        margin-bottom: 10px;
        flex-shrink: 0;
    }

    .editor-header h2 {
        margin: 0;
    }

    .header-controls {
        display: flex;
        gap: 15px;
        align-items: center;
        font-size: 13px;
    }

    .header-controls label {
        display: flex;
        align-items: center;
        gap: 5px;
        cursor: pointer;
    }

    .editor-container {
        flex: 1 1 auto;
        overflow-y: auto;
        overflow-x: hidden;
        margin-bottom: 15px;
        min-height: 0;
    }

    #chapterTable {
        width: 100%;
        border-collapse: collapse;
    }

    #chapterTable th,
    #chapterTable td {
        text-align: left;
        padding: 8px;
        border-bottom: 1px solid var(--border-color);
        vertical-align: top;
    }

    #chapterTable th {
        background-color: var(--input-bg);
        position: sticky;
        top: 0;
        z-index: 1;
    }

    #chapterTable textarea {
        width: 100%;
        background-color: var(--input-bg);
        border: 1px solid var(--border-color);
        color: var(--text-color);
        padding: 10px;
        border-radius: 4px;
        font-family: inherit;
        font-size: 13px;
        resize: vertical;
        min-height: 60px;
        line-height: 1.4;
    }

    #chapterTable textarea:focus {
        outline: none;
        border-color: var(--accent-color);
    }

    .num-cell {
        width: 30px;
        color: #6b7280;
        font-size: 12px;
    }

    .del-cell {
        width: 30px;
        text-align: center;
    }

    .btn-del {
        background: none;
        border: none;
        color: #6b7280;
        cursor: pointer;
        font-size: 16px;
        padding: 5px;
        opacity: 0.6;
        transition: opacity 0.2s, color 0.2s;
    }

    .btn-del:hover {
        opacity: 1;
        color: var(--danger-color);
    }

    .chapter-row.selected {
        background-color: rgba(16, 185, 129, 0.1);
    }

    .actions {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        padding-top: 10px;
        border-top: 1px solid var(--border-color);
        flex-shrink: 0;
    }

    .btn-editor {
        padding: 8px 16px;
        border: none;
        border-radius: 6px;
        cursor: pointer;
        font-weight: bold;
        font-size: 13px;
        transition: background-color 0.2s;
    }

    .btn-save {
        background-color: var(--accent-color);
        color: white;
    }

    .btn-save:hover {
        background-color: var(--accent-hover);
    }

    .btn-cancel {
        background-color: transparent;
        border: 1px solid var(--border-color);
        color: var(--text-color);
    }

    .btn-cancel:hover {
        background-color: var(--input-bg);
    }

    .btn-danger {
        background-color: var(--danger-color);
        color: white;
    }

    .btn-danger:hover {
        background-color: #dc2626;
    }

    .chk-cell {
        width: 25px;
        text-align: center;
    }

    .chk-cell input {
        width: 14px;
        height: 14px;
        cursor: pointer;
    }

    /* Fix for Gradio Dataframe row options dropdown menu position */
    /* Move dropdown to LEFT side of the row */
    #gr_cancel_job_btn {
        display: none !important;
    }
    
    #gr_main_cancel_btn {
        padding: 0 !important;
        border: none !important;
        align-self: stretch !important;
    }
    #gr_main_cancel_btn > button {
        background-color: #ef4444 !important;
        color: white !important;
        height: 100% !important;
        min-height: 70px !important; /* Force match with Convert button */
        width: 100% !important;
        font-size: 22px !important;
    }

    #gr_chapter_trans_lang .options, #gr_chapter_trans_lang ul {
        max-height: 300px !important;
    }

    #gr_chapter_dataframe .cell-menu {
        left: 0 !important;
        right: auto !important;
        transform: none !important;
        position: absolute !important;
        z-index: 9999 !important;
    }
    
    #gr_chapter_dataframe .cell-menu-button {
        position: relative !important;
    }
    
    /* Alternative fix using parent container */
    .table-wrap {
        position: relative !important;
        overflow: visible !important;
    }
    
    [data-testid="dataframe"] .cell-menu,
    .dataframe .cell-menu {
        left: 0 !important;
        right: auto !important;
        transform: none !important;
        position: absolute !important;
    }
    """
    
        with gr.Blocks(theme=theme, title=title, css=header_css + chapter_editor_css, js=header_js, delete_cache=(604800, 86400)) as app:
            with gr.Group(visible=True, elem_id='gr_group_main', elem_classes='gr-group-main') as gr_group_main:
                with gr.Tabs(elem_id='gr_tabs'):
                    gr_tab_main = gr.Tab('Dashboard', elem_id='gr_tab_main', elem_classes='gr-tab')
                    with gr_tab_main:
                        with gr.Row(elem_id='gr_row_tab_main'):
                            with gr.Column(elem_id='gr_col_1', elem_classes=['gr-col'], scale=3):
                                with gr.Group(elem_id='gr_group_ebook_file', elem_classes=['gr-group']):
                                    gr_import_markdown = gr.Markdown(elem_id='gr_import_markdown', elem_classes=['gr-markdown'], value='Import')
                                    gr_ebook_file = gr.File(label=src_label_file, elem_id='gr_ebook_file', file_types=ebook_formats, file_count='single', allow_reordering=True, height=100)
                                    gr_row_ebook_mode = gr.Row(elem_id='gr_row_ebook_mode')
                                    with gr_row_ebook_mode:
                                        gr_ebook_mode = gr.Dropdown(label='', elem_id='gr_ebook_mode', choices=[('File','single'), ('Directory','directory')], interactive=True, scale=2)
                                        gr_chapters_preview = gr.Button(value='Chapters Preview', elem_id='gr_chapters_preview', interactive=True, scale=1)
                                    gr_language = gr.Dropdown(label='Language', elem_id='gr_language', choices=language_options, value=args.get('language', 'en'), interactive=True)
                                    gr_force_ocr = gr.Checkbox(
                                        label="Force OCR (for mixed PDFs)", 
                                        value=False, 
                                        interactive=True, 
                                        info="Force OCR on all pages, ignoring embedded text. Useful for older scanned PDFs with poor hidden text layers.",
                                        elem_id='gr_force_ocr'
                                    )
                                    gr_translate_btn = gr.Button(value='Translate', elem_id='gr_translate_btn', interactive=True)
                                    
                                    # Overlays
                                    gr_chapter_editor_overlay = gr.HTML(visible=False, elem_id='gr_chapter_editor_overlay')
                                    gr_translation_overlay = gr.HTML(visible=False, elem_id='gr_translation_overlay')
                                    gr_chapters_data = gr.Textbox(visible=False, elem_id='gr_chapters_data')
                                    gr_save_chapters_btn = gr.Button(visible=False, elem_id='gr_save_chapters_btn')
                                    
                                    # Hidden translation controls for JS-Python bridge
                                    with gr.Row():
                                        gr_translation_target_lang = gr.Textbox(label="Target Language", visible=False, elem_id="gr_translation_target_lang")
                                        gr_translation_service = gr.Textbox(label="Service", visible=False, elem_id="gr_translation_service")
                                        gr_translation_trigger = gr.Button("Trigger Translation", visible=False, elem_id="gr_translation_trigger")
                                    
                                    gr_voice_markdown = gr.Markdown(elem_id='gr_voice_markdown', elem_classes=['gr-markdown'], value='Voices')
                                    gr_voice_file = gr.File(label='Upload Voice', elem_id='gr_voice_file', file_types=voice_formats, value=None, height=100)
                                    gr_row_voice_player = gr.Row(elem_id='gr_row_voice_player')
                                    with gr_row_voice_player:
                                        gr_voice_player_hidden = gr.Audio(elem_id='gr_voice_player_hidden', type='filepath', interactive=False, waveform_options=gr.WaveformOptions(show_recording_waveform=False), show_download_button=False, container=False, visible='hidden', show_share_button=True, show_label=False, scale=0, min_width=60)
                                        gr_voice_play = gr.Button('▶', elem_id='gr_voice_play', elem_classes=['small-btn'], variant='secondary', interactive=True, visible=False, scale=0, min_width=60)
                                        gr_voice_list = gr.Dropdown(label='Voices', elem_id='gr_voice_list', choices=voice_options, type='value', interactive=True, scale=2)
                                        gr_voice_del_btn = gr.Button('🗑', elem_id='gr_voice_del_btn', elem_classes=['small-btn-red'], variant='secondary', interactive=True, visible=False, scale=0, min_width=60)
                                with gr.Group(elem_id='gr_group_device', elem_classes=['gr-group']):
                                    gr_device_markdown = gr.Markdown(elem_id='gr_device_markdown', elem_classes=['gr-markdown'], value='Processor')
                                    gr_device = gr.Dropdown(label='', elem_id='gr_device', choices=[(k, v["proc"]) for k, v in devices.items()], type='value', value=default_device, interactive=True)
                            with gr.Column(elem_id='gr_col_2', elem_classes=['gr-col'], scale=3):
                                with gr.Group(elem_id='gr_group_tts_engine', elem_classes=['gr-group']):
                                    gr_tts_rating = gr.Markdown(elem_id='gr_tts_rating', elem_classes=['gr-markdown'], value='TTS Engine')
                                    gr_tts_engine_list = gr.Dropdown(label='', elem_id='gr_tts_engine_list', choices=tts_engine_options, type='value', interactive=True)
                                with gr.Group(elem_id='gr_group_models', elem_classes=['gr-group']):
                                    gr_models_markdown = gr.Markdown(elem_id='gr_models_markdown', elem_classes=['gr-markdown'], value='Models')
                                    gr_fine_tuned_list = gr.Dropdown(label='Fine Tuned Preset Models', elem_id='gr_fine_tuned_list', choices=fine_tuned_options, type='value', interactive=True)
                                    gr_group_custom_model = gr.Group(visible=visible_gr_group_custom_model)
                                    with gr_group_custom_model:
                                        gr_custom_model_label = gr.Textbox(label='', elem_id='gr_custom_model_label', elem_classes=['gr-label'], interactive=False)
                                        gr_custom_model_file = gr.File(label=f"Upload ZIP File", elem_id='gr_custom_model_file', value=None, file_types=['.zip'], height=100)
                                        gr_row_custom_model_list = gr.Row(elem_id='gr_row_custom_model_list')
                                        with gr_row_custom_model_list:
                                            gr_custom_model_list = gr.Dropdown(label='', elem_id='gr_custom_model_list', choices=custom_model_options, type='value', interactive=True, scale=2)
                                            gr_custom_model_del_btn = gr.Button('🗑', elem_id='gr_custom_model_del_btn', elem_classes=['small-btn'], variant='secondary', interactive=True, visible=False, scale=0, min_width=60)
                                with gr.Group(elem_id='gr_group_output_format'):
                                    gr_output_markdown = gr.Markdown(elem_id='gr_output_markdown', elem_classes=['gr-markdown'], value='Output')
                                    with gr.Row(elem_id='gr_row_output_format'):
                                        gr_output_format_list = gr.Dropdown(label='Format', elem_id='gr_output_format_list', choices=output_formats, type='value', value=default_output_format, interactive=True, scale=1)
                                        gr_output_channel_list = gr.Dropdown(label='Channel', elem_id='gr_output_channel_list', choices=['mono', 'stereo'], type='value', value=default_output_channel, interactive=True, scale=1)
                                        with gr.Group(elem_id='gr_group_output_split'):
                                            gr_output_split = gr.Checkbox(label='Split File', elem_id='gr_output_split', value=default_output_split, interactive=True)
                                            gr_row_output_split_hours = gr.Row(elem_id='gr_row_output_split_hours', visible=False)
                                            with gr_row_output_split_hours:
                                                gr_output_split_hours_markdown = gr.Markdown(elem_id='gr_output_split_hours_markdown',elem_classes=['gr-markdown-output-split-hours'], value='Hours<br/>/ Part')
                                                gr_output_split_hours = gr.Dropdown(label='', elem_id='gr_output_split_hours', choices=options_output_split_hours, type='value', value=default_output_split_hours, interactive=True, scale=1)
                                with gr.Group(elem_id='gr_group_session', elem_classes=['gr-group']):
                                    gr_session_markdown = gr.Markdown(elem_id='gr_session_markdown', elem_classes=['gr-markdown'], value='Session')
                                    gr_session = gr.Textbox(label='', elem_id='gr_session', interactive=False)
                            
                    gr_tab_xtts_params = gr.Tab('XTTSv2 Settings', elem_id='gr_tab_xtts_params', elem_classes='gr-tab', visible=visible_gr_tab_xtts_params)           
                    with gr_tab_xtts_params:
                        with gr.Group(elem_id='gr_group_xtts_params', elem_classes=['gr-group']):
                            gr_xtts_temperature = gr.Slider(
                                label='Temperature',
                                minimum=0.05,
                                maximum=10.0,
                                step=0.05,
                                value=float(default_engine_settings[TTS_ENGINES['XTTSv2']]['temperature']),
                                elem_id='gr_xtts_temperature',
                                info='Higher values lead to more creative, unpredictable outputs. Lower values make it more monotone.'
                            )
                            gr_xtts_length_penalty = gr.Slider(
                                label='Length Penalty',
                                minimum=0.3,
                                maximum=5.0,
                                step=0.1,
                                value=float(default_engine_settings[TTS_ENGINES['XTTSv2']]['length_penalty']),
                                elem_id='gr_xtts_length_penalty',
                                info='Adjusts how much longer sequences are preferred. Higher values encourage the model to produce longer and more natural speech.',
                                visible=False
                            )
                            gr_xtts_num_beams = gr.Slider(
                                label='Number Beams',
                                minimum=1,
                                maximum=10,
                                step=1,
                                value=int(default_engine_settings[TTS_ENGINES['XTTSv2']]['num_beams']),
                                elem_id='gr_xtts_num_beams',
                                info='Controls how many alternative sequences the model explores. Higher values improve speech coherence and pronunciation but increase inference time.',
                                visible=False
                            )
                            gr_xtts_repetition_penalty = gr.Slider(
                                label='Repetition Penalty',
                                minimum=1.0,
                                maximum=10.0,
                                step=0.1,
                                value=float(default_engine_settings[TTS_ENGINES['XTTSv2']]['repetition_penalty']),
                                elem_id='gr_xtts_repetition_penalty',
                                info='Penalizes repeated phrases. Higher values reduce repetition.'
                            )
                            gr_xtts_top_k = gr.Slider(
                                label='Top-k Sampling',
                                minimum=10,
                                maximum=100,
                                step=1,
                                value=int(default_engine_settings[TTS_ENGINES['XTTSv2']]['top_k']),
                                elem_id='gr_xtts_top_k',
                                info='Lower values restrict outputs to more likely words and increase speed at which audio generates.'
                            )
                            gr_xtts_top_p = gr.Slider(
                                label='Top-p Sampling',
                                minimum=0.1,
                                maximum=1.0, 
                                step=0.01,
                                value=float(default_engine_settings[TTS_ENGINES['XTTSv2']]['top_p']),
                                elem_id='gr_xtts_top_p',
                                info='Controls cumulative probability for word selection. Lower values make the output more predictable and increase speed at which audio generates.'
                            )
                            gr_xtts_speed = gr.Slider(
                                label='Speed', 
                                minimum=0.5, 
                                maximum=3.0, 
                                step=0.1, 
                                value=float(default_engine_settings[TTS_ENGINES['XTTSv2']]['speed']),
                                elem_id='gr_xtts_speed',
                                info='Adjusts how fast the narrator will speak.'
                            )
                            gr_xtts_enable_text_splitting = gr.Checkbox(
                                label='Enable Text Splitting', 
                                value=default_engine_settings[TTS_ENGINES['XTTSv2']]['enable_text_splitting'],
                                elem_id='gr_xtts_enable_text_splitting',
                                info='Coqui-tts builtin text splitting. Can help against hallucinations bu can also be worse.',
                                visible=False
                            )
                    gr_tab_bark_params = gr.Tab('Bark Settings', elem_id='gr_tab_bark_params', elem_classes='gr-tab', visible=visible_gr_tab_bark_params)
                    with gr_tab_bark_params:
                        gr.Markdown(
                            elem_id='gr_markdown_tab_bark_params',
                            value="### Customize BARK Parameters\nAdjust the settings below to influence how the audio is generated, emotional and voice behavior random or more conservative"
                        )
                        with gr.Group(elem_id='gr_group_bark_params', elem_classes=['gr-group']):
                            gr_bark_text_temp = gr.Slider(
                                label='Text Temperature',
                                minimum=0.0,
                                maximum=1.0,
                                step=0.01,
                                value=float(default_engine_settings[TTS_ENGINES['BARK']]['text_temp']),
                                elem_id='gr_bark_text_temp',
                                info='Higher values lead to more creative, unpredictable outputs. Lower values make it more conservative.'
                            )
                            gr_bark_waveform_temp = gr.Slider(
                                label='Waveform Temperature',
                                minimum=0.0,
                                maximum=1.0,
                                step=0.01,
                                value=float(default_engine_settings[TTS_ENGINES['BARK']]['waveform_temp']),
                                elem_id='gr_bark_waveform_temp',
                                info='Higher values lead to more creative, unpredictable outputs. Lower values make it more conservative.'
                            )

                    gr_tab_supertonic_params = gr.Tab('Supertonic Settings', elem_id='gr_tab_supertonic_params', elem_classes='gr-tab', visible=interface_component_options['gr_tab_supertonic_params'])
                    with gr_tab_supertonic_params:
                        gr.Markdown(
                            elem_id='gr_markdown_tab_supertonic_params',
                            value="### Customize Supertonic Parameters\nAdjust the settings below to influence how the audio is generated with Supertonic TTS"
                        )
                        with gr.Group(elem_id='gr_group_supertonic_params', elem_classes=['gr-group']):
                            gr_supertonic_speed = gr.Slider(
                                label='Speed',
                                minimum=0.1,
                                maximum=3.0,
                                step=0.1,
                                value=float(default_engine_settings[TTS_ENGINES['SUPERTONIC']]['speed']),
                                elem_id='gr_supertonic_speed',
                                info='Adjusts how fast the narrator will speak.'
                            )
                            gr_supertonic_total_step = gr.Slider(
                                label='Total Step',
                                minimum=1,
                                maximum=100,
                                step=1,
                                value=int(default_engine_settings[TTS_ENGINES['SUPERTONIC']]['total_step']),
                                elem_id='gr_supertonic_total_step',
                                info='Higher values improve quality but increase generation time. 10 is recommended for normal speech.'
                            )
                with gr.Group(elem_id='gr_group_progress', elem_classes=['gr-group-sides-padded']):
                    gr_progress_markdown = gr.Markdown(elem_id='gr_progress_markdown', elem_classes=['gr-markdown'], value='Status')
                    gr_progress = gr.Textbox(elem_id='gr_progress', label='', interactive=False, visible=True)
                gr_group_audiobook_list = gr.Group(elem_id='gr_group_audiobook_list', elem_classes=['gr-group-sides-padded'], visible=True)
                with gr_group_audiobook_list:
                    gr_audiobook_markdown = gr.Markdown(elem_id='gr_audiobook_markdown', elem_classes=['gr-markdown'], value='Audiobook')
                    gr_audiobook_vtt = gr.Textbox(elem_id='gr_audiobook_vtt', label='', interactive=False, visible='hidden')
                    gr_playback_time = gr.Number(elem_id="gr_playback_time", label='', interactive=False, visible='hidden', value=0.0)
                    gr_audiobook_sentence = gr.Textbox(elem_id='gr_audiobook_sentence', label='', value='...', interactive=False, lines=3, max_lines=3)
                    gr_audiobook_player = gr.Audio(elem_id='gr_audiobook_player', label='', type='filepath', autoplay=False, interactive=False, waveform_options=gr.WaveformOptions(show_recording_waveform=False), show_download_button=False, show_share_button=False, container=True, visible=True)
                    gr_row_audiobook_list = gr.Row(elem_id='gr_row_audiobook_list', visible=True)
                    with gr_row_audiobook_list:
                        gr_audiobook_download_btn = gr.Button(elem_id='gr_audiobook_download_btn', value='↧', elem_classes=['small-btn'], variant='secondary', interactive=True, scale=0, min_width=60)
                        gr_audiobook_list = gr.Dropdown(elem_id='gr_audiobook_list', label='', choices=audiobook_options, type='value', interactive=True, scale=2)
                        gr_audiobook_del_btn = gr.Button(elem_id='gr_audiobook_del_btn', value='🗑', elem_classes=['small-btn-red'], variant='secondary', interactive=True, scale=0, min_width=60)
                    gr_audiobook_files = gr.Files(label='', elem_id='gr_audiobook_files', visible=False)
                    gr_audiobook_files_toggled = gr.State(False)
                with gr.Group(elem_id='gr_convert_btn', elem_classes=['gr-group-convert-btn']):
                    with gr.Row():
                        gr_convert_btn = gr.Button(elem_id='gr_convert_btn', value='Convert 📚', elem_classes='gr-convert-btn', variant='primary', interactive=False, scale=2)
                        gr_main_cancel_btn = gr.Button(elem_id='gr_main_cancel_btn', value='Cancel Job 🛑', variant='secondary', scale=1)

            gr_version_markdown = gr.Markdown(elem_id='gr_version_markdown', value=f'<div style="right:0;margin:auto;padding:10px;text-align:center"><a href="https://github.com/DrewThomasson/ebook2audiobook" style="text-decoration:none;font-size:14px" target="_blank"><b>{title}</b>&nbsp;<b style="color:orange; text-shadow: 0.3px 0.3px 0.3px #303030">{prog_version}</b></a></div>')

            # Chapter Editor Modal - Native Gradio Components
            with gr.Group(visible=False, elem_id="gr_chapter_editor_group") as gr_chapter_editor_group:
                with gr.Row():
                    gr.Markdown("## Chapter Editor", elem_classes=["chapter-editor-header"])
                    gr_chapter_cancel_btn = gr.Button("✕", variant="secondary", elem_id="gr_chapter_cancel_btn", scale=0, min_width=40)
                
                gr.Markdown("Edit your chapters below. Rows can be added or deleted.", elem_classes=["chapter-editor-desc"])
                
                gr_chapter_dataframe = gr.Dataframe(
                    headers=["Chapter Content"],
                    datatype=["str"],
                    col_count=(1, "fixed"),
                    interactive=True,
                    wrap=True,
                    elem_id="gr_chapter_dataframe"
                )
                
                with gr.Row():
                    # Populate choices from language_mapping keys or a default list if not yet defined at this point
                    # We'll use a placeholder for now and populate it in show_chapter_editor_overlay if dynamic update is needed
                    # But ideally we want it static. Let's assume language_mapping is available.
                    gr_chapter_trans_lang = gr.Dropdown(
                        label=None,
                        show_label=False, 
                        choices=[("No Translation (Keep Original)", "")] + get_translation_languages(),
                        value="",
                        interactive=True,
                        elem_id="gr_chapter_trans_lang",
                        scale=3,
                        container=False
                    )
                    gr_chapter_translate_btn = gr.Button("🌐 Translate", variant="secondary", elem_id="gr_chapter_translate_btn", scale=1)
                    gr_chapter_save_btn = gr.Button("💾 Save", variant="primary", elem_id="gr_chapter_save_btn", scale=1)

            with gr.Group(visible=False, elem_id='gr_group_blocks', elem_classes=['gr-group-main']) as gr_group_blocks:
                gr.Markdown('### Confirm Blocks')
                with gr.Group() as gr_group_blocks_content:
                    pass
                with gr.Row():
                    gr_confirm_blocks_yes_btn = gr.Button(elem_id='gr_confirm_blocks_yes_btn', elem_classes=['hide-elem'], value='', variant='secondary', visible=True, scale=0, min_width=30)
                    gr_confirm_blocks_no_btn = gr.Button(elem_id='gr_confirm_blocks_no_btn', elem_classes=['hide-elem'], value='', variant='secondary', visible=True, scale=0, min_width=30)

            gr_modal = gr.HTML(visible=False)
            gr_glassmask = gr.HTML(gr_glassmask_msg, elem_id='gr_glassmask', elem_classes=['gr-glass-mask'])
            gr_confirm_deletion_field_hidden = gr.Textbox(elem_id='confirm_hidden', visible=False)
            gr_confirm_deletion_yes_btn = gr.Button(elem_id='gr_confirm_deletion_yes_btn', elem_classes=['hide-elem'], value='', variant='secondary', visible=True, scale=0, min_width=30)
            gr_confirm_deletion_no_btn = gr.Button(elem_id='gr_confirm_deletion_no_btn', elem_classes=['hide-elem'], value='', variant='secondary', visible=True, scale=0, size='sm', min_width=0)

            gr_state_update = gr.State(value={'hash': None})
            gr_restore_session = gr.JSON(elem_id='gr_restore_session', visible='hidden')
            gr_save_session = gr.JSON(elem_id='gr_save_session', visible='hidden') 

            def disable_components()->tuple:
                outputs = tuple([gr.update(interactive=False) for _ in range(12)])
                return outputs
            
            def enable_components(id:str)->tuple:
                session = context.get_session(id)
                if session['event'] == 'confirm_blocks':
                    outputs = tuple([gr.update() for _ in range(12)])
                else:
                    outputs = tuple([gr.update(interactive=True) for _ in range(12)])
                return outputs

            def show_gr_modal(type:str, msg:str)->str:
                return f'<div id="custom-gr_modal" class="gr-modal"><div class="gr-modal-content"><p style="color:#ffffff; word-wrap:break-word; overflow-wrap:break-word; white-space:pre-wrap;">{msg[:70]}...</p>{show_confirm_buttons(type)}</div></div>'

            def show_confirm_buttons(mode:str)->str:
                if mode in ['confirm_deletion', 'confirm_blocks']:
                    button_yes = f'#gr_{mode}_yes_btn'
                    button_no = f'#gr_{mode}_no_btn'
                    return f'<div class="confirm-buttons"><button class="button-green" onclick="document.querySelector(\'{button_yes}\').click()">✔</button><button class="button-red" onclick="document.querySelector(\'{button_no}\').click()">⨉</button></div>'
                else:
                    return '<div class="spinner"></div>'

            def show_rating(tts_engine:str)->str:
                def yellow_stars(n:int):
                    return "".join(
                        "<span style='color:#f0bc00; font-size:12px'>★</span>" for _ in range(n)
                    )

                def color_box(value:int)->str:
                    if value <= 4:
                        color = "#4CAF50"  # Green = low
                    elif value <= 8:
                        color = "#FF9800"  # Orange = medium
                    else:
                        color = "#F44336"  # Red = high
                    return f"<span style='background:{color};color:white; padding: 0 3px 0 3px; border-radius:3px; font-size:11px; white-space: nowrap'>{str(value)} GB</span>"
                
                rating = default_engine_settings[tts_engine]['rating']
                return f'<div style="display:flex; justify-content:space-between; align-items:flex-end;"><span class="gr-markdown-span">TTS Engine</span><table style="display:inline-block; border-collapse:collapse; border:none; margin:0; padding:0; font-size:12px; line-height:1.2;"><tr style="border:none; vertical-align:bottom;"><td style="padding:0 5px 0 2.5px; border:none; vertical-align:bottom;"><b>VRAM:</b> {color_box(int(rating["VRAM"]))}</td><td style="padding:0 5px 0 2.5px; border:none; vertical-align:bottom;"><b>CPU:</b> {yellow_stars(int(rating["CPU"]))}</td><td style="padding:0 5px 0 2.5px; border:none; vertical-align:bottom;"><b>RAM:</b> {color_box(int(rating["RAM"]))}</td><td style="padding:0 5px 0 2.5px; border:none; vertical-align:bottom;"><b>Realism:</b> {yellow_stars(int(rating["Realism"]))}</td></tr></table></div>'

            def restore_interface(id:str, req:gr.Request)->tuple:
                try:
                    session = context.get_session(id)
                    socket_hash = str(req.session_hash)
                    if not session.get(socket_hash):
                        outputs = tuple([gr.update() for _ in range(15)])
                        return outputs
                    ebook_data = None
                    file_count = session['ebook_mode']
                    if session['ebook_list'] is not None and file_count == 'directory':
                        session['ebook'] = None
                        ebook_data = [f for f in session["ebook_list"] if os.path.exists(f)]
                        if not ebook_data:
                            ebook_data = None
                    elif isinstance(session['ebook'], str) and file_count == 'single':
                        session['ebook_list'] = None
                        if os.path.exists(session['ebook']):
                            ebook_data = session['ebook']
                        else:
                            ebook_data = session['ebook'] = None
                    else:
                        ebook_data = session['ebook'] = None
                    if ebook_data is not None:
                        current_dir_cache = tempfile.gettempdir()
                        current_dir_cache_norm = os.path.normpath(current_dir_cache)
                        prev_cache_dir = os.path.normpath(os.path.dirname(ebook_data[0]) if isinstance(ebook_data, list) else os.path.dirname(ebook_data))
                        if prev_cache_dir != current_dir_cache_norm:
                            ebook_data = None
                        session['ebook'] = ebook_data
                    visible_row_split_hours = True if session['output_split'] else False
                    return (
                        gr.update(value=ebook_data),
                        gr.update(value=session['ebook_mode']),
                        gr.update(value=bool(session['chapters_preview'])),
                        gr.update(value=session['device']),
                        gr.update(value=session['language']),
                        update_gr_voice_list(id),
                        update_gr_tts_engine_list(id),
                        update_gr_custom_model_list(id),
                        update_gr_fine_tuned_list(id),
                        gr.update(value=session['output_format']),
                        gr.update(value=session['output_channel']),
                        gr.update(value=bool(session['output_split'])),
                        gr.update(value=session['output_split_hours']),
                        gr.update(visible=visible_row_split_hours),
                        update_gr_audiobook_list(id)
                    )
                except Exception as e:
                    error = f'restore_interface(): {e}'
                    alert_exception(error, id)
                    outputs = tuple([gr.update() for _ in range(15)])
                    return outputs

            def restore_audiobook_player(audiobook:str|None)->tuple:
                try:
                    visible = True if audiobook is not None else False
                    return gr.update(visible=visible), gr.update(value=audiobook), gr.update(active=True)
                except Exception as e:
                    error = f'restore_audiobook_player(): {e}'
                    alert_exception(error, None)
                    outputs = tuple([gr.update() for _ in range(3)])
                    return outputs

            def refresh_interface(id:str)->tuple:
                session = context.get_session(id)
                if session['event'] == 'confirm_blocks':
                    outputs = tuple([gr.update() for _ in range(9)])
                    return outputs
                else:
                    return (
                        gr.update(interactive=False), gr.update(value=None), gr.update(value=session['device']), update_gr_audiobook_list(id), 
                        gr.update(value=session['audiobook']), gr.update(visible=False), update_gr_voice_list(id), gr.update(value='')
                    )

            def change_gr_audiobook_list(selected:str|None, id:str)->dict:
                try:
                    session = context.get_session(id)
                    session['audiobook'] = selected
                    group_visible = True if len(audiobook_options) > 0 else False
                    return gr.update(visible=group_visible)
                except Exception as e:
                    error = f'change_gr_audiobook_list(): {e}'
                    alert_exception(error, id)
                return gr.update(visible=group_visible)

            def update_gr_audiobook_player(id:str)->tuple:
                try:
                    session = context.get_session(id)
                    if session['audiobook'] is not None: 
                        vtt = Path(session['audiobook']).with_suffix('.vtt')
                        if not os.path.exists(session['audiobook']) or not os.path.exists(vtt):
                            error = f"{Path(session['audiobook']).name} does not exist!"
                            print(error)
                            alert_exception(error, id)
                            return gr.update(value=0.0), gr.update(value=None), gr.update(value=None)
                        audio_info = mediainfo(session['audiobook'])
                        duration = audio_info.get('duration', False)
                        if duration:
                            session['duration'] = float(audio_info['duration'])
                            with open(vtt, "r", encoding="utf-8-sig", errors="replace") as f:
                                vtt_content = f.read()
                            return gr.update(value=0.0), gr.update(value=session['audiobook']), gr.update(value=vtt_content)
                        else:
                            error = f"{Path(session['audiobook']).name} corrupted or not encoded!"
                            print(error)
                            alert_exception(error, id)
                except Exception as e:
                    error = f'update_gr_audiobook_player(): {e}'
                    print(error)
                    alert_exception(error, id)
                return gr.update(value=0.0), gr.update(value=None), gr.update(value=None)

            def update_gr_glassmask(str:str=gr_glassmask_msg, attr:list=['gr-glass-mask'])->dict:
                return gr.update(value=str, elem_id='gr_glassmask', elem_classes=attr)

            def change_convert_btn(upload_file:str|None=None, upload_file_mode:str|None=None, custom_model_file:str|None=None, session:DictProxy=None)->dict:
                try:
                    if session is None:
                        return gr.update(variant='primary', interactive=False)
                    else:
                        if hasattr(upload_file, 'name') and not hasattr(custom_model_file, 'name'):
                            return gr.update(variant='primary', interactive=True)
                        elif isinstance(upload_file, list) and len(upload_file) > 0 and upload_file_mode == 'directory' and not hasattr(custom_model_file, 'name'):
                            return gr.update(variant='primary', interactive=True)
                        else:
                            return gr.update(variant='primary', interactive=False)
                except Exception as e:
                    error = f'change_convert_btn(): {e}'
                    alert_exception(error, None)
                    return gr.update()

            def change_gr_ebook_file(data:str|None, id:str, progress=gr.Progress())->tuple:
                try:
                    print(f"DEBUG change_gr_ebook_file: data type={type(data)}, data={data}")
                    session = context.get_session(id)
                    session["ebook"] = None
                    session["ebook_list"] = None
                    session["chapters"] = None  # Reset chapters when file changes
                    if data is None:
                        print("DEBUG: data is None")
                        if session.get("status") == "converting":
                            session["cancellation_requested"] = True
                            msg = "Cancellation requested, please wait..."
                            yield gr.update(value=show_gr_modal("wait", msg), visible=True)
                            return
                    # Get max_chars from current TTS engine settings
                    tts_engine = session.get('tts_engine', default_tts_engine)
                    max_chars = default_engine_settings.get(tts_engine, {}).get('max_chars', 250)
                    print(f"DEBUG: Using max_chars={max_chars} for TTS engine {tts_engine}")
                    
                    if isinstance(data, list):
                        print(f"DEBUG: data is list with {len(data)} items")
                        ebook_list = []
                        for f in data:
                            path = f.get("path") if isinstance(f, dict) else str(f)
                            ebook_list.append(path)
                        session["ebook_list"] = ebook_list
                        # Extract preview from first file in list
                        if ebook_list:
                            print(f"DEBUG: Calling extract_preview_chapters with {ebook_list[0]}")
                            result = extract_preview_chapters(ebook_list[0], id, max_chars, progress=progress)
                            print(f"DEBUG: extract_preview_chapters returned: {result is not None}, chapters in session: {session.get('chapters') is not None}")
                    else:
                        # Data could be a file path string or a Gradio FileData object
                        file_path = data
                        if hasattr(data, 'name'):
                            file_path = data.name
                        elif isinstance(data, dict) and 'path' in data:
                            file_path = data['path']
                        print(f"DEBUG: file_path={file_path}")
                        session["ebook"] = file_path
                        # Extract preview chapters for the Chapter Editor
                        if file_path:
                            print(f"DEBUG: Calling extract_preview_chapters with {file_path}")
                            result = extract_preview_chapters(file_path, id, max_chars, progress=progress)
                            print(f"DEBUG: extract_preview_chapters returned: {result is not None}, chapters in session: {session.get('chapters') is not None}")
                    session["cancellation_requested"] = False
                    return gr.update(value='', visible=False)


                except Exception as e:
                    error = f'change_gr_ebook_file(): {e}'
                    print(f"DEBUG ERROR: {error}")
                    import traceback
                    traceback.print_exc()
                    alert_exception(error, id)
                return gr.update(value='', visible=False)

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
                    
                    return gr.update(), gr.update(value='', visible=False)
                except Exception as e:
                    print(f"reprocess_ebook Error: {e}")
                    import traceback
                    traceback.print_exc()
                    return gr.update(), gr.update()

            def change_gr_ebook_mode(val:str, id:str)->tuple:
                session = context.get_session(id)
                session['ebook_mode'] = val
                if val == 'single':
                    return gr.update(label=src_label_file, file_count='single'), gr.update(visible=True)
                else:
                    return gr.update(label=src_label_dir, file_count='directory'), gr.update(visible=False)

            def change_gr_force_ocr(val:bool, id:str)->None:
                session = context.get_session(id)
                session['force_ocr'] = val
                print(f"Session {id} force_ocr set to {val}")

            def change_gr_voice_file(f:str|None, id:str)->tuple:
                state = {}
                if f is not None:
                    if len(voice_options) > max_custom_voices:
                        error = f'You are allowed to upload a max of {max_custom_voices} voices'
                        state['type'] = 'warning'
                        state['msg'] = error
                    elif os.path.splitext(f.name)[1] not in voice_formats:
                        error = f'The audio file format selected is not valid.'
                        state['type'] = 'warning'
                        state['msg'] = error
                    else:                  
                        session = context.get_session(id)
                        voice_name = os.path.splitext(os.path.basename(f))[0].replace('&', 'And')
                        voice_name = get_sanitized(voice_name)
                        final_voice_file = os.path.join(session['voice_dir'], f'{voice_name}.wav')
                        extractor = VoiceExtractor(session, f, voice_name)
                        status, msg = extractor.extract_voice()
                        if status:
                            session['voice'] = final_voice_file
                            msg = f'Voice {voice_name} added to the voices list'
                            state['type'] = 'success'
                            state['msg'] = msg
                            show_alert(state)
                            return update_gr_voice_list(id)
                        else:
                            error = 'failed! Check if you audio file is compatible.'
                            state['type'] = 'warning'
                            state['msg'] = error
                    show_alert(state)
                return gr.update()

            def change_gr_voice_list(selected:str|None, id:str)->tuple:
                session = context.get_session(id)
                session['voice'] = next((value for label, value in voice_options if value == selected), voice_options[0][1])
                visible = True if session['voice'] is not None else False
                return gr.update(value=session['voice']), gr.update(visible=visible), gr.update(visible=visible)

            def click_gr_voice_del_btn(selected:str, id:str)->tuple:
                try:
                    if selected is not None:
                        session = context.get_session(id)
                        speaker_path = os.path.abspath(selected)
                        speaker = re.sub(r'\.wav$|\.npz|\.pth$', '', os.path.basename(selected))
                        builtin_root = os.path.join(voices_dir, session['language'])
                        is_in_builtin = os.path.commonpath([
                            speaker_path,
                            os.path.abspath(builtin_root)
                        ]) == os.path.abspath(builtin_root)
                        is_in_models = os.path.commonpath([
                            speaker_path,
                            os.path.abspath(session['custom_model_dir'])
                        ]) == os.path.abspath(session['custom_model_dir'])
                        # Check if voice is built-in
                        is_builtin = any(
                            speaker in settings.get('voices', {})
                            for settings in (default_engine_settings[engine] for engine in TTS_ENGINES.values())
                        )
                        if is_builtin and is_in_builtin:
                            error = f'Voice file {speaker} is a builtin voice and cannot be deleted.'
                            show_alert({"type": "warning", "msg": error})
                            return gr.update(), gr.update(visible=False)
                        if is_in_models:
                            error = f'Voice file {speaker} is a voice of one of your custom model and cannot be deleted.'
                            show_alert({"type": "warning", "msg": error})
                            return gr.update(), gr.update(visible=False)                          
                        try:
                            selected_path = Path(selected).resolve()
                            parent_path = Path(session['voice_dir']).parent.resolve()
                            if parent_path in selected_path.parents:
                                msg = f'Are you sure to delete {speaker}...'
                                return (
                                    gr.update(value='confirm_voice_del'),
                                    gr.update(value=show_gr_modal('confirm_deletion', msg), visible=True)
                                )
                            else:
                                error = f'{speaker} is part of the global voices directory. Only your own custom uploaded voices can be deleted!'
                                show_alert({"type": "warning", "msg": error})
                                return gr.update(), gr.update(visible=False)
                        except Exception as e:
                            error = f'Could not delete the voice file {selected}!\n{e}'
                            alert_exception(error, id)
                            return gr.update(), gr.update(visible=False)
                    # Fallback/default return if not selected or after errors
                    return gr.update(), gr.update(visible=False)
                except Exception as e:
                    error = f'click_gr_voice_del_btn(): {e}'
                    alert_exception(error, id)
                    return gr.update(), gr.update(visible=False)

            def click_gr_custom_model_del_btn(selected:str, id:str)->tuple:
                try:
                    if selected is not None:
                        session = context.get_session(id)
                        selected_name = os.path.basename(selected)
                        msg = f'Are you sure to delete {selected_name}...'
                        return gr.update(value='confirm_custom_model_del'), gr.update(value=show_gr_modal('confirm_deletion', msg), visible=True)
                except Exception as e:
                    error = f'Could not delete the custom model {selected_name}!'
                    alert_exception(error, id)
                return gr.update(), gr.update(visible=False)

            def click_gr_audiobook_del_btn(selected:str, id:str)->tuple:
                try:
                    if selected is not None:
                        session = context.get_session(id)
                        selected_name = Path(selected).stem
                        msg = f'Are you sure to delete {selected_name}...'
                        return gr.update(value='confirm_audiobook_del'), gr.update(value=show_gr_modal('confirm_deletion', msg), visible=True)
                except Exception as e:
                    error = f'Could not delete the audiobook {selected_name}!'
                    alert_exception(error, id)
                return gr.update(), gr.update(visible=False), gr.update(visible=False)

            def confirm_deletion(voice_path:str, custom_model:str, audiobook:str, id:str, method:str|None=None)->tuple:
                try:
                    if method is not None:
                        session = context.get_session(id)
                        if method == 'confirm_voice_del':
                            selected_name = Path(voice_path).stem
                            pattern = re.sub(r'\.wav$', '*.wav', voice_path)
                            files2remove = glob(pattern)
                            for file in files2remove:
                                os.remove(file)
                            shutil.rmtree(os.path.join(os.path.dirname(voice_path), 'bark', selected_name), ignore_errors=True)
                            msg = f"Voice file {re.sub(r'.wav$', '', selected_name)} deleted!"
                            session['voice'] = None
                            show_alert({"type": "warning", "msg": msg})
                            return gr.update(), gr.update(), gr.update(value='', visible=False), update_gr_voice_list(id)
                        elif method == 'confirm_custom_model_del':
                            selected_name = os.path.basename(custom_model)
                            shutil.rmtree(custom_model, ignore_errors=True)                           
                            msg = f'Custom model {selected_name} deleted!'
                            if session['custom_model'] in session['voice']:
                                session['voice'] = None if voice_options[0][1] == None else models[session['tts_engine']][session['fine_tuned']]['voice']
                            session['custom_model'] = None
                            show_alert({"type": "warning", "msg": msg})
                            return update_gr_custom_model_list(id), gr.update(), gr.update(value='', visible=False), gr.update()
                        elif method == 'confirm_audiobook_del':
                            selected_name = Path(audiobook).stem
                            if os.path.isdir(audiobook):
                                shutil.rmtree(selected, ignore_errors=True)
                            elif os.path.exists(audiobook):
                                os.remove(audiobook)
                            vtt_path = Path(audiobook).with_suffix('.vtt')
                            if os.path.exists(vtt_path):
                                os.remove(vtt_path)
                            process_dir = os.path.join(session['session_dir'], f"{hashlib.md5(os.path.join(session['audiobooks_dir'], audiobook).encode()).hexdigest()}")
                            shutil.rmtree(process_dir, ignore_errors=True)
                            msg = f'Audiobook {selected_name} deleted!'
                            session['audiobook'] = None
                            show_alert({"type": "warning", "msg": msg})
                            return gr.update(), update_gr_audiobook_list(id), gr.update(value='', visible=False), gr.update()
                except Exception as e:
                    error = f'confirm_deletion(): {e}!'
                    alert_exception(error, id)
                return gr.update(), gr.update(), gr.update(value='', visible=False), gr.update()

            def confirm_blocks(choice:str, id:str)->dict:
                session = context.get_session(id)
                if choice == 'yes':           
                    session['event'] = 'blocks_confirmed'
                else:
                    session['status'] = 'ready'
                return gr.update(value='', visible=False)

            def update_gr_voice_list(id:str)->dict:
                try:
                    nonlocal voice_options
                    session = context.get_session(id)
                    lang_dir = session['language'] if session['language'] != 'con' else 'con-'  # Bypass Windows CON reserved name
                    file_pattern = "*.wav"
                    eng_options = []
                    bark_options = []
                    builtin_options = [
                        (os.path.splitext(f.name)[0], str(f))
                        for f in Path(os.path.join(voices_dir, lang_dir)).rglob(file_pattern)
                    ]
                    if session['language'] in language_tts[TTS_ENGINES['XTTSv2']]:
                        builtin_names = {t[0]: None for t in builtin_options}
                        eng_dir = Path(os.path.join(voices_dir, "eng"))
                        eng_options = [
                            (base, str(f))
                            for f in eng_dir.rglob(file_pattern)
                            for base in [os.path.splitext(f.name)[0]]
                            if base not in builtin_names
                        ]
                    if session['tts_engine'] == TTS_ENGINES['BARK']:
                        lang_dict = Lang(session['language'])
                        if lang_dict:
                            lang_iso1 = lang_dict.pt1
                            lang = lang_iso1.lower()
                            speakers_path = Path(default_engine_settings[TTS_ENGINES['BARK']]['speakers_path'])
                            pattern_speaker = re.compile(r"^.*?_speaker_(\d+)$")
                            bark_options = [
                                (pattern_speaker.sub(r"Speaker \1", f.stem), str(f.with_suffix(".wav")))
                                for f in speakers_path.rglob(f"{lang}_speaker_*.npz")
                            ]
                    # Handle SUPERTONIC built-in voices - SUPERTONIC uses text-based voice IDs only, not audio files
                    supertonic_options = []
                    if session['tts_engine'] == TTS_ENGINES['SUPERTONIC']:
                        supertonic_voices = default_engine_settings.get(TTS_ENGINES['SUPERTONIC'], {}).get('voices', {})
                        supertonic_options = [(desc, voice_id) for voice_id, desc in supertonic_voices.items()]
                        # For SUPERTONIC, only use text-based voice options (not audio files)
                        voice_options = supertonic_options
                    else:
                        # For other TTS engines, combine audio file voices
                        voice_options = builtin_options + eng_options + bark_options
                    session['voice_dir'] = os.path.join(voices_dir, '__sessions', f"voice-{session['id']}", session['language'])
                    os.makedirs(session['voice_dir'], exist_ok=True)
                    # Only add custom/session voices for non-SUPERTONIC engines
                    if session['tts_engine'] != TTS_ENGINES['SUPERTONIC']:
                        if session['voice_dir'] is not None:
                            session_voice_dir = Path(session['voice_dir'])
                            voice_options += [
                                (os.path.splitext(f.name)[0], str(f))
                                for f in session_voice_dir.rglob(file_pattern)
                                if f.is_file()
                            ]
                        if session.get('custom_model_dir'):
                            voice_options.extend(
                                (f.stem, str(f))
                                for f in Path(session['custom_model_dir']).rglob('*.wav')
                                if f.is_file()
                            )
                    if session['tts_engine'] in [TTS_ENGINES['VITS'], TTS_ENGINES['FAIRSEQ'], TTS_ENGINES['TACOTRON2'], TTS_ENGINES['YOURTTS']]:
                        voice_options = [('Default', None)] + sorted(voice_options, key=lambda x: x[0].lower())
                    else:
                        voice_options = sorted(voice_options, key=lambda x: x[0].lower())    
                    if session['voice'] is not None and session['voice'] not in [v[1] for v in voice_options]:
                        new_voice_path = session['voice'].replace('/eng/', f"/{session['language']}/")
                        # For SUPERTONIC, get default voice ID; for others, check if path exists
                        if session['tts_engine'] == TTS_ENGINES['SUPERTONIC']:
                            session['voice'] = models[session['tts_engine']][session['fine_tuned']]['voice']
                        else:
                            session['voice'] = new_voice_path if os.path.exists(new_voice_path) else (voice_options[0][1] if voice_options else None)
                    return gr.update(choices=voice_options, value=session['voice'])
                except Exception as e:
                    error = f'update_gr_voice_list(): {e}!'
                    alert_exception(error, id)
                    return gr.update()

            def update_gr_tts_engine_list(id:str)->dict:
                try:
                    nonlocal tts_engine_options
                    session = context.get_session(id)
                    tts_engine_options = get_compatible_tts_engines(session['language'])
                    session['tts_engine'] = session['tts_engine'] if session['tts_engine'] in tts_engine_options else tts_engine_options[0]
                    return gr.update(choices=tts_engine_options, value=session['tts_engine'])
                except Exception as e:
                    error = f'update_gr_tts_engine_list(): {e}!'
                    return gr.update()

            # Translation functions
            def get_translation_overlay_html(detected_lang: str = 'en') -> str:
                """Generate HTML for the translation overlay modal"""
                from lib.classes.translator import SUPPORTED_LANGUAGES
                lang_options = ''.join([
                    f'<option value="{code}">{name}</option>'
                    for code, name in sorted(SUPPORTED_LANGUAGES.items(), key=lambda x: x[1])
                ])
                detected_name = SUPPORTED_LANGUAGES.get(detected_lang, 'Unknown')
                return f'''
                <div id="translation_backdrop" class="translation-overlay-backdrop" onclick="window.closeTranslationOverlay()"></div>
                <div class="translation-overlay-content">
                    <div class="translation-overlay-header">
                        <h3 class="translation-overlay-title">🌐 Translate Document</h3>
                        <button class="translation-overlay-close" onclick="window.closeTranslationOverlay()">×</button>
                    </div>
                    <div class="translation-form-group">
                        <label class="translation-form-label">Detected Language</label>
                        <div class="translation-detected-lang">
                            {detected_name} ({detected_lang})
                        </div>
                    </div>
                    <div class="translation-form-group">
                        <label class="translation-form-label">Translate To</label>
                        <select id="translation_target_lang" class="translation-form-select">
                            {lang_options}
                        </select>
                    </div>
                    <div class="translation-form-group">
                        <label class="translation-form-label">Translation Service</label>
                        <select id="translation_service" class="translation-form-select">
                            <option value="google">Google Translate (Online)</option>
                            <option value="argos">Argos Translate (Offline)</option>
                            <!-- <option value="mymemory">MyMemory</option> -->
                        </select>
                    </div>
                    <div id="translation_progress" class="translation-progress" style="display: none;">
                        <span id="translation_status">Translating...</span>
                        <div class="translation-progress-bar">
                            <div id="translation_progress_fill" class="translation-progress-fill" style="width: 0%"></div>
                        </div>
                    </div>
                    <div class="translation-btn-row">
                        <button class="translation-btn translation-btn-secondary" onclick="window.closeTranslationOverlay()">Cancel</button>
                        <button id="start_translation_btn" class="translation-btn translation-btn-primary" onclick="window.startTranslation()">Translate</button>
                    </div>
                </div>
                '''

            def show_translation_overlay(id: str) -> tuple:
                """Show the translation overlay with detected language"""
                try:
                    session = context.get_session(id)
                    detected_lang = 'en'  # Default
                    
                    # Try to detect language from uploaded ebook file
                    ebook_path = session.get('ebook')
                    if ebook_path and isinstance(ebook_path, str) and os.path.exists(ebook_path):
                        try:
                            # Read text from the file (handle txt, epub, etc.)
                            sample_text = ""
                            if ebook_path.lower().endswith('.txt'):
                                with open(ebook_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    sample_text = f.read(2000)
                            else:
                                # For other formats, try reading as text
                                try:
                                    with open(ebook_path, 'r', encoding='utf-8', errors='ignore') as f:
                                        sample_text = f.read(2000)
                                except:
                                    pass
                            
                            if sample_text and len(sample_text) > 20:
                                from langdetect import detect
                                detected_lang = detect(sample_text)
                                print(f"Detected language: {detected_lang} from {ebook_path}")
                        except Exception as e:
                            print(f"Language detection error: {e}")
                    else:
                        print(f"No ebook path found in session. session['ebook'] = {ebook_path}")
                    
                    overlay_html = get_translation_overlay_html(detected_lang)
                    return gr.update(value=overlay_html, visible=True)
                except Exception as e:
                    print(f"show_translation_overlay error: {e}")
                    return gr.update(visible=False)

            def execute_translation(target_lang: str, service: str, id: str) -> tuple:
                """Execute the translation and update the session"""
                print(f">>> execute_translation CALLED: target_lang={target_lang}, service={service}, id={id}")
                try:
                    # Strip timestamp suffix from service (e.g., "google_1701234567890" -> "google")
                    if '_' in service and service.split('_')[-1].isdigit():
                        service = service.rsplit('_', 1)[0]
                    
                    # Skip if this is just the default value (not triggered by user)
                    if service == 'google' and target_lang == 'en':
                        print(f"Skipping default translation trigger")
                        return gr.update(), gr.update()
                    
                    from lib.classes.translator import translate_document, SUPPORTED_LANGUAGES
                    session = context.get_session(id)
                    
                    # Get language name for display
                    lang_name = SUPPORTED_LANGUAGES.get(target_lang, target_lang)
                    
                    print(f"Starting translation to {lang_name} ({target_lang}) using {service}")
                    
                    # Show starting status
                    show_alert({"type": "info", "msg": f"🌐 Translating to {lang_name}... Please wait."})
                    
                    success, translated_path, error = translate_document(session, target_lang, service)
                    
                    if success:
                        show_alert({"type": "success", "msg": f"✅ Translation complete! Document translated to {lang_name}."})
                        print(f"Translation successful: {translated_path}")
                        return gr.update(visible=False), gr.update(value=f"✅ Translated to {lang_name}")
                    else:
                        show_alert({"type": "error", "msg": f"❌ Translation failed: {error}"})
                        print(f"Translation failed: {error}")
                        return gr.update(visible=False), gr.update(value=f"❌ Translation failed")
                except Exception as e:
                    show_alert({"type": "error", "msg": f"❌ Translation error: {e}"})
                    print(f"Translation exception: {e}")
                    return gr.update(visible=False), gr.update(value=f"❌ Error: {e}")

            def update_gr_custom_model_list(id:str)->dict:
                try:
                    nonlocal custom_model_options
                    session = context.get_session(id)
                    custom_model_tts_dir = check_custom_model_tts(session['custom_model_dir'], session['tts_engine'])
                    custom_model_options = [('None', None)] + [
                        (
                            str(dir),
                            os.path.join(custom_model_tts_dir, dir)
                        )
                        for dir in os.listdir(custom_model_tts_dir)
                        if os.path.isdir(os.path.join(custom_model_tts_dir, dir))
                    ]
                    session['custom_model'] = session['custom_model'] if session['custom_model'] in [option[1] for option in custom_model_options] else custom_model_options[0][1]
                    model_paths = {v[1] for v in custom_model_options}
                    return gr.update(choices=custom_model_options, value=session['custom_model'])
                except Exception as e:
                    error = f'update_gr_custom_model_list(): {e}!'
                    alert_exception(error, id)
                    return gr.update()

            def update_gr_fine_tuned_list(id:str)->dict:
                try:
                    nonlocal fine_tuned_options
                    session = context.get_session(id)
                    fine_tuned_options = [
                        name for name, details in models.get(session['tts_engine'], {}).items()
                        if details.get('lang') in ('multi', session['language'])
                    ]
                    if session['fine_tuned'] in fine_tuned_options:
                        fine_tuned = session['fine_tuned']
                    else:
                        fine_tuned = default_fine_tuned
                    session['fine_tuned'] = fine_tuned
                    return gr.update(choices=fine_tuned_options, value=session['fine_tuned'])
                except Exception as e:
                    error = f'update_gr_fine_tuned_list(): {e}!'
                    alert_exception(error, id)              
                    return gr.update()

            def change_gr_device(selected:str, id:str)->None:
                session = context.get_session(id)
                session['device'] = selected

            def change_gr_language(selected:str, id:str)->tuple:
                if selected:
                    session = context.get_session(id)
                    prev = session['language']      
                    session['language'] = selected
                    return (
                        gr.update(value=session['language']),
                        update_gr_tts_engine_list(id),
                        update_gr_custom_model_list(id),
                        update_gr_fine_tuned_list(id),
                        update_gr_voice_list(id)
                    )
                return gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

            def check_custom_model_tts(custom_model_dir:str, tts_engine:str)->str|None:
                dir_path = None
                if custom_model_dir is not None and tts_engine is not None:
                    dir_path = os.path.join(custom_model_dir, tts_engine)
                    if not os.path.isdir(dir_path):
                        os.makedirs(dir_path, exist_ok=True)
                return dir_path

            def change_gr_custom_model_file(f:str|None, t:str, id:str)->tuple:
                if f is not None:
                    state = {}
                    if len(custom_model_options) > max_custom_model:
                        error = f'You are allowed to upload a max of {max_custom_models} models'   
                        state['type'] = 'warning'
                        state['msg'] = error
                    else:
                        session = context.get_session(id)
                        session['tts_engine'] = t
                        if analyze_uploaded_file(f, models[session['tts_engine']]['internal']['files']):
                            model = extract_custom_model(f, id, models[session['tts_engine']][default_fine_tuned]['files'])
                            if model is not None:
                                session['custom_model'] = model
                                session['voice'] = os.path.join(model, f'{os.path.basename(os.path.normpath(model))}.wav')
                                msg = f'{os.path.basename(model)} added to the custom models list'
                                state['type'] = 'success'
                                state['msg'] = msg
                                show_alert(state)
                                return gr.update(value=None), update_gr_custom_model_list(id), update_gr_voice_list(id)
                            else:
                                error = f'Cannot extract custom model zip file {os.path.basename(f)}'
                                state['type'] = 'warning'
                                state['msg'] = error
                        else:
                            error = f'{os.path.basename(f)} is not a valid model or some required files are missing'
                            state['type'] = 'warning'
                            state['msg'] = error
                    show_alert(state)
                return gr.update(), gr.update(), gr.update()

            def change_gr_tts_engine_list(engine:str, id:str)->tuple:
                session = context.get_session(id)
                session['tts_engine'] = engine
                session['fine_tuned'] = default_fine_tuned
                session['voice'] = models[session['tts_engine']][session['fine_tuned']]['voice']
                if engine in [TTS_ENGINES['XTTSv2']]:
                    if session['custom_model'] is not None:
                        session['voice'] = os.path.join(session['custom_model'], f"{os.path.basename(session['custom_model'])}.wav")
                bark_visible = False
                supertonic_visible = False
                if session['tts_engine'] == TTS_ENGINES['XTTSv2']:
                    visible_custom_model = True if session['fine_tuned'] == 'internal' else False
                    return (
                        gr.update(value=show_rating(session['tts_engine'])),
                        gr.update(visible=visible_gr_tab_xtts_params),
                        gr.update(visible=False),
                        gr.update(visible=False),
                        gr.update(visible=visible_custom_model),
                        update_gr_fine_tuned_list(id),
                        gr.update(label=f"Upload {session['tts_engine']} ZIP file (Mandatory: {', '.join(models[session['tts_engine']][default_fine_tuned]['files'])})"),
                        update_gr_voice_list(id),
                        gr.update(value=f"My {session['tts_engine']} Custom Models")
                    )
                else:
                    if session['tts_engine'] == TTS_ENGINES['BARK']:
                        bark_visible = visible_gr_tab_bark_params
                    elif session['tts_engine'] == TTS_ENGINES['SUPERTONIC']:
                        supertonic_visible = interface_component_options['gr_tab_supertonic_params']
                    return (
                        gr.update(value=show_rating(session['tts_engine'])),
                        gr.update(visible=False),
                        gr.update(visible=bark_visible),
                        gr.update(visible=supertonic_visible),
                        gr.update(visible=False),
                        update_gr_fine_tuned_list(id),
                        gr.update(label=f"*Upload Custom Model not available for {session['tts_engine']}"),
                        update_gr_voice_list(id),
                        gr.update(value='')
                    )
                    
            def change_gr_fine_tuned_list(selected:str, id:str)->tuple:
                if selected:
                    session = context.get_session(id)
                    session['fine_tuned'] = selected
                    visible_custom_model = False
                    if selected == 'internal':
                        visible_custom_model = visible_gr_group_custom_model
                    else:
                        visible_custom_model = False
                        session['voice'] = models[session['tts_engine']][selected]['voice']
                    return gr.update(visible=visible_custom_model), update_gr_voice_list(id)
                return gr.update(), gr.update()

            def change_gr_custom_model_list(selected:str|None, id:str)->tuple:
                session = context.get_session(id)
                session['custom_model'] = selected
                if selected is not None:
                    session['voice'] = os.path.join(selected, f"{os.path.basename(selected)}.wav")
                visible_fine_tuned = True if selected is None else False
                visible_del_btn = False if selected is None else True
                return gr.update(visible=visible_fine_tuned), gr.update(visible=visible_del_btn), update_gr_voice_list(id)
            
            def change_gr_output_format_list(val:str, id:str)->None:
                session = context.get_session(id)
                session['output_format'] = val
                return

            def change_gr_output_channel_list(val:str, id:str)->None:
                session = context.get_session(id)
                session['output_channel'] = val
                return
                
            def change_gr_output_split(val:str, id:str)->dict:
                session = context.get_session(id)
                session['output_split'] = val
                return gr.update(visible=val)

            def change_gr_playback_time(time:float, id:str)->None:
                session = context.get_session(id)
                session['playback_time'] = time
                return

            def toggle_audiobook_files(audiobook:str, is_visible:bool)->tuple:
                if not audiobook:
                    error = 'No audiobook selected.'
                    alert_exception(error, None)
                    return gr.update(), False
                if is_visible:
                    return gr.update(visible=False, value=None), False
                p = Path(audiobook)
                if not p.exists():
                    error = f'Audio not found: {p}'
                    alert_exception(error, None)
                    return gr.update(), False
                files = [str(p)]
                vtt = p.with_suffix(".vtt")
                if vtt.exists():
                    files.append(str(vtt))
                return gr.update(visible=True, value=files), True

            def change_param(key:str, val:Any, id:str, val2:Any=None)->None:
                session = context.get_session(id)
                session[key] = val
                state = {}
                if key == 'xtts_length_penalty':
                    if val2 is not None:
                        if float(val) > float(val2):
                            error = 'Length penalty must be always lower than num beams if greater than 1.0 or equal if 1.0'
                            state['type'] = 'warning'
                            state['msg'] = error
                            show_alert(state)
                elif key == 'xtts_num_beams':
                    if val2 is not None:
                        if float(val) < float(val2):
                            error = 'Num beams must be always higher than length penalty or equal if its value is 1.0'
                            state['type'] = 'warning'
                            state['msg'] = error
                            show_alert(state)

            def submit_convert_btn(
                    id:str, device:str, ebook_file:str, chapters_preview:bool, tts_engine:str, language:str, voice:str, custom_model:str, fine_tuned:str, output_format:str, output_channel:str, xtts_temperature:float,
                    xtts_length_penalty:int, xtts_num_beams:int, xtts_repetition_penalty:float, xtts_top_k:int, xtts_top_p:float, xtts_speed:float, xtts_enable_text_splitting:bool, bark_text_temp:float, bark_waveform_temp:float,
                    supertonic_speed:float, supertonic_total_step:int,
                    output_split:bool, output_split_hours:str
                )->tuple:
                try:
                    session = context.get_session(id)
                    
                    # session['ebook'] or session['ebook_list'] acts as the source of truth,
                    # potentially updated by translation or chapter editing.
                    # The ebook_file argument from Gradio UI might point to the original file.
                    actual_ebook = session.get('ebook')
                    if not actual_ebook:
                        actual_ebook = ebook_file
                    
                    print(f"DEBUG: submit_convert_btn using ebook: {actual_ebook}")
                    
                    # If we have a list in session, use that
                    if session.get('ebook_list') and isinstance(session['ebook_list'], list):
                        ebook_file_list = session['ebook_list']
                    else:
                        ebook_file_list = actual_ebook if isinstance(actual_ebook, list) else None

                    args = {
                        "is_gui_process": session['is_gui_process'],
                        "session": id,
                        "script_mode": script_mode,
                        "chapters_preview": chapters_preview,
                        "device": device,
                        "tts_engine": tts_engine,
                        "ebook": actual_ebook if isinstance(actual_ebook, str) else None,
                        "ebook_list": ebook_file_list,
                        "audiobooks_dir": session['audiobooks_dir'],
                        "voice": voice,
                        "language": language,
                        "custom_model": custom_model,
                        "fine_tuned": fine_tuned,
                        "output_format": output_format,
                        "output_channel": output_channel,
                        "xtts_temperature": float(xtts_temperature),
                        "xtts_length_penalty": float(xtts_length_penalty),
                        "xtts_num_beams": int(session['xtts_num_beams']),
                        "xtts_repetition_penalty": float(xtts_repetition_penalty),
                        "xtts_top_k": int(xtts_top_k),
                        "xtts_top_p": float(xtts_top_p),
                        "xtts_speed": float(xtts_speed),
                        "xtts_enable_text_splitting": bool(xtts_enable_text_splitting),
                        "bark_text_temp": float(bark_text_temp),
                        "bark_waveform_temp": float(bark_waveform_temp),
                        "supertonic_speed": float(supertonic_speed),
                        "supertonic_total_step": int(supertonic_total_step),
                        "output_split": bool(output_split),
                        "output_split_hours": output_split_hours,
                        "event": None
                    }
                    error = None
                    if args['ebook'] is None and args['ebook_list'] is None:
                        error = 'Error: a file or directory is required.'
                        show_alert({"type": "warning", "msg": error})
                    elif args['xtts_num_beams'] < args['xtts_length_penalty']:
                        error = 'Error: num beams must be greater or equal than length penalty.'
                        show_alert({"type": "warning", "msg": error})                   
                    else:
                        session['status'] = 'converting'
                        session['progress'] = len(audiobook_options)
                        if isinstance(args['ebook_list'], list):
                            args['chapters_preview'] = None
                            ebook_list = args['ebook_list'][:]
                            for file in ebook_list:
                                if any(file.endswith(ext) for ext in ebook_formats):
                                    print(f'Processing eBook file: {os.path.basename(file)}')
                                    args['ebook'] = file
                                    progress_status, passed = convert_ebook(args)
                                    if passed is False:
                                        if session['status'] == 'converting':
                                            error = 'Conversion cancelled.'
                                            break
                                        else:
                                            error = 'Conversion failed.'
                                            break
                                    else:
                                        show_alert({"type": "success", "msg": progress_status})
                                        args['ebook_list'].remove(file)
                                        reset_session(args['session'])
                                        count_file = len(args['ebook_list'])
                                        if count_file > 0:
                                            msg = f"{os.path.basename(file)} / converted. {len(args['ebook_list'])} ebook(s) conversion remaining..."
                                            yield gr.update(value=msg), gr.update()
                                        else:
                                            msg = 'Conversion successful!'
                                            session['status'] = 'ready'
                                            return gr.update(value=msg), gr.update()
                        else:
                            print(f"Processing eBook file: {os.path.basename(args['ebook'])}")
                            progress_status, passed = convert_ebook(args)
                            if passed is False:
                                if session['status'] == 'converting':
                                    error = 'Conversion cancelled.'
                                else:
                                    error = 'Conversion failed.'
                            else:
                                if progress_status == 'confirm_blocks':
                                    session['event'] = progress_status
                                    msg = 'Select the blocks to convert:'
                                    print(msg)
                                    yield gr.update(value=''), gr.update(value=show_gr_modal(progress_status, msg), visible=True)
                                    return
                                else:
                                    show_alert({"type": "success", "msg": progress_status})
                                    reset_session(args['session'])
                                    msg = 'Conversion successful!'
                                    session['status'] = 'ready'
                                    return gr.update(value=msg), gr.update()
                    if error is not None:
                        show_alert({"type": "warning", "msg": error})
                except Exception as e:
                    error = f'submit_convert_btn(): {e}'
                    alert_exception(error, id)
                session['status'] = 'ready'
                return gr.update(), gr.update()
            
            def submit_confirmed_blocks(id:str)->tuple:
                try:
                    session = context.get_session(id)
                    error = None
                    if isinstance(session['ebook_list'], list):
                        ebook_list = session['ebook_list'][:]
                        for file in ebook_list:
                            if any(file.endswith(ext) for ext in ebook_formats):
                                print(f'Processing eBook file: {os.path.basename(file)}')
                                session['ebook'] = file
                                progress_status, passed = convert_ebook(session)
                                if passed is False:
                                    if session['status'] == 'converting':
                                        error = 'Conversion cancelled.'
                                        break
                                    else:
                                        error = 'Conversion failed.'
                                        break
                                else:
                                    show_alert({"type": "success", "msg": progress_status})
                                    session['ebook_list'].remove(file)
                                    reset_session(session['id'])
                                    msg = 'Conversion successful!'
                                    session['status'] = 'ready'
                                    return gr.update(value=msg), gr.update()
                    else:
                        print(f"Processing eBook file: {os.path.basename(session['ebook'])}")
                        progress_status, passed = convert_ebook(session)
                        if passed is False:
                            if session['status'] == 'converting':
                                error = 'Conversion cancelled.'
                            else:
                                error = 'Conversion failed.'
                            session['status'] = 'ready'
                        else:
                            show_alert({"type": "success", "msg": progress_status})
                            reset_session(session['id'])
                            msg = 'Conversion successful!'
                            session['status'] = 'ready'
                            return gr.update(value=msg), gr.update()
                    if error is not None:
                        show_alert({"type": "warning", "msg": error})
                except Exception as e:
                    error = f'submit_confirmed_blocks(): {e}'
                    alert_exception(error, id)
                return gr.update(), gr.update()          

            def update_gr_audiobook_list(id:str)->dict:
                try:
                    nonlocal audiobook_options
                    session = context.get_session(id)
                    if session['audiobooks_dir'] is not None:
                        audiobook_options = [
                            (f, os.path.join(session['audiobooks_dir'], str(f)))
                            for f in os.listdir(session['audiobooks_dir'])
                            if not f.lower().endswith(".vtt")
                        ]
                    audiobook_options.sort(
                        key=lambda x: os.path.getmtime(x[1]),
                        reverse=True
                    )
                    session['audiobook'] = (
                        session['audiobook']
                        if session['audiobook'] in [option[1] for option in audiobook_options]
                        else None
                    )
                    if len(audiobook_options) > 0:
                        if session['audiobook'] is not None:
                            return gr.update(choices=audiobook_options, value=session['audiobook'])
                        else:
                            return gr.update(choices=audiobook_options, value=audiobook_options[0][1])
                    else:
                        return gr.update(choices=audiobook_options, value=None)
                except Exception as e:
                    error = f'update_gr_audiobook_list(): {e}!'
                    alert_exception(error, id)              
                return gr.update()

            def change_gr_restore_session(data:DictProxy|None, state:dict, req:gr.Request)->tuple:
                try:
                    msg = 'Error while loading saved session. Please try to delete your cookies and refresh the page'
                    if data is None or isinstance(data, str) or not data.get('id'):
                        data = context.get_session(str(uuid.uuid4()))
                    session = context.get_session(data['id'])
                    if len(active_sessions) == 0 or session['status'] is None:
                        restore_session_from_data(data, session)
                        session['status'] = None
                    if not context_tracker.start_session(session['id']):
                        error = "Your session is already active.<br>If it's not the case please close your browser and relaunch it."
                        return gr.update(), gr.update(), gr.update(value=''), update_gr_glassmask(str=error)
                    else:
                        active_sessions.add(req.session_hash)
                        session[req.session_hash] = req.session_hash
                        session['cancellation_requested'] = False
                    if isinstance(session['ebook'], str):
                        if not os.path.exists(session['ebook']):
                            session['ebook'] = None
                    if session['voice'] is not None:
                        if not os.path.exists(session['voice']):
                            session['voice'] = None
                    if session['custom_model'] is not None:
                        if not os.path.exists(session['custom_model_dir']):
                            session['custom_model'] = None 
                    if session['fine_tuned'] is not None:
                        if session['tts_engine'] is not None:
                            if session['tts_engine'] in models.keys():
                                if session['fine_tuned'] not in models[session['tts_engine']].keys():
                                    session['fine_tuned'] = default_fine_tuned
                            else:
                                session['tts_engine'] = default_tts_engine
                                session['fine_tuned'] = default_fine_tuned
                    if session['audiobook'] is not None:
                        if not os.path.exists(session['audiobook']):
                            session['audiobook'] = None
                    if session['status'] == 'converting':
                        session['status'] = 'ready'
                    session['is_gui_process'] = is_gui_process
                    session['system'] = (f"{platform.system()}-{platform.release()}").lower()
                    session['session_dir'] = os.path.join(tmp_dir, f"proc-{session['id']}")
                    session['custom_model_dir'] = os.path.join(models_dir, '__sessions', f"model-{session['id']}")
                    session['voice_dir'] = os.path.join(voices_dir, '__sessions', f"voice-{session['id']}", session['language'])
                    os.makedirs(session['custom_model_dir'], exist_ok=True)
                    os.makedirs(session['voice_dir'], exist_ok=True)
                    # As now uploaded voice files are in their respective language folder so check if no wav and bark folder are on the voice_dir root from previous versions
                    #[shutil.move(src, os.path.join(session['voice_dir'], os.path.basename(src))) for src in glob(os.path.join(os.path.dirname(session['voice_dir']), '*.wav')) + ([os.path.join(os.path.dirname(session['voice_dir']), 'bark')] if os.path.isdir(os.path.join(os.path.dirname(session['voice_dir']), 'bark')) and not os.path.exists(os.path.join(session['voice_dir'], 'bark')) else [])]                
                    if is_gui_shared:
                        msg = f' Note: access limit time: {interface_shared_tmp_expire} days'
                        session['audiobooks_dir'] = os.path.join(audiobooks_gradio_dir, f"web-{session['id']}")
                        delete_unused_tmp_dirs(audiobooks_gradio_dir, interface_shared_tmp_expire, session['id'])
                    else:
                        msg = f' Note: if no activity is detected after {tmp_expire} days, your session will be cleaned up.'
                        session['audiobooks_dir'] = os.path.join(audiobooks_host_dir, f"web-{session['id']}")
                        delete_unused_tmp_dirs(audiobooks_host_dir, tmp_expire, session['id'])
                    if not os.path.exists(session['audiobooks_dir']):
                        os.makedirs(session['audiobooks_dir'], exist_ok=True)
                    previous_hash = state['hash']
                    new_hash = hash_proxy_dict(MappingProxyType(session))
                    state['hash'] = new_hash
                    show_alert({"type": "info", "msg": msg})
                    return gr.update(value=json.dumps(session, cls=JSONDictProxyEncoder)), gr.update(value=state), gr.update(value=session['id']), update_gr_glassmask(attr=['gr-glass-mask', 'hide'])
                except Exception as e:
                    error = f'change_gr_restore_session(): {e}'
                    alert_exception(error, None)
                    return gr.update(), gr.update(), gr.update(), gr.update()

            async def inner_update_gr_save_session(id:str, state:dict)->tuple:
                try:
                    if id and id in context.sessions:
                        session = context.get_session(id)
                        if session:
                            previous_hash = state.get("hash")
                            if session.get("status") == "converting":
                                try:
                                    if session.get("progress") != len(audiobook_options):
                                        session["progress"] = len(audiobook_options)
                                        new_hash = hash_proxy_dict(MappingProxyType(session))
                                        state["hash"] = new_hash
                                        session_dict = json.dumps(
                                            session, cls=JSONDictProxyEncoder
                                        )
                                        yield (
                                            gr.update(value=session_dict),
                                            gr.update(value=state),
                                            update_gr_audiobook_list(id),
                                        )
                                    else:
                                        yield gr.update(), gr.update(), gr.update()
                                except NameError:
                                    new_hash = hash_proxy_dict(MappingProxyType(session))
                                    state["hash"] = new_hash
                                    session_dict = json.dumps(
                                        session, cls=JSONDictProxyEncoder
                                    )
                                    yield (
                                        gr.update(value=session_dict),
                                        gr.update(value=state),
                                        gr.update(),
                                    )
                            else:
                                new_hash = hash_proxy_dict(MappingProxyType(session))
                                if previous_hash == new_hash:
                                    yield gr.update(), gr.update(), gr.update()
                                else:
                                    state["hash"] = new_hash
                                    session_dict = json.dumps(session, cls=JSONDictProxyEncoder)
                                    yield (
                                        gr.update(value=session_dict),
                                        gr.update(value=state),
                                        gr.update(),
                                    )
                    yield gr.update(), gr.update(), gr.update()
                except Exception as e:
                    error = f'update_gr_save_session(): {e}!'
                    alert_exception(error, id)
                    yield gr.update(), gr.update(value=e), gr.update()
            
            def clear_event(id:str)->None:
                if id:
                    session = context.get_session(id)
                    if session['event'] is not None:
                        session['event'] = None

            gr_ebook_file.change(
                fn=change_convert_btn,
                inputs=[gr_ebook_file, gr_ebook_mode, gr_custom_model_file, gr_session],
                outputs=[gr_convert_btn]
            ).then(
                fn=change_gr_ebook_file,
                inputs=[gr_ebook_file, gr_session],
                outputs=[gr_modal]
            )
            gr_ebook_mode.change(
                fn=change_gr_ebook_mode,
                inputs=[gr_ebook_mode, gr_session],
                outputs=[gr_ebook_file, gr_chapters_preview]
            )
            
            gr_force_ocr.change(
                fn=change_gr_force_ocr,
                inputs=[gr_force_ocr, gr_session],
                outputs=None
            ).then(
                fn=reprocess_ebook,
                inputs=[gr_session],
                outputs=[gr_ebook_file, gr_modal]
            )
            gr_chapters_preview.click(
                fn=lambda val, id: change_param('chapters_preview', bool(val), id),
                inputs=[gr_chapters_preview, gr_session],
                outputs=None
            )
            # Translation button click event - DISABLED: components not yet defined
            # gr_translate_btn.click(
            #     fn=show_translation_overlay,
            #     inputs=[gr_session],
            #     outputs=[gr_translation_overlay]
            # )
            # # Translation trigger - fires when service textbox value changes (set by JS)
            # gr_translation_service.change(
            #     fn=execute_translation,
            #     inputs=[gr_translation_target_lang, gr_translation_service, gr_session],
            #     outputs=[gr_translation_overlay, gr_modal]
            # )
            # # Also trigger when the button is clicked directly
            # gr_translation_trigger.click(
            #     fn=execute_translation,
            #     inputs=[gr_translation_target_lang, gr_translation_service, gr_session],
            #     outputs=[gr_translation_overlay, gr_modal]
            # )
            gr_voice_file.upload(
                fn=change_gr_voice_file,
                inputs=[gr_voice_file, gr_session],
                outputs=[gr_voice_list]
            ).then(
                fn=lambda: gr.update(value=None),
                inputs=None,
                outputs=[gr_voice_file]
            )
            gr_voice_list.change(
                fn=change_gr_voice_list,
                inputs=[gr_voice_list, gr_session],
                outputs=[gr_voice_player_hidden, gr_voice_play, gr_voice_del_btn]
            )
            # Play button click - trigger the hidden audio player
            gr_voice_play.click(
                fn=None,
                inputs=None,
                outputs=None,
                js="()=>{var a=document.querySelector('#gr_voice_player_hidden audio');if(a){a.currentTime=0;a.play();}}"
            )
            gr_voice_del_btn.click(
                fn=click_gr_voice_del_btn,
                inputs=[gr_voice_list, gr_session],
                outputs=[gr_confirm_deletion_field_hidden, gr_modal]
            )
            gr_device.change(
                fn=change_gr_device,
                inputs=[gr_device, gr_session],
                outputs=None
            )
            gr_language.change(
                fn=change_gr_language,
                inputs=[gr_language, gr_session],
                outputs=[gr_language, gr_tts_engine_list, gr_custom_model_list, gr_fine_tuned_list, gr_voice_list]
            )
            gr_tts_engine_list.change(
                fn=change_gr_tts_engine_list,
                inputs=[gr_tts_engine_list, gr_session],
                outputs=[gr_tts_rating, gr_tab_xtts_params, gr_tab_bark_params, gr_tab_supertonic_params, gr_group_custom_model, gr_fine_tuned_list, gr_custom_model_file, gr_voice_list, gr_custom_model_label]
            )
            gr_fine_tuned_list.change(
                fn=change_gr_fine_tuned_list,
                inputs=[gr_fine_tuned_list, gr_session],
                outputs=[gr_group_custom_model, gr_voice_list]
            )
            gr_custom_model_file.upload(
                fn=change_gr_custom_model_file,
                inputs=[gr_custom_model_file, gr_tts_engine_list, gr_session],
                outputs=[gr_custom_model_file, gr_custom_model_list, gr_voice_list],
                show_progress_on=[gr_custom_model_list]
            )
            gr_custom_model_list.change(
                fn=change_gr_custom_model_list,
                inputs=[gr_custom_model_list, gr_session],
                outputs=[gr_fine_tuned_list, gr_custom_model_del_btn, gr_voice_list]
            )
            gr_custom_model_del_btn.click(
                fn=click_gr_custom_model_del_btn,
                inputs=[gr_custom_model_list, gr_session],
                outputs=[gr_confirm_deletion_field_hidden, gr_modal]
            )
            gr_output_format_list.change(
                fn=change_gr_output_format_list,
                inputs=[gr_output_format_list, gr_session],
                outputs=None
            )
            gr_output_channel_list.change(
                fn=change_gr_output_channel_list,
                inputs=[gr_output_channel_list, gr_session],
                outputs=None
            )
            gr_output_split.select(
                fn=change_gr_output_split,
                inputs=[gr_output_split, gr_session],
                outputs=[gr_row_output_split_hours]
            )
            gr_output_split_hours.change(
                fn=lambda val, id: change_param('output_split_hours', str(val), id),
                inputs=[gr_output_split_hours, gr_session],
                outputs=None
            )
            gr_progress.change(
                fn=None,
                inputs=[gr_progress],
                js=r'(filename)=>{const gr_root=(window.gradioApp&&window.gradioApp())||document;const gr_ebook_file=gr_root.querySelector("#gr_ebook_file");if(!gr_ebook_file){return;}function normalizeForGradio(name){return name.normalize("NFC").replace(/[<>:"/\\|?*\x00-\x1F]/g,"").replace(/[!(){}\[\]\u0027]/g,"").replace(/\s+\./g,".").replace(/[. ]+$/,"").replace(/[\u0640\u0651\u064B-\u065F]/g,"").trim();}const rows=gr_ebook_file.querySelectorAll("table.file-preview tr.file");rows.forEach((row,idx)=>{const filenameCell=row.querySelector("td.filename");if(filenameCell){const rowName=normalizeForGradio(filenameCell.getAttribute("aria-label"));filename=filename.split("/")[0].trim();if(rowName===filename){row.style.display="none";}}});}'
            )
            gr_playback_time.change(
                fn=change_gr_playback_time,
                inputs=[gr_playback_time, gr_session],
                js='(time)=>{try{if(!window.session_storage){window.session_storage={};}window.session_storage.playback_time=Number(time);}catch(e){console.warn("gr_playback_time.change error: "+e);}}'
            )
            gr_audiobook_download_btn.click(
                fn=toggle_audiobook_files,
                inputs=[gr_audiobook_list, gr_audiobook_files_toggled],
                outputs=[gr_audiobook_files, gr_audiobook_files_toggled],
                show_progress="minimal",
            )
            gr_audiobook_list.change(
                fn=change_gr_audiobook_list,
                inputs=[gr_audiobook_list, gr_session],
                outputs=[gr_group_audiobook_list]
            ).then(
                fn=update_gr_audiobook_player,
                inputs=[gr_session],
                outputs=[gr_playback_time, gr_audiobook_player, gr_audiobook_vtt]
            ).then(
                fn=None,
                inputs=None,
                js='()=>{window.load_vtt();}'
            )
            gr_audiobook_del_btn.click(
                fn=click_gr_audiobook_del_btn,
                inputs=[gr_audiobook_list, gr_session],
                outputs=[gr_confirm_deletion_field_hidden, gr_modal]
            )
            ########### XTTSv2 Params
            gr_tab_xtts_params.select(
                fn=None,
                inputs=None,
                outputs=None,
                js='()=>{if(!window._xtts_sliders_initialized){const checkXttsExist=setInterval(()=>{const slider=document.querySelector("#gr_xtts_speed input[type=range]");if(slider){clearInterval(checkXttsExist);window._xtts_sliders_initialized=true;init_xtts_sliders();}},500);}}'
            )
            gr_xtts_temperature.change(
                fn=lambda val, id: change_param('xtts_temperature', float(val), id),
                inputs=[gr_xtts_temperature, gr_session],
                outputs=None
            )
            gr_xtts_length_penalty.change(
                fn=lambda val, id, val2: change_param('xtts_length_penalty', int(val), id, int(val2)),
                inputs=[gr_xtts_length_penalty, gr_session, gr_xtts_num_beams],
                outputs=None,
            )
            gr_xtts_num_beams.change(
                fn=lambda val, id, val2: change_param('xtts_num_beams', int(val), id, int(val2)),
                inputs=[gr_xtts_num_beams, gr_session, gr_xtts_length_penalty],
                outputs=None,
            )
            gr_xtts_repetition_penalty.change(
                fn=lambda val, id: change_param('xtts_repetition_penalty', float(val), id),
                inputs=[gr_xtts_repetition_penalty, gr_session],
                outputs=None
            )
            gr_xtts_top_k.change(
                fn=lambda val, id: change_param('xtts_top_k', int(val), id),
                inputs=[gr_xtts_top_k, gr_session],
                outputs=None
            )
            gr_xtts_top_p.change(
                fn=lambda val, id: change_param('xtts_top_p', float(val), id),
                inputs=[gr_xtts_top_p, gr_session],
                outputs=None
            )
            gr_xtts_speed.change(
                fn=lambda val, id: change_param('xtts_speed', float(val), id),
                inputs=[gr_xtts_speed, gr_session],
                outputs=None
            )
            gr_xtts_enable_text_splitting.select(
                fn=lambda val, id: change_param('xtts_enable_text_splitting', bool(val), id),
                inputs=[gr_xtts_enable_text_splitting, gr_session],
                outputs=None
            )
            ########### BARK Params
            gr_tab_bark_params.select(
                fn=None,
                inputs=None,
                outputs=None,
                js='()=>{if(!window._bark_sliders_initialized){const checkBarkExist=setInterval(()=>{const slider=document.querySelector("#gr_bark_waveform_temp input[type=range]");if(slider){clearInterval(checkBarkExist);window._bark_sliders_initialized=true;init_bark_sliders();}},500);}}'
            )
            gr_bark_text_temp.change(
                fn=lambda val, id: change_param('bark_text_temp', float(val), id),
                inputs=[gr_bark_text_temp, gr_session],
                outputs=None
            )
            gr_bark_waveform_temp.change(
                fn=lambda val, id: change_param('bark_waveform_temp', float(val), id),
                inputs=[gr_bark_waveform_temp, gr_session],
                outputs=None
            )

            ########### SUPERTONIC Params
            gr_tab_supertonic_params.select(
                fn=None,
                inputs=None,
                outputs=None,
                js='()=>{if(!window._supertonic_sliders_initialized){const checkSupertonicExist=setInterval(()=>{const slider=document.querySelector("#gr_supertonic_speed input[type=range]");if(slider){clearInterval(checkSupertonicExist);window._supertonic_sliders_initialized=true;init_supertonic_sliders();}},500);}}'
            )
            gr_supertonic_speed.change(
                fn=lambda val, id: change_param('supertonic_speed', float(val), id),
                inputs=[gr_supertonic_speed, gr_session],
                outputs=None
            )
            gr_supertonic_total_step.change(
                fn=lambda val, id: change_param('supertonic_total_step', int(val), id),
                inputs=[gr_supertonic_total_step, gr_session],
                outputs=None
            )
            ############ Timer to save session to localStorage
            gr_timer = gr.Timer(9, active=False)
            gr_timer.tick(
                fn=inner_update_gr_save_session,
                inputs=[gr_session, gr_state_update],
                outputs=[gr_save_session, gr_state_update, gr_audiobook_list]
            ).then(
                fn=clear_event,
                inputs=[gr_session],
                outputs=None
            )
            gr_convert_btn.click(
                fn=change_convert_btn,
                inputs=None,
                outputs=[gr_convert_btn]
            ).then(
                fn=disable_components,
                inputs=None,
                outputs=[gr_ebook_mode, gr_chapters_preview, gr_language, gr_voice_file, gr_voice_list, gr_device, gr_tts_engine_list, gr_fine_tuned_list, gr_custom_model_file, gr_custom_model_list, gr_output_format_list, gr_output_channel_list]
            ).then(
                fn=submit_convert_btn,
                inputs=[
                    gr_session, gr_device, gr_ebook_file, gr_chapters_preview, gr_tts_engine_list, gr_language, gr_voice_list,
                    gr_custom_model_list, gr_fine_tuned_list, gr_output_format_list, gr_output_channel_list,
                    gr_xtts_temperature, gr_xtts_length_penalty, gr_xtts_num_beams, gr_xtts_repetition_penalty, gr_xtts_top_k, gr_xtts_top_p, gr_xtts_speed, gr_xtts_enable_text_splitting,
                    gr_bark_text_temp, gr_bark_waveform_temp, gr_supertonic_speed, gr_supertonic_total_step,
                    gr_output_split, gr_output_split_hours
                ],
                outputs=[gr_progress, gr_modal]
            ).then(
                fn=enable_components,
                inputs=[gr_session],
                outputs=[gr_ebook_mode, gr_chapters_preview, gr_language, gr_voice_file, gr_voice_list, gr_device, gr_tts_engine_list, gr_fine_tuned_list, gr_custom_model_file, gr_custom_model_list, gr_output_format_list, gr_output_channel_list]
            ).then(
                fn=refresh_interface,
                inputs=[gr_session],
                outputs=[gr_convert_btn, gr_ebook_file, gr_device, gr_audiobook_list, gr_audiobook_player, gr_modal, gr_voice_list, gr_progress]
            )
            gr_save_session.change(
                fn=None,
                inputs=[gr_save_session],
                js='(data)=>{try{if(data){localStorage.clear();if(window.session_storage){data.playback_time=Number(window.session_storage.playback_time||0);data.playback_volume=parseFloat(window.session_storage.playback_volume||1);}localStorage.setItem("data",JSON.stringify(data));}}catch(e){console.warn("gr_save_session.change error: "+e);}}'
            )       
            gr_restore_session.change(
                fn=change_gr_restore_session,
                inputs=[gr_restore_session, gr_state_update],
                outputs=[gr_save_session, gr_state_update, gr_session, gr_glassmask]
            ).then(
                fn=restore_interface,
                inputs=[gr_session],
                outputs=[
                    gr_ebook_file, gr_ebook_mode, gr_chapters_preview, gr_device, gr_language, gr_voice_list,
                    gr_tts_engine_list, gr_custom_model_list, gr_fine_tuned_list, gr_output_format_list, gr_output_channel_list,
                    gr_output_split, gr_output_split_hours, gr_row_output_split_hours, gr_audiobook_list
                ]
            ).then(
                fn=restore_audiobook_player,
                inputs=[gr_audiobook_list],
                outputs=[
                    gr_group_audiobook_list, gr_audiobook_player, gr_timer
                ]
            )
            gr_confirm_blocks_no_btn.click(
                fn=lambda session: confirm_blocks("no", session),
                inputs=[gr_session],
                outputs=[gr_modal]
            ).then(
                fn=change_convert_btn,
                inputs=[gr_ebook_file, gr_ebook_mode, gr_custom_model_file, gr_session],
                outputs=[gr_convert_btn]
            ).then(
                fn=enable_components,
                inputs=[gr_session],
                outputs=[gr_ebook_mode, gr_chapters_preview, gr_language, gr_voice_file, gr_voice_list, gr_device, gr_tts_engine_list, gr_fine_tuned_list, gr_custom_model_file, gr_custom_model_list, gr_output_format_list, gr_output_channel_list]
            )


            # Note: Chapter Editor functions (show_chapter_editor_overlay, save_chapters_from_overlay)
            # are defined later in this file with full translation support.
            # The gr_chapters_preview.click handler is also defined later (after function definitions).

            # Chapter Editor Functions - Native Rewrite
            def show_chapter_editor_overlay(id_or_session:str|dict):
                print(f"[DEBUG] show_chapter_editor_overlay CALLED")
                try:
                    if isinstance(id_or_session, dict):
                        session = id_or_session
                    else:
                        session = context.get_session(str(id_or_session))
                    
                    if not session or 'chapters' not in session or not session['chapters']:
                         return gr.update(value=[], visible=False), gr.update(visible=False), gr.update(visible=False)
                    
                    chapters = session['chapters']
                    # Format for Dataframe: List of Lists [[content], [content]]
                    # chapters is [[seg1, seg2, ...]] - a list containing one list of segments
                    data = []
                    for chapter in chapters:
                        if isinstance(chapter, str):
                            data.append([chapter])
                        elif isinstance(chapter, list):
                            # Iterate over all segments in the chapter list
                            for segment in chapter:
                                if segment and isinstance(segment, str):
                                    data.append([segment])
                                elif segment:
                                    data.append([str(segment)])
                        elif isinstance(chapter, dict):
                            data.append([chapter.get('content', str(chapter))])
                        else:
                            data.append([str(chapter)])
                            
                    print(f"[DEBUG] Populating Dataframe with {len(data)} rows")
                    
                    # Show Group, Update Dataframe, Show Glassmask
                    return gr.update(value=data, visible=True), gr.update(visible=True), gr.update(visible=True)
                except Exception as e:
                    print(f"[DEBUG] Error in show_chapter_editor_overlay: {e}")
                    import traceback
                    traceback.print_exc()
                    return gr.update(value=[], visible=False), gr.update(visible=False), gr.update(visible=False)

            def save_chapters_from_overlay(dataframe_data, target_lang, id_or_session:str|dict):
                print(f"[DEBUG] save_chapters_from_overlay CALLED with target_lang={target_lang}")
                try:
                    if isinstance(id_or_session, dict):
                        id = id_or_session.get('id')
                    else:
                        id = str(id_or_session)
                        
                    # basic dataframe data is a pandas dataframe or list of lists
                    new_chapters = []
                    try:
                        import pandas as pd
                        if isinstance(dataframe_data, pd.DataFrame):
                            new_chapters = dataframe_data.iloc[:, 0].tolist()
                        else:
                            new_chapters = [row[0] for row in dataframe_data if row]
                    except ImportError:
                        new_chapters = [row[0] for row in dataframe_data if row]
                        
                    # Filter out empty strings
                    new_chapters = [str(c) for c in new_chapters if str(c).strip()]
                    
                    print(f"[DEBUG] Saving {len(new_chapters)} chapters")
                    update_session_chapters(id, new_chapters)
                    
                    if target_lang:
                        print(f"Chapter Editor: Triggering translation to {target_lang}")
                        session = context.get_session(id)
                        
                        # Save current chapters to a temporary file for translation
                        temp_input_path = os.path.join(session['session_dir'], 'edited_chapters_for_translation.txt')
                        with open(temp_input_path, 'w', encoding='utf-8') as f:
                            for chap in new_chapters:
                                f.write(str(chap) + '\n\n')
                        
                        # Update session to use this file as input
                        session['ebook'] = temp_input_path
                        session['txt_file'] = temp_input_path
                        
                        from lib.classes.translator import translate_document
                        # Default to google for now
                        success, translated_path, error = translate_document(session, target_lang, 'google')
                        
                        if success:
                             print(f"Chapter Editor: Translation successful to {translated_path}")
                             
                             # CRITICAL: Update ebook_list so convert_ebook uses the translated file
                             session['ebook_list'] = [translated_path]
                             print(f"[DEBUG] Updated session['ebook_list'] to use translated file: {translated_path}")

                             # Clear previous audio progress to prevent stale resume logic
                             try:
                                 if session.get('chapters_dir') and os.path.exists(session['chapters_dir']):
                                     shutil.rmtree(session['chapters_dir'])
                                     print(f"Cleared chapters_dir: {session['chapters_dir']}")
                                 os.makedirs(session['chapters_dir'], exist_ok=True)
                                 
                                 if session.get('chapters_dir_sentences') and os.path.exists(session['chapters_dir_sentences']):
                                     shutil.rmtree(session['chapters_dir_sentences'])
                                     print(f"Cleared chapters_dir_sentences: {session['chapters_dir_sentences']}")
                                 os.makedirs(session['chapters_dir_sentences'], exist_ok=True)
                                 
                             except Exception as e:
                                 print(f"Error clearing audio cache: {e}")

                             show_alert({"type": "success", "msg": f"✅ Text saved and translated to {target_lang}!"})
                        else:
                             print(f"Chapter Editor: Translation failed: {error}")
                             show_alert({"type": "error", "msg": f"❌ Translation failed: {error}"})
                    else:
                        show_alert({"type": "success", "msg": "✅ Chapters saved successfully!"})
                    
                    # Hide Group, Hide Glassmask
                    return gr.update(visible=False), gr.update(visible=False)
                except Exception as e:
                    print(f"Error saving chapters: {e}")
                    import traceback
                    traceback.print_exc()
                    return gr.update(visible=False), gr.update(visible=False)

            def cancel_chapter_editor():
                 return gr.update(visible=False), gr.update(visible=False)

            def translate_chapters_in_place(dataframe_data, target_lang, id_or_session:str|dict):
                """Translate chapters in-place and update the dataframe without closing overlay."""
                print(f"[DEBUG] translate_chapters_in_place CALLED with target_lang={target_lang}")
                try:
                    if not target_lang:
                        show_alert({"type": "warning", "msg": "⚠️ Please select a translation target language first."})
                        return gr.update()
                    
                    if isinstance(id_or_session, dict):
                        id = id_or_session.get('id')
                    else:
                        id = str(id_or_session)
                        
                    # Extract text from dataframe
                    new_chapters = []
                    try:
                        import pandas as pd
                        if isinstance(dataframe_data, pd.DataFrame):
                            new_chapters = dataframe_data.iloc[:, 0].tolist()
                        else:
                            new_chapters = [row[0] for row in dataframe_data if row]
                    except ImportError:
                        new_chapters = [row[0] for row in dataframe_data if row]
                        
                    # Filter out empty strings
                    new_chapters = [str(c) for c in new_chapters if str(c).strip()]
                    
                    if not new_chapters:
                        show_alert({"type": "warning", "msg": "⚠️ No text to translate."})
                        return gr.update()
                    
                    print(f"[DEBUG] Translating {len(new_chapters)} segments to {target_lang}")
                    show_alert({"type": "info", "msg": f"🔄 Translating {len(new_chapters)} segments to {target_lang}..."})
                    
                    # Import translator
                    from lib.classes.translator import TranslationService
                    translator = TranslationService('google')
                    
                    # Detect source language from first segment
                    source_lang = 'auto'
                    try:
                        detected_lang, _ = translator.detect_language(new_chapters[0])
                        if detected_lang:
                            source_lang = detected_lang
                            print(f"[DEBUG] Detected source language: {source_lang}")
                    except Exception as e:
                        print(f"[DEBUG] Language detection failed, using auto: {e}")
                    
                    # Translate each segment
                    translated_chapters = []
                    session_obj = id_or_session if isinstance(id_or_session, dict) else context.get_session(str(id_or_session))
                    
                    for i, segment in enumerate(new_chapters):
                        if session_obj and session_obj.get("cancellation_requested"):
                            print(f"[DEBUG] Translation cancelled at segment {i}")
                            show_alert({"type": "info", "msg": "🛑 Translation cancelled."})
                            # Append remaining as original
                            translated_chapters.extend(new_chapters[i:])
                            break
                            
                        try:
                            success, translated_text, error = translator.translate(segment, source_lang, target_lang)
                            if success:
                                translated_chapters.append(translated_text)
                            else:
                                print(f"Translation failed for segment {i}: {error}")
                                translated_chapters.append(segment)  # Keep original on failure
                        except Exception as e:
                            print(f"Translation error for segment {i}: {e}")
                            translated_chapters.append(segment)
                    
                    # Format for Dataframe: List of Lists [[content], [content]]
                    data = [[seg] for seg in translated_chapters]
                    
                    print(f"[DEBUG] Translation complete, returning {len(data)} translated rows")
                    show_alert({"type": "success", "msg": f"✅ Translated {len(translated_chapters)} segments to {target_lang}!"})
                    
                    return gr.update(value=data)
                except Exception as e:
                    print(f"Error translating chapters: {e}")
                    import traceback
                    traceback.print_exc()
                    show_alert({"type": "error", "msg": f"❌ Translation error: {str(e)}"})
                    return gr.update()

            def request_cancellation(id_or_session):
                print(f"[DEBUG] Cancellation requested")
                if isinstance(id_or_session, dict):
                    session = id_or_session
                else:
                    session = context.get_session(str(id_or_session))
                
                if session:
                    session["cancellation_requested"] = True
                    show_alert({"type": "info", "msg": "🛑 Job cancellation requested..."})
                    print(f"[DEBUG] Session cancellation_requested set to True")
                return gr.update()

            # Event Handlers - Native Rewrite
            gr_chapters_preview.click(
                fn=show_chapter_editor_overlay,
                inputs=[gr_session],
                outputs=[gr_chapter_dataframe, gr_chapter_editor_group, gr_glassmask]
            )
            
            # Hidden button for JS to click (must be visible=True to be in DOM, hidden via CSS)
            gr_cancel_job_btn = gr.Button(elem_id="gr_cancel_job_btn", visible=True)
            gr_cancel_job_btn.click(
                fn=request_cancellation,
                inputs=[gr_session],
                outputs=None
            )
            
            # Wire Main Cancel Button
            gr_main_cancel_btn.click(
                fn=request_cancellation,
                inputs=[gr_session],
                outputs=None
            )
            
            gr_chapter_translate_btn.click(
                fn=translate_chapters_in_place,
                inputs=[gr_chapter_dataframe, gr_chapter_trans_lang, gr_session],
                outputs=[gr_chapter_dataframe]
            )
            
            gr_chapter_save_btn.click(
                fn=save_chapters_from_overlay,
                inputs=[gr_chapter_dataframe, gr_chapter_trans_lang, gr_session],
                outputs=[gr_chapter_editor_group, gr_glassmask]
            )
            
            gr_chapter_cancel_btn.click(
                fn=cancel_chapter_editor,
                inputs=None,
                outputs=[gr_chapter_editor_group, gr_glassmask]
            )
            gr_confirm_blocks_yes_btn.click(
                fn=lambda session: confirm_blocks("yes", session),
                inputs=[gr_session],
                outputs=[gr_modal]
            ).then(
                fn=submit_confirmed_blocks,
                inputs=[gr_session],
                outputs=[gr_progress, gr_modal]
            ).then(
                fn=enable_components,
                inputs=[gr_session],
                outputs=[gr_ebook_mode, gr_chapters_preview, gr_language, gr_voice_file, gr_voice_list, gr_device, gr_tts_engine_list, gr_fine_tuned_list, gr_custom_model_file, gr_custom_model_list, gr_output_format_list, gr_output_channel_list]
            ).then(
                fn=refresh_interface,
                inputs=[gr_session],
                outputs=[gr_convert_btn, gr_ebook_file, gr_device, gr_audiobook_list, gr_audiobook_player, gr_modal, gr_voice_list, gr_progress]
            )
            gr_confirm_blocks_no_btn.click(
                fn=lambda session: confirm_blocks("no", session),
                inputs=[gr_session],
                outputs=[gr_modal]
            ).then(
                fn=enable_components,
                inputs=[gr_session],
                outputs=[gr_ebook_mode, gr_chapters_preview, gr_language, gr_voice_file, gr_voice_list, gr_device, gr_tts_engine_list, gr_fine_tuned_list, gr_custom_model_file, gr_custom_model_list, gr_output_format_list, gr_output_channel_list]
            )

            # Confirm Deletion Event Handlers
            gr_confirm_deletion_yes_btn.click(
                fn=lambda voice, custom, audio, id, method: confirm_deletion(voice, custom, audio, id, method),
                inputs=[gr_voice_list, gr_custom_model_list, gr_audiobook_list, gr_session, gr_confirm_deletion_field_hidden],
                outputs=[gr_custom_model_list, gr_audiobook_list, gr_modal, gr_voice_list]
            )
            gr_confirm_deletion_no_btn.click(
                fn=lambda: gr.update(visible=False),
                inputs=None,
            ).then(
                fn=refresh_interface,
                inputs=[gr_session],
                outputs=[gr_convert_btn, gr_ebook_file, gr_device, gr_audiobook_list, gr_audiobook_player, gr_modal, gr_voice_list, gr_progress]
            )

            app.load(
                fn=None,
                js="() => { try { if(!window.session_storage){window.session_storage={};} return JSON.parse(localStorage.getItem('data')); } catch (e) { return null; } }",
                outputs=[gr_restore_session],
            )
            app.unload(cleanup_session)
            all_ips = get_all_ip_addresses()
            msg = f'IPs available for connection:\n{all_ips}\nNote: 0.0.0.0 is not the IP to connect. Instead use an IP above to connect and port {interface_port}'
            show_alert({"type": "info", "msg": msg})
            os.environ['no_proxy'] = ' ,'.join(all_ips)
            return app

    except Exception as e:
            print(f"build_interface Error: {e}")
            import traceback
            traceback.print_exc()
            return None
