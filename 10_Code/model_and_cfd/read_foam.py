"""Parse OpenFOAM ASCII polyMesh + fields directly.

This build's function-object writer fails with an IOstream "sha1" error, so patch
averages are computed here from the raw files instead.
"""
import re, numpy as np, os, gzip


def _open(p):
    if os.path.exists(p): return open(p, 'r', errors='replace')
    if os.path.exists(p + '.gz'): return gzip.open(p + '.gz', 'rt', errors='replace')
    raise FileNotFoundError(p)


def read_list_scalar(path):
    txt = _open(path).read()
    m = re.search(r'internalField\s+nonuniform\s+List<scalar>\s*\n?\s*(\d+)\s*\(', txt)
    if m:
        n = int(m.group(1)); s = txt.index('(', m.end() - 1) + 1
        vals = txt[s:].split(')', 1)[0].split()
        return np.array(vals[:n], dtype=float)
    m = re.search(r'internalField\s+uniform\s+([-\d.eE+]+)', txt)
    if m:
        return np.array([float(m.group(1))])
    raise ValueError("no internalField in " + path)


def read_list_vector(path):
    txt = _open(path).read()
    m = re.search(r'internalField\s+nonuniform\s+List<vector>\s*\n?\s*(\d+)\s*\(', txt)
    n = int(m.group(1)); s = txt.index('(', m.end() - 1) + 1
    body = txt[s:]
    vecs = re.findall(r'\(([-\d.eE+\s]+)\)', body[:body.rindex(')\n;') if ')\n;' in body else len(body)])
    out = np.array([v.split() for v in vecs[:n]], dtype=float)
    return out


def read_owner(case):
    txt = _open(os.path.join(case, 'constant/polyMesh/owner')).read()
    m = re.search(r'\n(\d+)\s*\n\(', txt)
    n = int(m.group(1)); s = txt.index('(', m.end() - 1) + 1
    return np.array(txt[s:].split(')', 1)[0].split()[:n], dtype=int)


def read_boundary(case):
    txt = _open(os.path.join(case, 'constant/polyMesh/boundary')).read()
    out = {}
    for m in re.finditer(r'(\w+)\s*\{([^}]*)\}', txt):
        name, body = m.group(1), m.group(2)
        nf = re.search(r'nFaces\s+(\d+)', body)
        sf = re.search(r'startFace\s+(\d+)', body)
        if nf and sf:
            out[name] = (int(nf.group(1)), int(sf.group(1)))
    return out


def face_areas(case):
    """Face areas and centres from points + faces."""
    txt = _open(os.path.join(case, 'constant/polyMesh/points')).read()
    m = re.search(r'\n(\d+)\s*\n\(', txt)
    n = int(m.group(1)); s = txt.index('(', m.end() - 1) + 1
    body = txt[s:]
    end = body.rindex(')\n)')
    pts = np.array(re.findall(r'\(([^)]*)\)', body[:end]), dtype=object)
    pts = np.array([p.split() for p in pts[:n]], dtype=float)

    txt = _open(os.path.join(case, 'constant/polyMesh/faces')).read()
    m = re.search(r'\n(\d+)\s*\n\(', txt)
    nf = int(m.group(1)); s = txt.index('(', m.end() - 1) + 1
    body = txt[s:]
    faces = re.findall(r'\d+\(([^)]*)\)', body)
    faces = [np.array(f.split(), dtype=int) for f in faces[:nf]]
    return pts, faces


def patch_average(case, field_vals, owner, patch, use_cells=True):
    nf, sf = patch
    cells = owner[sf:sf + nf]
    return field_vals[cells].mean(), cells
