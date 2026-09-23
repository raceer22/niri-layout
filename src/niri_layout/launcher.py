from __future__ import annotations

import subprocess
from collections.abc import Sequence
from typing import Any


def launch_process(command: Sequence[str] | str, *, runner=subprocess.Popen, **kwargs: Any):
    if isinstance(command, str):
        tokens = [command]
    else:
        tokens = [str(part) for part in command]
    if not tokens:
        raise ValueError("launch command must not be empty")
    shell = kwargs.pop("shell", False)
    return runner(tokens, shell=shell, **kwargs)
