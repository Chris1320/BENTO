import argparse
import asyncio
import datetime as dt
import getpass
import sys
from collections import defaultdict
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from faker import Faker

f = Faker()


@dataclass
class SchoolData:
    name: str
    address: str | None
    phone: str | None
    email: str | None
    website: str | None


@dataclass
class UserData:
    username: str
    role_id: int
    password: str
    email: str | None = None
    name_first: str | None = None
    name_middle: str | None = None
    name_last: str | None = None
    school_id: int | None = None


@dataclass
class DailySalesAndPurchases:
    date: str
    sales: float
    purchases: float


@dataclass
class LiquidationEntry:
    category: str  # operating_expenses, administrative_expenses, school_operations_fund, supplementary_feeding_fund
    date: str
    description: str
    quantity: float | None = None
    unit: str | None = None
    unit_price: float | None = None
    amount: float | None = None  # For categories without quantity/unit


@dataclass
class PayrollEntry:
    week_number: int
    employee_name: str
    sun: float
    mon: float
    tue: float
    wed: float
    thu: float
    fri: float
    sat: float


DAILY_SALES_AND_PURCHASES: list[DailySalesAndPurchases] = [
    DailySalesAndPurchases(date="2025-01-06", sales=6104.00, purchases=4816.75),
    DailySalesAndPurchases(date="2025-01-07", sales=7283.00, purchases=5639.25),
    DailySalesAndPurchases(date="2025-01-08", sales=8255.00, purchases=6505.00),
    DailySalesAndPurchases(date="2025-01-09", sales=8120.00, purchases=6241.00),
    DailySalesAndPurchases(date="2025-01-10", sales=8700.00, purchases=6710.50),
    DailySalesAndPurchases(date="2025-01-13", sales=7099.00, purchases=5446.25),
    DailySalesAndPurchases(date="2025-01-14", sales=6280.00, purchases=5077.00),
    DailySalesAndPurchases(date="2025-01-15", sales=8396.00, purchases=6445.50),
    DailySalesAndPurchases(date="2025-01-16", sales=7875.00, purchases=6113.75),
    DailySalesAndPurchases(date="2025-01-17", sales=7861.00, purchases=6137.25),
    DailySalesAndPurchases(date="2025-01-20", sales=6883.00, purchases=5465.25),
    DailySalesAndPurchases(date="2025-01-21", sales=5994.00, purchases=4423.00),
    DailySalesAndPurchases(date="2025-01-22", sales=6613.00, purchases=5041.50),
    DailySalesAndPurchases(date="2025-01-24", sales=6310.00, purchases=4844.50),
    DailySalesAndPurchases(date="2025-01-27", sales=5190.00, purchases=4122.00),
    DailySalesAndPurchases(date="2025-01-28", sales=5370.00, purchases=4110.00),
    DailySalesAndPurchases(date="2025-01-30", sales=5170.00, purchases=4018.00),
    DailySalesAndPurchases(date="2025-01-31", sales=5358.00, purchases=4302.50),
]


LIQUIDATION_ENTRIES: list[LiquidationEntry] = [
    # Operating Expenses - from actual liquidation report for January 2025
    LiquidationEntry(
        category="operating_expenses",
        date="2025-01-31",
        description="LPG",
        quantity=2.0,
        unit="pcs",
        unit_price=830.00,
    ),
    LiquidationEntry(
        category="operating_expenses",
        date="2025-01-31",
        description="Rice",
        quantity=50.0,
        unit="kgs",
        unit_price=60.20,
    ),
    LiquidationEntry(
        category="operating_expenses",
        date="2025-01-31",
        description="Water",
        quantity=30.0,
        unit="gallons",
        unit_price=25.00,
    ),
    LiquidationEntry(
        category="operating_expenses",
        date="2025-01-31",
        description="Cleaning materials",
        quantity=1.0,
        unit="pcs",
        unit_price=528.00,
    ),
    # Administrative Expenses - from actual liquidation report for January 2025
    LiquidationEntry(
        category="administrative_expenses",
        date="2025-01-31",
        description="UTILITY",
        quantity=1.0,
        unit="pcs",
        unit_price=1000.00,
    ),
    # Supplementary Feeding Fund - from actual liquidation report for January 2025
    LiquidationEntry(
        category="supplementary_feeding_fund",
        date="2025-01-08",
        description="lugaw",
        quantity=1.0,
        unit="pcs",
        unit_price=214.00,
    ),
    LiquidationEntry(
        category="supplementary_feeding_fund",
        date="2025-01-15",
        description="Sopas",
        quantity=1.0,
        unit="pcs",
        unit_price=215.00,
    ),
    LiquidationEntry(
        category="supplementary_feeding_fund",
        date="2025-01-22",
        description="Champorado",
        quantity=1.0,
        unit="pcs",
        unit_price=214.00,
    ),
    LiquidationEntry(
        category="supplementary_feeding_fund",
        date="2025-01-29",
        description="Palabok",
        quantity=1.0,
        unit="pcs",
        unit_price=215.00,
    ),
    # School Operation Fund - from actual liquidation report for January 2025
    LiquidationEntry(
        category="school_operations_fund",
        date="2025-01-07",
        description="Gasoline (for grass cutter)",
        quantity=1.0,
        unit="pcs",
        unit_price=613.50,
    ),
]


PAYROLL_ENTRIES: list[PayrollEntry] = [
    # Week 1 (Jan 6-10) - from actual payroll report
    PayrollEntry(
        week_number=1,
        employee_name="Geraldine Balasta",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    PayrollEntry(
        week_number=1,
        employee_name="Jomala Saavedra",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    # Week 2 (Jan 13-17) - from actual payroll report
    PayrollEntry(
        week_number=2,
        employee_name="Geraldine Balasta",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    PayrollEntry(
        week_number=2,
        employee_name="Jomala Saavedra",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    # Week 3 (Jan 20-24) - from actual payroll report
    PayrollEntry(
        week_number=3,
        employee_name="Geraldine Balasta",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    PayrollEntry(
        week_number=3,
        employee_name="Jomala Saavedra",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    # Week 4 (Jan 27-31) - from actual payroll report
    PayrollEntry(
        week_number=4,
        employee_name="Geraldine Balasta",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    PayrollEntry(
        week_number=4,
        employee_name="Jomala Saavedra",
        sun=0.00,
        mon=500.00,
        tue=500.00,
        wed=500.00,
        thu=500.00,
        fri=500.00,
        sat=0.00,
    ),
    PayrollEntry(
        week_number=4,
        employee_name="Juancho C. Santos",
        sun=0.00,
        mon=1000.00,
        tue=0.00,
        wed=0.00,
        thu=0.00,
        fri=0.00,
        sat=0.00,
    ),
]


def get_token(
    username: str, password: str, required_role: int, endpoint: str
) -> str | None:
    self_info_endpoint = urljoin(endpoint, "v1/users/me")

    auth_response = httpx.post(
        urljoin(endpoint, "v1/auth/login"),
        data={"username": username, "password": password},
    )

    if auth_response.status_code != 200:
        print(f"Error: {auth_response.status_code} - {auth_response.text}")
        return None

    self_info_response = httpx.get(
        self_info_endpoint,
        headers={"Authorization": f"Bearer {auth_response.json()['access_token']}"},
    )
    if self_info_response.status_code != 200:
        print(
            f"Error fetching user info: {self_info_response.status_code} - {self_info_response.text}"
        )
        return None
    user_info = self_info_response.json()[0]
    if user_info.get("roleId") != required_role:
        print("User does not have the required role.")
        return None

    return auth_response.json().get("access_token")


async def upload_daily_sales_data(
    client: httpx.AsyncClient, endpoint: str, headers: dict[str, str], school_id: int
) -> None:
    """Upload daily sales and purchases data."""
    print("\n📊 Uploading daily sales and purchases data...")

    # Group data by month for processing
    monthly_data: dict[tuple[int, int], list[dict[str, int | float]]] = defaultdict(
        list
    )

    for entry in DAILY_SALES_AND_PURCHASES:
        # Parse the date
        date_obj = dt.datetime.strptime(entry.date, "%Y-%m-%d").date()
        month_key = (date_obj.year, date_obj.month)

        # Convert to the required format for the API
        daily_entry: dict[str, int | float] = {
            "day": date_obj.day,
            "sales": entry.sales,
            "purchases": entry.purchases,
            "schoolId": school_id,
        }
        monthly_data[month_key].append(daily_entry)

    # Process each month
    for (year, month), entries in monthly_data.items():
        print(f"   Processing {year}-{month:02d} with {len(entries)} entries...")

        # Upload the daily entries using bulk endpoint
        # The bulk endpoint will automatically create monthly and daily reports if they don't exist
        bulk_entries_url = urljoin(
            endpoint, f"v1/reports/daily/{school_id}/{year}/{month}/entries/bulk"
        )
        bulk_response = await client.post(
            bulk_entries_url, json=entries, headers=headers
        )

        if bulk_response.status_code in [200, 201]:
            print(
                f"   ✅ Successfully uploaded {len(entries)} entries for {year}-{month:02d}"
            )
        elif (
            bulk_response.status_code == 409 and "already exists" in bulk_response.text
        ):
            print(f"   ⚠️  Entries already exist for {year}-{month:02d}, skipping...")
        else:
            print(
                f"   ❌ Failed to upload entries for {year}-{month:02d}: {bulk_response.status_code} - {bulk_response.text}"
            )


async def upload_liquidation_data(
    client: httpx.AsyncClient,
    endpoint: str,
    headers: dict[str, str],
    school_id: int,
    user_id: str,
) -> None:
    """Upload liquidation report data."""
    print("\n💰 Uploading liquidation report data...")

    # Group data by month and category
    import datetime as dt
    from collections import defaultdict

    monthly_data: dict[tuple[int, int], dict[str, list[dict[str, str | float]]]] = (
        defaultdict(lambda: defaultdict(list))
    )

    for entry in LIQUIDATION_ENTRIES:
        # Parse the date
        date_obj = dt.datetime.strptime(entry.date, "%Y-%m-%d").date()
        month_key = (date_obj.year, date_obj.month)

        # Convert to the required format for the API
        liquidation_entry: dict[str, str | float] = {
            "date": entry.date,
            "particulars": entry.description,
        }

        # All liquidation entries require quantity, unit, and unitPrice
        if (
            entry.quantity is not None
            and entry.unit is not None
            and entry.unit_price is not None
        ):
            liquidation_entry["quantity"] = entry.quantity
            liquidation_entry["unit"] = entry.unit
            liquidation_entry["unitPrice"] = entry.unit_price
        else:
            # This should not happen with the corrected data structure
            print(f"Warning: Missing quantity/unit/unit_price for entry: {entry.description}")
            continue
        
        monthly_data[month_key][entry.category].append(liquidation_entry)

    # Process each month
    for (year, month), categories in monthly_data.items():
        print(f"   Processing liquidation for {year}-{month:02d}...")

        for category, entries in categories.items():
            print(f"      Processing {category} with {len(entries)} entries...")

            # First, create the liquidation report for this category
            create_report_url = urljoin(
                endpoint,
                f"v1/reports/liquidation/{school_id}/{year}/{month}/{category}",
            )

            # Prepare the request body with the entries
            liquidation_request_body = {
                "schoolId": school_id,
                "entries": entries,
                "memo": f"Liquidation report for {category.replace('_', ' ').title()} - {year}-{month:02d}",
                "certifiedBy": [],
                "teacherInCharge": user_id,  # Set to current authenticated user
                "preparedBy": user_id,  # Set to current authenticated user
                "notedBy": None,  # Let API auto-assign school's principal
            }

            create_response = await client.patch(
                create_report_url, json=liquidation_request_body, headers=headers
            )

            if create_response.status_code in [200, 201]:
                print(
                    f"      ✅ Successfully created/updated {category} liquidation report with {len(entries)} entries for {year}-{month:02d}"
                )
            elif create_response.status_code == 409 or (
                create_response.status_code == 500
                and "already exists" in create_response.text.lower()
            ):
                print(
                    f"      ⚠️  Liquidation report for {category} already exists for {year}-{month:02d}"
                )
            else:
                print(
                    f"      ❌ Failed to create liquidation report for {category}: {create_response.status_code} - {create_response.text}"
                )


async def upload_payroll_data(
    client: httpx.AsyncClient, endpoint: str, headers: dict[str, str], school_id: int
) -> None:
    """Upload payroll report data."""
    print("\n👥 Uploading payroll report data...")

    # All payroll entries are for January 2025 based on the data
    year, month = 2025, 1

    print(
        f"   Processing payroll for {year}-{month:02d} with {len(PAYROLL_ENTRIES)} entries..."
    )

    # First, create the payroll report
    create_payroll_url = urljoin(
        endpoint, f"v1/reports/payroll/{school_id}/{year}/{month}"
    )
    # Don't pass noted_by parameter - let API auto-assign school's principal
    create_response = await client.patch(create_payroll_url, headers=headers)

    if create_response.status_code not in [200, 201]:
        # Check if the error is because the report already exists
        if create_response.status_code == 409 or (
            create_response.status_code == 500
            and "already exists" in create_response.text.lower()
        ):
            print(f"   ⚠️  Payroll report already exists for {year}-{month:02d}")
        else:
            print(
                f"   ❌ Failed to create payroll report: {create_response.status_code} - {create_response.text}"
            )
            return

    # Convert payroll entries to the required format for the API
    payroll_api_entries: list[dict[str, int | str | float]] = []
    for entry in PAYROLL_ENTRIES:
        api_entry: dict[str, int | str | float] = {
            "week_number": entry.week_number,
            "employee_name": entry.employee_name,
            "sun": entry.sun,
            "mon": entry.mon,
            "tue": entry.tue,
            "wed": entry.wed,
            "thu": entry.thu,
            "fri": entry.fri,
            "sat": entry.sat,
        }
        payroll_api_entries.append(api_entry)

    # Upload the payroll entries using bulk endpoint
    bulk_entries_url = urljoin(
        endpoint, f"v1/reports/payroll/{school_id}/{year}/{month}/entries/bulk"
    )
    bulk_response = await client.post(
        bulk_entries_url, json=payroll_api_entries, headers=headers
    )

    if bulk_response.status_code in [200, 201]:
        print(
            f"   ✅ Successfully uploaded {len(payroll_api_entries)} payroll entries for {year}-{month:02d}"
        )
    elif bulk_response.status_code == 409 and "already exists" in bulk_response.text:
        print(
            f"   ⚠️  Payroll entries already exist for {year}-{month:02d}, skipping..."
        )
    else:
        print(
            f"   ❌ Failed to upload payroll entries for {year}-{month:02d}: {bulk_response.status_code} - {bulk_response.text}"
        )


async def main(endpoint: str) -> int:
    print("Enter your credentials to obtain an access token.")
    print("Required Role: Canteen Manager")
    print()
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    school_creation_token = get_token(username, password, 5, endpoint)
    if not school_creation_token:
        print("Failed to obtain access token for school creation.")
        return 2

    # Get user information to find their school ID
    headers = {"Authorization": f"Bearer {school_creation_token}"}
    user_info_response = httpx.get(
        urljoin(endpoint, "v1/users/me"),
        headers=headers,
    )

    if user_info_response.status_code != 200:
        print(
            f"Failed to get user info: {user_info_response.status_code} - {user_info_response.text}"
        )
        return 3

    user_info = user_info_response.json()[0]  # API returns tuple of [user, permissions]
    school_id = user_info.get("schoolId")
    user_id = user_info.get("id")  # Extract user ID for required fields

    if not school_id:
        print(
            "User is not assigned to a school. Only canteen managers assigned to schools can upload report data."
        )
        return 4

    if not user_id:
        print("Could not determine user ID from login response.")
        return 5

    print(f"Found user ID: {user_id}")
    print(f"Found user school ID: {school_id}")
    print("🚀 Starting report data upload...")

    async with httpx.AsyncClient() as client:
        # Upload all report types
        await upload_daily_sales_data(client, endpoint, headers, school_id)
        await upload_liquidation_data(client, endpoint, headers, school_id, user_id)
        await upload_payroll_data(client, endpoint, headers, school_id)

    print("\n🎉 All report data upload completed!")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        default="http://localhost:8081/api/",
    )
    args = parser.parse_args()

    sys.exit(asyncio.run(main(args.endpoint)))
