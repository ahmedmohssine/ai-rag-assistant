from pathlib import Path
from pypdf import PdfReader

from src.ingestion.url_builder import URLBuilder
from src.models.document import Document

SKIP_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
}

SUPPORTED_EXTENSIONS = {
    ".md",
    ".mdx",
    ".txt",
    ".rst",
    ".csv",
    ".json",
    ".jsonl",
    ".pdf",
}


class DocumentReader:
    """Reads documents from a local or exported knowledge corpus."""

    def __init__(self, supported_extensions: set[str] = None):
        self.supported_extensions = supported_extensions or SUPPORTED_EXTENSIONS

    def load_documents(self, directory: Path) -> list[Document]:
        """Load supported documents from a directory."""
        documents = []
        directory = Path(directory)

        for file in directory.rglob("*"):
            if not file.is_file():
                continue
            if file.name in SKIP_FILES:
                continue
            if file.suffix.lower() not in self.supported_extensions:
                continue

            content = self._read_file(file)
            if not content.strip():
                continue

            relative_path = file.relative_to(directory).as_posix()
            source = self._source_from_path(relative_path)
            url_builder = URLBuilder()
            document = Document(
                source=source,
                path=file.as_posix(),
                content=content,
                filename=file.stem,
                file_type=file.suffix.lower().lstrip("."),
                title=self._extract_title(content, file),
                url=url_builder.build(source, file.as_posix()),
                metadata={
                    "relative_path": relative_path,
                    "extension": file.suffix.lower(),
                },
            )

            documents.append(document)

        return documents

    def _read_file(self, file: Path) -> str:
        if file.suffix.lower() == ".pdf":
            return self._read_pdf(file)

        with open(file, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

    def _read_pdf(self, file: Path) -> str:

        reader = PdfReader(str(file))
        pages = []

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                pages.append(f"[Page {page_number}]\n{text}")

        return "\n\n".join(pages)

    def _source_from_path(self, relative_path: str) -> str:
        parts = Path(relative_path).parts
        return parts[0] if parts else "unknown"

    def _extract_title(self, content: str, file: Path) -> str:
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()

        return file.stem
