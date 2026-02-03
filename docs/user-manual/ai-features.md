# AI-Assisted Features

QualCoder v2 includes AI-powered features to accelerate your qualitative analysis while keeping you in control.

!!! info "Human-in-the-Loop"
    All AI features are designed as suggestions. You always review and approve before changes are made to your data.

## Code Suggestions

The AI analyzes your documents and suggests new codes based on patterns it detects.

### Getting Suggestions

1. Click **AI > Suggest Codes** from the menu
2. The AI analyzes your document content
3. Review the suggestions dialog

![Code Suggestions List](images/code-suggestions-list.png)

### Reviewing Suggestions

Each suggestion card shows:

- **Name** - The proposed code name
- **Description** - What the code captures
- **Confidence** - How confident the AI is

![Code Suggestion Details](images/code-suggestions-details.png)

### Actions

| Action | Result |
|--------|--------|
| **Approve** | Adds the code to your codebook |
| **Reject** | Dismisses the suggestion |
| **Edit** | Modify the name before approving |
| **Approve All** | Accept all suggestions at once |

### Empty State

When no suggestions are available:

![Empty Suggestions](images/code-suggestions-empty.png)

## Duplicate Detection

Over time, you may create similar or redundant codes. The duplicate detector identifies potential matches.

### Finding Duplicates

1. Click **AI > Find Duplicates**
2. The AI compares all codes using semantic similarity
3. Review candidate pairs

![Duplicate Codes List](images/duplicate-codes-list.png)

### Understanding Similarity

Each pair shows:

- **Code names** - The two potentially duplicate codes
- **Similarity %** - How similar they are semantically
- **Segment counts** - How many segments use each code

![Duplicate Similarity Score](images/duplicate-codes-similarity.png)

!!! tip "Similarity Threshold"
    - **90%+** - Very likely duplicates
    - **70-90%** - Possibly related, review carefully
    - **Below 70%** - Probably distinct concepts

### Actions

| Action | Result |
|--------|--------|
| **Merge A → B** | Combines codes, moves all segments from A to B |
| **Merge B → A** | Combines codes, moves all segments from B to A |
| **Dismiss** | Marks as "not duplicates", won't suggest again |

### Empty State

When no duplicates are found:

![No Duplicates](images/duplicate-codes-empty.png)

## Auto-Code

Automatically apply codes to text matching a pattern.

### Pattern-Based Auto-Coding

1. Click **AI > Auto-Code**
2. Enter a search pattern:
   - Plain text: `"interview"`
   - Regex: `"participant\s+\d+"`
3. Select the code to apply
4. Click **Preview** to see matches
5. Click **Apply All** to code all matches

### Auto-Code by Speaker

For transcripts with speaker labels:

1. Click **AI > Auto-Code by Speaker**
2. Select a speaker (e.g., "Interviewer", "P01")
3. Select the code to apply
4. All text by that speaker is coded

## Find Similar

Find passages similar to a coded segment.

### Using Find Similar

1. Select a coded segment
2. Click **AI > Find Similar**
3. Review passages with similar meaning
4. Apply the same code to matches

!!! tip "Semantic Search"
    This uses semantic similarity, not just keyword matching. It finds passages with similar meaning even if they use different words.

## MCP Tools for AI Agents

QualCoder v2 exposes its functionality through MCP (Model Context Protocol) tools, allowing AI agents to:

| Tool | Purpose |
|------|---------|
| `list_codes` | Get all codes in the project |
| `create_code` | Create a new code |
| `apply_code` | Apply a code to a text range |
| `suggest_codes` | Get AI code suggestions |
| `find_duplicates` | Detect duplicate codes |
| `search_text` | Search across all sources |

### Agent Workflow Example

```python
# AI agent workflow
codes = await mcp.list_codes()
suggestions = await mcp.suggest_codes(source_id=1)

for suggestion in suggestions:
    if suggestion.confidence > 0.8:
        await mcp.create_code(
            name=suggestion.name,
            color=suggestion.color
        )
```

## Best Practices

!!! success "Review All Suggestions"
    - Never blindly accept AI suggestions
    - Check if suggested codes fit your conceptual framework
    - Consider if distinctions are meaningful for your research

!!! success "Iterative Refinement"
    - Start with AI suggestions as a first pass
    - Refine and merge codes as understanding develops
    - Use duplicate detection periodically

!!! success "Document Decisions"
    - Add memos explaining why you accepted/rejected suggestions
    - Note merge decisions in code memos
    - Keep an audit trail of AI-assisted changes
