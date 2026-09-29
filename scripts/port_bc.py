from pathlib import Path
import re
root=Path("bc")
p=root/"gradle.properties"
s=p.read_text().replace("mc_version=1.20.1","mc_version=26.1.2").replace("neo_version=47.1.96","neo_version=26.1.2.106")
p.write_text(s)
p=root/"build.gradle"
s=p.read_text()
s=re.sub(r"id 'com.github.johnrengelman.shadow'.*\n","",s)
s=re.sub(r"id 'net.neoforged.gradle'.*\n","    id 'net.neoforged.moddev' version '2.0.147'\n",s)
s=re.sub(r"id 'org.spongepowered.mixin'.*\n","",s)
s=s.replace("JavaLanguageVersion.of(17)","JavaLanguageVersion.of(25)")
# Replace legacy minecraft/mixin/configuration setup with ModDevGradle.
a=s.index("minecraft {")
b=s.index("\nrepositories {",a)
neo="""neoForge {
    version = neo_version
    mods {
        brandonscore {
            sourceSet(sourceSets.main)
        }
    }
}

"""
s=s[:a]+neo+s[b:]
# local CCL jar built by workflow
a=s.index("dependencies {")
b=s.index("\nprocessResources {",a)
deps="""dependencies {
    implementation files("../ccl/build/libs/" + file("../ccl/build/libs").list().find { it.endsWith(".jar") && !it.contains("sources") && !it.contains("javadoc") })
}

"""
s=s[:a]+deps+s[b:]
# Remove obsolete reobf finalizer.
s=s.replace("    finalizedBy 'reobfJar'\n","").replace("    dependsOn(\"reobfJar\")\n","")
p.write_text(s)

w=root/"gradle/wrapper/gradle-wrapper.properties"
if w.exists():
    t=w.read_text()
    t=re.sub(r"gradle-[0-9.]+-(bin|all)\\.zip", "gradle-9.1.0-bin.zip", t)
    w.write_text(t)

# Force legacy wrapper URL forward for Java 25.
w=root/"gradle/wrapper/gradle-wrapper.properties"
if w.exists():
    w.write_text(w.read_text().replace("gradle-8.1-bin.zip", "gradle-9.1.0-bin.zip"))

# Gradle 9 removed archivesBaseName project property.
p=root/"build.gradle"
t=p.read_text()
t=t.replace('archivesBaseName = "BrandonsCore"', 'base { archivesName = "BrandonsCore" }\ndef archivesBaseName = "BrandonsCore"')
p.write_text(t)

p=root/"build.gradle"
t=p.read_text()
t=t.replace('def archivesBaseName = "BrandonsCore"', '')
t=t.replace('archivesBaseName', '"BrandonsCore"')
# Repair any accidental quoted assignment if encountered.
t=t.replace('"BrandonsCore" = "BrandonsCore"', 'base { archivesName = "BrandonsCore" }')
p.write_text(t)

# Repair interpolation damaged by legacy archivesBaseName replacement.
p=root/"build.gradle"
t=p.read_text()
t=t.replace('$"BrandonsCore"', 'BrandonsCore')
t=t.replace('"libs/BrandonsCore-$version-publishing.json"', '"libs/BrandonsCore-$version-publishing.json"')
p.write_text(t)

# Replace all bare BrandonsCore identifiers introduced by the legacy archive-name rewrite.
p=root/"build.gradle"
t=p.read_text()
t=re.sub(r'(?<!["\'])\bBrandonsCore\b(?!["\'])', '"BrandonsCore"', t)
# Restore publication declaration syntax, where BrandonsCore is a publication name.
t=t.replace('"BrandonsCore"(MavenPublication)', 'BrandonsCore(MavenPublication)')
p.write_text(t)

# Publishing is irrelevant to local port builds and still references removed legacy Gradle properties.
p=root/"build.gradle"
t=p.read_text()
idx=t.find("\npublishing {")
if idx != -1:
    t=t[:idx]+"\n"
p.write_text(t)

# The publishing metadata variable sits before the publishing block; remove it too.
p=root/"build.gradle"
t=p.read_text()
t=re.sub(r'\ndef publishingMetadata = .*?\n', '\n', t)
t=re.sub(r'\ndef publishingMetadataTask = tasks\.register\("publishingMetadata"\) \{[\s\S]*?\n\}\n\n', '\n', t, count=1)
p.write_text(t)

# BrandonsCore master is still Forge-namespaced. NeoForge kept most APIs under equivalent net.neoforged paths.
for java in (root/"src/main/java").rglob("*.java"):
    t=java.read_text()
    t=t.replace("net.minecraftforge.", "net.neoforged.neoforge.")
    java.write_text(t)
