from app.retrieval.store_schema import ChunkMeta

SYSTEM_PROMPT = (
    "You are a helpful assistant that answers questions based strictly on the provided document context. "
    "Only use information from the context below. If the context does not contain enough information "
    "to answer the question, say so clearly. Cite the source document names when possible. "
    "always answer in the same language as the question. "
)


def build_context(chunks: list[ChunkMeta]) -> str:
    """Format retrieved chunks into a context string for the LLM."""
    sections = []
    for c in chunks:
        sections.append(
            f"[Source: {c.document_name}, Chunk {c.chunk_index}]\n{c.text}"
        )
    return "\n\n---\n\n".join(sections)


def build_user_prompt(question: str, context: str) -> str:
    return f"Context:\n{context}\n\nQuestion: {question}"
