"use client";

import { useLocale, useTranslations } from "next-intl";
import { useRouter, usePathname } from "@/i18n/navigation";
import { Select } from "@mantine/core";
import { IconLanguage } from "@tabler/icons-react";

interface LanguageSelectorProps {
    variant?: "default" | "minimal";
    size?: "xs" | "sm" | "md" | "lg" | "xl";
}

export function LanguageSelector({ variant = "default", size = "sm" }: LanguageSelectorProps) {
    const t = useTranslations("language");
    const locale = useLocale();
    const router = useRouter();
    const pathname = usePathname();

    const languages = [
        { value: "en", label: t("english") },
        { value: "fil", label: t("filipino") },
    ];

    const handleLanguageChange = (newLocale: string | null) => {
        if (newLocale && newLocale !== locale) {
            router.replace(pathname, { locale: newLocale });
        }
    };

    if (variant === "minimal") {
        return (
            <Select
                value={locale}
                data={languages}
                onChange={handleLanguageChange}
                size={size}
                variant="subtle"
                leftSection={<IconLanguage size={16} />}
                comboboxProps={{ withinPortal: true }}
                aria-label={t("select")}
            />
        );
    }

    return (
        <Select
            label={t("select")}
            description={t("changeLanguage")}
            value={locale}
            data={languages}
            onChange={handleLanguageChange}
            size={size}
            leftSection={<IconLanguage size={16} />}
            comboboxProps={{ withinPortal: true }}
        />
    );
}
