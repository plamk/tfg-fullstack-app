from pathlib import Path

def discover_projects(projects_dir: Path) -> list[str]:
    """
    Devuelve nombres de proyectos válidos (carpetas con config.json).
    """
    if not projects_dir.exists():
        return []

    return sorted(
        p.name for p in projects_dir.iterdir()
        if p.is_dir()
        and not p.name.startswith(".")
        and (p / "config.json").exists()
    )