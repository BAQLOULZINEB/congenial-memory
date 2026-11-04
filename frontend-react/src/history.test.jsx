import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";
import SavedAnalyses, { SaveAnalysis } from "./SavedAnalyses";
import App from "./App";

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});
const response = (body, status = 200) => ({
  ok: status < 400,
  status,
  json: async () => body,
});
const saved = {
  id: "example-id",
  title: "Bilan développeuse",
  score: 67.7,
  is_demo: true,
  created_at: "2026-11-04T08:00:00+00:00",
  result: { score: 67.7 },
};

describe("Explicit report persistence", () => {
  it("does not save automatically and submits only on explicit action", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(saved, 201));
    vi.stubGlobal("fetch", fetchMock);
    const onSaved = vi.fn();
    render(
      <MemoryRouter>
        <SaveAnalysis
          result={saved.result}
          isDemo
          savedId={null}
          onSaved={onSaved}
        />
      </MemoryRouter>,
    );
    expect(fetchMock).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Nom du bilan"), {
      target: { value: "Bilan développeuse" },
    });
    fireEvent.click(
      screen.getByRole("button", { name: "Enregistrer ce bilan" }),
    );
    await waitFor(() => expect(onSaved).toHaveBeenCalledWith(saved.id));
    const [url, request] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/analyses");
    expect(JSON.parse(request.body)).toEqual({
      title: saved.title,
      result: saved.result,
      is_demo: true,
    });
  });

  it("reopens a report from the database", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(response({ items: [saved], total: 1 }))
        .mockResolvedValueOnce(response(saved)),
    );
    const onOpen = vi.fn();
    render(
      <MemoryRouter>
        <SavedAnalyses onOpen={onOpen} onDeleted={vi.fn()} />
      </MemoryRouter>,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: "Ouvrir le bilan" }),
    );
    await waitFor(() => expect(onOpen).toHaveBeenCalledWith(saved));
  });

  it("requires confirmation before deleting, then refreshes the list", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(response({ items: [saved], total: 1 }))
      .mockResolvedValueOnce(response(null, 204))
      .mockResolvedValueOnce(response({ items: [], total: 0 }));
    vi.stubGlobal("fetch", fetchMock);
    const onDeleted = vi.fn();
    render(
      <MemoryRouter>
        <SavedAnalyses onOpen={vi.fn()} onDeleted={onDeleted} />
      </MemoryRouter>,
    );
    fireEvent.click(
      await screen.findByRole("button", { name: `Supprimer ${saved.title}` }),
    );
    expect(fetchMock).toHaveBeenCalledTimes(1);
    fireEvent.click(
      screen.getByRole("button", { name: "Confirmer la suppression" }),
    );
    await waitFor(() => expect(onDeleted).toHaveBeenCalledWith(saved.id));
    expect(
      await screen.findByText("Votre histoire commence ici."),
    ).toBeInTheDocument();
    expect(fetchMock.mock.calls[1][1].method).toBe("DELETE");
  });

  it("shows a recoverable database error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    render(
      <MemoryRouter>
        <SavedAnalyses onOpen={vi.fn()} onDeleted={vi.fn()} />
      </MemoryRouter>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent("injoignable");
    expect(screen.getByRole("button", { name: "Réessayer" })).toBeEnabled();
  });

  it("explains the prototype layers including the database", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(response({ status: "ready" })),
    );
    render(
      <MemoryRouter initialEntries={["/architecture"]}>
        <App />
      </MemoryRouter>,
    );
    expect(
      screen.getByRole("heading", { name: "04 · La mémoire du prototype" }),
    ).toBeInTheDocument();
    expect(screen.getByText("SQLite · stockage local")).toBeInTheDocument();
    expect(
      screen.getByText(/Le cahier des charges définit le pipeline/),
    ).toBeInTheDocument();
  });
});
