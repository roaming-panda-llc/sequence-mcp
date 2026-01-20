# GitHub Copilot Instructions

## Test Requirements

### pytest-describe Testing Pattern

This project uses **pytest-describe** for BDD-style testing. The nested function pattern is intentional and not a code smell.

#### Pattern Explanation

```python
def describe_MyClass():
    def describe_method_name():
        def it_does_something():
            # Test code here
            assert result == expected
```

- Functions prefixed with `describe_` define test contexts/groups
- Functions prefixed with `it_` define individual test cases
- These nested functions are **automatically discovered and executed by pytest-describe**
- They are NOT unused variables or dead code

#### Important Notes

- Do not suggest removing these "unused" nested functions
- Do not add `# noqa` comments or underscore prefixes to these functions
- Do not refactor these into class-based tests unless explicitly requested
- The nesting hierarchy is meaningful and defines test organization

### pytest-describe Pattern

When using pytest-describe for test organization:
- Test functions are nested functions with descriptive names (e.g., `it_calculates_tool_efficiency`)
- These function names serve as test descriptions and are discovered by the pytest-describe framework
- **Do not flag these nested functions as "unused variables"** - they are intentionally not called directly
- The naming pattern follows BDD-style: `it_<describes_behavior>` or `describe_<feature>`
