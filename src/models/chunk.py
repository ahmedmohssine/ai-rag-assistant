
class Chunk:
    """A class representing a chunk of a document."""
    def __init__(self,document_source,document_path,chunk_id,content,): 
        self.document_source = document_source
        self.document_path = document_path
        self.chunk_id = chunk_id
        self.content = content