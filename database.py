
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()


# ==========================================
# 1. DATABASE CONNECTION
# ==========================================

def get_connection():
    print("1. Reading database settings...")

    try:
        print("2. Connecting to MySQL...")

        connection = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=3306,
            connection_timeout=10,
            use_pure=True
        )

        print("3. Connection successful!")
        return connection

    except mysql.connector.Error as error:
        print("MySQL error:", error)
        return None


# ==========================================
# 2. CREATE A NEW CONVERSATION
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
        """

        cursor.execute(query, (user_id, title))
        connection.commit()

        return cursor.lastrowid

    except mysql.connector.Error as error:
        print("Error creating conversation:", error)
        return None

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==========================================
# 3. GET USER CONVERSATIONS
# ==========================================

def get_user_conversations(user_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return []

        cursor = connection.cursor(dictionary=True)

        query = """
            SELECT id, title, created_at, updated_at
            FROM conversations
            WHERE user_id = %s
            ORDER BY updated_at DESC
        """

        cursor.execute(query, (user_id,))

        return cursor.fetchall()

    except mysql.connector.Error as error:
        print("Error retrieving conversations:", error)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==========================================
# 4. SAVE A MESSAGE
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

        # Verify that this conversation belongs to the user
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

    except mysql.connector.Error as error:
        print("Error saving message:", error)
        return False

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()


# ==========================================
# 5. GET CONVERSATION MESSAGES
# ==========================================

def get_messages(user_id, conversation_id):
    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return []

        cursor = connection.cursor(dictionary=True)

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

    except mysql.connector.Error as error:
        print("Error retrieving messages:", error)
        return []

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()
