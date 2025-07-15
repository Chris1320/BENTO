import argparse
import datetime
import asyncio
import random
import sys
from typing import Any
from urllib.parse import urljoin

import httpx
from faker import Faker

DEFAULT_USERNAME = "bento"
DEFAULT_PASSWORD = "ProjectSCARS1"
SI_USERNAME = "mock_superintendent"
SI_PASSWORD = "MockPassword1"
USERS_PASSWORD = "MockPassword1"

f = Faker()


async def get_token(
    username: str, password: str, required_role: int, endpoint: str
) -> str | None:
    self_info_endpoint = urljoin(endpoint, "v1/users/me")

    async with httpx.AsyncClient() as client:
        auth_response = await client.post(
            urljoin(endpoint, "v1/auth/login"),
            data={"username": username, "password": password},
        )

        if auth_response.status_code != 200:
            print(f"Error: {auth_response.status_code} - {auth_response.text}")
            return None

        self_info_response = await client.get(
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


async def simulate_school_history(
    school_id: int,
    days: int,
    endpoint: str,
    token: str,
    canteen_manager_data: list[dict[str, str]],
    principal_data: list[dict[str, str]],
) -> None:
    """Simulate school history by generating random data for the past `days` days."""

    # Get current date and calculate start date
    current_date = datetime.datetime.now()
    start_date = current_date - datetime.timedelta(days=days)

    # Generate data for each month from start_date to current_date
    current_month = start_date.replace(day=1)

    async with httpx.AsyncClient() as client:
        while current_month <= current_date:
            year = current_month.year
            month = current_month.month

            # Choose a random canteen manager for this month's reports
            canteen_manager = random.choice(canteen_manager_data)
            canteen_manager_id = canteen_manager["id"]

            # Get canteen manager token for creating reports
            canteen_manager_token = await get_token(
                canteen_manager["username"],
                canteen_manager["password"],
                5,  # Canteen manager role
                endpoint,
            )
            if not canteen_manager_token:
                print(f"Failed to get token for canteen manager {canteen_manager_id}")
                continue

            canteen_headers = {"Authorization": f"Bearer {canteen_manager_token}"}

            # Determine if this is a current month (should remain draft) or past month (should be approved)
            is_current_month = year == current_date.year and month == current_date.month

            print(
                f"Generating reports for {year}-{month:02d} for school {school_id}..."
            )

            # 1. Create daily sales and purchases reports
            try:
                await create_daily_sales_purchases(
                    client,
                    school_id,
                    year,
                    month,
                    endpoint,
                    canteen_headers,
                    canteen_manager_id,
                )
            except Exception as e:
                print(f"Error creating daily report for {year}-{month:02d}: {e}")
                continue

            # 2. Create liquidation reports for all categories
            liquidation_categories = [
                "operating_expenses",
                "administrative_expenses",
                "supplementary_feeding_fund",
                "clinic_fund",
                "faculty_stud_dev_fund",
                "he_fund",
                "school_operations_fund",
                "revolving_fund",
            ]

            for category in liquidation_categories:
                try:
                    await create_liquidation_report(
                        client,
                        school_id,
                        year,
                        month,
                        category,
                        endpoint,
                        canteen_headers,
                        canteen_manager_id,
                    )
                except Exception as e:
                    print(
                        f"Error creating liquidation report for {category} in {year}-{month:02d}: {e}"
                    )
                    continue

            # 3. Create payroll reports
            try:
                await create_payroll_report(
                    client,
                    school_id,
                    year,
                    month,
                    endpoint,
                    canteen_headers,
                    canteen_manager_id,
                )
            except Exception as e:
                print(f"Error creating payroll report for {year}-{month:02d}: {e}")
                continue

            # 4. Mark the automatically-generated monthly reports as for review
            if not is_current_month:
                mrresp = await client.patch(
                    urljoin(
                        endpoint,
                        f"v1/reports/monthly/{school_id}/{year}/{month}/status",
                    ),
                    headers=canteen_headers,
                    json={
                        "new_status": "review",
                        "comments": "Monthly reports created",
                    },
                )
                if mrresp.status_code not in [200, 201]:
                    print(
                        f"Error marking monthly reports as for review for {year}-{month:02d}: {mrresp.text}"
                    )
                    continue

            # 5. Approve reports if they are from past months
            if not is_current_month:
                # Choose a random principal for approving reports
                principal = random.choice(principal_data)
                principal_token = await get_token(
                    principal["username"],
                    principal["password"],
                    4,  # Principal role
                    endpoint,
                )
                if not principal_token:
                    print(f"Failed to get token for principal {principal['id']}")
                    continue

                principal_headers = {"Authorization": f"Bearer {principal_token}"}

                try:
                    await approve_reports(
                        client,
                        school_id,
                        year,
                        month,
                        endpoint,
                        principal_headers,
                        liquidation_categories,
                    )
                    # approve monthly report as well
                    mrr = await client.patch(
                        urljoin(
                            endpoint,
                            f"v1/reports/monthly/{school_id}/{year}/{month}/status",
                        ),
                        headers=principal_headers,
                        json={
                            "new_status": "approved",
                            "comments": "Approved by principal",
                        },
                    )
                    if mrr.status_code not in [200, 201]:
                        print(
                            f"Error approving monthly reports for {year}-{month:02d}: {mrr.text}"
                        )
                except Exception as e:
                    print(f"Error approving reports for {year}-{month:02d}: {e}")
                    continue

            # Move to next month
            if month == 12:
                current_month = current_month.replace(year=year + 1, month=1)
            else:
                current_month = current_month.replace(month=month + 1)


async def create_daily_sales_purchases(
    client: httpx.AsyncClient,
    school_id: int,
    year: int,
    month: int,
    endpoint: str,
    headers: dict[str, str],
    canteen_manager_id: str,
) -> None:
    """Create daily sales and purchases entries for a month."""

    # First create the daily report
    daily_report_url = urljoin(endpoint, f"v1/reports/daily/{school_id}/{year}/{month}")
    daily_report_response = await client.patch(
        daily_report_url, headers=headers, params={"noted_by": canteen_manager_id}
    )

    if daily_report_response.status_code not in [200, 201]:
        # Check if the error is because the report already exists
        if daily_report_response.status_code == 409 or (
            daily_report_response.status_code == 500
            and "UNIQUE constraint failed" in daily_report_response.text
        ):
            print(f"Daily report already exists for {year}-{month:02d}, skipping...")
            return
        print(
            f"Error creating daily report: {daily_report_response.status_code} - {daily_report_response.text}"
        )
        return

    # Get the number of days in the month
    if month == 12:
        next_month = datetime.datetime(year + 1, 1, 1)
    else:
        next_month = datetime.datetime(year, month + 1, 1)

    last_day = (next_month - datetime.timedelta(days=1)).day

    # Create entries for each day of the month
    entries: list[dict[str, float | int]] = []
    for day in range(1, last_day + 1):
        # Generate random sales and purchases data
        sales = round(random.uniform(1000, 5000), 2)
        purchases = round(random.uniform(500, 2000), 2)

        entries.append(
            {"day": day, "sales": sales, "purchases": purchases, "schoolId": school_id}
        )

    # Create bulk entries
    bulk_entries_url = urljoin(
        endpoint, f"v1/reports/daily/{school_id}/{year}/{month}/entries/bulk"
    )
    bulk_response = await client.post(bulk_entries_url, json=entries, headers=headers)

    if bulk_response.status_code not in [200, 201]:
        # Check if entries already exist
        if bulk_response.status_code == 409 and "already exists" in bulk_response.text:
            print(f"Daily entries already exist for {year}-{month:02d}, skipping...")
            return
        print(
            f"Error creating daily entries: {bulk_response.status_code} - {bulk_response.text}"
        )

    # Mark the daily report as for review
    daily_status_url = urljoin(
        endpoint, f"v1/reports/daily/{school_id}/{year}/{month}/status"
    )
    await client.patch(
        daily_status_url,
        json={"new_status": "review", "comments": "Daily report created"},
        headers=headers,
    )


async def create_liquidation_report(
    client: httpx.AsyncClient,
    school_id: int,
    year: int,
    month: int,
    category: str,
    endpoint: str,
    headers: dict[str, str],
    canteen_manager_id: str,
) -> None:
    """Create a liquidation report for a specific category."""

    # Generate random liquidation entries
    entries: list[dict[str, str | float]] = []
    num_entries = random.randint(3, 8)

    for _ in range(num_entries):
        # Generate random date within the month
        day = random.randint(1, 28)  # Use 28 to avoid month boundary issues
        entry_date = datetime.datetime(year, month, day)

        entries.append(
            {
                "date": entry_date.isoformat(),
                "particulars": f.catch_phrase(),
                "receiptNumber": f"REC-{random.randint(1000, 9999)}",
                "quantity": round(random.uniform(1, 10), 2),
                "unit": random.choice(["pcs", "kg", "liter", "box", "pack"]),
                "unitPrice": round(random.uniform(10, 500), 2),
                "amount": round(random.uniform(50, 2000), 2),
            }
        )

    liquidation_url = urljoin(
        endpoint, f"v1/reports/liquidation/{school_id}/{year}/{month}/{category}"
    )
    liquidation_data: dict[str, Any] = {
        "schoolId": school_id,
        # "notedBy": canteen_manager_id,
        "preparedBy": canteen_manager_id,
        "teacherInCharge": canteen_manager_id,
        "memo": f"Liquidation report for {category} - {month:02d}/{year}",
        "entries": entries,
        "certifiedBy": [canteen_manager_id],
    }

    liquidation_response = await client.patch(
        liquidation_url, json=liquidation_data, headers=headers
    )

    if liquidation_response.status_code not in [200, 201]:
        # Check if the error is because the report already exists or has constraint issues
        if liquidation_response.status_code == 409 and (
            "already exists" in liquidation_response.text
        ):
            print(
                f"Liquidation report for {category} already exists for {year}-{month:02d}, skipping..."
            )
            return
        print(
            f"Error creating liquidation report for {category}: {liquidation_response.status_code} - {liquidation_response.text}"
        )

    # Mark the liquidation report as for review
    liquidation_status_url = urljoin(
        endpoint,
        f"v1/reports/liquidation/{school_id}/{year}/{month}/{category}/status",
    )
    await client.patch(
        liquidation_status_url,
        json={"new_status": "review", "comments": "Liquidation report created"},
        headers=headers,
    )


async def create_payroll_report(
    client: httpx.AsyncClient,
    school_id: int,
    year: int,
    month: int,
    endpoint: str,
    headers: dict[str, str],
    canteen_manager_id: str,
) -> None:
    """Create a payroll report for a month."""

    # First create the payroll report
    payroll_url = urljoin(endpoint, f"v1/reports/payroll/{school_id}/{year}/{month}")
    payroll_response = await client.patch(
        payroll_url, headers=headers, params={"noted_by": canteen_manager_id}
    )

    if payroll_response.status_code not in [200, 201]:
        # Check if the error is because the report already exists
        if payroll_response.status_code == 409 or (
            payroll_response.status_code == 500
            and "UNIQUE constraint failed" in payroll_response.text
        ):
            print(f"Payroll report already exists for {year}-{month:02d}, skipping...")
            return
        print(
            f"Error creating payroll report: {payroll_response.status_code} - {payroll_response.text}"
        )
        return

    # Generate payroll entries for different employees and weeks
    employees = [
        "Maria Santos",
        "Juan Dela Cruz",
        "Ana Rodriguez",
        "Pedro Martinez",
        "Carmen Lopez",
    ]

    entries: list[dict[str, str | int | float]] = []
    for week in range(1, 5):  # 4 weeks in a month
        for employee in employees:
            # Generate random daily amounts
            daily_amounts = [round(random.uniform(100, 300), 2) for _ in range(7)]

            entry: dict[str, str | int | float] = {
                "week_number": week,
                "employee_name": employee,
                "sun": daily_amounts[0],
                "mon": daily_amounts[1],
                "tue": daily_amounts[2],
                "wed": daily_amounts[3],
                "thu": daily_amounts[4],
                "fri": daily_amounts[5],
                "sat": daily_amounts[6],
                "signature": f"sig_{employee.lower().replace(' ', '_')}",
            }
            entries.append(entry)

    # Create bulk payroll entries
    bulk_entries_url = urljoin(
        endpoint, f"v1/reports/payroll/{school_id}/{year}/{month}/entries/bulk"
    )
    bulk_response = await client.post(bulk_entries_url, json=entries, headers=headers)

    if bulk_response.status_code not in [200, 201]:
        # Check if entries already exist
        if bulk_response.status_code == 409 and "already exists" in bulk_response.text:
            print(f"Payroll entries already exist for {year}-{month:02d}, skipping...")
            return
        print(
            f"Error creating payroll entries: {bulk_response.status_code} - {bulk_response.text}"
        )

    # Mark the payroll report as for review
    payroll_status_url = urljoin(
        endpoint, f"v1/reports/payroll/{school_id}/{year}/{month}/status"
    )
    await client.patch(
        payroll_status_url,
        json={"new_status": "review", "comments": "Payroll report created"},
        headers=headers,
    )


async def approve_reports(
    client: httpx.AsyncClient,
    school_id: int,
    year: int,
    month: int,
    endpoint: str,
    headers: dict[str, str],
    liquidation_categories: list[str],
) -> None:
    """Approve all reports for a given month (for past months only)."""

    # Approve daily report
    daily_status_url = urljoin(
        endpoint, f"v1/reports/daily/{school_id}/{year}/{month}/status"
    )
    await client.patch(
        daily_status_url,
        json={"new_status": "approved", "comments": "Approved by principal"},
        headers=headers,
    )

    # Approve liquidation reports
    for category in liquidation_categories:
        liquidation_status_url = urljoin(
            endpoint,
            f"v1/reports/liquidation/{school_id}/{year}/{month}/{category}/status",
        )
        await client.patch(
            liquidation_status_url,
            json={"new_status": "approved", "comments": "Approved by principal"},
            headers=headers,
        )

    # Approve payroll report
    payroll_status_url = urljoin(
        endpoint, f"v1/reports/payroll/{school_id}/{year}/{month}/status"
    )
    await client.patch(
        payroll_status_url,
        json={"new_status": "approved", "comments": "Approved by principal"},
        headers=headers,
    )


async def main(
    endpoint: str,
    quantity: int = 31,
    days: int = 731,
    superintendents: int = 10,
    administrators: int = 10,
    principals: int = 1,
    canteen_managers: int = 1,
) -> int:
    wa = await get_token(DEFAULT_USERNAME, DEFAULT_PASSWORD, 1, endpoint)
    # create a superintendent user for use in the script
    if not wa:
        print("Failed to obtain access token for school creation.")
        return 1

    r = httpx.post(
        urljoin(endpoint, "v1/auth/create"),
        json={
            "username": SI_USERNAME,
            "password": SI_PASSWORD,
            "roleId": 2,  # Superintendent role
        },
        headers={"Authorization": f"Bearer {wa}"},
    )
    if r.status_code not in [201, 409]:  # 409 means user already exists
        print(f"Error creating mock superintendent: {r.text}")
        return 1
    elif r.status_code == 409:
        print("Mock superintendent already exists, continuing...")

    print()
    school_creation_token = await get_token(SI_USERNAME, SI_PASSWORD, 2, endpoint)
    if not school_creation_token:
        print("Failed to obtain access token for school creation.")
        return 2

    create_user_endpoint = urljoin(endpoint, "v1/auth/create")
    update_user_endpoint = urljoin(endpoint, "v1/users/")
    update_school_endpoint = urljoin(endpoint, "v1/schools/")
    headers = {"Authorization": f"Bearer {school_creation_token}"}

    async with httpx.AsyncClient() as client:
        # Create superintendents
        for i in range(superintendents):
            print(f"Creating superintendent {i + 1} of {superintendents}...")
            user_data: dict[str, str | int] = {
                "username": generate_valid_username(suffix=f"_{i + 1}"),
                # "password": f"{f.password(
                #     upper_case=True, digits=True, lower_case=True, length=12
                # )}",
                "password": USERS_PASSWORD,
                "roleId": 2,  # Superintendent role
            }
            response = await client.post(
                create_user_endpoint,
                json=user_data,
                headers=headers,
            )
            if response.status_code != 201:
                print(f"Error creating superintendent: {response.text}")
                return 4

            user_info: dict[str, str] = {
                "id": response.json().get("id"),
                "email": f.email(),
                "nameFirst": f.first_name(),
                "nameMiddle": f.last_name(),
                "nameLast": f.last_name(),
                "position": "Superintendent",
            }
            # Update superintendent user info
            response2 = await client.patch(
                update_user_endpoint,
                json=user_info,
                headers=headers,
            )
            if response2.status_code not in [200, 201]:
                print(f"Error updating superintendent info: {response2.text}")
                return 4

        # Create administrators
        for i in range(administrators):
            print(f"Creating administrator {i + 1} of {administrators}...")
            user_data = {
                "username": generate_valid_username(suffix=f"_{i + 1}_admin"),
                # "password": f"{f.password(upper_case=True, digits=True, lower_case=True, length=12)}",
                "password": USERS_PASSWORD,
                "roleId": 3,  # Administrator role
            }
            response = await client.post(
                create_user_endpoint,
                json=user_data,
                headers=headers,
            )
            if response.status_code != 201:
                print(f"Error creating administrator: {response.text}")
                return 5

            user_info: dict[str, str] = {
                "id": response.json().get("id"),
                "email": f.email(),
                "nameFirst": f.first_name(),
                "nameMiddle": f.last_name(),
                "nameLast": f.last_name(),
                "position": "Administrator",
            }

            # Update administrator user info
            response2 = await client.patch(
                update_user_endpoint,
                json=user_info,
                headers=headers,
            )
            if response2.status_code not in [200, 201]:
                print(f"Error updating administrator info: {response2.text}")
                return 5

        # Create schools with principals and canteen managers, and their history
        for i in range(quantity):
            print(f"Creating school {i + 1} of {quantity}...")
            school_data = {
                "name": f"{f.company()} (Sample School {i + 1})",
                "address": f"{f.street_address()}",
                "phone": f.phone_number(),
                "email": f.email(),
                "website": f.url(),
            }
            create_school_endpoint = urljoin(endpoint, "v1/schools/create")
            response = await client.post(
                create_school_endpoint,
                json=school_data,
                headers=headers,
            )
            if response.status_code != 201:
                print(f"Error creating school {i + 1}: {response.text}")
                return 3

            school_id = response.json().get("id")
            print(f"Created school {i + 1}: {school_data['name']} (ID: {school_id})")

            # Create principals
            principal_data: list[dict[str, str]] = []
            for j in range(principals):
                print(
                    f"Creating principal {j + 1} of {principals} for school {i + 1}..."
                )
                principal_username = generate_valid_username(
                    suffix=f"_principal_{i + 1}_{j + 1}"
                )
                # principal_password = f"{f.password(upper_case=True, digits=True, lower_case=True, length=12)}"
                principal_password = USERS_PASSWORD
                principal_user_data: dict[str, str | int] = {
                    "username": principal_username,
                    "password": principal_password,
                    "roleId": 4,  # Principal role
                }
                response = await client.post(
                    create_user_endpoint,
                    json=principal_user_data,
                    headers=headers,
                )
                if response.status_code != 201:
                    print(f"Error creating principal: {response.text}")
                    return 6

                principal_resp_data = response.json()
                response2 = await client.patch(
                    update_user_endpoint,
                    json={
                        "id": principal_resp_data.get("id"),
                        "email": f"{f.email()}",
                        "nameFirst": f"{f.first_name()}",
                        "nameMiddle": f"{f.last_name()}",
                        "nameLast": f"{f.last_name()}",
                        "position": f"Principal of {school_data['name']}",
                        "schoolId": school_id,
                    },
                    headers=headers,
                )
                if response2.status_code not in [200, 201]:
                    print(f"Error updating principal: {response2.text}")
                    return 7

                principal_data.append(
                    {
                        "id": principal_resp_data.get("id"),
                        "username": principal_username,
                        "password": principal_password,
                    }
                )

            # Assign a random principal to the school
            response = await client.patch(
                update_school_endpoint,
                json={
                    "id": school_id,
                    "name": school_data["name"],
                    "assignedNotedBy": random.choice(principal_data)["id"],
                },
                headers=headers,
            )

            if response.status_code not in [200, 201]:
                print(f"Error updating school with principal: {response.text}")
                return 8

            print(
                f"Assigned principal to school {i + 1}: {response.json().get('assignedNotedBy')}"
            )

            # Create canteen managers
            canteen_manager_data: list[dict[str, str]] = []
            for j in range(canteen_managers):
                print(
                    f"Creating canteen manager {j + 1} of {canteen_managers} for school {i + 1}..."
                )
                canteen_manager_username = generate_valid_username(
                    suffix=f"_canteen_{i + 1}_{j + 1}"
                )
                # canteen_manager_password = f"{f.password(upper_case=True, digits=True, lower_case=True, length=12)}"
                canteen_manager_password = USERS_PASSWORD
                canteen_manager_user_data: dict[str, str | int] = {
                    "username": canteen_manager_username,
                    "password": canteen_manager_password,
                    "roleId": 5,  # Canteen Manager role
                }
                response = await client.post(
                    create_user_endpoint,
                    json=canteen_manager_user_data,
                    headers=headers,
                )
                if response.status_code not in [201, 200]:
                    print(f"Error creating canteen manager: {response.text}")
                    return 9

                canteen_manager_resp_data = response.json()
                response2 = await client.patch(
                    update_user_endpoint,
                    json={
                        "id": canteen_manager_resp_data.get("id"),
                        "email": f"{f.email()}",
                        "nameFirst": f"{f.first_name()}",
                        "nameMiddle": f"{f.last_name()}",
                        "nameLast": f"{f.last_name()}",
                        "position": f"Canteen Manager of {school_data['name']}",
                        "schoolId": school_id,
                    },
                    headers=headers,
                )
                if response2.status_code not in [200, 201]:
                    print(f"Error updating canteen manager: {response2.text}")
                    return 10

                canteen_manager_data.append(
                    {
                        "id": canteen_manager_resp_data.get("id"),
                        "username": canteen_manager_username,
                        "password": canteen_manager_password,
                    }
                )

            # Simulate school history
            await simulate_school_history(
                school_id,
                days,
                endpoint,
                school_creation_token,
                canteen_manager_data,
                principal_data,
            )

    return 0


def generate_valid_username(prefix: str = "", suffix: str = "") -> str:
    """Generate a valid username between 3-22 characters."""
    while True:
        base_username = f.user_name()
        full_username = f"{prefix}{base_username}{suffix}"

        # Ensure username is within valid range
        if 3 <= len(full_username) <= 22:
            return full_username

        # If too long, truncate the base username
        if len(full_username) > 22:
            max_base_length = 22 - len(prefix) - len(suffix)
            if max_base_length >= 1:
                truncated_base = base_username[:max_base_length]
                return f"{prefix}{truncated_base}{suffix}"

        # If too short, try again or pad with numbers
        if len(full_username) < 3:
            padding_needed = 3 - len(full_username)
            padded_username = full_username + str(
                random.randint(10 ** (padding_needed - 1), 10**padding_needed - 1)
            )
            if len(padded_username) <= 22:
                return padded_username


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Populate the database with initial data."
    )
    parser.add_argument(
        "-e",
        "--endpoint",
        type=str,
        help="The endpoint to populate the database with initial data.",
        default="http://localhost:8081/api/",
    )
    parser.add_argument(
        "-q",
        "--quantity",
        type=int,
        default=31,
        help="The number of sample schools to create. (Default: 31)",
    )
    parser.add_argument(
        "-d",
        "--days",
        type=int,
        default=731,
        help="How many days in the past to generate data for. (Default: 731)",
    )
    parser.add_argument(
        "-s",
        "--superintendents",
        type=int,
        default=10,
        help="The number of superintendents to create. (Default: 10)",
    )
    parser.add_argument(
        "-a",
        "--administrators",
        type=int,
        default=10,
        help="The number of administrators to create. (Default: 10)",
    )
    parser.add_argument(
        "-p",
        "--principals",
        type=int,
        default=1,
        help="The number of principals to create per school. (Default: 1)",
    )
    parser.add_argument(
        "-c",
        "--canteen-managers",
        type=int,
        default=1,
        help="The number of canteen managers to create per school. (Default: 1)",
    )
    args = parser.parse_args()

    sys.exit(
        asyncio.run(
            main(
                args.endpoint,
                quantity=args.quantity,
                days=args.days,
                superintendents=args.superintendents,
                administrators=args.administrators,
                principals=args.principals,
                canteen_managers=args.canteen_managers,
            )
        )
    )
