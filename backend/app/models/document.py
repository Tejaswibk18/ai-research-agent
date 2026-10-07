from datetime import datetime

from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    content_type: str
    size_bytes: int
    character_count: int
    chunk_count: int
    created_at: datetime


class DocumentUploadResponse(BaseModel):
    message: str
    document: DocumentMetadata


class DocumentListResponse(BaseModel):
    documents: list[DocumentMetadata]