"""Modeles Pydantic v2 pour book.yaml (Story 2.1)."""

from pydantic import BaseModel, field_validator


class ChapterConfig(BaseModel):
    """Configuration d'un chapitre."""

    titre: str
    fichier: str


class BookConfig(BaseModel):
    """Configuration complete d'un livre definie par book.yaml."""

    titre: str
    sous_titre: str | None = None
    auteur: str
    genre: str
    isbn: str | None = None
    dedicace: str | None = None
    chapitres: list[ChapterConfig]

    @field_validator("chapitres")
    @classmethod
    def chapitres_non_vide(cls, v: list[ChapterConfig]) -> list[ChapterConfig]:
        if not v:
            raise ValueError("La liste des chapitres ne peut pas etre vide")
        return v
