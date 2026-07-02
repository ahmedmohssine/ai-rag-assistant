from pathlib import Path

from src.models.document import Document


class DocumentReader:
    """A class responsible for reading markdown documents from a directory."""
    def __init__(self):
        pass
    def load_documents(self, directory: Path) -> list[Document]:
        """Load markdown documents from a directory.(for now)"""
        documents = []

        for file in directory.rglob("*.md"): # Recursively find all markdown files in the directory

            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

            document = Document(      # Create a Document object for each markdown file
                source=file.parts[1],
                path=str(file),
                content=content,
            )

            documents.append(document) # Append the Document object to the list of documents

        return documents
