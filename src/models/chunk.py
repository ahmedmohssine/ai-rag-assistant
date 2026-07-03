class Chunk:
    """A class representing a chunk of a document."""

    def __init__(
        self,
        document_source,
        document_path,
        filename,
        relative_path,
        chunk_id,
        content,
        author=None,
        date=None,
        url=None
    ):
        self.document_source = document_source
        self.document_path = document_path
        self.filename = filename
        self.relative_path = relative_path
        self.chunk_id = chunk_id
        self.content = content
        self.author = author
        self.date = date
        self.url = url

    def to_dict(self):
        return {
            "chunk_id": self.chunk_id,
            "source": self.document_source,
            "path": self.document_path,
            "filename": self.filename,
            "relative_path": self.relative_path,
            "content": self.content,
            "author": self.author,
            "date": self.date,
            "url": self.url,
        }

    def __repr__(self):
        return (
            f"Chunk("
            f"id='{self.chunk_id}', "
            f"source='{self.document_source}', "
            f"filename='{self.filename}', " 
            f"length={len(self.content)})"
            
        )