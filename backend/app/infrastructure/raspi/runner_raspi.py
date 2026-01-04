from __future__ import annotations

from pathlib import Path
from typing import Optional


class RaspiRunner:
    """
    Adaptador para ejecutar el core real (meapis) en Raspberry Pi.

    Importante:
    - Este runner NO debe importarse/instanciarse en Mac si no tienes las libs de Raspberry
      (picamera2/libcamera/gpiod). Por eso hacemos imports "dentro" del __init__.
    - Comparte estructura de data_dir con FakeRunner:
        data/
          projects/
          media/
    """

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.projects_dir = data_dir / "projects"
        self.media_dir = data_dir / "media"

        # Import diferido: solo funcionará en Raspberry con dependencias instaladas
        from meapis.utils.project_runner import ProjectRunner  # type: ignore
        from meapis.utils.light import Light  # type: ignore

        # Guardamos referencias para poder apagarlas en shutdown()
        self._light = Light()
        self._runner = ProjectRunner(self._light)

        # Estado mínimo para status()
        self._active_project: Optional[str] = None

    # ---------------------------
    # Métodos requeridos por RunnerPort
    # ---------------------------

    def status(self) -> dict:
        """
        Devuelve un estado básico. Cuando conectemos bien el core, podremos enriquecerlo
        (intervalo real, última captura real, etc.).
        """
        return {
            "env": "raspi",
            "active_project": self._active_project,
        }

    def list_projects(self) -> list[str]:
        """
        Lista proyectos disponibles leyendo el filesystem (igual que en FakeRunner).
        """
        from app.infrastructure.projects_fs import discover_projects

        return discover_projects(self.projects_dir)

    def start_project(self, name: str) -> None:
        """
        Arranca un proyecto usando el core.
        """
        # Nota: ProjectRunner ya sabe leer current.txt y config, según tu core.
        # Si tu ProjectRunner necesita un nombre y luego lee config, perfecto.
        self._runner.start_project(name)
        self._active_project = name

    def stop_project(self) -> None:
        """
        Para el proyecto actual.
        """
        self._runner.stop_project()
        self._active_project = None

    def capture_now(self) -> dict:
        """
        Captura inmediata: depende de cómo esté montado el core.
        En tu core, la captura real ocurre en CameraController.take_picture() disparada por tasks.
        Cuando tengamos la Raspberry, lo implementamos de forma segura.

        De momento, dejamos esto claro:
        - o implementamos ProjectRunner.capture_now() en el core
        - o accedemos a camera_controller si está expuesto
        """
        raise NotImplementedError(
            "capture_now() pendiente: al tener Raspberry definimos el disparo directo de captura "
            "(vía ProjectRunner o camera_controller)."
        )

    def shutdown(self) -> None:
        """
        Apaga de forma segura el core y libera recursos (scheduler, cámara, GPIO).
        """
        try:
            self._runner.shutdown()
        except Exception:
            pass

        try:
            self._light.close()
        except Exception:
            pass