"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { customLogger } from "@/lib/api/customLogger";
import { GetAccessTokenHeader } from "@/lib/utils/token";

function OAuthCallbackContent() {
    const searchParams = useSearchParams();

    useEffect(() => {
        const handleOAuthCallback = async () => {
            try {
                const code = searchParams.get("code");
                const error = searchParams.get("error");
                const provider = "google"; // For now, we only support Google

                if (error) {
                    throw new Error(`OAuth error: ${error}`);
                }

                if (!code) {
                    throw new Error("No authorization code received");
                }

                customLogger.debug("OAuth callback received:", { code, provider });

                // Call the OAuth link endpoint with the redirect URI
                const currentOrigin = window.location.origin;
                const redirectUri = `${currentOrigin}/account/oauth-callback`;

                const response = await fetch(
                    `${
                        process.env.NEXT_PUBLIC_CENTRAL_SERVER_ENDPOINT
                    }/v1/auth/oauth/google/link?code=${encodeURIComponent(code)}&redirect_uri=${encodeURIComponent(
                        redirectUri
                    )}`,
                    {
                        method: "GET",
                        headers: {
                            Authorization: GetAccessTokenHeader(),
                            "Content-Type": "application/json",
                        },
                    }
                );

                if (!response.ok) {
                    throw new Error(`Failed to link account: ${response.status} ${response.statusText}`);
                }

                // Success - the account has been linked

                // Send success message to parent window
                if (window.opener) {
                    window.opener.postMessage(
                        {
                            type: "OAUTH_RESULT",
                            success: true,
                            provider,
                        },
                        window.location.origin
                    );
                }

                // Close the popup
                window.close();
            } catch (error) {
                customLogger.error("OAuth callback error:", error);

                // Send error message to parent window
                if (window.opener) {
                    window.opener.postMessage(
                        {
                            type: "OAUTH_RESULT",
                            success: false,
                            error: error instanceof Error ? error.message : "OAuth linking failed",
                        },
                        window.location.origin
                    );
                }

                // Close the popup
                window.close();
            }
        };

        handleOAuthCallback();
    }, [searchParams]);

    return (
        <div style={{ textAlign: "center" }}>
            <h3>Processing OAuth...</h3>
            <p>Please wait while we link your account.</p>
        </div>
    );
}

export default function OAuthCallbackPage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <OAuthCallbackContent />
        </Suspense>
    );
}
