import json
import shlex
import subprocess
from collections.abc import Sequence

from . import NiriIPCError, NiriIPCJSONError


def query_niri(query: str, *, runner=subprocess.run):
    """Query Niri's JSON IPC surface."""
    if not query or not str(query).strip():
        raise ValueError("Niri IPC query must be non-empty")

    cmd = ["niri", "msg", "--json", str(query)]
    result = runner(cmd, capture_output=True, text=True, check=False)

    if result.returncode != 0:
        stderr = (result.stderr or "").strip() or "unknown error"
        stdout = (result.stdout or "").strip()
        detail = stdout if stdout else stderr
        raise NiriIPCError(f"niri msg failed for {query!r}: {detail}")

    payload = (result.stdout or "").strip()
    try:
        return json.loads(payload or "null")
    except json.JSONDecodeError as exc:
        raise NiriIPCJSONError(f"Invalid JSON from niri msg {query!r}: {exc.msg}") from exc


def niri_action(action: str | Sequence[str]) -> list[str]:
    if isinstance(action, str):
        tokens = shlex.split(action)
    elif isinstance(action, Sequence) and not isinstance(action, (str, bytes)):
        tokens = [str(part) for part in action]
    else:
        raise TypeError("Niri action must be a string or sequence of strings")
    if not tokens:
        raise ValueError("Niri action must not be empty")
    return ["niri", "msg", "action", *tokens]


def start_event_stream(*, runner=subprocess.Popen, command: Sequence[str] | None = None):
    cmd = list(command or ["niri", "msg", "--json", "event-stream"])
    process = runner(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    process.cmd = cmd
    return process


def close_event_stream(process) -> bool:
    if process is None:
        return False
    try:
        process.terminate()
    except Exception:
        pass
    try:
        process.kill()
    except Exception:
        pass
    try:
        process.close()
    except Exception:
        pass
    stdout = getattr(process, "stdout", None)
    if stdout is not None:
        try:
            stdout.close()
        except Exception:
            pass
    stderr = getattr(process, "stderr", None)
    if stderr is not None:
        try:
            stderr.close()
        except Exception:
            pass
    return True
