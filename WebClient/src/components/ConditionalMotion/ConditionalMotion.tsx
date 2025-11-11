/**
 * Conditional motion wrapper that respects user preferences for reduced motion and mobile optimizations
 */

import { motion, type MotionProps } from "motion/react";
import { ReactNode } from "react";
import { useThemeContext } from "@/lib/providers/theme";
import { shouldDisableAnimations, isMobileDevice } from "@/lib/utils/deviceUtils";

interface ConditionalMotionDivProps extends Omit<MotionProps, "children"> {
    children: ReactNode;
    fallback?: ReactNode;
}

/**
 * A motion.div wrapper that conditionally applies animations based on user preferences
 * Falls back to a regular div when animations should be disabled
 */
export const ConditionalMotion: React.FC<ConditionalMotionDivProps> = ({ children, fallback, ...motionProps }) => {
    // Safely get theme context, fallback to defaults if not available
    let userPreferences;
    try {
        const themeContext = useThemeContext();
        userPreferences = themeContext.userPreferences;
    } catch {
        // Fallback when used outside ThemeProvider
        userPreferences = {
            accentColor: "#228be6",
            language: "en",
            mobileOptimizations: undefined,
            reducedMotion: undefined,
        };
    }

    const isMobile = typeof window !== "undefined" ? isMobileDevice() : false;
    const disableAnimations = shouldDisableAnimations(
        isMobile,
        userPreferences.mobileOptimizations ?? false,
        userPreferences.reducedMotion ?? false
    );

    if (disableAnimations) {
        // Return fallback content or children wrapped in a regular div
        if (fallback) {
            return <>{fallback}</>;
        }

        return <div>{children}</div>;
    }

    // Return the motion.div component with all props
    return <motion.div {...motionProps}>{children}</motion.div>;
};

/**
 * Hook to determine if animations should be disabled based on current context
 */
export const useMotionPreferences = () => {
    // Safely get theme context, fallback to defaults if not available
    let userPreferences;
    try {
        const themeContext = useThemeContext();
        userPreferences = themeContext.userPreferences;
    } catch {
        // Fallback when used outside ThemeProvider
        userPreferences = {
            accentColor: "#228be6",
            language: "en",
            mobileOptimizations: undefined,
            reducedMotion: undefined,
        };
    }

    const isMobile = typeof window !== "undefined" ? isMobileDevice() : false;
    const disableAnimations = shouldDisableAnimations(
        isMobile,
        userPreferences.mobileOptimizations ?? false,
        userPreferences.reducedMotion ?? false
    );

    return {
        disableAnimations,
        isMobile,
        mobileOptimizations: userPreferences.mobileOptimizations ?? false,
        reducedMotion: userPreferences.reducedMotion ?? false,
    };
};
