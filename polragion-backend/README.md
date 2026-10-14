# PolRAGion backend

FastAPI backend for Polarion ingestion, Qdrant retrieval, GitHub authentication, and Copilot conversations.

See the [project README](../README.md), [setup guide](../doc/setup.md), and [architecture notes](ARCHITECTURE.md). Current configuration defaults are in [settings.py](polragion/settings.py); Python requirements are in [pyproject.toml](pyproject.toml).

From this directory, run `uv sync --extra dev` to install dependencies and `uv run pytest` for tests. Enable `DEBUG=true` for Swagger API documentation in development.

## MCP (Streamable HTTP with personal bearer tokens)

Open **Settings → MCP Server** while signed into the website. The panel explains
setup and offers **Create Token for PolRAGion MCP Server**. The backend validates
the current website session, user and GitHub whitelist before issuing a random,
user-bound, read-only token. Copy the secret immediately; it is shown only until
leaving that tab or closing Settings. Only its SHA-256 hash is stored in SQLite.

The panel always lists your token metadata: creation date, expiration date and
Active/Expired/Revoked status. It also lets you revoke individual tokens and
reopen the detailed VS Code setup guide. Secrets are never saved in localStorage
or returned by the list endpoint. Tokens are personal credentials; keep them
private and do not commit them into configuration files.

Set backend environment variables as needed:

```dotenv
MCP_ENABLED=true
MCP_PUBLIC_URL=https://localhost/api
MCP_TOKEN_LIFETIME_DAYS=30
```

MCP is enabled by default. The token lifetime defaults to 30 days and can be
configured from 1 to 365 days; changes apply only to newly created tokens.
`MCP_PUBLIC_URL` is the externally reachable backend base URL without `/mcp/`.
If omitted, the website derives the MCP address from its configured API URL.
For local HTTP Uvicorn use `http://localhost:8000`; for the Docker nginx proxy
use `https://<host>/api`. No additional GitHub OAuth App or MCP login is needed.
The website still uses its existing GitHub authentication.

### VS Code

The website generates a configuration with the correct server URL. Example
`.vscode/mcp.json` (merge with any existing configuration):

```json
{
	"mcpServers": {
		"polragion-mcp": {
			"url": "https://localhost:8000/mcp/",
			"type": "http",
			"headers": {
				"Authorization": "Bearer [YOUR_TOKEN_STARTING_WITH_pmcp]"
			}
		}
	}
}
```

Start the MCP server in VS Code and paste the token into the password prompt.
The URL must be reachable and the TLS certificate trusted. Input variables are
supported by VS Code's `mcp.json` format; other clients may need their own secret
configuration. See the [VS Code configuration reference](https://code.visualstudio.com/docs/agents/reference/mcp-configuration).

### Expiration and revocation

Every request and tool execution revalidates the token, its owner and the
current whitelist without contacting GitHub. After expiry or revocation,
subsequent HTTP requests receive 401 and no new tool calls are permitted.
Calls already executing are not cancelled. There is no automatic refresh:
create a replacement on the website and update the MCP client's saved secret.
For the example above, change the input ID in both places (e.g.
`polragion-token-2`) to obtain a new prompt, then restart the connection.
You may create the replacement before the old token expires, switch your client,
and revoke the old token afterwards. Website logout does not revoke MCP tokens.

### Structure and tools

`models/mcp_token.py` defines credential records and public metadata.
`database/repository.py` defines the repository interface; its SQLite adapter
owns all SQL. `application/mcp_token_service.py` handles creation, hashing,
expiration and revocation through that interface. `infrastructure/mcp_auth.py`
adapts the shared whitelist and local token service to FastMCP authentication.
Management routes in `api/mcp_tokens.py` use the existing website session and
validate Origin and a custom header for writes.

- `GET /auth/mcp-tokens`: configuration and your token metadata.
- `POST /auth/mcp-tokens`: create a token; secret returned once with no-store.
- `DELETE /auth/mcp-tokens/<id>`: revoke a token owned by the current user.

POST/DELETE require `X-MCP-Token-Management: true`. Public URLs additionally
include the existing `/api` proxy prefix. SQLite schema creation adds the token
table automatically and is compatible with the earlier personal-token schema.
OAuth MCP endpoints and OAuth-specific settings are removed; OAuth credentials
issued by that earlier integration are no longer accepted. Existing unused
`mcp-oauth/` files are left untouched.

Copilot and MCP share `application/work_item_tools_service.py` and
`models/tool_parameters.py`. Four read-only tools are exposed with descriptions:
`search_work_items(params)`, `find_work_item_by_id(params)`,
`get_polarion_projects()` and `get_polarion_documents(params)`.
Server instructions describe scope, citations and index freshness. All allowed
users can read the indexed data; this does not introduce project-level ACLs.
MCP is mounted last at `/`, with its endpoint at `/mcp/`, preserving REST routing
behind nginx without a path-rewriting middleware. Its lifespan runs after the
backend initializes and ends before Qdrant closes.
