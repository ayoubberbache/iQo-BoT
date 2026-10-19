#!/bin/sh
set -e
OUT=/artifacts
mkdir -p "$OUT"
python train.py "$@"
python export.py
cp edge_chem_net.pt edge_chem_net.onnx edge_chem_net_quantized.pt iqo_chem_embedded_config.h \
   edge_chem_net_weights.pt "$OUT"/
# runtime code needed by the dashboard on the target device
cp config.py topics.py guardrail.py engine.py dashboard.py knowledge.py "$OUT"/
echo "Done. Artifacts in $OUT:"; ls -lh "$OUT"
