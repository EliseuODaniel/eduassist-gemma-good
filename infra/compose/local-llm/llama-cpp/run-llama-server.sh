#!/usr/bin/env bash
set -euo pipefail

hf_repo="${LOCAL_LLM_HF_REPO:-${LOCAL_LLM_GEMMA4E4B_HF_REPO:-ggml-org/gemma-4-E4B-it-GGUF:Q4_K_M}}"
hf_file="${LOCAL_LLM_HF_FILE:-}"
model_path="${LOCAL_LLM_MODEL_PATH:-${LOCAL_LLM_GEMMA4E4B_MODEL_PATH:-}}"

if [[ -z "${model_path}" ]]; then
  shopt -s nullglob
  cached_models=(/root/.cache/llama.cpp/*.gguf)
  shopt -u nullglob
  if [[ ${#cached_models[@]} -gt 0 ]]; then
    model_path="${cached_models[0]}"
  fi
fi

args=(
  --host 0.0.0.0
  --port 8080
  --no-mmproj
  --ctx-size "${LOCAL_LLM_CTX_SIZE:-${LOCAL_LLM_GEMMA4E4B_CTX_SIZE:-8192}}"
  --threads "${LOCAL_LLM_THREADS:-${LOCAL_LLM_GEMMA4E4B_THREADS:-8}}"
  --parallel "${LOCAL_LLM_PARALLEL:-${LOCAL_LLM_GEMMA4E4B_PARALLEL:-1}}"
  --n-gpu-layers "${LOCAL_LLM_GPU_LAYERS:-${LOCAL_LLM_GEMMA4E4B_GPU_LAYERS:-999}}"
  --cache-type-k "${LOCAL_LLM_CACHE_TYPE_K:-${LOCAL_LLM_GEMMA4E4B_CACHE_TYPE_K:-q4_0}}"
  --cache-type-v "${LOCAL_LLM_CACHE_TYPE_V:-${LOCAL_LLM_GEMMA4E4B_CACHE_TYPE_V:-q4_0}}"
  --api-key "${LOCAL_LLM_API_KEY:-local-llm}"
  --jinja
)

if [[ -n "${model_path}" && -f "${model_path}" ]]; then
  echo "Using cached local GGUF: ${model_path}"
  exec /opt/llama.cpp/build/bin/llama-server --model "${model_path}" "${args[@]}"
fi

if [[ -n "${hf_file}" ]]; then
  echo "Using Hugging Face repo download: ${hf_repo} (file ${hf_file})"
  exec /opt/llama.cpp/build/bin/llama-server --hf-repo "${hf_repo}" --hf-file "${hf_file}" "${args[@]}"
fi

echo "Using Hugging Face repo download: ${hf_repo}"
exec /opt/llama.cpp/build/bin/llama-server --hf-repo "${hf_repo}" "${args[@]}"
