import {
  Configuration,
  GitHubAuthenticationApi,
  GitHubModelsApi,
  HealthApi,
  WorkItemsApi,
} from "./index";

const config = new Configuration({
  basePath: import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000",
  credentials: "include",
});

export const apiBasePath = config.basePath;

export const workItemsApi = new WorkItemsApi(config);
export const healthApi = new HealthApi(config);
export const gitHubAuthApi = new GitHubAuthenticationApi(config);
export const gitHubModelsApi = new GitHubModelsApi(config);