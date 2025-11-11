import { redirect } from "next/navigation";

/**
 * Root page that redirects to the default locale.
 * This is required for next-intl routing when using the [locale] segment.
 */
export default function RootPage() {
    redirect("/en");
}
