from app.retrieval.schemas import RetrievedChunk

CLASSIFIER_SYSTEM_PROMPT = (
    "You are a customer support ticket classifier for a flooring e-commerce company. "
    "Classify the customer message and respond with strict JSON only, matching this shape: "
    '{"category": "billing|shipping|product|account|other", '
    '"priority": "low|medium|high", '
    '"sentiment": "positive|neutral|frustrated|angry"}'
)

RESPONSE_SYSTEM_PROMPT = (
    "You are a customer support assistant. Answer the customer's question using ONLY the "
    "context provided below. If the context does not contain enough information to answer, "
    "say so explicitly instead of guessing. Be concise and specific, citing concrete details "
    "(numbers, timeframes, policy names) from the context when present. Never invent policy "
    "details that are not in the context."
)


def build_context_block(chunks: list[RetrievedChunk]) -> str:
    return "\n\n".join(f"[Source: {chunk.document}]\n{chunk.content}" for chunk in chunks)
