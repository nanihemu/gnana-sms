# Gnana Progress Log

## Current status
- Phase: 0 (Foundations)
- Last completed day: 1

## Day 1 — Repo setup, Docker, Django 5 + custom User, role dashboards

Built (and tests pass):

- Repo hygiene: `.gitignore`, `.env.example` (+ local `.env`, gitignored),
  initial `docs/my-notes.md`, README demo-user section.
- Docker Compose: Postgres 16 + Redis 7 with healthchecks, data volume.
- Django 5.1 project with split settings (`config/settings/`: base, dev, prod,
  test) and template/static layout per the README.
- Custom `User` model (`apps/accounts`): email login
  (`USERNAME_FIELD = "email"`, no username) plus a `role` field with the five
  fixed roles (Super Admin, School Admin, Teacher, Student, Parent).
- Login page styled with Tailwind (CDN for now), listing the demo accounts.
- Role-based redirect after login: one empty dashboard per role at
  `/platform/dashboard/`, `/admin/dashboard/`, `/teacher/dashboard/`,
  `/student/dashboard/`, `/parent/dashboard/`. Wrong role → 403.
- `seed_demo_users` management command: 5 users, one per role, password
  `demo1234` (overridable via `DEMO_PASSWORD` in `.env`), idempotent.
- Makefile with `install`, `up`, `down`, `migrate`, `seed`, `run`, `test`,
  `lint`, `fmt`.
- Tests: login redirect per role, dashboard titles per role, 403 on wrong
  role, login required, seed idempotency. `make test` = 11 tests, all green.

Commands to try on your machine:

```bash
cp .env.example .env            # then edit SECRET_KEY if you like
make install
docker compose up -d            # start Postgres + Redis
make migrate
make seed                       # create the 5 demo users
make run                        # http://localhost:8000
```

Checklist (should see):

1. `http://localhost:8000/accounts/login/` — branded login card.
2. Log in as each of the 5 demo accounts (password `demo1234`):
   `superadmin@demo.gnana.in`, `admin@demo.gnana.in`, `teacher@demo.gnana.in`,
   `student@demo.gnana.in`, `parent@demo.gnana.in`.
3. After each login you land on that role's dashboard, titled "X Dashboard",
   and different roles give different titles. Logging in as student, then
   manually opening `/teacher/dashboard/`, gives "403 Forbidden".

Suggested commit message:

```
Set up repo skeleton, Docker, Django + custom User, role dashboards

Phase 0 (Foundations), Day 1.

- .gitignore, .env.example, docs/my-notes.md
- docker-compose.yml (Postgres 16 + Redis 7)
- Django 5.1 split settings (base/dev/prod/test)
- Custom User model: email login + role (5 roles)
- Tailwind login page and 5 empty role dashboards
- seed_demo_users command + pytest suite + Makefile

Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>
```

