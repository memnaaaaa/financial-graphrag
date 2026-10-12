import time

SYSTEM = (
    "You answer questions about SEC 10-K filings using ONLY the provided context passages. "
    "Be concise. If the context does not contain the information needed, reply exactly: "
    "\"I cannot answer from the provided context.\" Do not use outside knowledge."
)


def build_prompt(question: str, passages: list[tuple[str, str]]) -> str:
    ctx = "\n\n".join(f"[{cid}]\n{text}" for cid, text in passages)
    return f"Context:\n{ctx}\n\nQuestion: {question}\nAnswer:"


def answer(llm, question: str, passages) -> tuple[str, float]:
    t0 = time.perf_counter()
    out = llm.generate(build_prompt(question, passages), system=SYSTEM)
    return out, (time.perf_counter() - t0) * 1000
