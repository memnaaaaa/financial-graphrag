"""Cap the GPU memory of the vLLM embedding model that gfmrag starts (Qwen3-Embedding-0.6B).

gfmrag's Qwen3TextEmbModel calls vllm.LLM(...) with no memory settings, so vLLM reserves 90% of
the GPU and sizes its KV cache for ~110k tokens. On a T4 (no FlashAttention 2) vLLM uses
FlexAttention, which builds a block mask of (batch tokens x KV cache tokens) on every step; with
90% already reserved that mask does not fit and embedding the graph fails with CUDA OOM.

A smaller KV cache makes the mask small and leaves the rest of the GPU for G-reasoner. Our texts
are a few hundred tokens, so a 8k context is plenty. Override with the environment variables
GFM_VLLM_GPU_UTIL and GFM_VLLM_MAX_LEN.

Call limit_vllm_memory() before anything creates the embedding model.
"""
import os


def limit_vllm_memory(gpu_util: float = 0.35, max_model_len: int = 8192) -> None:
    from gfmrag.text_emb_models import qwen3_model

    if getattr(qwen3_model.LLM, "_limited", False):
        return
    gpu_util = float(os.environ.get("GFM_VLLM_GPU_UTIL", gpu_util))
    max_model_len = int(os.environ.get("GFM_VLLM_MAX_LEN", max_model_len))
    original = qwen3_model.LLM

    def limited_llm(*args, **kwargs):
        kwargs.setdefault("gpu_memory_utilization", gpu_util)
        kwargs.setdefault("max_model_len", max_model_len)
        return original(*args, **kwargs)

    limited_llm._limited = True
    qwen3_model.LLM = limited_llm  # Qwen3TextEmbModel looks LLM up in its own module
    print(f"vLLM limited to gpu_memory_utilization={gpu_util}, max_model_len={max_model_len}")
