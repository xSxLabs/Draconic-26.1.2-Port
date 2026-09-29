from pathlib import Path
import re

root = Path("ccl")
p = root / "gradle.properties"
s = p.read_text()
s = s.replace("mc_version=1.21.11", "mc_version=26.1.2")
s = s.replace("forge_version=21.11.42", "forge_version=26.1.2.106")
p.write_text(s)

p = root / "build.gradle"
s = p.read_text().replace("JavaLanguageVersion.of(21)", "JavaLanguageVersion.of(25)")
s = re.sub(r'\n\s*compileOnly\("mezz\.jei:jei-\$\{mc_version\}-neoforge:\$\{jei_version\}"\) \{\s*transitive false\s*\}\s*', '\n', s)
p.write_text(s)

replacements = {
    "net.minecraft.client.renderer.block.model.BakedQuad": "net.minecraft.client.resources.model.geometry.BakedQuad",
    "net.minecraft.client.resources.model.QuadCollection": "net.minecraft.client.resources.model.geometry.QuadCollection",
    "net.minecraft.client.renderer.block.model.BlockModelPart": "net.minecraft.client.renderer.block.dispatch.BlockStateModelPart",
    "BlockModelPart": "BlockStateModelPart",
    "net.minecraft.world.level.BlockAndTintGetter": "net.minecraft.world.level.BlockAndLightGetter",
    "BlockAndTintGetter": "BlockAndLightGetter",
    "net.minecraft.client.gui.GuiGraphics": "net.minecraft.client.gui.GuiGraphicsExtractor",
    "net.minecraft.client.gui.render.state.": "net.minecraft.client.renderer.state.gui.",
    "net.minecraft.world.inventory.ClickType": "net.minecraft.world.inventory.ContainerInput",
}
for java in (root / "src/main/java").rglob("*.java"):
    t = java.read_text()
    for a, b in replacements.items():
        t = t.replace(a, b)
    t = re.sub(r"\bGuiGraphics\b", "GuiGraphicsExtractor", t)
    t = re.sub(r"\bClickType\b", "ContainerInput", t)
    t = t.replace("net.minecraft.client.gui.GuiGraphicsExtractorExtractor", "net.minecraft.client.gui.GuiGraphicsExtractor")
    t = t.replace("net.minecraft.client.renderer.state.BlockOutlineRenderState", "net.minecraft.client.renderer.state.level.BlockOutlineRenderState")
    if "net.minecraft.client.resources.model.Material" in t:
        t = t.replace("net.minecraft.client.resources.model.Material", "net.minecraft.client.resources.model.sprite.SpriteId")
        t = re.sub(r"\bMaterial\b", "SpriteId", t)
    t = t.replace("RenderLevelStageEvent.AfterParticles", "RenderLevelStageEvent.AfterTranslucentParticles")
    t = t.replace("LevelRenderer.getLightColor(", "LevelRenderer.getLightCoords(")
    for a,b in {
        ".drawString(": ".text(",
        ".drawCenteredString(": ".centeredText(",
        ".renderItemDecorations(": ".itemDecorations(",
        ".renderTooltip(": ".tooltip(",
        ".renderFakeItem(": ".fakeItem(",
        ".renderItem(": ".item(",
        ".renderOutline(": ".outline(",
        ".hLine(": ".horizontalLine(",
        ".vLine(": ".verticalLine(",
    }.items():
        t = t.replace(a,b)
    t = re.sub(r"\b(world|level)\.random\.", r"\1.getRandom().", t)
    java.write_text(t)

q = root / "src/main/java/codechicken/lib/model/Quad.java"
t = q.read_text()
t = t.replace("import net.neoforged.neoforge.client.model.quad.BakedColors;", "import net.neoforged.neoforge.client.model.quad.BakedColors;\nimport net.neoforged.neoforge.client.model.quad.MutableQuad;")
t = t.replace("        var normals = quad.bakedNormals();\n        var colors = quad.bakedColors();", "        var mq = new MutableQuad().setFrom(quad);\n        var normals = quad.bakedNormals();\n        var colors = quad.bakedColors();")
t = t.replace("        tintIndex = quad.tintIndex();\n        direction = quad.direction();\n        sprite = quad.sprite();\n        shade = quad.shade();\n        lightEmission = quad.lightEmission();\n        ambientOcclusion = quad.hasAmbientOcclusion();", "        tintIndex = mq.tintIndex();\n        direction = mq.direction();\n        sprite = mq.sprite();\n        shade = mq.shade();\n        lightEmission = mq.lightEmission();\n        ambientOcclusion = mq.hasAmbientOcclusion();")
start = t.index("    public BakedQuad bake() {")
end = t.index("\n    private static float interpColor", start)
new_bake = """    public BakedQuad bake() {
        var mq = new MutableQuad();
        mq.setDirection(requireNonNull(direction, "Direction not computed."));
        mq.setSprite(requireNonNull(sprite, "Quad requires a sprite."), net.minecraft.client.renderer.chunk.ChunkSectionLayer.SOLID, net.minecraft.client.renderer.Sheets.cutoutBlockItemSheet());
        mq.setTintIndex(tintIndex).setShade(shade).setLightEmission(lightEmission).setAmbientOcclusion(ambientOcclusion);
        for (int i = 0; i < 4; i++) {
            mq.setPosition(i, vertices[i].vec.vector3f());
            mq.setPackedUv(i, vertices[i].packUV());
            mq.setNormal(i, (float) vertices[i].normal.x, (float) vertices[i].normal.y, (float) vertices[i].normal.z);
            mq.setColor(i, vertices[i].color);
        }
        return mq.toBakedQuad();
    }
"""
t = t[:start] + new_bake + t[end:]
q.write_text(t)

for pth in ["codechicken/lib/render/CCRenderState.java", "codechicken/lib/render/RenderUtils.java"]:
    p = root / "src/main/java" / pth
    if p.exists():
        t = p.read_text().replace("getTintColor(fluidStack)", "getTintColor()").replace("getTintColor(stack)", "getTintColor()").replace("getStillTexture(stack)", "getStillTexture()")
        p.write_text(t)

p = root / "src/main/java/codechicken/lib/render/particle/CustomBreakingParticle.java"
if p.exists():
    p.write_text(p.read_text().replace("Layer.TERRAIN", "Layer.OPAQUE_TERRAIN"))

p = root / "src/main/java/codechicken/lib/render/CCRenderPipelines.java"
if p.exists():
    t = p.read_text()
    t = t.replace("import com.mojang.blaze3d.pipeline.RenderPipeline;", "import com.mojang.blaze3d.pipeline.RenderPipeline;\nimport com.mojang.blaze3d.pipeline.DepthStencilState;\nimport com.mojang.blaze3d.platform.CompareOp;")
    t = t.replace(".withDepthWrite(true)", ".withDepthStencilState(new DepthStencilState(CompareOp.LESS_THAN_OR_EQUAL, true, 0f, 0f))")
    t = t.replace(".withDepthWrite(false)", ".withDepthStencilState(new DepthStencilState(CompareOp.LESS_THAN_OR_EQUAL, false, 0f, 0f))")
    p.write_text(t)

jei = root / "src/main/java/codechicken/lib/internal/compat/JEIPlugin.java"
if jei.exists():
    jei.unlink()
