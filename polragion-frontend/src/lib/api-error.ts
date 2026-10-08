import { ResponseError } from "@/api/runtime"

const fallbackMessage = "Something went wrong while contacting the backend. Please try again."

export async function getApiErrorMessage(error: unknown): Promise<string> {
  if (!(error instanceof ResponseError)) {
    return fallbackMessage
  }

  const { response } = error
  if (response.status === 401) return "Your session or GitHub authorization has expired. Please sign in again."
  if (response.status === 403) return "You do not have permission to perform this action."
  if (response.status === 414) return "Your request is too long. Please shorten the prompt and try again."
  if (response.status === 429) return "Too many requests. Please try again later."
  if (response.status === 408 || response.status === 504) return "The request timed out. Please try again."
  if (response.status === 502 || response.status === 503) return "A backend service is temporarily unavailable. Please try again later."

  if ([400, 409, 413, 422].includes(response.status)) {
    try {
      const body: unknown = await response.json()
      if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
        return body.detail
      }
    } catch {
      // Upstream servers may send an HTML error page instead of JSON.
    }
    return "Please check your input and try again."
  }

  return fallbackMessage
}