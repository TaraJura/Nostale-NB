import platform
import subprocess
from re import search
from .api import PhoenixApi

_ports: list[int] = []


def find_all_api_ports() -> list[int]:
    """Find all ports of the current bot windows."""
    _ports.clear()
    if platform.system() == "Windows":
        from win32gui import EnumWindows
        EnumWindows(_enum_windows_callback, 0)
    else:
        _find_ports_via_powershell()
        if not _ports:
            _find_ports_via_netstat()
    return _ports.copy()


def _find_ports_via_powershell():
    """Find Phoenix Bot ports using PowerShell window titles (for WSL environments)."""
    ps_script = (
        "Get-Process | Where-Object {$_.MainWindowTitle -like '*- Phoenix Bot*'} "
        "| Select-Object -ExpandProperty MainWindowTitle"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if "- Phoenix Bot" in line:
                match = search(r"Bot:\d+ (\d+)", line)
                if match:
                    _ports.append(int(match.group(1)))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _find_ports_via_netstat():
    """Fallback: find Phoenix Bot ports via netstat by checking which NostaleClientX
    processes have listening TCP ports in the 50000+ range."""
    ps_script = (
        "Get-NetTCPConnection -State Listen "
        "| Where-Object {$_.LocalPort -ge 50000 -and $_.LocalPort -le 65535} "
        "| ForEach-Object { "
        "  $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; "
        "  if ($proc.ProcessName -eq 'NostaleClientX') { $_.LocalPort } "
        "}"
    )
    try:
        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=15
        )
        for line in result.stdout.strip().splitlines():
            line = line.strip()
            if line.isdigit():
                _ports.append(int(line))
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def create_api_from_port(port: int) -> PhoenixApi:
    """Create an API instance by connecting directly to a known port."""
    return PhoenixApi(port)


def create_api_from_name(character_name: str) -> PhoenixApi:
    """
    Create an instance of the API class from the character's name.

    Raises:
        RuntimeError: If no bot with that name is found or no bots are running.
    """
    ports = find_all_api_ports()

    if len(ports) == 0:
        raise RuntimeError("No bot windows found.")

    for port in ports:
        try:
            api = PhoenixApi(port)
            player_obj_manager = api.player_obj_manager.get_player_obj_manager()
            name = player_obj_manager["player"]["name"]

            if name == character_name:
                return api
        except Exception:
            continue

    raise RuntimeError(f"Could not find bot with character name: {character_name}")


def _enum_windows_callback(hwnd, lparam) -> bool:
    """Callback function to enumerate windows and check if it is a bot window."""
    from win32gui import GetWindowText
    window_title = GetWindowText(hwnd)

    if "- Phoenix Bot" in window_title:
        match = search(r"Bot:\d+ (\d+)", window_title)
        if match:
            port = int(match.group(1))
            _ports.append(port)

    return True
