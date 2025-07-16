"use client";

import {
    MonthlyReport,
    ReportStatus,
    getLiquidationReportV1ReportsLiquidationSchoolIdYearMonthCategoryGet,
    getSchoolDailyReportV1ReportsDailySchoolIdYearMonthGet,
    getSchoolPayrollReportV1ReportsPayrollSchoolIdYearMonthGet,
    getDailySalesAndPurchasesSummaryV1ReportsDailySchoolIdYearMonthSummaryGet,
    LiquidationReportResponse,
} from "@/lib/api/csclient";
import { customLogger } from "@/lib/api/customLogger";
import { formatUTCDateOnlyLocalized } from "@/lib/utils/date";
import { ActionIcon, Alert, Badge, Button, Group, Modal, Stack, Table, Text, Title } from "@mantine/core";
import {
    IconAlertCircle,
    IconCalendar,
    IconCash,
    IconExternalLink,
    IconEye,
    IconReceipt,
    IconUsers,
} from "@tabler/icons-react";
import dayjs from "dayjs";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

interface LiquidationReportData {
    reportStatus?: string;
    category?: string;
    [key: string]: unknown;
}

interface FinancialData {
    netSales: number;
    costOfSales: number;
    grossProfit: number;
    operatingExpenses: number;
    administrativeExpenses: number;
    netIncomeFromOperations: number;
    utilizationBreakdown: {
        supplementaryFeeding: { percentage: number; actual: number; balance: number };
        clinicFund: { percentage: number; actual: number; balance: number };
        facultyStudentDev: { percentage: number; actual: number; balance: number };
        heFund: { percentage: number; actual: number; balance: number };
        schoolOperations: { percentage: number; actual: number; balance: number };
        revolvingCapital: { percentage: number; actual: number; balance: number };
    };
}

interface LinkedReport {
    id: string;
    name: string;
    type: "daily" | "payroll" | "liquidation";
    category?: string;
    status: ReportStatus | "not-created";
    icon: React.ElementType;
    route: string;
}

interface MonthlyReportDetailsModalProps {
    opened: boolean;
    onClose: () => void;
    report: MonthlyReport | null;
    onDelete?: (reportId: string) => void;
}

const liquidationCategories = [
    { key: "operating_expenses", name: "Operating Expenses" },
    { key: "administrative_expenses", name: "Administrative Expenses" },
    { key: "clinic_fund", name: "Clinic Fund" },
    { key: "supplementary_feeding_fund", name: "Supplementary Feeding Fund" },
    { key: "he_fund", name: "HE Fund" },
    { key: "faculty_stud_dev_fund", name: "Faculty & Student Development Fund" },
    { key: "school_operations_fund", name: "School Operations Fund" },
    { key: "revolving_fund", name: "Revolving Fund" },
];

export function MonthlyReportDetailsModal({ opened, onClose, report, onDelete }: MonthlyReportDetailsModalProps) {
    const router = useRouter();
    const [linkedReports, setLinkedReports] = useState<LinkedReport[]>([]);
    const [loading, setLoading] = useState(false);
    const [financialData, setFinancialData] = useState<FinancialData | null>(null);
    const [financialLoading, setFinancialLoading] = useState(false);

    const getStatusColor = (status: ReportStatus | "not-created") => {
        switch (status) {
            case "approved":
                return "green";
            case "draft":
                return "blue";
            case "review":
                return "yellow";
            case "rejected":
                return "red";
            case "archived":
                return "gray";
            case "not-created":
                return "gray";
            default:
                return "gray";
        }
    };

    const formatReportPeriod = (reportId: string) => {
        return dayjs(reportId).format("MMMM YYYY");
    };

    const formatCurrency = (amount: number) => {
        return `₱${amount.toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
        })}`;
    };

    const fetchLinkedReports = useCallback(async () => {
        if (!report) return;

        setLoading(true);
        const reports: LinkedReport[] = [];

        try {
            const year = dayjs(report.id).format("YYYY");
            const month = dayjs(report.id).format("MM");

            // Always add Daily Financial Report entry
            try {
                const { data: dailyReport } = await getSchoolDailyReportV1ReportsDailySchoolIdYearMonthGet({
                    path: {
                        school_id: report.submittedBySchool,
                        year: parseInt(year),
                        month: parseInt(month),
                    },
                });

                reports.push({
                    id: `daily-${year}-${month}`,
                    name: `Daily Sales & Purchases Report - ${formatReportPeriod(report.id)}`,
                    type: "daily",
                    status: dailyReport?.reportStatus || "not-created",
                    icon: IconCash,
                    route: `/reports/sales`,
                });
            } catch (error) {
                customLogger.warn("Daily report not found or error fetching:", error);
                // Add as not created
                reports.push({
                    id: `daily-${year}-${month}`,
                    name: `Daily Sales & Purchases Report - ${formatReportPeriod(report.id)}`,
                    type: "daily",
                    status: "not-created",
                    icon: IconCash,
                    route: `/reports/sales`,
                });
            }

            // Always add Payroll Report entry
            try {
                const { data: payrollReport } = await getSchoolPayrollReportV1ReportsPayrollSchoolIdYearMonthGet({
                    path: {
                        school_id: report.submittedBySchool,
                        year: parseInt(year),
                        month: parseInt(month),
                    },
                });

                reports.push({
                    id: `payroll-${year}-${month}`,
                    name: `Payroll Report - ${formatReportPeriod(report.id)}`,
                    type: "payroll",
                    status: payrollReport?.reportStatus || "not-created",
                    icon: IconUsers,
                    route: `/reports/payroll`,
                });
            } catch (error) {
                customLogger.warn("Payroll report not found or error fetching:", error);
                // Add as not created
                reports.push({
                    id: `payroll-${year}-${month}`,
                    name: `Payroll Report - ${formatReportPeriod(report.id)}`,
                    type: "payroll",
                    status: "not-created",
                    icon: IconUsers,
                    route: `/reports/payroll`,
                });
            }

            // Always add all Liquidation Report categories
            for (const category of liquidationCategories) {
                try {
                    const { data: liquidationReport } =
                        await getLiquidationReportV1ReportsLiquidationSchoolIdYearMonthCategoryGet({
                            path: {
                                school_id: report.submittedBySchool,
                                year: parseInt(year),
                                month: parseInt(month),
                                category: category.key,
                            },
                        });

                    // Check if the report actually exists (has data)
                    if (liquidationReport && Object.keys(liquidationReport).length > 0) {
                        const reportStatus =
                            ((liquidationReport as LiquidationReportData)?.reportStatus as ReportStatus) ||
                            "not-created";
                        reports.push({
                            id: `liquidation-${category.key}-${year}-${month}`,
                            name: `${category.name} Liquidation Report - ${formatReportPeriod(report.id)}`,
                            type: "liquidation",
                            category: category.key,
                            status: reportStatus,
                            icon: IconReceipt,
                            route: `/reports/liquidation-report?category=${category.key}`,
                        });
                    } else {
                        // API succeeded but returned empty/null data - report doesn't exist
                        reports.push({
                            id: `liquidation-${category.key}-${year}-${month}`,
                            name: `${category.name} Liquidation Report - ${formatReportPeriod(report.id)}`,
                            type: "liquidation",
                            category: category.key,
                            status: "not-created",
                            icon: IconReceipt,
                            route: `/reports/liquidation-report?category=${category.key}`,
                        });
                    }
                } catch (error) {
                    // If we get a 404 or any error, the report doesn't exist
                    customLogger.warn(`Liquidation report for ${category.key} not found or error fetching:`, error);
                    reports.push({
                        id: `liquidation-${category.key}-${year}-${month}`,
                        name: `${category.name} Liquidation Report - ${formatReportPeriod(report.id)}`,
                        type: "liquidation",
                        category: category.key,
                        status: "not-created",
                        icon: IconReceipt,
                        route: `/reports/liquidation-report?category=${category.key}`,
                    });
                }
            }

            setLinkedReports(reports);
        } catch (error) {
            customLogger.error("Error fetching linked reports:", error);
        } finally {
            setLoading(false);
        }
    }, [report]);

    const fetchFinancialData = useCallback(async () => {
        if (!report) return;

        setFinancialLoading(true);
        try {
            const year = parseInt(dayjs(report.id).format("YYYY"));
            const month = parseInt(dayjs(report.id).format("MM"));

            // Fetch daily sales summary
            let dailySummary: {
                [key: string]:
                    | number
                    | number
                    | {
                          [key: string]: number | number;
                      }
                    | null;
            } | null = null;
            try {
                const { data } = await getDailySalesAndPurchasesSummaryV1ReportsDailySchoolIdYearMonthSummaryGet({
                    path: {
                        school_id: report.submittedBySchool,
                        year,
                        month,
                    },
                });
                if (data) {
                    dailySummary = data;
                }
            } catch (error) {
                customLogger.warn("Failed to fetch daily sales summary:", error);
            }

            // Fetch liquidation reports for expenses
            const liquidationReports: { [key: string]: LiquidationReportResponse } = {};
            for (const category of liquidationCategories) {
                try {
                    const { data } = await getLiquidationReportV1ReportsLiquidationSchoolIdYearMonthCategoryGet({
                        path: {
                            school_id: report.submittedBySchool,
                            year,
                            month,
                            category: category.key,
                        },
                    });
                    if (data) {
                        liquidationReports[category.key] = data;
                    }
                } catch (error) {
                    customLogger.warn(`Failed to fetch liquidation report for ${category.key}:`, error);
                }
            }

            // Calculate financial data
            const netSales = typeof dailySummary?.total_sales === "number" ? dailySummary.total_sales : 0;
            const costOfSales = typeof dailySummary?.total_purchases === "number" ? dailySummary.total_purchases : 0;
            const grossProfit = netSales - costOfSales;

            const operatingExpenses = liquidationReports.operating_expenses?.totalAmount || 0;
            const administrativeExpenses = liquidationReports.administrative_expenses?.totalAmount || 0;
            const netIncomeFromOperations = grossProfit - operatingExpenses - administrativeExpenses;

            // Calculate utilization breakdown
            const utilizationBreakdown = {
                supplementaryFeeding: {
                    percentage: 30,
                    actual: liquidationReports.supplementary_feeding_fund?.totalAmount || 0,
                    balance:
                        netIncomeFromOperations * 0.3 -
                        (liquidationReports.supplementary_feeding_fund?.totalAmount || 0),
                },
                clinicFund: {
                    percentage: 5,
                    actual: liquidationReports.clinic_fund?.totalAmount || 0,
                    balance: netIncomeFromOperations * 0.05 - (liquidationReports.clinic_fund?.totalAmount || 0),
                },
                facultyStudentDev: {
                    percentage: 15,
                    actual: liquidationReports.faculty_stud_dev_fund?.totalAmount || 0,
                    balance:
                        netIncomeFromOperations * 0.15 - (liquidationReports.faculty_stud_dev_fund?.totalAmount || 0),
                },
                heFund: {
                    percentage: 10,
                    actual: liquidationReports.he_fund?.totalAmount || 0,
                    balance: netIncomeFromOperations * 0.1 - (liquidationReports.he_fund?.totalAmount || 0),
                },
                schoolOperations: {
                    percentage: 25,
                    actual: liquidationReports.school_operations_fund?.totalAmount || 0,
                    balance:
                        netIncomeFromOperations * 0.25 - (liquidationReports.school_operations_fund?.totalAmount || 0),
                },
                revolvingCapital: {
                    percentage: 15,
                    actual: liquidationReports.revolving_fund?.totalAmount || 0,
                    balance: netIncomeFromOperations * 0.15 - (liquidationReports.revolving_fund?.totalAmount || 0),
                },
            };

            setFinancialData({
                netSales,
                costOfSales,
                grossProfit,
                operatingExpenses,
                administrativeExpenses,
                netIncomeFromOperations,
                utilizationBreakdown,
            });
        } catch (error) {
            customLogger.error("Error fetching financial data:", error);
        } finally {
            setFinancialLoading(false);
        }
    }, [report]);

    useEffect(() => {
        if (opened && report) {
            fetchLinkedReports();
            fetchFinancialData();
        }
    }, [opened, report, fetchLinkedReports, fetchFinancialData]);

    const handleOpenReport = (reportRoute: string) => {
        router.push(reportRoute);
        onClose();
    };

    const handleDeleteReport = async () => {
        if (report && onDelete) {
            await onDelete(report.id);
            onClose();
        }
    };

    if (!report) return null;

    return (
        <Modal
            opened={opened}
            onClose={onClose}
            title={
                <Group>
                    <IconCalendar size={20} />
                    <Title order={3}>{report.name}</Title>
                </Group>
            }
            size="xl"
            padding="lg"
        >
            <Stack gap="lg">
                {/* Report Information */}
                <div>
                    <Group gap="md" mb="sm">
                        <Badge color={getStatusColor(report.reportStatus || "draft")} variant="filled">
                            {report.reportStatus || "Draft"}
                        </Badge>
                        <Text size="sm" c="dimmed">
                            Period: {formatReportPeriod(report.id)}
                        </Text>
                    </Group>

                    <Group gap="md">
                        <Text size="sm">
                            <strong>Last Modified:</strong>{" "}
                            {formatUTCDateOnlyLocalized(report.lastModified, "en-US", {
                                month: "long",
                                day: "numeric",
                                year: "numeric",
                            })}
                        </Text>
                        {report.dateApproved && (
                            <Text size="sm">
                                <strong>Date Approved:</strong>{" "}
                                {formatUTCDateOnlyLocalized(report.dateApproved, "en-US", {
                                    month: "long",
                                    day: "numeric",
                                    year: "numeric",
                                })}
                            </Text>
                        )}
                    </Group>
                </div>

                <div>
                    <Title order={4} mb="md">
                        Statement of Receipts, Disbursements and Utilization of Income
                    </Title>
                    <Table highlightOnHover>
                        <Table.Tbody>
                            {/* Sales Section */}
                            <Table.Tr>
                                <Table.Td>
                                    <Text size="sm" fw={600}>
                                        Net Sales
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.netSales)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>

                            {/* Cost of Sales Section */}
                            <Table.Tr>
                                <Table.Td>
                                    <Text size="sm" fw={600}>
                                        Cost of Sales
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.costOfSales)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>

                            {/* Gross Profit */}
                            <Table.Tr style={{ backgroundColor: "#f8f9fa" }}>
                                <Table.Td>
                                    <Text size="sm" fw={700}>
                                        GROSS PROFIT
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={700} c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.grossProfit)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>

                            {/* Expenses Section */}
                            <Table.Tr>
                                <Table.Td>
                                    <Text size="sm" fw={600}>
                                        EXPENSES
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.operatingExpenses + financialData.administrativeExpenses
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">Operating Costs</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.operatingExpenses)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">Administrative Costs</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.administrativeExpenses)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>

                            {/* Net Income From Operations */}
                            <Table.Tr style={{ backgroundColor: "#f8f9fa" }}>
                                <Table.Td>
                                    <Text size="sm" fw={700}>
                                        NET INCOME FROM OPERATIONS
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={700} c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.netIncomeFromOperations)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>

                            {/* Utilization of Net Income Section */}
                            <Table.Tr>
                                <Table.Td>
                                    <Text size="sm" fw={600} pt="md">
                                        UTILIZATION OF NET INCOME
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={600} pt="md">
                                        Percentage
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={600} pt="md">
                                        Actual
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={600} pt="md">
                                        Balance/Output
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">Supplementary Feeding Program</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        30%
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.supplementaryFeeding.actual
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.supplementaryFeeding.balance
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">Clinic Fund</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        5%
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.utilizationBreakdown.clinicFund.actual)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.utilizationBreakdown.clinicFund.balance)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">Faculty and Student Development Fund</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        15%
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.facultyStudentDev.actual
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.facultyStudentDev.balance
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">HE Instructional Fund</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        10%
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.utilizationBreakdown.heFund.actual)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.utilizationBreakdown.heFund.balance)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">Schools Operations Fund</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        25%
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.utilizationBreakdown.schoolOperations.actual)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.schoolOperations.balance
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr>
                                <Table.Td pl="md">
                                    <Text size="sm">Revolving Capital</Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        15%
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(financialData.utilizationBreakdown.revolvingCapital.actual)
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.revolvingCapital.balance
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                            <Table.Tr style={{ backgroundColor: "#f8f9fa" }}>
                                <Table.Td>
                                    <Text size="sm" fw={700}>
                                        UTILIZATION OF NET INCOME
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={700}>
                                        100%
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={700} c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.supplementaryFeeding.actual +
                                                      financialData.utilizationBreakdown.clinicFund.actual +
                                                      financialData.utilizationBreakdown.facultyStudentDev.actual +
                                                      financialData.utilizationBreakdown.heFund.actual +
                                                      financialData.utilizationBreakdown.schoolOperations.actual +
                                                      financialData.utilizationBreakdown.revolvingCapital.actual
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                                <Table.Td>
                                    <Text size="sm" fw={700} c="dimmed">
                                        {financialLoading
                                            ? "Loading..."
                                            : financialData
                                            ? formatCurrency(
                                                  financialData.utilizationBreakdown.supplementaryFeeding.balance +
                                                      financialData.utilizationBreakdown.clinicFund.balance +
                                                      financialData.utilizationBreakdown.facultyStudentDev.balance +
                                                      financialData.utilizationBreakdown.heFund.balance +
                                                      financialData.utilizationBreakdown.schoolOperations.balance +
                                                      financialData.utilizationBreakdown.revolvingCapital.balance
                                              )
                                            : "₱0.00"}
                                    </Text>
                                </Table.Td>
                            </Table.Tr>
                        </Table.Tbody>
                    </Table>
                </div>

                {/* Linked Reports Section */}
                <div>
                    <Title order={4} mb="md">
                        Related Reports
                    </Title>

                    {loading ? (
                        <Text size="sm" c="dimmed">
                            Loading related reports...
                        </Text>
                    ) : linkedReports.length > 0 ? (
                        <Table highlightOnHover>
                            <Table.Thead>
                                <Table.Tr>
                                    <Table.Th>Report Name</Table.Th>
                                    <Table.Th>Type</Table.Th>
                                    <Table.Th>Status</Table.Th>
                                    {/* <Table.Th>Signatures</Table.Th> */}
                                    <Table.Th>Actions</Table.Th>
                                </Table.Tr>
                            </Table.Thead>
                            <Table.Tbody>
                                {linkedReports.map((linkedReport) => {
                                    const Icon = linkedReport.icon;
                                    return (
                                        <Table.Tr key={linkedReport.id}>
                                            <Table.Td>
                                                <Group gap="sm">
                                                    <Icon size={16} />
                                                    <Text size="sm">{linkedReport.name}</Text>
                                                </Group>
                                            </Table.Td>
                                            <Table.Td>
                                                <Text size="sm" tt="capitalize">
                                                    {linkedReport.type}
                                                </Text>
                                            </Table.Td>
                                            <Table.Td>
                                                <Badge
                                                    color={getStatusColor(linkedReport.status)}
                                                    variant="light"
                                                    size="sm"
                                                >
                                                    {linkedReport.status === "not-created"
                                                        ? "Not Created"
                                                        : linkedReport.status || "Draft"}
                                                </Badge>
                                            </Table.Td>
                                            {/* <Table.Td>
                                                <Text size="sm" c="dimmed">
                                                    {linkedReport.status === "approved" ? "Signed" : "Not Signed"}
                                                </Text>
                                            </Table.Td> */}
                                            <Table.Td>
                                                <ActionIcon
                                                    variant="subtle"
                                                    color={linkedReport.status === "not-created" ? "gray" : "blue"}
                                                    onClick={() => handleOpenReport(linkedReport.route)}
                                                    aria-label={
                                                        linkedReport.status === "not-created"
                                                            ? `Create ${linkedReport.name}`
                                                            : `Open ${linkedReport.name}`
                                                    }
                                                    title={
                                                        linkedReport.status === "not-created"
                                                            ? "Click to create this report"
                                                            : "Click to open this report"
                                                    }
                                                >
                                                    <IconExternalLink size={16} />
                                                </ActionIcon>
                                            </Table.Td>
                                        </Table.Tr>
                                    );
                                })}
                            </Table.Tbody>
                        </Table>
                    ) : (
                        <Alert
                            variant="light"
                            color="blue"
                            icon={<IconAlertCircle size={16} />}
                            title="No Related Reports"
                        >
                            This monthly report doesn&apos;t have any related daily, payroll, or liquidation reports
                            yet.
                        </Alert>
                    )}
                </div>

                {/* Actions */}
                <Group justify="space-between" mt="md">
                    <Group>
                        <Button variant="light">Download Monthly Report</Button>
                    </Group>
                    <Group>
                        {onDelete && (
                            <Button color="red" variant="outline" onClick={handleDeleteReport}>
                                Delete Report
                            </Button>
                        )}
                        <Button variant="default" onClick={onClose}>
                            Close
                        </Button>
                    </Group>
                </Group>
            </Stack>
        </Modal>
    );
}
