import re
from pathlib import Path

class URLBuilder:

    def build(self, source: str, path: str) -> str:
        posix_path = Path(path).as_posix()

        embedded_url = self._extract_url_from_file(posix_path)
        if embedded_url:
            return embedded_url

        structural = self._build_structural_url(source, posix_path)
        if structural:
            return structural

        return posix_path

    def _extract_url_from_file(self, path: str) -> str | None:
        """Extract a URL directly from document metadata or HTML."""

        try:
            p = Path(path)

            if not p.is_file():
                return None

            # Read only the beginning of the file (where frontmatter usually lives)
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content_sample = "".join(f.readline() for _ in range(40))

            patterns = [
                # YAML frontmatter
                r'^\s*url:\s*["\']?(https?://[^\s"\']+)["\']?',
                r'^\s*link:\s*["\']?(https?://[^\s"\']+)["\']?',
                r'^\s*canonical:\s*["\']?(https?://[^\s"\']+)["\']?',
                r'^\s*permalink:\s*["\']?(https?://[^\s"\']+)["\']?',

                # HTML
                r'<link\s+rel=["\']canonical["\']\s+href=["\'](https?://[^"\']+)["\']',

                # OpenGraph
                r'property=["\']og:url["\']\s+content=["\'](https?://[^"\']+)["\']',
            ]

            for pattern in patterns:
                match = re.search(
                    pattern,
                    content_sample,
                    re.MULTILINE | re.IGNORECASE,
                )
                if match:
                    return match.group(1).strip()

        except Exception:
            pass

        return None
    def _build_structural_url(self, source: str, path: str) -> str | None:
        if not source or not path:
            return None

        path = Path(path).as_posix()
        lower = path.lower()
        source = source.lower()

        # ---------------- FASTAPI ----------------
        if source == "fastapi":

            marker = "docs/fastapi/docs/"

            if marker not in lower:
                return None

            route = path[lower.index(marker) + len(marker):]

            route = re.sub(r"\.(md|mdx)$", "", route)

            if route.endswith("/index"):
                route = route[:-6]

            route = route.strip("/")

            return f"https://fastapi.tiangolo.com/{route}/"
        
        
           # ---------------- Chroma ----------------
        if source == "chromadb" or source == "chroma":

            marker = "docs/chromadb/docs/mintlify/"

            if marker not in lower:
                return None

            route = path[lower.index(marker) + len(marker):]

            route = re.sub(r"\.(md|mdx)$", "", route)

            if route.endswith("/index"):
                route = route[:-6]

            route = route.strip("/")

            return f"https://docs.trychroma.com/{route}/"



        return None