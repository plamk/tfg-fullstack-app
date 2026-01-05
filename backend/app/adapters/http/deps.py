from fastapi import Request
from app.application.ports.runner_port import RunnerPort

def get_runner(request: Request) -> RunnerPort:
    return request.app.state.runner