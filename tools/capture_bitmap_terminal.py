import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'terminal-evidence'
TITLE = 'Polars development terminal - GitHub Actions runner - issue 30105'
SCRIPT = r'''#!/usr/bin/env bash
set -euo pipefail
cd "$GITHUB_WORKSPACE"
source .venv/bin/activate
run_step() {
    phase="$1"
    shift
    clear
    printf 'Polars development terminal | GitHub Actions runner | issue #30105\n'
    printf 'Candidate: 95260c56c1eb30b46a60da4628428206bc5db092\n'
    printf 'UTC time: '; date -u --iso-8601=seconds
    printf '\n$ '; printf '%q ' "$@"; printf '\n\n'
    set +e
    "$@" 2>&1 | tee "terminal-evidence/$phase.log"
    status=${PIPESTATUS[0]}
    set -e
    printf '\nCommand exit status: %s\n' "$status"
    printf '%s' "$status" > "terminal-evidence/$phase.done"
    while [[ ! -f "terminal-evidence/$phase.continue" ]]; do sleep 0.2; done
    return "$status"
}
run_step 01-environment bash -c 'uname -a; free -h; python --version; rustc --version; printf "Checkout commit: "; git rev-parse HEAD; printf "Repository: "; git remote get-url origin'
run_step 03-full-suite make -C py-polars test 'PYTEST_ARGS=-n 2 --junitxml=../terminal-full-suite.xml'
run_step 04-focused bash -e -c 'cd py-polars; ../.venv/bin/pytest -v tests/unit/series/test_extend.py tests/unit/series/test_scatter.py tests/unit/dataframe/test_extend.py; ../.venv/bin/ruff check --no-fix tests/unit/series/test_extend.py tests/unit/series/test_scatter.py tests/unit/dataframe/test_extend.py; ../.venv/bin/ruff format --check tests/unit/series/test_extend.py tests/unit/series/test_scatter.py tests/unit/dataframe/test_extend.py'
run_step 05-rust-bitmap python tools/validate_bitmap_30105.py
'''


def capture(name):
    # Capture the actual X desktop, including the window decoration. No crop or edits.
    time.sleep(0.7)
    subprocess.run(['scrot', '--overwrite', str(OUT / (name + '.png'))], check=True)


def main():
    os.chdir(ROOT)
    OUT.mkdir(exist_ok=True)
    script = OUT / 'run-tests.sh'
    script.write_text(SCRIPT, encoding='utf-8')
    desktop = subprocess.Popen(['openbox'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    terminal = subprocess.Popen([
        'xterm', '-hold', '-title', TITLE, '-fa', 'DejaVu Sans Mono', '-fs', '12',
        '-bg', '#ffffff', '-fg', '#111827', '-sb', '-sl', '2000',
        '-geometry', '170x46+8+8', '-e', 'bash', str(script),
    ])
    phases = ['01-environment', '03-full-suite', '04-focused', '05-rust-bitmap']
    results = {}
    build_captured = False
    deadline = time.monotonic() + 5100
    try:
        for _ in range(100):
            windows = subprocess.run(
                ['wmctrl', '-l'], text=True, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, check=False,
            )
            if TITLE in windows.stdout:
                subprocess.run(['wmctrl', '-r', TITLE, '-e', '0,30,30,1840,980'], check=True)
                break
            time.sleep(0.1)
        else:
            raise RuntimeError('The terminal window did not become ready')
        for phase in phases:
            done = OUT / (phase + '.done')
            while not done.exists():
                if time.monotonic() > deadline or terminal.poll() is not None:
                    raise RuntimeError('Terminal did not finish phase: ' + phase)
                log = OUT / '03-full-suite.log'
                if phase == '03-full-suite' and not build_captured and log.exists():
                    if 'Compiling ' in log.read_text(encoding='utf-8', errors='replace'):
                        capture('02-build-running')
                        build_captured = True
                time.sleep(0.25)
            status = int(done.read_text())
            results[phase] = status
            capture(phase)
            (OUT / (phase + '.continue')).touch()
            print(phase + ': exit status ' + str(status), flush=True)
            if status:
                raise RuntimeError('Test command failed in phase: ' + phase)
        (OUT / 'results.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    finally:
        terminal.terminate()
        desktop.terminate()


if __name__ == '__main__':
    main()
