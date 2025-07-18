import { GetAccessTokenHeader } from "@/lib/utils/token";

/**
 * Opens an OAuth popup window and returns a promise that resolves with the result
 * @param url - The OAuth authorization URL to open
 * @param provider - The OAuth provider name (e.g., 'google')
 * @returns Promise that resolves with the OAuth result
 */
export function openOAuthPopup(
    url: string,
    provider: string
): Promise<{ success: boolean; provider?: string; error?: string }> {
    return new Promise((resolve, reject) => {
        // Calculate popup dimensions and position
        const width = 500;
        const height = 600;
        const left = window.screen.width / 2 - width / 2;
        const top = window.screen.height / 2 - height / 2;

        // Open popup window
        const popup = window.open(
            url,
            `${provider}_oauth`,
            `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
        );

        if (!popup) {
            reject(new Error("Failed to open popup window. Please allow popups for this site."));
            return;
        }

        // Listen for messages from the popup
        const messageListener = (event: MessageEvent) => {
            // Verify origin for security
            if (event.origin !== window.location.origin) {
                return;
            }

            if (event.data.type === "OAUTH_RESULT") {
                // Clean up
                window.removeEventListener("message", messageListener);

                if (popup && !popup.closed) {
                    popup.close();
                }

                // Resolve with the result
                resolve(event.data);
            }
        };

        // Set up message listener
        window.addEventListener("message", messageListener);

        // Check if popup was closed manually
        const checkClosed = setInterval(() => {
            if (popup.closed) {
                clearInterval(checkClosed);
                window.removeEventListener("message", messageListener);
                reject(new Error("OAuth popup was closed by user"));
            }
        }, 1000);

        // Timeout after 5 minutes
        setTimeout(() => {
            clearInterval(checkClosed);
            window.removeEventListener("message", messageListener);
            if (popup && !popup.closed) {
                popup.close();
            }
            reject(new Error("OAuth popup timed out"));
        }, 5 * 60 * 1000);
    });
}

/**
 * Initiates Google OAuth linking using a popup
 * @returns Promise that resolves when the linking is complete
 */
export async function linkGoogleAccountPopup(): Promise<void> {
    const response = await fetch(`${process.env.NEXT_PUBLIC_CENTRAL_SERVER_ENDPOINT}/v1/auth/oauth/google/login/link`);

    if (!response.ok) {
        throw new Error("Failed to get OAuth authorization URL");
    }

    const data = await response.json();

    if (!data.url) {
        throw new Error("No OAuth authorization URL received");
    }

    // Open OAuth popup and wait for result
    const result = await openOAuthPopup(data.url, "google");

    if (!result.success) {
        throw new Error(result.error || "OAuth linking failed");
    }
}

/**
 * Initiates Google OAuth unlinking using a direct API call
 * @returns Promise that resolves when the unlinking is complete
 */
export async function unlinkGoogleAccountPopup(): Promise<void> {
    const response = await fetch(`${process.env.NEXT_PUBLIC_CENTRAL_SERVER_ENDPOINT}/v1/auth/oauth/google/unlink`, {
        method: "GET",
        headers: {
            Authorization: GetAccessTokenHeader(),
            "Content-Type": "application/json",
        },
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
            errorData.detail || `Failed to unlink Google account: ${response.status} ${response.statusText}`
        );
    }
}
