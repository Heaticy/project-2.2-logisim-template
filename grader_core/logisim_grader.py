#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LOGISIM_JAR = ROOT / "logisim-evolution-4.1.0-all.jar"
DEFAULT_CIRC_DIR = ROOT / "testing" / "circ_files"
DEFAULT_REFERENCE_DIR = ROOT / "testing" / "reference_output"
DEFAULT_STUDENT_DIR = ROOT / "testing" / "student_output"
DEFAULT_STUDENT_UNMASKED_DIR = ROOT / "testing" / "student_output_unmasked"
RUN_CONTEXT = os.environ.get("P22_RUN_CONTEXT", "unknown")

TABLE_HEADERS = [
    "count",
    "PC",
    "memReadData",
    "memAddress",
    "memWriteEnable",
    "memWriteData",
    "memByteEnable3",
    "memByteEnable2",
    "memByteEnable1",
    "memByteEnable0",
    "regWriteEnable",
    "regWriteAddress",
    "regWriteData",
]

FIELD_WIDTHS = {
    "count": 7,
    "PC": 32,
    "memReadData": 32,
    "memAddress": 32,
    "memWriteEnable": 1,
    "memWriteData": 32,
    "memByteEnable3": 1,
    "memByteEnable2": 1,
    "memByteEnable1": 1,
    "memByteEnable0": 1,
    "regWriteEnable": 1,
    "regWriteAddress": 5,
    "regWriteData": 32,
}

COL_COUNT = 0
COL_PC = 1
COL_MEM_READ_DATA = 2
COL_MEM_ADDRESS = 3
COL_MEM_WRITE_ENABLE = 4
COL_MEM_WRITE_DATA = 5
COL_MEM_BYTE_ENABLE3 = 6
COL_MEM_BYTE_ENABLE2 = 7
COL_MEM_BYTE_ENABLE1 = 8
COL_MEM_BYTE_ENABLE0 = 9
COL_REG_WRITE_ENABLE = 10
COL_REG_WRITE_ADDRESS = 11
COL_REG_WRITE_DATA = 12


def resolve_logisim_command() -> list[str]:
    if RUN_CONTEXT == "autograder":
        java_cmd = shutil.which("java")
        if java_cmd and LOGISIM_JAR.is_file():
            return [java_cmd, "-jar", str(LOGISIM_JAR)]
        raise RuntimeError(
            "Autograder mode requires java and the bundled Logisim JAR. "
            f"Expected: java -jar {LOGISIM_JAR}. Current run context: {RUN_CONTEXT}"
        )

    logisim_cmd = shutil.which("logisim-evolution")
    if logisim_cmd:
        return [logisim_cmd]

    opt_cmd = Path("/opt/logisim-evolution/bin/logisim-evolution")
    if opt_cmd.is_file():
        return [str(opt_cmd)]

    java_cmd = shutil.which("java")
    if java_cmd and LOGISIM_JAR.is_file():
        return [java_cmd, "-jar", str(LOGISIM_JAR)]

    raise RuntimeError(
        "Unable to find a usable Logisim executable. "
        "Tried: logisim-evolution, /opt/logisim-evolution/bin/logisim-evolution, "
        f"and java -jar {LOGISIM_JAR}. "
        f"Current run context: {RUN_CONTEXT}"
    )


class TestCase:
    def __init__(self, circfile: Path, tracefile: Path):
        self.circfile = Path(circfile)
        self.tracefile = Path(tracefile)

    def __call__(self, student_output_path: Path) -> tuple[bool, str]:
        student_output_path = Path(student_output_path)
        student_output_path.parent.mkdir(parents=True, exist_ok=True)
        logisim_cmd = resolve_logisim_command()

        proc = subprocess.Popen(
            [*logisim_cmd, "--tty", "table", str(self.circfile)],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        try:
            raw_stdout, raw_stderr = proc.communicate(timeout=30)
        finally:
            try:
                os.kill(proc.pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass

        if proc.returncode not in (0, None):
            stderr_text = raw_stderr.strip()
            if stderr_text:
                message = f"Logisim exited with code {proc.returncode}: {stderr_text}"
            else:
                message = f"Logisim exited with code {proc.returncode}"
            student_output_path.write_text(build_debug_output([]), encoding="utf-8")
            return False, message

        if RUN_CONTEXT == "student_local_test":
            unmasked_output_path = DEFAULT_STUDENT_UNMASKED_DIR / student_output_path.name
            unmasked_output_path.parent.mkdir(parents=True, exist_ok=True)
            unmasked_output_path.write_text(
                build_debug_output(raw_table_lines(raw_stdout)),
                encoding="utf-8",
            )

        with self.tracefile.open("r", encoding="utf-8") as reference:
            passed, student_lines = compare_with_mask(raw_stdout, reference)

        student_output_path.write_text(build_debug_output(student_lines), encoding="utf-8")
        return (passed, "Matched expected output" if passed else "Did not match expected output")


def raw_table_lines(raw_stdout: str) -> list[str]:
    raw_lines = [line.rstrip("\r\n") for line in raw_stdout.splitlines() if line.strip()]
    if raw_lines:
        raw_lines = raw_lines[:-1]
    return raw_lines


def compare_with_mask(raw_stdout: str, reference_out) -> tuple[bool, list[str]]:
    reference_lines = [line.rstrip("\r\n") for line in reference_out]
    if reference_lines and reference_lines[0] == ",".join(TABLE_HEADERS):
        reference_data_lines = reference_lines[1:]
    else:
        reference_data_lines = reference_lines

    raw_student_lines = raw_table_lines(raw_stdout)

    reference_grading_lines: list[str] = []
    student_debug_lines: list[str] = []
    for student_line, reference_csv_line in zip(raw_student_lines, reference_data_lines):
        student_mask = build_dynamic_mask_line(student_line)
        reference_mask = build_dynamic_mask_line(csv_line_to_table_line(reference_csv_line))
        student_debug_lines.append(apply_mask_for_debug(student_line, student_mask))
        reference_grading_lines.append(
            to_csv_line(apply_mask_for_debug(csv_line_to_table_line(reference_csv_line), reference_mask))
        )

    expected_student_lines = [to_csv_line(line) for line in student_debug_lines]
    passed = expected_student_lines == reference_grading_lines
    return passed, student_debug_lines


def build_dynamic_mask_line(line: str) -> str:
    cols = parse_raw_columns(line)
    keep_cols = selected_columns(cols)
    ranges = char_ranges_for_columns(line)

    mask = ["0"] * len(line)
    for col_idx, (start, end) in enumerate(ranges):
        fill = "1" if col_idx in keep_cols else "0"
        for i in range(start, end):
            mask[i] = fill

    for idx, ch in enumerate(line):
        if ch == "\t":
            mask[idx] = "1"
    return "".join(mask)


def csv_line_to_table_line(line: str) -> str:
    return "\t".join(line.split(","))


def parse_raw_columns(line: str) -> list[str]:
    cols = line.split("\t")
    if len(cols) < len(TABLE_HEADERS):
        cols = cols + [""] * (len(TABLE_HEADERS) - len(cols))
    elif len(cols) > len(TABLE_HEADERS):
        cols = cols[: len(TABLE_HEADERS)]
    return [value.replace(" ", "") for value in cols]


def char_ranges_for_columns(line: str) -> list[tuple[int, int]]:
    cols = line.split("\t")
    ranges: list[tuple[int, int]] = []
    cursor = 0
    for idx, col in enumerate(cols[: len(TABLE_HEADERS)]):
        start = cursor
        end = start + len(col)
        ranges.append((start, end))
        cursor = end
        if idx != len(cols) - 1:
            cursor += 1
    return ranges


def selected_columns(cols: list[str]) -> set[int]:
    keep = {COL_COUNT, COL_PC, COL_REG_WRITE_ENABLE, COL_MEM_WRITE_ENABLE}

    reg_write_enable = enabled(cols, COL_REG_WRITE_ENABLE)
    mem_write_enable = enabled(cols, COL_MEM_WRITE_ENABLE)

    if reg_write_enable:
        keep.update({COL_REG_WRITE_ADDRESS, COL_REG_WRITE_DATA})

    if mem_write_enable:
        keep.update(
            {
                COL_MEM_ADDRESS,
                COL_MEM_WRITE_DATA,
                COL_MEM_BYTE_ENABLE3,
                COL_MEM_BYTE_ENABLE2,
                COL_MEM_BYTE_ENABLE1,
                COL_MEM_BYTE_ENABLE0,
            }
        )

    return keep


def enabled(cols: list[str], idx: int) -> bool:
    return idx < len(cols) and cols[idx].strip() == "1"


def apply_mask_for_debug(line: str, mask_line: str) -> str:
    masked_chars: list[str] = []
    for i, char in enumerate(line):
        keep = i < len(mask_line) and mask_line[i] == "1"
        if keep:
            masked_chars.append(char)
        elif char in {"\t", " "}:
            masked_chars.append(char)
        else:
            masked_chars.append("x")
    return "".join(masked_chars)


def build_debug_output(student_lines: list[str]) -> str:
    header = ",".join(TABLE_HEADERS)
    if not student_lines:
        return header + "\n"
    csv_lines = [to_csv_line(line) for line in student_lines]
    return header + "\n" + "\n".join(csv_lines) + "\n"


def normalize_field(header: str, value: str) -> str:
    compact = value.replace(" ", "")
    width = FIELD_WIDTHS[header]
    if compact and set(compact) <= {"x", "X"}:
        return "x" * width
    return compact


def to_csv_line(line: str) -> str:
    cols = line.split("\t")
    if len(cols) < len(TABLE_HEADERS):
        cols = cols + [""] * (len(TABLE_HEADERS) - len(cols))
    elif len(cols) > len(TABLE_HEADERS):
        cols = cols[: len(TABLE_HEADERS)]
    normalized = [normalize_field(header, value) for header, value in zip(TABLE_HEADERS, cols)]
    return ",".join(normalized)


def run_one(case_name: str) -> int:
    circfile = DEFAULT_CIRC_DIR / f"{case_name}.circ"
    tracefile = DEFAULT_REFERENCE_DIR / f"{case_name}.csv"
    student_output = DEFAULT_STUDENT_DIR / f"{case_name}.csv"

    testcase = TestCase(circfile, tracefile)
    passed, message = testcase(student_output)
    print(f"{case_name}: {'PASSED' if passed else 'FAILED'} ({message})")
    return 0 if passed else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one Logisim testcase and emit masked student_output with a header row."
    )
    parser.add_argument(
        "case_name",
        help="Base testcase name without extension, e.g. p22_localtest",
    )
    args = parser.parse_args()
    return run_one(args.case_name)


if __name__ == "__main__":
    raise SystemExit(main())
