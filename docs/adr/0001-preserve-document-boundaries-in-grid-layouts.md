# Preserve document boundaries in grid layouts

Stackshot will first compose every source document's frames into one document tile, then arrange those tiles row-major in a two-column grid. This preserves the user-visible rule that a source document, rather than an individual PDF page or slide, occupies a grid cell; it adds a composition stage but avoids splitting multi-frame documents across cells.
