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
    ) -> list[Chunk]: 
        """Chunk a document into smaller pieces.(MVP)"""

        chunks = []

        text = document.content # Get the content of the document

        for i in range(0, len(text), chunk_size): # Iterate through the text in steps of chunk_size
            chunk_content = text[i:i + chunk_size]
            chunk = Chunk(
                document_source=document.source,
                document_path=document.path,
                chunk_id=f"{document.path}_{i}",
                content=chunk_content
            )
            chunks.append(chunk)    

        return chunks
    
