from abc import ABC, abstractmethod

from src.models.document import Document


class SourceConnector(ABC):
    """Base interface for API-backed knowledge sources."""

    @abstractmethod
    def load_documents(self) -> list[Document]:
        """Load documents from the external source."""


class NotionConnector(SourceConnector):
    def load_documents(self) -> list[Document]:
        raise NotImplementedError("Notion ingestion requires API credentials and page export rules.")


class ConfluenceConnector(SourceConnector):
    def load_documents(self) -> list[Document]:
        raise NotImplementedError("Confluence ingestion requires API credentials and space/page rules.")


class GoogleDriveConnector(SourceConnector):
    def load_documents(self) -> list[Document]:
        raise NotImplementedError("Google Drive ingestion requires OAuth credentials and export MIME types.")


class SlackConnector(SourceConnector):
    def load_documents(self) -> list[Document]:
        raise NotImplementedError("Slack ingestion requires API credentials, channel selection, and thread rules.")
