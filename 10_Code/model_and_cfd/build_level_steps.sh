#!/bin/bash
# Same steps as 06_cht/build.sh, run explicitly, each logged. Refuses to overwrite.
NX=$1
ROOT=/home/claude/grail_cfd/06_cht
CASE=$ROOT/cht_nx${NX}
MSH=/home/claude/grail_cfd/03_mesh/levels/nu64_nr5_nx${NX}.msh
if [ -e "$CASE" ]; then echo "REFUSING: $CASE exists"; exit 1; fi
source /usr/share/openfoam/etc/bashrc > /dev/null 2>&1
echo "[$(date +%T)] make_case"; python3 $ROOT/make_case.py "$CASE" "$MSH" > $ROOT/steps_nx${NX}.make_case.log 2>&1 || { echo FAIL make_case; exit 1; }
cd "$CASE" && cp "$MSH" .
echo "[$(date +%T)] gmshToFoam"; gmshToFoam "$(basename $MSH)" > log.gmshToFoam 2>&1 || { echo FAIL gmshToFoam; exit 1; }
echo "[$(date +%T)] createPatch"; createPatch -overwrite > log.createPatch 2>&1 || { echo FAIL createPatch; exit 1; }
echo "[$(date +%T)] splitMeshRegions"; splitMeshRegions -cellZonesOnly -overwrite > log.splitMeshRegions 2>&1 || { echo FAIL split; exit 1; }
echo "[$(date +%T)] checkMesh"; checkMesh -region fluid > log.checkMesh.fluid 2>&1; checkMesh -region solid > log.checkMesh.solid 2>&1
echo "[$(date +%T)] done"
