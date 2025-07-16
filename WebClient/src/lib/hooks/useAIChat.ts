import { useState, useCallback } from "react";
import { chatWithAI, ChatMessage } from "@/lib/api/ai";
import { customLogger } from "@/lib/api/customLogger";

export interface UseAIChatOptions {
    schoolId?: number;
    maxHistoryLength?: number;
}

export interface UseAIChatReturn {
    messages: ChatMessage[];
    loading: boolean;
    error: string | null;
    sendMessage: (message: string) => Promise<void>;
    clearMessages: () => void;
    schoolName: string | null;
}

export function useAIChat(options: UseAIChatOptions = {}): UseAIChatReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [schoolName, setSchoolName] = useState<string | null>(null);

    const { schoolId, maxHistoryLength = 20 } = options;

    const sendMessage = useCallback(
        async (message: string) => {
            if (!message.trim()) return;

            setLoading(true);
            setError(null);

            // Add user message
            const userMessage: ChatMessage = { role: "user", content: message };
            setMessages((prev) => [...prev, userMessage]);

            try {
                const response = await chatWithAI({
                    message,
                    school_id: schoolId,
                    conversation_history: messages.slice(-maxHistoryLength),
                });

                // Add assistant response
                const assistantMessage: ChatMessage = { role: "assistant", content: response.response };
                setMessages((prev) => [...prev, assistantMessage]);
                setSchoolName(response.school_name);
            } catch (err) {
                const errorMessage = err instanceof Error ? err.message : "Failed to send message";
                setError(errorMessage);
                customLogger.error("Failed to send chat message", err);

                // Remove the user message if the request failed
                setMessages((prev) => prev.slice(0, -1));
            } finally {
                setLoading(false);
            }
        },
        [messages, schoolId, maxHistoryLength]
    );

    const clearMessages = useCallback(() => {
        setMessages([]);
        setError(null);
        setSchoolName(null);
    }, []);

    return {
        messages,
        loading,
        error,
        sendMessage,
        clearMessages,
        schoolName,
    };
}
