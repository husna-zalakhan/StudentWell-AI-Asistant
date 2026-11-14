
import bcrypt
import mysql.connector
from database import get_connection


# ==========================================
# 1. STUDENT REGISTRATION
# ==========================================

def register_student(full_name, email, password):

    # 1. Validate student information
    full_name = full_name.strip()
    email = email.strip().lower()

    if not full_name or not email or not password:
        return False, "All fields are required."

    if len(password) < 8:
        return False, "Password must contain at least 8 characters."

    # 2. Securely hash the password
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    conn = None
    cursor = None

    try:
        # 3. Connect to MySQL
        conn = get_connection()
        cursor = conn.cursor()

        # 4. Save student information
        query = """
            INSERT INTO users (full_name, email, password_hash)
            VALUES (%s, %s, %s)
        """

        cursor.execute(
            query,
            (full_name, email, password_hash)
        )

        conn.commit()

        return True, "Registration successful!"

    except mysql.connector.IntegrityError:
        return False, "This email is already registered."

    except mysql.connector.Error as error:
        print("Database error:", error)
        return False, "Registration failed. Please try again."

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()


# ==========================================
# 2. STUDENT LOGIN
# ==========================================

def login_student(email, password):

    # 1. Clean email
    email = email.strip().lower()

    if not email or not password:
        return False, "Email and password are required.", None

    conn = None
    cursor = None

    try:
        # 2. Connect to MySQL
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # 3. Find student using email
        query = """
            SELECT id, full_name, email, password_hash
            FROM users
            WHERE email = %s
        """

        cursor.execute(query, (email,))
        student = cursor.fetchone()

        # 4. Check if student exists
        if student is None:
            return False, "Invalid email or password.", None

        # 5. Verify password
        stored_hash = student["password_hash"].encode("utf-8")

        if bcrypt.checkpw(password.encode("utf-8"), stored_hash):

            student.pop("password_hash")

            return True, "Login successful!", student

        return False, "Invalid email or password.", None

    except mysql.connector.Error as error:
        print("Login database error:", error)
        return False, "Login failed. Please try again.", None

    finally:
        if cursor:
            cursor.close()

        if conn:
            conn.close()
