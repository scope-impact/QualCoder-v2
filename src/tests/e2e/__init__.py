"""
End-to-End Tests

E2E tests use REAL infrastructure - no mocks allowed:
- Real in-memory SQLite database
- Real services and repositories
- Real ViewModels connected to real services
- Real UI components

These tests verify full round-trip behavior:
UI Action → ViewModel → Service → Repository → Database → Events → UI Update

For unit tests with mocks (failure scenarios), see:
- src/presentation/viewmodels/tests/
- src/application/*/tests/
"""
