import json
import subprocess

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
