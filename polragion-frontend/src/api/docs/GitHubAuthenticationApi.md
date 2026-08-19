# GitHubAuthenticationApi

All URIs are relative to *http://localhost*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**githubLogin**](GitHubAuthenticationApi.md#githublogin) | **GET** /auth/github/login | Github Login |
| [**githubSwitchAccount**](GitHubAuthenticationApi.md#githubswitchaccount) | **GET** /auth/github/switch-account | Github Switch Account |
| [**logout**](GitHubAuthenticationApi.md#logout) | **POST** /auth/github/logout | Logout |
| [**me**](GitHubAuthenticationApi.md#me) | **GET** /auth/github/me | Me |



## githubLogin

> githubLogin(selectAccount)

Github Login

### Example

```ts
import {
  Configuration,
  GitHubAuthenticationApi,
} from '';
import type { GithubLoginRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new GitHubAuthenticationApi();

  const body = {
    // boolean (optional)
    selectAccount: true,
  } satisfies GithubLoginRequest;

  try {
    const data = await api.githubLogin(body);
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters


| Name | Type | Description  | Notes |
|------------- | ------------- | ------------- | -------------|
| **selectAccount** | `boolean` |  | [Optional] [Defaults to `false`] |

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **303** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## githubSwitchAccount

> githubSwitchAccount()

Github Switch Account

### Example

```ts
import {
  Configuration,
  GitHubAuthenticationApi,
} from '';
import type { GithubSwitchAccountRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new GitHubAuthenticationApi();

  try {
    const data = await api.githubSwitchAccount();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

`void` (Empty response body)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **303** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## logout

> any logout()

Logout

### Example

```ts
import {
  Configuration,
  GitHubAuthenticationApi,
} from '';
import type { LogoutRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new GitHubAuthenticationApi();

  try {
    const data = await api.logout();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

**any**

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## me

> User me()

Me

### Example

```ts
import {
  Configuration,
  GitHubAuthenticationApi,
} from '';
import type { MeRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new GitHubAuthenticationApi();

  try {
    const data = await api.me();
    console.log(data);
  } catch (error) {
    console.error(error);
  }
}

// Run the test
example().catch(console.error);
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**User**](User.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **200** | Successful Response |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

