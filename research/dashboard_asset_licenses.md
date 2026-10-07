# Dashboard Asset Licenses

Audit/replacement date: 2026-10-07. This manifest records dashboard asset replacements. The hero replacement is documented first; the fire-overlay replacement is documented below.

## Asset: Optional dashboard hero fly illustration

### Asset

Original: `dashboard assests/fly_hero_transparent.png` (430 ? 310 px; 205,352 bytes; PNG). The project ledger records visual-only usage and no source for its creator or generation method; this audit does not assert that it was AI-generated.

Replacement: `dashboard assests/fly_hero_human_commons_ccby.png` (285 ? 170 px; 37,482 bytes; RGBA PNG). The renderer fits it inside the existing 285 ? 285 px hero box while preserving aspect ratio.

### Source

Creator: DataBase Center for Life Science (DBCLS). Wikimedia Commons lists DBCLS as author; the vector record cites the DBCLS Togopic illustration page.

Source page: [201902 Drosophila melanogaster.svg](https://commons.wikimedia.org/wiki/File:201902_Drosophila_melanogaster.svg) ? [DBCLS source record](https://doi.org/10.7875/togopic.2019.02).

Direct asset URL: <https://thumb.wikimedia.org/wikipedia/commons/thumb/d/d1/201902_Drosophila_melanogaster.svg/960px-201902_Drosophila_melanogaster.svg.png>

License: [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/). Attribution required.

Attribution: ?Drosophila melanogaster, DBCLS, CC BY 4.0, Wikimedia Commons; cropped and resized.? No endorsement is implied.

Human-made evidence: the Commons file record identifies an institutional author and the original SVG source; the illustration is credited to DBCLS and is linked to its Togopic source record. The asset is used as a decorative fly illustration only, not as MN5, Giant Fiber, MaleCNS, EM, connectome, or measured anatomy.

### Usage

Dashboard location: optional fallback hero in `brain_dashboard.py::_hero` via `HERO_ASSET_PATH`; the dashboard layout and behavior remain unchanged. The displayed illustration occupies the same contain-fit 285 ? 285 px box.

Visual role: decorative Drosophila illustration beside the live functional-group map.

### Processing

Original project asset dimensions: 430 ? 310 px.

Replacement source dimensions: 512 ? 512 px SVG; downloaded raster derivative 960 ? 960 px PNG, 72,288 bytes.

Final dimensions: 285 ? 170 px.

Original project asset size: 205,352 bytes.

Final size: 37,482 bytes.

Format: RGBA PNG, preserving transparency; required by the dependency-free dashboard PNG loader.

Compression: PNG produced by rasterizing and high-quality bicubic downsampling from the Wikimedia 960 px PNG derivative; output uses standard PNG encoding. Dashboard output remains PNG with existing zlib compression level 6.

Crop method: trim transparent canvas to nontransparent bounding box `(x=107, y=352, width=606, height=362)` in the 960 ? 960 source raster, then resample to 285 ? 170. The full illustrated fly is retained.

Quality check: project PNG loader accepts the replacement; alpha remains transparent; it was visually reviewed at the dashboard display size and tested in the existing fallback renderer.

## Other active visual assets reviewed

The 120 active 96 ? 96 behavior-frame PNGs across 15 non-MATE states, the overload GIF, and the two remaining command overlays remain unchanged. Their presentation role is documented, but the pack does not provide named creators or reuse licenses. Online search located licensed individual illustrations and photographs, but no complete human-made animation set matching those states and behaviors. Those assets remain `NO_SUITABLE_REPLACEMENT_FOUND` in the replacement log. The MATE animation state and the separate 40 MATE assets were excluded by task scope and left untouched. The five `sprites/*.gif` files are not attached by the current Discord command path and were not candidates.

## Asset: Fire/burn command overlay

### Asset

Original: `dashboard assests/fly_behavior_assets_codex_v2/effects/fire_overlay.png` (102 x 102 px; 21,805 bytes; PNG; SHA-256 `EDA9CA22FE154C1DA1C5170DCD032EA5BD1F3E388B39454C608573D8A415E348`). The pack did not identify its creator or reuse license.

Replacement: `dashboard assests/fly_behavior_assets_codex_v2/effects/fire_overlay.png` (102 x 102 px; 3,238 bytes; RGBA PNG; SHA-256 `F3401A4B19ED0AEFDD8308AB8B69DF1AACE24C2998953BADEF32E9F97358BE0D`). The existing filename and square footprint are retained.

Visual role: decorative/UI fire illustration for the existing `FIRE (BURN)` state. This asset is not biological data. The burn/high-temperature trigger, visual-state mapping, dashboard layout, and label meaning were not changed.

### Source and license

Creator: Carl Olsen. The Commons record attributes the icon to Carl Olsen and identifies Game-icons.net as its source.

Source page: [Flame – Carl Olsen – white – game-icons.svg](https://commons.wikimedia.org/wiki/File:Flame_-_Carl_Olsen_-_white_-_game-icons.svg).

Direct source SVG: <https://upload.wikimedia.org/wikipedia/commons/2/2b/Flame_-_Carl_Olsen_-_white_-_game-icons.svg> (512 x 512 px; 775 bytes; downloaded 2026-10-07; SHA-256 `7424D535C14CC35E1DBCC6EC04D0BF9716CFC04AEF32A5281E97B6B5D0C42D2D`).

License: [Creative Commons Attribution 3.0 Unported (CC BY 3.0)](https://creativecommons.org/licenses/by/3.0/). Attribution is required. Suggested attribution: “Flame” icon by Carl Olsen, from Game-icons.net via Wikimedia Commons, CC BY 3.0; recolored and rasterized for this dashboard. Changes made; no endorsement is implied.

### Processing and validation

The human-authored SVG silhouette was rasterized at 4x working resolution, recolored with a warm yellow/orange/red gradient, and smoothly downsampled to the existing 102 x 102 px transparent canvas. The original overlay's `FIRE (BURN)` label was recreated with the dashboard's existing HUD glyphs and color; its wording is unchanged. No crop was used. Final output is RGBA PNG with fully transparent and opaque pixels, 3,238 bytes, and is loaded/composited through the existing PNG dashboard path. The final overlay was visually reviewed in the existing `_hero()` rendering path.

## Discord attachment and render verification

The repository has no local maximum-image-dimension or attachment-size guard. `brain_dashboard.py` sets a 1400 ? 1420 px default canvas and 1400 ? 1760 px opt-in canvas. `DashboardImage.save` emits PNG and uses `zlib.compress(rows, 6)`; `fly_bot.dashboard_file` sends that buffer as `brain.png`.

Rendered output measured after the replacement: default dashboard 79,896 bytes (1400 ? 1420 PNG); opt-in research panel 87,221 bytes (1400 ? 1760 PNG). Both are below 0.1 MB. The replacement source image is 37,482 bytes.

Discord's current support page states a 20 MB free upload limit while noting that upload limits are being experimented with for some users. The new regression test uses a conservative 18 MiB upper threshold for generated dashboard output. The observed opt-in output is about 0.44% of that threshold.

References: [Discord File Attachments FAQ](https://support.discord.com/hc/en-us/articles/25444343291031-File-Attachments-FAQ); repository code: `brain_dashboard.py::WIDTH`, `HEIGHT`, `render_dashboard`, `DashboardImage.save`; `fly_bot.py::dashboard_file`.
