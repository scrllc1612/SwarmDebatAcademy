from pydantic import BaseModel


class DebateSummary(BaseModel):
    """
    Resumen generado por el moderador
    después de cada ronda.
    """

    pro_main_point: str

    contra_main_point: str

    main_conflict: str

    unresolved_issue: str