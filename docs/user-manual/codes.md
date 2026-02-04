# Managing Codes

Codes are labels you apply to segments of your data. They help categorize and analyze patterns in your research.

## Understanding Codes

A **code** represents a concept, theme, or category in your data. Each code has:

- **Name** - A descriptive label (e.g., "Positive Experience")
- **Color** - Visual identifier for highlighting
- **Memo** - Optional notes about the code's meaning

## Creating Codes

### Create a New Code

There are two ways to create a new code:

**Method 1: Keyboard Shortcut (Recommended)**

1. In the **Coding** screen, press ++n++
2. The Create Code dialog opens
3. Enter a code name
4. Select a color from the palette
5. Optionally add a description
6. Click **Create Code**

![Create Code Dialog](images/create-code-dialog.png)

*The Create Code dialog - press N while coding to open it.*

**Method 2: Plus Button**

1. In the **Coding** screen, click the **+** button
2. Enter a code name
3. Select a color from the color picker

#### Color Picker

The color picker offers preset colors for quick selection:

![Color Picker - Preset Colors](images/color-picker-presets.png)

Click any color swatch to select it. The preview updates immediately.

![Color Picker - Color Selected](images/color-picker-selected.png)

#### Custom Colors

For precise control, enter a custom hex color:

![Color Picker - Custom Hex](images/color-picker-custom-hex.png)

!!! tip "Hex Colors"
    Hex colors start with `#` followed by 6 characters (e.g., `#FF5733`).
    Use a color picker tool online to find the exact color you want.

## Organizing Codes

### Create Categories

Categories group related codes into a hierarchy:

1. Click **Create Category**
2. Enter a category name

![Create Category Dialog](images/create-category-initial.png)

3. Enter the category name

![Create Category - Name Entered](images/create-category-name.png)

4. Optionally select a parent category for nesting

![Create Category - Parent Selection](images/create-category-parent.png)

5. Add an optional memo to describe the category
6. Click **Create**

![Create Category - Filled Form](images/create-category-filled.png)

### Hierarchy Example

```
Emotions (category)
├── Positive (code)
│   ├── Joy (code)
│   └── Gratitude (code)
└── Negative (code)
    ├── Frustration (code)
    └── Disappointment (code)
```

## Editing Codes

### Rename or Recolor

1. Right-click a code in the code list
2. Select **Edit**
3. Modify the name, color, or memo
4. Click **Save**

### Add a Memo

Memos help document what a code means and when to use it:

1. Right-click a code
2. Select **Edit Memo**
3. Enter your description
4. Click **Save**

!!! tip "Good Memo Practice"
    Include:

    - Definition of the code
    - Examples of when to apply it
    - Boundaries (what it doesn't include)

## Deleting Codes

### Simple Deletion

For codes with no coded segments:

![Delete Code - Simple](images/delete-code-simple.png)

Click **Delete** to confirm.

### Deletion with Segments

!!! warning "Segment Warning"
    If a code has been applied to data, you'll see a warning.

![Delete Code - With Segments](images/delete-code-warning.png)

You can choose to:

- **Delete code only** - Removes the code but keeps segments (they become orphaned)
- **Delete code and segments** - Removes both

![Delete Code - Segments Checked](images/delete-code-segments-checked.png)

## AI-Assisted Code Management

### Suggest New Codes

The AI can analyze your data and suggest new codes:

1. Click **AI > Suggest Codes**
2. Review the suggestions

![Code Suggestions List](images/code-suggestions-list.png)

Each suggestion includes:

- Suggested name
- Description
- Confidence level

![Code Suggestion Details](images/code-suggestions-details.png)

3. Click **Approve** to add the code
4. Click **Reject** to dismiss

![Empty Suggestions](images/code-suggestions-empty.png)

*When no suggestions are available, you'll see the empty state.*

### Detect Duplicate Codes

Over time, similar codes may accumulate. The duplicate detector helps clean up:

1. Click **AI > Find Duplicates**
2. Review candidate pairs

![Duplicate Codes List](images/duplicate-codes-list.png)

Each pair shows:

- Both code names
- Similarity percentage
- Segment counts

![Duplicate Similarity Score](images/duplicate-codes-similarity.png)

3. Click **Merge A → B** to combine codes
4. Click **Dismiss** if they're not duplicates

![No Duplicates](images/duplicate-codes-empty.png)

*The empty state when no duplicates are found.*

## Best Practices

!!! success "Code Naming"
    - Use clear, descriptive names
    - Be consistent with verb tense ("Expressing" vs "Expressed")
    - Avoid overly long names

!!! success "Color Usage"
    - Use similar colors for related codes
    - Reserve bright colors for important codes
    - Consider colorblind-friendly palettes

!!! success "Categories"
    - Don't over-categorize early
    - Let categories emerge from your data
    - Reorganize as your understanding grows

## Next Steps

With your coding scheme ready:

1. [Start coding your text](coding.md)
2. [Use auto-code for patterns](ai-features.md)
