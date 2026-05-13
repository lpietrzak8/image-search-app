import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import MissionPage from "../pages/MissionPage";

describe("MissionPage", () => {
  it("renders the heading", () => {
    render(<MissionPage />);
    expect(screen.getByRole("heading", { name: /our mission/i })).toBeInTheDocument();
  });

  it("renders the AI creativity statement", () => {
    render(<MissionPage />);
    expect(screen.getByText(/true creativity still begins with real people/i)).toBeInTheDocument();
  });

  it("renders the human artistry statement", () => {
    render(<MissionPage />);
    expect(screen.getByText(/genuine human artistry/i)).toBeInTheDocument();
  });

  it("renders the final tagline", () => {
    render(<MissionPage />);
    expect(screen.getByText(/only humans can create art/i)).toBeInTheDocument();
  });

  it("renders the container element", () => {
    const { container } = render(<MissionPage />);
    expect(container.querySelector(".mission-page-container")).toBeInTheDocument();
  });
});
