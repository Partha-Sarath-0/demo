here = pwd() + "/";
exec(here + "grail_xcos_build.sce", -1);
xcosDiagramToScilab(here + "GRAIL_system.zcos", scs_m); mprintf("saved\n");
exit(0);
