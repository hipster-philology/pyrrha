from typing import Optional
from dataclasses import dataclass


@dataclass
class LemmatizerService:
    title: str   # e.g. "Old French"
    uri: str  # Current address
    provider: str  # e.g. Deucalion at Ecole nationale des Chartes
    bibtex: str  # Citation Scheme
    apa: str  # APA equivalent
    ui: Optional[str] = None
