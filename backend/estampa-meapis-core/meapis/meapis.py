import logging
import signal
import sys
import time

from camera.camera_config import CameraConfig
from camera.owlsight import Owlsight
from camera.v3 import V3
from project import Project
from utils.light import Light
from utils.log import setup_logging
from utils.project_runner import ProjectRunner

def test():
    project = Project("prova")

    camera = V3(project)
    # camera = Owlsight(project)

    config_picture = CameraConfig(camera).create_picture_config()
    config_focus = CameraConfig(camera).create_focus_config()
    config_exposure = CameraConfig(camera).create_exposure_config()

    camera.setup(config_focus)

    # Autofocus and take picture to get the correct focus setting
    focused = camera.autofocus()
    metadata = camera.take_picture(config_focus)
    # print(metadata)
    if focused:
        logging.info("Autofocus successful")
        config_exposure.set_control("LensPosition", metadata["LensPosition"])
        config_picture.set_control("LensPosition", metadata["LensPosition"])
    else:
        logging.warning("Autofocus failed")

    time.sleep(1)

    # Autoexposure and take picture to get the correct exposure setting
    metadata = camera.take_picture(config_exposure)
    logging.info("Autoexposure complete")
    config_picture.set_control("AnalogueGain", metadata["AnalogueGain"])
    config_picture.set_control("ExposureTime", metadata["ExposureTime"])

    time.sleep(1)

    # Take the final picture with the correct focus and exposure settings
    camera.take_picture(config_picture)


def main():
    setup_logging("DEBUG")
    logging.info("Starting")

    # test()

    project_runner = None

    light = Light()

    def shutdown(signum=None, frame=None):
        # perform cleanup here
        logging.info("Shutdown")

        try:
            if light and not light.is_closed:
                light.close()
        except Exception as e:
            logging.error(e)

        try:
            if project_runner is not None:
                project_runner.shutdown()
        except Exception as e:
            logging.error(e)

        sys.exit(0)  # raises SystemExit

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    # atexit.register(shutdown)

    try:
        project_runner = ProjectRunner(light)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # If no SIGINT handler installed this will run
        shutdown()
    except SystemExit:
        # Normal shutdown path
        pass


if __name__ == '__main__':
    main()
