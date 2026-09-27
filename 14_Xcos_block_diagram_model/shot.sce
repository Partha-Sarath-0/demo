xcos(pwd() + "/GRAIL_system.zcos");
sleep(25000);
unix("for w in $(xdotool search --name ''Palette browser''); do xdotool windowunmap $w; done");
unix("W=$(xdotool search --name ''GRAIL_system'' | head -1); xdotool windowactivate $W; xdotool windowsize $W 2400 1300; xdotool windowmove $W 0 0");
sleep(4000);
unix("import -window root " + pwd() + "/shot1.png");
exit(0);
