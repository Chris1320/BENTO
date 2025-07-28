/**
 * Error parsing utility for API responses
 * Provides user-friendly error messages based on API response status codes and error details
 */

interface APIError {
    response: {
        status: number;
        statusText: string;
        data?: unknown;
    };
    error?: unknown;
}

interface ParsedError {
    title: string;
    message: string;
    isUserFriendly: boolean;
}

/**
 * Maps common HTTP status codes to user-friendly error messages
 */
const STATUS_CODE_MESSAGES: Record<number, { title: string; message: string }> = {
    400: {
        title: "Invalid Input",
        message: "Please check the information you provided and try again.",
    },
    401: {
        title: "Authentication Required",
        message: "Please log in again to continue.",
    },
    403: {
        title: "Access Denied",
        message: "You don't have permission to perform this action.",
    },
    404: {
        title: "Not Found",
        message: "The requested resource could not be found.",
    },
    409: {
        title: "Conflict",
        message: "This action conflicts with existing data.",
    },
    422: {
        title: "Validation Error",
        message: "Please check the information you provided.",
    },
    429: {
        title: "Too Many Requests",
        message: "Please wait a moment before trying again.",
    },
    500: {
        title: "Server Error",
        message: "Something went wrong on our end. Please try again later.",
    },
    502: {
        title: "Service Unavailable",
        message: "The service is temporarily unavailable. Please try again later.",
    },
    503: {
        title: "Service Unavailable",
        message: "The service is temporarily down for maintenance.",
    },
};

/**
 * Context-specific error messages for different operations
 */
const CONTEXT_SPECIFIC_ERRORS: Record<string, Record<number, { title: string; message: string }>> = {
    createUser: {
        400: {
            title: "Invalid User Information",
            message:
                "Please check the username, email, and other details. Username may already exist or contain invalid characters.",
        },
        409: {
            title: "User Already Exists",
            message: "A user with this username or email already exists. Please choose a different username or email.",
        },
        422: {
            title: "Invalid User Data",
            message: "Please ensure all required fields are filled correctly and the password meets requirements.",
        },
    },
    updateUser: {
        400: {
            title: "Invalid Update Information",
            message: "Please check the updated information for any errors.",
        },
        404: {
            title: "User Not Found",
            message: "The user you're trying to update could not be found.",
        },
        409: {
            title: "Update Conflict",
            message: "The username or email you're trying to use is already taken by another user.",
        },
    },
    deleteUser: {
        404: {
            title: "User Not Found",
            message: "The user you're trying to delete could not be found.",
        },
        409: {
            title: "Cannot Delete User",
            message: "This user cannot be deleted because they have associated data or are currently active.",
        },
    },
    login: {
        401: {
            title: "Login Failed",
            message: "Invalid username or password. Please check your credentials and try again.",
        },
        403: {
            title: "Account Disabled",
            message: "Your account has been disabled. Please contact an administrator.",
        },
        429: {
            title: "Too Many Login Attempts",
            message: "Too many failed login attempts. Please wait before trying again.",
        },
    },
    uploadFile: {
        400: {
            title: "Invalid File",
            message: "The file you're trying to upload is invalid or corrupted.",
        },
        413: {
            title: "File Too Large",
            message: "The file you're trying to upload is too large. Please choose a smaller file.",
        },
        415: {
            title: "Unsupported File Type",
            message: "This file type is not supported. Please choose a different file.",
        },
    },
    createReport: {
        400: {
            title: "Invalid Report Data",
            message: "Please check all report fields and ensure the data is valid.",
        },
        409: {
            title: "Report Already Exists",
            message: "A report for this period already exists.",
        },
    },
    updateReport: {
        400: {
            title: "Invalid Report Update",
            message: "Please check the report data for any errors.",
        },
        409: {
            title: "Report Cannot Be Updated",
            message: "This report cannot be updated because it has been finalized or is being reviewed.",
        },
    },
};

/**
 * Extracts detailed error information from API response
 */
function extractErrorDetails(error: unknown): string | null {
    try {
        // Try to parse error response body if available
        if (error && typeof error === "object" && "response" in error) {
            const apiError = error as APIError;
            const data = apiError.response?.data;

            // Check for common error detail fields
            if (typeof data === "string") return data;
            if (data && typeof data === "object") {
                const errorData = data as Record<string, unknown>;
                if (errorData.detail && typeof errorData.detail === "string") return errorData.detail;
                if (errorData.message && typeof errorData.message === "string") return errorData.message;
                if (errorData.error && typeof errorData.error === "string") return errorData.error;

                // Check for validation errors
                if (errorData.errors && Array.isArray(errorData.errors)) {
                    return errorData.errors
                        .map((err: unknown) => {
                            if (typeof err === "string") return err;
                            if (err && typeof err === "object" && "message" in err) {
                                return (err as { message: string }).message;
                            }
                            return String(err);
                        })
                        .join("; ");
                }

                // Check for field-specific errors
                const fieldErrors = Object.entries(errorData)
                    .filter(([key, value]) => key !== "detail" && key !== "message" && value)
                    .map(([key, value]) => `${key}: ${String(value)}`)
                    .join("; ");

                if (fieldErrors) return fieldErrors;
            }
        }

        // Fallback to error message
        if (error && typeof error === "object" && "message" in error) {
            const errorWithMessage = error as { message: unknown };
            if (typeof errorWithMessage.message === "string") {
                return errorWithMessage.message;
            }
        }

        return null;
    } catch {
        return null;
    }
}

/**
 * Parses API errors and returns user-friendly error messages
 *
 * @param error - The error object from the API call
 * @param context - The context/operation being performed (e.g., 'createUser', 'login')
 * @param fallbackTitle - Optional fallback title if no specific error is found
 * @returns Parsed error with user-friendly title and message
 */
export function parseAPIError(
    error: APIError | Error | unknown,
    context?: string,
    fallbackTitle: string = "Error"
): ParsedError {
    // Handle network errors or non-API errors
    if (error instanceof Error && !("response" in error)) {
        return {
            title: "Connection Error",
            message: "Unable to connect to the server. Please check your internet connection and try again.",
            isUserFriendly: true,
        };
    }

    // Extract status code from API error
    const statusCode =
        error && typeof error === "object" && "response" in error ? (error as APIError).response?.status : undefined;

    if (!statusCode) {
        const errorMessage =
            error &&
            typeof error === "object" &&
            "message" in error &&
            typeof (error as { message: unknown }).message === "string"
                ? (error as { message: string }).message
                : "An unexpected error occurred. Please try again.";

        return {
            title: fallbackTitle,
            message: errorMessage,
            isUserFriendly: false,
        };
    }

    // Check for context-specific error messages first
    if (context && CONTEXT_SPECIFIC_ERRORS[context]?.[statusCode]) {
        const contextError = CONTEXT_SPECIFIC_ERRORS[context][statusCode];
        const details = extractErrorDetails(error);

        return {
            title: contextError.title,
            message: details || contextError.message,
            isUserFriendly: true,
        };
    }

    // Fall back to generic status code messages
    if (STATUS_CODE_MESSAGES[statusCode]) {
        const genericError = STATUS_CODE_MESSAGES[statusCode];
        const details = extractErrorDetails(error);

        return {
            title: genericError.title,
            message: details || genericError.message,
            isUserFriendly: true,
        };
    }

    // Final fallback
    const details = extractErrorDetails(error);
    return {
        title: fallbackTitle,
        message: details || `An error occurred (${statusCode}). Please try again.`,
        isUserFriendly: false,
    };
}

/**
 * Helper function to show better error notifications
 *
 * @param error - The error object from the API call
 * @param context - The context/operation being performed
 * @param notificationId - The ID for the notification
 * @param showFunction - The notification show function
 * @param fallbackTitle - Optional fallback title
 */
export function showAPIErrorNotification(
    error: unknown,
    context: string,
    notificationId: string,
    showFunction: (options: { id: string; title: string; message: string; color: string; autoClose?: number }) => void,
    fallbackTitle?: string
): void {
    const parsedError = parseAPIError(error, context, fallbackTitle);

    showFunction({
        id: notificationId,
        title: parsedError.title,
        message: parsedError.message,
        color: "red",
        autoClose: parsedError.isUserFriendly ? 5000 : 10000, // Keep generic errors visible longer
    });
}
