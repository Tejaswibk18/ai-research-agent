import json
from pathlib import Path

import numpy as np
from google import genai
from google.genai import types

from app.config import get_settings


class DocumentIndexer:
    def __init__(self):
        self.settings = get_settings()

        self.client = genai.Client(
            api_key=self.settings.GEMINI_API_KEY
        )

        self.index_dir = Path(self.settings.INDEX_DIR)

        self.index_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.embeddings_path = (
            self.index_dir / "embeddings.npy"
        )

        self.chunks_path = (
            self.index_dir / "chunks.json"
        )

    async def create_embedding(
        self,
        text: str,
        task_type: str
    ) -> list[float]:

        response = await self.client.aio.models.embed_content(
            model=self.settings.GEMINI_EMBEDDING_MODEL,
            contents=text,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self.settings.EMBEDDING_DIMENSION,
            ),
        )

        if not response.embeddings:
            raise RuntimeError(
                "Gemini returned no embedding."
            )

        embedding = response.embeddings[0].values

        if not embedding:
            raise RuntimeError(
                "Gemini returned an empty embedding."
            )

        return list(embedding)

    async def index_document(
        self,
        document_id: str,
        filename: str,
        chunks: list
    ):
        if not chunks:
            return

        existing_embeddings = None
        existing_chunks = []

        if self.embeddings_path.exists():
            existing_embeddings = np.load(
                self.embeddings_path
            )

        if self.chunks_path.exists():
            with open(
                self.chunks_path,
                "r",
                encoding="utf-8"
            ) as file:
                existing_chunks = json.load(file)

        new_embeddings = []

        for chunk in chunks:
            embedding = await self.create_embedding(
                chunk.text,
                "RETRIEVAL_DOCUMENT"
            )

            new_embeddings.append(embedding)

            existing_chunks.append(
                {
                    "document_id": document_id,
                    "chunk_index": chunk.index,
                    "text": chunk.text,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                }
            )

        new_embeddings = np.array(
            new_embeddings,
            dtype=np.float32
        )

        if existing_embeddings is not None:
            combined_embeddings = np.vstack(
                [
                    existing_embeddings,
                    new_embeddings,
                ]
            )
        else:
            combined_embeddings = new_embeddings

        np.save(
            self.embeddings_path,
            combined_embeddings
        )

        with open(
            self.chunks_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                existing_chunks,
                file,
                ensure_ascii=False,
                indent=2,
            )

    async def search(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
    ) -> list[dict]:

        if not self.embeddings_path.exists():
            return []

        if not self.chunks_path.exists():
            return []

        embeddings = np.load(
            self.embeddings_path
        )

        with open(
            self.chunks_path,
            "r",
            encoding="utf-8"
        ) as file:
            chunks = json.load(file)

        if len(embeddings) == 0 or not chunks:
            return []

        query_embedding = np.array(
            await self.create_embedding(
                query,
                "RETRIEVAL_QUERY"
            ),
            dtype=np.float32,
        )

        # Normalize query vector
        query_norm = np.linalg.norm(
            query_embedding
        )

        if query_norm == 0:
            return []

        query_embedding = (
            query_embedding / query_norm
        )

        # Normalize document vectors
        embedding_norms = np.linalg.norm(
            embeddings,
            axis=1,
            keepdims=True,
        )

        embedding_norms[
            embedding_norms == 0
        ] = 1

        normalized_embeddings = (
            embeddings / embedding_norms
        )

        # Cosine similarity
        similarities = (
            normalized_embeddings
            @ query_embedding
        )

        top_k = (
            top_k
            if top_k is not None
            else self.settings.RAG_TOP_K
        )

        similarity_threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else self.settings.RAG_SIMILARITY_THRESHOLD
        )

        ranked_indices = np.argsort(
            similarities
        )[::-1]

        results = []

        for index in ranked_indices:
            score = float(
                similarities[index]
            )

            if score < similarity_threshold:
                continue

            chunk = chunks[index]

            results.append(
                {
                    "document_id": chunk["document_id"],
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "score": round(score, 4),
                }
            )

            if len(results) >= top_k:
                break

        return results

    def remove_document(
        self,
        document_id: str
    ) -> int:
        if not self.chunks_path.exists():
            return 0

        with open(
            self.chunks_path,
            "r",
            encoding="utf-8"
        ) as file:
            chunks = json.load(file)

        if not chunks:
            return 0

        if not self.embeddings_path.exists():
            return 0

        embeddings = np.load(
            self.embeddings_path
        )

        keep_indices = [
            index
            for index, chunk in enumerate(chunks)
            if chunk["document_id"] != document_id
        ]

        filtered_chunks = [
            chunks[index]
            for index in keep_indices
        ]

        if keep_indices:
            filtered_embeddings = embeddings[
                keep_indices
            ]
        else:
            filtered_embeddings = np.empty(
                (
                    0,
                    self.settings.EMBEDDING_DIMENSION,
                ),
                dtype=np.float32,
            )

        np.save(
            self.embeddings_path,
            filtered_embeddings
        )

        removed_count = len(chunks) - len(filtered_chunks)

        with open(
            self.chunks_path,
            "w",
            encoding="utf-8"
        ) as file:
            json.dump(
                filtered_chunks,
                file,
                ensure_ascii=False,
                indent=2,
            )

        return removed_count