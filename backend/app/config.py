from pathlib import Path
import os

ENV = os.getenv("MEAPLAN_ENV", "sim")  # sim | raspi
DATA_DIR = Path(os.getenv("MEAPLAN_DATA_DIR", "data")).resolve()