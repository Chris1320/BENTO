import { useAIChat } from "@/lib/hooks/useAIChat";
import {
    ActionIcon,
    Alert,
    Badge,
    Button,
    Group,
    Loader,
    Modal,
    Paper,
    ScrollArea,
    Stack,
    Text,
    TextInput,
} from "@mantine/core";
import { IconAlertCircle, IconBrain, IconSend, IconTrash } from "@tabler/icons-react";
import React, { useState } from "react";

interface AIChatModalProps {
    opened: boolean;
    onClose: () => void;
    schoolId?: number;
}

export function AIChatModal({ opened, onClose, schoolId }: AIChatModalProps) {
    const [inputMessage, setInputMessage] = useState("");
    const { messages, loading, error, sendMessage, clearMessages, schoolName } = useAIChat({ schoolId });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!inputMessage.trim() || loading) return;

        await sendMessage(inputMessage);
        setInputMessage("");
    };

    return (
        <Modal
            opened={opened}
            onClose={onClose}
            title={
                <Group gap="sm">
                    <IconBrain size={20} />
                    <Text fw={600}>AI Financial Assistant</Text>
                    {schoolName && (
                        <Badge variant="light" color="blue">
                            {schoolName}
                        </Badge>
                    )}
                </Group>
            }
            size="lg"
            styles={{
                body: { padding: 0 },
                header: { paddingBottom: 12 },
            }}
        >
            <Stack gap="md" style={{ height: "500px" }}>
                {/* Chat Messages */}
                <ScrollArea flex={1} p="md" style={{ backgroundColor: "var(--mantine-color-gray-0)" }}>
                    <Stack gap="sm">
                        {messages.length === 0 ? (
                            <Text c="dimmed" ta="center" mt="xl">
                                👋 Hello! I&apos;m your AI financial assistant. Ask me anything about your school&apos;s
                                financial data.
                            </Text>
                        ) : (
                            messages.map((message, index) => (
                                <Paper
                                    key={index}
                                    p="sm"
                                    style={{
                                        backgroundColor:
                                            message.role === "user"
                                                ? "var(--mantine-color-blue-1)"
                                                : "var(--mantine-color-gray-2)",
                                        marginLeft: message.role === "user" ? "auto" : "0",
                                        marginRight: message.role === "user" ? "0" : "auto",
                                        maxWidth: "80%",
                                    }}
                                >
                                    <Text size="sm" style={{ whiteSpace: "pre-wrap" }}>
                                        {message.content}
                                    </Text>
                                </Paper>
                            ))
                        )}
                        {loading && (
                            <Paper p="sm" style={{ backgroundColor: "var(--mantine-color-gray-2)" }}>
                                <Group gap="sm">
                                    <Loader size="sm" />
                                    <Text size="sm" c="dimmed">
                                        AI is thinking...
                                    </Text>
                                </Group>
                            </Paper>
                        )}
                    </Stack>
                </ScrollArea>

                {/* Error Alert */}
                {error && (
                    <Alert
                        icon={<IconAlertCircle size={16} />}
                        title="Error"
                        color="red"
                        variant="light"
                        mx="md"
                        withCloseButton
                        onClose={() => {
                            /* Handle error dismissal */
                        }}
                    >
                        {error}
                    </Alert>
                )}

                {/* Input Area */}
                <Paper p="md" style={{ borderTop: "1px solid var(--mantine-color-gray-3)" }}>
                    <form onSubmit={handleSubmit}>
                        <Group gap="sm" align="flex-end">
                            <TextInput
                                flex={1}
                                placeholder="Ask about your school's financial data..."
                                value={inputMessage}
                                onChange={(e) => setInputMessage(e.target.value)}
                                disabled={loading}
                                size="sm"
                            />
                            <Button
                                type="submit"
                                size="sm"
                                disabled={!inputMessage.trim() || loading}
                                leftSection={<IconSend size={16} />}
                            >
                                Send
                            </Button>
                            {messages.length > 0 && (
                                <ActionIcon
                                    variant="light"
                                    color="red"
                                    size="sm"
                                    onClick={clearMessages}
                                    disabled={loading}
                                >
                                    <IconTrash size={16} />
                                </ActionIcon>
                            )}
                        </Group>
                    </form>
                </Paper>
            </Stack>
        </Modal>
    );
}
