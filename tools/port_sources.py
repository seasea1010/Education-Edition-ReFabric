import re, shutil, sys, zipfile
from collections import defaultdict
from pathlib import Path

src, joined, client, server, out, original = map(Path, sys.argv[1:7])

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
    prim = {"byte":"B","char":"C","double":"D","float":"F","int":"I","long":"J","short":"S","boolean":"Z","void":"V"}
    return "[" * arr + prim.get(t, "L" + t.replace(".", "/") + ";")

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
            if m:
                _ret, name, args = m.groups()
                desc = "(" + "".join(type_desc(a) for a in args.split(",") if a.strip()) + ")"
                named[owner].append((obf, desc, name))
        else:
            m = re.match(r"(?:\d+:\d+:)?(.+?)\s+([A-Za-z0-9_$<>]+)$", left)
            if m:
                named[owner].append((obf, None, m.group(2)))

replacements = {}
for obf_owner, entries in srg.items():
    for obf_member, desc, srg_name in entries:
        for n_obf, n_desc, human_name in named.get(obf_owner, []):
            if n_obf == obf_member and (desc is None or desc.split(")", 1)[0] + ")" == n_desc):
                old_name = replacements.get(srg_name)
                if old_name is None or old_name == human_name:
                    replacements[srg_name] = human_name
                break

token_re = re.compile(r"\b[fm]_\d+[A-Za-z0-9_]*\b")
forge_map = {
    "net.minecraftforge.common.MinecraftForge":"MinecraftForge",
    "net.minecraftforge.common.brewing.BrewingRecipeRegistry":"BrewingRecipeRegistry",
    "net.minecraftforge.common.brewing.IBrewingRecipe":"IBrewingRecipe",
    "net.minecraftforge.common.capabilities.Capability":"Capability",
    "net.minecraftforge.common.capabilities.ForgeCapabilities":"ForgeCapabilities",
    "net.minecraftforge.common.extensions.IForgeMenuType":"IForgeMenuType",
    "net.minecraftforge.common.util.LazyOptional":"LazyOptional",
    "net.minecraftforge.event.TickEvent":"TickEvent",
    "net.minecraftforge.eventbus.api.IEventBus":"IEventBus",
    "net.minecraftforge.fml.ModList":"ModList",
    "net.minecraftforge.fml.event.lifecycle.FMLClientSetupEvent":"FMLClientSetupEvent",
    "net.minecraftforge.fml.event.lifecycle.FMLCommonSetupEvent":"FMLCommonSetupEvent",
    "net.minecraftforge.fml.javafmlmod.FMLJavaModLoadingContext":"FMLJavaModLoadingContext",
    "net.minecraftforge.fml.util.thread.SidedThreadGroups":"SidedThreadGroups",
    "net.minecraftforge.network.NetworkEvent":"NetworkEvent",
    "net.minecraftforge.network.NetworkHooks":"NetworkHooks",
    "net.minecraftforge.network.NetworkRegistry":"NetworkRegistry",
    "net.minecraftforge.network.simple.SimpleChannel":"SimpleChannel",
    "net.minecraftforge.registries.DeferredRegister":"DeferredRegister",
    "net.minecraftforge.registries.ForgeRegistries":"ForgeRegistries",
    "net.minecraftforge.registries.IForgeRegistry":"IForgeRegistry",
    "net.minecraftforge.registries.RegistryObject":"RegistryObject",
    "net.minecraftforge.items.IItemHandler":"IItemHandler",
    "net.minecraftforge.items.IItemHandlerModifiable":"IItemHandlerModifiable",
    "net.minecraftforge.items.ItemStackHandler":"ItemStackHandler",
    "net.minecraftforge.items.SlotItemHandler":"SlotItemHandler",
    "net.minecraftforge.items.wrapper.SidedInvWrapper":"SidedInvWrapper",
    "net.minecraftforge.api.distmarker.Dist":"Dist",
}

if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
left=set()
count=0
for p in src.rglob("*.java"):
    rel=p.relative_to(src)
    text=p.read_text(errors="replace")
    text=token_re.sub(lambda m: replacements.get(m.group(0), (left.add(m.group(0)) or m.group(0))), text)
    lines=[]
    for line in text.splitlines():
        m=re.match(r"\s*import\s+([^;]+);", line)
        if m and m.group(1).startswith("net.minecraftforge"):
            fq=m.group(1)
            if fq in ("net.minecraftforge.fml.common.Mod","net.minecraftforge.eventbus.api.SubscribeEvent"):
                continue
            simple=forge_map.get(fq)
            if simple:
                line="import net.mcreator.educationeditionreforged.compat.ForgeCompat."+simple+";"
        lines.append(line)
    text="\n".join(lines)+"\n"
    text=re.sub(r"^\s*@Mod(?:\.[A-Za-z0-9_]+)?(?:\([^\n]*\))?\s*$","",text,flags=re.M)
    text=re.sub(r"^\s*@SubscribeEvent\s*$","",text,flags=re.M)
    for obj in ["_ent","itemstack","this.boundItem","this.boundEntity","this.boundBlockEntity"]:
        text=text.replace(obj+".getCapability(ForgeCapabilities.ITEM_HANDLER, null)","ForgeCompat.getItemHandler("+obj+")")
    text=re.sub(r"public <T> LazyOptional<T> getCapability\(Capability<T> capability, @Nullable Direction facing\) \{.*?\n    \}","public <T> LazyOptional<T> getCapability(Capability<T> capability, @Nullable Direction facing) { return LazyOptional.empty(); }",text,flags=re.S)
    if "ForgeCompat.getItemHandler" in text:
        text="import net.mcreator.educationeditionreforged.compat.ForgeCompat;\n"+text
    target=out/rel
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(text)
    count+=1

with zipfile.ZipFile(original) as z:
    for info in z.infolist():
        name=info.filename
        if info.is_dir() or not (name.startswith("assets/") or name.startswith("data/") or name=="pack.mcmeta"):
            continue
        target=out.parent/"resources"/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(z.read(info))

print(f"Port source preparation: {count} Java files")
print(f"SRG replacements available: {len(replacements)}")
print(f"Unmapped SRG-like tokens remaining: {len(left)}")
if left:
    print("Remaining examples:", ", ".join(sorted(left)[:80]))
