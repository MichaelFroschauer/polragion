# Setting up PolRAGion

[Back to the README](../README.md)

This guide uses the complete Docker Compose deployment. Commands assume you start in the repository's `docker/` directory. The examples use `localhost`; use your server hostname consistently if deploying elsewhere.

## 1. Prepare the configuration files

You need Docker with Compose and Linux containers, access to your Polarion server, and GitHub Copilot access for users of the AI assistant.

Create `backend-data`, `cache`, and `certs` inside `docker/`. Then copy these templates:

| Copy from | Copy to |
| --- | --- |
| `.env.backend.example` | `.env.backend` |
| `.env.frontend.example` | `.env.frontend` |
| `github-user-config.example.json` | `backend-data/github-user-config.json` |
| `polarion-import-config.example.json` | `backend-data/polarion-import-config.json` |

Run these commands in Bash:

```bash
mkdir -p backend-data cache certs
cp .env.backend.example .env.backend
cp .env.frontend.example .env.frontend
cp github-user-config.example.json backend-data/github-user-config.json
cp polarion-import-config.example.json backend-data/polarion-import-config.json
```

Keep existing configuration when updating an installation.

## 2. Create a GitHub App

1. In GitHub, open **Settings → Developer settings → GitHub Apps → New GitHub App**.
2. Enter a name and set the **Homepage URL** to your application URL, for example `https://localhost/`.
3. Set the **Callback URL** to `https://localhost:443/api/auth/github/callback`. For a server, replace `localhost` with its hostname.
4. Keep **Expire user authorization tokens** enabled. PolRAGion requires expiring access tokens and refresh tokens.
5. Disable **Active** under Webhook; this project does not use webhooks.
6. Create the app, copy its **Client ID**, and generate a **client secret**.

Save those values in `.env.backend` as described below. The current login flow does not need the App ID or an App private key. Users authorize the app when signing in and use their own Copilot access; your organization may need to approve the app.

For registration details, see [GitHub's App guide](https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/registering-a-github-app) and [Copilot OAuth setup](https://docs.github.com/en/copilot/how-tos/copilot-sdk/setup/github-oauth).

## 3. Set the environment variables

Edit `.env.backend`:

```dotenv
HOST_IP=localhost
FRONTEND_PORT=443

SESSION_SECRET=your_generated_random_secret
ENCRYPTION_SECRET=your_generated_fernet_key
GITHUB_CLIENT_ID=your_github_app_client_id
GITHUB_CLIENT_SECRET=your_github_app_client_secret

POLARION_HOST=https://polarion.example.com
POLARION_USER=your_polarion_username
POLARION_PASSWORD=your_polarion_password
```

- `HOST_IP` is your application's hostname or IP, without `https://` or a path. It determines the login callback, so it must match the GitHub App configuration.
- `SESSION_SECRET` is a long random secret used for browser sessions.
- `ENCRYPTION_SECRET` must be a **Fernet key**, used to encrypt stored GitHub tokens. Keep it unchanged between restarts.
- Polarion credentials must belong to an account that can read the selected projects through Polarion's web services.
- Leave the template's `GITHUB_FINE_GRAINED_TOKEN` empty; the current application uses user login tokens.

If Python with `cryptography` is available, generate the two secrets with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

You can also run these through `uv run python` from the backend directory after `uv sync --extra dev`.

Edit `.env.frontend`:

```dotenv
VITE_POLARION_WEB_URL=https://polarion.example.com
```

This is the Polarion URL users open in their browsers. Docker Compose supplies the internal service URLs and configuration paths automatically. Keep secrets out of `VITE_*` variables, which are included in browser assets. Local environment files are ignored by Git.

## 4. Add the certificates

Place these PEM files in `docker/certs/`:

| File | Purpose |
| --- | --- |
| `lan-cert.pem` | HTTPS certificate for your application hostname |
| `lan-key.pem` | Matching private key |
| `polarion-ca.pem` | CA certificates used to trust your Polarion server |

Obtain appropriate certificates from your administrator. For local development, a self-signed certificate can be used if it includes `localhost` and is trusted by your browser. The current Docker configuration requires all three files.

On Linux, the backend runs as UID/GID `1000:1000`: it needs write access to `backend-data` and `cache`, and read access to the certificates.

## 5. Approve users in the whitelist

Edit `backend-data/github-user-config.json`. Add GitHub **login names**, not email addresses or display names:

```json
{
  "userNotAllowedMessage": {
    "header": "Access denied",
    "text": "Contact the administrator to request access."
  },
  "whiteList": [
    { "userName": "your-github-username" },
    { "userName": "another-approved-user" }
  ]
}
```

Preserve the property names shown above. Usernames are compared without regard to case. Whitelist edits take effect on the next authenticated request, so no restart is needed.

Approved users can query the shared index. PolRAGion does not check their individual Polarion permissions.

## 6. Select the Polarion documents to import

Edit `backend-data/polarion-import-config.json` using the copied example:

- Set `project_id` to the technical ID of your Polarion project.
- Set each document's `name` to its **Polarion document title**, not its path or module ID.
- Use `category` and `project_context` to group documents/projects for search filtering.
- Set `language` and descriptions to describe the source documents.
- Adjust `work_items.query` to select the relevant work-item types.
- Adjust `common_fields`, `fields_by_type`, and relationship fields for your Polarion installation. Remove example custom fields that do not exist there.
- Add further documents/projects by following the structure in the example. Use `enabled=false` to skip importing a project.

The [example JSON](../docker/polarion-import-config.example.json) defines the format; keep its structure and required properties. After changing document selection, restart the backend to refresh its metadata and run another import. Removing a selection does not delete previously indexed items.

## 7. Start the application and import data

From `docker/`:

```bash
docker compose --env-file .env.backend --env-file .env.frontend up -d --build
docker compose ps
docker compose logs -f polragion-backend
```

The first start downloads embedding models and can take several minutes. Open `https://localhost/` once the services are ready.

Imports are started explicitly. Run this from a trusted administrator machine to import the configured documents:

```bash
curl --fail --request POST "https://localhost/api/v1/work-items/ingest/import-polarion"
```

Use your deployment hostname and a trusted HTTPS certificate. For a small trial import, append `?limit=10` to the URL.

The import runs synchronously. For a large import that exceeds the proxy timeout, run it directly inside the backend container:

```bash
docker compose exec polragion-backend curl --fail --insecure --request POST https://localhost:8000/v1/work-items/ingest/import-polarion
```

The `--insecure` flag here is only for the container-local HTTPS connection. The current import endpoint is public; restrict external access to it if deploying beyond a trusted network.

Sign in with a whitelisted GitHub account and test a search for a known work item. Retrieved text is sent to GitHub Copilot when used in AI conversations, so select data appropriate for that use.

## Everyday commands

```bash
# View status and logs
docker compose ps
docker compose logs -f

# Apply code or environment changes
docker compose --env-file .env.backend --env-file .env.frontend up -d --build

# Stop the application; host data remains
docker compose down
```

Keep a secure backup of `backend-data`, Qdrant storage, your environment files, and certificates. For a simple file backup, stop the stack first. The encryption secret is needed to read stored GitHub tokens.

For optional configuration defaults, consult [backend settings](../polragion-backend/polragion/settings.py). For API details, use Swagger in development rather than maintaining an endpoint list here.
