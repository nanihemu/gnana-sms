# My Notes

These are my own notes, in my own words. I write them after reviewing each
day's code — 3 lines, whatever was non-obvious to me. This is my file; Claude
does the building, I do the understanding.

## Day 1 — repo setup, Docker, Django + auth

- Login is by email, not username: we told Django `USERNAME_FIELD = "email"`
  and removed the username field, so Django's built-in login treats email as
  the username.
- One user model carries a `role` field and that role decides which of the 5
  dashboards you land on after login — one URL per role
  (`/teacher/dashboard/` etc.), all sharing a single template.
- Settings are split (base/dev/prod/test) so dev is loose, prod is strict,
  and tests run on in-memory SQLite — no Docker needed to `make test`.
