from dataclasses import dataclass


@dataclass
class TextChunk:
    index: int
    text: str
    start_char: int
    end_char: int


def split_text(
    text: str,
    chunk_size: int = 3500,
    chunk_overlap: int = 500,
) -> list[TextChunk]:

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero."
        )

    if chunk_overlap < 0:
        raise ValueError(
            "chunk_overlap cannot be negative."
        )

    if chunk_overlap >= chunk_size:
        raise ValueError(
            "chunk_overlap must be smaller than chunk_size."
        )

    text_length = len(text)

    if text_length <= chunk_size:
        return [
            TextChunk(
                index=0,
                text=text,
                start_char=0,
                end_char=text_length,
            )
        ]

    chunks = []

    start = 0
    index = 0

    while start < text_length:

        target_end = min(
            start + chunk_size,
            text_length,
        )

        end = target_end

        if target_end < text_length:

            paragraph_boundary = text.rfind(
                "\n",
                start,
                target_end,
            )

            sentence_boundary = text.rfind(
                ". ",
                start,
                target_end,
            )

            if paragraph_boundary > start + chunk_size // 2:
                end = paragraph_boundary

            elif sentence_boundary > start + chunk_size // 2:
                end = sentence_boundary + 1

        chunk_text = text[start:end].strip()

        if chunk_text:

            chunks.append(
                TextChunk(
                    index=index,
                    text=chunk_text,
                    start_char=start,
                    end_char=end,
                )
            )

            index += 1

        if end >= text_length:
            break

        next_start = end - chunk_overlap

        if next_start <= start:
            next_start = end

        start = next_start

    return chunks