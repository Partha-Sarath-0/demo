#!/bin/bash
# Build one grid level: a CHT template case and alternating + co-current flow cases on its
# EXACT fluid mesh. Refuses to overwrite anything.
set -e
NX=$1
ROOT=/home/claude/grail_cfd/06_cht
MSH=/home/claude/grail_cfd/03_mesh/levels/nu64_nr5_nx${NX}.msh
CHT=$ROOT/cht_nx${NX}
for d in "$CHT" "$ROOT/flow_alt_nx${NX}" "$ROOT/flow_co_nx${NX}"; do
  if [ -e "$d" ]; then echo "REFUSING: $d exists"; exit 1; fi
done
test -f "$MSH"
bash $ROOT/build.sh "$CHT" "$MSH" > $ROOT/build_nx${NX}.log 2>&1
for arr in alt co; do
  F=$ROOT/flow_${arr}_nx${NX}
  mkdir -p "$F/constant"
  cp -r $ROOT/flow_${arr}_nx60/system "$F/"
  cp -r $ROOT/flow_${arr}_nx60/constant/transportProperties $ROOT/flow_${arr}_nx60/constant/turbulenceProperties "$F/constant/" 2>/dev/null || true
  for f in $(ls $ROOT/flow_${arr}_nx60/constant | grep -v polyMesh); do cp -r "$ROOT/flow_${arr}_nx60/constant/$f" "$F/constant/"; done
  cp -r "$CHT/constant/fluid/polyMesh" "$F/constant/"
  sed -i 's/mappedWall/wall/' "$F/constant/polyMesh/boundary"
  python3 - "$F/constant/polyMesh/boundary" <<'PY'
import re,sys
b=open(sys.argv[1]).read()
b=re.sub(r'\n\s*(sampleMode|sampleRegion|samplePatch|offsetMode|offset)\s+[^;]*;','',b)
open(sys.argv[1],'w').write(b)
PY
  mkdir -p "$F/0" && cp $ROOT/flow_${arr}_nx60/0/U $ROOT/flow_${arr}_nx60/0/p "$F/0/"
done
echo "level NX=$NX built: $CHT, flow_alt_nx${NX}, flow_co_nx${NX}"
