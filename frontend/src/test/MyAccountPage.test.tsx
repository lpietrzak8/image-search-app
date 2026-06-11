import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
import MyAccountPage from "../pages/MyAccountPage";

const mockNavigate = vi.fn();
vi.mock("react-router-dom", async () => {
  const actual = await vi.importActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

vi.mock("../keycloak", () => ({
  default: {
    authenticated: true,
    token: "mock-token",
    tokenParsed: {
      preferred_username: "testuser",
      email: "test@example.com",
    },
    logout: vi.fn(),
  },
}));

vi.mock("axios", () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

function renderMyAccountPage(
    setIsLoggedIn = vi.fn(),
    setSelectedPost = vi.fn(),
    handleDeletePhoto = vi.fn(),
    deletingId = null,
    loading = false,) {
  return render(
    <MemoryRouter>
      <MyAccountPage
          setIsLoggedIn={setIsLoggedIn}
          setSelectedPost={setSelectedPost}
          handleDeletePhoto={handleDeletePhoto}
          deletingId={deletingId}
          loading={loading}
          savedPhotos={[]}
      />
    </MemoryRouter>
  );
}

describe("MyAccountPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page heading", () => {
    renderMyAccountPage();
    expect(screen.getByRole("heading", { name: /my account/i })).toBeInTheDocument();
  });

  it("renders the My Resources tab button", () => {
    renderMyAccountPage();
    expect(screen.getByRole("button", { name: /my resources/i })).toBeInTheDocument();
  });

  it("renders the Account Information tab button", () => {
    renderMyAccountPage();
    expect(screen.getByRole("button", { name: /account information/i })).toBeInTheDocument();
  });

  it("renders the Log Out tab button", () => {
    renderMyAccountPage();
    expect(screen.getByRole("button", { name: /^log out$/i })).toBeInTheDocument();
  });

  it("shows empty saved photos message when no photos", async () => {
    (axios.get as any).mockResolvedValue({ data: [] });
    renderMyAccountPage();
    await waitFor(() => {
      expect(screen.getByText(/you haven't saved any photos yet/i)).toBeInTheDocument();
    });
  });

  it("shows saved photos when data is returned", async () => {
    render(
        <MemoryRouter>
          <MyAccountPage
              setIsLoggedIn={vi.fn()}
              setSelectedPost={vi.fn()}
              handleDeletePhoto={vi.fn()}
              deletingId={null}
              loading={false}
              savedPhotos={[
                {
                  id: "1",
                  author: {
                    author_name: "John",
                    author_url: null,
                  },
                  source_url: "http://img.com",
                  image_url: "http://img.com/1.jpg",
                  description: "Sunset",
                  provider: "pixabay",
                  created_at: null },
              ]}
          />
        </MemoryRouter>
    )
    renderMyAccountPage();
    await waitFor(() => {
      expect(screen.getByRole("img", { name: /sunset/i })).toBeInTheDocument();
    });
  });

  it("switches to Account Information tab and shows username", async () => {
    renderMyAccountPage();
    fireEvent.click(screen.getByRole("button", { name: /account information/i }));
    await waitFor(() => {
      expect(screen.getByText(/testuser/i)).toBeInTheDocument();
      expect(screen.getByText(/test@example\.com/i)).toBeInTheDocument();
    });
  });

  it("switches to Log Out tab and shows confirmation", () => {
    renderMyAccountPage();
    fireEvent.click(screen.getByRole("button", { name: /^log out$/i }));
    expect(screen.getByText(/are you sure you want to log out/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /yes, log out/i })).toBeInTheDocument();
  });

  it("calls keycloak.logout and setIsLoggedIn when confirming logout", async () => {
    const keycloak = (await import("../keycloak")).default;
    const setIsLoggedIn = vi.fn();
    renderMyAccountPage(setIsLoggedIn);
    fireEvent.click(screen.getByRole("button", { name: /^log out$/i }));
    fireEvent.click(screen.getByRole("button", { name: /yes, log out/i }));
    expect(keycloak.logout).toHaveBeenCalled();
    expect(setIsLoggedIn).toHaveBeenCalledWith(false);
  });

  it("redirects to /login when not authenticated", async () => {
    const keycloak = (await import("../keycloak")).default;
    (keycloak as any).authenticated = false;
    renderMyAccountPage();
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
    (keycloak as any).authenticated = true;
  });

  it("deletes a saved photo when remove button is clicked", async () => {
    const handleDeletePhoto = vi.fn();

    render(
        <MemoryRouter>
          <MyAccountPage
              setIsLoggedIn={vi.fn()}
              setSelectedPost={vi.fn()}
              handleDeletePhoto={handleDeletePhoto}
              deletingId={null}
              loading={false}
              savedPhotos={[
                {
                  id: "1",
                  author: {
                    author_name: "John",
                    author_url: null,
                  },
                  source_url: "http://img.com",
                  image_url: "http://img.com/1.jpg",
                  description: "Sunset",
                  provider: "pixabay",
                  created_at: null },
              ]}
          />
        </MemoryRouter>
    )

    renderMyAccountPage();

    fireEvent.click(screen.getByTitle(/remove from saved/i))

    expect(handleDeletePhoto).toHaveBeenCalledTimes(1);
    expect(handleDeletePhoto).toHaveBeenCalledWith(
        expect.objectContaining({ id: "1", description: "Sunset" }),
    )
  });
});
