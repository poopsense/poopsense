import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, it } from "vitest";
import DemoReportContent from "./DemoReportContent";
afterEach(cleanup);

it("renders structured model sections and preserves actionable advice and links", () => {
  render(<DemoReportContent text={'## 本次观察\n\n红色模拟样本。\n\n## 可以从这些小事开始\n\n### 安排活动\n\n**怎么做：**选择适合自己的活动。\n\n## 下一次怎么观察\n\n记录感受。\n\n[来源](https://example.com)'} />);
  expect(screen.getByRole("heading", { name: "这次记录了什么" })).toBeVisible();
  expect(screen.getByRole("heading", { name: "安排活动" })).toBeVisible();
  expect(screen.getByText(/选择适合自己的活动/)).toBeVisible();
  expect(screen.queryByText(/\*\*怎么做/)).not.toBeInTheDocument();
  expect(screen.getByRole("link", { name: "来源" })).toHaveAttribute("href", "https://example.com/");
});

it("preserves existing unstructured reports", () => {
  render(<DemoReportContent text="原来已保存的报告正文。" />);
  expect(screen.getByText("原来已保存的报告正文。")).toBeVisible();
});
