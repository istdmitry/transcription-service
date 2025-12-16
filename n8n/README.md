# n8n on Railway

This directory contains the configuration to run [n8n](https://n8n.io/) as a generic service on Railway.

## Deployment Instructions

1.  **Push these changes** to your GitHub repository.
2.  Go to your **Railway Project**.
3.  Click **+ New** -> **GitHub Repo**.
4.  Select your `Services` repository.
5.  **Important**: Before the first build completes (or in the Settings tab afterwards):
    *   Go to **Settings** > **General** > **Root Directory**.
    *   Change it to `/n8n`.
    *   This ensures Railway builds using the Dockerfile in this folder, not the root one.

## Environment Variables

Configure these variables in Railway for persistent storage and access:

| Variable | Value | Description |
| :--- | :--- | :--- |
| `N8N_ENCRYPTION_KEY` | *(Random String)* | **CRITICAL**. Generate a random string. If you lose this, you lose access to credentials. |
| `N8N_HOST` | *(Your Railway URL)* | e.g. `n8n-production.up.railway.app` |
| `N8N_PORT` | `5678` | internal port |
| `N8N_PROTOCOL` | `https` | |
| `WEBHOOK_URL` | `https://Your-Railway-URL/` | Required for webhooks to work correctly. |

## Persistence (Database)

By default, n8n uses SQLite. For production on Railway, **use PostgreSQL**:

1.  Add a **PostgreSQL** service to your Railway project.
2.  In the n8n service **Variables**, add:
    *   `DB_TYPE`: `postgresdb`
    *   `DB_POSTGRESDB_HOST`: `${{Postgres.HOST}}`
    *   `DB_POSTGRESDB_PORT`: `${{Postgres.PORT}}`
    *   `DB_POSTGRESDB_DATABASE`: `${{Postgres.MYSQL_DATABASE}}` (or just `railway`)
    *   `DB_POSTGRESDB_USER`: `${{Postgres.POSTGRES_USER}}`
    *   `DB_POSTGRESDB_PASSWORD`: `${{Postgres.POSTGRES_PASSWORD}}`

*(Note: Railway's variable referencing syntax might vary, checking the PostgreSQL service connection details is the safest bet.)*
