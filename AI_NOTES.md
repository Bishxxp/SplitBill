# AI Usage Notes

**Project:** SplitBill  
**AI Tool:** ChatGPT (OpenAI)

## 1. AI Tools Used

ChatGPT was used as a development assistant for the following tasks:

| Area | AI Assistance |
|---|---|
| Backend | Explained FastAPI, SQLAlchemy, API design, and business logic. |
| Database | Guided PostgreSQL setup, Docker, and Alembic migrations. |
| Testing | Explained test cases, Pytest, and automated testing. |
| Frontend | Assisted with Next.js, TypeScript, and UI components. |
| Debugging | Helped identify errors and suggest solutions. |

AI-generated code was reviewed and tested before being used in the project.

## 2. Effective Prompts

### Prompt 1: FastAPI & Database

> อธิบายการทำงานของ Fast API และ database โดยมีเครื่องมือไหนช่วยในการทำงานของ 2 ระบบนี้บ้าง

**How it helped:**

Helped me understand how FastAPI communicates with PostgreSQL using SQLAlchemy and Psycopg, how Alembic manages database migrations, and how Docker Compose simplifies database setup.

This knowledge helped me organize the backend into routers, services, and repositories.

### Prompt 2: Test Cases & Automation

> สอนรูปแบบการทำพวก Tests case ให้หน่อย และ การทำให้มันเป็น Automated

**How it helped:**

Helped me understand the Arrange–Act–Assert testing pattern and how to write unit and integration tests using Pytest and FastAPI TestClient.

I applied these concepts to test expense splitting, authorization, balance calculations, and idempotency.

## 3. Incorrect AI Output & Correction

**Issue:** AI-generated PowerShell commands for testing idempotency caused syntax errors.

**Detection:** PowerShell displayed errors such as `Unexpected token` and `The hash literal was incomplete`.

**Correction:** I separated the commands into individual lines, fixed the PowerShell syntax, and reran the test.

**Result:** Both POST requests returned the same Expense ID (`9`), confirming that idempotency worked as expected.

**Lesson:** AI-generated commands should always be checked and tested rather than executed without review.

## 4. Review Process Before Commits

I used the following workflow to review AI-assisted code:

1. **Understand:** Read the suggested code and check its purpose.
2. **Review:** Compare the implementation with the project requirements.
3. **Test:** Verify functionality using Pytest, Swagger UI, or the frontend.
4. **Check Quality:** Use Ruff, TypeScript, and ESLint to detect errors.
5. **Commit:** Inspect Git changes and commit related work incrementally.

When an issue was found, I corrected it and tested again before committing. The checks used depended on the type of change.

## Conclusion

AI helped accelerate learning, implementation, and debugging. However, the final code, testing, and project decisions remained my responsibility.