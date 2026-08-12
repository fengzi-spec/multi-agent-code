# Example task

Use `$multi-agent-code` on this directory.

Improve `calculate_discount` with these acceptance criteria:

- Raise `ValueError` when `price < 0`.
- Raise `ValueError` when `percentage < 0` or `percentage > 100`.
- Treat percentage values `0` and `100` as valid boundaries.
- Add regression tests for every validation rule and both valid boundaries.
- Finish only after the relevant tests pass and review finds no critical/high issue.

Run the initial tests with:

```bash
python -m unittest -v
```
