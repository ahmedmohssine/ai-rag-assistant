from pathlib import Path
import re

from src.models.document import Document
from src.models.chunk import Chunk

class Chunker:
    """A class responsible for chunking documents into smaller pieces."""
    def __init__(self, chunk_size: int = 750, overlap: int = 150):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_document(
        self,
        document: Document,
        chunk_size: int = None,
        overlap: int = None,
    ) -> list[Chunk]: 
        """Chunk a document into structure-aware overlapping chunks."""

        chunks = []
        text = document.content
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap if overlap is not None else self.overlap
        filename = document.filename or Path(document.path).stem
        relative_path = document.metadata.get(
            "relative_path",
            Path(document.path).with_suffix("").as_posix()
        )
        chunk_path = Path(relative_path).with_suffix("").as_posix()

        for chunk_content, start_index in self._split_text(text, chunk_size, overlap):
            if len(chunk_content.strip()) < 50:
                continue

            citation_id = f"{document.source}:{filename}_{start_index}"
            chunk = Chunk(
                document_source=document.source,
                document_path=document.path.replace("\\", "/"),
                filename=filename,
                relative_path=relative_path,
                chunk_id=f"{chunk_path}_{start_index}",
                content=chunk_content,
                file_type=document.file_type,
                title=document.title,
                author=document.author,
                date=document.date,
                url=document.url,
                metadata={
                    **document.metadata,
                    "citation_id": citation_id,
                    "start_index": start_index,
                },
            )
            chunks.append(chunk)    

        return chunks

    def _split_text(self, text: str, chunk_size: int, overlap: int) -> list[tuple[str, int]]:
        # Use markdown-aware blocks instead of raw character windows.
        # Smaller chunks keep tutorial pages focused, so one chunk is more likely
        # to contain exactly the "how to" answer instead of unrelated sections.
        blocks = self._markdown_blocks(text)
        chunks = []
        current_parts = []
        current_start = None
        current_length = 0

        for block, start_index in blocks:
            if len(block) > chunk_size:
                if current_parts:
                    chunks.append(("\n\n".join(current_parts).strip(), current_start))
                    current_parts = []
                    current_start = None
                    current_length = 0

                chunks.extend(self._recursive_split(block, start_index, chunk_size, overlap))
                continue

            separator = 2 if current_parts else 0
            next_length = current_length + separator + len(block)

            if current_parts and next_length > chunk_size:
                chunk_text = "\n\n".join(current_parts).strip()
                chunks.append((chunk_text, current_start))
                overlap_text = self._tail_overlap(chunk_text, overlap)
                current_parts = [overlap_text, block] if overlap_text else [block]
                current_start = start_index - len(overlap_text) if overlap_text else start_index
                current_length = sum(len(part) for part in current_parts) + 2 * (len(current_parts) - 1)
            else:
                if current_start is None:
                    current_start = start_index
                current_parts.append(block)
                current_length = next_length

        if current_parts:
            chunks.append(("\n\n".join(current_parts).strip(), current_start))

        return chunks

    def _markdown_blocks(self, text: str) -> list[tuple[str, int]]:
        blocks = []
        in_code_block = False
        current_lines = []
        current_start = 0
        offset = 0
        heading_stack = []

        for line in text.splitlines(keepends=True):
            stripped = line.strip()
            starts_heading = stripped.startswith("#")
            starts_fence = stripped.startswith("```") or stripped.startswith("~~~")

            if starts_fence:
                in_code_block = not in_code_block

            if current_lines and not in_code_block and starts_heading:
                blocks.append((self._with_heading_context("".join(current_lines).strip(), heading_stack), current_start))
                current_lines = []
                current_start = offset

            if current_lines and not in_code_block and not stripped:
                blocks.append((self._with_heading_context("".join(current_lines).strip(), heading_stack), current_start))
                current_lines = []
                current_start = offset + len(line)
            else:
                if not current_lines:
                    current_start = offset
                current_lines.append(line)

            if starts_heading and not in_code_block:
                heading_stack = self._update_heading_stack(heading_stack, stripped)

            offset += len(line)

        if current_lines:
            blocks.append((self._with_heading_context("".join(current_lines).strip(), heading_stack), current_start))

        return [(block, start) for block, start in blocks if block.strip()]

    def _update_heading_stack(self, heading_stack: list[str], heading_line: str) -> list[str]:
        # Track the current markdown heading path, e.g.
        # "# Tutorial" + "## First Steps" becomes ["Tutorial", "First Steps"].
        level = len(heading_line) - len(heading_line.lstrip("#"))
        title = heading_line.lstrip("#").strip()
        next_stack = heading_stack[:max(level - 1, 0)]
        next_stack.append(title)
        return next_stack

    def _with_heading_context(self, block: str, heading_stack: list[str]) -> str:
        if not heading_stack:
            return block

        heading_context = "\n".join(f"Section: {heading}" for heading in heading_stack)
        if block.startswith("#") or block.startswith("Section:"):
            return block

        # Prefix every chunk block with the active headings. This helps both BM25
        # and embeddings understand that a paragraph belongs to "First Steps"
        # or "Tutorial" even if the heading appeared a few lines earlier.
        return f"{heading_context}\n\n{block}"

    def _recursive_split(
        self,
        text: str,
        start_index: int,
        chunk_size: int,
        overlap: int,
    ) -> list[tuple[str, int]]:
        separators = [r"(?<=[.!?])\s+", r"\n", r"\s+"]

        for separator in separators:
            pieces = re.split(separator, text)
            if len(pieces) == 1:
                continue

            chunks = []
            current = ""
            cursor = start_index

            for piece in pieces:
                if not piece:
                    continue
                candidate = f"{current} {piece}".strip() if current else piece.strip()
                if len(candidate) > chunk_size and current:
                    chunks.append((current, cursor))
                    overlap_text = self._tail_overlap(current, overlap)
                    cursor += max(len(current) - len(overlap_text), 0)
                    current = f"{overlap_text} {piece}".strip() if overlap_text else piece.strip()
                else:
                    current = candidate

            if current:
                chunks.append((current, cursor))

            if all(len(chunk) <= chunk_size + overlap for chunk, _ in chunks):
                return chunks

        step = max(chunk_size - overlap, 1)
        return [
            (text[index:index + chunk_size], start_index + index)
            for index in range(0, len(text), step)
        ]

    def _tail_overlap(self, text: str, overlap: int) -> str:
        if overlap <= 0:
            return ""

        tail = text[-overlap:]
        boundary = max(tail.rfind("\n"), tail.rfind(". "), tail.rfind(" "))
        if boundary > 0:
            return tail[boundary:].strip()

        return tail.strip()
