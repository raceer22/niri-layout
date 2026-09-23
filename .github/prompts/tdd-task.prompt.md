---
description: Implement a task file using strict TDD aligned with the PRD
---

Implement the task specified in ${input:taskFile} by strictly following the rules set by [PRD](PRD.md).

**Follow strict TDD (Test-Driven Development):**

1. **Write the failing tests first** based on the acceptance criteria of the task.
2. **Run the test suite** to confirm the tests fail as expected.
3. **Implement only the minimal code** necessary to make all tests pass.
4. **Run tests and linters/type checks** again to verify full pass and code quality.

**Rules:**
- Do not add features, refactor unrelated modules, or write code outside the explicit scope of this task.
- Target task file: ${input:taskFile}