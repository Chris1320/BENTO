import { useState, useEffect, useCallback } from "react";
import { generateFinancialInsights, AIInsightsResponse, isAIAvailable } from "@/lib/api/ai";
import { customLogger } from "@/lib/api/customLogger";

export interface UseAIInsightsOptions {
    schoolId?: number;
    year?: number;
    month?: number;
    autoFetch?: boolean;
}

export interface UseAIInsightsReturn {
    insights: AIInsightsResponse | null;
    loading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
    isAvailable: boolean;
}

export function useAIInsights(options: UseAIInsightsOptions = {}): UseAIInsightsReturn {
    const [insights, setInsights] = useState<AIInsightsResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isAvailable, setIsAvailable] = useState(false);

    const { schoolId, year, month, autoFetch = true } = options;

    // Check if AI is available
    useEffect(() => {
        const checkAvailability = async () => {
            try {
                const available = await isAIAvailable();
                setIsAvailable(available);
            } catch (err) {
                customLogger.warn("Failed to check AI availability", err);
                setIsAvailable(false);
            }
        };

        checkAvailability();
    }, []);

    const fetchInsights = useCallback(async () => {
        if (!isAvailable) {
            setError("AI service is not available");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const response = await generateFinancialInsights({
                school_id: schoolId,
                year,
                month,
            });
            setInsights(response);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : "Failed to generate insights";
            setError(errorMessage);
            customLogger.error("Failed to fetch AI insights", err);
        } finally {
            setLoading(false);
        }
    }, [isAvailable, schoolId, year, month]);

    // Auto-fetch when available and options are provided
    useEffect(() => {
        if (autoFetch && isAvailable) {
            fetchInsights();
        }
    }, [autoFetch, isAvailable, fetchInsights]);

    return {
        insights,
        loading,
        error,
        refetch: fetchInsights,
        isAvailable,
    };
}
