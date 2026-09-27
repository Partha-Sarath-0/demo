#!/bin/bash
# Restart-safe benchmark queue. One lane per arrangement (alt | co), one core each.
#   for each mesh tag: flow (simpleFoam) -> CHT (frozen flow), each resumed from latestTime.
# A stage is DONE only when its marker file exists; markers are written by this script after the
# stage's stop condition, never by hand. Re-running the script after a restart continues where
# it stopped.
ARR=$1                                  # alt | co
shift
TAGS="$@"                               # e.g. nx240 nu48_nr4_nx120 nu96_nr8_nx120
ROOT=/home/claude/grail_cfd/06_cht
T=/home/claude/grail_cfd/tools
source /usr/share/openfoam/etc/bashrc > /dev/null 2>&1
log(){ echo "[$(date +%T)] $ARR $*"; }

for TAG in $TAGS; do
  FLOW=$ROOT/flow_${ARR}_$TAG
  if [ "$TAG" = "nx240" ]; then CHTT=$ROOT/cht_nx240; SRC_CHT=$ROOT/bench_${ARR}_nx120;
  else CHTT=$ROOT/cht_$TAG; SRC_CHT=$ROOT/bench_${ARR}_nx120; fi
  BENCH=$ROOT/bench_${ARR}_$TAG

  # ---------------------------------------------------------------- flow
  if [ ! -f $FLOW/FLOW_DONE ]; then
    cd $FLOW
    sed -i 's/^\(\s*startFrom\s\+\)[^;]*;/\1latestTime;/' system/controlDict
    if ! ls -d [1-9]* > /dev/null 2>&1 && [ ! -f 0/.mapped ]; then
      src=$ROOT/flow_${ARR}_nx120
      mapFields $src -sourceTime latestTime -consistent > log.mapFields 2>&1 && touch 0/.mapped
      log "flow $TAG initialised from $src"
    fi
    log "flow $TAG start"
    simpleFoam >> log.run 2>&1
    if grep -q "SIMPLE solution converged\|^End" log.run; then touch FLOW_DONE; log "flow $TAG done"; else log "flow $TAG STOPPED without End"; exit 1; fi
  fi

  # ---------------------------------------------------------------- CHT
  if [ ! -f $BENCH/CHT_DONE ]; then
    if [ ! -d $BENCH ]; then
      if [ "$ARR" = "co" ]; then python3 $T/cht_frozen.py $CHTT $FLOW $BENCH 3000 co; else python3 $T/cht_frozen.py $CHTT $FLOW $BENCH 3000; fi
      python3 $T/cht_energy_settings.py $BENCH
      cd $BENCH
      # write every 250, run to 3000; convergence is judged from snapshots afterwards
      sed -i 's/^\(\s*endTime\s\+\)[^;]*;/\1 3000;/; s/^\(\s*writeInterval\s\+\)[^;]*;/\1 250;/' system/controlDict
      sed -i 's/^\(\s*startFrom\s\+\)[^;]*;/\1latestTime;/' system/controlDict
      # initial temperature from the converged NX120/NU64 solution (starting guess only)
      for R in fluid solid; do
        mapFields $SRC_CHT -sourceRegion $R -targetRegion $R -sourceTime latestTime -consistent \
          -fields '(T)' > log.mapFields.$R 2>&1 || log "map $R failed (continuing from 300 K)"
      done
      log "CHT $TAG built and initialised from $SRC_CHT"
    fi
    cd $BENCH
    log "CHT $TAG start"
    chtMultiRegionSimpleFoam >> log.run 2>&1
    if grep -q "^End" log.run; then touch CHT_DONE; log "CHT $TAG reached endTime"; else log "CHT $TAG STOPPED without End"; exit 1; fi
  fi
done
log "lane complete"
