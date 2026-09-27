"""Energy-only solver settings for the frozen-flow benchmark. Speed only; the converged answer
is unchanged. With frozen flow and constant properties the energy problem is linear, so the
solid is solved fully each outer iteration and relaxation is near unity."""
import re, sys, os
case = sys.argv[1]
s = os.path.join(case, "system/solid/fvSolution")
t = open(s).read()
t = re.sub(r'relTol\s+0\.01;', 'relTol          0;', t)
t = re.sub(r'equations\s*\{\s*h\s+[\d.]+;\s*\}', 'equations { h 1.0; }', t)
open(s, "w").write(t)
f = os.path.join(case, "system/fluid/fvSolution")
t = open(f).read()
t = re.sub(r'(equations\s*\{[^}]*\bh\s+)[\d.]+;', r'\g<1>0.8;', t)
# fluid relTol: full solve of the fluid energy each outer iteration (linear problem)
t = re.sub(r'("\(U\|h\|e\|k\|epsilon\|omega\)"\s*\{[^}]*?relTol\s+)0\.01;', r'\g<1>0;', t)
open(f, "w").write(t)
c = os.path.join(case, "system/controlDict")
t = open(c).read()
t = re.sub(r"endTime\s+[^;]+;", "endTime         40000;", t)
t = re.sub(r"writeInterval\s+[^;]+;", "writeInterval   2000;", t)
open(c, "w").write(t)
print(open(s).read().count("relTol          0;"), "solid relTol set; fluid h", re.search(r'h\s+([\d.]+);', open(f).read().split('equations')[1]).group(1))
