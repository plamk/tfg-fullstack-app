import datetime
import json
import logging
import os
import platform

from meapis.environment import Environment

class Project:
    def __init__(self, name: str, camera: int = 0, filename: str = None, interval: int = 60, image_format: str = "jpg", use_light: bool = True):
        self.name = name
        self.camera = camera  # 0 = OwlSight, 1 = V3
        self.filename = name if filename is not None else name
        self.interval = interval  # seconds
        self.image_format = image_format  # Picture format
        self.use_light = use_light

        self.path = os.path.join(Environment.get_project_path(), self.name)
        if not os.path.exists(self.path):
            os.makedirs(self.path)

        self.path_pictures = os.path.join(self.path, "pictures")  # Store pictures here
        if not os.path.exists(self.path_pictures):
            os.makedirs(self.path_pictures)

        self.path_metadata = os.path.join(self.path, "metadata")  # Store metadata here
        if not os.path.exists(self.path_metadata):
            os.makedirs(self.path_metadata)

        self.path_setup = os.path.join(self.path, "setup")  # Store setup pictures here
        if not os.path.exists(self.path_setup):
            os.makedirs(self.path_setup)

        if os.path.isfile(os.path.join(self.path, "config.json")):
            logging.info("Found config.json, retrieving project settings")
            with open(os.path.join(self.path, "config.json"), "r") as json_file:
                json_data = json.load(json_file)

                self.camera = json_data.get("camera", self.camera)
                self.filename = json_data.get("filename", self.filename)
                self.interval = json_data.get("interval", self.interval)
                self.image_format = json_data.get("format", self.image_format)
                self.use_light = json_data.get("use_light", self.use_light)

        self.camera_settings = self.load_camera_settings()  # Load picture settings

    def load_camera_settings(self):
        camera_settings_path = os.path.join(self.path, "camera_settings.json")
        if os.path.isfile(camera_settings_path):
            logging.info("Loading picture settings from camera_settings.json")
            with open(camera_settings_path, "r") as json_file:
                return json.load(json_file)

        return None

    def set_camera_settings(self, camera_settings: dict, save: bool = True):
        self.camera_settings = camera_settings

        if not save:
            return

        camera_settings_path = os.path.join(self.path, "camera_settings.json")
        logging.info("Saving picture settings to camera_settings.json")
        with open(camera_settings_path, "w") as json_file:
            json.dump(camera_settings, json_file, indent=2)

    def get_picture_filename(self, postfix: str = None):
        current_date_and_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        computer_name = platform.node()
        filename = f"{self.filename}-{computer_name}-{self.camera}-{current_date_and_time}"
        if postfix is not None and postfix != "":
            filename += f"-{postfix}"
        return filename

    @property
    def has_camera_settings(self):
        return self.camera_settings is not None
