/**
 * Device detection and mobile optimization utilities
 */

/**
 * Detects if the current device is likely a mobile device
 * Based on user agent, screen size, and touch capabilities
 */
export const isMobileDevice = (): boolean => {
    if (typeof window === "undefined") {
        return false;
    }

    // Check user agent for mobile indicators
    const userAgent = window.navigator.userAgent.toLowerCase();
    const mobileKeywords = [
        "android",
        "webos",
        "iphone",
        "ipad",
        "ipod",
        "blackberry",
        "windows phone",
        "mobile",
        "opera mini",
    ];

    const hasMobileUserAgent = mobileKeywords.some((keyword) => userAgent.includes(keyword));

    // Check screen size (typical mobile breakpoint)
    const hasSmallScreen = window.innerWidth <= 768;

    // Check for touch capability
    const hasTouchScreen = "ontouchstart" in window || navigator.maxTouchPoints > 0;

    // Consider it mobile if it has mobile user agent OR (small screen AND touch)
    return hasMobileUserAgent || (hasSmallScreen && hasTouchScreen);
};

/**
 * Detects if the user prefers reduced motion
 * Based on system settings or user preferences
 */
export const prefersReducedMotion = (): boolean => {
    if (typeof window === "undefined") {
        return false;
    }

    return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
};

/**
 * Gets the appropriate loader type based on device and preferences
 */
export const getOptimalLoaderType = (
    isMobile: boolean,
    mobileOptimizations: boolean,
    reducedMotion: boolean
): "simple" | "animated" => {
    if (reducedMotion || (isMobile && mobileOptimizations)) {
        return "simple";
    }
    return "animated";
};

/**
 * Determines if animations should be disabled
 */
export const shouldDisableAnimations = (
    isMobile: boolean,
    mobileOptimizations: boolean,
    reducedMotion: boolean
): boolean => {
    return reducedMotion || (isMobile && mobileOptimizations);
};
