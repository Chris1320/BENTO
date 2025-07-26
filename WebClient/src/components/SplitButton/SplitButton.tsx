"use client";

import { ActionIcon, Button, Group, Menu, useMantineTheme } from "@mantine/core";
import { IconChevronDown, IconEye, IconSend } from "@tabler/icons-react";
import { useState } from "react";
import { useUser } from "@/lib/providers/user";
import { SubmitForReviewModal } from "./SubmitForReviewModal";
import classes from "./SplitButton.module.css";

interface SplitButtonProps {
    onSaveReport?: () => void;
    onSubmitForReview?: () => void;
    onPreview?: () => void;
    disabled?: boolean;
    className?: string;
    children?: React.ReactNode;
    showPreview?: boolean;
    // Submit for Review props
    reportType?: "daily" | "payroll" | "liquidation" | "monthly";
    reportPeriod?: {
        schoolId: number;
        year: number;
        month: number;
        category?: string; // For liquidation reports
    };
    onSubmitForReviewSuccess?: () => void;
}

export function SplitButton({
    onSaveReport,
    onSubmitForReview,
    onPreview,
    disabled = false,
    className = "",
    children = "Save Report",
    showPreview = true,
    reportType,
    reportPeriod,
    onSubmitForReviewSuccess,
}: SplitButtonProps) {
    const theme = useMantineTheme();
    const [submitForReviewModalOpened, setSubmitForReviewModalOpened] = useState(false);
    const userCtx = useUser();

    // Only show for Canteen Managers (roleId: 5)
    const isCanteenManager = userCtx.userInfo?.roleId === 5;
    const canShowSubmitForReview = isCanteenManager && reportType && reportPeriod;

    const handleSubmitForReviewClick = () => {
        if (onSubmitForReview) {
            onSubmitForReview();
        } else if (canShowSubmitForReview) {
            setSubmitForReviewModalOpened(true);
        }
    };

    const handleSubmitForReviewSuccess = () => {
        setSubmitForReviewModalOpened(false);
        if (onSubmitForReviewSuccess) {
            onSubmitForReviewSuccess();
        }
    };

    return (
        <>
            <Group wrap="nowrap" gap={0}>
                <Button className={`${classes.button} ${className}`} onClick={onSaveReport} disabled={disabled}>
                    {children}
                </Button>
                <Menu transitionProps={{ transition: "pop" }} position="bottom-end" withinPortal>
                    <Menu.Target>
                        <ActionIcon
                            variant="filled"
                            color={theme.primaryColor}
                            size={36}
                            className={classes.menuControl}
                            disabled={disabled}
                        >
                            <IconChevronDown size={16} stroke={1.5} />
                        </ActionIcon>
                    </Menu.Target>
                    <Menu.Dropdown>
                        {showPreview && onPreview && (
                            <Menu.Item
                                leftSection={<IconEye size={16} stroke={1.5} color={theme.colors.blue[5]} />}
                                onClick={onPreview}
                            >
                                Preview
                            </Menu.Item>
                        )}
                        {canShowSubmitForReview && (
                            <Menu.Item
                                leftSection={<IconSend size={16} stroke={1.5} color={theme.colors.blue[5]} />}
                                onClick={handleSubmitForReviewClick}
                            >
                                Submit for Review
                            </Menu.Item>
                        )}
                    </Menu.Dropdown>
                </Menu>
            </Group>

            {/* Submit for Review Modal */}
            {canShowSubmitForReview && (
                <SubmitForReviewModal
                    opened={submitForReviewModalOpened}
                    onClose={() => setSubmitForReviewModalOpened(false)}
                    reportType={reportType!}
                    reportPeriod={reportPeriod!}
                    onSuccess={handleSubmitForReviewSuccess}
                />
            )}
        </>
    );
}
