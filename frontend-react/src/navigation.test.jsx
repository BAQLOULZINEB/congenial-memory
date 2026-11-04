import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

it("removes the closed mobile sidebar from accessibility and restores focus after Escape", () => {
  vi.spyOn(window, "matchMedia").mockImplementation((query) => ({
    matches: query === "(max-width: 680px)",
    media: query,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    addListener: vi.fn(),
    removeListener: vi.fn(),
  }));
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ status: "ready" }) }),
  );
  render(
    <MemoryRouter>
      <App />
    </MemoryRouter>,
  );
  const sidebar = document.getElementById("app-sidebar");
  expect(sidebar).toHaveAttribute("inert");
  expect(
    screen.queryByRole("link", { name: "Nouvelle analyse" }),
  ).not.toBeInTheDocument();
  const open = screen.getByRole("button", { name: "Ouvrir le menu" });
  fireEvent.click(open);
  expect(sidebar).not.toHaveAttribute("inert");
  expect(
    screen.getByRole("link", { name: "Nouvelle analyse" }),
  ).toBeInTheDocument();
  const first = sidebar.querySelector("a");
  expect(first).toHaveFocus();
  fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
  expect(
    sidebar.querySelectorAll("a")[sidebar.querySelectorAll("a").length - 1],
  ).toHaveFocus();
  fireEvent.keyDown(document, { key: "Escape" });
  expect(sidebar).toHaveAttribute("inert");
  expect(screen.getByRole("button", { name: "Ouvrir le menu" })).toHaveFocus();
});
