# Managing Sources

Sources are the documents and media files you analyze. QualCoder supports text, PDF, images, audio, and video.

## Supported File Types

| Type | Extensions | Features |
|------|------------|----------|
| Text | `.txt`, `.docx`, `.rtf` | Full-text search, coding |
| PDF | `.pdf` | Text extraction, region coding |
| Images | `.png`, `.jpg`, `.gif` | Region selection, coding |
| Audio | `.mp3`, `.wav`, `.m4a` | Timeline coding, transcription |
| Video | `.mp4`, `.mov`, `.avi` | Timeline coding, frame extraction |

## Importing Sources

### Import Individual Files

1. Navigate to the **File Manager** screen
2. Click **Import Files**
3. Select one or more files
4. Click **Open**

![File Manager - With Sources](images/file-manager-with-folders.png)

*The File Manager showing imported source files with type statistics and folder tree.*

> **Tip: Bulk Import**
>
> You can select multiple files at once. Hold `Cmd` (macOS) or `Ctrl` (Windows) while clicking to select multiple files.

### Import a Folder

To import all files from a folder:

1. Click **Import Folder**
2. Select the folder containing your files
3. Choose file type filters (optional)
4. Click **Import**

## Organizing Sources

### Create Folders

Organize sources into folders for better management:

1. Click **New Folder** in the File Manager toolbar
2. Enter a folder name (1–255 characters, must be unique within the parent folder, no slashes)
3. Optionally select a **parent folder** to create a nested folder
4. Click **Create**

> **Tip: Nested Folders**
>
> You can create folders inside other folders for hierarchical organization — for example, `Interviews / Round 1` and `Interviews / Round 2`.

### Rename Folders

1. Right-click the folder in the folder tree
2. Select **Rename**
3. Enter the new name (must be unique within the same parent)
4. Press **Enter** or click **OK**

### Delete Folders

1. Right-click the folder
2. Select **Delete**
3. Confirm the deletion

> **Warning:** A folder must be empty before it can be deleted. Move or remove all sources from the folder first.

### Move Sources

Move sources into folders using one of these methods:

- **Drag and drop** — Drag a source onto a folder in the tree
- **Right-click** — Right-click a source, select **Move to Folder**, and choose the target folder
- **Move to root** — Select **No Folder** (or root) to remove a source from its current folder

### Source Metadata

Each source has metadata you can view and edit:

1. Right-click a source
2. Select **View Metadata**
3. Edit fields like:
   - Author
   - Date
   - Description
   - Custom attributes

## Viewing Sources

### Text Documents

Click a text source to open it in the document viewer. The text is displayed with:

- Line numbers
- Coding highlights
- Search functionality

### PDF Documents

PDFs are displayed page-by-page with:

- Page navigation
- Zoom controls
- Text selection for coding

### Images

Images open in the image viewer with:

- Pan and zoom
- Region selection tools
- Overlay of coded regions

![Image Viewer](images/image-viewer.png)

*The Image Viewer displaying an imported image with zoom controls.*

### Audio/Video

Media files open in the media player with:

- Playback controls
- Timeline visualization
- Segment marking tools

![Media Player](images/media-player.png)

*The Media Player with playback controls for audio/video files.*

### Empty State

When no sources have been imported yet:

![File Manager - Empty](images/file-manager-empty.png)

*The File Manager empty state with import options.*

## AI Agent Source Management

When an AI assistant is connected via MCP (see [MCP Setup](./mcp-setup.md)), it can manage sources programmatically:

### Adding Text Sources

The agent can add text sources directly using the `add_text_source` tool, providing a name and content without needing a file on disk. This is useful for:

- Ingesting interview transcripts from other tools
- Adding field notes collected during research
- Creating sources from processed or transformed text

Each source must have a unique name within the project.

### Importing Files

The agent can import file-based sources (PDFs, images, audio, video) using the `import_file_source` tool by providing an absolute file path. The file type is auto-detected from the extension:

- **Text:** `.txt`, `.docx`, `.rtf`, `.md`, `.odt`, `.epub`
- **PDF:** `.pdf` (with automatic text extraction)
- **Images:** `.png`, `.jpg`, `.gif`, `.bmp`, `.tiff`, `.webp`
- **Audio:** `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`
- **Video:** `.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`

Use the `dry_run` parameter to validate a file before importing. The optional `name` parameter overrides the default filename-based source name.

### Listing and Reading Sources

The agent can browse and read your sources programmatically:

- **`list_sources`** — Lists all sources in the project. Use the optional `source_type` filter (`text`, `pdf`, `image`, `audio`, `video`) to narrow results.
- **`read_source_content`** — Reads the text content of a source document. For large documents, content is paginated using `start_pos`, `end_pos`, and `max_length` parameters. The response includes `has_more: true` when additional content is available.
- **`navigate_to_segment`** — Opens a source in the coding screen and scrolls to a specific character position. Optionally highlights the segment for easy identification.

### Suggesting Metadata

The agent can analyze sources and suggest metadata using `suggest_source_metadata`:

- **Language detection** — Suggests a language code (e.g., `en`, `es`, `fr`)
- **Topic extraction** — Suggests key topics and themes found in the text
- **Organization hints** — Suggests how the source might be grouped or categorized

All metadata suggestions are stored with pending status and require your approval before being applied.

### Organizing into Folders

The agent can manage the full folder lifecycle:

- **`list_folders`** — Lists all folders with their hierarchy (parent-child relationships)
- **`create_folder`** — Creates a new folder, optionally nested under a parent folder via `parent_id`
- **`rename_folder`** — Renames an existing folder (new name must be unique within the parent)
- **`delete_folder`** — Deletes an empty folder (fails if the folder still contains sources)
- **`move_source_to_folder`** — Moves a source into a folder, or back to root by passing `folder_id=0` or `null`

This enables automated organization of large source collections — for example, sorting interview transcripts by participant or date.

### Removing Sources

The agent uses a **preview-then-confirm** workflow for safe deletion:

1. `remove_source` with `confirm=false` (default) shows what would be deleted
2. You review the preview (source name, type, number of coded segments affected)
3. `remove_source` with `confirm=true` performs the actual deletion

This ensures you always know what will be removed before it happens.

## Deleting Sources

> **Warning: Caution**
>
> Deleting a source also removes all coded segments associated with it.

1. Right-click the source
2. Select **Delete**
3. Confirm the deletion

## Next Steps

With your sources imported, you're ready to:

1. [Create a coding scheme](codes.md)
2. [Start coding your data](coding.md)
