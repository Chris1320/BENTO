import asyncio
import getpass
import sys
from dataclasses import dataclass
from urllib.parse import urljoin

import httpx
from faker import Faker

f = Faker()


@dataclass
class School:
    name: str
    address: str | None = None
    phone: str | None = None
    email: str | None = None
    website: str | None = None


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


SCHOOLS: list[School] = [
    # District I
    School(  # https://sites.google.com/deped.gov.ph/engrvicentercruzmemorialschool/contact-us
        name="Engr. Vicente R. Cruz Memorial School",
        address="A. Mabini St., Tibag, Baliwag, Bulacan",
        phone="(044) 798-0223",
        email="104741@deped.gov.ph",
        website="https://www.facebook.com/EVRCTibag",
    ),
    School(  # https://sites.google.com/deped.gov.ph/104746-sabang-es/home
        name="Sabang Elementary School",
        address="Brgy. Sabang, Baliwag, Bulacan",
        phone="(044) 798-0225",
        email="104746@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104746-sabang-es/home",
    ),
    School(  # https://www.facebook.com/TEMHSOfficial/
        name="Teodoro Evangelista Memorial High School",
        address="A. Mabini St., Tibag, Baliwag, Bulacan",
        phone="(044) 798 0803",
        email="306717@deped.gov.ph",
        website="https://www.facebook.com/TEMHSOfficial/",
    ),
    # District II
    School(  # https://sites.google.com/deped.gov.ph/subic-elementary-school/home
        name="Subic Elementary School",
        address="Aurea Village, Osmeña St., Baliwag, Bulacan",
        email="104784@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/subic-elementary-school/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/marianoponcenhs
        name="Mariano Ponce National High School",
        address="Benigno S. Aquino Ave., Bagong Nayon, Baliwag, Bulacan",
        phone="(044) 766-2759",
        email="100199915124829@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/marianoponcenhs",
    ),
    School(  # https://www.facebook.com/DepEdTayoBaliuagSeniorHighSchool/
        name="Baliuag Senior High School",
        address="Virgen Delas Flores, Baliwag, Bulacan",
        phone="(044) 816-1513",
        email="345213@deped.gov.ph",
        website="https://www.facebook.com/DepEdTayoBaliuagSeniorHighSchool/",
    ),
    # District III
    School(  # https://sites.google.com/deped.gov.ph/baliwag-north-central-school/home
        name="Baliwag North Central School",
        address="J. Buizon St., Poblacion, Baliwag, Bulacan",
        email="104737@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/baliwag-north-central-school/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/104750baliwagsouthcs/home
        name="Baliwag South Central School",
        address="J. Buizon St, Santo Cristo, Baliwag, Bulacan",
        email="104750@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104750baliwagsouthcs/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/jacintoponceelementaryschool/home
        name="Jacinto Ponce Elementary School",
        address="L. Pile St., Tangos, Baliwag, Bulacan",
        email="104743@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/jacintoponceelementaryschool/home",
    ),
    # District IV
    School(  # https://sites.google.com/deped.gov.ph/104752cones/home
        name="Concepcion Elementary School",
        address="R.E. Chico St, Concepcion, Baliwag, Bulacan",
        email="104752@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104752cones/home",
    ),
    School(  # https://www.facebook.com/104760VirgenDelasFloresES/
        name="Virgen Delas Flores Elementary School",
        address="Alido Subd Phase II, Virgen Delas Flores, Baliwag, Bulacan 3006",
        email="104760@deped.gov.ph",
        website="https://www.facebook.com/104760VirgenDelasFloresES/",
    ),
    School(  # https://www.facebook.com/DepEdTayoVDFHS/
        name="Virgen Delas Flores High School",
        address="Luyong St., Alido Subdivision Phase II, Virgen Delas Flores",
        phone="(044) 798-4746",
        email="306705@deped.gov.ph",
        website="https://www.facebook.com/DepEdTayoVDFHS/",
    ),
    # District V
    School(  # https://sites.google.com/deped.gov.ph/104759tiaongelementaryschool/home
        name="Tiaong Elementary School",
        address="Segismundo St, Tiaong, Baliwag, Bulacan",
        email="104759@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104759tiaongelementaryschool/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/104757stabarbaraes/home
        name="Sta. Barbara Elementary School",
        address="J. P. Rizal Street, Sta. Barbara, Baliwag, Bulacan",
        phone="(044) 816-7280",
        email="104757@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104757stabarbaraes/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/sta-barbara-high-school/home
        name="Sta. Barbara High School",
        address="Aldama St., Sta. Barbara, Baliwag, Bulacan",
        phone="0922-254-1648",
        email="305993@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/sta-barbara-high-school/home",
    ),
    # District VI
    School(  # https://sites.google.com/deped.gov.ph/104753makes/home
        name="Makinabang Elementary School",
        address="Calle Rizal, Makinabang, Baliwag, Bulacan",
        email="104753@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104753makes/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/104756sanjose/home
        name="San Jose Elementary School",
        address="Aquino Ave, San Jose, Baliwag, Bulacan",
        email="102756@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104756sanjose/home",
    ),
    School(  # https://www.facebook.com/people/DepEd-Tayo-Tarcan-Elementary-School-104758/100057649021443/
        name="Tarcan Elementary School",
        address="Tarcan, Baliwag, Bulacan",
        email="104758@deped.gov.ph",
        website="https://www.facebook.com/people/DepEd-Tayo-Tarcan-Elementary-School-104758/100057649021443/",
    ),
    # District VII
    School(  # https://sites.google.com/deped.gov.ph/drgdelamercedmemorialschool
        name="Dr. G. Dela Merced Memorial School",
        address="Barangca, Baliwag, Bulacan",
        email="104739@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/drgdelamercedmemorialschool",
    ),
    School(  # https://sites.google.com/deped.gov.ph/drnicolasvrustiamemorialschool/home
        name="Dr. Nicolas V. Rustia Memorial School",
        address="Zone 2, Piel, Baliwag, Bulacan",
        email="104740@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/drnicolasvrustiamemorialschool/home",
    ),
    School(  # https://www.facebook.com/SNHS306712/
        name="Sto. Niño High School",
        address="Sto. Niño, Baliwag, Baliwag, Bulacan",
        phone="0916 495 9935",
        email="306712@deped.gov.ph",
        website="https://www.facebook.com/SNHS306712/",
    ),
    # District VIII
    School(  # https://sites.google.com/deped.gov.ph/hinukay-elementary-school/home
        name="Hinukay Elementary School",
        address="F. Clemente St., Hinukay, Baliwag, Bulacan",
        email="104742@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/hinukay-elementary-school/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/104744-josefa-v-ycasiano-ms/home
        name="Josefa V. Ycasiano Memorial School",
        address="Aquino Avenue, San Roque, Baliwag, Bulacan",
        email="104744@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104744-josefa-v-ycasiano-ms/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/paitan-es/home
        name="Paitan Elementary School",
        address="Paitan, Baliwag, Bulacan",
        email="104745@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/paitan-es/home",
    ),
    # District IX
    School(  # https://sites.google.com/deped.gov.ph/104738catulinanes/home
        name="Catulinan Elementary School",
        address="Catulinan, Baliwag, Bulacan",
        email="104738@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104738catulinanes/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/104749-tes/home
        name="Tilapayong Elementary School",
        address="Magsaysay St., Tilapayong, Baliwag, Bulacan",
        email="104749@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104749-tes/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/deped-sulivan-nhs/home
        name="Sulivan National High School",
        address="Sulivan, Baliwag, Bulacan",
        phone="(044) 816-7731",
        email="300778@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/deped-sulivan-nhs/home",
    ),
    # District X
    School(  # https://sites.google.com/deped.gov.ph/104754mates/home
        name="Matangtubig Elementary School",
        address="Camia, Matangtubig, Baliwag, Bulacan",
        email="1104754@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104754mates/home",
    ),
    School(  # https://sites.google.com/deped.gov.ph/104751cales/home
        name="Calantipay Elementary School",
        address="Calantipay, Baliwag, Bulacan",
        email="104751@deped.gov.ph",
        website="https://sites.google.com/deped.gov.ph/104751cales/home",
    ),
    School(  # https://sites.google.com/view/104755pinagbarilanelemschool/home
        name="Pinagbarilan Elementary School",
        address="Sta. Lucia St, Pinagbarilan, Baliwag, Bulacan 3006",
        email="104755@deped.gov.ph",
        website="https://sites.google.com/view/104755pinagbarilanelemschool/home",
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


async def create_school_users(
    school_id: int, school_name: str, endpoint: str, token: str
) -> bool:
    """Create a principal and canteen manager for a specific school."""
    headers = {"Authorization": f"Bearer {token}"}
    add_user_endpoint = urljoin(endpoint, "v1/auth/create")
    update_user_endpoint = urljoin(endpoint, "v1/users/")

    # Create users for this school
    users_to_create = [
        UserData(
            username=f"principal_{school_id}",
            role_id=4,  # Principal role
            password="Password123",
            email=f"principal_{school_id}@school.edu",
            name_first=f.first_name(),
            name_last=f.last_name(),
            school_id=school_id,
        ),
        UserData(
            username=f"canteen_{school_id}",
            role_id=5,  # Canteen manager role
            password="Password123",
            email=f"canteen_{school_id}@school.edu",
            name_first=f.first_name(),
            name_last=f.last_name(),
            school_id=school_id,
        ),
    ]

    async with httpx.AsyncClient() as client:
        for user_data in users_to_create:
            role_name = "Principal" if user_data.role_id == 4 else "Canteen Manager"
            print(f"  Creating {role_name} for '{school_name}'...")

            # Create user
            create_response = await client.post(
                add_user_endpoint,
                json={
                    "username": user_data.username,
                    "roleId": user_data.role_id,
                    "password": user_data.password,
                },
                headers=headers,
            )
            if create_response.status_code != 201:
                print(
                    f"  Error creating {role_name}: {create_response.status_code} - {create_response.text}"
                )
                return False

            # Update user with additional details
            update_response = await client.patch(
                update_user_endpoint,
                json={
                    "id": create_response.json()["id"],
                    "email": user_data.email,
                    "nameFirst": user_data.name_first,
                    "nameMiddle": user_data.name_middle,
                    "nameLast": user_data.name_last,
                    "schoolId": user_data.school_id,
                },
                headers=headers,
            )
            if update_response.status_code != 200:
                print(
                    f"  Error updating {role_name}: {update_response.status_code} - {update_response.text}"
                )
                return False

            print(f"  {role_name} '{user_data.username}' created successfully.")

    return True


async def main(endpoint: str) -> int:
    exit_code = 0
    print("Enter your credentials to obtain an access token.")
    print("Required Role: Superintendent")
    print()
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    school_creation_token = get_token(username, password, 2, endpoint)
    if not school_creation_token:
        print("Failed to obtain access token for school creation.")
        return 2

    print("Access token obtained successfully.")
    print("Creating schools...")
    school_ids: dict[str, int] = {}  # To store school names and their IDs

    async with httpx.AsyncClient() as client:
        for school in SCHOOLS:
            response = await client.post(
                urljoin(endpoint, "v1/schools/create"),
                headers={"Authorization": f"Bearer {school_creation_token}"},
                json={
                    "name": school.name,
                    "address": school.address,
                    "phone": school.phone,
                    "email": school.email,
                    "website": school.website,
                },
            )
            if response.status_code == 201:
                school_id = response.json()["id"]
                school_ids[school.name] = school_id
                print(f"School '{school.name}' created successfully (ID: {school_id}).")
            else:
                print(
                    f"Failed to create school '{school.name}': {response.status_code} - {response.text}"
                )
                exit_code += 1

    print("All schools processed.")

    if school_ids:
        print("\nCreating users for each school...")
        for school_name, school_id in school_ids.items():
            success = await create_school_users(
                school_id, school_name, endpoint, school_creation_token
            )
            if not success:
                print(f"Failed to create users for school '{school_name}'.")
                exit_code += 1

        print("All users processed.")

    return exit_code


if __name__ == "__main__":
    sys.exit(asyncio.run(main("http://localhost:8081/api/")))
