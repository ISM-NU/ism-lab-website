# ISM Lab website

Website of the ISM group: public pages (members, projects, publications,
datasets, events, announcements) and a control panel for administrators and
managers. Go HTTP server, PostgreSQL, server-side HTML templates with plain JS.

## Run locally

1. Create a PostgreSQL database and apply the schema:
   `psql "$DATABASE_URL" -f database/migrations/init.sql`
2. Start the server from the repository root (templates and static files are
   read with relative paths):
   `DATABASE_URL=postgres://user:password@127.0.0.1:5432/ism_lab go run ./application`
3. Open http://localhost:9992/.

Create the first administrator with the interactive CLI:
`DATABASE_URL=... go run ./CLI`

See `ARCHITECTURE.md` for the route list and `docs/main.pdf` for the full
documentation.
