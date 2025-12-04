#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
source "$ROOT/.venv/bin/activate"
python "$ROOT/scripts/update_pipeline.py" "$@"
if [[ -f "$ROOT/benchmark_questions.txt" ]]; then
  python "$ROOT/scripts/report_answer_metrics.py" --mode llm --questions-file "$ROOT/benchmark_questions.txt"
fi
