import os

def get_bench_dir(bench_name: str, bench_dirs: list) -> str:
    for bench_dir in bench_dirs:
        dir_bench_name = os.path.basename(
            os.path.dirname(
                os.path.dirname(bench_dir)))
        if dir_bench_name == bench_name:
            return bench_dir
    return ""
