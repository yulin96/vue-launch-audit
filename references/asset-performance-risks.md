# Asset and Rendering Risk Review

Read this reference only when the release uses 3D models, canvas/WebGL, video, large images, generated preload manifests, or asset-heavy first screens.

## Inspect Before Concluding

- Identify the rendering library and installed version, browser targets, main render component, initialization lifecycle, and largest relevant assets.
- Compare exact URLs emitted by HTML/preload code, JavaScript imports, CSS, and runtime requests. Encoded and unencoded forms can prevent browser reuse.
- Check whether initialization waits for a container with a real size and whether existing resize/destroy lifecycle handling already exists.
- Trace loading overlays, opacity gates, progress indicators, and debug switches to the same source of readiness as the renderer.
- Distinguish asset bytes, decode/parse cost, shader/renderer startup, network latency, and duplicate loading. Do not infer hardware requirements from source size alone.

## Evidence Boundary

Static inspection can confirm dependency choices, asset sizes, URL identity, lifecycle omissions, and browser-target declarations. It cannot confirm frame rate, memory pressure, first-content timing, device compatibility, or CDN behavior without runtime measurement. Label those conclusions `Likely` or unverified as appropriate.
