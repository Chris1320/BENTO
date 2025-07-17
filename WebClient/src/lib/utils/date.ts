import dayjs from "dayjs";
import timezone from "dayjs/plugin/timezone";
import utc from "dayjs/plugin/utc";

// Configure dayjs with timezone support
dayjs.extend(utc);
dayjs.extend(timezone);

/**
 * Converts a UTC date string to the user's local timezone
 * @param utcDateString - The UTC date string from the server
 * @returns A dayjs object in the user's local timezone
 */
export function utcToLocal(utcDateString: string | null | undefined): dayjs.Dayjs | null {
    if (!utcDateString) return null;

    // Parse the UTC date string and convert to local timezone
    return dayjs.utc(utcDateString).local();
}

/**
 * Formats a UTC date string to a localized date string
 * @param utcDateString - The UTC date string from the server
 * @param format - The format string (defaults to 'MM/DD/YYYY, h:mm:ss A')
 * @returns A formatted date string in the user's local timezone
 */
export function formatUTCDate(
    utcDateString: string | null | undefined,
    format: string = "MM/DD/YYYY, h:mm:ss A"
): string {
    const localDate = utcToLocal(utcDateString);
    return localDate ? localDate.format(format) : "N/A";
}

/**
 * Formats a UTC date string to a localized date only (no time)
 * @param utcDateString - The UTC date string from the server
 * @param format - The format string (defaults to 'MM/DD/YYYY')
 * @returns A formatted date string in the user's local timezone
 */
export function formatUTCDateOnly(utcDateString: string | null | undefined, format: string = "MM/DD/YYYY"): string {
    const localDate = utcToLocal(utcDateString);
    return localDate ? localDate.format(format) : "N/A";
}

/**
 * Formats a UTC date string using toLocaleDateString for better localization
 * @param utcDateString - The UTC date string from the server
 * @param locale - The locale string (defaults to undefined for browser default)
 * @param options - Intl.DateTimeFormatOptions
 * @returns A formatted date string in the user's local timezone
 */
export function formatUTCDateLocalized(
    utcDateString: string | null | undefined,
    locale?: string,
    options?: Intl.DateTimeFormatOptions
): string {
    const localDate = utcToLocal(utcDateString);
    if (!localDate) return "N/A";

    const defaultOptions: Intl.DateTimeFormatOptions = {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZoneName: "short",
    };

    return localDate.toDate().toLocaleDateString(locale, { ...defaultOptions, ...options });
}

/**
 * Formats a UTC date string using toLocaleDateString for date only
 * @param utcDateString - The UTC date string from the server
 * @param locale - The locale string (defaults to undefined for browser default)
 * @param options - Intl.DateTimeFormatOptions
 * @returns A formatted date string in the user's local timezone
 */
export function formatUTCDateOnlyLocalized(
    utcDateString: string | null | undefined,
    locale?: string,
    options?: Intl.DateTimeFormatOptions
): string {
    // const localDate = utcToLocal(utcDateString);
    const localDate = dayjs(utcDateString);
    if (!localDate) return "N/A";

    const defaultOptions: Intl.DateTimeFormatOptions = {
        year: "numeric",
        month: "long",
        day: "numeric",
    };

    return localDate.toDate().toLocaleDateString(locale, { ...defaultOptions, ...options });
}

/**
 * Gets the current local timezone name
 * @returns The timezone name (e.g., 'America/New_York', 'Europe/London')
 */
export function getCurrentTimezone(): string {
    return dayjs.tz.guess();
}

/**
 * Checks if a date is today in the user's local timezone
 * @param utcDateString - The UTC date string from the server
 * @returns True if the date is today in local timezone
 */
export function isToday(utcDateString: string | null | undefined): boolean {
    const localDate = utcToLocal(utcDateString);
    if (!localDate) return false;

    return localDate.isSame(dayjs(), "day");
}

/**
 * Gets a relative time string (e.g., "2 hours ago", "in 3 days")
 * @param utcDateString - The UTC date string from the server
 * @returns A relative time string in the user's local timezone
 */
export function getRelativeTime(utcDateString: string | null | undefined): string {
    const localDate = utcToLocal(utcDateString);
    // const localDate = dayjs(utcDateString);
    if (!localDate) return "N/A";

    return localDate.fromNow();
}
