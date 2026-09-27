"""After LibreOffice recalculation, put every typed-in number back at full double precision.

LibreOffice writes numbers with 15 significant digits when it saves. openpyxl also shortens
floats when it writes. The build script therefore records the exact text of every numeric constant
(the CSV text for the dataset, repr() for the rest) in a .exact.json file, and this script writes
that text into the recalculated file's sheet XML.
Formula cells keep their recalculated cached values. Nothing else in the file is touched.

usage: python3 restore_full_precision.py values.exact.json recalculated.xlsx out.xlsx
"""
import sys, zipfile, re
from lxml import etree
import json

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
      "rel": "http://schemas.openxmlformats.org/package/2006/relationships"}

exact_path, recalc_path, out_path = sys.argv[1:4]
exact = json.load(open(exact_path))        # sheet -> cell -> exact number text (from the build script)

z = zipfile.ZipFile(recalc_path)
files = {n: z.read(n) for n in z.namelist()}
wbx = etree.fromstring(files["xl/workbook.xml"])
rels = etree.fromstring(files["xl/_rels/workbook.xml.rels"])
rid2target = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}

changed = checked = 0
for sh in wbx.find("m:sheets", NS).findall("m:sheet", NS):
    name = sh.get("name")
    target = rid2target[sh.get("{%s}id" % NS["r"])]
    path = "xl/" + target.lstrip("/").replace("xl/", "", 1) if not target.startswith("xl/") else target
    root = etree.fromstring(files[path])
    ws = exact.get(name, {})
    for c in root.iter("{%s}c" % NS["m"]):
        ref = c.get("r")
        if ref not in ws:
            continue
        new = ws[ref]
        src = float(new)
        if c.find("m:f", NS) is not None:
            continue
        v = c.find("m:v", NS)
        if v is None:
            continue
        checked += 1
        if v.text != new:
            if float(v.text) != float(src) and abs(float(v.text) - src) > 1e-12 * max(abs(src), 1e-300):
                raise SystemExit("unexpected value difference at %s!%s: %s vs %s" % (name, ref, v.text, src))
            v.text = new
            changed += 1
    files[path] = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zo:
    for n in z.namelist():
        zo.writestr(n, files[n])
expected = sum(len(v) for v in exact.values())
print("constant numeric cells expected %d, found %d, restored to full precision %d" % (expected, checked, changed))
if checked != expected:
    raise SystemExit("not every recorded cell was found")
