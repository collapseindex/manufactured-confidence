#!/usr/bin/env bash
# Full poisoning grid: every backend x every victim model, n=10. Each run writes to data/.
# Requires an editable install of the package: pip install -e .
cd "$(dirname "$0")"
for backend in mem0 langmem rawvector; do
  for model in sonnet haiku llama70 gpt4o-mini qwen72; do
    echo ">>> $backend / $model"
    python -u experiments/poison.py --backend "$backend" --decider "$model" --n 10 \
      2>/dev/null | grep -E "laundering|defense=" || echo "   (run failed)"
  done
done
echo "GRID DONE"
