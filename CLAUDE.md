# CLAUDE.md: Gnana

## Product
Gnana is a multi-tenant SaaS for school management and learning. Each school is
a client (tenant) with its own branded homepage at <school-slug>.gnana.in.
Roles: Super Admin (platform), Admin (per school), Teacher, Student, Parent.

## Tech stack (do not deviate without asking)
- Language: Python 3.12 for everything server-side
- Backend: Django 5.x + Django Ninja (OpenAPI), Pydantic schemas
- Web UI: Django templates + HTMX + Alpine.js + Tailwind (no separate SPA)
- Admin: Django Admin used as the Super Admin console (platform staff only)
- DB: PostgreSQL 16 with Row-Level Security; pgvector later
- Cache/queue: Redis + Celery (+ Celery beat for scheduled jobs)
- Storage: Cloudflare R2 (S3-compatible, signed URLs only) via django-storages;
  MinIO in Docker for local development
- Mobile later: PWA first, then Flutter/React Native using the same /api/v1
- Infra: Docker Compose on a single VPS, Cloudflare in front
- Tests: pytest-django, factory_boy; Playwright for critical flows
- Lint/format: ruff + black; mypy on services

## Architecture rules
1. Modular monolith as Django apps: tenants, accounts, academic, attendance,
   content, assessments, fees, notifications, analytics, ai_gateway. Business
   logic lives in services.py per app, never in views or API handlers. Web
   pages and mobile both call the same services and /api/v1 endpoints. No
   cross-app DB access except through service functions.
2. Every API is versioned under /api/v1, documented by OpenAPI, and works
   identically for web and mobile. Group APIs by feature (/students, /fees,
   /quizzes) and protect each with permissions. Role dashboards
   (/admin/dashboard, /parent/dashboard) are thin endpoints over services.
3. Multi-tenancy: shared database, school_id on every tenant table.
   TenantMiddleware resolves the school from the subdomain and runs
   SET LOCAL app.current_school per request, inside the transaction.
   Enforce with Postgres RLS policies. The app connects as a non-superuser DB
   role (superusers bypass RLS). Never rely on application-level filtering
   alone. A missing school context must return zero rows, never all rows.
4. Authorization is permission-based (roles -> permissions tables), not
   hard-coded role checks. Parents may only access linked children; teachers
   only their assigned sections and subjects; students only themselves.
5. Fees use an append-only ledger (fee items, adjustments, payments,
   allocations). Never overwrite balances. All money is stored as integer
   paise. Payments are idempotent (idempotency keys, signature-verified
   webhooks). Never trust the browser to confirm a payment.
6. Use UUID primary keys, soft deletes (deleted_at), created_at/updated_at,
   and an audit_logs entry for every admin-level mutation. Never log
   passwords, tokens or secrets.
7. All AI calls go through ai_gateway (provider-agnostic interface), log
   tokens and estimated cost per school, and enforce monthly per-school
   quotas. AI-generated content (quizzes, summaries, videos) is saved as
   DRAFT until a teacher approves it. Chatbot answers must be grounded in
   school content (RAG), cite sources, refuse off-topic or unsafe requests,
   and stay child-safe. Use a fake provider in tests so tests cost nothing.
8. Students are minors: follow India's DPDP Act 2023 principles. Collect
   minimal data, store parental consent records, no ad tracking, support
   data export and deletion.
9. Background work (notifications, AI jobs, video rendering, analytics
   rollups) runs in Celery with retries, backoff and idempotency keys. Never
   do slow work inside a web request.
10. Files never pass through the Django server: use short-lived signed
    upload and download URLs, validate type and size, and key files as
    school_id/<area>/<uuid>.
11. Analytics are rule-based first (weighted mastery score: exams 40%,
    quizzes 25%, practice 15%, teacher feedback 20%). AI only explains the
    numbers; it must never invent facts or figures.

## Conventions
- Type hints everywhere. Run ruff, black and mypy before finishing a task.
- Every endpoint has request/response schemas, pagination and clear error
  codes. Use 401 for unauthenticated and 403 for unauthorized.
- Every feature ships with tests, including a tenant-isolation test (School A
  can never read School B) and a permission test per role.
- Avoid N+1 queries (use select_related/prefetch_related) and add indexes
  such as (school_id, student_id) and (student_id, created_at).
- Secrets only via environment variables. Never commit .env. Keep
  .env.example up to date.
- Small commits with clear messages. One day of work equals one commit.
- Update docs/ and README.md when the design or commands change.

## Folder layout
- config/ (settings: base, dev, prod), apps/<module>/, templates/, static/,
  docs/, infra/, tests/
- Each app: models.py, services.py, api.py (Ninja router), schemas.py,
  tests/. Register each router in the /api/v1 root.

## Budget and cost rules
Total budget is about 60,000 INR, so:
- Prefer free tiers and open-source options. Ask before adding any paid
  service or any dependency not listed above.
- Start with free browser speech APIs, Brevo or SES for email, FCM for push.
- Prefer low-cost LLMs (Gemini Flash or Claude Haiku class).
- Flag any design that could cause surprise costs (AI loops, WhatsApp
  volume, large video storage).

## How to work with me (build first, review after)
I am building this alone and learning mainly by reviewing finished code.
The workflow for each day's task:
1. Write a short plan (5 lines maximum) and start building. Stop and wait for
   my approval only for design-heavy or risky work: RLS, fee ledger, payments,
   mastery score, career guidance, AI quotas, deployment, and anything that
   needs a new dependency or a paid service.
2. Build in small steps. Do not build anything beyond the current task.
3. Run tests and linters. Fix failures before telling me it is done.
4. Give me the exact commands to run and click through so I can test it
   myself, plus a short checklist of what I should see.
5. Suggest a commit message. 
6. Do not quiz me or explain concepts at length unless I ask. I review the
   code after testing, and I will ask for the walkthrough then.

## Learning mode: when I ask for a walkthrough
When I say "walk me through" or "review day":
- Explain the code in the order a request flows through it (URL, API or view,
  service, model, database).
- For each file: one line on what it does, the 2 or 3 most important lines,
  and why it is written that way. Use simple language and small examples.
- End with the 3 concepts I should be able to explain, and append them to
  docs/progress.md.
- On a weekly review day: give me a reading list of the 5 most important
  files of the week in reading order, with one question per file. Wait for my
  answers, then correct me.
- At the end of a phase: explain how the whole phase works as a story from
  request to database, draw a simple text diagram, and point out the 3 places
  where mistakes would be most costly.

## Break-it check (required for risky modules)
After building any of these, act as an attacker before calling the work done:
tenant isolation and RLS, auth and permissions, fees and payments, quiz
attempts and grading, file access, AI quotas and chat safety, notifications
(wrong recipient). List 5 ways it could leak data, lose money or be abused,
write a test for each, run them, and report which failed. Do not skip this
even if everything looks fine in manual testing.

## Never do
- Never write a tenant query that skips RLS or school context.
- Never store plain-text passwords, tokens or API keys in code or logs.
- Never edit a ledger row to change a balance; add an adjustment instead.
- Never publish AI-generated content to students without teacher approval.
- Never expose correct quiz answers to the client before submission.
- Never run destructive commands (drop, reset, force push) without asking.
- Never say a task is done if tests are failing or were not run.
