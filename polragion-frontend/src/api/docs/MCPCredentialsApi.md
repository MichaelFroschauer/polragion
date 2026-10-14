# MCPCredentialsApi

All URIs are relative to *https://localhost:8000/api*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**createMcpToken**](MCPCredentialsApi.md#createmcptoken) | **POST** /auth/mcp-tokens | Create Mcp Token |
| [**listMcpTokens**](MCPCredentialsApi.md#listmcptokens) | **GET** /auth/mcp-tokens | List Mcp Tokens |
| [**revokeMcpToken**](MCPCredentialsApi.md#revokemcptoken) | **DELETE** /auth/mcp-tokens/{token_id} | Revoke Mcp Token |



## createMcpToken

> IssuedToken createMcpToken(createToken)

Create Mcp Token

### Example

```ts
import {
  Configuration,
  MCPCredentialsApi,
} from '';
import type { CreateMcpTokenRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MCPCredentialsApi();

  const body = {
    // CreateToken
    createToken: ...,
  } satisfies CreateMcpTokenRequest;

  try {
    const data = await api.createMcpToken(body);
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
| **createToken** | [CreateToken](CreateToken.md) |  | |

### Return type

[**IssuedToken**](IssuedToken.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: `application/json`
- **Accept**: `application/json`


### HTTP response details
| Status code | Description | Response headers |
|-------------|-------------|------------------|
| **201** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)


## listMcpTokens

> TokenOverview listMcpTokens()

List Mcp Tokens

### Example

```ts
import {
  Configuration,
  MCPCredentialsApi,
} from '';
import type { ListMcpTokensRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MCPCredentialsApi();

  try {
    const data = await api.listMcpTokens();
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

[**TokenOverview**](TokenOverview.md)

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


## revokeMcpToken

> revokeMcpToken(tokenId)

Revoke Mcp Token

### Example

```ts
import {
  Configuration,
  MCPCredentialsApi,
} from '';
import type { RevokeMcpTokenRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new MCPCredentialsApi();

  const body = {
    // string
    tokenId: 38400000-8cf0-11bd-b23e-10b96e4ef00d,
  } satisfies RevokeMcpTokenRequest;

  try {
    const data = await api.revokeMcpToken(body);
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
| **tokenId** | `string` |  | [Defaults to `undefined`] |

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
| **204** | Successful Response |  -  |
| **422** | Validation Error |  -  |

[[Back to top]](#) [[Back to API list]](../README.md#api-endpoints) [[Back to Model list]](../README.md#models) [[Back to README]](../README.md)

