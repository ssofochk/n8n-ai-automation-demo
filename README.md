# n8n-ai-automation-demo

Minimal Python calculator for demonstrating AI code review and GitHub Issues automation with n8n. No external dependencies.

## Run

Requires Python 3. From the repository root:

```bash
python -m unittest discover -s tests -v
python -c "from src.calculator import add; print(add(2, 3))"
```

Division by zero and averaging an empty list raise `ValueError`.
