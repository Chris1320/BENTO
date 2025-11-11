import { routing } from "@/i18n/routing";
import { theme, defaultColorscheme } from "@/lib/theme";
import { ColorSchemeScript, MantineProvider, mantineHtmlProps } from "@mantine/core";
import { NextIntlClientProvider } from "next-intl";
import { getMessages } from "next-intl/server";

import "@mantine/core/styles.css";
import "@mantine/charts/styles.css";
import "@mantine/dropzone/styles.css";
import "@mantine/notifications/styles.css";
import "@mantine/spotlight/styles.css";

interface LocaleLayoutProps {
    children: React.ReactNode;
    params: Promise<{ locale: string }>;
}

export function generateStaticParams() {
    return routing.locales.map((locale) => ({ locale }));
}

/**
 * LocaleLayout component handles locale-specific layout with i18n support.
 * This layout wraps the existing layout to provide internationalization.
 */
export default async function LocaleLayout({ children, params }: LocaleLayoutProps) {
    // Note: locale is available from params but getMessages() automatically
    // uses the current locale from the request context
    await params; // Ensure params is awaited even though we don't use the destructured value

    // Providing all messages to the client side is the easiest way to get started
    const messages = await getMessages();

    return (
        <html lang="en" {...mantineHtmlProps}>
            <head>
                <ColorSchemeScript />
            </head>
            <body>
                <MantineProvider theme={theme} defaultColorScheme={defaultColorscheme}>
                    <NextIntlClientProvider messages={messages}>{children}</NextIntlClientProvider>
                </MantineProvider>
            </body>
        </html>
    );
}
