import json
import logging
import os
import datetime

from picamera2 import Picamera2, Preview  # type: ignore
from libcamera import controls  # type: ignore

from ..project import Project
from .camera_config import CameraConfig


class Camera:
    """
    Base camera class for handling camera operations.
    :param project: Project instance associated with the camera.
    :param num: Camera number (0 for OwlSight, 1 for V3).
    """
    def __init__(self, project: Project, num: int = 0):
        self.num = num
        self.project = project

        os.environ["LIBCAMERA_LOG_LEVELS"] = "ERROR"
        # os.environ["LIBCAMERA_LOG_LEVELS"] = "WARN"

        # Load appropriate tuning file based on camera number
        if self.num == 0:
            tuning = Picamera2.load_tuning_file("ov64a40.json")
        else:
            tuning = Picamera2.load_tuning_file("imx708_noir.json")

        # Adjust autofocus algorithm parameters
        algo = Picamera2.find_tuning_algo(tuning, "rpi.af")
        if "ranges" in algo:
            algo["ranges"]["macro"] = {"min": 7.0, "max": 15.0, "default": 8.0}

        if "speeds" in algo:
            algo["speeds"]["normal"]["step_coarse"] = 0.5
            algo["speeds"]["normal"]["step_fine"] = 0.1

        # Initialize picam2 instance
        self.picam2 = Picamera2(self.num, tuning=tuning)
        # print(Picamera2.global_camera_info())

    """ 
    Create the setup and picture configurations.
    :param setup_mode: If True, configure the camera with the setup configuration after creation.
    """
    def setup(self, config: CameraConfig) -> None:
        logging.info("Setting up camera")
        self.picam2.configure(config.dict)

    """
    Hook for subclasses to add custom camera configuration. 
    :param config: Camera configuration dictionary to modify.
    """
    def add_custom_camera_config(self, config) -> None:
        pass

    """
    ️Take a picture with the camera.
    :param config: Optional custom camera configuration to use for taking the picture.
    :param save: Whether to save the captured image to disk.
    :param save_metadata: Whether to save the metadata of the captured image to disk.
    :param filename_postfix: Optional postfix to append to the filename.
    :param output_path: Optional output path to save the image and metadata.
    :return: Metadata dictionary for the captured image.
    """
    def take_picture(self, config: CameraConfig = None, save: bool = True, save_metadata: bool = True, filename_postfix: str = None, output_path: str = None) -> dict:
        logging.info("Taking picture")

        if config is not None:
            logging.debug("Switching to custom config")
            self.picam2.switch_mode(config.dict)

        self.picam2.start()

        request = self.picam2.capture_request()

        filename = self.project.get_picture_filename(filename_postfix)
        if save:
            picture_path = self.project.path_pictures if output_path is None else output_path
            image_filename = f"{filename}.{self.project.image_format}"
            image_path = os.path.join(picture_path, image_filename)
            request.save("main", image_path)

        metadata = request.get_metadata()
        if save_metadata:
            metadata_path = self.project.path_metadata if output_path is None else output_path
            with open(os.path.join(metadata_path, f"{filename}-metadata.json"), "w") as f:
                json.dump(metadata, f, indent=2)

        request.release()

        self.picam2.stop()

        return metadata

    """
    Perform an autofocus cycle.
    :return: True if autofocus was successful, False otherwise.
    """
    def autofocus(self) -> bool:
        logging.info("Autofocus")

        def print_af_state(request):
            md = request.get_metadata()
            print(("Idle", "Scanning", "Success", "Fail")[md['AfState']], md.get('LensPosition'))

        self.picam2.pre_callback = print_af_state

        self.picam2.start()
        success = self.picam2.autofocus_cycle()
        self.picam2.stop()

        self.picam2.pre_callback = None

        logging.debug(f"Autofocus complete ({'success' if success else 'failed'})")

        return success

    """
    Find the mode with the biggest size (area)
    :param sensor_modes: List of sensor mode dictionaries.
    :return: Sensor mode dictionary with the largest size.
    """
    @staticmethod
    def get_largest_mode(sensor_modes) -> dict:
        sensor_modes = filter(lambda m: m['size'][0] != 1920, sensor_modes)
        return max(sensor_modes, key=lambda m: m['size'][0] * m['size'][1])

    """ 
    Find the mode with the smallest size (area)
    :param sensor_modes: List of sensor mode dictionaries.
    :return: Sensor mode dictionary with the smallest size.
    """
    @staticmethod
    def get_smallest_mode(sensor_modes) -> dict:
        sensor_modes = filter(lambda m: m['size'][0] != 1920, sensor_modes)
        return min(sensor_modes, key=lambda m: m['size'][0] * m['size'][1])

    """
    Get the picture mode
    :param smallest: If True, return the smallest mode.
    :param biggest: If True, return the biggest mode.
    :return: Sensor mode dictionary.
    """
    def get_picture_mode(self, smallest: bool = False, biggest: bool = True) -> dict:
        logging.getLogger("picamera2").setLevel(logging.WARNING)
        sensor_modes = self.picam2.sensor_modes
        logging.getLogger("picamera2").setLevel(logging.INFO)

        if biggest:
            return self.get_largest_mode(sensor_modes)
        elif smallest:
            return self.get_smallest_mode(sensor_modes)
        else:
            raise ValueError("Either smallest or biggest must be True")

    """
    Get a central square focus area for the given mode.
    :param mode: Camera mode dictionary.
    :return: Crop tuple (x, y, width, height) for central square focus area.
    """
    @staticmethod
    def get_central_focus_area(mode) -> tuple:
        # Assuming the mode has a 'size' attribute with (width, height)
        width, height = mode['size']
        # crop_limits is expected to be a tuple (x, y, width, height)
        crop_limits = mode['crop_limits']

        min_x_crop = int((crop_limits[2] - width) / 2)
        # print("min_x_crop", min_x_crop)
        min_y_crop = int((crop_limits[3] - height) / 2)
        # print("min_y_crop", min_y_crop)

        square_x_crop = int(min_x_crop + (width - height) / 2)

        crop_tuple = (square_x_crop, min_y_crop, height, height)

        # print("crop tuple", crop_tuple)

        assert (crop_tuple[0] * 2 + crop_tuple[2] == crop_limits[2]), "Crop width different than sensor limits"
        assert (crop_tuple[1] * 2 + crop_tuple[3] == crop_limits[3]), "Crop height different than sensor limits"
        assert (crop_tuple[2] == crop_tuple[3]), "Crop must be square"

        return crop_tuple

    """
    Close the camera and release resources.
    """
    def close(self):
        # close underlying device
        try:
            self.picam2.close()
        except Exception as e:
            logging.error("picam2.close() exception", exc_info=True)