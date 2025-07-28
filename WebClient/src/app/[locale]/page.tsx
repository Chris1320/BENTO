"use client";
import { LoadingComponent } from "@/components/LoadingComponent/LoadingComponent";
import { useRouter } from "@/i18n/navigation";
import { useEffect } from "react";

/**
 * Root page component.
 * @returns {JSX.Element} The rendered component.
 */
export default function RootPage() {
    const router = useRouter();

    useEffect(() => {
        // Always redirect to the login page
        router.replace("/login");
    }, [router]);

    return <LoadingComponent withBorder={false} />;
}
