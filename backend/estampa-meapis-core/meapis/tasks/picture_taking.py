class PictureTakingTask:
    def __init__(self, camera_controller):
        self.camera_controller = camera_controller

    def execute(self):
        print(f"Taking picture.")
        self.camera_controller.take_picture()
