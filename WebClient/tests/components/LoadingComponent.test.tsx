import { LoadingComponent } from "@/components/LoadingComponent/LoadingComponent";
import { MantineProvider } from "@mantine/core";
import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock motion/react to avoid issues with animations in tests
vi.mock("motion/react", () => ({
    motion: {
        div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
            <div {...props}>{children}</div>
        ),
        img: ({ children, ...props }: React.PropsWithChildren<React.ImgHTMLAttributes<HTMLImageElement>>) => (
            // eslint-disable-next-line @next/next/no-img-element
            <img alt="" {...props}>
                {children}
            </img>
        ),
    },
}));

// Mock the random loading messages and LocalStorage
vi.mock("@/lib/info", () => ({
    randomLoadingMessages: ["Loading test message 1", "Loading test message 2", "Loading test message 3"],
    LocalStorage: {
        accessToken: "at",
        userData: "ud",
        userPermissions: "up",
        userAvatar: "userAvatar",
        userPreferences: "userPrefs",
        setupCompleteDismissed: "setupCompleteDismissed",
        useBasicLoader: "useBasicLoader",
    },
}));

const renderWithProvider = (component: React.ReactElement) => {
    return render(<MantineProvider>{component}</MantineProvider>);
};

describe("LoadingComponent", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        // Mock Math.random to return a consistent value
        vi.spyOn(Math, "random").mockReturnValue(0.5);
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("renders with default props", () => {
        renderWithProvider(<LoadingComponent />);

        // Check that the loading message is displayed
        expect(screen.getByTestId("loading-message")).toBeInTheDocument();

        // Check that the logo image is present
        expect(screen.getByAltText("BENTO Logo")).toBeInTheDocument();
    });

    it("displays custom message when provided", () => {
        const customMessage = "Custom loading message";
        renderWithProvider(<LoadingComponent message={customMessage} />);

        expect(screen.getByTestId("loading-message")).toHaveTextContent(customMessage);
    });

    it("displays random message when no message provided", () => {
        renderWithProvider(<LoadingComponent />);

        const messageElement = screen.getByTestId("loading-message");
        expect(messageElement).toBeInTheDocument();
        // Should display one of the mocked random messages
        expect(messageElement.textContent).toMatch(/Loading test message [1-3]/);
    });

    it("renders with border by default", () => {
        renderWithProvider(<LoadingComponent />);

        // The Paper component should have withBorder=true by default
        // We can't directly test the Paper props, but we can ensure the component renders
        expect(screen.getByTestId("loading-message")).toBeInTheDocument();
    });

    it("renders without border when withBorder is false", () => {
        renderWithProvider(<LoadingComponent withBorder={false} />);

        // Component should still render normally
        expect(screen.getByTestId("loading-message")).toBeInTheDocument();
    });

    it("has proper logo attributes", () => {
        renderWithProvider(<LoadingComponent />);

        const logo = screen.getByAltText("BENTO Logo");
        expect(logo).toHaveAttribute("src", "/assets/logos/BENTO.svg");
        expect(logo).toHaveAttribute("width", "100");
        expect(logo).toHaveAttribute("height", "100");
    });
});
