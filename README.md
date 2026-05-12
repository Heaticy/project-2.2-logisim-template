# Local Testing Guide

This document explains how to run the local test for `project-2.2-logisim`.

## Environment Setup

You need Python 3 and Logisim Evolution.

The local test script supports both:

- `python`
- `python3`

For Logisim Evolution, follow the Lab 5 installation instructions:

- https://faculty.sist.shanghaitech.edu.cn/liust/courses/labs/Lab5.html

## How to Run Local Tests

Put your circuit here:

- `project-2.2-logisim/proj_2_2_top.circ`

The provided 2.1 reference circuit is also included:

- `project-2.2-logisim/proj_2_1_top_solution.circ`

You may reuse that 2.1 solution or replace it with your own 2.1 implementation when building your 2.2 circuit. The 2.2 solution/netlist file is for staff reference generation and is not the student template.

From the `project-2.2-logisim` directory, run:

```bash
bash ./student_local_test.sh
```

The script will:

- copy `proj_2_2_top.circ` into `testing/circ_files/`
- run the single local testcase `p22_localtest`
- write masked CSV output into `testing/student_output/p22_localtest.csv`

## How to Read the Output

The fixed column order is:

`count, PC, memReadData, memAddress, memWriteEnable, memWriteData, memByteEnable3, memByteEnable2, memByteEnable1, memByteEnable0, regWriteEnable, regWriteAddress, regWriteData`

Meaning of `x`:

- `x` means that field is intentionally not checked for that cycle.
- Your circuit may still drive any value there.
- `memReadData` is not graded directly. `lw` and `lb` correctness is checked through the later `regWriteData` value, and this testcase stores that loaded register value to memory for debugging.
- In every CSV, `memAddress`, `memWriteData`, and byte-enable columns are shown only when that row's own `memWriteEnable` is active; otherwise they are `x`.
- In every CSV, `regWriteAddress` and `regWriteData` are shown only when that row's own `regWriteEnable` is active; otherwise they are `x`.
- Load `memAddress` is not graded directly.

When reading local output, focus first on:

- whether `PC` changes correctly
- whether register writeback happens when expected
- whether memory write behavior matches the instruction
- whether load results and byte-lane behavior look correct

## Testcase Overview

The local testing flow uses one testcase:

- `p22_localtest`

Its corresponding assembly source is:

- `testcases/assembly/top_testbench_debug.s`

The testcase exercises the required Project 2.2 instructions together and writes debug observations into DMEM. It includes:

- `add`, `sub`, `and`, `slt`
- `addi`, `andi`, `slti`
- `lw`, `lb`
- `sw`, `sb`
- `beq`, `blt`
- `jal`, `jalr`
- `lui`, `auipc`

## `halt` Convention

The testcase ends with:

- `.word 0x00100073`

In this project, that machine word is treated as the testcase `halt` marker.

Important notes:

- your hardware does not need to implement any special `halt` handling
- you do not need to stop the CPU for this instruction inside your circuit
- the local testing script and grading script directly drop the output row for this final `halt` instruction
- that row is not checked during comparison

## Common Problems

### `python: command not found` or `python3: command not found`

- Install Python 3.
- Reopen your terminal after installation.
- Make sure `python` or `python3` is in `PATH`.

### `Unable to find a usable Logisim executable`

- Follow the Logisim setup instructions in the Lab 5 document.
- If the native installation does not work, use the Java fallback method.

### `Missing circuit file: .../proj_2_2_top.circ`

- Your circuit is not in the expected location.
- Move it to `project-2.2-logisim/proj_2_2_top.circ`.

### The testcase fails with mismatch output

Compare:

- your masked local output in `testing/student_output/p22_localtest.csv`
- your unmasked local debug output in `testing/student_output_unmasked/p22_localtest.csv`
- the masked grading reference in `testing/reference_output/p22_localtest.csv`

On Ubuntu or macOS, you can compare files with:

```bash
diff -u testing/reference_output/p22_localtest.csv testing/student_output/p22_localtest.csv
```

The masked local output and masked reference are what the grader compares. The unmasked local output is only for debugging masked-out signals from your own circuit.

When reading a mismatch, focus on the first wrong line first. Later lines are often secondary effects caused by the first incorrect behavior.
