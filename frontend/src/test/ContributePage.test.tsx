import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import ContributePage from "../pages/ContributePage";

vi.mock("../keycloak", () => ({
  default: {
    authenticated: false,
    token: null,
  },
}));

const mockRecaptchaToken = "mock-recaptcha-token";

function setupRecaptchaMock(shouldSucceed = true) {
  (window as any).grecaptcha = {
    ready: vi.fn((cb: () => void) => cb()),
    execute: shouldSucceed
      ? vi.fn().mockResolvedValue(mockRecaptchaToken)
      : vi.fn().mockRejectedValue(new Error("reCAPTCHA failed")),
  };
}

function triggerRecaptchaLoad() {
  const script = document.querySelector(
    'script[src*="recaptcha"]',
  ) as HTMLScriptElement | null;
  if (script?.onload) {
    script.onload(new Event("load"));
  }
}

function renderContributePage() {
  return render(
    <MemoryRouter>
      <ContributePage />
    </MemoryRouter>,
  );
}

describe("ContributePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    (window as any).grecaptcha = undefined;
    Object.defineProperty(URL, "createObjectURL", {
      value: vi.fn().mockReturnValue("blob:mock-url"),
      writable: true,
    });
  });

  it("renders the page title", () => {
    renderContributePage();
    expect(screen.getByText("Contribute Data")).toBeInTheDocument();
  });

  it("renders the description textarea", () => {
    renderContributePage();
    expect(
      screen.getByPlaceholderText(/describe what's in the image/i),
    ).toBeInTheDocument();
  });

  it("renders the file upload input", () => {
    renderContributePage();
    expect(screen.getByLabelText(/upload image/i)).toBeInTheDocument();
  });

  it("renders the submit button", () => {
    renderContributePage();
    expect(
      screen.getByRole("button", { name: /upload image/i }),
    ).toBeInTheDocument();
  });

  it("shows error when submitting without description and image", async () => {
    renderContributePage();
    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));
    await waitFor(() => {
      expect(
        screen.getByText(/please add a description and select an image/i),
      ).toBeInTheDocument();
    });
  });

  it("shows error when submitting without description only", async () => {
    renderContributePage();

    const file = new File(["content"], "photo.jpg", { type: "image/jpeg" });
    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));

    await waitFor(() => {
      expect(screen.getByText(/please add a description/i)).toBeInTheDocument();
    });
  });

  it("shows error when submitting without image only", async () => {
    renderContributePage();

    fireEvent.change(
      screen.getByPlaceholderText(/describe what's in the image/i),
      { target: { value: "A nice landscape photo" } },
    );

    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));

    await waitFor(() => {
      expect(screen.getByText(/please select an image/i)).toBeInTheDocument();
    });
  });

  it("shows image preview after selecting a file", async () => {
    renderContributePage();

    const file = new File(["image-content"], "sunset.jpg", {
      type: "image/jpeg",
    });

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(screen.getByText(/✓ sunset\.jpg/i)).toBeInTheDocument();
    });
  });

  it("shows remove image button after selecting a file", async () => {
    renderContributePage();

    const file = new File(["content"], "photo.png", { type: "image/png" });

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /remove image/i }),
      ).toBeInTheDocument();
    });
  });

  it("removes image preview when remove button is clicked", async () => {
    renderContributePage();

    const file = new File(["content"], "photo.png", { type: "image/png" });

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: /remove image/i }),
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: /remove image/i }));

    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: /remove image/i }),
      ).not.toBeInTheDocument();
    });
  });

  it("shows reCAPTCHA loading error when recaptcha not loaded", async () => {
    renderContributePage();

    const file = new File(["content"], "img.jpg", { type: "image/jpeg" });

    fireEvent.change(
      screen.getByPlaceholderText(/describe what's in the image/i),
      { target: { value: "A beautiful mountain landscape" } },
    );

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/recaptcha is still loading/i),
      ).toBeInTheDocument();
    });
  });

  it("calls fetch API with correct data on successful submit", async () => {
    setupRecaptchaMock(true);

    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi
        .fn()
        .mockResolvedValue({ message: "Thank you for your contribution!" }),
    });
    (window as any).fetch = mockFetch;

    renderContributePage();
    triggerRecaptchaLoad();

    const file = new File(["content"], "landscape.jpg", { type: "image/jpeg" });

    fireEvent.change(
      screen.getByPlaceholderText(/describe what's in the image/i),
      { target: { value: "A beautiful mountain landscape photo" } },
    );

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        "/api/contribute",
        expect.objectContaining({ method: "POST" }),
      );
    });
  });

  it("shows success message after successful upload", async () => {
    setupRecaptchaMock(true);
    (window as any).fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: vi
        .fn()
        .mockResolvedValue({ message: "Thank you for your contribution!" }),
    });

    renderContributePage();
    triggerRecaptchaLoad();

    const file = new File(["content"], "photo.jpg", { type: "image/jpeg" });

    fireEvent.change(
      screen.getByPlaceholderText(/describe what's in the image/i),
      { target: { value: "A beautiful mountain landscape photo" } },
    );

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/thank you for your contribution/i),
      ).toBeInTheDocument();
    });
  });

  it("shows error message on API failure", async () => {
    setupRecaptchaMock(true);
    (window as any).fetch = vi.fn().mockResolvedValue({
      ok: false,
      json: vi.fn().mockResolvedValue({
        error: "Invalid file extension. Allowed: PNG, JPG, JPEG, WebP",
      }),
    });

    renderContributePage();
    triggerRecaptchaLoad();

    const file = new File(["content"], "doc.gif", { type: "image/gif" });

    fireEvent.change(
      screen.getByPlaceholderText(/describe what's in the image/i),
      { target: { value: "A beautiful landscape photo here" } },
    );

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));

    await waitFor(() => {
      expect(screen.getByText(/invalid file extension/i)).toBeInTheDocument();
    });
  });

  it("shows network error message on fetch failure", async () => {
    setupRecaptchaMock(true);
    (window as any).fetch = vi
      .fn()
      .mockRejectedValue(new Error("Network error"));

    renderContributePage();
    triggerRecaptchaLoad();

    const file = new File(["content"], "img.jpg", { type: "image/jpeg" });

    fireEvent.change(
      screen.getByPlaceholderText(/describe what's in the image/i),
      { target: { value: "A beautiful landscape photo here" } },
    );

    const fileInput = screen.getByLabelText(/upload image/i);
    fireEvent.change(fileInput, { target: { files: [file] } });

    fireEvent.click(screen.getByRole("button", { name: /upload image/i }));

    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });
});
