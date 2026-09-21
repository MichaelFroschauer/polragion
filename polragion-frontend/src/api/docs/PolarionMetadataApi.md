# PolarionMetadataApi

All URIs are relative to *https://localhost:8000/api*

| Method | HTTP request | Description |
|------------- | ------------- | -------------|
| [**getPolarionImportConfig**](PolarionMetadataApi.md#getpolarionimportconfig) | **GET** /v1/polarion-metadata/get-config | Get Polarion Import Config |
| [**getPolarionSearchScopes**](PolarionMetadataApi.md#getpolarionsearchscopes) | **GET** /v1/polarion-metadata/get-search-scopes | Get Polarion Search Scopes |
| [**loadPolarionImportConfig**](PolarionMetadataApi.md#loadpolarionimportconfig) | **POST** /v1/polarion-metadata/load-config | Load Polarion Import Config |



## getPolarionImportConfig

> PolarionImportConfig getPolarionImportConfig()

Get Polarion Import Config

### Example

```ts
import {
  Configuration,
  PolarionMetadataApi,
} from '';
import type { GetPolarionImportConfigRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PolarionMetadataApi();

  try {
    const data = await api.getPolarionImportConfig();
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

[**PolarionImportConfig**](PolarionImportConfig.md)

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


## getPolarionSearchScopes

> PolarionMetadataResponse getPolarionSearchScopes()

Get Polarion Search Scopes

### Example

```ts
import {
  Configuration,
  PolarionMetadataApi,
} from '';
import type { GetPolarionSearchScopesRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PolarionMetadataApi();

  try {
    const data = await api.getPolarionSearchScopes();
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

[**PolarionMetadataResponse**](PolarionMetadataResponse.md)

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


## loadPolarionImportConfig

> PolarionImportConfig loadPolarionImportConfig()

Load Polarion Import Config

### Example

```ts
import {
  Configuration,
  PolarionMetadataApi,
} from '';
import type { LoadPolarionImportConfigRequest } from '';

async function example() {
  console.log("🚀 Testing  SDK...");
  const api = new PolarionMetadataApi();

  try {
    const data = await api.loadPolarionImportConfig();
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

[**PolarionImportConfig**](PolarionImportConfig.md)

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

