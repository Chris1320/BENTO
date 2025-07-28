"use client";

import { useEffect, useState } from "react";
import { Card, Text, Stack, Button, Group } from "@mantine/core";
import { IconDownload } from "@tabler/icons-react";

interface BeforeInstallPromptEvent extends Event {
    readonly platforms: string[];
    readonly userChoice: Promise<{
        outcome: "accepted" | "dismissed";
        platform: string;
    }>;
    prompt(): Promise<void>;
}

export function PWADebugInfo() {
    const [debugInfo, setDebugInfo] = useState<{
        isInstalled: boolean;
        isInstallable: boolean;
        isServiceWorkerSupported: boolean;
        isServiceWorkerRegistered: boolean;
        userAgent: string;
        displayMode: string;
        isIOS: boolean;
        isAndroid: boolean;
        isSecureContext: boolean;
    }>({
        isInstalled: false,
        isInstallable: false,
        isServiceWorkerSupported: false,
        isServiceWorkerRegistered: false,
        userAgent: "",
        displayMode: "",
        isIOS: false,
        isAndroid: false,
        isSecureContext: false,
    });

    const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);

    useEffect(() => {
        const checkPWAStatus = async () => {
            const isInstalled = window.matchMedia("(display-mode: standalone)").matches;
            const isServiceWorkerSupported = "serviceWorker" in navigator;
            const userAgent = navigator.userAgent;
            const displayMode = window.matchMedia("(display-mode: standalone)").matches ? "standalone" : "browser";
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
            const isAndroid = /Android/.test(navigator.userAgent);
            const isSecureContext = location.protocol === "https:" || location.hostname === "localhost";

            let isServiceWorkerRegistered = false;
            if (isServiceWorkerSupported) {
                try {
                    const registration = await navigator.serviceWorker.getRegistration();
                    isServiceWorkerRegistered = !!registration;
                } catch (error) {
                    console.error("Error checking service worker:", error);
                }
            }

            setDebugInfo({
                isInstalled,
                isInstallable: !!installPrompt,
                isServiceWorkerSupported,
                isServiceWorkerRegistered,
                userAgent,
                displayMode,
                isIOS,
                isAndroid,
                isSecureContext,
            });
        };

        const handleBeforeInstallPrompt = (e: BeforeInstallPromptEvent) => {
            e.preventDefault();
            setInstallPrompt(e);
            checkPWAStatus();
        };

        window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
        checkPWAStatus();

        return () => {
            window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
        };
    }, [installPrompt]);

    const handleInstall = async () => {
        if (!installPrompt) return;

        try {
            installPrompt.prompt();
            const { outcome } = await installPrompt.userChoice;
            console.log("Install outcome:", outcome);
            if (outcome === "accepted") {
                setInstallPrompt(null);
            }
        } catch (error) {
            console.error("Error during installation:", error);
        }
    };

    if (process.env.NODE_ENV === "production") {
        return null; // Don't show in production
    }

    return (
        <Card withBorder p="md" style={{ position: "fixed", top: 10, right: 10, width: 350, zIndex: 1000 }}>
            <Stack gap="xs">
                <Text fw={600} size="sm">
                    PWA Debug Info
                </Text>

                <Text size="xs">
                    <strong>Installed:</strong> {debugInfo.isInstalled ? "✅" : "❌"}
                </Text>
                <Text size="xs">
                    <strong>Installable:</strong> {debugInfo.isInstallable ? "✅" : "❌"}
                </Text>
                <Text size="xs">
                    <strong>Service Worker Supported:</strong> {debugInfo.isServiceWorkerSupported ? "✅" : "❌"}
                </Text>
                <Text size="xs">
                    <strong>Service Worker Registered:</strong> {debugInfo.isServiceWorkerRegistered ? "✅" : "❌"}
                </Text>
                <Text size="xs">
                    <strong>Secure Context:</strong> {debugInfo.isSecureContext ? "✅" : "❌"}
                </Text>
                <Text size="xs">
                    <strong>Display Mode:</strong> {debugInfo.displayMode}
                </Text>
                <Text size="xs">
                    <strong>iOS:</strong> {debugInfo.isIOS ? "✅" : "❌"}
                </Text>
                <Text size="xs">
                    <strong>Android:</strong> {debugInfo.isAndroid ? "✅" : "❌"}
                </Text>

                {installPrompt && (
                    <Group gap="xs">
                        <Button size="xs" leftSection={<IconDownload size={12} />} onClick={handleInstall}>
                            Install Now
                        </Button>
                    </Group>
                )}

                <Text size="xs" c="dimmed" style={{ wordBreak: "break-all" }}>
                    <strong>User Agent:</strong> {debugInfo.userAgent}
                </Text>
            </Stack>
        </Card>
    );
}
