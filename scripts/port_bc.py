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
    implementation files("../ccl/build/libs/" + file("../ccl/build/libs").list().find { it.endsWith(".jar") && !it.contains("sources") && !it.contains("javadoc") })
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
