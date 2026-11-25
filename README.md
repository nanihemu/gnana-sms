# Gnana

Gnana is a multi-tenant SaaS platform for school management and learning.
Each school is a client with its own branded homepage at `<school>.gnana.in`.

**Roles:** Super Admin (platform), Admin (per school), Teacher, Student, Parent.

## Features (planned)

- School management: classes, sections, subjects, teachers, students, parents
- Attendance, announcements, achievements
- Fees: append-only ledger, adjustments, Razorpay payments, PDF receipts
- Content upload, quizzes, exams, marks, teacher feedback, daily practice
- Parent dashboard with strengths and weaknesses, and Class 10 career guidance
- Notifications: in-app, email, push, WhatsApp
- AI layer: auto quizzes, auto grading, RAG study chatbot, English speaking
  practice, explainer videos, with per-school cost quotas

## Tech stack

| Layer | Choice |
|---|---|
| Language | Python 3.12 |
| Backend and API | Django 5 + Django Ninja (OpenAPI at `/api/v1/docs`) |
| Web UI | Django templates + HTMX + Alpine.js + Tailwind |
| Database | PostgreSQL 16 with Row-Level Security (pgvector later) |
| Queue | Redis + Celery |
| Storage | Cloudflare R2 (MinIO locally) |
| Mobile (later) | PWA first, then Flutter or React Native on the same API |
| Infra | Docker Compose on one VPS, Cloudflare in front |

## Architecture in brief

- Modular monolith. Each Django app is a module: `tenants`, `accounts`,
  `academic`, `attendance`, `content`, `assessments`, `fees`,
  `notifications`, `analytics`, `ai_gateway`.
- Business logic lives in `services.py`, never in views or API handlers.
- Every tenant table has `school_id`, protected by Postgres RLS.
- Every feature is exposed through `/api/v1`, so web and mobile share it.

## Getting started

### Prerequisites
- Python 3.12, Git, Docker Desktop

### Setup
```bash
git clone https://github.com/<your-username>/gnana.git
cd gnana
cp .env.example .env          # then edit values
make install                  # create venv and install dependencies
docker compose up -d          # start Postgres and Redis
make migrate                  # apply migrations
make seed                     # create the 5 demo users (one per role)
make run                      # start Django at http://localhost:8000
```

### Demo accounts
All demo users share the password `demo1234` (override with `DEMO_PASSWORD`
in `.env`):

| Role | Email |
|---|---|
| Super Admin | superadmin@demo.gnana.in |
| School Admin | admin@demo.gnana.in |
| Teacher | teacher@demo.gnana.in |
| Student | student@demo.gnana.in |
| Parent | parent@demo.gnana.in |

Each user is redirected to their own empty dashboard after login
(`/platform/dashboard/`, `/admin/dashboard/`, `/teacher/dashboard/`,
`/student/dashboard/`, `/parent/dashboard/`).

### Useful commands
```bash
make lint      # ruff + black checks
make test      # pytest
make worker    # start Celery worker
```

### Try a school locally
Subdomains work on localhost:
`http://sunrise.localhost:8000`, `http://abc.localhost:8000`

## Project structure

```
gnana/
├── config/          # Django project and split settings (base, dev, prod)
├── apps/            # Django apps (one per module)
├── templates/       # Django templates
├── static/
├── docs/            # design docs, progress log, notes
├── infra/           # Docker and deployment files
├── tests/
├── CLAUDE.md        # rules for Claude Code
├── docker-compose.yml
└── Makefile
```

## Documentation

- `docs/progress.md` is the daily progress log
- `docs/my-notes.md` holds my own notes in my own words
- `docs/db-design.md` is the database design
- `docs/fees-design.md` is the fee ledger design
- `docs/analytics-design.md` is the mastery score design
- `docs/deploy.md` is the deployment guide
- `docs/roadmap.md` is the roadmap

## Daily workflow (build first, review after)

Claude Code reads `CLAUDE.md` for the project rules. Each day:

1. **Build:** paste the start-of-day prompt and that day's task.
2. **Test:** run the commands Claude gives you and click through the
   checklist yourself.
3. **Push:** commit and push to GitHub.
4. **Learn:** paste the walkthrough prompt and read today's code.
5. **Notes:** write 3 lines in `docs/my-notes.md` in your own words.
6. **Review day (every 7th day):** paste the review-day prompt.
7. **End of each phase:** paste the phase-review prompt.
8. **Risky days (RLS, fees, quizzes, files, AI quotas):** also paste the
   break-it prompt before you push.

### 1. Start-of-day prompt
```
Read CLAUDE.md and docs/progress.md. Today is Day N of the Gnana plan.
Write a short plan (5 lines maximum) and build it. Stop for my approval
only if the work is risky or needs a new dependency, as CLAUDE.md says.
Run the tests and linters, then give me the exact commands to try it
myself, a checklist of what I should see, and a commit message.
Task:
```

### 2. Walkthrough prompt (after testing and pushing)
```
Today's task is done and I tested it. Now walk me through the code you
wrote today, file by file, in the order a request flows through it.
For each file: what it does in one line, the 2 or 3 most important
lines, and why it is written that way. Use simple language. Then list
the 3 concepts I should be able to explain, and append them to
docs/progress.md. Do not ask me quiz questions yet.
```

### 3. Break-it prompt (risky modules)
```
Now act as an attacker. Try to break what we built today: list 5 ways
data could leak between schools, or money could go wrong, or the feature
could be abused, and write a test for each. Run them and show me which
tests fail. Fix the failures.
```

### 4. Review-day prompt (every 7th day)
```
This is a review day. Give me a reading list of the 5 most important
files written this week, in reading order, with one question for each
that I should be able to answer after reading it. Wait while I read.
Then I will answer, and you correct me.
```

### 5. Phase-review prompt (end of each phase)
```
Phase N is finished. Explain how the whole phase works end to end as a
story: a request enters, what happens at each layer, where data is
stored, where security is enforced. Then draw the flow as a simple
diagram in text. Then point out the 3 places in the code I must
understand best because mistakes there are costly.
```

### 6. Stuck prompt
```
I am stuck. Here is the exact error and what I expected: <paste>.
Explain what the error means first, then give me the smallest fix.
```

## Rules

- Every query is tenant-scoped, and RLS is the safety net
- Money is stored as integer paise in an append-only ledger
- AI-generated content is saved as DRAFT until a teacher approves it
- All AI calls go through `ai_gateway` with logging and quotas
- Students are minors: follow DPDP Act 2023 principles, store parental consent
- Secrets only in `.env`, never committed
- Every feature ships with tests, including a tenant-isolation test

## Status

Work in progress. See `docs/progress.md`.

## License

Proprietary. All rights reserved. (c) Gnana.
