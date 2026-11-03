import io
import re
import unicodedata
import zipfile
from collections import Counter
from pathlib import Path

import pymupdf
from docx import Document

from backend.config import settings


class DocumentError(ValueError):
    pass


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    text = "".join(c for c in text if c in "\n\t" or not unicodedata.category(c).startswith("C"))
    text = re.sub(r"(?<=\w)-\n(?=\w)", "", text)
    return "\n".join(re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines() if line.strip())


def extract_document(filename: str, data: bytes) -> str:
    if not data or len(data) > settings().max_file_bytes:
        raise DocumentError("Le fichier doit contenir des données et ne pas dépasser 5 Mo.")
    suffix = Path(filename).suffix.lower()
    try:
        if suffix == ".pdf":
            with pymupdf.open(stream=data, filetype="pdf") as doc:
                if doc.needs_pass:
                    raise DocumentError("Le PDF est protégé par un mot de passe.")
                if len(doc) > 30:
                    raise DocumentError("Le document ne doit pas dépasser 30 pages.")
                pages = [p.get_text(sort=True).splitlines() for p in doc]
                # Remove only repeated margin lines, never repeated body evidence.
                edges = Counter(line.strip() for p in pages for line in set(p[:2] + p[-2:]) if line.strip())
                repeated = {line for line, count in edges.items() if len(pages) > 1 and count == len(pages)}
                text = "\n".join(line for p in pages for i, line in enumerate(p)
                                 if not (line.strip() in repeated and (i < 2 or i >= len(p) - 2)))
        elif suffix == ".docx":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if sum(f.file_size for f in archive.infolist()) > 30 * 1024 * 1024:
                    raise DocumentError("Le contenu décompressé du DOCX est trop volumineux.")
            doc = Document(io.BytesIO(data))
            text = "\n".join([p.text for p in doc.paragraphs] +
                             [" | ".join(c.text for c in row.cells) for t in doc.tables for row in t.rows])
        else:
            raise DocumentError("Format non pris en charge. Utilisez un PDF ou DOCX.")
    except DocumentError:
        raise
    except Exception as exc:
        raise DocumentError("Fichier illisible ou corrompu. Exportez-le de nouveau en PDF ou DOCX.") from exc
    text = clean_text(text)
    if len(text) < 30:
        raise DocumentError("Texte insuffisant. Les PDF scannés nécessitent une reconnaissance OCR préalable.")
    if len(text) > settings().max_text_chars:
        raise DocumentError("Le texte extrait dépasse la limite de 30 000 caractères.")
    return text

