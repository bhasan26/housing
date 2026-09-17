##Importing all necessary libraries and modules
import os
import sys
import logging
import base64
from io import BytesIO
import mysql.connector
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter


# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


# Load Environment Variables
load_dotenv()

db_user     = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")
db_database = os.environ.get("DB_DATABASE")
db_host     = os.environ.get("DB_HOST")
db_port     = int(os.environ.get("DB_PORT", 3306))


# Flask Application Setup
app = Flask(__name__)

PDF_FOLDER = "pdfs"
os.makedirs(PDF_FOLDER, exist_ok=True)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

CORS(app, resources={r"/*": {"origins": "*"}})


# Inventory items used by the HTML, JS, MySQL save logic, and PDF
INVENTORY_SECTIONS = [
    ("BEDROOM", [
        ("Bed Frame", "bed_frame"),
        ("Mattress", "mattress"),
        ("Wardrobe/Closet", "wardrobe_closet"),
        ("Dresser", "dresser"),
        ("Desk", "desk"),
        ("Chair", "chair"),
        ("Hutch (with Light)", "hutch_light"),
        ("Bookshelf", "bookshelf"),
        ("Walls/Ceiling", "bedroom_walls_ceiling"),
        ("Floor", "bedroom_floor"),
        ("Window/Screen/Crank", "bedroom_window_screen_crank"),
        ("Blinds", "bedroom_blinds"),
        ("Light/Cover Plate", "bedroom_light_cover_plate"),
        ("Phone/Internet/Outlets", "bedroom_phone_internet_outlets"),
        ("Smoke Detector", "smoke_detector"),
        ("Thermostat", "thermostat"),
        ("Room Door/Lock", "room_door_lock"),
        ("Wall Outside Room", "bedroom_wall_outside_room"),
    ]),
    ("LIVING ROOM", [
        ("Sofa", "sofa"),
        ("Overstuffed Chair", "overstuffed_chair"),
        ("Walls/Ceiling", "living_walls_ceiling"),
        ("Floor", "living_floor"),
        ("Window/Screen/Crank", "living_window_screen_crank"),
        ("Blinds", "living_blinds"),
        ("Light/Cover Plate", "living_light_cover_plate"),
        ("Phone/Internet/Outlets", "living_phone_internet_outlets"),
        ("Front Door/Lock", "front_door_lock"),
        ("Wall Outside Room", "living_wall_outside_room"),
    ]),
    ("BATHROOM", [
        ("Mirror", "mirror"),
        ("Sink/Counter", "sink"),
        ("Cabinet/Drawers", "cabinet_drawers"),
        ("Shelves", "shelves"),
        ("Towel Racks", "towel_racks"),
        ("Tub/Shower/Curtain", "tub_shower_curtain"),
        ("Walls/Ceiling", "bathroom_walls_ceiling"),
        ("Floor", "bathroom_floor"),
        ("Light/Fan", "light_fan"),
        ("Outlets", "bathroom_outlets"),
        ("Wall Outside Room", "bathroom_wall_outside_room"),
    ]),
]

INVENTORY_KEYS = []
for section_name, section_items in INVENTORY_SECTIONS:
    for label, key in section_items:
        INVENTORY_KEYS.append(key)


# Residence-hall (traditional dorm) inventory form. Single section, no quantity
# column, walls split into Left/Right/Front/Back plus separate Ceiling/Floor.
# Used by: Arend, Baldwin-Jenkins, Ballard, Village, McMillan, Warren.
RH_INVENTORY_ITEMS = [
    ("Bed Frame", "rh_bed_frame"),
    ("Mattress", "rh_mattress"),
    ("Wardrobe/Closet", "rh_wardrobe_closet"),
    ("Dresser", "rh_dresser"),
    ("Desk", "rh_desk"),
    ("Chair", "rh_chair"),
    ("Hutch (with Light)", "rh_hutch_light"),
    ("Bookshelf", "rh_bookshelf"),
    ("Walls: Left", "rh_walls_left"),
    ("Walls: Right", "rh_walls_right"),
    ("Walls: Front", "rh_walls_front"),
    ("Walls: Back", "rh_walls_back"),
    ("Ceiling", "rh_ceiling"),
    ("Floor", "rh_floor"),
    ("Window/Screen/Crank", "rh_window_screen_crank"),
    ("Blinds", "rh_blinds"),
    ("Light/Cover Plate", "rh_light_cover_plate"),
    ("Phone/Internet/Outlets", "rh_phone_internet_outlets"),
    ("Smoke Detector", "rh_smoke_detector"),
    ("Thermostat", "rh_thermostat"),
    ("Room Door/Lock", "rh_room_door_lock"),
    ("Wall Outside Room", "rh_wall_outside_room"),

]

RH_INVENTORY_KEYS = [key for label, key in RH_INVENTORY_ITEMS]


# Database Connection Helper
def get_db_connection():
    return mysql.connector.connect(
        host=db_host,
        port=db_port,
        user=db_user,
        password=db_password,
        database=db_database
    )


def present_to_bool(value):
    if value == "Yes":
        return True
    if value == "No":
        return False
    return None


# ================= BASIC ROUTES =================

@app.route("/", methods=["GET"])
def index():
    return "Backend is running"


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "healthy", "message": "Flask backend is running"})


@app.route("/testdb", methods=["GET"])
def test_db():
    conn = None
    try:
        conn = get_db_connection()
        return jsonify({"status": "success", "message": "Database connection successful"})
    except mysql.connector.Error as err:
        logger.error(f"Database connection failed: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500
    finally:
        if conn:
            conn.close()


# ================= RESET DB =================

@app.route("/resetdb", methods=["GET"])
def reset_db():
    conn = None
    crsr = None
    sql = ""

    try:
        conn = get_db_connection()
        crsr = conn.cursor()

        crsr.execute("DROP TABLE IF EXISTS pdf_approvals")
        crsr.execute("DROP TABLE IF EXISTS backlog_forms")
        crsr.execute("DROP TABLE IF EXISTS housing")
        crsr.execute("DROP TABLE IF EXISTS users")

        crsr.execute("""
        CREATE TABLE pdf_approvals (
            id              INT NOT NULL AUTO_INCREMENT,
            filename        VARCHAR(255) NOT NULL UNIQUE,
            keys_turned_in  BOOLEAN NOT NULL DEFAULT FALSE,
            admin_signature LONGTEXT,
            completed       BOOLEAN NOT NULL DEFAULT FALSE,
            approved_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id)
        )
        """)

        crsr.execute("""
        CREATE TABLE users (
            id         INT NOT NULL AUTO_INCREMENT,
            sign_in_id VARCHAR(255) NOT NULL UNIQUE,
            password   VARCHAR(255) NOT NULL,
            role       VARCHAR(20) NOT NULL DEFAULT 'student',
            PRIMARY KEY (id)
        )
        """)

        # Seed accounts so there's one working login per role to start with
        crsr.execute(
            "INSERT INTO users (sign_in_id, password, role) VALUES (%s, %s, %s)",
            ["test@whitworth.edu", generate_password_hash("Test1234!"), "student"]
        )
        crsr.execute(
            "INSERT INTO users (sign_in_id, password, role) VALUES (%s, %s, %s)",
            ["admin@whitworth.edu", generate_password_hash("Test1234!"), "admin"]
        )

        crsr.execute("""
        CREATE TABLE housing (
            id           INT NOT NULL AUTO_INCREMENT,
            housing_type VARCHAR(100) NOT NULL,
            housing_name VARCHAR(255),
            capacity     INT,
            PRIMARY KEY (id)
        )
        """)

        # With both forms in one table (~280 columns) we must keep the inline row
        # under InnoDB's 8126-byte limit: note columns are TEXT (stored off-page,
        # ~20-byte pointer each) and the Yes/No work-order columns are VARCHAR(3).
        inventory_columns = ""
        for key in INVENTORY_KEYS:
            inventory_columns += f"""
            {key}_qty           INT NULL,
            {key}_checkin       TEXT NULL,
            {key}_wo_checkin    VARCHAR(3) NULL,
            {key}_checkout      TEXT NULL,
            {key}_wo_checkout   VARCHAR(3) NULL,
            """

        # Residence-hall form columns (no quantity column).
        for key in RH_INVENTORY_KEYS:
            inventory_columns += f"""
            {key}_checkin       TEXT NULL,
            {key}_wo_checkin    VARCHAR(3) NULL,
            {key}_checkout      TEXT NULL,
            {key}_wo_checkout   VARCHAR(3) NULL,
            """

        crsr.execute(f"""
        CREATE TABLE backlog_forms (
            id          INT NOT NULL AUTO_INCREMENT,
            user_id     INT NOT NULL,
            student_id  VARCHAR(150) NOT NULL,
            student_name VARCHAR(150) NULL,

            dorm        VARCHAR(100) NULL,
            room_number VARCHAR(50)  NULL,
            present     BOOLEAN      NULL,
            completion_date DATE     NULL,
            checkout_date   DATE     NULL,
            form_type   VARCHAR(20)  NOT NULL DEFAULT 'apartment',

            {inventory_columns}

            form_status           VARCHAR(50) NOT NULL DEFAULT 'draft',
            completion_percentage INT         NOT NULL DEFAULT 0,
            created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

            PRIMARY KEY (id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        ) ROW_FORMAT=DYNAMIC
        """)

        conn.commit()
        return jsonify({"status": "success", "message": "Database reset successfully"})

    except mysql.connector.Error as err:
        logger.error(f"Error executing {sql}: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500

    finally:
        if crsr:
            crsr.close()
        if conn:
            conn.close()


# ================= USERS =================

@app.route("/login", methods=["POST"])
def login():
    conn = None
    crsr = None
    sql = ""

    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "Missing JSON body"}), 400

        sign_in_id = data.get("sign_in_id")
        password = data.get("password")
        role = data.get("role")

        if not sign_in_id or not password or not role:
            return jsonify({"status": "error", "message": "sign_in_id, password, and role are required"}), 400

        conn = get_db_connection()
        crsr = conn.cursor(dictionary=True)

        sql = "SELECT id, sign_in_id, password, role FROM users WHERE sign_in_id = %s"
        crsr.execute(sql, [sign_in_id])
        user = crsr.fetchone()

        if not user or not check_password_hash(user["password"], password) or user["role"] != role:
            return jsonify({"status": "error", "message": "Invalid email, password, or role"}), 401

        return jsonify({
            "status": "success",
            "user": {"id": user["id"], "sign_in_id": user["sign_in_id"], "role": user["role"]}
        })

    except mysql.connector.Error as err:
        logger.error(f"Error executing {sql}: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500

    finally:
        if crsr:
            crsr.close()
        if conn:
            conn.close()


@app.route("/save_user", methods=["POST"])
def save_user():
    conn = None
    crsr = None
    sql = ""

    try:
        data = request.get_json()

        if not data:
            return jsonify({"status": "error", "message": "Missing JSON body"}), 400

        sign_in_id = data.get("sign_in_id")
        password = data.get("password")
        role = data.get("role", "student")

        if not sign_in_id or not password:
            return jsonify({"status": "error", "message": "sign_in_id and password are required"}), 400

        password_hash = generate_password_hash(password)

        conn = get_db_connection()
        crsr = conn.cursor(buffered=True)

        sql = "SELECT id FROM users WHERE sign_in_id = %s"
        crsr.execute(sql, [sign_in_id])

        if crsr.rowcount > 0:
            result = crsr.fetchone()
            user_id = result[0]
            sql = "UPDATE users SET password = %s, role = %s WHERE id = %s"
            crsr.execute(sql, [password_hash, role, user_id])
            message = "User updated"
        else:
            sql = "INSERT INTO users (sign_in_id, password, role) VALUES (%s, %s, %s)"
            crsr.execute(sql, [sign_in_id, password_hash, role])
            user_id = crsr.lastrowid
            message = "User created"

        conn.commit()

        return jsonify({
            "status": "success",
            "message": message,
            "user": {"id": user_id, "sign_in_id": sign_in_id, "role": role}
        })

    except mysql.connector.Error as err:
        logger.error(f"Error executing {sql}: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500

    finally:
        if crsr:
            crsr.close()
        if conn:
            conn.close()


@app.route("/get_user/<sign_in_id>", methods=["GET"])
def get_user(sign_in_id):
    conn = None
    crsr = None
    sql = ""

    try:
        conn = get_db_connection()
        crsr = conn.cursor(dictionary=True)

        sql = "SELECT id, sign_in_id, role FROM users WHERE sign_in_id = %s"
        crsr.execute(sql, [sign_in_id])
        user = crsr.fetchone()

        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        return jsonify({"status": "success", "user": user})

    except mysql.connector.Error as err:
        logger.error(f"Error executing {sql}: {err}")
        return jsonify({"status": "error", "message": str(err)}), 500

    finally:
        if crsr:
            crsr.close()
        if conn:
            conn.close()


# ================= SAVE FORM =================

# Human-readable labels for the top-of-form fields, used in validation messages.
TOP_FIELD_LABELS = {
    "student_name": "Student name",
    "present": "Present (Yes/No)",
    "dorm": "Dorm",
    "room_number": "Room number",
    "completion_date": "Completion date",
}


def validate_backlog_form(data, form_status, form_type="apartment"):
    """Return an error string if a required field is missing/invalid, else None.

    Validation is mode-aware and form-type-aware:
      - apartment form: top fields + every item's qty / check-in condition.
      - residence-hall form: top fields + every item's check-in condition
        (no quantity column).

    Work order (Yes/No) is optional on both forms and defaults to "No".
    """
    def blank(value):
        return value is None or str(value).strip() == ""

    keys = RH_INVENTORY_KEYS if form_type == "residence_hall" else INVENTORY_KEYS
    check_qty = (form_type != "residence_hall")

    if form_status == "checked-in":
        for field, label in TOP_FIELD_LABELS.items():
            if blank(data.get(field)):
                return f"{label} is required."

        for key in keys:
            if check_qty:
                qty = data.get(f"{key}_qty")
                if blank(qty):
                    return f"Quantity is required for every item ({key})."
                try:
                    if int(qty) < 0:
                        return f"Quantity cannot be negative ({key})."
                except (ValueError, TypeError):
                    return f"Quantity must be a whole number ({key})."

            if blank(data.get(f"{key}_checkin")):
                return f"Check-In condition is required for every item ({key})."

    elif form_status == "checked-out":
        if blank(data.get("checkout_date")):
            return "Check-Out date is required."

        for key in keys:
            if blank(data.get(f"{key}_checkout")):
                return f"Check-Out condition is required for every item ({key})."

    return None


@app.route("/save_backlog_form", methods=["POST"])
def save_backlog_form():
    conn = None
    crsr = None

    try:
        data = request.get_json()
        sign_in_id = data.get("sign_in_id")
        form_status = data.get("form_status", "draft")
        form_type = data.get("form_type", "apartment")
        if form_type not in ("apartment", "residence_hall"):
            form_type = "apartment"

        # Which item set / whether a quantity column applies for this form type.
        keys = RH_INVENTORY_KEYS if form_type == "residence_hall" else INVENTORY_KEYS
        has_qty = (form_type != "residence_hall")

        # Server-side required-field validation (mirrors the browser checks so a
        # blank/incomplete form can't be saved by bypassing the frontend).
        error = validate_backlog_form(data, form_status, form_type)
        if error:
            return jsonify({"status": "error", "message": error}), 400

        conn = get_db_connection()
        crsr = conn.cursor(buffered=True)

        crsr.execute("SELECT id FROM users WHERE sign_in_id=%s", [sign_in_id])
        user = crsr.fetchone()

        if not user:
            return jsonify({"status": "error", "message": "User not found"}), 404

        user_id = user[0]

        crsr.execute("SELECT id FROM backlog_forms WHERE user_id=%s", [user_id])
        exists = crsr.fetchone()

        if exists:
            if form_status == "checked-in":
                set_parts = [
                    "student_name=%s",
                    "dorm=%s",
                    "room_number=%s",
                    "present=%s",
                    "completion_date=%s",
                    "form_type=%s",
                    "form_status=%s"
                ]

                values = [
                    data.get("student_name"),
                    data.get("dorm"),
                    data.get("room_number"),
                    present_to_bool(data.get("present")),
                    data.get("completion_date") or None,
                    form_type,
                    form_status
                ]

                for key in keys:
                    if has_qty:
                        set_parts.append(f"{key}_qty=%s")
                        values.append(data.get(f"{key}_qty"))
                    set_parts.append(f"{key}_checkin=%s")
                    set_parts.append(f"{key}_wo_checkin=%s")
                    values.append(data.get(f"{key}_checkin"))
                    values.append(data.get(f"{key}_wo_checkin"))

                values.append(user_id)

                crsr.execute(f"""
                    UPDATE backlog_forms
                    SET {", ".join(set_parts)}
                    WHERE user_id=%s
                """, values)

            elif form_status == "checked-out":
                set_parts = ["form_status=%s", "checkout_date=%s"]
                values = [form_status, data.get("checkout_date") or None]

                for key in keys:
                    set_parts.append(f"{key}_checkout=%s")
                    set_parts.append(f"{key}_wo_checkout=%s")
                    values.append(data.get(f"{key}_checkout"))
                    values.append(data.get(f"{key}_wo_checkout"))

                values.append(user_id)

                crsr.execute(f"""
                    UPDATE backlog_forms
                    SET {", ".join(set_parts)}
                    WHERE user_id=%s
                """, values)

        else:
            columns = [
                "user_id",
                "student_id",
                "student_name",
                "dorm",
                "room_number",
                "present",
                "completion_date",
                "form_type",
                "form_status"
            ]

            values = [
                user_id,
                sign_in_id,
                data.get("student_name"),
                data.get("dorm"),
                data.get("room_number"),
                present_to_bool(data.get("present")),
                data.get("completion_date") or None,
                form_type,
                form_status
            ]

            for key in keys:
                if has_qty:
                    columns.append(f"{key}_qty")
                    values.append(data.get(f"{key}_qty"))
                columns.append(f"{key}_checkin")
                columns.append(f"{key}_wo_checkin")
                values.append(data.get(f"{key}_checkin"))
                values.append(data.get(f"{key}_wo_checkin"))

            placeholders = ", ".join(["%s"] * len(values))

            crsr.execute(f"""
                INSERT INTO backlog_forms ({", ".join(columns)})
                VALUES ({placeholders})
            """, values)

        conn.commit()

        # Generate a PDF once the form is submitted. The generator renders the
        # correct layout per form type (apartment vs residence-hall). The paper
        # form's header/footer extras (Key #, initials, RA signature) are Phase 2B.
        if form_status in ("checked-in", "checked-out"):
            generate_pdf(sign_in_id)

        return jsonify({"status": "success", "form_status": form_status})

    except Exception as e:
        logger.error(f"save_backlog_form error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if crsr:
            crsr.close()
        if conn:
            conn.close()


# ================= PHOTO UPLOAD =================

@app.route("/upload_photos/<sign_in_id>", methods=["POST"])
def upload_photos(sign_in_id):
    try:
        if "photos" not in request.files:
            return jsonify({"status": "error", "message": "No photos uploaded"}), 400

        files = request.files.getlist("photos")
        lengths = request.form.getlist("lengths")
        widths = request.form.getlist("widths")

        student_folder = os.path.join(UPLOAD_FOLDER, secure_filename(sign_in_id))
        os.makedirs(student_folder, exist_ok=True)

        saved_files = []

        for index, file in enumerate(files):
            if file.filename == "":
                continue

            filename = secure_filename(file.filename)
            file_path = os.path.join(student_folder, filename)
            file.save(file_path)
            saved_files.append(filename)

            length = ""
            width = ""

            if index < len(lengths):
                length = lengths[index]

            if index < len(widths):
                width = widths[index]

            measurement_file = os.path.join(student_folder, filename + "_measurements.txt")

            with open(measurement_file, "w") as f:
                f.write(f"Length: {length}\n")
                f.write(f"Width: {width}\n")

        return jsonify({
            "status": "success",
            "message": "Photos uploaded",
            "files": saved_files
        })

    except Exception as e:
        logger.error(f"upload_photos error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


# ================= GET FORM =================

@app.route("/get_backlog_form/<sign_in_id>", methods=["GET"])
def get_backlog_form(sign_in_id):
    conn = get_db_connection()
    crsr = conn.cursor(dictionary=True)

    crsr.execute("""
        SELECT bf.*
        FROM backlog_forms bf
        JOIN users u ON bf.user_id = u.id
        WHERE u.sign_in_id=%s
    """, [sign_in_id])

    form = crsr.fetchone()
    crsr.close()
    conn.close()

    if not form:
        return jsonify({"status": "error", "message": "Not found"}), 404

    if form.get("completion_date"):
        form["completion_date"] = str(form["completion_date"])

    return jsonify({"status": "success", "form": form})


# ================= ADMIN VIEW =================

@app.route("/admin/forms", methods=["GET"])
def get_all_forms():
    conn = get_db_connection()
    crsr = conn.cursor(dictionary=True)

    # sign_in_id comes along so the dashboard can link straight to a student's
    # form (e.g. the check-out queue) without going via PDF filenames.
    crsr.execute("""
        SELECT bf.*, u.sign_in_id
        FROM backlog_forms bf
        JOIN users u ON bf.user_id = u.id
    """)
    forms = crsr.fetchall()

    crsr.close()
    conn.close()

    for form in forms:
        if form.get("completion_date"):
            form["completion_date"] = str(form["completion_date"])
        if form.get("checkout_date"):
            form["checkout_date"] = str(form["checkout_date"])

    return jsonify({"status": "success", "forms": forms})


# ================= ADMIN PDF INFO =================

@app.route("/save_pdf_approval", methods=["POST"])
def save_pdf_approval():
    conn = None
    crsr = None
    try:
        data = request.get_json()
        filename = data.get("filename")
        keys_turned_in = data.get("keys_turned_in", False)
        admin_signature = data.get("admin_signature")
        completed = data.get("completed", False)

        if not filename:
            return jsonify({"status": "error", "message": "filename is required"}), 400
        if not admin_signature:
            return jsonify({"status": "error", "message": "Admin signature is required"}), 400

        conn = get_db_connection()
        crsr = conn.cursor()

        crsr.execute("""
            INSERT INTO pdf_approvals (filename, keys_turned_in, admin_signature, completed)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                keys_turned_in  = VALUES(keys_turned_in),
                admin_signature = VALUES(admin_signature),
                completed       = VALUES(completed),
                approved_at     = CURRENT_TIMESTAMP
        """, (filename, keys_turned_in, admin_signature, completed))

        conn.commit()
        return jsonify({"status": "success", "message": "PDF approval saved"})

    except Exception as e:
        logger.error(f"save_pdf_approval error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        if crsr:
            crsr.close()
        if conn:
            conn.close()


@app.route("/get_pdf_approval/<filename>", methods=["GET"])
def get_pdf_approval(filename):
    conn = get_db_connection()
    crsr = conn.cursor(dictionary=True)
    crsr.execute("SELECT * FROM pdf_approvals WHERE filename=%s", [filename])
    row = crsr.fetchone()
    crsr.close()
    conn.close()
    if not row:
        return jsonify({"status": "not_found"})
    return jsonify({"status": "success", "approval": row})


# ================= PDF =================

def generate_pdf(sign_in_id):
    conn = get_db_connection()
    crsr = conn.cursor(dictionary=True)
    crsr.execute("""
        SELECT bf.*
        FROM backlog_forms bf
        JOIN users u ON bf.user_id = u.id
        WHERE u.sign_in_id = %s
    """, [sign_in_id])
    data = crsr.fetchone()
    crsr.close()
    conn.close()

    if not data:
        return None

    file_name = f"{sign_in_id}_inventory.pdf"
    file_path = os.path.join(PDF_FOLDER, file_name)

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "title_style", parent=styles["Title"],
        fontSize=16, spaceAfter=4
    )
    header_style = ParagraphStyle(
        "header_style", parent=styles["Normal"],
        fontSize=10, textColor=colors.white
    )
    normal_style = ParagraphStyle(
        "normal_style", parent=styles["Normal"],
        fontSize=9
    )
    section_style = ParagraphStyle(
        "section_style", parent=styles["Normal"],
        fontSize=9, textColor=colors.white, fontName="Helvetica-Bold"
    )

    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        leftMargin=0.6*inch, rightMargin=0.6*inch,
        topMargin=0.7*inch, bottomMargin=0.7*inch
    )
    content = []

    content.append(Paragraph("Whitworth Housing — Room Inventory Form", title_style))
    content.append(Spacer(1, 6))

    info_table_data = [
        [Paragraph("<b>Student ID:</b>", normal_style), Paragraph(str(data.get("student_id", "") or ""), normal_style),
         Paragraph("<b>Student Name:</b>", normal_style), Paragraph(str(data.get("student_name", "") or ""), normal_style)],
        [Paragraph("<b>Dorm:</b>", normal_style), Paragraph(str(data.get("dorm", "") or ""), normal_style),
         Paragraph("<b>Room Number:</b>", normal_style), Paragraph(str(data.get("room_number", "") or ""), normal_style)],
        [Paragraph("<b>Check-In Date:</b>", normal_style), Paragraph(str(data.get("completion_date", "") or ""), normal_style),
         Paragraph("<b>Check-Out Date:</b>", normal_style), Paragraph(str(data.get("checkout_date", "") or ""), normal_style)],
        [Paragraph("<b>Form Status:</b>", normal_style), Paragraph(str(data.get("form_status", "") or ""), normal_style),
         Paragraph("", normal_style), Paragraph("", normal_style)],
        [Paragraph("<b>Present in Room:</b>", normal_style),
         Paragraph("Yes" if data.get("present") else ("No" if data.get("present") is False else ""), normal_style),
         Paragraph("", normal_style), Paragraph("", normal_style)],
    ]

    info_tbl = Table(info_table_data, colWidths=[1.2*inch, 2.2*inch, 1.3*inch, 2.5*inch])
    info_tbl.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.5, colors.grey),
        ("GRID", (0,0), (-1,-1), 0.3, colors.lightgrey),
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F4F7FA")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    content.append(info_tbl)
    content.append(Spacer(1, 12))

    NAV_BG = colors.HexColor("#1A2B4A")
    SEC_BG = colors.HexColor("#0D7C8F")
    ALT_BG = colors.HexColor("#EBF4F7")
    WHITE = colors.white
    GREY = colors.HexColor("#E2E8F0")

    # The residence-hall form has no Qty column and one flat item list; the
    # apartment form has a Qty column and BEDROOM/LIVING/BATHROOM sections.
    form_type = data.get("form_type") or "apartment"
    is_rh = (form_type == "residence_hall")

    if is_rh:
        inv_header = [
            Paragraph("<b>Item</b>", header_style),
            Paragraph("<b>Check-In (Move-In)</b>", header_style),
            Paragraph("<b>WO</b>", header_style),
            Paragraph("<b>Check-Out (Move-Out)</b>", header_style),
            Paragraph("<b>WO</b>", header_style),
        ]
    else:
        inv_header = [
            Paragraph("<b>Item</b>", header_style),
            Paragraph("<b>Qty</b>", header_style),
            Paragraph("<b>Check-In (Move-In)</b>", header_style),
            Paragraph("<b>WO</b>", header_style),
            Paragraph("<b>Check-Out (Move-Out)</b>", header_style),
            Paragraph("<b>WO</b>", header_style),
        ]

    ncols = len(inv_header)
    inv_rows = [inv_header]

    def section_row(label):
        cells = [Paragraph(f"<b>{label}</b>", section_style)]
        cells += [Paragraph("", section_style) for _ in range(ncols - 1)]
        return cells

    section_row_indices = []
    data_row_indices = []

    if is_rh:
        for item_name, key in RH_INVENTORY_ITEMS:
            checkin_val = str(data.get(f"{key}_checkin") or "—")
            checkin_wo_val = str(data.get(f"{key}_wo_checkin") or "—")
            checkout_val = str(data.get(f"{key}_checkout") or "—")
            checkout_wo_val = str(data.get(f"{key}_wo_checkout") or "—")

            data_row_indices.append(len(inv_rows))
            inv_rows.append([
                Paragraph(item_name, normal_style),
                Paragraph(checkin_val, normal_style),
                Paragraph(checkin_wo_val, normal_style),
                Paragraph(checkout_val, normal_style),
                Paragraph(checkout_wo_val, normal_style),
            ])

        col_widths = [1.8*inch, 2.0*inch, 0.6*inch, 2.0*inch, 0.6*inch]
    else:
        for section_name, section_items in INVENTORY_SECTIONS:
            section_row_indices.append(len(inv_rows))
            inv_rows.append(section_row(section_name))

            for item_name, key in section_items:
                checkin_val = str(data.get(f"{key}_checkin") or "—")
                checkin_wo_val = str(data.get(f"{key}_wo_checkin") or "—")
                checkout_val = str(data.get(f"{key}_checkout") or "—")
                checkout_wo_val = str(data.get(f"{key}_wo_checkout") or "—")

                data_row_indices.append(len(inv_rows))
                inv_rows.append([
                    Paragraph(item_name, normal_style),
                    Paragraph("", normal_style),
                    Paragraph(checkin_val, normal_style),
                    Paragraph(checkin_wo_val, normal_style),
                    Paragraph(checkout_val, normal_style),
                    Paragraph(checkout_wo_val, normal_style),
                ])

        col_widths = [1.6*inch, 0.5*inch, 1.7*inch, 0.5*inch, 1.7*inch, 0.5*inch]
    inv_tbl = Table(inv_rows, colWidths=col_widths, repeatRows=1)

    tbl_style_cmds = [
        ("BOX", (0,0), (-1,-1), 0.8, colors.HexColor("#334155")),
        ("GRID", (0,0), (-1,-1), 0.4, GREY),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("BACKGROUND", (0,0), (-1,0), NAV_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,0), 9),
    ]

    for idx in section_row_indices:
        tbl_style_cmds.append(("BACKGROUND", (0,idx), (-1,idx), SEC_BG))
        tbl_style_cmds.append(("TEXTCOLOR", (0,idx), (-1,idx), WHITE))
        tbl_style_cmds.append(("SPAN", (0,idx), (-1,idx)))
        tbl_style_cmds.append(("FONTNAME", (0,idx), (-1,idx), "Helvetica-Bold"))

    for i, idx in enumerate(data_row_indices):
        bg = ALT_BG if i % 2 == 0 else WHITE
        tbl_style_cmds.append(("BACKGROUND", (0,idx), (-1,idx), bg))

    inv_tbl.setStyle(TableStyle(tbl_style_cmds))
    content.append(inv_tbl)
    content.append(Spacer(1, 16))

    photo_folder = os.path.join(UPLOAD_FOLDER, secure_filename(sign_in_id))

    if os.path.exists(photo_folder):
        photos = os.listdir(photo_folder)

        image_photos = []
        for photo in photos:
            if photo.lower().endswith((".png", ".jpg", ".jpeg")):
                image_photos.append(photo)

        if image_photos:
            content.append(PageBreak())
            content.append(Paragraph("Uploaded Work Order Photos", title_style))
            content.append(Spacer(1, 10))

            for photo in image_photos:
                photo_path = os.path.join(photo_folder, photo)
                measurement_file = os.path.join(photo_folder, photo + "_measurements.txt")

                length = ""
                width = ""

                if os.path.exists(measurement_file):
                    with open(measurement_file, "r") as f:
                        lines = f.readlines()

                        if len(lines) > 0:
                            length = lines[0].replace("Length:", "").strip()

                        if len(lines) > 1:
                            width = lines[1].replace("Width:", "").strip()

                content.append(Paragraph(f"<b>{photo}</b>", normal_style))

                if length or width:
                    content.append(Paragraph(f"Length: {length} inches", normal_style))
                    content.append(Paragraph(f"Width: {width} inches", normal_style))

                content.append(Spacer(1, 6))

                img = Image(photo_path)
                img.drawWidth = 2.5 * inch
                img.drawHeight = 2.5 * inch

                content.append(img)
                content.append(Spacer(1, 12))

    conn2 = get_db_connection()
    crsr2 = conn2.cursor(dictionary=True)
    crsr2.execute("SELECT * FROM pdf_approvals WHERE filename=%s", [file_name])
    approval = crsr2.fetchone()
    crsr2.close()
    conn2.close()

    key_val = ""
    sig_img = None

    if approval:
        key_val = "Yes" if approval.get("keys_turned_in") else "No"

        sig_data = approval.get("admin_signature")

        if sig_data and str(sig_data).startswith("data:image"):
            try:
                header, encoded = sig_data.split(",", 1)
                sig_bytes = base64.b64decode(encoded)
                sig_img = Image(BytesIO(sig_bytes))
                sig_img.drawWidth = 2.2 * inch
                sig_img.drawHeight = 0.6 * inch
            except Exception as e:
                logger.error(f"Signature image error: {e}")
                sig_img = Paragraph("Signature saved but could not display", normal_style)

    if not sig_img:
        sig_img = Paragraph("______________________________", normal_style)

    admin_data = [
        [Paragraph("<b>Admin Review</b>", header_style),
         Paragraph("", header_style),
         Paragraph("", header_style),
         Paragraph("", header_style)],
        [Paragraph("<b>Key Received:</b>", normal_style),
         Paragraph(key_val or "_______", normal_style),
         Paragraph("<b>Admin Signature:</b>", normal_style),
         sig_img],
    ]

    admin_tbl = Table(admin_data, colWidths=[1.3*inch, 1.7*inch, 1.5*inch, 2.7*inch])
    admin_tbl.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.8, colors.HexColor("#334155")),
        ("GRID", (0,0), (-1,-1), 0.4, GREY),
        ("BACKGROUND", (0,0), (-1,0), NAV_BG),
        ("TEXTCOLOR", (0,0), (-1,0), WHITE),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BACKGROUND", (0,1), (-1,1), colors.HexColor("#F4F7FA")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
    ]))
    content.append(admin_tbl)

    doc.build(content)
    return file_name


@app.route("/pdfs/<filename>")
def get_pdf(filename):
    return send_from_directory(PDF_FOLDER, filename)


@app.route("/get_all_pdfs")
def get_all_pdfs():
    files = [
        file for file in os.listdir(PDF_FOLDER)
        if file.lower().endswith(".pdf")
    ]
    return jsonify({"files": files})


@app.route("/generate_pdf/<sign_in_id>", methods=["GET"])
def regenerate_pdf(sign_in_id):
    file_name = generate_pdf(sign_in_id)

    if not file_name:
        return jsonify({
            "status": "error",
            "message": "Could not generate PDF"
        }), 404

    return jsonify({
        "status": "success",
        "file": file_name
    })


# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
