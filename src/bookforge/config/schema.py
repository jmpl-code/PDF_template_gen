"""Modeles Pydantic v2 pour book.yaml (Stories 2.1, 4.2)."""

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ChapterConfig(BaseModel):
    """Configuration d'un chapitre."""

    titre: str
    fichier: str


class BookConfig(BaseModel):
    """Configuration complete d'un livre definie par book.yaml."""

    model_config = ConfigDict(populate_by_name=True)

    titre: str
    sous_titre: str | None = None
    auteur: str
    genre: str
    isbn: str | None = None
    dedicace: str | None = None
    description: str | None = None
    mots_cles: list[str] | None = None
    categories: list[str] | None = None
    chapitres: list[ChapterConfig]
    document_class: str = Field(
        default="business-manual",
        alias="class",
        pattern=r"^[a-z][a-z0-9]*(-[a-z0-9]+)*$",
    )
    tokens: str | None = None

    @field_validator("chapitres")
    @classmethod
    def chapitres_non_vide(cls, v: list[ChapterConfig]) -> list[ChapterConfig]:
        if not v:
            raise ValueError("La liste des chapitres ne peut pas etre vide")
        return v
