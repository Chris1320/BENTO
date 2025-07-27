import argparse
import asyncio
import getpass
import sys
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

    if not school_id:
        print(
            "User is not assigned to a school. Only canteen managers assigned to schools can upload daily sales data."
        )
        return 4

    print(f"Found user school ID: {school_id}")
    print("Uploading daily sales and purchases data...")

    # Group data by month for processing
    from collections import defaultdict
    import datetime as dt

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
    async with httpx.AsyncClient() as client:
        for (year, month), entries in monthly_data.items():
            print(f"Processing {year}-{month:02d} with {len(entries)} entries...")

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
                    f"✅ Successfully uploaded {len(entries)} entries for {year}-{month:02d}"
                )
            elif (
                bulk_response.status_code == 409
                and "already exists" in bulk_response.text
            ):
                print(f"⚠️  Entries already exist for {year}-{month:02d}, skipping...")
            else:
                print(
                    f"❌ Failed to upload entries for {year}-{month:02d}: {bulk_response.status_code} - {bulk_response.text}"
                )

    print("\n✅ Daily sales and purchases data upload completed!")
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
