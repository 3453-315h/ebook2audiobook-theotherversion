ARG BASE=python:3.12-slim
FROM ${BASE}

ARG DOCKER_DEVICE_STR
ARG DOCKER_PROGRAMS_STR
ARG CALIBRE_INSTALLER_URL="https://download.calibre-ebook.com/linux-installer.sh"
ARG ISO3_LANG

ENV DEBIAN_FRONTEND=noninteractive
ENV PATH="/root/.local/bin:$PATH"
ENV CALIBRE_DISABLE_CHECKS=1
ENV CALIBRE_DISABLE_GUI=1

# Performance optimization environment variables
ENV PYTORCH_ENABLE_MPS_FALLBACK=1
ENV PYTORCH_NO_CUDA_MEMORY_CACHING=1
ENV PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:32,garbage_collection_threshold:0.6,expandable_segments:True
ENV CUDA_DEVICE_ORDER=PCI_BUS_ID
ENV CUDA_LAUNCH_BLOCKING=1
ENV CUDA_CACHE_MAXSIZE=2147483648
ENV SUNO_OFFLOAD_CPU=False
ENV SUNO_USE_SMALL_MODELS=False

WORKDIR /app
COPY . /app
RUN chmod +x ebook2audiobook.sh

RUN apt-get update && \
    apt-get install -y --no-install-recommends --allow-change-held-packages \
    gcc g++ make build-essential python3-dev pkg-config cargo rustc && \
    apt-get install -y --no-install-recommends --allow-change-held-packages \
    wget xz-utils bash git \
    libegl1 libopengl0 \
    libx11-6 libglib2.0-0 libnss3 libdbus-1-3 \
    libatk1.0-0 libgdk-pixbuf-2.0-0 \
    libxcb-cursor0 \
    tesseract-ocr tesseract-ocr-$ISO3_LANG \
    $DOCKER_PROGRAMS_STR && \
    echo "Building image for Ebook2Audiobook on Linux Debian Slim" && \
    ./ebook2audiobook.sh --script_mode build_docker --docker_device "$DOCKER_DEVICE_STR" && \
    apt-get purge -y \
    gcc g++ make build-essential python3-dev pkg-config cargo rustc && \
    apt-get autoremove -y --purge && \
    wget -nv -O- "$CALIBRE_INSTALLER_URL" | sh /dev/stdin && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*



EXPOSE 7860
ENTRYPOINT ["python3", "app.py", "--script_mode", "full_docker"]