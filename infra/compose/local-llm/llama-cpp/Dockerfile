FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ARG LLAMA_CPP_REF=ff5ef8278615a2462b79b50abdf3cc95cfb31c6f
ARG CUDA_ARCHITECTURES=89-real

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        ca-certificates \
        cmake \
        curl \
        git \
        libcurl4-openssl-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN git clone https://github.com/ggml-org/llama.cpp /opt/llama.cpp \
    && cd /opt/llama.cpp \
    && git checkout "${LLAMA_CPP_REF}"

RUN ln -sf /usr/local/cuda/lib64/stubs/libcuda.so /usr/lib/x86_64-linux-gnu/libcuda.so.1

RUN cmake -S /opt/llama.cpp -B /opt/llama.cpp/build \
      -DGGML_CUDA=ON \
      -DLLAMA_BUILD_SERVER=ON \
      -DLLAMA_OPENSSL=ON \
      -DGGML_NATIVE=OFF \
      -DCMAKE_CUDA_ARCHITECTURES="${CUDA_ARCHITECTURES}" \
      -DCMAKE_EXE_LINKER_FLAGS="-L/usr/local/cuda/lib64/stubs" \
      -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /opt/llama.cpp/build --target llama-server -j"$(nproc)"

COPY infra/compose/local-llm/llama-cpp/run-llama-server.sh /usr/local/bin/run-llama-server.sh

WORKDIR /opt/llama.cpp

RUN chmod +x /usr/local/bin/run-llama-server.sh

ENTRYPOINT ["/usr/local/bin/run-llama-server.sh"]
