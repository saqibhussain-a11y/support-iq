import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AnswerText } from "./answer-text";

const PASSWORD_ANSWER = [
  "To reset your password, click the **“Forgot password”** link on the login page.  ",
  "A reset link will be emailed to the address on file and will expire after **1 hour**.  ",
  "",
  "*Support agents cannot reset passwords manually or send a link to any other email address.*",
].join("\n");

describe("AnswerText", () => {
  it("renders markdown emphasis as formatting instead of showing asterisks", () => {
    const { container } = render(<AnswerText text={PASSWORD_ANSWER} />);

    expect(container.textContent).not.toContain("*");
    expect(screen.getByText("“Forgot password”").tagName).toBe("STRONG");
    expect(screen.getByText("1 hour").tagName).toBe("STRONG");
    expect(
      screen.getByText("Support agents cannot reset passwords manually or send a link to any other email address.")
        .tagName,
    ).toBe("EM");
  });

  it("renders numbered steps as a real list", () => {
    render(<AnswerText text={"1. Open Account Settings\n2. Click Cancel Plan"} />);

    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(screen.getByRole("list").tagName).toBe("OL");
  });

  it("does not render raw HTML from the model", () => {
    const { container } = render(<AnswerText text={'Hello <img src="x" onerror="alert(1)"> there'} />);

    expect(container.querySelector("img")).toBeNull();
  });
});
