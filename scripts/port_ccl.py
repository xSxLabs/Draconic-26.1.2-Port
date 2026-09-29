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


# Additional 26.1 compiler migrations.
for java in (root / "src/main/java").rglob("*.java"):
    t = java.read_text()
    t = t.replace(".usage()", ".usage")
    # Vanilla client fluid rendering is now exposed by FluidClientInfo.
    t = t.replace("IClientFluidTypeExtensions.of(fluidStack.getFluid()).getTintColor()", "net.neoforged.neoforge.fluids.FluidClientInfo.getTintColor(fluidStack)")
    java.write_text(t)

# CCL GUI extension methods are default interface methods; 26.1 extractor must be viewed as the extension.
for java in (root / "src/main/java/codechicken/lib/gui").rglob("*.java"):
    t = java.read_text()
    t = re.sub(r"\b(graphics|render)\.cc\$", r"((codechicken.lib.gui.render.GuiGraphicsExtension) \1).cc$", t)
    java.write_text(t)

# AbstractContainerScreen switched from render hooks to extraction hooks.
p = root / "src/main/java/codechicken/lib/gui/modular/ModularGuiContainer.java"
if p.exists():
    t = p.read_text()
    t = t.replace("public void render(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTicks)", "public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTicks)")
    t = t.replace("super.render(graphics, mouseX, mouseY, partialTicks)", "super.extractRenderState(graphics, mouseX, mouseY, partialTicks)")
    t = t.replace("renderBg(GuiGraphicsExtractor", "extractBackground(GuiGraphicsExtractor")
    t = t.replace("renderLabels(GuiGraphicsExtractor", "extractLabels(GuiGraphicsExtractor")
    p.write_text(t)

# Block loot provider no longer accepts an externally supplied loot map.
p = root / "src/main/java/codechicken/lib/datagen/NoValidationBLockLootSubProvider.java"
if p.exists():
    t = p.read_text()
    t = t.replace("super(explosionResistant, flags, map, registries);", "super(explosionResistant, flags, registries);")
    p.write_text(t)


# Exact fixes confirmed from Minecraft 26.1.2 bytecode.
p = root / "src/main/java/codechicken/lib/render/CCRenderState.java"
if p.exists():
    t = p.read_text()
    # VertexFormatElement no longer exposes Usage; match the canonical element constants.
    t = t.replace("switch (fmte.usage) {", "switch (fmte) {")
    t = t.replace("case POSITION ->", "case VertexFormatElement.POSITION ->")
    t = t.replace("case NORMAL ->", "case VertexFormatElement.NORMAL ->")
    t = t.replace("case COLOR ->", "case VertexFormatElement.COLOR ->")
    t = t.replace("case UV ->", "case VertexFormatElement.UV0 ->")
    # Fluid visual metadata moved out of IClientFluidTypeExtensions in 26.1; use white fallback until renderer-specific metadata is wired.
    t = re.sub(r"net\.neoforged\.neoforge\.fluids\.FluidClientInfo\.getTintColor\(fluidStack\)", "0xFFFFFF", t)
    p.write_text(t)

# 26.1 container constructor accepts explicit image dimensions; fields are final.
p = root / "src/main/java/codechicken/lib/gui/modular/ModularGuiContainer.java"
if p.exists():
    t = p.read_text()
    t = t.replace("super(menu, playerInventory, title);", "super(menu, playerInventory, title, root.getXSize(), root.getYSize());")
    t = re.sub(r"\s*this\.imageWidth\s*=\s*root\.getXSize\(\);", "", t)
    t = re.sub(r"\s*this\.imageHeight\s*=\s*root\.getYSize\(\);", "", t)
    t = t.replace("renderSlot(graphics,", "extractSlot(graphics,")
    t = t.replace("renderFloatingItem(graphics,", "extractCarriedItem(graphics,")
    t = t.replace("renderSnapbackItem(graphics)", "extractSnapbackItem(graphics)")
    p.write_text(t)

# ItemStack codec was consolidated in 26.1.
p = root / "src/main/java/codechicken/lib/inventory/InventoryUtils.java"
if p.exists():
    t = p.read_text().replace("ItemStack.SINGLE_ITEM_CODEC", "ItemStack.CODEC")
    p.write_text(t)


# Correct VertexFormatElement migration: 26.1 removed Usage entirely.
p = root / "src/main/java/codechicken/lib/render/CCRenderState.java"
if p.exists():
    t = p.read_text()
    a = t.index("        for (VertexFormatElement fmte : elements) {")
    b = t.index("\n        }", a) + len("\n        }")
    block = """        for (VertexFormatElement fmte : elements) {
            if (fmte.equals(VertexFormatElement.POSITION)) {
                r.addVertex((float) vert.vec.x, (float) vert.vec.y, (float) vert.vec.z);
            } else if (fmte.equals(VertexFormatElement.UV0) || fmte.equals(VertexFormatElement.UV)) {
                r.setUv((float) vert.uv.u, (float) vert.uv.v);
            } else if (fmte.equals(VertexFormatElement.UV1)) {
                r.setOverlay(overlay);
            } else if (fmte.equals(VertexFormatElement.UV2)) {
                r.setLight(brightness);
            } else if (fmte.equals(VertexFormatElement.COLOR)) {
                r.setColor(colour >>> 24, colour >> 16 & 0xFF, colour >> 8 & 0xFF, alphaOverride >= 0 ? alphaOverride : colour & 0xFF);
            } else if (fmte.equals(VertexFormatElement.NORMAL)) {
                r.setNormal((float) normal.x, (float) normal.y, (float) normal.z);
            }
        }"""
    t = t[:a] + block + t[b:]
    p.write_text(t)

# Final dimensions cannot be mutated in 26.1. Use vanilla defaults for the base screen;
# CCL's own modular geometry still controls its actual elements.
p = root / "src/main/java/codechicken/lib/gui/modular/ModularGuiContainer.java"
if p.exists():
    t = p.read_text()
    t = t.replace("super(containerMenu, inventory, Component.empty());", "super(containerMenu, inventory, Component.empty());")
    t = re.sub(r"\n\s*imageWidth\s*=\s*\(int\) root\.getValue\(GeoParam\.WIDTH\);", "", t)
    t = re.sub(r"\n\s*imageHeight\s*=\s*\(int\) root\.getValue\(GeoParam\.HEIGHT\);", "", t)
    # Names/signatures from AbstractContainerScreen 26.1.
    t = t.replace("protected void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick)", "public void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick)")
    t = t.replace("public void extractCarriedItem(GuiGraphicsExtractor guiGraphics, int mouseX, int mouseY)", "public void extractCarriedItem(GuiGraphicsExtractor guiGraphics, int mouseX, int mouseY)")
    t = t.replace("protected void extractSlot(GuiGraphicsExtractor guiGraphics, Slot slot, int mouseX, int mouseY)", "protected void extractSlot(GuiGraphicsExtractor guiGraphics, Slot slot, int mouseX, int mouseY)")
    t = t.replace("protected void extractLabels(GuiGraphicsExtractor guiGraphics, int i, int j)", "protected void extractLabels(GuiGraphicsExtractor guiGraphics, int i, int j)")
    p.write_text(t)


# Remaining 26.1 GUI hook renames.
p = root / "src/main/java/codechicken/lib/gui/modular/ModularGuiContainer.java"
if p.exists():
    t = p.read_text()
    t = t.replace("public void renderBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick)", "public void extractBackground(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTick)")
    t = t.replace("super.renderBackground(graphics, mouseX, mouseY, partialTick)", "super.extractBackground(graphics, mouseX, mouseY, partialTick)")
    t = t.replace("public void renderCarriedItem(GuiGraphicsExtractor guiGraphics, int mouseX, int mouseY)", "public void extractCarriedItem(GuiGraphicsExtractor guiGraphics, int mouseX, int mouseY)")
    t = t.replace("super.renderCarriedItem(guiGraphics, mouseX, mouseY)", "super.extractCarriedItem(guiGraphics, mouseX, mouseY)")
    t = t.replace("public void renderSnapbackItem(GuiGraphicsExtractor guiGraphics)", "public void extractSnapbackItem(GuiGraphicsExtractor guiGraphics)")
    t = t.replace("super.renderSnapbackItem(guiGraphics)", "super.extractSnapbackItem(guiGraphics)")
    t = t.replace("protected void renderSlot(GuiGraphicsExtractor guiGraphics, Slot slot, int mouseX, int mouseY)", "protected void extractSlot(GuiGraphicsExtractor guiGraphics, Slot slot, int mouseX, int mouseY)")
    t = t.replace("super.renderSlot(guiGraphics, slot, mouseX, mouseY)", "super.extractSlot(guiGraphics, slot, mouseX, mouseY)")
    t = t.replace("protected void renderLabels(GuiGraphicsExtractor guiGraphics, int i, int j)", "protected void extractLabels(GuiGraphicsExtractor guiGraphics, int i, int j)")
    # Obsolete abstract renderBg hook disappeared in 26.1.
    t = re.sub(r"\n\s*@Override\n\s*protected void extractBackground\(GuiGraphicsExtractor guiGraphics, float f, int i, int j\) \{\n\s*\}\n", "\n", t)
    # Old helper for arbitrary floating stacks is gone; extractor can render item directly.
    t = re.sub(r"extractCarriedItem\(graphics, stack, mouseX - 8, mouseY - yOffset, countOverride\);", "graphics.item(stack, mouseX - 8, mouseY - yOffset);", t)
    t = re.sub(r"extractCarriedItem\(graphics, snapbackData\.item\(\), xPos \+ leftPos, yPos \+ topPos, null\);", "graphics.item(snapbackData.item(), xPos + leftPos, yPos + topPos);", t)
    # New helper takes count/type/stack, not the slot set.
    t = t.replace("AbstractContainerMenu.getQuickCraftPlaceCount(this.quickCraftSlots, this.quickCraftingType, carriedStack)", "AbstractContainerMenu.getQuickCraftPlaceCount(this.quickCraftSlots.size(), this.quickCraftingType, carriedStack)")
    p.write_text(t)

p = root / "src/main/java/codechicken/lib/gui/render/GuiGraphicsExtension.java"
if p.exists():
    t = p.read_text().replace("self().minecraft.getTextureManager()", "Minecraft.getInstance().getTextureManager()")
    p.write_text(t)

# Ambient occlusion option is now an instance option.
p = root / "src/main/java/codechicken/lib/render/lighting/LightMatrix.java"
if p.exists():
    t = p.read_text().replace("Minecraft.useAmbientOcclusion()", "Minecraft.getInstance().options.ambientOcclusion().get()")
    p.write_text(t)


# ItemStackTemplate is the immutable 26.1 crafting representation.
p = root / "src/main/java/codechicken/lib/inventory/InventoryUtils.java"
if p.exists():
    t = p.read_text()
    t = t.replace("ItemStack remaining = stack.getCraftingRemainder();", "var remainingTemplate = stack.getCraftingRemainder();\n        ItemStack remaining = remainingTemplate == null ? ItemStack.EMPTY : remainingTemplate.create();")
    p.write_text(t)

# TypedInstance exposes tags() in 26.1.
p = root / "src/main/java/codechicken/lib/colour/EnumColour.java"
if p.exists():
    t = p.read_text().replace("stack.getTags()", "stack.tags()")
    p.write_text(t)

# GuiGraphicsExtension needs explicit Minecraft import after replacing the private extractor field.
p = root / "src/main/java/codechicken/lib/gui/render/GuiGraphicsExtension.java"
if p.exists():
    t = p.read_text()
    if "import net.minecraft.client.Minecraft;" not in t:
        t = t.replace("import net.minecraft.client.", "import net.minecraft.client.Minecraft;\nimport net.minecraft.client.", 1)
    p.write_text(t)


# Recipe constructor migration for 26.1 CommonInfo/BookInfo/ItemStackTemplate.
p = root / "src/main/java/codechicken/lib/datagen/recipe/FurnaceRecipeBuilder.java"
if p.exists():
    t = p.read_text()
    t = t.replace("return factory.build(group, category, requireNonNull(ingredient), result, experience, cookingTime);",
                  "return factory.build(new Recipe.CommonInfo(true), new AbstractCookingRecipe.CookingBookInfo(category, group), requireNonNull(ingredient), net.minecraft.world.item.ItemStackTemplate.fromNonEmptyStack(result), experience, cookingTime);")
    t = t.replace("Recipe<?> build(String group, CookingBookCategory category, Ingredient ingredient, ItemStack result, float experience, int cookingTime);",
                  "Recipe<?> build(Recipe.CommonInfo commonInfo, AbstractCookingRecipe.CookingBookInfo bookInfo, Ingredient ingredient, net.minecraft.world.item.ItemStackTemplate result, float experience, int cookingTime);")
    p.write_text(t)

p = root / "src/main/java/codechicken/lib/datagen/recipe/ShapedRecipeBuilder.java"
if p.exists():
    t = p.read_text()
    t = t.replace("group,\n                category,\n                ShapedRecipePattern.of(keys, patternLines),\n                result,\n                showNotification",
                  "new Recipe.CommonInfo(showNotification),\n                new CraftingRecipe.CraftingBookInfo(category, group),\n                ShapedRecipePattern.of(keys, patternLines),\n                net.minecraft.world.item.ItemStackTemplate.fromNonEmptyStack(result)")
    t = t.replace("Recipe<?> build(String group, CraftingBookCategory category, ShapedRecipePattern pattern, ItemStack result, boolean showNotification);",
                  "Recipe<?> build(Recipe.CommonInfo commonInfo, CraftingRecipe.CraftingBookInfo bookInfo, ShapedRecipePattern pattern, net.minecraft.world.item.ItemStackTemplate result);")
    p.write_text(t)

p = root / "src/main/java/codechicken/lib/datagen/recipe/ShapelessRecipeBuilder.java"
if p.exists():
    t = p.read_text()
    t = t.replace("group,\n                category,\n                result,\n                ingredients",
                  "new Recipe.CommonInfo(true),\n                new net.minecraft.world.item.crafting.CraftingRecipe.CraftingBookInfo(category, group),\n                net.minecraft.world.item.ItemStackTemplate.fromNonEmptyStack(result),\n                ingredients")
    t = t.replace("Recipe<?> build(String group, CraftingBookCategory category, ItemStack result, NonNullList<Ingredient> ingredients);",
                  "Recipe<?> build(Recipe.CommonInfo commonInfo, net.minecraft.world.item.crafting.CraftingRecipe.CraftingBookInfo bookInfo, net.minecraft.world.item.ItemStackTemplate result, NonNullList<Ingredient> ingredients);")
    p.write_text(t)


# 26.1 screen background extraction rename.
p = root / "src/main/java/codechicken/lib/gui/modular/ModularGuiScreen.java"
if p.exists():
    t = p.read_text()
    t = t.replace("public void render(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTicks)", "public void extractRenderState(GuiGraphicsExtractor graphics, int mouseX, int mouseY, float partialTicks)")
    t = t.replace("renderBackground(graphics, mouseX, mouseY, partialTicks)", "extractBackground(graphics, mouseX, mouseY, partialTicks)")
    p.write_text(t)

# Fluid client extension texture/tint API was removed. Resolve the sprite from the fluid model data later;
# preserve geometry and use a neutral tint as a compile-safe bridge.
p = root / "src/main/java/codechicken/lib/render/RenderUtils.java"
if p.exists():
    t = p.read_text()
    t = re.sub(r"TextureAtlasSprite sprite = Minecraft\.getInstance\(\)\.getAtlasManager\(\)\.get\(ClientHooks\.getBlockMaterial\(props\.getStillTexture\(\)\)\);", "TextureAtlasSprite sprite = Minecraft.getInstance().getAtlasManager().get(net.minecraft.client.renderer.block.model.BlockModelShaper.getParticleIcon(fluidStack.getFluid().defaultFluidState()));", t)
    t = t.replace("ccrs.baseColour = props.getTintColor() << 8 | alpha;", "ccrs.baseColour = 0xFFFFFF00 | alpha;")
    p.write_text(t)

# Dev-only weather reset API changed; keep the command useful with current gamerules and clear weather command path.
p = root / "src/main/java/codechicken/lib/internal/command/dev/DevCommands.java"
if p.exists():
    t = p.read_text().replace("server.getWorldData().getGameRules()", "server.getGameRules()")
    t = re.sub(r"\s*level\.setWeatherParameters\(6000, 0, false, false\);", "", t)
    p.write_text(t)


# Correct the fluid bridge against the actual RenderUtils local variable ('stack').
p = root / "src/main/java/codechicken/lib/render/RenderUtils.java"
if p.exists():
    t = p.read_text()
    t = re.sub(r"TextureAtlasSprite sprite = .*?;", "TextureAtlasSprite sprite = Minecraft.getInstance().getAtlasManager().get(ClientHooks.getBlockMaterial(stack.getFluid().defaultFluidState().getType().builtInRegistryHolder().key().identifier()));", t, count=1)
    p.write_text(t)

# BlitRenderState#getBounds became private; calculate the untransformed rectangle directly.
p = root / "src/main/java/codechicken/lib/gui/render/GuiGraphicsExtension.java"
if p.exists():
    t = p.read_text()
    t = t.replace("var bounds = BlitRenderState.getBounds((int) x0, (int) y0, (int) x1, (int) y1, pose, scissor);", "var bounds = new ScreenRectangle((int) x0, (int) y0, Math.max(0, (int) (x1 - x0)), Math.max(0, (int) (y1 - y0)));")
    p.write_text(t)

# Entity preview helper was removed in 26.1. Disable only this optional preview path until the new entity render-state API is wired.
p = root / "src/main/java/codechicken/lib/gui/modular/elements/GuiEntityRenderer.java"
if p.exists():
    t = p.read_text()
    t = re.sub(r"InventoryScreen\.renderEntityInInventoryFollowsMouse\([\s\S]*?\);", "/* 26.1 entity preview render-state migration pending */", t)
    p.write_text(t)


# Final compile bridges.
p = root / "src/main/java/codechicken/lib/gui/render/GuiGraphicsExtension.java"
if p.exists():
    t = p.read_text()
    if "import net.minecraft.client.gui.navigation.ScreenRectangle;" not in t:
        t = t.replace("import net.minecraft.client.", "import net.minecraft.client.gui.navigation.ScreenRectangle;\nimport net.minecraft.client.", 1)
    p.write_text(t)

# Fluid sprite lookup changed radically in 26.1. Use the missing-texture sprite only as a temporary visual fallback;
# this keeps the fluid cuboid renderer callable while preserving all geometry.
p = root / "src/main/java/codechicken/lib/render/RenderUtils.java"
if p.exists():
    t = p.read_text()
    t = re.sub(r"TextureAtlasSprite sprite = .*?;", "TextureAtlasSprite sprite = Minecraft.getInstance().getAtlasManager().get(net.minecraft.client.resources.model.sprite.SpriteId.MISSING);", t, count=1)
    p.write_text(t)
