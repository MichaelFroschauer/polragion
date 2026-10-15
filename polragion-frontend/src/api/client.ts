import {
  Configuration,
  GitHubAuthenticationApi,
  GitHubModelsApi,
  HealthApi, MCPCredentialsApi,
  PolarionMetadataApi,
  WorkItemsApi,
} from "./index";

const config = new Configuration({
  basePath: import.meta.env.VITE_API_URL ?? "http://localhost:8000",
  credentials: "include",
});

export const apiBasePath = config.basePath;

export const workItemsApi = new WorkItemsApi(config);
export const healthApi = new HealthApi(config);
export const gitHubAuthApi = new GitHubAuthenticationApi(config);
export const gitHubModelsApi = new GitHubModelsApi(config);
export const polarionMetadataApi = new PolarionMetadataApi(config);


const mcpConfig = new Configuration({
  basePath: config.basePath,
  credentials: config.credentials,
  headers: {
    "Content-Type": "application/json",
    "X-MCP-Token-Management": "true",
  },
});

export const mcpTokensApi = new MCPCredentialsApi(mcpConfig);
