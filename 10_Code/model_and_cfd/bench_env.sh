#!/bin/bash
# Nu-envelope lane: co-current benchmark at the flow-rate extremes, NU64 / NX120 mesh.
# Restart-safe in the same way as bench_queue.sh.
ROOT=/home/claude/grail_cfd/06_cht
T=/home/claude/grail_cfd/tools
source /usr/share/openfoam/etc/bashrc > /dev/null 2>&1
log(){ echo "[$(date +%T)] env $*"; }
for TAG in m1p0 m4p5; do
  FLOW=$ROOT/flow_co_nx120_$TAG
  BENCH=$ROOT/bench_co_nx120_$TAG
  if [ ! -f $FLOW/FLOW_DONE ]; then
    cd $FLOW
    sed -i 's/^\(\s*startFrom\s\+\)[^;]*;/\1latestTime;/' system/controlDict
    log "flow $TAG start"; simpleFoam >> log.run 2>&1
    if grep -q "SIMPLE solution converged\|^End" log.run; then touch FLOW_DONE; log "flow $TAG done"; else log "flow $TAG STOPPED"; exit 1; fi
  fi
  if [ ! -f $BENCH/CHT_DONE ]; then
    if [ ! -d $BENCH ]; then
      python3 $T/cht_frozen.py $ROOT/cht_nx120 $FLOW $BENCH 3000 co
      python3 $T/cht_energy_settings.py $BENCH
      sed -i 's/^\(\s*endTime\s\+\)[^;]*;/\1 6000;/; s/^\(\s*writeInterval\s\+\)[^;]*;/\1 250;/; s/^\(\s*startFrom\s\+\)[^;]*;/\1latestTime;/' $BENCH/system/controlDict
      # seed T only (starting guess) from the design-point co-current solution, via a
      # throw-away copy so U and phi in the real case are never touched
      TMP=/tmp/claude-0/-home-claude/09cdd886-3a71-5b52-bd3e-e373da90433a/scratchpad/seed_env_$TAG
      [ -e "$TMP" ] && rm -r -- "$TMP"
      mkdir -p $TMP && cp -r $BENCH/constant $BENCH/system $BENCH/0 $TMP/
      ok=1
      for R in fluid solid; do
        (cd $TMP && mapFields $ROOT/bench_co_nx120 -sourceRegion $R -targetRegion $R -sourceTime latestTime -consistent > log.map.$R 2>&1) || ok=0
      done
      if [ $ok = 1 ]; then
        for R in fluid solid; do cp $BENCH/0/$R/T $BENCH/0/$R/T.cold && cp $TMP/0/$R/T $BENCH/0/$R/T; done
        log "CHT $TAG built, T seeded from design point"
      else
        log "CHT $TAG built, seeding failed -> cold start"
      fi
    fi
    cd $BENCH; log "CHT $TAG start"; chtMultiRegionSimpleFoam >> log.run 2>&1
    if grep -q "^End" log.run; then touch CHT_DONE; log "CHT $TAG reached endTime"; else log "CHT $TAG STOPPED"; exit 1; fi
  fi
done
log "lane complete"
