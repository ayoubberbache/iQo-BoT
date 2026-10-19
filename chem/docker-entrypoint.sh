#!/bin/sh
set -e
OUT=/artifacts
mkdir -p "$OUT"
python train.py "$@"
python export.py
cp edge_*_net.pt edge_*_net.onnx edge_*_net_quantized.pt edge_*_net_weights.pt iqo_*_embedded_config.h "$OUT"/
echo "Done. Artifacts in $OUT:"; ls -lh "$OUT"
