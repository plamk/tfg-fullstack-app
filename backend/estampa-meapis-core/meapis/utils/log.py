import io
import os
import logging
from datetime import datetime

import coloredlogs

import __main__


def setup_logging(level):
    logging.basicConfig(level=level)
    logging.getLogger("picamera2").setLevel(logging.INFO)
    logging.getLogger("dmaallocator").setLevel(logging.WARNING)

    datetime_str = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    main_filename = __main__.__file__.split("/")[-1].split(".")[0]
    log_file_name = f"{main_filename}-{datetime_str}.log"
    log_folder = "logs"
    os.makedirs(log_folder, exist_ok=True)
    log_path = os.path.join(log_folder, log_file_name)
    fh = logging.FileHandler(log_path, mode='w')
    logging.getLogger().addHandler(fh)
    logging.getLogger().handlers[1].setFormatter(logging.Formatter('%(asctime)s %(levelname)8s %(filename)24.24s %(message)s'))

    level_styles = {
        'trace': {
            'color': 'black',
            'bright': True
        },
        'debug': {
            'color': 'white'
        },
        'info': {
            'color': 'green'
        },
        'warning': {
            'color': 'yellow'
        },
        'error': {
            'color': 'red'
        },
        'critical': {
            'bold': True,
            'color': 'red'
        }
    }

    field_styles = dict(
        asctime=dict(color='white'),
        hostname=dict(color='magenta'),
        levelname=dict(color='white', bold=True),
        threadname=dict(color='blue', bold=True, faint=True),
        name=dict(color='blue'),
        filename=dict(color='blue'),
        programname=dict(color='cyan'),
        username=dict(color='yellow'),
    )

    coloredlogs.install(level=level, level_styles=level_styles, field_styles=field_styles, isatty=True,
                        fmt='%(asctime)s %(levelname)8s %(filename)24.24s %(message)s')


def print_to_string(*args, **kwargs):
    output = io.StringIO()
    print(*args, file=output, **kwargs)
    contents = output.getvalue()
    output.close()
    return contents
