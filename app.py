import streamlit as st
import sqlite3
import os
import uuid
from datetime import datetime
import pandas as pd
import plotly.express as px

# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Smart Waste Management",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

DB_NAME = "smart_waste.db"


# ============================================================
# DATABASE
# ============================================================

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            complaint_id TEXT UNIQUE NOT NULL,
            citizen_email TEXT NOT NULL,
            waste_type TEXT NOT NULL,
            description TEXT NOT NULL,
            location TEXT NOT NULL,
            latitude REAL,
            longitude REAL,
            image_path TEXT,
            status TEXT DEFAULT 'Pending',
            assigned_worker TEXT,
            proof_image TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Default users for demo
    demo_users = [
        ("Admin", "admin@waste.com", "admin123", "Admin"),
        ("Worker One", "worker1@waste.com", "worker123", "Worker"),
        ("Worker Two", "worker2@waste.com", "worker123", "Worker"),
    ]

    for user in demo_users:
        try:
            cursor.execute("""
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
            """, user)
        except sqlite3.IntegrityError:
            pass

    conn.commit()
    conn.close()


init_database()


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown("""
<style>

.main {
    background-color: #f5f8f6;
}

.block-container {
    padding-top: 1.5rem;
}

.hero {
    background: linear-gradient(135deg, #075e54, #128c7e);
    padding: 30px;
    border-radius: 18px;
    color: white;
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 38px;
    margin-bottom: 5px;
}

.hero p {
    font-size: 17px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
    margin-bottom: 15px;
}

.metric-card {
    background: white;
    padding: 20px;
    border-radius: 15px;
    text-align: center;
    box-shadow: 0 2px 10px rgba(0,0,0,0.07);
}

.metric-number {
    font-size: 32px;
    font-weight: bold;
    color: #075e54;
}

.metric-title {
    color: #666;
    font-size: 15px;
}

.status {
    padding: 5px 12px;
    border-radius: 20px;
    font-weight: bold;
}

</style>
""", unsafe_allow_html=True)


# ============================================================
# SESSION STATE
# ============================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "user_role" not in st.session_state:
    st.session_state.user_role = None

if "user_name" not in st.session_state:
    st.session_state.user_name = None


# ============================================================
# DATABASE FUNCTIONS
# ============================================================

def authenticate(email, password):
    conn = get_connection()

    query = """
        SELECT name, email, role
        FROM users
        WHERE email = ? AND password = ?
    """

    result = conn.execute(query, (email, password)).fetchone()

    conn.close()

    return result


def register_user(name, email, password):
    conn = get_connection()

    try:
        conn.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, 'Citizen')
        """, (name, email, password))

        conn.commit()
        conn.close()

        return True, "Registration successful."

    except sqlite3.IntegrityError:
        conn.close()
        return False, "Email already registered."


def create_complaint(
    citizen_email,
    waste_type,
    description,
    location,
    latitude,
    longitude,
    image_path
):

    conn = get_connection()

    complaint_id = "SW-" + uuid.uuid4().hex[:8].upper()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        INSERT INTO complaints (
            complaint_id,
            citizen_email,
            waste_type,
            description,
            location,
            latitude,
            longitude,
            image_path,
            status,
            assigned_worker,
            proof_image,
            created_at,
            updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        complaint_id,
        citizen_email,
        waste_type,
        description,
        location,
        latitude,
        longitude,
        image_path,
        "Pending",
        None,
        None,
        now,
        now
    ))

    conn.commit()
    conn.close()

    return complaint_id


def get_complaints():
    conn = get_connection()

    df = pd.read_sql_query(
        "SELECT * FROM complaints ORDER BY created_at DESC",
        conn
    )

    conn.close()

    return df


def get_citizen_complaints(email):
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM complaints
        WHERE citizen_email = ?
        ORDER BY created_at DESC
        """,
        conn,
        params=(email,)
    )

    conn.close()

    return df


def get_workers():
    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT name, email
        FROM users
        WHERE role = 'Worker'
        """,
        conn
    )

    conn.close()

    return df


def assign_worker(complaint_id, worker_email):

    conn = get_connection()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        UPDATE complaints
        SET assigned_worker = ?,
            status = 'Assigned',
            updated_at = ?
        WHERE complaint_id = ?
    """, (
        worker_email,
        now,
        complaint_id
    ))

    conn.commit()
    conn.close()


def update_status(complaint_id, status):

    conn = get_connection()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        UPDATE complaints
        SET status = ?,
            updated_at = ?
        WHERE complaint_id = ?
    """, (
        status,
        now,
        complaint_id
    ))

    conn.commit()
    conn.close()


def save_proof(complaint_id, proof_path):

    conn = get_connection()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn.execute("""
        UPDATE complaints
        SET proof_image = ?,
            status = 'Resolved',
            updated_at = ?
        WHERE complaint_id = ?
    """, (
        proof_path,
        now,
        complaint_id
    ))

    conn.commit()
    conn.close()


# ============================================================
# LOGIN PAGE
# ============================================================

def login_page():

    st.markdown("""
    <div class="hero">
        <h1>♻️ Smart Waste Management</h1>
        <p>Connecting citizens, administrators and sanitation workers
        for cleaner and smarter communities.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:

        st.markdown("### 🔐 Login")

        email = st.text_input(
            "Email",
            placeholder="Enter your email"
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password"
        )

        if st.button(
            "Login",
            use_container_width=True,
            type="primary"
        ):

            result = authenticate(email, password)

            if result:

                st.session_state.logged_in = True
                st.session_state.user_name = result[0]
                st.session_state.user_email = result[1]
                st.session_state.user_role = result[2]

                st.success("Login successful!")
                st.rerun()

            else:
                st.error("Invalid email or password.")

        st.divider()

        st.markdown("### New Citizen?")

        if st.button(
            "Create Citizen Account",
            use_container_width=True
        ):
            st.session_state.show_register = True
            st.rerun()


# ============================================================
# REGISTRATION
# ============================================================

def registration_page():

    st.markdown("""
    <div class="hero">
        <h1>♻️ Create Account</h1>
        <p>Join the Smart Waste Management platform.</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:

        name = st.text_input("Full Name")

        email = st.text_input("Email Address")

        password = st.text_input(
            "Password",
            type="password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password"
        )

        if st.button(
            "Register",
            type="primary",
            use_container_width=True
        ):

            if not name or not email or not password:
                st.error("Please fill all fields.")

            elif password != confirm_password:
                st.error("Passwords do not match.")

            else:

                success, message = register_user(
                    name,
                    email,
                    password
                )

                if success:
                    st.success(message)
                    st.info("You can now login.")
                else:
                    st.error(message)

        if st.button("Back to Login"):
            st.session_state.show_register = False
            st.rerun()


# ============================================================
# CITIZEN DASHBOARD
# ============================================================

def citizen_dashboard():

    st.markdown("""
    <div class="hero">
        <h1>👤 Citizen Dashboard</h1>
        <p>Report waste problems and track their resolution.</p>
    </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio(
        "Citizen Menu",
        [
            "Dashboard",
            "Report Waste",
            "My Complaints"
        ]
    )

    if menu == "Dashboard":

        df = get_citizen_complaints(
            st.session_state.user_email
        )

        total = len(df)

        pending = len(
            df[df["status"] == "Pending"]
        ) if not df.empty else 0

        resolved = len(
            df[df["status"] == "Resolved"]
        ) if not df.empty else 0

        st.subheader(
            f"Welcome, {st.session_state.user_name} 👋"
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{total}</div>
                <div class="metric-title">My Complaints</div>
            </div>
            """, unsafe_allow_html=True)

        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{pending}</div>
                <div class="metric-title">Pending</div>
            </div>
            """, unsafe_allow_html=True)

        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{resolved}</div>
                <div class="metric-title">Resolved</div>
            </div>
            """, unsafe_allow_html=True)

    elif menu == "Report Waste":

        report_waste()

    elif menu == "My Complaints":

        df = get_citizen_complaints(
            st.session_state.user_email
        )

        st.subheader("📋 My Complaints")

        if df.empty:
            st.info("You have not submitted any complaints yet.")

        else:

            for _, row in df.iterrows():

                with st.expander(
                    f"{row['complaint_id']} — {row['status']}"
                ):

                    st.write(
                        f"**Waste Type:** {row['waste_type']}"
                    )

                    st.write(
                        f"**Location:** {row['location']}"
                    )

                    st.write(
                        f"**Description:** {row['description']}"
                    )

                    st.write(
                        f"**Assigned Worker:** "
                        f"{row['assigned_worker'] or 'Not assigned'}"
                    )

                    st.write(
                        f"**Created:** {row['created_at']}"
                    )

                    st.write(
                        f"**Last Updated:** {row['updated_at']}"
                    )

                    if row["image_path"] and os.path.exists(
                        row["image_path"]
                    ):
                        st.image(
                            row["image_path"],
                            width=350
                        )

                    if row["proof_image"] and os.path.exists(
                        row["proof_image"]
                    ):
                        st.write("### Completion Proof")
                        st.image(
                            row["proof_image"],
                            width=350
                        )


# ============================================================
# REPORT WASTE
# ============================================================

def report_waste():

    st.subheader("🚨 Report a Waste Problem")

    with st.form("complaint_form"):

        waste_type = st.selectbox(
            "Waste Type",
            [
                "Overflowing Garbage",
                "Plastic Waste",
                "Food / Organic Waste",
                "Construction Waste",
                "Medical Waste",
                "Illegal Dumping",
                "E-Waste",
                "Other"
            ]
        )

        location = st.text_input(
            "Location",
            placeholder="Example: Ongole Bus Stand"
        )

        col1, col2 = st.columns(2)

        with col1:

            latitude = st.number_input(
                "Latitude",
                value=15.5057,
                format="%.6f"
            )

        with col2:

            longitude = st.number_input(
                "Longitude",
                value=80.0499,
                format="%.6f"
            )

        description = st.text_area(
            "Describe the Problem",
            placeholder="Explain the waste problem..."
        )

        uploaded_file = st.file_uploader(
            "Upload Waste Image",
            type=[
                "jpg",
                "jpeg",
                "png"
            ]
        )

        submitted = st.form_submit_button(
            "🚨 Submit Complaint",
            use_container_width=True
        )

        if submitted:

            if not location or not description:
                st.error(
                    "Please provide location and description."
                )

            else:

                image_path = None

                if uploaded_file:

                    filename = (
                        datetime.now().strftime("%Y%m%d%H%M%S")
                        + "_"
                        + uploaded_file.name
                    )

                    image_path = os.path.join(
                        UPLOAD_DIR,
                        filename
                    )

                    with open(
                        image_path,
                        "wb"
                    ) as f:
                        f.write(
                            uploaded_file.getbuffer()
                        )

                complaint_id = create_complaint(
                    st.session_state.user_email,
                    waste_type,
                    description,
                    location,
                    latitude,
                    longitude,
                    image_path
                )

                st.success(
                    f"Complaint submitted successfully!"
                )

                st.info(
                    f"Your Complaint ID is: **{complaint_id}**"
                )


# ============================================================
# ADMIN DASHBOARD
# ============================================================

def admin_dashboard():

    st.markdown("""
    <div class="hero">
        <h1>👨‍💼 Admin Dashboard</h1>
        <p>Monitor complaints, assign workers and analyze
        waste-management performance.</p>
    </div>
    """, unsafe_allow_html=True)

    menu = st.sidebar.radio(
        "Admin Menu",
        [
            "Dashboard",
            "Complaints",
            "Assign Workers",
            "Analytics"
        ]
    )

    df = get_complaints()

    if menu == "Dashboard":

        admin_overview(df)

    elif menu == "Complaints":

        admin_complaints(df)

    elif menu == "Assign Workers":

        admin_assign_workers(df)

    elif menu == "Analytics":

        analytics(df)


# ============================================================
# ADMIN OVERVIEW
# ============================================================

def admin_overview(df):

    st.subheader("📊 Waste Management Overview")

    total = len(df)

    pending = (
        len(df[df["status"] == "Pending"])
        if not df.empty else 0
    )

    assigned = (
        len(df[df["status"] == "Assigned"])
        if not df.empty else 0
    )

    progress = (
        len(df[df["status"] == "In Progress"])
        if not df.empty else 0
    )

    resolved = (
        len(df[df["status"] == "Resolved"])
        if not df.empty else 0
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    metrics = [
        ("Total", total),
        ("Pending", pending),
        ("Assigned", assigned),
        ("In Progress", progress),
        ("Resolved", resolved)
    ]

    for col, (title, value) in zip(
        [c1, c2, c3, c4, c5],
        metrics
    ):

        with col:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{value}</div>
                <div class="metric-title">{title}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    if not df.empty:

        st.subheader("Recent Complaints")

        st.dataframe(
            df[
                [
                    "complaint_id",
                    "waste_type",
                    "location",
                    "status",
                    "assigned_worker",
                    "created_at"
                ]
            ].head(10),
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# ADMIN COMPLAINTS
# ============================================================

def admin_complaints(df):

    st.subheader("📋 Complaint Management")

    if df.empty:

        st.info("No complaints available.")

        return

    status_filter = st.selectbox(
        "Filter by Status",
        [
            "All",
            "Pending",
            "Assigned",
            "In Progress",
            "Resolved"
        ]
    )

    filtered = df.copy()

    if status_filter != "All":

        filtered = filtered[
            filtered["status"] == status_filter
        ]

    st.dataframe(
        filtered[
            [
                "complaint_id",
                "citizen_email",
                "waste_type",
                "location",
                "status",
                "assigned_worker",
                "created_at"
            ]
        ],
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# ASSIGN WORKERS
# ============================================================

def admin_assign_workers(df):

    st.subheader("👷 Assign Complaints to Workers")

    pending_df = df[
        df["status"].isin(
            ["Pending", "Assigned"]
        )
    ]

    if pending_df.empty:

        st.success(
            "No pending complaints requiring assignment."
        )

        return

    workers = get_workers()

    if workers.empty:

        st.warning("No workers available.")

        return

    worker_options = dict(
        zip(
            workers["name"],
            workers["email"]
        )
    )

    for _, row in pending_df.iterrows():

        with st.container():

            st.markdown(
                f"### 🚨 {row['complaint_id']}"
            )

            st.write(
                f"**Waste:** {row['waste_type']}"
            )

            st.write(
                f"**Location:** {row['location']}"
            )

            st.write(
                f"**Status:** {row['status']}"
            )

            selected_worker = st.selectbox(
                "Select Worker",
                list(worker_options.keys()),
                key=f"worker_{row['complaint_id']}"
            )

            if st.button(
                "Assign Worker",
                key=f"assign_{row['complaint_id']}"
            ):

                assign_worker(
                    row["complaint_id"],
                    worker_options[selected_worker]
                )

                st.success(
                    f"Assigned to {selected_worker}"
                )

                st.rerun()

            st.divider()


# ============================================================
# WORKER DASHBOARD
# ============================================================

def worker_dashboard():

    st.markdown("""
    <div class="hero">
        <h1>🧹 Worker Dashboard</h1>
        <p>View assigned waste complaints and update task progress.</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM complaints
        WHERE assigned_worker = ?
        ORDER BY created_at DESC
        """,
        conn,
        params=(st.session_state.user_email,)
    )

    conn.close()

    total = len(df)

    assigned = len(
        df[df["status"] == "Assigned"]
    ) if not df.empty else 0

    progress = len(
        df[df["status"] == "In Progress"]
    ) if not df.empty else 0

    resolved = len(
        df[df["status"] == "Resolved"]
    ) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)

    values = [
        ("Assigned", assigned),
        ("In Progress", progress),
        ("Resolved", resolved),
        ("Total Tasks", total)
    ]

    for col, (title, value) in zip(
        [c1, c2, c3, c4],
        values
    ):

        with col:

            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-number">{value}</div>
                <div class="metric-title">{title}</div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    st.subheader("🧹 My Assigned Tasks")

    if df.empty:

        st.info("No complaints assigned to you.")

        return

    for _, row in df.iterrows():

        with st.expander(
            f"{row['complaint_id']} — {row['status']}"
        ):

            st.write(
                f"**Waste Type:** {row['waste_type']}"
            )

            st.write(
                f"**Location:** {row['location']}"
            )

            st.write(
                f"**Description:** {row['description']}"
            )

            st.write(
                f"**Coordinates:** "
                f"{row['latitude']}, {row['longitude']}"
            )

            if row["image_path"] and os.path.exists(
                row["image_path"]
            ):

                st.write("### Complaint Image")

                st.image(
                    row["image_path"],
                    width=400
                )

            # Map
            if row["latitude"] and row["longitude"]:

                map_df = pd.DataFrame({
                    "latitude": [row["latitude"]],
                    "longitude": [row["longitude"]]
                })

                st.map(map_df)

            if row["status"] == "Assigned":

                if st.button(
                    "▶ Start Work",
                    key=f"start_{row['complaint_id']}"
                ):

                    update_status(
                        row["complaint_id"],
                        "In Progress"
                    )

                    st.success("Work started.")

                    st.rerun()

            elif row["status"] == "In Progress":

                proof = st.file_uploader(
                    "Upload Completion Proof",
                    type=["jpg", "jpeg", "png"],
                    key=f"proof_{row['complaint_id']}"
                )

                if st.button(
                    "✅ Complete Complaint",
                    key=f"complete_{row['complaint_id']}"
                ):

                    if proof:

                        filename = (
                            "proof_"
                            + datetime.now().strftime(
                                "%Y%m%d%H%M%S"
                            )
                            + "_"
                            + proof.name
                        )

                        proof_path = os.path.join(
                            UPLOAD_DIR,
                            filename
                        )

                        with open(
                            proof_path,
                            "wb"
                        ) as f:
                            f.write(
                                proof.getbuffer()
                            )

                        save_proof(
                            row["complaint_id"],
                            proof_path
                        )

                        st.success(
                            "Complaint marked as resolved!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Please upload a completion proof image."
                        )


# ============================================================
# ANALYTICS
# ============================================================

def analytics(df):

    st.subheader("📈 Waste Management Analytics")

    if df.empty:

        st.info(
            "Analytics will appear after complaints are submitted."
        )

        return

    total = len(df)

    resolved = len(
        df[df["status"] == "Resolved"]
    )

    resolution_rate = (
        resolved / total * 100
        if total > 0 else 0
    )

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Total Complaints",
            total
        )

    with c2:

        st.metric(
            "Resolved Complaints",
            resolved
        )

    with c3:

        st.metric(
            "Resolution Rate",
            f"{resolution_rate:.1f}%"
        )

    st.divider()

    # Status chart

    st.subheader("Complaint Status")

    status_data = (
        df["status"]
        .value_counts()
        .reset_index()
    )

    status_data.columns = [
        "Status",
        "Count"
    ]

    fig1 = px.pie(
        status_data,
        names="Status",
        values="Count",
        title="Complaints by Status"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    # Waste type chart

    st.subheader("Waste Types")

    waste_data = (
        df["waste_type"]
        .value_counts()
        .reset_index()
    )

    waste_data.columns = [
        "Waste Type",
        "Count"
    ]

    fig2 = px.bar(
        waste_data,
        x="Waste Type",
        y="Count",
        title="Most Reported Waste Types"
    )

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # Location chart

    st.subheader("Frequently Affected Locations")

    location_data = (
        df["location"]
        .value_counts()
        .head(10)
        .reset_index()
    )

    location_data.columns = [
        "Location",
        "Complaints"
    ]

    fig3 = px.bar(
        location_data,
        x="Complaints",
        y="Location",
        orientation="h",
        title="Top Waste Problem Areas"
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # Map

    st.subheader("🗺️ Waste Complaint Map")

    map_data = df[
        ["latitude", "longitude"]
    ].dropna()

    if not map_data.empty:

        st.map(map_data)


# ============================================================
# SIDEBAR USER INFORMATION
# ============================================================

def sidebar_user():

    st.sidebar.markdown("---")

    st.sidebar.write(
        f"👤 **{st.session_state.user_name}**"
    )

    st.sidebar.write(
        f"Role: **{st.session_state.user_role}**"
    )

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False
        st.session_state.user_email = None
        st.session_state.user_role = None
        st.session_state.user_name = None

        st.rerun()


# ============================================================
# MAIN APPLICATION
# ============================================================

if "show_register" not in st.session_state:
    st.session_state.show_register = False


if not st.session_state.logged_in:

    if st.session_state.show_register:

        registration_page()

    else:

        login_page()

else:

    sidebar_user()

    if st.session_state.user_role == "Citizen":

        citizen_dashboard()

    elif st.session_state.user_role == "Admin":

        admin_dashboard()

    elif st.session_state.user_role == "Worker":

        worker_dashboard()

    else:

        st.error("Invalid user role.")