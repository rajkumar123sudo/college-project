
import streamlit as st
import sqlite3
from pathlib import Path
import hashlib
import hmac
import os
import pandas 
import requests
import math
from streamlit_geolocation import streamlit_geolocation

# Demo login configuration
# Real deployment: store credentials in Streamlit
# Demo login configuration
ADMIN_USERNAME = "rk_verma05"
ADMIN_PASSWORD = "12345"



def show_login():
    st.title("🔐 Admin Login")
    st.write("Sign in to manage healthcare records.")

    if st.session_state.get("admin_logged_in", False):
        st.success("✅ Login successful! Admin is logged in.")

        if st.button("Logout", key="login_page_logout"):
            st.session_state["admin_logged_in"] = False
            st.session_state["login_success"] = False
            st.rerun()

        return

    with st.form("admin_login_form"):
        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        submitted = st.form_submit_button(
            "Login",
            type="primary"
        )

    if submitted:
        if (
            hmac.compare_digest(username, ADMIN_USERNAME)
            and hmac.compare_digest(password, ADMIN_PASSWORD)
        ):
            st.session_state["admin_logged_in"] = True
            st.session_state["login_success"] = True
            st.rerun()
        else:
            st.error("Incorrect username or password.")


st.set_page_config(
    page_title="Rural Healthcare System",
    page_icon="🏥",
    layout="wide"
)

DB_PATH = Path(__file__).parent / "healthcare.db"



def get_connection():
    return sqlite3.connect(DB_PATH)


def ensure_appointments_user_id():
    with get_connection() as conn:
        columns = [
            row[1]
            for row in conn.execute(
                "PRAGMA table_info(appointments)"
            ).fetchall()
        ]

        if "user_id" not in columns:
            conn.execute(
                "ALTER TABLE appointments ADD COLUMN user_id INTEGER"
            )



def create_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER NOT NULL,
                village TEXT NOT NULL,
                phone TEXT
            )
        """)


def create_users_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                appointment_time TEXT NOT NULL,
                health_center TEXT NOT NULL,
                reason TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Booked',
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """) 

def register_patient(name, age, village, phone):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO patients
               (name, age, village, phone)
               VALUES (?, ?, ?, ?)""",
            (name, age, village, phone)
        )


def get_patients(search=""):
    with get_connection() as conn:
        return conn.execute(
            """SELECT id, name, age, village, phone
               FROM patients
               WHERE name LIKE ?
               ORDER BY id DESC""",
            (f"%{search}%",)
        ).fetchall()


create_table()

create_users_table()

ensure_appointments_user_id()

def hash_password(password):
    return hashlib.sha256(
        password.encode("utf-8")
    ).hexdigest()


def register_user(full_name, mobile, username, password):
    password_hash = hash_password(password)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO users
                (full_name, mobile, username, password_hash)
                VALUES (?, ?, ?, ?)
                """,
                (
                    full_name.strip(),
                    mobile.strip(),
                    username.strip(),
                    password_hash
                )
            )
        return True, "Account created successfully!"

    except sqlite3.IntegrityError:
        return False, "This username already exists."

def login_user(username, password):    
    password_hash = hash_password(password)

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, full_name, username, password_hash
            FROM users
            WHERE username = ?
            """,
            (username.strip(),)
        ).fetchone()

    if user and hmac.compare_digest(user[3], password_hash):
        return user

    return None
 
def login_user(username, password):
    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, full_name, username, password_hash
            FROM users
            WHERE username = ?
            """,
            (username.strip(),)
        ).fetchone()

    if user and hmac.compare_digest(
        user[3], hash_password(password)
    ):
        return True, user

    return False, None


def login_user(username, password):
    password_hash = hash_password(password)

    with get_connection() as conn:
        user = conn.execute(
            """
            SELECT id, full_name, username, password_hash
            FROM users
            WHERE username = ?
            """,
            (username.strip(),)
        ).fetchone()

    if user and hmac.compare_digest(user[3], password_hash):
        return user

    return None


def book_appointment(
    patient_id, appointment_date, appointment_time,
    health_center, reason
):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO appointments
               (patient_id, appointment_date, appointment_time,
                health_center, reason)
               VALUES (?, ?, ?, ?, ?)""",
            (
                patient_id, str(appointment_date),
                str(appointment_time), health_center, reason
            )
        )


def get_appointments():
    with get_connection() as conn:
        return conn.execute("""
            SELECT a.id, p.name, a.appointment_date,
                   a.appointment_time, a.health_center,
                   a.reason, a.status
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            ORDER BY a.appointment_date, a.appointment_time
        """).fetchall()


def cancel_appointment(appointment_id):
    with get_connection() as conn:
        conn.execute(
            """UPDATE appointments
               SET status = 'Cancelled'
               WHERE id = ?""",
            (appointment_id,)
        )


def update_patient(patient_id, name, age, village, phone):
    with get_connection() as conn:
        conn.execute(
            """UPDATE patients
               SET name = ?, age = ?, village = ?, phone = ?
               WHERE id = ?""",
            (name, age, village, phone, patient_id)
        )


def delete_patient(patient_id):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM patients WHERE id = ?",
            (patient_id,)
        )


def create_center_table():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS healthcare_centers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                village TEXT NOT NULL,
                district TEXT NOT NULL,
                phone TEXT,
                services TEXT NOT NULL
            )
        """)


def add_healthcare_center(name, village, district, phone, services):
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO healthcare_centers
            (name, village, district, phone, services)
            VALUES (?, ?, ?, ?, ?)
        """, (name, village, district, phone, services))


def get_healthcare_centers(search=""):
    with get_connection() as conn:
        return conn.execute("""
            SELECT id, name, village, district, phone, services
            FROM healthcare_centers
            WHERE name LIKE ?
               OR village LIKE ?
               OR district LIKE ?
            ORDER BY name
        """, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()


create_center_table()



def get_place_coordinates(place):
    url = "https://nominatim.openstreetmap.org/search"

    queries = [
        f"{place}, Madhya Pradesh, India",
        f"{place}, India",
        place
    ]

    headers = {
        "User-Agent": "RuralHealthcareAssistance/1.0"
    }

    for query in queries:
        try:
            response = requests.get(
                url,
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 1,
                    "countrycodes": "in"
                },
                headers=headers,
                timeout=20
            )
            response.raise_for_status()
            results = response.json()

            if results:
                return (
                    float(results[0]["lat"]),
                    float(results[0]["lon"])
                )

        except (requests.RequestException, ValueError, KeyError):
            continue

    return None



def get_nearby_hospitals(latitude, longitude, radius=10000):
    query = f"""
    [out:json][timeout:40];
    (
      nwr(around:{int(radius)},{latitude},{longitude})["amenity"~"^(hospital|clinic|doctors|health_post)$"];
      nwr(around:{int(radius)},{latitude},{longitude})["healthcare"];
    );
    out center tags;
    """

    endpoints = [
        "https://overpass.kumi.systems/api/interpreter",
        "https://overpass-api.de/api/interpreter",
    ]

    data = None
    last_error = None

    for url in endpoints:
        try:
            response = requests.post(
                url,
                data={"data": query},
                headers={
                    "User-Agent": "RuralHealthcareAssistance/1.0 (healthcare finder)",
                    "Accept": "application/json"
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            break

        except (requests.RequestException, ValueError) as error:
            last_error = error

    if data is None:
        raise RuntimeError(
            f"Healthcare map service failed: {last_error}"
        )

    hospitals = []
    seen = set()

    for item in data.get("elements", []):
        tags = item.get("tags", {})

        if item["type"] == "node":
            lat = item.get("lat")
            lon = item.get("lon")
        else:
            center = item.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")

        if lat is None or lon is None:
            continue

        lat = float(lat)
        lon = float(lon)

        # Approximate distance in kilometres
        lat1 = math.radians(float(latitude))
        lat2 = math.radians(lat)
        dlat = lat2 - lat1
        dlon = math.radians(lon - float(longitude))

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2)
            * math.sin(dlon / 2) ** 2
        )
        distance = 6371 * 2 * math.asin(
            math.sqrt(min(1, a))
        )

        # Keep only facilities within the requested radius
        if distance > int(radius) / 1000:
            continue

        name = tags.get("name", "Name not listed")
        unique_key = (name, round(lat, 5), round(lon, 5))

        if unique_key in seen:
            continue
        seen.add(unique_key)

        address = ", ".join(
            str(tags[key])
            for key in [
                "addr:street",
                "addr:city",
                "addr:postcode"
            ]
            if tags.get(key)
        ) or "Address not listed"

        phone = tags.get(
            "phone",
            tags.get("contact:phone", "Not listed")
        )

        map_url = (
            "https://www.google.com/maps/dir/?api=1"
            f"&destination={lat},{lon}"
        )

        hospitals.append({
            "name": name,
            "type": tags.get(
                "amenity",
                tags.get("healthcare", "Healthcare")
            ),
            "address": address,
            "phone": phone,
            "distance_km": round(distance, 2),
            "latitude": lat,
            "longitude": lon,
            "map_url": map_url
        })

    return sorted(
        hospitals,
        key=lambda hospital: hospital["distance_km"]
    )


st.markdown("""
<style>
.stApp { background: #f3f8f6; }
[data-testid="stSidebar"] { background: #e0eee8; }
.hero {
    background: linear-gradient(120deg, #075e54, #159b83);
    color: white;
    padding: 28px;
    border-radius: 16px;
}
.hero h1 { color: white; }
</style>
""", unsafe_allow_html=True)

st.sidebar.title("🏥 Rural Health")
st.sidebar.caption("Healthcare for every village")



# Require login before showing application pages
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False





page = st.sidebar.radio(
    "Navigation",
    [
        "Find Hospitals",
        "Health Information",
        "Healthcare Centers",
        "Appointment Booking",
        "Patient Admit",
        "Sign Up",
        "User login",
        "My Profile",
        "Admin Login",
        "Dashboard",
        "Patient Records",
        "Appointments List",
    ],
    key="navigation"
)




if page == "Sign Up":
    st.title("📝 Create Your Account")
    st.write("Register to view your own healthcare information.")

    with st.form("user_registration_form"):
        full_name = st.text_input("Full Name")
        mobile = st.text_input("Mobile Number")
        username = st.text_input("Choose Username")
        password = st.text_input("Create Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")

        submitted = st.form_submit_button("Create Account", type="primary")

    if submitted:
        if not all([
            full_name.strip(), mobile.strip(), username.strip(),
            password, confirm_password
        ]):
            st.error("Please fill in all fields.")
        elif not mobile.isdigit() or len(mobile) != 10:
            st.error("Enter a valid 10-digit mobile number.")
        elif len(password) < 8:
            st.error("Password must be at least 8 characters.")
        elif password != confirm_password:
            st.error("Passwords do not match.")
        else:
            success, message = register_user(
                full_name, mobile, username, password
            )
            if success:
                st.success(message)
            else:
                st.error(message)



# ---------------- USER LOGIN ----------------
if page == "User login":
    st.title("🔐 User Login")

    with st.form("user_login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login_button = st.form_submit_button("Login")

    if login_button:
        if not username.strip() or not password:
            st.warning("Please enter username and password.")
        else:
            user = login_user(username, password)

            if user:
                st.session_state["user_logged_in"] = True
                st.session_state["user_id"] = user[0]
                st.session_state["user_full_name"] = user[1]
                st.session_state["username"] = user[2]

                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid username or password.")


# ---------------- MY PROFILE ----------------

if page == "My Profile":
    st.title("👤 My Profile")

    if st.session_state.get("user_logged_in", False):
        st.success("You are logged in!")

        st.write(
            "**Full Name:**",
            st.session_state.get("user_full_name", "")
        )

        st.write(
            "**Username:**",
            st.session_state.get("username", "")
        )

        st.divider()

        # My Appointments
        st.subheader("📅 My Appointments")

        user_id = st.session_state.get("user_id")

        with get_connection() as conn:
            appointments = conn.execute(
                """
                SELECT
                    id,
                    appointment_date,
                    appointment_time,
                    health_center,
                    reason,
                    status
                FROM appointments
                WHERE user_id = ?
                ORDER BY appointment_date DESC
                """,
                (user_id,)
            ).fetchall()

        if appointments:
            for appointment in appointments:
                with st.container(border=True):
                    st.write(f"**Appointment ID:** {appointment[0]}")
                    st.write(f"**Date:** {appointment[1]}")
                    st.write(f"**Time:** {appointment[2]}")
                    st.write(f"**Healthcare Center:** {appointment[3]}")
                    st.write(f"**Reason:** {appointment[4]}")
                    st.write(f"**Status:** {appointment[5]}")

        else:
            st.info("अभी आपकी कोई appointment नहीं हुई है।")


        st.divider()

        # Logout
        if st.button("🚪 Logout", key="user_logout_button"):
            for key in [
                "user_logged_in",
                "user_id",
                "user_full_name",
                "username"
            ]:
                st.session_state.pop(key, None)

            st.success("You have logged out successfully!")
            st.rerun()

    else:
        st.warning("Please log in first.")
        st.info("Go to User login to access your profile.")


if page == "Admin Login":
    show_login()

admin_only_pages = [
    "Dashboard",
    "Patient Records",
    "Appointments List"
]

if (
    page in admin_only_pages
    and not st.session_state.get("admin_logged_in", False)
):
    st.warning("Please log in as admin first.")
    st.stop()


if page == "Find Hospitals":
    st.title("🏥 Find Nearby Hospitals")
    st.write(
        "Search for healthcare facilities by village, city, "
        "or your current location."
    )

    search_mode = st.radio(
        "Choose search method",
        ["Village / City", "My Current Location"],
        horizontal=True,
        key="hospital_search_mode"
    )

    radius_km = st.selectbox(
        "Search radius",
        [5, 10, 25, 50, 100],
        index=2,
        key="hospital_radius"
    )

    coordinates = None
    location_label = ""

    if search_mode == "Village / City":
        place = st.text_input(
            "Enter village, city or district",
            placeholder="e.g. Chhatarpur, Madhya Pradesh",
            key="city_hospital_search"
        )

        if st.button("🔎 Search Hospitals", key="city_search_button"):
            if not place.strip():
                st.warning("Please enter a village or city name.")
            else:
                with st.spinner("Finding location..."):
                    coordinates = get_place_coordinates(place.strip())

                if coordinates is None:
                    st.error(
                        "Location not found. Try village, district "
                        "and state name."
                    )
                else:
                    st.session_state["hospital_coordinates"] = coordinates
                    st.session_state["hospital_location_label"] = place.strip()

    else:
        st.write(
            "Allow location access in your browser, then search nearby."
        )

        location = streamlit_geolocation()

        if isinstance(location, dict):
            lat = location.get("latitude")
            lon = location.get("longitude")

            if lat is not None and lon is not None:
                st.success("Current location received.")

                if st.button(
                    "📍 Search Hospitals Near Me",
                    key="current_location_search"
                ):
                    st.session_state["hospital_coordinates"] = (
                        float(lat), float(lon)
                    )
                    st.session_state["hospital_location_label"] = (
                        "Your current location"
                    )
            else:
                st.info(
                    "Location coordinates not received. Allow location "
                    "permission and try again."
                )
        else:
            st.info("Waiting for browser location permission.")

    saved_coordinates = st.session_state.get("hospital_coordinates")
    saved_label = st.session_state.get("hospital_location_label", "")

    # Show results only for the selected search method
    should_show = (
        saved_coordinates is not None
        and (
            (search_mode == "Village / City"
             and saved_label != "Your current location")
            or
            (search_mode == "My Current Location"
             and saved_label == "Your current location")
        )
    )

    if should_show:
        lat, lon = saved_coordinates

        st.write(f"**Search location:** {saved_label}")

        try:
            with st.spinner("Searching hospitals..."):
                results = get_nearby_hospitals(
                    lat,
                    lon,
                    radius=radius_km * 1000
                )
            st.write(f"Village latitude: {lat}")
            st.write(f"Village longitude: {lon}")
               
            if results:
                st.success(f"Found {len(results)} mapped facilities.")

                for hospital in results:
                    with st.container(border=True):
                        st.subheader("🏥 " + hospital["name"])
                        st.write("Type:", hospital["type"])
                        st.write(
                            f"Approx. distance: "
                            f"{hospital['distance_km']} km"
                        )
                        st.write("Address:", hospital["address"])

                        phone = hospital.get("phone", "Not listed")

                        if phone and phone != "Not listed":
                            phone_number = (
                                str(phone)
                                .replace(" ", "")
                                .replace("-", "")
                                .replace("(", "")
                                .replace(")", "")
                            )
                            st.markdown(f"📞 Phone: {phone}")
                            st.markdown(
                                f"[📞 Call Hospital](tel:{phone_number})"
                            )
                        else:
                            st.caption("Phone number not available.")

                        st.link_button(
                            "📍 Open Map",
                            hospital["map_url"]
                        )

                        hospital_lat = hospital.get("latitude")
                        hospital_lon = hospital.get("longitude")

                        if (
                            hospital_lat is not None
                            and hospital_lon is not None
                        ):
                            directions_url = (
                                "https://www.google.com/maps/dir/?api=1"
                                f"&destination={hospital_lat},{hospital_lon}"
                            )
                            st.link_button(
                                "🚗 Get Directions",
                                directions_url
                            )
            else:
                st.warning(
                    f"No mapped facilities found within {radius_km} km. "
                    "Try a larger radius or another location."
                )

        except requests.RequestException as error:
            st.error(f"Map service connection failed: {error}")


if page == "Dashboard":
    st.markdown("""
    <div class="hero">
        <h1>Rural Healthcare Assistance System</h1>
        <p>Healthcare services and information for rural communities.</p>
    </div>
    """, unsafe_allow_html=True)

    patients = get_patients()
    Appointments = get_appointments()
    centers = get_healthcare_centers()

    total_patients = len(patients)
    total_appointments = len(Appointments)
    booked_appointments = sum(
        1 for a in Appointments if a[6] == "Booked"
    )
    total_centers = len(centers)

    st.subheader("📊 Healthcare Overview")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("👥 Registered Patients", total_patients)
    c2.metric("📅 Total Appointments", total_appointments)
    c3.metric("✅ Booked Appointments", booked_appointments)
    c4.metric("🏥 Healthcare Centers", total_centers)

    st.divider()
    st.subheader("👥 Patients by Village")

    if patients:
        import pandas as pd

        patient_df = pd.DataFrame(
            [
                {"Village": p[3]}
                for p in patients
            ]
        )

        village_counts = (
            patient_df["Village"]
            .value_counts()
            .rename_axis("Village")
            .reset_index(name="Patients")
        )

        st.bar_chart(
            village_counts,
            x="Village",
            y="Patients"
        )
    else:
        st.info(
            "Patient statistics will appear after patients are registered."
        )

    st.divider()
    st.subheader("📅 Recent Appointments")

    if Appointments:
        for a in Appointments[:5]:
            with st.container(border=True):
                st.write(f"**Patient:** {a[1]}")
                st.write(f"**Date:** {a[2]} | **Time:** {a[3]}")
                st.write(f"**Center:** {a[4]}")
                st.write(f"**Status:** {a[6]}")
    else:
        st.info("No appointments have been booked yet.")


elif page == "Patient Admit":
    st.title("👤 Patient Admit")
    st.write("Enter the patient's basic details.")

    with st.form("patient_form", clear_on_submit=True):
        name = st.text_input("Full Name")
        age = st.number_input(
            "Age", min_value=0, max_value=120, value=18
        )
        village = st.text_input("Village")
        phone = st.text_input("Mobile Number (optional)")

        submitted = st.form_submit_button(
            "Submit Admission Request",
            type="primary"
        )

        if submitted:
            if not name.strip() or not village.strip():
                st.error("Please enter the name and village.")
            elif phone and (
                not phone.isdigit() or len(phone) != 10
            ):
                st.error("Enter a valid 10-digit mobile number.")
            else:
                register_patient(
                    name.strip(),
                    int(age),
                    village.strip(),
                    phone.strip()
                )
                st.success(
                    f"Patient {name.strip()} registered successfully!"
                )


elif page == "Patient Records":
    st.title("📋 Patient Records")
    st.caption("Patient record management")

    search = st.text_input("Search by patient name")
    records = get_patients(search.strip())

    if records:
        st.dataframe(
            [
                {
                    "Patient ID": r[0],
                    "Name": r[1],
                    "Age": r[2],
                    "Village": r[3],
                    "Mobile": r[4] or "Not provided"
                }
                for r in records
            ],
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Manage Patient")

        patient_options = {
            f"ID {r[0]} - {r[1]}": r
            for r in records
        }

        selected_label = st.selectbox(
            "Select a patient",
            list(patient_options.keys())
        )

        patient = patient_options[selected_label]
        patient_id, old_name, old_age, old_village, old_phone = patient

        action = st.radio(
            "Choose action",
            ["Edit Patient", "Delete Patient"],
            horizontal=True
        )

        if action == "Edit Patient":
            with st.form("edit_patient_form"):
                name = st.text_input("Full Name", value=old_name)
                age = st.number_input(
                    "Age", min_value=0, max_value=120,
                    value=old_age
                )
                village = st.text_input(
                    "Village", value=old_village
                )
                phone = st.text_input(
                    "Mobile Number", value=old_phone or ""
                )

                save = st.form_submit_button("Save Changes")

                if save:
                    if not name.strip() or not village.strip():
                        st.error("Name and village are required.")
                    elif phone and (
                        not phone.isdigit() or len(phone) != 10
                    ):
                        st.error("Enter a valid 10-digit mobile number.")
                    else:
                        update_patient(
                            patient_id, name.strip(), int(age),
                            village.strip(), phone.strip()
                        )
                        st.success("Patient record updated!")
                        st.rerun()

        else:
            st.warning(
                f"You are about to delete the record for {old_name}."
            )

            confirm = st.checkbox(
                "I confirm that I want to delete this record."
            )

            if st.button("Delete Patient", type="primary"):
                if confirm:
                    delete_patient(patient_id)
                    st.success("Patient record deleted.")
                    st.rerun()
                else:
                    st.error("Please confirm before deleting.")

    else:
        st.info("No patient records found.")


    search = st.text_input(
    "Search by patient name",
    key="patient_search"
)
    records = get_patients(search.strip())

    if records:
        st.dataframe(
            [
                {
                    "Patient ID": r[0],
                    "Name": r[1],
                    "Age": r[2],
                    "Village": r[3],
                    "Mobile": r[4] or "Not provided"
                }
                for r in records
            ],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No patient records found.")





elif page == "Healthcare Centers":
    st.title("🏥 Healthcare Center Management")
    st.write("Add and search healthcare facilities.")

    with st.expander("➕ Add Healthcare Center"):
        with st.form("add_center_form"):
            name = st.text_input("Center / Hospital Name")
            village = st.text_input("Village / Town")
            district = st.text_input("District")
            phone = st.text_input("Contact Number (optional)")
            services = st.text_area(
                "Available Services",
                placeholder="Example: General consultation, vaccination"
            )

            submitted = st.form_submit_button("Save Center")

            if submitted:
                if not name.strip() or not village.strip() or not district.strip() or not services.strip():
                    st.error("Name, village, district and services are required.")
                elif phone and (
                    not phone.isdigit() or len(phone) != 10
                ):
                    st.error("Enter a valid 10-digit contact number.")
                else:
                    add_healthcare_center(
                        name.strip(),
                        village.strip(),
                        district.strip(),
                        phone.strip(),
                        services.strip()
                    )
                    st.success("Healthcare center saved!")
                    st.rerun()

    st.divider()
    st.subheader("🔎 Search Healthcare Centers")

    search = st.text_input(
        "Search by name, village or district",
        key="health_center_search"
    )

    centers = get_healthcare_centers(search.strip())

    if centers:
        st.write(f"Found {len(centers)} healthcare center(s).")

        for center in centers:
            with st.container(border=True):
                st.subheader(f"🏥 {center[1]}")
                st.write(f"**Village / Town:** {center[2]}")
                st.write(f"**District:** {center[3]}")
                st.write(f"**Contact:** {center[4] or 'Not provided'}")
                st.write(f"**Services:** {center[5]}")
    else:
        st.info("No centers found. Add a verified center to get started.")


elif page == "Health Information":
    st.title("💚 Health Information")

    with st.expander("Personal Hygiene"):
        st.write(
            "Wash hands with soap and clean water regularly."
        )

    with st.expander("Nutrition"):
        st.write(
            "Eat a varied, balanced diet with nutritious local foods."
        )

    with st.expander("Preventive Healthcare"):
        st.write(
            "Consult qualified healthcare workers about "
            "vaccination and routine checkups."
        )



elif page == "Appointment Booking":
    st.title("📅 Appointment Booking")
    st.write("Enter your details to book an appointment.")

    with st.form("appointment_form", clear_on_submit=True):
        patient_name = st.text_input("Patient Name")
        age = st.number_input(
            "Age", min_value=1, max_value=120, value=18
        )
        village = st.text_input("Village")
        phone = st.text_input("Mobile Number")

        appointment_date = st.date_input("Appointment Date")
        appointment_time = st.time_input("Appointment Time")

        health_center = st.text_input(
            "Healthcare Center Name",
            key="appointment_center"
        )

        reason = st.text_area(
            "Reason for Visit",
            key="appointment_reason"
        )

        submitted = st.form_submit_button(
            "Book Appointment",
            type="primary"
        )


        if submitted:
            if not st.session_state.get("user_logged_in", False):
                st.warning(
                    "Please log in before booking an appointment."
                )

            elif not patient_name.strip() or not village.strip():
                st.error("Please enter patient name and village.")

            elif phone and (
                not phone.isdigit() or len(phone) != 10
            ):
                st.error("Enter a valid 10-digit mobile number.")

            elif not health_center.strip() or not reason.strip():
                st.error(
                    "Please enter the healthcare center and reason."
                )

            else:
                try:
                    user_id = st.session_state.get("user_id")

                    with get_connection() as conn:
                        cursor = conn.execute(
                            """
                            INSERT INTO patients
                            (name, age, village, phone)
                            VALUES (?, ?, ?, ?)
                            """,
                            (
                                patient_name.strip(),
                                int(age),
                                village.strip(),
                                phone.strip()
                            )
                        )

                        patient_id = cursor.lastrowid

                        conn.execute(
                            """
                            INSERT INTO appointments
                            (
                                patient_id,
                                appointment_date,
                                appointment_time,
                                health_center,
                                reason,
                                user_id
                            )
                            VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                patient_id,
                                str(appointment_date),
                                str(appointment_time),
                                health_center.strip(),
                                reason.strip(),
                                user_id
                            )
                        )

                    st.success(
                        f"Appointment booked successfully for "
                        f"{patient_name.strip()}!"
                    )

                except Exception as e:
                    st.error(f"Unable to book appointment: {e}")


elif page == "Appointments List":
    st.title("📋 Appointments List")
    st.write("View all booked appointments.")

    appointments = get_appointments()

    if appointments:
        import pandas as pd

        appointment_data = [
            {
                "Appointment ID": a[0],
                "Patient Name": a[1],
                "Date": a[2],
                "Time": a[3],
                "Healthcare Center": a[4],
                "Reason": a[5],
                "Status": a[6]
            }
            for a in appointments
        ]

        st.dataframe(
            appointment_data,
            use_container_width=True,
            hide_index=True
        )

        st.subheader("Cancel Appointment")

        appointment_ids = [a[0] for a in appointments]

        selected_id = st.selectbox(
            "Select Appointment ID",
            appointment_ids
        )

        if st.button("Cancel Selected Appointment"):
            cancel_appointment(selected_id)
            st.success("Appointment cancelled successfully!")
            st.rerun()

    else:
        st.info("No appointments have been booked yet.")


        

st.divider()
st.caption("Rural Healthcare Assistance System | Educational Project")
st.caption(
    "This application is not a substitute for professional medical advice."
)

#    
