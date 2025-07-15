import * as csclient from "@/lib/api/csclient";
import { customLogger } from "@/lib/api/customLogger";

export interface AIInsightsRequest {
    school_id?: number;
    year?: number;
    month?: number;
}

export interface AIInsightsResponse {
    insights: string;
    school_name: string;
    period: string;
}

export interface ChatMessage {
    role: "user" | "assistant";
    content: string;
}

export interface ChatRequest {
    message: string;
    school_id?: number;
    conversation_history?: ChatMessage[];
}

export interface ChatResponse {
    response: string;
    school_name: string;
}

export interface AIStatus {
    status: "available" | "unavailable" | "error";
    message: string;
    model?: string;
    features: {
        insights: boolean;
        chat: boolean;
    };
}

/**
 * Generate AI insights for financial data
 */
export async function generateFinancialInsights(request: AIInsightsRequest = {}): Promise<AIInsightsResponse> {
    try {
        const response = await csclient.generateFinancialInsightsV1AiInsightsPost({
            body: {
                school_id: request.school_id,
                year: request.year,
                month: request.month,
            },
        });

        if (response.error) {
            const errorMessage = Array.isArray(response.error.detail)
                ? response.error.detail.map((e) => e.msg).join(", ")
                : response.error.detail || "Failed to generate insights";
            throw new Error(errorMessage);
        }

        return response.data as AIInsightsResponse;
    } catch (error) {
        customLogger.error("Failed to generate AI insights", error);
        throw error;
    }
}

/**
 * Chat with AI about financial data
 */
export async function chatWithAI(request: ChatRequest): Promise<ChatResponse> {
    try {
        const response = await csclient.chatWithAiV1AiChatPost({
            body: {
                message: request.message,
                school_id: request.school_id,
                conversation_history: request.conversation_history || [],
            },
        });

        if (response.error) {
            const errorMessage = Array.isArray(response.error.detail)
                ? response.error.detail.map((e) => e.msg).join(", ")
                : response.error.detail || "Failed to process chat request";
            throw new Error(errorMessage);
        }

        return response.data as ChatResponse;
    } catch (error) {
        customLogger.error("Failed to chat with AI", error);
        throw error;
    }
}

/**
 * Get AI service status
 */
export async function getAIStatus(): Promise<AIStatus> {
    try {
        const response = await csclient.getAiStatusV1AiStatusGet();

        if (response.error) {
            throw new Error("Failed to get AI status");
        }

        return response.data as unknown as AIStatus;
    } catch (error) {
        customLogger.error("Failed to get AI status", error);
        throw error;
    }
}

/**
 * Check if AI features are available
 */
export async function isAIAvailable(): Promise<boolean> {
    try {
        const status = await getAIStatus();
        return status.status === "available";
    } catch (error) {
        customLogger.warn("AI service is not available", error);
        return false;
    }
}
