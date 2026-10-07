import numpy as np

from google.genai import types

from app.config import get_settings
from app.services.document.indexer import DocumentIndexer


settings = get_settings()


def search_knowledge_base(
    query: str,
    top_k: int = 5
) -> dict:
    """
    Search the uploaded knowledge base using semantic similarity.

    Use this tool when the user asks about information
    that may exist in their uploaded documents.

    Args:
        query: The semantic search question.
        top_k: Number of relevant chunks to retrieve.

    Returns:
        Relevant document chunks and similarity scores.
    """

    if not query.strip():
        return {
            "query": query,
            "results": [],
        }

    top_k = max(
        1,
        min(top_k, 10)
    )

    try:
        indexer = DocumentIndexer()

        results = _search_sync(
            indexer,
            query,
            top_k
        )

        return {
            "query": query,
            "results": results,
            "count": len(results),
        }

    except Exception as exc:
        return {
            "query": query,
            "results": [],
            "count": 0,
            "error": str(exc),
        }


def _search_sync(
    indexer: DocumentIndexer,
    query: str,
    top_k: int
):
    if not indexer.embeddings_path.exists():
        return []

    if not indexer.chunks_path.exists():
        return []

    embeddings = np.load(
        indexer.embeddings_path
    )

    with open(
        indexer.chunks_path,
        "r",
        encoding="utf-8"
    ) as file:
        import json

        chunks = json.load(file)

    if (
        len(embeddings) == 0
        or not chunks
    ):
        return []

    response = indexer.client.models.embed_content(
        model=indexer.settings.GEMINI_EMBEDDING_MODEL,
        contents=query,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=indexer.settings.EMBEDDING_DIMENSION,
        ),
    )

    if not response.embeddings:
        return []

    query_embedding = np.array(
        response.embeddings[0].values,
        dtype=np.float32
    )

    query_norm = np.linalg.norm(
        query_embedding
    )

    if query_norm == 0:
        return []

    query_embedding /= query_norm

    embedding_norms = np.linalg.norm(
        embeddings,
        axis=1,
        keepdims=True
    )

    embedding_norms[
        embedding_norms == 0
    ] = 1

    normalized_embeddings = (
        embeddings / embedding_norms
    )

    similarities = (
        normalized_embeddings
        @ query_embedding
    )

    ranked_indices = np.argsort(
        similarities
    )[::-1]

    results = []

    for index in ranked_indices:

        score = float(
            similarities[index]
        )

        if score < settings.RAG_SIMILARITY_THRESHOLD:
            continue

        chunk = chunks[index]

        results.append(
            {
                "document_id": chunk[
                    "document_id"
                ],
                "chunk_index": chunk[
                    "chunk_index"
                ],
                "text": chunk["text"],
                "similarity": round(
                    score,
                    4
                ),
            }
        )

        if len(results) >= top_k:
            break

    return results