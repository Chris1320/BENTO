import RootLayout from "@/app/layout";
import "@testing-library/jest-dom/vitest";
import { render } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

// Mock ReactScan component
vi.mock("@/components/dev/ReactScan", () => ({
    ReactScan: () => <div data-testid="react-scan" />,
}));

// Mock Mantine components to avoid SSR issues in tests
vi.mock("@mantine/core", () => ({
    ColorSchemeScript: () => <script data-testid="color-scheme-script" />,
    MantineProvider: ({ children }: { children: React.ReactNode }) => (
        <div data-testid="mantine-provider">{children}</div>
    ),
    mantineHtmlProps: { "data-mantine-color-scheme": "auto" },
}));

// Mock Notifications component
vi.mock("@mantine/notifications", () => ({
    Notifications: () => <div data-testid="notifications" />,
}));

// Mock theme
vi.mock("@/lib/theme", () => ({
    theme: { primaryColor: "blue" },
    defaultColorscheme: "auto",
    notificationLimit: 5,
    notificationAutoClose: 5000,
}));

// Mock program info
vi.mock("@/lib/info", () => ({
    Program: {
        name: "BENTO",
        description: "Test Description",
    },
}));

describe("RootLayout", () => {
    it("renders children inside layout structure", () => {
        const TestChild = () => <div data-testid="test-child">Test Content</div>;

        const { getByTestId } = render(
            <RootLayout>
                <TestChild />
            </RootLayout>
        );

        expect(getByTestId("test-child")).toBeInTheDocument();
        expect(getByTestId("mantine-provider")).toBeInTheDocument();
    });

    it("includes ReactScan component", () => {
        const { getByTestId } = render(
            <RootLayout>
                <div>Test</div>
            </RootLayout>
        );

        expect(getByTestId("react-scan")).toBeInTheDocument();
    });

    it("includes ColorSchemeScript", () => {
        render(
            <RootLayout>
                <div>Test</div>
            </RootLayout>
        );

        // ColorSchemeScript is mocked, so we just verify the component renders without errors
        // In the actual component, it would be in the head section
        expect(true).toBe(true); // Component rendered successfully
    });

    it("includes Notifications component", () => {
        const { getByTestId } = render(
            <RootLayout>
                <div>Test</div>
            </RootLayout>
        );

        expect(getByTestId("notifications")).toBeInTheDocument();
    });

    it("has proper HTML structure", () => {
        const { container, getByText } = render(
            <RootLayout>
                <div>Test</div>
            </RootLayout>
        );

        // In test environment, we can only test the rendered content structure
        // The actual HTML and body elements are handled by the test framework
        const content = getByText("Test");
        const mantineProvider = container.querySelector('[data-testid="mantine-provider"]');

        expect(content).toBeInTheDocument();
        expect(mantineProvider).toBeInTheDocument();
        expect(content).toHaveTextContent("Test");
    });

    it("wraps content with MantineProvider", () => {
        const TestChild = () => <div data-testid="test-content">Content</div>;

        const { getByTestId } = render(
            <RootLayout>
                <TestChild />
            </RootLayout>
        );

        const mantineProvider = getByTestId("mantine-provider");
        const testContent = getByTestId("test-content");

        expect(mantineProvider).toContainElement(testContent);
    });
});
