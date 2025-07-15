import { defaultColorscheme, theme } from "@/lib/theme";
import { describe, expect, it } from "vitest";

describe("Theme configuration", () => {
    it("has correct default color scheme", () => {
        expect(defaultColorscheme).toBe("auto");
    });

    it("has theme object", () => {
        expect(theme).toBeDefined();
        expect(typeof theme).toBe("object");
    });

    it("has colors configuration", () => {
        expect(theme.colors).toBeDefined();
        expect(theme.colors).toHaveProperty("defaultColors");
    });

    it("default colors is a valid Mantine color tuple", () => {
        const colors = theme.colors?.defaultColors;
        expect(Array.isArray(colors)).toBe(true);
        expect(colors).toHaveLength(10);

        // Each color should be a valid hex color
        colors?.forEach((color: string) => {
            expect(color).toMatch(/^#[0-9a-fA-F]{6}$/);
        });
    });

    it("colors progress from light to dark", () => {
        const colors = theme.colors?.defaultColors;
        if (colors) {
            // First color should be lighter (higher values)
            const firstColor = colors[0];
            const lastColor = colors[colors.length - 1];

            expect(firstColor).toMatch(/^#[d-f]/); // Lighter colors start with d-f
            expect(lastColor).toMatch(/^#[0-9a-c]/); // Darker colors start with 0-c
        }
    });
});
