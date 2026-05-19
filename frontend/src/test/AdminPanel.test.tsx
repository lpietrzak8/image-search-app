import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import AdminPanel from "../pages/AdminPanel";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("../keycloak", () => ({
  default: {
    authenticated: true,
    token: "admin-token",
    tokenParsed: {
      preferred_username: "adminuser",
      email: "admin@example.com",
      realm_access: { roles: ["admin"] },
    },
    logout: vi.fn(),
  },
}));

const mockPosts = [
  { id: 1, author: "Alice", description: "Sunset photo", image_url: "http://img.com/1.jpg", keywords: ["sunset", "sky"], status: "pending" as const },
  { id: 2, author: "Bob", description: "Mountain view", image_url: "http://img.com/2.jpg", keywords: ["mountain"], status: "approved" as const },
];

function setupFetchMock(posts = mockPosts) {
  (window as any).fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: vi.fn().mockResolvedValue({ posts }),
  });
}

function renderAdminPanel(setIsLoggedIn = vi.fn()) {
  return render(
    <MemoryRouter>
      <AdminPanel setIsLoggedIn={setIsLoggedIn} />
    </MemoryRouter>
  );
}

describe("AdminPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupFetchMock();
  });

  it("renders the Admin Panel heading", async () => {
    renderAdminPanel();
    expect(screen.getByRole("heading", { name: /admin panel/i })).toBeInTheDocument();
  });

  it("renders the Posts Moderation tab button", () => {
    renderAdminPanel();
    expect(screen.getByRole("button", { name: /posts moderation/i })).toBeInTheDocument();
  });

  it("renders the Account Information tab button", () => {
    renderAdminPanel();
    expect(screen.getByRole("button", { name: /account information/i })).toBeInTheDocument();
  });

  it("renders the Log Out tab button", () => {
    renderAdminPanel();
    expect(screen.getByRole("button", { name: /^log out$/i })).toBeInTheDocument();
  });

  it("renders filter buttons in moderation tab", () => {
    renderAdminPanel();
    expect(screen.getByRole("button", { name: /^all$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^pending$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^approved$/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^rejected$/i })).toBeInTheDocument();
  });

  it("displays fetched posts", async () => {
    renderAdminPanel();
    await waitFor(() => {
      expect(screen.getByText("Alice")).toBeInTheDocument();
      expect(screen.getByText("Bob")).toBeInTheDocument();
    });
  });

  it("shows No posts found when list is empty", async () => {
    (window as any).fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi.fn().mockResolvedValue({ posts: [] }),
    });
    renderAdminPanel();
    await waitFor(() => {
      expect(screen.getByText(/no posts found/i)).toBeInTheDocument();
    });
  });

  it("calls approve endpoint when Approve button is clicked", async () => {
    renderAdminPanel();
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    const approveBtns = screen.getAllByText(/✓ approve/i);
    fireEvent.click(approveBtns[0]);
    await waitFor(() => {
      const calls = (window.fetch as any).mock.calls;
      expect(calls.some((c: any[]) => c[0].includes("/approve"))).toBe(true);
    });
  });

  it("calls reject endpoint when Reject button is clicked", async () => {
    renderAdminPanel();
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    const rejectBtns = screen.getAllByText(/✗ reject/i);
    fireEvent.click(rejectBtns[0]);
    await waitFor(() => {
      const calls = (window.fetch as any).mock.calls;
      expect(calls.some((c: any[]) => c[0].includes("/reject"))).toBe(true);
    });
  });

  it("calls delete endpoint when Delete button is clicked", async () => {
    window.confirm = vi.fn().mockReturnValue(true);
    renderAdminPanel();
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    const deleteBtns = screen.getAllByText(/🗑 delete/i);
    fireEvent.click(deleteBtns[0]);
    await waitFor(() => {
      const calls = (window.fetch as any).mock.calls;
      expect(calls.some((c: any[]) => (c[1] as any)?.method === "DELETE")).toBe(true);
    });
  });

  it("does not delete when confirm is cancelled", async () => {
    window.confirm = vi.fn().mockReturnValue(false);
    renderAdminPanel();
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    const initialCallCount = (window.fetch as any).mock.calls.length;
    const deleteBtns = screen.getAllByText(/🗑 delete/i);
    fireEvent.click(deleteBtns[0]);
    expect((window.fetch as any).mock.calls.length).toBe(initialCallCount);
  });

  it("switches to Account Information tab and shows admin data", async () => {
    renderAdminPanel();
    fireEvent.click(screen.getByRole("button", { name: /account information/i }));
    await waitFor(() => {
      expect(screen.getByText(/adminuser/i)).toBeInTheDocument();
      expect(screen.getByText(/admin@example\.com/i)).toBeInTheDocument();
      expect(screen.getByText(/administrator/i)).toBeInTheDocument();
    });
  });

  it("switches to Log Out tab and shows confirmation", () => {
    renderAdminPanel();
    fireEvent.click(screen.getByRole("button", { name: /^log out$/i }));
    expect(screen.getByText(/are you sure you want to log out/i)).toBeInTheDocument();
  });

  it("calls keycloak.logout on confirm logout", async () => {
    const keycloak = (await import("../keycloak")).default;
    const setIsLoggedIn = vi.fn();
    renderAdminPanel(setIsLoggedIn);
    fireEvent.click(screen.getByRole("button", { name: /^log out$/i }));
    fireEvent.click(screen.getByRole("button", { name: /yes, log out/i }));
    expect(keycloak.logout).toHaveBeenCalled();
    expect(setIsLoggedIn).toHaveBeenCalledWith(false);
  });

  it("changes filter to All and re-fetches", async () => {
    renderAdminPanel();
    await waitFor(() => expect(screen.getByText("Alice")).toBeInTheDocument());
    const initialCalls = (window.fetch as any).mock.calls.length;
    fireEvent.click(screen.getByRole("button", { name: /^all$/i }));
    await waitFor(() => {
      expect((window.fetch as any).mock.calls.length).toBeGreaterThan(initialCalls);
    });
  });

  it("redirects to /login when not authenticated", async () => {
    const keycloak = (await import("../keycloak")).default;
    (keycloak as any).authenticated = false;
    renderAdminPanel();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/login"));
    (keycloak as any).authenticated = true;
    (keycloak as any).tokenParsed = {
      preferred_username: "adminuser",
      email: "admin@example.com",
      realm_access: { roles: ["admin"] },
    };
  });

  it("redirects to / when user is not admin", async () => {
    const keycloak = (await import("../keycloak")).default;
    (keycloak as any).tokenParsed = {
      preferred_username: "regularuser",
      email: "user@example.com",
      realm_access: { roles: [] },
    };
    renderAdminPanel();
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith("/"));
    (keycloak as any).tokenParsed = {
      preferred_username: "adminuser",
      email: "admin@example.com",
      realm_access: { roles: ["admin"] },
    };
  });
});
