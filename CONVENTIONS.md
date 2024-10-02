# Conventions

## Coding Style
- Adhere to Clean Architecture, SOLID, DRY, KISS, YAGNI, etc.
- Don't document, just minimal comments
- Prefer dictionaries and lambda functions over if-elif chains.
- Prefer to create only one class over multiple classes if length is less than 600 lines
- Prefer split methods over one long method.
- Create helper methods for common tasks.

## Environment
Preferably, use:
- python 3.12 goodies
- pytest for testing
We use Windows 10 (for command line)

## Testing Conventions

- Always use pytest for testing.
- Use class-based tests instead of function-based tests.
- Test classes should follow this structure:
  ```python
  class TestClassName:
      @pytest.fixture(autouse=True)
      def setup(self):
          # Setup code here
          pass

      def test_something(self):
          # Test code here
          pass
  ```
- Use descriptive class names that start with "Test", e.g., `class TestUserAuthentication:`.
- Organize related tests into methods within the class.
- Use the `setup` method with `@pytest.fixture(autouse=True)` to prepare the test environment before each test method.
- If teardown is needed, use `yield` in the setup method and place teardown code after it.
- Test method names should be descriptive and start with "test_".
- Group related tests into separate test classes when appropriate.
- Use pytest fixtures for reusable test data or objects.
- Prefer `assert` statements over unittest-style assertions.
  
