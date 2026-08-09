# Stackshot

Stackshot renders source documents into a single PNG. Its layout language describes how independently rendered documents are composed.

## Language

**Source document**:
An input file named in a layout configuration and rendered independently before composition.
_Avoid_: Source file, input asset

**Document tile**:
The complete rendered result of one source document when placed in a grid; its pages or frames are not separate grid cells.
_Avoid_: Frame tile, page tile

**Layout configuration**:
An opt-in description of a composition of multiple source documents; the normal single-input invocation is not a layout configuration.
_Avoid_: Layout flag, CLI mode

**Two-column grid**:
A layout configuration that places document tiles in exactly two columns and derives its rows from the number of source documents.
_Avoid_: Arbitrary grid, N-column grid

**Row-major order**:
The source-document list fills a two-column grid from left to right, then from top to bottom.
_Avoid_: Column-major order

**Trailing empty cell**:
The unused right-hand position in the final row of a two-column grid with an odd number of source documents.
_Avoid_: Centered final tile, incomplete layout

**Document composition**:
The complete rendering of a source document's frames into its document tile before that tile is arranged in a two-column grid.
_Avoid_: Frame grid, flattened frame sequence

**Canvas width**:
The width of the completed composite PNG; document tiles preserve their rendered layout and scale to fit within it.
_Avoid_: Cell width, reflow width

**Unified gap**:
The single spacing value used between frames within a document tile and between document tiles in a two-column grid.
_Avoid_: Inner gap, outer gap

**Mixed-source layout**:
A layout configuration whose source documents may use any format Stackshot supports.
_Avoid_: Homogeneous layout, format-specific grid

**Layout manifest**:
A TOML layout configuration that names the source documents and global rendering rules for one composite output.
_Avoid_: Override file, source manifest

**Row height**:
The height of a two-column grid row, determined by its tallest document tile.
_Avoid_: Fixed cell height, shortest-tile height

**Top alignment**:
The placement of a document tile at the upper edge of its grid cell; unused lower area uses the canvas background.
_Avoid_: Center alignment, bottom alignment

**Global stylesheet**:
An optional stylesheet in a layout manifest that applies to every Markdown and HTML source document, but not to PDF or PowerPoint sources.
_Avoid_: Per-source stylesheet, universal stylesheet
