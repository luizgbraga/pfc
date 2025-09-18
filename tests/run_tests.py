import json
import os
import resource
import sys
import threading
import time

import GPUtil
import psutil

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from main import generate_playbook

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


class ResourceMonitor(threading.Thread):
    def __init__(self, pid=None, interval=0.5):
        super().__init__()
        self.daemon = True
        self.pid = pid or os.getpid()
        self.interval = interval
        self.running = threading.Event()
        self.running.set()
        self.process = psutil.Process(self.pid)

        # Track max values
        self.max_cpu = 0.0
        self.max_per_cpu = []
        self.max_rss = 0
        self.max_mem_percent = 0.0
        self.max_threads = 0
        self.max_gpu_load = 0.0
        self.max_gpu_mem_used = 0.0

    def run(self):
        while self.running.is_set():
            try:
                cpu = self.process.cpu_percent(interval=None)
                per_cpu = psutil.cpu_percent(percpu=True)
                mem = self.process.memory_info()
                mem_percent = self.process.memory_percent()
                threads = self.process.num_threads()

                self.max_cpu = max(self.max_cpu, cpu)
                self.max_per_cpu = [
                    max(a, b) for a, b in zip(self.max_per_cpu or per_cpu, per_cpu)
                ]
                self.max_rss = max(self.max_rss, mem.rss)
                self.max_mem_percent = max(self.max_mem_percent, mem_percent)
                self.max_threads = max(self.max_threads, threads)

                try:
                    gpus = GPUtil.getGPUs()
                    for gpu in gpus:
                        self.max_gpu_load = max(self.max_gpu_load, gpu.load * 100)
                        self.max_gpu_mem_used = max(
                            self.max_gpu_mem_used, gpu.memoryUsed
                        )
                except Exception:
                    pass
            except psutil.NoSuchProcess:
                break

            time.sleep(self.interval)

    def stop(self):
        self.running.clear()


def run_with_mode(alert, output_file, graph_rag_enabled: bool):
    print(
        f"Generating playbook for {os.path.basename(output_file)} with graph_rag_enabled={graph_rag_enabled}"
    )
    start_time = time.time()
    usage_start = resource.getrusage(resource.RUSAGE_SELF)
    monitor = ResourceMonitor()
    monitor.start()

    generate_playbook(
        alert=json.dumps(alert),
        output_file=output_file,
        export=True,
        display=False,
        graph_rag_enabled=graph_rag_enabled,
    )

    monitor.stop()
    monitor.join()

    elapsed = time.time() - start_time
    usage_end = resource.getrusage(resource.RUSAGE_SELF)

    # Write resource usage
    resources_file = output_file.replace(".json", ".resources")
    with open(resources_file, "w") as rf:
        rf.write(f"Elapsed time (s): {elapsed:.2f}\n")
        rf.write(
            f"Max RSS delta (MB): {(usage_end.ru_maxrss - usage_start.ru_maxrss) / 1024:.2f}\n"
        )
        rf.write(
            f"User CPU time delta (s): {usage_end.ru_utime - usage_start.ru_utime:.2f}\n"
        )
        rf.write(
            f"System CPU time delta (s): {usage_end.ru_stime - usage_start.ru_stime:.2f}\n"
        )
        rf.write("\n--- Max observed during run ---\n")
        rf.write(f"Max CPU percent: {monitor.max_cpu:.1f}\n")
        rf.write(f"Max per-CPU percent: {monitor.max_per_cpu}\n")
        rf.write(f"Max RSS (MB): {monitor.max_rss / 1024 / 1024:.2f}\n")
        rf.write(f"Max memory percent: {monitor.max_mem_percent:.2f}\n")
        rf.write(f"Max threads: {monitor.max_threads}\n")
        rf.write(f"Max GPU load (%): {monitor.max_gpu_load:.1f}\n")
        rf.write(f"Max GPU memory used (MB): {monitor.max_gpu_mem_used:.1f}\n")


def main():
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    for log_filename in os.listdir(LOGS_DIR):
        log_path = os.path.join(LOGS_DIR, log_filename)
        if not os.path.isfile(log_path):
            continue
        with open(log_path, "r") as f:
            try:
                alert = json.load(f)
            except Exception as e:
                print(f"Failed to load {log_filename}: {e}")
                continue

        # Run with graph_rag_enabled True
        run_with_mode(
            alert,
            os.path.join(RESULTS_DIR, log_filename.replace(".json", "-enabled.json")),
            graph_rag_enabled=True,
        )

        # Run with graph_rag_enabled False
        run_with_mode(
            alert,
            os.path.join(RESULTS_DIR, log_filename.replace(".json", "-disabled.json")),
            graph_rag_enabled=False,
        )


if __name__ == "__main__":
    main()
