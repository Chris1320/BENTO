"use client";

import { getAllUsersEndpointV1UsersAllGet, School, UserPublic } from "@/lib/api/csclient";
import { customLogger } from "@/lib/api/customLogger";
import { CreateSchool } from "@/lib/api/school";
import { Button, Modal, Stack, TextInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useDisclosure } from "@mantine/hooks";
import { notifications } from "@mantine/notifications";
import { IconBuildingPlus, IconCheck, IconSendOff, IconUserExclamation } from "@tabler/icons-react";
import { useCallback, useEffect, useState } from "react";

interface CreateSchoolComponentProps {
    modalOpen: boolean;
    setModalOpen: (open: boolean) => void;
    onSchoolCreate?: (newSchool: School) => void;
}

export function CreateSchoolComponent({ modalOpen, setModalOpen, onSchoolCreate }: CreateSchoolComponentProps) {
    const [buttonLoading, buttonStateHandler] = useDisclosure(false);
    const [users, setUsers] = useState<UserPublic[]>([]);
    const [loadingUsers, setLoadingUsers] = useState(false);

    const form = useForm({
        initialValues: {
            schoolName: "",
            address: "",
            phone: "",
            email: "",
            website: "",
            assignedNotedBy: "",
        },
        validate: {
            schoolName: (value) => (!value ? "School name is required" : null),
        },
    });

    const loadUsers = useCallback(async () => {
        setLoadingUsers(true);
        try {
            const result = await getAllUsersEndpointV1UsersAllGet({
                query: { show_all: false, limit: 999 },
            });
            if (result.data) {
                // Filter to only show principals (roleId: 4) who can approve reports
                const principals = result.data.filter((user) => user.roleId === 4);
                setUsers(principals);
            } else {
                setUsers([]);
            }
        } catch (error) {
            customLogger.error("Failed to load users:", error);
            setUsers([]);
        } finally {
            setLoadingUsers(false);
        }
    }, []);

    // Load users when modal opens
    useEffect(() => {
        if (modalOpen) {
            loadUsers();
        }
    }, [modalOpen, loadUsers]);

    const handleCreateSchool = useCallback(
        async (values: typeof form.values) => {
            buttonStateHandler.open();
            try {
                const createdSchool = await CreateSchool({
                    name: values.schoolName,
                    address: values.address !== "" ? values.address : null,
                    phone: values.phone !== "" ? values.phone : null,
                    email: values.email !== "" ? values.email : null,
                    website: values.website !== "" ? values.website : null,
                    assignedNotedBy: values.assignedNotedBy !== "" ? values.assignedNotedBy : null,
                });
                notifications.show({
                    id: "create-school-success",
                    title: "Success",
                    message: "School created successfully.",
                    color: "green",
                    icon: <IconCheck />,
                });
                setModalOpen(false);
                form.reset();
                if (onSchoolCreate) onSchoolCreate(createdSchool);
            } catch (error) {
                customLogger.error("Failed to create school:", error);
                if (error instanceof Error && error.message.includes("already exists")) {
                    notifications.show({
                        id: "create-school-exists",
                        title: "Error",
                        message: "A school with this name already exists.",
                        color: "orange",
                        icon: <IconUserExclamation />,
                    });
                } else if (error instanceof Error) {
                    notifications.show({
                        id: "create-school-error",
                        title: "Error",
                        message: error.message,
                        color: "red",
                        icon: <IconSendOff />,
                    });
                } else {
                    customLogger.error("Unexpected error:", error);
                    notifications.show({
                        id: "create-school-unexpected-error",
                        title: "Error",
                        message: "An unexpected error occurred while creating the school.",
                        color: "red",
                        icon: <IconSendOff />,
                    });
                }
            } finally {
                buttonStateHandler.close();
            }
        },
        [buttonStateHandler, form, setModalOpen, onSchoolCreate]
    );

    return (
        <Modal opened={modalOpen} onClose={() => setModalOpen(false)} title="Add New School">
            <form onSubmit={form.onSubmit(handleCreateSchool)}>
                <Stack>
                    <TextInput withAsterisk label="School Name" {...form.getInputProps("schoolName")} />
                    <TextInput label="Address" {...form.getInputProps("address")} />
                    <TextInput label="Phone Number" {...form.getInputProps("phone")} />
                    <TextInput label="Email Address" type="email" {...form.getInputProps("email")} />
                    <TextInput label="Website" {...form.getInputProps("website")} />
                    <Button type="submit" loading={buttonLoading} rightSection={<IconBuildingPlus />}>
                        Create School
                    </Button>
                </Stack>
            </form>
        </Modal>
    );
}
