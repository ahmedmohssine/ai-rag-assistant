from pathlib import Path

from src.models.document import Document
from src.models.chunk import Chunk

class Chunker:
    """A class responsible for chunking documents into smaller pieces."""
    def __init__(self):
        pass
    def chunk_document(
        self,
        document: Document,
        chunk_size: int = 1000,
        overlap: int = 200,
    ) -> list[Chunk]: 
        """Chunk a document into smaller pieces.(MVP)"""

        chunks = []

        text = document.content # Get the content of the document

        step = chunk_size - overlap

        for i in range(0, len(text), step): # Iterate through the text in steps of chunk_size
            chunk_content = text[i:i + chunk_size]
            filename = Path(document.path).stem
            # Use a POSIX-style string for relative_path to avoid Path objects in Chunk
            relative_path = Path(document.path).with_suffix("").as_posix()
            chunk = Chunk(
                document_source=document.source,
                document_path=document.path.replace("\\", "/"),
                filename=filename,
                relative_path=relative_path,
                chunk_id=f"{relative_path}_{i}",
                content=chunk_content,
                author=document.author,
                date=document.date,
                url=document.url,
            )
            if len(chunk_content.strip()) < 50:
                continue
            chunks.append(chunk)    

        return chunks
