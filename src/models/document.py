class Document:
    """A class representing a document."""
    def __init__(
            self, 
            source: str, 
            path: str, 
            content: str,
            filename: str = None,
            file_type: str = None,
            title: str = None,
            author: str = None,
            date: str = None,
            url: str = None,
            metadata: dict = None,
            ):
        self.source = source
        self.path = path
        self.content = content
        self.filename = filename
        self.file_type = file_type
        self.title = title
        self.author = author
        self.date = date
        self.url = url
        self.metadata = metadata or {}
        


    def __repr__(self):
        """Return a string representation of the Document object."""
        return (
            f"Document("
            f"source='{self.source}', "
            f"path='{self.path}', "
            f"file_type='{self.file_type}', "
            f"content_length={len(self.content)})"
        )
