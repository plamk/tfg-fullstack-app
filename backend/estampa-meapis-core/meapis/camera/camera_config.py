import logging

from libcamera import controls, Rectangle  # type: ignore


class CameraConfig:

    """
    Class to create and manage camera configurations for picture taking and setup.
    :param camera: Camera instance to associate with this configuration.
    """
    def __init__(self, camera):
        self.camera = camera

        self.picam2 = camera.picam2
        self.config = None

    """
    Get the picture mode from the camera.
    :param smallest: If True, return the smallest picture mode.
    :param biggest: If True, return the biggest picture mode.
    :return: Picture mode dictionary.
    """
    def _get_picture_mode(self, smallest: bool = False, biggest: bool = True):
        if self.camera and hasattr(self.camera, "get_picture_mode"):
            return self.camera.get_picture_mode(smallest, biggest)

        raise NotImplementedError

    """
    Create the base camera configuration used in both picture taking and setup.
    :param smallest: If True, use the smallest picture mode.
    :param biggest: If True, use the biggest picture mode.
    :return: Base configuration dictionary.
    """
    def create_base_config(self, smallest: bool = False, biggest: bool = True) -> dict:
        if self.camera.num == 1:
            smallest = False
            biggest = True

        # Create and return a base still configuration dict (does not set controls).
        mode = self._get_picture_mode(smallest=smallest, biggest=biggest)

        cfg = self.picam2.create_still_configuration(
            sensor={'output_size': mode['size'], 'bit_depth': mode.get('bit_depth')},
            main={'size': mode['size']},
        )

        cfg.setdefault("controls", {})

        # cfg["controls"]["AeFlickerMode"] = controls.AeFlickerModeEnum.Manual
        # cfg["controls"]["AeFlickerPeriod"] = 10

        cfg["controls"]["AeExposureMode"] = controls.AeExposureModeEnum.Long
        cfg["controls"]["NoiseReductionMode"] = controls.draft.NoiseReductionModeEnum.Off
        cfg["controls"]["Sharpness"] = 4.0

        # Allow owner camera to add custom configuration
        if self.camera and hasattr(self.camera, 'add_custom_camera_config'):
            try:
                self.camera.add_custom_camera_config(cfg)
            except:
                # Keep config creation robust; logging by caller
                pass

        return cfg

    """ 
    Create the picture taking configuration.
    - Auto exposure disabled with fixed exposure time and gain.
    - Auto focus disabled (manual focus).
    - Auto white balance disabled with custom colour gains.
    """
    def create_picture_config(self):
        """Build a picture (still) configuration and store it in `self.config`.
        Returns self for chaining or inspection."""
        cfg = self.create_base_config(smallest=False, biggest=True)

        cfg["controls"]["AeEnable"] = False
        cfg["controls"]["ExposureTime"] = 10000
        cfg["controls"]["AnalogueGain"] = 1.0

        cfg["controls"]["AfMode"] = controls.AfModeEnum.Manual

        self.set_manual_balanced_wb(cfg)

        self.config = cfg
        return self

    """
    Create the focus configuration.
    - Auto focus enabled (auto mode).
    - Auto white balance enabled.
    - Focus area set to central square region of the sensor.
    """
    def create_focus_config(self):
        cfg = self.create_base_config(smallest=True, biggest=False)

        cfg["controls"]["AfMode"] = controls.AfModeEnum.Auto
        cfg["controls"]["AfRange"] = controls.AfRangeEnum.Macro
        cfg["controls"]["AfMetering"] = controls.AfMeteringEnum.Windows
        cfg["controls"]["AfSpeed"] = controls.AfSpeedEnum.Normal

        cfg["controls"]["AwbEnable"] = True
        cfg["controls"]["AwbMode"] = controls.AwbModeEnum.Auto

        self.set_central_window(cfg)

        self.config = cfg
        return self

    """
    Create the exposure configuration.
    - Auto exposure enabled with highlight constraint mode.
    - Manual focus enabled.
    - Custom white balance enabled.
    - Focus area set to central square region of the sensor.
    """
    def create_exposure_config(self):
        cfg = self.create_base_config(smallest=False, biggest=True)

        cfg["controls"]["AeEnable"] = True
        cfg["controls"]["AeConstraintMode"] = controls.AeConstraintModeEnum.Highlight
        cfg["controls"]["AeMeteringMode"] = controls.AeMeteringModeEnum.Matrix
        cfg["controls"]["AfMetering"] = controls.AfMeteringEnum.Windows

        cfg["controls"]["AfMode"] = controls.AfModeEnum.Manual

        self.set_central_window(cfg)

        self.set_manual_balanced_wb(cfg)

        self.config = cfg
        return self

    """
    Set manual balanced white balance in a configuration.
    :param cfg: Configuration dict to modify.
    """
    @staticmethod
    def set_manual_balanced_wb(cfg):
        cfg["controls"]["AwbEnable"] = False
        cfg["controls"]["AwbMode"] = controls.AwbModeEnum.Custom
        cfg["controls"]["ColourGains"] = [1, 1]

    """
    Set the area to a central square region of the sensor.
    :param cfg: Configuration dict to modify.
    """
    def set_central_window(self, cfg):
        mode = self.camera.get_picture_mode()
        focus_crop = self.camera.get_central_focus_area(mode)
        cfg["controls"]["AfWindows"] = [focus_crop]

    """
    Set a control value in a configuration.
    :param control: Control name as string.
    :param value: Value to set for the control.
    """
    def set_control(self, control, value) -> None:
        if self.config is None:
            raise RuntimeError("Config not built yet; call create_picture_config() or create_setup_config() first")
        self.config.setdefault('controls', {})[control] = value

    """
    Get a control value from a configuration.
    :param control: Control name as string.
    :return: Value of the control, or None if not set.
    """
    def get_control(self, control):
        if self.config is None:
            raise RuntimeError("Config not built yet; call create_picture_config() or create_setup_config() first")
        return self.config.get('controls', {}).get(control, None)

    """
    Convenience: allow access to the underlying dict via property
    """
    @property
    def dict(self):
        return self.config

