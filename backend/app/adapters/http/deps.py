from app.application.ports.runner_port import RunnerPort

def get_runner(request) -> RunnerPort:
    return request.app.state.runner