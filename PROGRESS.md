# Project Progress

## Completed
- [x] **Chapter Editor Overlay**: Implemented a new "Chapter Editor" view in the Gradio interface, allowing users to modify chapters before conversion.
    - Integrated `chapter_editor.html` into the main application.
    - Added `update_session_chapters` logic to `lib/functions.py`.
    - Updated `convert_ebook` to respect user-edited chapters.
- [x] **Build Script Fixes**: Resolved critical syntax errors and logic issues in `ebook2audiobook.cmd` and `ebook2audiobook.sh`.
    - Fixed `else was unexpected` syntax errors in batch script.
    - Corrected argument parsing for empty values in shell script.
    - Ensured correct virtual environment activation.
- [x] **Docker Build Order**: Optimized `Dockerfile` to ensure build tools are available during dependency installation.
- [x] **Documentation**: Restored `ROADMAP.md` and `PROGRESS.md` to track project status.
- [x] **Job Cancellation**: Implemented robust cancellation for both TTS and OCR processes, including UI controls.
- [x] **Force OCR**: Added manual override for OCR with progress monitoring for difficult PDFs.
- [x] **AMD ROCm Support**: Enabled ROCm 6.1 support in Docker for AMD GPU acceleration.

## In Progress
- [ ] **Docker Image Build**: Currently building the Docker image. The process is downloading large dependencies (UniDic, PyTorch) and compiling packages.
- [ ] **Verification**: Once the Docker image is built, full system verification will be performed.

## Pending
- [ ] **GPU Detection**: Further testing and refinement of GPU detection logic within the Docker container.
- [ ] **Release**: Preparing the verified Docker image for release/tagging.
