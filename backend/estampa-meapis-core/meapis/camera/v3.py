import libcamera

from camera import Camera


class V3(Camera):
    def __init__(self, project):
        super().__init__(project, 1)

    def add_custom_camera_config(self, config):
        config["transform"] = libcamera.Transform(hflip=1, vflip=1)