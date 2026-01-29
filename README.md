# QualCoder v2

A modern reimagining of [QualCoder](https://github.com/ccbogel/QualCoder) - qualitative data analysis with AI-enhanced features.

## Quick Start

```bash
uv sync
uv run storybook
```

## Project Structure

```
├── design_system/     # PyQt6 component library
├── src/
│   ├── domain/        # Business logic (DDD)
│   ├── application/   # Commands & queries (CQRS)
│   ├── infrastructure/# Adapters & persistence
│   └── presentation/  # UI screens & widgets
├── backlog/           # Tasks & milestones
└── docs/              # Architecture docs
```

## License

LGPL-3.0 - See [LICENSE.txt](LICENSE.txt)

## Credits

Inspired by [QualCoder](https://github.com/ccbogel/QualCoder) by Colin Curtain.
