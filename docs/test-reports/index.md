# Test Reports

QualCoder v2 uses [Allure](https://allurereport.org/) for comprehensive test reporting with traceability to user stories.

## Live Reports

- **[Allure Test Report](https://scope-impact.github.io/qualcoder-v2/allure/)** - Interactive test results with history, trends, and detailed failure analysis.
- **[Coverage Matrix](../DOC_COVERAGE.md)** - Documentation coverage tracking which features have docs and screenshots.

## Report Features

### Story Traceability

All E2E tests are tagged with `@allure.story("QC-XXX.YY Description")` decorators that map directly to backlog tasks:

```python
@allure.story("QC-028.03 Rename and Recolor Codes")
class TestColorPickerDialog:
    @allure.title("AC #3.1: Dialog shows preset color grid")
    def test_dialog_shows_preset_colors(self):
        ...
```

### What's in the Report

| Section | Description |
|---------|-------------|
| **Overview** | Pass/fail summary, duration, environment info |
| **Suites** | Tests organized by module |
| **Graphs** | Trend charts showing test stability over time |
| **Timeline** | Parallel execution visualization |
| **Behaviors** | Tests grouped by `@allure.story` tags |
| **Categories** | Failure classification (product defects vs test issues) |

### History & Trends

The Allure report maintains history across CI runs, showing:

- Test stability trends (flaky test detection)
- Duration changes over time
- Regression identification

## Running Tests Locally

Generate Allure results locally:

```bash
# Run tests with Allure output
QT_QPA_PLATFORM=offscreen uv run pytest -v --alluredir=allure-results

# Serve report locally (requires allure CLI)
allure serve allure-results
```

Install Allure CLI:

**macOS:**
```bash
brew install allure
```

**Linux:**
```bash
sudo apt-get install allure
```

**Windows:**
```powershell
scoop install allure
```

## CI/CD Integration

Allure reports are automatically generated and deployed on every push to `main`:

1. **CI runs tests** with `--alluredir=allure-results`
2. **Allure action** generates HTML report with history
3. **GitHub Pages** deploys to `/allure/` path

See [`.github/workflows/ci.yml`](https://github.com/scope-impact/qualcoder-v2/blob/main/.github/workflows/ci.yml) for the workflow configuration.
