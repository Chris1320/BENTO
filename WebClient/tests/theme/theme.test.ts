import { defaultColorscheme, theme } from "@/lib/theme";
import { describe, expect, it } from "vitest";

describe("Theme Configuration", () => {
    it("exports default colorscheme", () => {
        expect(defaultColorscheme).toBe("auto");
    });

    it("has correct theme structure", () => {
        expect(theme).toBeDefined();
        expect(typeof theme).toBe("object");
    });

    it("has default radius set to md", () => {
        expect(theme.defaultRadius).toBe("md");
    });

    it("has custom colors defined", () => {
        expect(theme.colors).toBeDefined();
        expect(theme.colors?.defaultColors).toBeDefined();
        expect(Array.isArray(theme.colors?.defaultColors)).toBe(true);
    });

    it("has correct number of color variations", () => {
        expect(theme.colors?.defaultColors).toHaveLength(10);
    });

    it("has valid color format", () => {
        const colors = theme.colors?.defaultColors;
        expect(colors).toBeDefined();

        // Check that all colors are valid hex colors
        colors?.forEach((color: string) => {
            expect(color).toMatch(/^#[0-9a-fA-F]{6}$/);
        });
    });

    it("has progressive color gradients", () => {
        const colors = theme.colors?.defaultColors;
        expect(colors).toBeDefined();

        // First color should be the lightest
        expect(colors?.[0]).toBe("#dffbff");

        // Last color should be the darkest
        expect(colors?.[9]).toBe("#007cb6");
    });
});
