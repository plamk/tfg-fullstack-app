import datetime
import logging
import os

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.background import BackgroundScheduler

from ..project import Project
from ..tasks.picture_taking import PictureTakingTask
from .file_monitor import FileMonitor


class ProjectRunner:
    def __init__(self, light):
        self.light = light

        self.curr_project = None
        self.camera_controller = None

        self.curr_project_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", "projects", "current.txt")

        # self.curr_project_monitor = FileMonitor(self.curr_project_file, on_change=self.current_project_change)
        # self.curr_project_monitor.start()

        self.scheduler = BackgroundScheduler()

        with open(self.curr_project_file, "r") as f:
            project_name = f.read().strip()

        if project_name and project_name.strip() != "":
            logging.info("Starting initial project: %s", project_name)
            self.start_project(project_name)
        else:
            logging.info("No initial project to start")

    def start_project(self, project_name):
        from meapis.camera.camera_controller import CameraController

        self.curr_project = Project(project_name)
        self.camera_controller = CameraController(self.curr_project, self.light)

        task = PictureTakingTask(self.camera_controller)

        self.scheduler.add_job(task.execute, 'interval', seconds=self.curr_project.interval, id='picture_taking_task', next_run_time=datetime.datetime.now())
        self.scheduler.start()

    def stop_project(self):
        if self.scheduler and self.scheduler.running:
            try:
                self.scheduler.remove_job('picture_taking_task')
                self.camera_controller.stop()
                logging.info("Removed job 'picture_taking_task'")
            except JobLookupError:
                logging.info("Job 'picture_taking_task' not found")

        self.curr_project = None

    def shutdown(self):
        # self.curr_project_monitor.stop()
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()

        if self.camera_controller:
            self.camera_controller.close()

    def capture_now(self) -> dict:
        if not self.camera_controller:
            raise RuntimeError("No hay proyecto activo")

        return self.camera_controller.take_picture()



    # def current_project_change(self, event):
    #     print(event)
    #
    #     new_project_name = None
    #     if not os.path.isfile(self.curr_project_file):
    #         logging.info("Current project file deleted")
    #     else:
    #         with open(self.curr_project_file, "r") as f:
    #             new_project_name = f.read().strip()
    #
    #         logging.info("Current project changed to: %s", new_project_name)
    #
    #     print("new_project_name", new_project_name)
    #     print("self.curr_project", self.curr_project.name if self.curr_project else None)
    #
    #     if self.curr_project is not None and self.curr_project.name != new_project_name:
    #         logging.info("Stopping current project: %s", self.curr_project.name)
    #         self.stop_project()
    #
    #     if new_project_name is not None and new_project_name != "" and (self.curr_project is None or self.curr_project.name != new_project_name):
    #         logging.info("Starting new project: %s", new_project_name)
    #         self.start_project(new_project_name)
