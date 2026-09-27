#!/bin/bash
# Build CHT template + alt/co flow cases for mesh tag (e.g. nu96_nr8_nx120). Refuses to overwrite.
TAG=$1
ROOT=/home/claude/grail_cfd/06_cht
CASE=$ROOT/cht_$TAG
MSH=/home/claude/grail_cfd/03_mesh/levels/$TAG.msh
for d in "$CASE" "$ROOT/flow_alt_$TAG" "$ROOT/flow_co_$TAG"; do [ -e "$d" ] && { echo "REFUSING: $d exists"; exit 1; }; done
test -f "$MSH" || { echo "no mesh $MSH"; exit 1; }
source /usr/share/openfoam/etc/bashrc > /dev/null 2>&1
python3 $ROOT/make_case.py "$CASE" "$MSH" > $ROOT/steps_$TAG.make_case.log 2>&1 || { echo FAIL make_case; exit 1; }
cd "$CASE" && cp "$MSH" .
gmshToFoam "$(basename $MSH)" > log.gmshToFoam 2>&1 || { echo FAIL gmshToFoam; exit 1; }
createPatch -overwrite > log.createPatch 2>&1 || { echo FAIL createPatch; exit 1; }
splitMeshRegions -cellZonesOnly -overwrite > log.splitMeshRegions 2>&1 || { echo FAIL split; exit 1; }
checkMesh -region fluid > log.checkMesh.fluid 2>&1; checkMesh -region solid > log.checkMesh.solid 2>&1
cd $ROOT
for arr in alt co; do
  F=$ROOT/flow_${arr}_$TAG; mkdir -p $F/constant $F/0
  cp -r flow_${arr}_nx60/system $F/
  for f in $(ls flow_${arr}_nx60/constant | grep -v polyMesh); do cp -r flow_${arr}_nx60/constant/$f $F/constant/; done
  cp -r $CASE/constant/fluid/polyMesh $F/constant/
  sed -i 's/mappedWall/wall/' $F/constant/polyMesh/boundary
  python3 -c "import re;f='$F/constant/polyMesh/boundary';b=open(f).read();b=re.sub(r'\n\s*(sampleMode|sampleRegion|samplePatch|offsetMode|offset)\s+[^;]*;','',b);open(f,'w').write(b)"
  cp flow_${arr}_nx60/0/U flow_${arr}_nx60/0/p $F/0/
done
echo "built $TAG"
