import re, shutil, sys, zipfile
from collections import defaultdict
from pathlib import Path

src = Path(sys.argv[1])
joined = Path(sys.argv[2])
client = Path(sys.argv[3])
server = Path(sys.argv[4])
out = Path(sys.argv[5])
original = Path(sys.argv[6])

obf_to_human = {}
for mapping_file in (client, server):
    for raw in mapping_file.read_text(errors="replace").splitlines():
        if raw and not raw.startswith(" ") and " -> " in raw and raw.endswith(":"):
            human, obf = raw[:-1].split(" -> ", 1)
            obf_to_human[obf] = human.replace(".", "/")

def normalize_desc(desc):
    return re.sub(r"L([^;]+);", lambda m: "L" + obf_to_human.get(m.group(1), m.group(1)) + ";", desc)

srg = defaultdict(list)
owner = None
for raw in joined.read_text(errors="replace").splitlines():
    if not raw or raw.startswith("tsrg2"):
        continue
    if not raw.startswith("\t"):
        p = raw.split()
        if len(p) >= 2:
            owner = p[0]
        continue
    p = raw.strip().split()
    if len(p) >= 3 and p[1].startswith("("):
        srg[owner].append((p[0], normalize_desc(p[1]), p[2]))
    elif len(p) >= 2:
        srg[owner].append((p[0], None, p[1]))

def type_desc(t):
    t = t.strip()
    arr = 0
    while t.endswith("[]"):
        arr += 1
        t = t[:-2]
    prim = {"byte":"B","char":"C","double":"D","float":"F","int":"I",
            "long":"J","short":"S","boolean":"Z","void":"V"}
    d = prim.get(t, "L" + t.replace(".", "/") + ";")
    return "[" * arr + d

named = defaultdict(list)
for mapping_file in (client, server):
    owner = None
    for raw in mapping_file.read_text(errors="replace").splitlines():
        if not raw or raw.startswith("#"):
            continue
        if not raw.startswith(" "):
            if " -> " in raw and raw.endswith(":"):
                _human, owner = raw[:-1].split(" -> ", 1)
            continue
        if " -> " not in raw:
            continue
        left, obf = raw.strip().split(" -> ", 1)
        if "(" in left and ")" in left:
            m = re.match(r"(?:\d+:\d+:)?(.+?)\s+([A-Za-z0-9_$<>]+)\((.*)\)$", left)
            if not m:
                continue
            _ret, name, args = m.groups()
            desc = "(" + "".join(type_desc(a) for a in args.split(",") if a.strip()) + ")"
            named[owner].append((obf, desc, name))
        else:
            m = re.match(r"(?:\d+:\d+:)?(.+?)\s+([A-Za-z0-9_$<>]+)$", left)
            if m:
                named[owner].append((obf, None, m.group(2)))

replacements = {}
for obf_owner, entries in srg.items():
    candidates = named.get(obf_owner, [])
    for obf_member, desc, srg_name in entries:
        for n_obf, n_desc, human_name in candidates:
            if n_obf == obf_member and (desc is None or desc.split(")", 1)[0] + ")" == n_desc):
                old = replacements.get(srg_name)
                if old is None or old == human_name:
                    replacements[srg_name] = human_name
                break

token_re = re.compile(r"\b[fm]_\d+[A-Za-z0-9_]*\b")
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)

count = 0
left = set()
for p in src.rglob("*.java"):
    rel = p.relative_to(src)
    text = p.read_text(errors="replace")
    def repl(m):
        token = m.group(0)
        if token in replacements:
            return replacements[token]
        left.add(token)
        return token
    text = token_re.sub(repl, text)
    target = out / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    count += 1

with zipfile.ZipFile(original) as z:
    for info in z.infolist():
        name = info.filename
        if info.is_dir() or not (name.startswith("assets/") or name.startswith("data/") or name == "pack.mcmeta"):
            continue
        target = out.parent / "resources" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(z.read(info))

print(f"Port source preparation: {count} Java files")
print(f"SRG replacements available: {len(replacements)}")
print(f"Unmapped SRG-like tokens remaining: {len(left)}")
if left:
    print("Remaining examples:", ", ".join(sorted(left)[:80]))
