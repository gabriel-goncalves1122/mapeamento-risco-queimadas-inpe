import subprocess
import threading
import time
from datetime import datetime

class DockerSampler:
    def __init__(self, enabled, interval_seconds, containers):
        self.enabled = enabled
        self.interval_seconds = interval_seconds
        self.containers = list(containers)
        self.rows = []
        self._stop_event = threading.Event()
        self._thread = None
        self.current_concurrency = None

    def set_concurrency(self, concurrency):
        self.current_concurrency = concurrency

    def start(self):
        if not self.enabled:
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.enabled:
            return
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=max(self.interval_seconds + 1, 2))

    def _run(self):
        while not self._stop_event.is_set():
            self.rows.extend(coletar_docker_stats(self.containers, self.current_concurrency))
            self._stop_event.wait(self.interval_seconds)

def coletar_docker_stats(containers, concurrency=None):
    timestamp = datetime.now().isoformat(timespec="seconds")
    cmd = [
        "docker",
        "stats",
        "--no-stream",
        "--format",
        "{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}},{{.NetIO}},{{.BlockIO}}",
        *containers,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, check=False)
    except Exception as exc:
        return [
            {
                "timestamp": timestamp,
                "concurrency": concurrency,
                "container": "docker",
                "status": "ERRO",
                "erro": str(exc),
            }
        ]

    if result.returncode != 0:
        return [
            {
                "timestamp": timestamp,
                "concurrency": concurrency,
                "container": "docker",
                "status": "ERRO",
                "erro": result.stderr.strip(),
            }
        ]

    rows = []
    for line in result.stdout.splitlines():
        partes = line.split(",", 5)
        if len(partes) != 6:
            continue
        container, cpu, mem_usage, mem_percent, net_io, block_io = partes
        rows.append(
            {
                "timestamp": timestamp,
                "concurrency": concurrency,
                "container": container,
                "status": "OK",
                "cpu_percent": cpu.replace("%", "").strip(),
                "mem_usage": mem_usage.strip(),
                "mem_percent": mem_percent.replace("%", "").strip(),
                "net_io": net_io.strip(),
                "block_io": block_io.strip(),
                "erro": "",
            }
        )
    return rows

