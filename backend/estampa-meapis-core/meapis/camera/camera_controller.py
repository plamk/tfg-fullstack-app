import logging
import time

from .camera_config import CameraConfig
from owlsight import Owlsight
from v3 import V3


class CameraController:
    def __init__(self, project, light):
        self.project = project
        self.light = light

        if project.camera == 0:
            self.camera = Owlsight(project)
        else:
            self.camera = V3(project)

        self.config_picture = CameraConfig(self.camera).create_picture_config()

        if not self.project.has_camera_settings:
            camera_settings = self.compute_camera_settings()
            self.project.set_camera_settings(camera_settings, save=True)
            logging.info("Computed and saved new camera settings")
        else:
            logging.info("Using saved camera settings")

        # Apply saved camera settings to picture config
        for setting, value in self.project.camera_settings.items():
            self.config_picture.set_control(setting, value)

        self.camera.setup(self.config_picture)

    def auto_focus(self, config_focus):
        focused = False

        while not focused:
            focused = self.camera.autofocus()
            metadata = self.camera.take_picture(config_focus, output_path=self.project.path_setup, filename_postfix="focus")
            # print(metadata)
            if focused:
                logging.info("Autofocus successful")
                return metadata["LensPosition"]
            else:
                logging.warning("Autofocus failed")

    def compute_camera_settings(self):
        config_focus = CameraConfig(self.camera).create_focus_config()
        config_exposure = CameraConfig(self.camera).create_exposure_config()

        self.camera.setup(config_focus)

        self.light.turn_on()

        # Autofocus twice to ensure good focus
        self.auto_focus(config_focus)
        lens_position = self.auto_focus(config_focus)
        logging.info(f"Autofocus complete, LensPosition: {lens_position}")
        config_exposure.set_control("LensPosition", lens_position)
        self.config_picture.set_control("LensPosition", lens_position)

        time.sleep(1)

        # Autoexposure and take picture to get the correct exposure setting
        metadata = self.camera.take_picture(config_exposure, output_path=self.project.path_setup, filename_postfix="exposure")
        logging.info("Autoexposure complete")
        self.config_picture.set_control("AnalogueGain", metadata["AnalogueGain"])
        self.config_picture.set_control("ExposureTime", metadata["ExposureTime"])

        self.light.turn_off()

        camera_settings = {
            "LensPosition": self.config_picture.get_control("LensPosition"),
            "AnalogueGain": self.config_picture.get_control("AnalogueGain"),
            "ExposureTime": self.config_picture.get_control("ExposureTime"),
        }

        return camera_settings

    def take_picture(self):
        if self.project.use_light:
            self.light.turn_on()

        metadata = self.camera.take_picture()

        if self.project.use_light:
            self.light.turn_off()

        return metadata

    def close(self):
        self.camera.close()