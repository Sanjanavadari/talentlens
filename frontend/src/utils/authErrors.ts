import axios from 'axios'

function parseDetail(detail: unknown): string | null {
  if (typeof detail === 'string') {
    return detail
  }
  return null
}

export function getAuthErrorMessage(error: unknown): string {
  if (!axios.isAxiosError(error)) {
    return 'Unable to connect to the server. Please try again later.'
  }

  if (!error.response) {
    return 'Unable to connect to the server. Please try again later.'
  }

  const status = error.response.status
  const detail = parseDetail(error.response.data?.detail)

  if (status === 404) {
    return "User not found. Please register if you don't have an account."
  }

  if (status === 401) {
    return 'Incorrect email or password.'
  }

  if (status >= 500) {
    return 'Unable to connect to the server. Please try again later.'
  }

  if (detail) {
    const normalized = detail.toLowerCase()
    if (normalized.includes('user not found')) {
      return "User not found. Please register if you don't have an account."
    }
    if (
      normalized.includes('invalid password') ||
      normalized.includes('incorrect email or password')
    ) {
      return 'Incorrect email or password.'
    }
  }

  return 'Unable to connect to the server. Please try again later.'
}
