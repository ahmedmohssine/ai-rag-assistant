from pathlib import Path


class URLBuilder:

    def build(self, source: str, path: str) -> str | None:
        path = Path(path).as_posix()

        if source.lower() == "fastapi":
            return self._fastapi(path)

        if source.lower() == "chromadb":
            return self._chromadb(path)

        return None

    def _fastapi(self, path: str) -> str | None:
        if "docs/fastapi/" not in path:
            return None

        relative = path.split("docs/fastapi/", 1)[1]
        relative = relative.removesuffix(".md")

        if relative == "index":
            return "https://fastapi.tiangolo.com/"

        if relative.endswith("/index"):
            relative = relative[:-6]

        return f"https://fastapi.tiangolo.com/{relative}/"

    def _chromadb(self, path: str) -> str | None:
        if "docs/chromadb/" not in path:
            return None

        relative = path.split("docs/chromadb/", 1)[1]
        relative = relative.removesuffix(".md")

        if relative == "index":
            return "https://docs.trychroma.com/"

        if relative.endswith("/index"):
            relative = relative[:-6]

        return f"https://docs.trychroma.com/{relative}/"