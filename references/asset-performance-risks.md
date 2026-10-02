# Asset and Rendering Risk Review

Read only the sections relevant to asset mappings, exported images, 3D models, canvas/WebGL, video, generated preload manifests, or asset-heavy first screens.

## Asset and Configuration Mappings

- Identify the authoritative table, design node, configuration, or supplied list. Compare identifiers, ordering, variant/color, filenames, and runtime lookup paths against that source. If supplied sources conflict, follow the user's designated source; do not invent a business mapping.
- Inspect import globs and dynamic path construction, including case, suffixes, encoded names, and resolution variants such as `@2x`. A file existing on disk does not prove the runtime loader includes it.
- Check missing references, duplicate mappings, unknown IDs, and unreferenced candidates separately. An unreferenced candidate is not permission to delete a file; it may serve another entry, platform, or dynamic lookup.
- Trace all consumers of a result mapping, such as the displayed result, stored payload, and API input, so they agree on the same identity and order.

## Canvas and Poster Export

- Follow source assets/fonts → DOM or WebGL capture → canvas composition → encoding → download/save. Distinguish the visible preview from the generated artifact at each stage.
- For text placement, inspect font loading, fallback fonts, capture-library text layout, and measured glyph bounds. CSS centering does not establish exported glyph centering; replacing text with a bitmap is a possible scoped correction, not a universal requirement.
- For seams or extra margins, inspect image alpha bounds, source/destination rectangles, scale, and canvas dimensions before changing CSS or background colors. Do not reuse a crop amount from another asset.
- Inspect whether capture starts before images decode, fonts load, or an entrance transition reaches the intended capture state. Preserve the user's interaction and animation behavior when fixing export readiness.
- For encoding failures, seek the actual exception name/message or null-blob result. Trace cross-origin images, fonts, SVG/CSS backgrounds, and WebGL capture separately. A shared Safari/WeChat failure on iPhone supports investigating WebKit, but does not establish a specific `SecurityError` or SVG cause.
- Static checks support source-path and readiness conclusions. Export positioning and device compatibility require the exported result: use representative short, long, and mixed-script text where relevant, and the affected device when authorized. Otherwise record the remaining gap.

## Inspect Before Concluding

- Identify the rendering library and installed version, browser targets, main render component, initialization lifecycle, and largest relevant assets.
- Compare exact URLs emitted by HTML/preload code, JavaScript imports, CSS, and runtime requests. Encoded and unencoded forms can prevent browser reuse.
- Check whether initialization waits for a container with a real size and whether existing resize/destroy lifecycle handling already exists.
- Trace loading overlays, opacity gates, progress indicators, and debug switches to the same source of readiness as the renderer.
- Distinguish asset bytes, decode/parse cost, shader/renderer startup, network latency, and duplicate loading. Do not infer hardware requirements from source size alone.

## Evidence Boundary

Static inspection can confirm dependency choices, asset sizes, URL identity, lifecycle omissions, and browser-target declarations. It cannot confirm frame rate, memory pressure, first-content timing, device compatibility, or CDN behavior without runtime measurement. Label those conclusions `Likely` or unverified as appropriate.
