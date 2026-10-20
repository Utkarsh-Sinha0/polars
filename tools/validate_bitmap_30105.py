import os
import shutil
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "crates/polars-arrow/src/bitmap/immutable.rs"
BASE = "04e0a7e625288e41dadf837992553b02d30380db"


def run_rust():
    harness = ROOT / ".validation-arrow"
    (harness / "tests").mkdir(parents=True, exist_ok=True)
    (harness / "Cargo.toml").write_text(
        '[package]\nname = "bitmap-offset-validation"\nversion = "0.0.0"\n'
        'edition = "2024"\n[workspace]\n[dependencies]\n'
        'polars-arrow = { path = "../crates/polars-arrow", default-features = false }\n'
        'proptest = { version = "1.6", default-features = false, features = ["std"] }\n',
        encoding="utf-8",
    )
    (harness / "tests/bitmap.rs").write_text(
        '#[path = "../../crates/polars/tests/it/arrow/bitmap/mod.rs"]\nmod bitmap;\n',
        encoding="utf-8",
    )
    shutil.copyfile(ROOT / "Cargo.lock", harness / "Cargo.lock")
    command = ["cargo", "test", "--manifest-path", str(harness / "Cargo.toml"),
               "--test", "bitmap"]
    patched = SOURCE.read_bytes()
    subprocess.run(["git", "fetch", "--depth=1", "origin", BASE], cwd=ROOT, check=True)
    baseline = subprocess.check_output(["git", "show", BASE + ":" + SOURCE.relative_to(ROOT).as_posix()],
                                       cwd=ROOT)
    try:
        SOURCE.write_bytes(baseline)
        red = subprocess.run(command + ["bitmap::immutable::"], cwd=ROOT,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(red.stdout, flush=True)
        (ROOT / "bitmap-red.log").write_text(red.stdout, encoding="utf-8")
        assert red.returncode != 0, "Baseline unexpectedly passed"
        for name in ["into_mut_sliced", "make_mut_sliced"]:
            assert f"test bitmap::immutable::{name} ... FAILED" in red.stdout, (
                "Expected assertion failure missing: " + name
            )
        assert "test result: FAILED." in red.stdout, "Baseline did not run tests"
    finally:
        SOURCE.write_bytes(patched)
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    os.chdir(ROOT)
    run_rust()
