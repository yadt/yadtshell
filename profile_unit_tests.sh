#!/bin/bash
pip install gprof2dot && python -m cProfile -o output.pstats venv/bin/pyb run_unit_tests && gprof2dot -f pstats output.pstats | dot -Tpng -o profiling_results.png
