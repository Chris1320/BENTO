/**
 * Mobile-optimized progress components that conditionally render simple or animated versions
 */

import { useMotionPreferences } from "@/components/ConditionalMotion/ConditionalMotion";
import { RingProgress, Progress, Box, Text, Center, SemiCircleProgress } from "@mantine/core";
import { ReactNode } from "react";

interface OptimizedRingProgressProps {
    size?: number;
    thickness?: number;
    sections: Array<{
        value: number;
        color: string;
        tooltip?: string;
    }>;
    label?: ReactNode;
    rootColor?: string;
    [key: string]: unknown;
}

/**
 * Ring progress that falls back to a simple horizontal progress bar on mobile
 */
export const OptimizedRingProgress: React.FC<OptimizedRingProgressProps> = ({
    size = 80,
    thickness = 8,
    sections,
    label,
    rootColor,
    ...props
}) => {
    const { disableAnimations } = useMotionPreferences();

    if (disableAnimations) {
        // Simple horizontal progress bar for mobile
        const totalValue = sections.reduce((sum, section) => sum + section.value, 0);
        const primarySection = sections[0];

        return (
            <Box>
                <Progress value={totalValue} color={primarySection?.color || "blue"} size="lg" radius="md" {...props} />
                {label && (
                    <Center mt="xs">
                        <Text size="sm">{label}</Text>
                    </Center>
                )}
            </Box>
        );
    }

    // Full ring progress for desktop
    return (
        <RingProgress
            size={size}
            thickness={thickness}
            sections={sections}
            label={label}
            rootColor={rootColor}
            {...props}
        />
    );
};

interface OptimizedSemiCircleProgressProps {
    value: number;
    size?: number;
    thickness?: number;
    color?: string;
    label?: ReactNode;
    [key: string]: unknown;
}

/**
 * Semi-circle progress that falls back to horizontal progress on mobile
 */
export const OptimizedSemiCircleProgress: React.FC<OptimizedSemiCircleProgressProps> = ({
    value,
    size = 200,
    thickness = 12,
    color = "blue",
    label,
    ...props
}) => {
    const { disableAnimations } = useMotionPreferences();

    if (disableAnimations) {
        // Simple horizontal progress bar for mobile
        return (
            <Box>
                <Progress value={value} color={color} size="lg" radius="md" {...props} />
                {label && (
                    <Center mt="xs">
                        <Text size="sm">{label}</Text>
                    </Center>
                )}
            </Box>
        );
    }

    // Return the full SemiCircleProgress for desktop
    return (
        <SemiCircleProgress value={value} size={size} thickness={thickness} color={color} label={label} {...props} />
    );
};
