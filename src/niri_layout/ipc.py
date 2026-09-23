import json
import selectors
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


def run_niri_action(action: str | Sequence[str], *, runner=subprocess.run, **kwargs):
    command = niri_action(action) if isinstance(action, str) else [str(part) for part in action]
    result = runner(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        stderr = (result.stderr or "").strip() or "unknown error"
        stdout = (result.stdout or "").strip()
        detail = stdout if stdout else stderr
        raise NiriIPCError(f"niri action failed: {detail}")
    return result


class _EventStreamReader:
    def __init__(self, process):
        self._process = process
        self.cmd = list(getattr(process, "cmd", []))
        self.stdout = getattr(process, "stdout", None)
        self.stderr = getattr(process, "stderr", None)

    def readline(self, timeout: float | None = None):
        if self.stdout is None:
            return ""
        if timeout is not None and timeout <= 0:
            return ""
        if timeout is not None:
            selector = selectors.DefaultSelector()
            try:
                selector.register(self.stdout, selectors.EVENT_READ)
                if not selector.select(timeout):
                    return ""
            finally:
                selector.close()
        return self.stdout.readline()

    def close(self):
        if self.stdout is not None:
            try:
                self.stdout.close()
            except Exception:
                pass
        if self.stderr is not None:
            try:
                self.stderr.close()
            except Exception:
                pass

    def terminate(self):
        try:
            self._process.terminate()
        except Exception:
            pass

    def kill(self):
        try:
            self._process.kill()
        except Exception:
            pass


def start_event_stream(*, runner=subprocess.Popen, command: Sequence[str] | None = None):
    cmd = list(command or ["niri", "msg", "--json", "event-stream"])
    process = runner(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    process.cmd = cmd
    return _EventStreamReader(process)


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
