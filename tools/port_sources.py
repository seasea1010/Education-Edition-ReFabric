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

compat_backup = None
compat_file = out / "net/mcreator/educationeditionreforged/compat/ForgeCompat.java"
if compat_file.exists():
    compat_backup = compat_file.read_text()
if out.exists():
    shutil.rmtree(out)
out.mkdir(parents=True)
if compat_backup is not None:
    compat_file.parent.mkdir(parents=True, exist_ok=True)
    compat_file.write_text(compat_backup)
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
    text=text.replace("import javax.annotation.Nullable;","")
    text=text.replace("@Nullable ","")
    for obj in ["_ent","itemstack","this.boundItem","this.boundEntity","this.boundBlockEntity"]:
        text=text.replace(obj+".getCapability(ForgeCapabilities.ITEM_HANDLER, null)","net.mcreator.educationeditionreforged.compat.ForgeCompat.getItemHandler("+obj+")")
        text=text.replace(obj+".getCapability(ForgeCapabilities.ITEM_HANDLER, (Direction)null)","net.mcreator.educationeditionreforged.compat.ForgeCompat.getItemHandler("+obj+")")
    text=text.replace("Map _slots", "Map<Integer, Slot> _slots")
    text=text.replace("Supplier _current", "Supplier<?> _current")
    text=text.replace("final Map value = _current.get();", "final Map value = (Map)_current.get();")
    text=text.replace("instanceof final Supplier<Map<Integer, Slot>> _current", "instanceof Supplier<?> _current")
    text=text.replace('guistate.get("text:Weight").getValue()', '((EditBox)guistate.get("text:Weight")).getValue()')
    text=text.replace("ItemTags.create(new ResourceLocation(", "TagKey.create(Registries.ITEM, new ResourceLocation(")
    if "TagKey.create(Registries.ITEM" in text:
        text=text.replace("import net.minecraft.tags.ItemTags;", "import net.minecraft.tags.TagKey;\nimport net.minecraft.core.registries.Registries;")
    text=text.replace("CreativeModeTab.builder()", "CreativeModeTab.builder(CreativeModeTab.Row.TOP, 0)")
    text=text.replace(".withSearchBar()", "")
    text=text.replace("addRenderableWidget((GuiEventListener)", "addRenderableWidget(")
    text=text.replace("addWidget((GuiEventListener)", "addWidget(")
    text=text.replace("NonNullList.withSize(10, (Object)ItemStack.EMPTY)", "NonNullList.withSize(10, ItemStack.EMPTY)")
    text=text.replace("NonNullList.withSize(this.getContainerSize(), (Object)ItemStack.EMPTY)", "NonNullList.withSize(this.getContainerSize(), ItemStack.EMPTY)")
    text=re.sub(r"NonNullList\.withSize\((\d+), \(Object\)ItemStack\.EMPTY\)", r"NonNullList.withSize(\1, ItemStack.EMPTY)", text)
    text=text.replace("return (LazyOptional<T>)super.getCapability((Capability)capability, facing);", "return LazyOptional.empty();")
    text=text.replace("super.onDestroyedByPlayer(blockstate, world, pos, entity, willHarvest, fluid)", "world.removeBlock(pos, false)")
    text=text.replace("() -> new BlockItem((Block)block.get(), new Item.Properties())", "() -> (Item)new BlockItem((Block)block.get(), new Item.Properties())")
    text=text.replace("EducationEditionReforgedMod.PACKET_HANDLER.sendToServer((Object)", "EducationEditionReforgedMod.PACKET_HANDLER.sendToServer(")
    text=re.sub(r"public <T> LazyOptional<T> getCapability\(Capability<T> capability, @Nullable Direction facing\) \{.*?\n    \}","public <T> LazyOptional<T> getCapability(Capability<T> capability, @Nullable Direction facing) { return LazyOptional.empty(); }",text,flags=re.S)
    if "ForgeCompat.getItemHandler" in text:
        text=re.sub(r"^(package [^;]+;\n)", r"\1import net.mcreator.educationeditionreforged.compat.ForgeCompat;\n", text, count=1)
    # Rebuild MCreator Combine procedures from their recipe conditions.
    if rel.name.startswith("Combine") and rel.name.endswith("Procedure.java"):
        if rel.name == "CombineProcedure.java":
            combine_files = sorted(src.rglob("Combine*Procedure.java"))
            calls = []
            for cp in combine_files:
                if cp.name != "CombineProcedure.java":
                    calls.append("        " + cp.stem + ".execute(entity);")
            text = "package net.mcreator.educationeditionreforged.procedures;\nimport net.minecraft.world.entity.Entity;\npublic class CombineProcedure {\n    public static void execute(Entity entity) {\n        if (entity == null) return;\n" + "\n".join(calls) + "\n    }\n}\n"
        else:
            amounts = [(int(a), int(n)) for a,n in re.findall(r"getAmount\((\d+)\)\s*==\s*(\d+)", text)]
            refs = []
            for m in re.finditer(r"EducationEditionReforgedModBlocks\.([A-Z0-9_]+)\.get\(\)", text):
                if m.group(1) not in refs:
                    refs.append(m.group(1))
            outm = re.search(r"EducationEditionReforgedModItems\.([A-Z0-9_]+)\.get\(\)", text)
            if len(amounts) == len(refs) and outm:
                checks = []
                for slot, need in amounts:
                    block = refs[len(checks)//2]
                    checks.append("        Slot s{0} = slots.get({0}) instanceof Slot ? (Slot) slots.get({0}) : null;".format(slot))
                    checks.append("        if (s{0} == null || s{0}.getItem().getItem() != EducationEditionReforgedModBlocks.{1}.get().asItem() || s{0}.getItem().getCount() < {2}) return;".format(slot, block, need))
                consume = ["        slots.get({}).remove({});".format(slot, need) for slot, need in amounts]
                output = outm.group(1)
                text = """package net.mcreator.educationeditionreforged.procedures;
import java.util.Map;
import java.util.function.Supplier;
import net.mcreator.educationeditionreforged.init.EducationEditionReforgedModBlocks;
import net.mcreator.educationeditionreforged.init.EducationEditionReforgedModItems;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.Slot;
import net.minecraft.world.item.ItemStack;
public class {0} {{
    public static void execute(Entity entity) {{
        if (!(entity instanceof Player player)) return;
        if (!(player.containerMenu instanceof Supplier<?> supplier)) return;
        Object raw = supplier.get();
        if (!(raw instanceof Map<?,?> rawSlots)) return;
        @SuppressWarnings("unchecked") Map<Integer, Slot> slots = (Map<Integer, Slot>) rawSlots;
{1}
{2}
        Slot outputSlot = slots.get(0);
        if (outputSlot != null) outputSlot.set(new ItemStack(EducationEditionReforgedModItems.{3}.get(), 1));
    }}
}}
""".format(rel.stem, "\n".join(checks), "\n".join(consume), output)

    if "/client/gui/" in str(rel) and rel.name.endswith("Screen.java"):
        menu_name=(rel.stem[:-6] if rel.stem.endswith("Screen") else rel.stem)+"Menu"
        text=text.replace("super((AbstractContainerMenu)container,", "super(("+menu_name+")container,")
    if rel.name == "EducationEditionReforgedModItems.java":
        text=re.sub(r"return \(RegistryObject<Item>\).*?register\(block\.getId\(\)\.getPath\(\), \(\) -> \{.*?\n\s*\}\);", "return REGISTRY.register(block.getId().getPath(), () -> (Item)new BlockItem((Block)block.get(), new Item.Properties()));", text, flags=re.S)
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
