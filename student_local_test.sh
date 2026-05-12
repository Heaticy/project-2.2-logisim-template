#!/bin/sh
set -eu

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"

if [ "$#" -gt 1 ]; then
  echo "Usage: ./student_local_test.sh [relative-circuit-file]" >&2
  exit 1
fi

SOURCE_CIRC_REL="${1:-proj_2_2_top.circ}"
SOURCE_CIRC="$SCRIPT_DIR/$SOURCE_CIRC_REL"
TARGET_CIRC="$SCRIPT_DIR/testing/circ_files/proj_2_2_top.circ"
export P22_RUN_CONTEXT="student_local_test"

cd "$SCRIPT_DIR"

case "$SOURCE_CIRC_REL" in
  /*)
    echo "Circuit file path must be relative to project-2.2-logisim: $SOURCE_CIRC_REL" >&2
    exit 1
    ;;
esac

if [ ! -f "$SOURCE_CIRC" ]; then
  echo "Missing circuit file: $SOURCE_CIRC" >&2
  echo "Put your student circuit at project-2.2-logisim/proj_2_2_top.circ, or pass a relative circuit file path." >&2
  exit 1
fi

if command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
elif command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
else
  echo "Python was not found. Install Python 3 and ensure \`python\` or \`python3\` is available in PATH." >&2
  echo "See README.md for setup instructions." >&2
  exit 1
fi

mkdir -p testing/circ_files
mkdir -p testing/student_output
mkdir -p testing/student_output_unmasked
cp "$SOURCE_CIRC" "$TARGET_CIRC"
rm -f testing/student_output/*.csv 2>/dev/null || true
rm -f testing/student_output_unmasked/*.csv 2>/dev/null || true

"$PYTHON_CMD" -m grader_core.grader
