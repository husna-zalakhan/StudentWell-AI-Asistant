import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()


# ==========================================
# 1. DATABASE SETTINGS
# ==========================================

def get_setting(key, default=None):
    value = os.getenv(key)

    if value:
        return value

    # Read from Streamlit Community Cloud Secrets
    try:
        import streamlit as st
        return st.secrets.get(key, default)
    except Exception:
        return default


# ==========================================
# 2. DATABASE CONNECTION
# ==========================================

def get_connection():
    print("1. Reading database settings...")

    try:
        print("2. Connecting to PostgreSQL...")

        connection = psycopg2.connect(
            host=get_setting("DB_HOST"),
            user=get_setting("DB_USER"),
            password=get_setting("DB_PASSWORD"),
            dbname=get_setting("DB_NAME"),
            port=int(get_setting("DB_PORT", "12946")),
            sslmode="require",
            connect_timeout=10
        )

        print("3. PostgreSQL connection successful!")
        return connection

    except psycopg2.Error as error:
        print("PostgreSQL error:", error)
        return None


# ==========================================
# 3. CREATE A NEW CONVERSATION
# ==========================================

def create_conversation(user_id, title="New Conversation"):
    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return None

        cursor = connection.cursor()

        query = """
            INSERT INTO conversations (user_id, title)
            VALUES (%s, %s)
            RETURNING id
        """

        cursor.execute(query, (user_id, title))

        conversation_id = cursor.fetchone()[0]

        connection.commit()

        return conversation_id

    except psycopg2.Error as error:
        if connection:
            connection.rollback()

        print("Error creating conversation:", error)
        return None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==========================================
# 4. GET USER CONVERSATIONS
# ==========================================

def get_user_conversations(user_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return []

        cursor = connection.cursor(
            cursor_factory=RealDictCursor
        )

        query = """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """

        cursor.execute(query, (user_id,))

        return cursor.fetchall()

    except psycopg2.Error as error:
        print("Error retrieving conversations:", error)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==========================================
# 5. SAVE A MESSAGE
# ==========================================

def save_message(user_id, conversation_id, role, content):
    connection = None
    cursor = None

    try:
        if role not in ("user", "assistant"):
            return False

        connection = get_connection()

        if connection is None:
            return False

        cursor = connection.cursor()

        # Verify conversation ownership
        cursor.execute(
            """
            SELECT id FROM conversations
            WHERE id = %s AND user_id = %s
            """,
            (conversation_id, user_id)
        )

        if cursor.fetchone() is None:
            return False

        query = """
            INSERT INTO messages (conversation_id, role, content)
            VALUES (%s, %s, %s)
        """

        cursor.execute(
            query,
            (conversation_id, role, content)
        )

        connection.commit()
        return True

    except psycopg2.Error as error:
        if connection:
            connection.rollback()

        print("Error saving message:", error)
        return False

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==========================================
# 6. GET CONVERSATION MESSAGES
# ==========================================

def get_messages(user_id, conversation_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return []

        cursor = connection.cursor(
            cursor_factory=RealDictCursor
        )

        query = """
            SELECT m.id, m.role, m.content, m.created_at
            FROM messages m
            INNER JOIN conversations c
                ON m.conversation_id = c.id
            WHERE c.id = %s AND c.user_id = %s
            ORDER BY m.created_at ASC, m.id ASC
        """

        cursor.execute(query, (conversation_id, user_id))

        return cursor.fetchall()

    except psycopg2.Error as error:
        print("Error retrieving messages:", error)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
