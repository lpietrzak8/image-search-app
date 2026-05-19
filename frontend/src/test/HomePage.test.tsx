import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import axios from "axios";
import HomePage from "../pages/HomePage";

vi.mock("../keycloak", () => ({
  default: {
    authenticated: false,
    token: null,
    tokenParsed: null,
  },
}));

vi.mock("axios", () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const mockEventSource = {
  addEventListener: vi.fn(),
  close: vi.fn(),
};

function renderHomePage(isLoggedIn = false) {
  return render(
    <MemoryRouter>
      <HomePage isLoggedIn={isLoggedIn} />
    </MemoryRouter>,
  );
}

describe("HomePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window as any).EventSource = vi.fn().mockReturnValue(mockEventSource);
  });

  it("renders the search textarea", () => {
    renderHomePage();
    expect(screen.getByPlaceholderText("Search...")).toBeInTheDocument();
  });

  it("renders the search button", () => {
    renderHomePage();
    expect(
      screen.getByRole("button", { name: /search for a photo/i }),
    ).toBeInTheDocument();
  });

  it('shows "Nothing to display yet" initially', () => {
    renderHomePage();
    expect(screen.getByText("Nothing to display yet")).toBeInTheDocument();
  });

  it("does not search when query is empty", () => {
    const mockedAxios = axios as any;
    renderHomePage();
    fireEvent.click(
      screen.getByRole("button", { name: /search for a photo/i }),
    );
    expect(mockedAxios.get).not.toHaveBeenCalled();
  });

  it("does not search when query is only whitespace", () => {
    const mockedAxios = axios as any;
    renderHomePage();
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "   " } });
    fireEvent.click(
      screen.getByRole("button", { name: /search for a photo/i }),
    );
    expect(mockedAxios.get).not.toHaveBeenCalled();
  });

  it("calls search API when query is provided", async () => {
    const mockedAxios = axios as any;
    mockedAxios.get.mockResolvedValueOnce({ data: { job_id: "test-job-123" } });

    renderHomePage();
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "mountains" } });
    fireEvent.click(
      screen.getByRole("button", { name: /search for a photo/i }),
    );

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalledWith(
        "/api/search",
        expect.objectContaining({
          params: expect.objectContaining({ s_query: "mountains" }),
        }),
      );
    });
  });

  it("shows loading state during search", async () => {
    const mockedAxios = axios as any;
    mockedAxios.get.mockResolvedValueOnce({ data: { job_id: "test-job-123" } });

    renderHomePage();
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "beach" } });
    fireEvent.click(
      screen.getByRole("button", { name: /search for a photo/i }),
    );

    await waitFor(() => {
      expect(screen.getByText(/searching\.\.\./i)).toBeInTheDocument();
    });
  });

  it("triggers search on Enter key", async () => {
    const mockedAxios = axios as any;
    mockedAxios.get.mockResolvedValueOnce({ data: { job_id: "test-job-456" } });

    renderHomePage();
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "forest" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: false });

    await waitFor(() => {
      expect(mockedAxios.get).toHaveBeenCalled();
    });
  });

  it("does not trigger search on Shift+Enter", () => {
    const mockedAxios = axios as any;
    renderHomePage();
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "forest" } });
    fireEvent.keyDown(textarea, { key: "Enter", shiftKey: true });
    expect(mockedAxios.get).not.toHaveBeenCalled();
  });

  it('shows "No results found" after search with empty results', async () => {
    const mockedAxios = axios as any;
    mockedAxios.get.mockResolvedValueOnce({ data: { job_id: "job-789" } });

    renderHomePage();
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "something" } });
    fireEvent.click(
      screen.getByRole("button", { name: /search for a photo/i }),
    );

    await waitFor(() => {
      expect((window as any).EventSource).toHaveBeenCalled();
    });

    const doneCallback = mockEventSource.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === "done",
    )?.[1];

    if (doneCallback) {
      doneCallback({ data: JSON.stringify([]) });
    }

    await waitFor(() => {
      expect(screen.getByText("No results found")).toBeInTheDocument();
    });
  });

  it("does not show save button for images when not logged in", async () => {
    const mockedAxios = axios as any;
    mockedAxios.get.mockResolvedValueOnce({ data: { job_id: "job-abc" } });

    renderHomePage(false);
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "cat" } });
    fireEvent.click(
      screen.getByRole("button", { name: /search for a photo/i }),
    );

    await waitFor(() => {
      expect((window as any).EventSource).toHaveBeenCalled();
    });

    const doneCallback = mockEventSource.addEventListener.mock.calls.find(
      (call: any[]) => call[0] === "done",
    )?.[1];

    if (doneCallback) {
      doneCallback({
        data: JSON.stringify([
          {
            id: "test-1",
            image_url: "http://example.com/cat.jpg",
            description: "A cat",
            provider: "pixabay",
          },
        ]),
      });
    }

    await waitFor(() => {
      expect(
        screen.queryByTitle("Save to My Resources"),
      ).not.toBeInTheDocument();
    });
  });

  it("clears the query after search is triggered", async () => {
    const mockedAxios = axios as any;
    mockedAxios.get.mockResolvedValueOnce({ data: { job_id: "job-clear" } });

    renderHomePage();
    const textarea = screen.getByPlaceholderText("Search...");
    fireEvent.change(textarea, { target: { value: "sunset" } });
    fireEvent.click(
      screen.getByRole("button", { name: /search for a photo/i }),
    );

    await waitFor(() => {
      expect((textarea as HTMLTextAreaElement).value).toBe("");
    });
  });
});
