"use client";

import { createContext, useContext, ReactNode, useEffect } from "react";
import { useLocalStorage } from "@mantine/hooks";
import { generateColors } from "@mantine/colors-generator";
import { UserPreferences } from "@/lib/types";
import { LocalStorage } from "@/lib/info";
import { isMobileDevice, prefersReducedMotion } from "@/lib/utils/deviceUtils";

interface ThemeContextType {
    userPreferences: UserPreferences;
    updatePreference: (key: keyof UserPreferences, value: string | boolean | null) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useThemeContext = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useThemeContext must be used within a ThemeProvider");
    }
    return context;
};

interface ThemeProviderProps {
    children: ReactNode;
}

export const DynamicThemeProvider = ({ children }: ThemeProviderProps) => {
    const [userPreferences, setUserPreferences] = useLocalStorage<UserPreferences>({
        key: LocalStorage.userPreferences,
        defaultValue: {
            accentColor: "#228be6",
            language: "en",
            mobileOptimizations: undefined, // Will be auto-detected on first load
            reducedMotion: undefined, // Will be auto-detected on first load
        },
    });

    const updatePreference = (key: keyof UserPreferences, value: string | boolean | null) => {
        setUserPreferences((prev) => ({ ...prev, [key]: value }));
    };

    // Auto-detect mobile optimizations and reduced motion preferences on first load only
    useEffect(() => {
        const AUTO_DETECT_KEY = `${LocalStorage.userPreferences}_autoDetected`;

        if (typeof window !== "undefined") {
            // Check if we've already done auto-detection
            const hasAlreadyDetected = localStorage.getItem(AUTO_DETECT_KEY) === "true";

            if (!hasAlreadyDetected) {
                let needsUpdate = false;
                const updates: Partial<UserPreferences> = {};

                // Only auto-detect if not explicitly set by user (undefined means never set)
                if (userPreferences.mobileOptimizations === undefined) {
                    const isMobile = isMobileDevice();
                    updates.mobileOptimizations = isMobile;
                    needsUpdate = true;
                }

                if (userPreferences.reducedMotion === undefined) {
                    const prefersReduced = prefersReducedMotion();
                    updates.reducedMotion = prefersReduced;
                    needsUpdate = true;
                }

                if (needsUpdate) {
                    setUserPreferences((prev) => ({ ...prev, ...updates }));
                }

                // Mark that we've done auto-detection
                localStorage.setItem(AUTO_DETECT_KEY, "true");
            }
        }
    }, [userPreferences, setUserPreferences]); // Include dependencies but use localStorage flag to prevent re-runs

    // Update CSS variables when accent color changes
    useEffect(() => {
        if (typeof window !== "undefined" && userPreferences.accentColor) {
            const root = document.documentElement;
            const accentColor = userPreferences.accentColor;

            // Validate that we have a valid hex color
            if (!accentColor || typeof accentColor !== "string" || !accentColor.startsWith("#")) {
                console.warn("Invalid accent color:", accentColor);
                return;
            }

            try {
                // Generate proper color shades using Mantine's color generator
                const colorShades = generateColors(accentColor);

                // Set the custom accent color shades
                colorShades.forEach((shade, index) => {
                    root.style.setProperty(`--mantine-color-accent-${index}`, shade);
                });

                // Update Mantine's primary color to use our accent color
                colorShades.forEach((shade, index) => {
                    root.style.setProperty(`--mantine-color-blue-${index}`, shade);
                });

                // Also update specific CSS variables that Mantine uses for primary colors
                root.style.setProperty("--mantine-primary-color-filled", colorShades[6]);
                root.style.setProperty("--mantine-primary-color-filled-hover", colorShades[7]);
                root.style.setProperty("--mantine-primary-color-light", colorShades[0]);
                root.style.setProperty("--mantine-primary-color-light-hover", colorShades[1]);
                root.style.setProperty("--mantine-primary-color-light-color", colorShades[6]);
            } catch (error) {
                console.error("Error generating colors for accent color:", accentColor, error);
            }
        }
    }, [userPreferences.accentColor]);

    return <ThemeContext.Provider value={{ userPreferences, updatePreference }}>{children}</ThemeContext.Provider>;
};
