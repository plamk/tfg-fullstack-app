from __future__ import annotations
from pathlib import Path
from typing import Optional


class RaspiRunner:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.projects_dir = data_dir / "projects"
        self.media_dir = data_dir / "media"

        # IMPORTS DIFERIDOS → solo funcionan en Raspberry
        from meapis.utils.project_runner import ProjectRunner
        from meapis.utils.light import Light

        self._light = Light()
        self._runner = ProjectRunner(self._light)

        self._active_project: Optional[str] = None

    def status(self) -> dict:
        return {
            "env": "raspi",
            "active_project": self._active_project,
        }

    def list_projects(self) -> list[str]:
        from app.infrastructure.projects_fs import discover_projects
        return discover_projects(self.projects_dir)

    def start_project(self, name: str) -> None:
        self._runner.start_project(name)
        self._active_project = name

    def stop_project(self) -> None:
        self._runner.stop_project()
        self._active_project = None

    def capture_now(self) -> dict:
        return self._runner.capture_now()

    def shutdown(self) -> None:
        try:
            self._runner.shutdown()
        except Exception:
            pass

        try:
            self._light.close()
        except Exception:
            pass