"use client";

import { Program } from "@/lib/info";
import { Flex, Image, Text, Title } from "@mantine/core";
import { animationControls, motion } from "motion/react";
import Link from "next/link";
import { useMotionPreferences } from "@/components/ConditionalMotion/ConditionalMotion";

interface ProgramTitleCenterProps {
    classes: { readonly [key: string]: string };
    logoControls: ReturnType<typeof animationControls>;
}

/**
 * A component that displays the program title and logo centered on the page.
 * @param {ProgramTitleCenterProps} props - The properties for the component.
 * @return {React.ReactElement} The rendered component.
 */
export function ProgramTitleCenter({ classes, logoControls }: ProgramTitleCenterProps): React.ReactElement {
    const { disableAnimations } = useMotionPreferences();

    return (
        <div>
            <Title ta="center" className={classes.title}>
                <Flex mih={50} justify="center" align="center" direction="row" wrap="wrap">
                    {disableAnimations ? (
                        <Image
                            src="/assets/logos/BENTO.svg"
                            alt="BENTO Logo"
                            radius="md"
                            h={70}
                            w="auto"
                            fit="contain"
                            style={{ marginRight: "10px" }}
                        />
                    ) : (
                        <Image
                            src="/assets/logos/BENTO.svg"
                            alt="BENTO Logo"
                            radius="md"
                            h={70}
                            w="auto"
                            fit="contain"
                            style={{ marginRight: "10px" }}
                            component={motion.img}
                            whileTap={{ scale: 0.95 }}
                            drag
                            dragElastic={{ top: 0.25, left: 0.25, right: 0, bottom: 0 }}
                            dragConstraints={{ top: 0, left: 0, right: 0, bottom: 0 }}
                            animate={logoControls}
                        />
                    )}
                    <Link href="/" style={{ textDecoration: "none", color: "inherit" }}>
                        {Program.name}
                    </Link>
                </Flex>
            </Title>
            <Text c="dimmed" size="sm" ta="center" mt={5}>
                {Program.description}
            </Text>
        </div>
    );
}
