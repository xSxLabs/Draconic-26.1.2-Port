from pathlib import Path
root=Path("bc/src/main/java")
for java in root.rglob("*.java"):
    t=java.read_text()
    t=t.replace('getBoolean("detectPassive")','getBoolean("detectPassive").orElse(false)')
    t=t.replace('getBoolean("detectHostile")','getBoolean("detectHostile").orElse(false)')
    t=t.replace('getBoolean("detectPlayer")','getBoolean("detectPlayer").orElse(false)')
    t=t.replace('getBoolean("detectOther")','getBoolean("detectOther").orElse(false)')
    t=t.replace('getBoolean("isWhiteList")','getBoolean("isWhiteList").orElse(false)')
    java.write_text(t)
