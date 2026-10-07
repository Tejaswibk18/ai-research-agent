import json
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.config import get_settings
from app.models.document import (
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
)
from app.services.document.chunker import split_text
from app.services.document.extractor import (
    SUPPORTED_EXTENSIONS,
    extract_text,
)
from app.services.document.indexer import (
    DocumentIndexer,
)


router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)


settings = get_settings()

indexer = DocumentIndexer()


def load_documents() -> list[dict]:

    file_path = (
        settings.INDEX_DIR
        / "documents.json"
    )

    if not file_path.exists():
        file_path.write_text(
            "[]",
            encoding="utf-8",
        )

    return json.loads(
        file_path.read_text(
            encoding="utf-8"
        )
    )


def save_documents(
    documents: list[dict],
):

    file_path = (
        settings.INDEX_DIR
        / "documents.json"
    )

    file_path.write_text(
        json.dumps(
            documents,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required.",
        )

    extension = Path(
        file.filename
    ).suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:

        supported = ", ".join(
            sorted(SUPPORTED_EXTENSIONS)
        )

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported file type. "
                f"Supported: {supported}"
            ),
        )

    contents = await file.read()

    max_size = (
        settings.MAX_UPLOAD_SIZE_MB
        * 1024
        * 1024
    )

    if len(contents) > max_size:

        raise HTTPException(
            status_code=413,
            detail=(
                f"File exceeds the "
                f"{settings.MAX_UPLOAD_SIZE_MB} MB limit."
            ),
        )

    document_id = str(uuid.uuid4())

    safe_filename = (
        f"{document_id}{extension}"
    )

    file_path = (
        settings.UPLOAD_DIR
        / safe_filename
    )

    settings.UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_bytes(contents)

    try:

        text = extract_text(file_path)

        chunks = split_text(
            text,
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
        )

        indexing_result = (
            await indexer.index_document(
                document_id=document_id,
                filename=file.filename,
                chunks=chunks,
            )
        )

        document = DocumentMetadata(
            document_id=document_id,
            filename=file.filename,
            content_type=(
                file.content_type
                or "application/octet-stream"
            ),
            size_bytes=len(contents),
            character_count=len(text),
            chunk_count=len(chunks),
            created_at=datetime.now(
                timezone.utc
            ),
        )

        documents = load_documents()

        documents.append(
            document.model_dump(
                mode="json"
            )
        )

        save_documents(documents)

        return DocumentUploadResponse(
            message=(
                "Document processed and indexed successfully."
            ),
            document=document,
        )

    except Exception as exc:

        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Failed to process document: {str(exc)}"
            ),
        )


@router.get(
    "",
    response_model=DocumentListResponse,
)
async def list_documents():

    documents = load_documents()

    return DocumentListResponse(
        documents=documents
    )


@router.delete(
    "/{document_id}",
)
async def delete_document(
    document_id: str,
):

    documents = load_documents()

    target = None

    for document in documents:

        if document["document_id"] == document_id:
            target = document
            break

    if target is None:

        raise HTTPException(
            status_code=404,
            detail="Document not found.",
        )

    documents = [
        document
        for document in documents
        if document["document_id"] != document_id
    ]

    save_documents(documents)

    removed_chunks = (
        indexer.remove_document(
            document_id
        )
    )

    extension = Path(
        target["filename"]
    ).suffix.lower()

    stored_file = (
        settings.UPLOAD_DIR
        / f"{document_id}{extension}"
    )

    if stored_file.exists():
        stored_file.unlink()

    return {
        "message": "Document deleted successfully.",
        "document_id": document_id,
        "chunks_removed": removed_chunks,
    }