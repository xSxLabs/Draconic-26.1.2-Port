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
