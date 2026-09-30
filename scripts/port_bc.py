from pathlib import Path
import re
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

# Deprecated teleport utility is not used by current DE core and depends on removed DimensionTransition.
p=root/"src/main/java/com/brandon3055/brandonscore/lib/TeleportUtils.java"
if p.exists(): p.unlink()

# CCL master has removed the old modular GUI/sprite/shader stack. Temporarily exclude BC client modules tied exclusively to that removed API.
for rel in [
"client/BCGuiTextures.java","client/shader/BCShader.java","client/shader/ContribShader.java",
"client/model/ContributorModel.java","client/model/EquippedItemModelLayer.java",
"client/hud/HudManager.java","client/hud/HudDataElement.java",
"api/hud/AbstractHudElement.java","api/hud/IHudDisplay.java"]:
    q=root/"src/main/java/com/brandon3055/brandonscore"/rel
    if q.exists(): q.unlink()

# Exclude the remainder of BC's legacy client implementation for the server/core compatibility pass.
client=root/"src/main/java/com/brandon3055/brandonscore/client"
if client.exists():
    import shutil
    shutil.rmtree(client)
p=root/"src/main/java/com/brandon3055/brandonscore/init/BCClient.java"
if p.exists(): p.unlink()

# Remove references to the disabled client bootstrap from common code.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=re.sub(r"^import com\.brandon3055\.brandonscore\.init\.BCClient;\n","",t,flags=re.M)
    t=re.sub(r"^.*BCClient\..*;\n","",t,flags=re.M)
    java.write_text(t)
