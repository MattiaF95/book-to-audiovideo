from __future__ import annotations

import shutil
from pathlib import Path

from docx import Document
from pypdf import PdfReader

from book_to_audiovideo.pipeline.errors import PipelineError


class FileService:
    SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf", ".docx"}

    def save_upload(self, source_path: Path, artifact_dir: Path) -> Path:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        target = artifact_dir / source_path.name
        shutil.copy2(source_path, target)
        return target

    def read_text(self, source_path: Path) -> str:
        # Il file viene letto in base all'estensione: testo semplice, PDF o DOCX richiedono logiche diverse.
        extension = source_path.suffix.lower()
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise PipelineError(f"Formato non supportato: {extension}")
        if extension in {".txt", ".md"}:
            return source_path.read_text(encoding="utf-8")
        if extension == ".pdf":
            reader = PdfReader(str(source_path))
            return "\n".join((page.extract_text() or "") for page in reader.pages)
        if extension == ".docx":
            document = Document(str(source_path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        raise PipelineError(f"Formato non gestito: {extension}")
