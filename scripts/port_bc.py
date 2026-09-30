from pathlib import Path
import re
import shutil
root=Path("bc")

p=root/"gradle.properties"
s=p.read_text().replace("mc_version=1.21.1","mc_version=26.1.2").replace("neo_version=21.1.72","neo_version=26.1.2.106")
p.write_text(s)

p=root/"build.gradle"
s=p.read_text()
s=s.replace("JavaLanguageVersion.of(21)","JavaLanguageVersion.of(25)")
s=s.replace("id 'net.neoforged.gradle.userdev' version '7.0.165'","id 'net.neoforged.moddev' version '2.0.147'")
s=re.sub(r"\nminecraft \{[\s\S]*?\n\}\n\n+runs \{[\s\S]*?\n\}\n", '\nneoForge {\n    version = neo_version\n    mods { brandonscore { sourceSet(sourceSets.main) } }\n}\n', s, count=1)
a=s.index("dependencies {")
b=s.index("\nprocessResources {",a)
s=s[:a]+'''dependencies {
    implementation files("../ccl/build/libs/" + file("../ccl/build/libs").list().find { it.endsWith(".jar") && !it.contains("sources") && !it.contains("javadoc") })\n    implementation "net.covers1624:Quack:0.4.9.+"
}
'''+s[b:]
# Publishing/signing are not needed to produce the port jar.
idx=s.find("\ndef publishingMetadata =")
if idx!=-1: s=s[:idx]+"\n"
p.write_text(s)

w=root/"gradle/wrapper/gradle-wrapper.properties"
if w.exists():
    t=w.read_text()
    t=re.sub(r"gradle-[0-9.]+-(bin|all)\\.zip","gradle-9.1.0-bin.zip",t)
    w.write_text(t)

# 1.21 branch wrapper is 8.10; Java 25 requires Gradle 9.x.
w=root/"gradle/wrapper/gradle-wrapper.properties"
if w.exists():
    t=w.read_text()
    t=re.sub(r"gradle-[0-9.]+-(?:bin|all)\\.zip", "gradle-9.1.0-bin.zip", t)
    t=t.replace("gradle-8.10-bin.zip","gradle-9.1.0-bin.zip")
    w.write_text(t)

p=root/"build.gradle"
t=p.read_text()
t=re.sub(r"\s*id 'com\.github\.johnrengelman\.shadow'.*\n", "\n", t)
p.write_text(t)

# Broad Mojang 26.1 naming migrations.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=t.replace("net.minecraft.resources.ResourceLocation", "net.minecraft.resources.Identifier")
    t=re.sub(r"\bResourceLocation\b", "Identifier", t)
    t=t.replace("Identifier.fromNamespaceAndPath(", "Identifier.fromNamespaceAndPath(")
    java.write_text(t)

# Optional JEI integration cannot compile until a 26.1 JEI API is available.
jei=root/"src/main/java/com/brandon3055/brandonscore/integration/BCJEIPlugin.java"
if jei.exists(): jei.unlink()

# NeoForge 26.1 removed INBTSerializable. Supply the compatibility contract BC uses while porting call sites.
compat=root/"src/main/java/net/neoforged/neoforge/common/util/INBTSerializable.java"
compat.parent.mkdir(parents=True, exist_ok=True)
compat.write_text("""package net.neoforged.neoforge.common.util;
import net.minecraft.core.HolderLookup;
import net.minecraft.nbt.Tag;
public interface INBTSerializable<T extends Tag> {
    T serializeNBT(HolderLookup.Provider provider);
    void deserializeNBT(HolderLookup.Provider provider, T nbt);
}
""")

# Util was renamed in Mojang 26.1.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text().replace("import net.minecraft.Util;","import net.minecraft.util.Util;")
    java.write_text(t)

# Remove the remaining optional JEI-only helper.
jei=root/"src/main/java/com/brandon3055/brandonscore/integration/ModularGuiProperties.java"
if jei.exists(): jei.unlink()

# 26.1 interaction result consolidation.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=t.replace("import net.minecraft.world.ItemInteractionResult;","")
    t=re.sub(r"\bItemInteractionResult\b", "InteractionResult", t)
    t=t.replace("InteractionResult.PASS_TO_DEFAULT_BLOCK_INTERACTION","InteractionResult.PASS")
    java.write_text(t)

# Deprecated BC sign-edit hook targets the removed vanilla GameRules API; disable this isolated handler.
p=root/"src/main/java/com/brandon3055/brandonscore/handlers/SighEditHandler.java"
if p.exists(): p.unlink()

# Remove stale registration/import left by disabled sign handler.
p=root/"src/main/java/com/brandon3055/brandonscore/BrandonsCore.java"
if p.exists():
    t=p.read_text()
    t=t.replace("import com.brandon3055.brandonscore.handlers.SighEditHandler;\n","")
    t=re.sub(r"^.*SighEditHandler.*\n","",t,flags=re.M)
    p.write_text(t)

# Preserve full BrandonsCore client/contributor/runtime surface; migrate it instead of pruning.\n\n# Common 26.1 Level accessor change.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text().replace(".isClientSide", ".isClientSide()")
    t=t.replace(".isClientSide()()", ".isClientSide()")
    java.write_text(t)

# 26.1 NBT boolean getters return Optional values.
for java in (root/'src/main/java').rglob('*.java'):
    t=java.read_text()
    for k in ['detectPassive','detectHostile','detectPlayer','detectOther','isWhiteList']:
        t=t.replace('getBoolean("'+k+'")','getBoolean("'+k+'").orElse(false)')
    java.write_text(t)

# Additional generic 26.1 NBT getter migrations.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=t.replace("compound.getBoolean(name);", "compound.getBoolean(name).orElse(false);")
    t=t.replace('nbt.getString("custom_name");', 'nbt.getString("custom_name").orElse("");')
    t=t.replace('nbt.getCompound(tagName)', 'nbt.getCompound(tagName).orElseGet(CompoundTag::new)')
    t=t.replace('nbt.getCompound("bc_caps")', 'nbt.getCompound("bc_caps").orElseGet(CompoundTag::new)')
    t=t.replace('nbt.contains("custom_name", 8)', 'nbt.contains("custom_name")')
    java.write_text(t)

# CompoundTag 26.1 typed contains/getCompound changes in core data manager.
for rel in ["lib/datamanager/TileDataManager.java","lib/datamanager/ManagedEnum.java","lib/StringyStacks.java","blocks/TileCapabilityManager.java"]:
    q=root/"src/main/java/com/brandon3055/brandonscore"/rel
    if q.exists():
        t=q.read_text()
        t=re.sub(r'\.contains\(([^,\n]+),\s*(?:8|10)\)', r'.contains(\1)', t)
        t=re.sub(r'\.getCompound\(([^\n\)]+)\)(?!\.orElse)', r'.getCompound(\1).orElseGet(CompoundTag::new)', t)
        q.write_text(t)

# Small 26.1 primitive/API migrations.
q=root/"src/main/java/com/brandon3055/brandonscore/lib/datamanager/ManagedEnum.java"
if q.exists():
    t=q.read_text().replace('nbt.getByte("value") & 0xFF','nbt.getByte("value").orElse((byte) 0) & 0xFF')
    q.write_text(t)
q=root/"src/main/java/com/brandon3055/brandonscore/api/power/OPStorage.java"
if q.exists():
    t=q.read_text().replace("((NumericTag) tag).getAsLong()","((NumericTag) tag).longValue()")
    q.write_text(t)

# Raise javac error cap so migration can be grouped accurately.
p=root/"build.gradle"
s=p.read_text()
if "Xmaxerrs" not in s:
    s += "\ntasks.withType(JavaCompile).configureEach { options.compilerArgs += ['-Xmaxerrs', '2000'] }\n"
p.write_text(s)

# Broad 26.1 NBT Optional migration across BC.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=re.sub(r'\.contains\(([^,\n()]+),\s*\d+\)', r'.contains(\1)', t)
    t=re.sub(r'\.getList\(([^,\n()]+),\s*\d+\)', r'.getList(\1)', t)
    for meth,default in [("getBoolean","false"),("getByte","(byte) 0"),("getShort","(short) 0"),("getInt","0"),("getLong","0L"),("getFloat","0F"),("getDouble","0D"),("getString",'""')]:
        pat=r'\.'+meth+r'\(([^\n()]+)\)(?!\.orElse)'
        t=re.sub(pat, lambda m: "."+meth+"("+m.group(1)+").orElse("+default+")", t)
    t=re.sub(r'\.getCompound\(([^\n()]+)\)(?!\.orElse)', r'.getCompound(\1).orElseGet(CompoundTag::new)', t)
    java.write_text(t)

# Inventory encapsulation introduced before 26.1: use Container slot API.
q=root/"src/main/java/com/brandon3055/brandonscore/inventory/PlayerSlot.java"
if q.exists():
    t=q.read_text()
    t=t.replace("player.getInventory().selected", "player.getInventory().getSelectedSlot()")
    t=t.replace("inv.getSelected()", "inv.getSelectedItem()")
    t=t.replace("inv.selected", "inv.getSelectedSlot()")
    t=t.replace("player.getInventory().items.size()", "36")
    t=t.replace("player.getInventory().items.set(slot, stack)", "player.getInventory().setItem(slot, stack)")
    t=t.replace("player.getInventory().armor.size()", "4")
    t=t.replace("player.getInventory().armor.set(slot, stack)", "player.getInventory().setItem(36 + slot, stack)")
    t=t.replace("player.getInventory().offhand.size()", "1")
    t=t.replace("player.getInventory().offhand.set(slot, stack)", "player.getInventory().setItem(40, stack)")
    t=t.replace("player.getInventory().armor.get(slot)", "player.getInventory().getItem(36 + slot)")
    t=t.replace("player.getInventory().items.get(slot)", "player.getInventory().getItem(slot)")
    t=t.replace("player.getInventory().offhand.get(slot)", "player.getInventory().getItem(40)")
    t=t.replace("inv.items.size()", "36").replace("inv.items.get(i)", "inv.getItem(i)")
    t=t.replace("inv.armor.size()", "4").replace("inv.armor.get(i)", "inv.getItem(36 + i)")
    t=t.replace("inv.offhand.size()", "1").replace("inv.offhand.get(i)", "inv.getItem(40)")
    q.write_text(t)

# Preserve command surface for final functional port.\n\n# Registry lookup and ResourceKey accessor migrations.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=t.replace(".dimension().location()", ".dimension().identifier()")
    for reg in ["BLOCK","ITEM","ENTITY_TYPE","FLUID"]:
        t=t.replace("BuiltInRegistries."+reg+".get(", "BuiltInRegistries."+reg+".getValue(")
    java.write_text(t)

# CCL 26.1 no longer exposes its configuration packet handler to consumers.
q=root/"src/main/java/com/brandon3055/brandonscore/network/BCoreNetwork.java"
if q.exists():
    t=q.read_text().replace("import codechicken.lib.internal.network.ClientConfigurationPacketHandler;\n","")
    t=t.replace("            .clientConfiguration(() -> ClientConfigurationPacketHandler::new)\n","")
    q.write_text(t)

# NeoForge 26.1 renamed its standard energy capability.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text().replace("Capabilities.EnergyStorage.", "Capabilities.Energy.")
    java.write_text(t)

# NeoForge 26.1 server reload event rename and keyed registration.
q=root/"src/main/java/com/brandon3055/brandonscore/multiblock/MultiBlockManager.java"
if q.exists():
    t=q.read_text().replace("AddReloadListenerEvent", "AddServerReloadListenersEvent")
    t=t.replace("event.addListener(new MultiBlockManager());", 'event.addListener(Identifier.fromNamespaceAndPath(BrandonsCore.MODID, "multiblocks"), new MultiBlockManager());')
    if "import com.brandon3055.brandonscore.BrandonsCore;" not in t:
        t=t.replace("import com.brandon3055.brandonscore.network.BCoreNetwork;", "import com.brandon3055.brandonscore.BrandonsCore;\nimport com.brandon3055.brandonscore.network.BCoreNetwork;")
    t=t.replace("net.minecraft.resources.ResourceLocation", "net.minecraft.resources.Identifier")
    t=re.sub(r"\bResourceLocation\b", "Identifier", t)
    q.write_text(t)

# TechLevel no longer needs the removed vanilla Tier type (field was unused upstream).
q=root/"src/main/java/com/brandon3055/brandonscore/api/TechLevel.java"
if q.exists():
    t=q.read_text().replace("import net.minecraft.world.item.Tier;\n","").replace("    private Tier itemTier;\n","")
    q.write_text(t)
# TargetPos identifier + Optional NBT migration.
q=root/"src/main/java/com/brandon3055/brandonscore/utils/TargetPos.java"
if q.exists():
    t=q.read_text().replace("import net.minecraft.resources.ResourceLocation;","import net.minecraft.resources.Identifier;")
    t=t.replace("ResourceLocation.parse(nbt.getString(\"dim\"))", "Identifier.parse(nbt.getString(\"dim\").orElse(\"minecraft:overworld\"))")
    t=t.replace("nbt.getDouble(\"facing_x\")", "nbt.getDouble(\"facing_x\").orElse(0D)").replace("nbt.getDouble(\"facing_y\")", "nbt.getDouble(\"facing_y\").orElse(0D)")
    q.write_text(t)

# Fix ResourceKey accessor and avoid double-applying Optional migration.
q=root/"src/main/java/com/brandon3055/brandonscore/utils/TargetPos.java"
if q.exists():
    t=q.read_text().replace(".location()", ".identifier()")
    t=t.replace(".orElse(0D).orElse(0D)", ".orElse(0D)")
    q.write_text(t)

# Port deprecated TeleportUtils to the 26.1 entity positioning signatures where direct equivalents exist.
q=root/"src/main/java/com/brandon3055/brandonscore/lib/TeleportUtils.java"
if q.exists():
    t=q.read_text()
    t=t.replace("entity.getServer()", "entity.level().getServer()")
    t=t.replace("entity.moveTo(xCoord, yCoord, zCoord, rotY, rotX)", "entity.snapTo(xCoord, yCoord, zCoord, rotY, rotX)")
    t=t.replace("movedEntity.moveTo(xCoord, yCoord, zCoord, rotY, rotX)", "movedEntity.snapTo(xCoord, yCoord, zCoord, rotY, rotX)")
    t=t.replace("entity.moveTo(entity.getX() + offsetX, entity.getY() + offsetY, entity.getZ() + offsetZ, entity.getYRot(), entity.getXRot())", "entity.snapTo(entity.getX() + offsetX, entity.getY() + offsetY, entity.getZ() + offsetZ, entity.getYRot(), entity.getXRot())")
    t=t.replace("passenger.entity.startRiding(entity, true)", "passenger.entity.startRiding(entity, true, false)")
    t=t.replace("player.teleportTo(targetWorld, xCoord, yCoord, zCoord, rotY, rotX)", "player.teleportTo(targetWorld, xCoord, yCoord, zCoord, java.util.Set.of(), rotY, rotX, false)")
    q.write_text(t)

# 26.1 cross-dimension entity fallback: recreate entity with explicit teleport spawn reason.
q=root/"src/main/java/com/brandon3055/brandonscore/lib/TeleportUtils.java"
if q.exists():
    t=q.read_text()
    t=t.replace("import net.minecraft.world.level.portal.DimensionTransition;\n","")
    if "import net.minecraft.world.entity.EntitySpawnReason;" not in t:
        t=t.replace("import net.minecraft.world.entity.Entity;","import net.minecraft.world.entity.Entity;\nimport net.minecraft.world.entity.EntitySpawnReason;")
    t=re.sub(r'        Entity movedEntity = entity\.changeDimension\(new DimensionTransition\([^\n]+\);\n        if \(movedEntity != null\) \{[\s\S]*?        \}\n\n        entity\.unRide\(\);\n        movedEntity = entity\.getType\(\)\.create\(targetWorld\);',
             '        entity.unRide();\n        Entity movedEntity = entity.getType().create(targetWorld, EntitySpawnReason.TRIGGERED);', t, count=1)
    q.write_text(t)

# BlockBCore 26.1 signature updates that are mechanically known.
q=root/"src/main/java/com/brandon3055/brandonscore/blocks/BlockBCore.java"
if q.exists():
    t=q.read_text()
    t=t.replace("import net.neoforged.neoforge.client.event.RenderHighlightEvent;\n","")
    t=re.sub(r'\n    @OnlyIn\(Dist.CLIENT\)\n    public boolean renderSelectionBox\(RenderHighlightEvent\.Block event, Level level\) \{\n        return true;\n    \}', '', t)
    t=t.replace("public void onBlockExploded(BlockState state, Level world,", "public void onBlockExploded(BlockState state, ServerLevel world,")
    if "import net.minecraft.server.level.ServerLevel;" not in t:
        t=t.replace("import net.minecraft.world.level.Level;", "import net.minecraft.world.level.Level;\nimport net.minecraft.server.level.ServerLevel;")
    q.write_text(t)

# BlockBCore imports Level through wildcard, so add explicit ServerLevel import.
q=root/"src/main/java/com/brandon3055/brandonscore/blocks/BlockBCore.java"
if q.exists():
    t=q.read_text()
    if "import net.minecraft.server.level.ServerLevel;" not in t:
        t=t.replace("import net.minecraft.stats.Stats;", "import net.minecraft.stats.Stats;\nimport net.minecraft.server.level.ServerLevel;")
    q.write_text(t)

# NeoForge 26.1 IBlockExtension pick-block signature.
q=root/"src/main/java/com/brandon3055/brandonscore/blocks/BlockBCore.java"
if q.exists():
    t=q.read_text()
    t=t.replace("public ItemStack getCloneItemStack(BlockState state, HitResult target, LevelReader level, BlockPos pos, Player player)", "public ItemStack getCloneItemStack(LevelReader level, BlockPos pos, BlockState state, boolean includeData, Player player)")
    t=t.replace("super.getCloneItemStack(state, target, level, pos, player)", "super.getCloneItemStack(level, pos, state, includeData, player)")
    q.write_text(t)

# Vanilla 26.1 neighbor update now carries redstone Orientation.
q=root/"src/main/java/com/brandon3055/brandonscore/blocks/BlockBCore.java"
if q.exists():
    t=q.read_text()
    if "net.minecraft.world.level.redstone.Orientation" not in t:
        t=t.replace("import net.minecraft.world.level.block.state.BlockState;", "import net.minecraft.world.level.block.state.BlockState;\nimport net.minecraft.world.level.redstone.Orientation;")
    t=t.replace("public void neighborChanged(BlockState state, Level world, BlockPos pos, Block blockIn, BlockPos fromPos, boolean isMoving)", "public void neighborChanged(BlockState state, Level world, BlockPos pos, Block blockIn, Orientation orientation, boolean isMoving)")
    t=t.replace("((IChangeListener) tile).onNeighborChange(fromPos);", "((IChangeListener) tile).onNeighborChange(pos);")
    t=t.replace("super.neighborChanged(state, world, pos, blockIn, fromPos, isMoving)", "super.neighborChanged(state, world, pos, blockIn, orientation, isMoving)")
    q.write_text(t)

# Block tooltip hook moved away from Block in 26.1; preserve saved-data indication through item-side port later.
q=root/"src/main/java/com/brandon3055/brandonscore/blocks/BlockBCore.java"
if q.exists():
    t=q.read_text()
    t=re.sub(r'\n    @OnlyIn \(Dist\.CLIENT\)\n    @Override\n    public void appendHoverText\([\s\S]*?\n    \}\n', '\n', t, count=1)
    q.write_text(t)

# Registry.get now returns Optional references in 26.1.
q=root/"src/main/java/com/brandon3055/brandonscore/client/hud/HudManager.java"
if q.exists():
    t=q.read_text()
    t=t.replace("hudElements.put(key, HUD_REGISTRY.get(key));", "HUD_REGISTRY.get(key).ifPresent(ref -> hudElements.put(key, ref.value()));")
    q.write_text(t)

# 26.1 Identifier rename in HUD manager.
q=root/"src/main/java/com/brandon3055/brandonscore/client/hud/HudManager.java"
if q.exists():
    t=q.read_text().replace("net.minecraft.resources.ResourceLocation","net.minecraft.resources.Identifier")
    t=re.sub(r"\\bResourceLocation\\b","Identifier",t)
    t=t.replace("Identifier.fromNamespaceAndPath(", "Identifier.fromNamespaceAndPath(")
    t=t.replace("        RenderSystem.setShaderColor(1.0F, 1.0F, 1.0F, 1.0F); //Fixes broken hud when underwater\n","")
    q.write_text(t)

# CCL 26.1 LanguageProvider merged client/server Side constructor.
q=root/"src/main/java/com/brandon3055/brandonscore/datagen/LangGenerator.java"
if q.exists():
    t=q.read_text()
    t=t.replace("public LangGenerator(DataGenerator gen, Side side) {\n        super(gen.getPackOutput(), MODID, \"en_us\", side);\n    }",
                "public LangGenerator(DataGenerator gen) {\n        super(gen.getPackOutput(), MODID, \"en_us\");\n    }")
    q.write_text(t)

# Undo Optional rewrite accidentally applied to Brigadier StringArgumentType.
for java in (root/"src/main/java/com/brandon3055/brandonscore/command").rglob("*.java"):
    t=java.read_text()
    t=re.sub(r'(StringArgumentType\.getString\([^\n;]+?\))\.orElse\(\"\"\)', r'\1', t)
    java.write_text(t)

# Property API now requires stable list ordering and internal index lookup.
q=root/"src/main/java/com/brandon3055/brandonscore/blocks/PropertyString.java"
if q.exists():
    t=q.read_text()
    t=t.replace("public Collection<String> getPossibleValues() {\n        return Collections.unmodifiableSet(valuesSet);\n    }",
                "public List<String> getPossibleValues() {\n        return Collections.unmodifiableList(Arrays.asList(metaLookup));\n    }")
    marker='    public int toMeta(String value) {'
    if "getInternalIndex" not in t:
        t=t.replace(marker, '    @Override\n    public int getInternalIndex(String value) {\n        return ArrayUtils.indexOf(metaLookup, value.intern());\n    }\n\n'+marker)
    q.write_text(t)

# Minecraft 26.1 moved render types into renderer.rendertype.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=t.replace("net.minecraft.client.renderer.RenderType", "net.minecraft.client.renderer.rendertype.RenderType")
    t=t.replace("net.minecraft.client.renderer.RenderStateShard", "net.minecraft.client.renderer.rendertype.RenderStateShard")
    java.write_text(t)
