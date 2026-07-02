class Document:
    """A class representing a document."""
    def __init__(self, source: str, path: str, content: str):
        self.source = source
        self.path = path
        self.content = content

    def __repr__(self):
        """Return a string representation of the Document object."""
        return (
            f"Document("
            f"source='{self.source}', "
            f"path='{self.path}', "
            f"content_length={len(self.content)})"
        )