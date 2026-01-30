# Signal Patterns

Qt signal-based interactivity patterns.

## Basic Signal Connection

```python
# Connect signals to handlers
button.clicked.connect(self.on_button_click)
table.row_clicked.connect(lambda idx, data: self.select_row(idx))
search.text_changed.connect(self.filter_results)
```

## Lambda Functions

Use lambdas for inline handlers or to pass additional data:

```python
# Pass additional context
for i, item in enumerate(items):
    button = Button(item.name)
    button.clicked.connect(lambda checked, idx=i: self.select_item(idx))
    layout.addWidget(button)
```

## Signal Forwarding

Forward signals to parent components:

```python
from PySide6.QtCore import Signal

class FilePanel(Panel):
    file_selected = Signal(str)  # Forward selection

    def __init__(self):
        super().__init__()
        self.file_list = FileList()
        self.file_list.item_clicked.connect(self.file_selected.emit)
        self.add_widget(self.file_list)
```

## Custom Signals

Define custom signals for component communication:

```python
from PySide6.QtCore import QObject, Signal

class DataManager(QObject):
    data_loaded = Signal(list)
    data_error = Signal(str)
    loading_started = Signal()
    loading_finished = Signal()

    def load_data(self):
        self.loading_started.emit()
        try:
            data = fetch_data()
            self.data_loaded.emit(data)
        except Exception as e:
            self.data_error.emit(str(e))
        finally:
            self.loading_finished.emit()
```

## Signal Disconnection

Disconnect signals when needed:

```python
class DynamicView(Panel):
    def __init__(self):
        super().__init__()
        self.current_handler = None

    def set_handler(self, handler):
        # Disconnect previous handler
        if self.current_handler:
            self.button.clicked.disconnect(self.current_handler)

        # Connect new handler
        self.current_handler = handler
        self.button.clicked.connect(handler)
```

## Debouncing

Debounce rapid signals (e.g., search input):

```python
from PySide6.QtCore import QTimer

class SearchPanel(Panel):
    def __init__(self):
        super().__init__()
        self.search = SearchBox()
        self.search.text_changed.connect(self.on_text_changed)

        self.debounce_timer = QTimer()
        self.debounce_timer.setSingleShot(True)
        self.debounce_timer.timeout.connect(self.execute_search)

        self.pending_query = ""

    def on_text_changed(self, text):
        self.pending_query = text
        self.debounce_timer.start(300)  # 300ms debounce

    def execute_search(self):
        self.perform_search(self.pending_query)
```

## Event Bus Pattern

Central event bus for application-wide communication:

```python
from PySide6.QtCore import QObject, Signal

class EventBus(QObject):
    _instance = None

    # Application events
    theme_changed = Signal(str)
    project_loaded = Signal(str)
    file_opened = Signal(str)
    code_applied = Signal(str, str, int, int)

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = EventBus()
        return cls._instance

# Usage
EventBus.instance().theme_changed.connect(self.on_theme_changed)
EventBus.instance().theme_changed.emit("dark")
```

## Signal Best Practices

### Do

- Use descriptive signal names (`item_selected`, not `clicked`)
- Include relevant data in signal parameters
- Disconnect signals when components are destroyed
- Use `blockSignals()` when updating programmatically

### Don't

- Connect signals in loops without proper cleanup
- Emit signals during initialization (use `QTimer.singleShot`)
- Create circular signal connections
- Ignore signal parameters that provide context
