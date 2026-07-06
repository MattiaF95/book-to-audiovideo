from pathlib import Path


def ensure_file(path: Path, label: str) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"{label} non trovato: {path}")


def ensure_non_empty(value: str, label: str) -> None:
    if not value.strip():
        raise ValueError(f"{label} vuoto")
