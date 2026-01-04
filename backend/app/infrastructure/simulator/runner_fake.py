from pathlib import Path
from datetime import datetime
import json
from apscheduler.schedulers.background import BackgroundScheduler
from PIL import Image, ImageDraw


class FakeRunner:
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.projects_dir = data_dir / "projects"
        self.media_dir = data_dir / "media"
        self.current_file = self.projects_dir / "current.txt"

        self.scheduler = BackgroundScheduler()
        self.scheduler.start()

        self.curr_project = None
        self.job_id = "capture_job"
        self.last_capture = None

        initial = self._read_text(self.current_file)
        if initial:
            try:
                self.start_project(initial)
            except FileNotFoundError:
                self.curr_project = None

    # --- helpers ---
    def _read_text(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8").strip()

    def _read_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _write_text(self, path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    # --- API del runner ---
    def list_projects(self) -> list[str]:
        if not self.projects_dir.exists():
            return []

        return sorted(
            p.name for p in self.projects_dir.iterdir()
            if p.is_dir()
            and not p.name.startswith(".")
            and (p / "config.json").exists()
        )

    def start_project(self, name: str) -> None:
        cfg_path = self.projects_dir / name / "config.json"
        if not cfg_path.exists():
            raise FileNotFoundError(str(cfg_path))
        cfg = self._read_json(cfg_path)

        self.curr_project = {
            "name": name,
            "filename": cfg.get("filename", name),
            "interval": int(cfg.get("interval", 10)),
        }
        self._write_text(self.current_file, name)

        self.scheduler.add_job(
            self._scheduled_capture,
            "interval",
            seconds=self.curr_project["interval"],
            id=self.job_id,
            replace_existing=True,
        )

    def stop_project(self) -> None:
        try:
            self.scheduler.remove_job(self.job_id)
        except Exception:
            pass
        self.curr_project = None

    def capture_now(self) -> dict:
        if not self.curr_project:
            raise RuntimeError("No hay proyecto activo")

        proj = self.curr_project
        out_dir = self.media_dir / proj["name"]
        out_dir.mkdir(parents=True, exist_ok=True)

        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f'{proj["filename"]}_{ts}.jpg'
        img_path = out_dir / filename

        img = Image.new("RGB", (1280, 720))
        draw = ImageDraw.Draw(img)
        draw.text((20, 20), f"SIM CAPTURE\n{proj['name']}\n{ts}", fill=(255, 255, 255))
        img.save(img_path, "JPEG", quality=90)

        meta = {
            "project": proj["name"],
            "filename": filename,
            "timestamp_utc": ts,
            "path": str(img_path),
            "camera": "SIM",
        }

        (out_dir / f"{filename}.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
        self.last_capture = meta
        return meta

    def _scheduled_capture(self) -> None:
        try:
            self.capture_now()
        except Exception:
            pass

    def status(self) -> dict:
        return {
            "env": "sim",
            "active_project": self.curr_project["name"] if self.curr_project else None,
            "interval": self.curr_project["interval"] if self.curr_project else None,
            "last_capture": self.last_capture,
        }

    def shutdown(self) -> None:
        try:
            self.scheduler.shutdown(wait=False)
        except Exception:
            pass