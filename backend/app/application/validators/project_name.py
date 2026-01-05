import re
from fastapi import HTTPException

# Solo letras minúsculas, números, guion y guion bajo
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def normalize_project_name(name: str) -> str:
    """
    Normaliza un nombre de proyecto a un 'slug' seguro.
    - trim
    - minúsculas
    - espacios -> guion
    """
    name = name.strip().lower()
    name = re.sub(r"\s+", "-", name)  # espacios a '-'
    return name


def validate_project_name(name: str) -> str:
    """
    Valida que el nombre:
    - sea seguro para rutas (sin ../, /, \\)
    - cumpla un slug sencillo [a-z0-9_-]
    - longitud razonable
    Devuelve el nombre normalizado si es válido.
    """
    normalized = normalize_project_name(name)

    # Bloqueos de seguridad básicos (path traversal)
    if ".." in normalized or "/" in normalized or "\\" in normalized:
        raise HTTPException(status_code=400, detail="Nombre de proyecto inválido")

    if not _SLUG_RE.match(normalized):
        raise HTTPException(
            status_code=400,
            detail="Nombre inválido. Usa letras (a-z), números (0-9), guion (-) o guion bajo (_), máximo 64 caracteres.",
        )

    return normalized