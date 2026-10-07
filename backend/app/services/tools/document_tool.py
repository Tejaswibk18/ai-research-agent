import json

from app.config import get_settings


settings = get_settings()


def _documents_path():
    return (
        settings.INDEX_DIR
        / "documents.json"
    )


def list_documents() -> dict:
    """
    List documents currently stored in the knowledge base.

    Returns:
        Document names, IDs, sizes, chunk counts,
        and creation timestamps.
    """

    path = _documents_path()

    if not path.exists():
        return {
            "documents": [],
            "count": 0,
        }

    try:
        with open(
            path,
            "r",
            encoding="utf-8"
        ) as file:
            documents = json.load(file)

        simplified = []

        for document in documents:
            simplified.append(
                {
                    "document_id": document.get(
                        "document_id"
                    ),
                    "filename": document.get(
                        "filename"
                    ),
                    "content_type": document.get(
                        "content_type"
                    ),
                    "size_bytes": document.get(
                        "size_bytes"
                    ),
                    "chunk_count": document.get(
                        "chunk_count"
                    ),
                    "created_at": document.get(
                        "created_at"
                    ),
                }
            )

        return {
            "documents": simplified,
            "count": len(simplified),
        }

    except Exception as exc:
        return {
            "documents": [],
            "count": 0,
            "error": str(exc),
        }