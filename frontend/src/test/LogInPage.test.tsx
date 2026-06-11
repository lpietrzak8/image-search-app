import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import LogInPage from "../pages/LogInPage";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("../keycloak", () => ({
  default: {
    authenticated: false,
    token: null,
    login: vi.fn(),
    register: vi.fn(),
  },
}));

function renderLogInPage(setIsLoggedIn = vi.fn()) {
  return render(
    <MemoryRouter>
      <LogInPage setIsLoggedIn={setIsLoggedIn} />
    </MemoryRouter>
  );
}

describe("LogInPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the welcome heading", () => {
    renderLogInPage();
    expect(screen.getByText(/welcome to photo-search/i)).toBeInTheDocument();
  });

  it("renders the login button", () => {
    renderLogInPage();
    expect(screen.getByRole("button", { name: /^login$/i })).toBeInTheDocument();
  });

  it("renders the register button", () => {
    renderLogInPage();
    expect(screen.getByRole("button", { name: /register/i })).toBeInTheDocument();
  });

  it("calls keycloak.login when Login button is clicked", async () => {
    const keycloak = (await import("../keycloak")).default;
    renderLogInPage();
    fireEvent.click(screen.getByRole("button", { name: /^login$/i }));
    expect(keycloak.login).toHaveBeenCalledWith(
      expect.objectContaining({ redirectUri: expect.stringContaining("/login") })
    );
  });

  it("calls keycloak.register when Register button is clicked", async () => {
    const keycloak = (await import("../keycloak")).default;
    renderLogInPage();
    fireEvent.click(screen.getByRole("button", { name: /register/i }));
    expect(keycloak.register).toHaveBeenCalledWith(
      expect.objectContaining({ redirectUri: expect.stringContaining("/login") })
    );
  });

  it("navigates to / when already authenticated", async () => {
    const keycloak = (await import("../keycloak")).default;
    (keycloak as any).authenticated = true;
    const setIsLoggedIn = vi.fn();
    renderLogInPage(setIsLoggedIn);
    await new Promise((r) => setTimeout(r, 200));
    expect(setIsLoggedIn).toHaveBeenCalledWith(true);
    expect(mockNavigate).toHaveBeenCalledWith("/");
    (keycloak as any).authenticated = false;
  });
});
