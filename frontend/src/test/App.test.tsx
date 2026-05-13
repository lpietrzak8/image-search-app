import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import App from "../App";
import keycloak from "../keycloak";

vi.mock("../keycloak", () => ({
  default: {
    authenticated: false,
    token: null,
    tokenParsed: null,
    onAuthSuccess: null,
    onAuthLogout: null,
    init: vi.fn().mockResolvedValue(false),
    login: vi.fn(),
    logout: vi.fn(),
    register: vi.fn(),
  },
}));

vi.mock("axios", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

describe("App", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state before keycloak initializes", () => {
    let resolveInit: (val: boolean) => void;
    (keycloak.init as any) = vi.fn().mockReturnValue(
      new Promise((r) => {
        resolveInit = r;
      }),
    );
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    resolveInit!(false);
  });

  it("renders Navbar after keycloak initializes", async () => {
    (keycloak.init as any) = vi.fn().mockResolvedValue(false);
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });
  });

  it("renders HomePage on / route", async () => {
    (keycloak.init as any) = vi.fn().mockResolvedValue(false);
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("textbox")).toBeInTheDocument();
    });
  });

  it("renders MissionPage on /mission route", async () => {
    (keycloak.init as any) = vi.fn().mockResolvedValue(false);
    render(
      <MemoryRouter initialEntries={["/mission"]}>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /our mission/i }),
      ).toBeInTheDocument();
    });
  });

  it("renders ContributePage on /contribute route", async () => {
    (keycloak.init as any) = vi.fn().mockResolvedValue(false);
    render(
      <MemoryRouter initialEntries={["/contribute"]}>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /contribute data/i }),
      ).toBeInTheDocument();
    });
  });

  it("sets isLoggedIn to true when keycloak returns authenticated", async () => {
    (keycloak.init as any) = vi.fn().mockResolvedValue(true);
    (keycloak as any).authenticated = true;
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });
    (keycloak as any).authenticated = false;
  });

  it("still initializes when keycloak init rejects", async () => {
    (keycloak.init as any) = vi
      .fn()
      .mockRejectedValue(new Error("Keycloak error"));
    render(
      <MemoryRouter>
        <App />
      </MemoryRouter>,
    );
    await waitFor(() => {
      expect(screen.getByRole("navigation")).toBeInTheDocument();
    });
  });
});
