from camera import Camera


class Owlsight(Camera):
    def __init__(self, project):
        super().__init__(project, 0)

    def add_custom_camera_config(self, config):
        config["controls"]["ExposureValue"] = -0.66  # Reduce exposure by 0.66 EV
