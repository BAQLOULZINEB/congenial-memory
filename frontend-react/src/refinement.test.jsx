import { useState } from "react";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import Architecture from "./Architecture";
import Settings from "./Settings";
import ScoreGauge from "./ScoreGauge";
import { defaultWeights } from "./demo";
afterEach(cleanup);
it("switches engineering views and explains the selected storage component", () => {
  render(<Architecture />);
  fireEvent.click(screen.getByRole("button", { name: /Données & API/ }));
  fireEvent.click(screen.getByRole("button", { name: /Conserver/ }));
  expect(screen.getByText(/id \(UUID\), title/)).toBeInTheDocument();
  fireEvent.click(screen.getByRole("button", { name: /Pipeline NLP/ }));
  expect(screen.getByRole("button", { name: /Comparer/ })).toBeInTheDocument();
});
it("presets change all criteria and invalid totals are visible", () => {
  function Harness() {
    const [weights, setWeights] = useState(defaultWeights);
    return (
      <Settings
        weights={weights}
        setWeights={setWeights}
        llm={false}
        setLLM={() => {}}
      />
    );
  }
  render(<Harness />);
  fireEvent.click(
    screen.getByRole("button", { name: "Équilibré", exact: true }),
  );
  for (const slider of screen.getAllByRole("slider"))
    expect(slider).toHaveValue("25");
  fireEvent.change(screen.getAllByRole("slider")[0], {
    target: { value: "30" },
  });
  expect(screen.getByRole("alert")).toHaveTextContent("105");
  fireEvent.click(screen.getByRole("button", { name: /Rétablir/ }));
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
it("gauge exposes the actual score and never invents an empty score", () => {
  const { rerender } = render(<ScoreGauge score={67.7} />);
  expect(screen.getByRole("img")).toHaveAccessibleName(
    "Adéquation : 67,7 sur 100",
  );
  rerender(<ScoreGauge />);
  expect(screen.getByRole("img")).toHaveAccessibleName(
    "Adéquation : aucune analyse",
  );
});
