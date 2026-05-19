import { vi } from 'vitest'

vi.mock('../keycloak', () => ({
  default: {
    init: vi.fn().mockResolvedValue(false),
    authenticated: false,
    token: null,
    tokenParsed: null,
    onAuthSuccess: null,
    onAuthLogout: null,
    login: vi.fn(),
    logout: vi.fn(),
  },
}))

vi.mock('axios', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}))
