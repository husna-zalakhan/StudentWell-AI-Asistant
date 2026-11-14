
import json
import streamlit as st

from ai_assistant import get_ai_turn
from auth import register_student, login_student
from database import (
    create_conversation,
    get_user_conversations,
    save_message,
    get_messages,
    get_connection,
)

# Load the trained ML model and its prediction function.
# If the model cannot load, the rest of the application can still run.
try:
    from stress_predictor import model as stress_model
    from stress_predictor import predict_stress

    STRESS_MODEL_AVAILABLE = True
    STRESS_MODEL_ERROR = None

except Exception as error:
    stress_model = None
    predict_stress = None
    STRESS_MODEL_AVAILABLE = False
    STRESS_MODEL_ERROR = str(error)


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="StudentWell AI",
    page_icon="🌱",
    layout="centered",
    initial_sidebar_state="expanded",
)


# =====================================================
# 2. CUSTOM DESIGN
# =====================================================

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(
            135deg,
            #F0F8FF,
            #E8F5F9,
            #EDF7F2
        );
    }

    .block-container {
        max-width: 850px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #243451;
    }

    [data-testid="stForm"] {
        background: white;
        padding: 30px;
        border: 1px solid #e3e8f0;
        border-radius: 18px;
        box-shadow: 0 8px 30px rgba(35, 52, 81, 0.08);
    }

    .stTextInput input {
        background-color: #f5f7fb;
        border: 1px solid #dce3ed;
        border-radius: 10px;
        min-height: 45px;
    }

    .stButton button,
    .stFormSubmitButton button {
        background: linear-gradient(100deg, #267f79, #5966a8);
        color: white !important;
        border: none;
        border-radius: 10px;
        min-height: 45px;
        font-weight: 600;
    }

    .stButton button:hover,
    .stFormSubmitButton button:hover {
        background: #1e6964;
        color: white !important;
        border: none;
    }

    [data-testid="stAlert"] {
        border-radius: 10px;
    }

    .footer {
        text-align: center;
        color: #8993a7;
        font-size: 12px;
        padding: 25px 0 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =====================================================
# 3. SESSION MANAGEMENT
# =====================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if "student" not in st.session_state:
    st.session_state.student = None

if "active_conversation_id" not in st.session_state:
    st.session_state.active_conversation_id = None

if "checkin_completed" not in st.session_state:
    st.session_state.checkin_completed = False

if "selected_mood" not in st.session_state:
    st.session_state.selected_mood = None


# =====================================================
# 4. APPLICATION HEADER
# =====================================================

def show_header():
    st.markdown(
        "<div style='text-align:center;'>",
        unsafe_allow_html=True,
    )

    st.title("🌱 StudentWell AI")
    st.caption("Your supportive space for student wellbeing")

    st.markdown(
        "<hr style='width:65px; border:2px solid #267f79;'>",
        unsafe_allow_html=True,
    )


# =====================================================
# 5. STUDENT REGISTRATION
# =====================================================

def show_registration():
    st.subheader("Create Your Account")

    st.caption(
        "Join StudentWell AI and take the first step "
        "toward supporting your wellbeing."
    )

    with st.form("registration_form"):

        full_name = st.text_input(
            "Full Name",
            placeholder="Enter your full name",
        )

        email = st.text_input(
            "Email Address",
            placeholder="Enter your email address",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Create a password (minimum 8 characters)",
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Enter your password again",
        )

        register_button = st.form_submit_button(
            "Create Account",
            use_container_width=True,
        )

    if register_button:

        if not full_name.strip() or not email.strip() or not password:
            st.error("Please complete all required fields.")

        elif "@" not in email or "." not in email.split("@")[-1]:
            st.error("Please enter a valid email address.")

        elif len(password) < 8:
            st.error("Your password must contain at least 8 characters.")

        elif password != confirm_password:
            st.error("Your passwords do not match.")

        else:
            success, message = register_student(
                full_name.strip(),
                email.strip(),
                password,
            )

            if success:
                st.success(message)
                st.info("Your account has been created. Please log in.")
            else:
                st.error(message)


# =====================================================
# 6. STUDENT LOGIN
# =====================================================

def show_login():

    st.subheader("Welcome Back!")

    st.caption("Log in to access your personal StudentWell AI space.")

    with st.form("login_form"):

        email = st.text_input(
            "Email Address",
            placeholder="Enter your registered email",
        )

        password = st.text_input(
            "Password",
            type="password",
            placeholder="Enter your password",
        )

        login_button = st.form_submit_button(
            "Login to Your Account",
            use_container_width=True,
        )

    if login_button:

        success, message, student = login_student(
            email.strip(),
            password,
        )

        if success:

            st.session_state.authenticated = True
            st.session_state.student = student
            st.session_state.active_conversation_id = None

            # Require a new check-in after each fresh login.
            st.session_state.checkin_completed = False
            st.session_state.selected_mood = None

            st.rerun()

        else:
            st.error(message)


# =====================================================
# 7. AUTHENTICATION INTERFACE
# =====================================================

def show_authentication():

    show_header()

    st.subheader("Welcome to StudentWell AI")

    st.write(
        "A supportive AI platform designed to help students "
        "manage their wellbeing and academic challenges."
    )

    register_tab, login_tab = st.tabs(
        ["Create Account", "Login"]
    )

    with register_tab:
        show_registration()

    with login_tab:
        show_login()


# =====================================================
# 8. CONVERSATION HELPERS
# =====================================================

def start_new_conversation(user_id):

    conversation_id = create_conversation(user_id)

    if conversation_id is not None:
        st.session_state.active_conversation_id = conversation_id
        st.rerun()

    else:
        st.error("Could not create a new conversation.")


def update_conversation_title(conversation_id, user_id, title):

    connection = None
    cursor = None

    try:
        connection = get_connection()

        if connection is None:
            return False

        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE conversations
            SET title = %s
            WHERE id = %s AND user_id = %s
            """,
            (title[:50], conversation_id, user_id),
        )

        connection.commit()
        return True

    except Exception as error:
        print("Title update error:", error)
        return False

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()


def decode_assistant_content(content):

    try:
        data = json.loads(content)

        if isinstance(data, dict) and isinstance(
            data.get("message"), str
        ):

            return {
                "message": data["message"],
                "options": data.get("options", []),
                "allow_multiple": data.get("allow_multiple", False),
                "stage": data.get("stage", "exploration"),
                "support_type": data.get("support_type", "general"),
                "enough_context": data.get("enough_context", False),
            }

    except (json.JSONDecodeError, TypeError):
        pass

    return {
        "message": content,
        "options": [],
        "allow_multiple": False,
        "stage": "exploration",
        "support_type": "general",
        "enough_context": False,
    }


def prepare_conversation_history(messages):

    history = []

    for message in messages:

        role = message["role"]
        content = message["content"]

        if role == "assistant":
            content = decode_assistant_content(content)["message"]

        if role in ("user", "assistant") and content:

            history.append({
                "role": role,
                "content": content,
            })

    return history


def process_student_message(
    user_id,
    conversation_id,
    messages,
    user_message,
):

    user_saved = save_message(
        user_id,
        conversation_id,
        "user",
        user_message,
    )

    if not user_saved:
        st.error("Your message could not be saved. Please try again.")
        return False

    if len(messages) <= 2:

        update_conversation_title(
            conversation_id,
            user_id,
            user_message,
        )

    history = prepare_conversation_history(messages)

    ai_turn = get_ai_turn(
        history,
        user_message,
    )

    if not isinstance(ai_turn, dict):

        ai_turn = {
            "message": str(ai_turn),
            "options": [],
            "allow_multiple": False,
            "stage": "exploration",
            "support_type": "general",
            "enough_context": False,
        }

    assistant_saved = save_message(
        user_id,
        conversation_id,
        "assistant",
        json.dumps(ai_turn, ensure_ascii=False),
    )

    if not assistant_saved:

        st.error(
            "Your message was saved, but the AI response "
            "could not be saved."
        )

        return False

    return True


# =====================================================
# 9. DAILY WELLBEING CHECK-IN
# =====================================================

def begin_mood_checkin(user_id, mood):

    conversation_id = create_conversation(user_id)

    if conversation_id is None:
        st.error("We couldn't start your check-in. Please try again.")
        return

    mood_message = f"My day was: {mood}"

    user_saved = save_message(
        user_id,
        conversation_id,
        "user",
        mood_message,
    )

    if not user_saved:
        st.error("Your check-in could not be saved. Please try again.")
        return

    ai_turn = get_ai_turn(
        [],
        mood_message,
    )

    assistant_saved = save_message(
        user_id,
        conversation_id,
        "assistant",
        json.dumps(ai_turn, ensure_ascii=False),
    )

    if not assistant_saved:

        st.error(
            "Your check-in was saved, but the AI response "
            "could not be saved."
        )

        return

    update_conversation_title(
        conversation_id,
        user_id,
        f"Daily check-in - {mood}",
    )

    st.session_state.selected_mood = mood
    st.session_state.checkin_completed = True
    st.session_state.active_conversation_id = conversation_id

    st.rerun()


def show_wellbeing_checkin(student, user_id):

    student_name = student.get("full_name", "there")

    st.title("Welcome to StudentWell AI 🌱")

    st.markdown(
        f"<h3 style='text-align:center; color:#267f79;'>"
        f"Hi {student_name}! 💚</h3>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "<p style='text-align:center; font-size:16px;'>"
        "It's good to have you here. This is your safe space to talk "
        "about your feelings, academic pressure, personal challenges, "
        "and everyday life. No judgment and no pressure. I'm here "
        "to listen and support you. 🌷"
        "</p>",
        unsafe_allow_html=True,
    )

    st.markdown("### How was your day? ☀️")

    st.caption(
        "Let's take a moment to check in with yourself. "
        "Choose the option that best describes your day."
    )

    day_options = [
        "🤩 Amazing!",
        "😊 Pretty good!",
        "🙂 Just okay",
        "😐 Nothing special / neutral",
        "😔 Not so good",
        "🥺 Really difficult",
    ]

    selected_mood = st.radio(
        "Tell me about your day:",
        day_options,
        index=None,
        key="daily_mood_selection",
    )

    if st.button(
        "Continue",
        use_container_width=True,
        disabled=selected_mood is None,
    ):

        begin_mood_checkin(user_id, selected_mood)


# =====================================================
# 10. ADAPTIVE AI OPTIONS
# =====================================================

def show_ai_options(
    ai_turn,
    user_id,
    conversation_id,
    messages,
):

    options = ai_turn.get("options", [])

    if not options:
        return

    st.markdown(
        "**You can choose an answer below or type your own response.**"
    )

    widget_id = f"{conversation_id}_{len(messages)}"

    if ai_turn.get("allow_multiple", False):

        selected_options = st.multiselect(
            "Select all that apply:",
            options,
            key=f"multi_choice_{widget_id}",
        )

        if st.button(
            "Send selected answers",
            key=f"send_multi_{widget_id}",
            use_container_width=True,
            disabled=not selected_options,
        ):

            answer = ", ".join(selected_options)

            if process_student_message(
                user_id,
                conversation_id,
                messages,
                answer,
            ):
                st.rerun()

    else:

        selected_option = st.radio(
            "Choose your answer:",
            options,
            index=None,
            key=f"single_choice_{widget_id}",
        )

        if st.button(
            "Send answer",
            key=f"send_single_{widget_id}",
            use_container_width=True,
            disabled=selected_option is None,
        ):

            if process_student_message(
                user_id,
                conversation_id,
                messages,
                selected_option,
            ):
                st.rerun()


# =====================================================
# 11. NEW: STRESS PREDICTION PAGE
# =====================================================

def show_stress_prediction_page():

    show_header()

    st.subheader("🎓 Academic Stress Prediction")

    st.write(
        "Enter your academic and lifestyle information "
        "to receive an experimental stress category prediction."
    )

    st.info(
        "Your answers are used to generate a prediction. "
        "This feature uses an academic dataset and is not a "
        "medical diagnosis or a validated assessment of your wellbeing."
    )

    # Stop the prediction form if the model could not be loaded.
    if not STRESS_MODEL_AVAILABLE:

        st.error(
            "The stress prediction model could not be loaded."
        )

        st.code(STRESS_MODEL_ERROR)
        return

    # Get the exact categorical values learned during model training.
    categorical_features = [
        "Gender",
        "Tuition",
        "Physical_Exercise",
        "Family_Income_Level",
        "University_Type",
    ]

    encoder = (
        stress_model
        .named_steps["preprocessor"]
        .named_transformers_["categorical"]
    )

    category_options = dict(
        zip(categorical_features, encoder.categories_)
    )

    st.markdown("### 1. Personal Information")

    with st.form("stress_prediction_form"):

        # Personal information
        age = st.number_input(
            "Age",
            min_value=19,
            max_value=24,
            value=21,
            step=1,
        )

        gender = st.selectbox(
            "Gender",
            category_options["Gender"],
        )

        university_type = st.selectbox(
            "University Type",
            category_options["University_Type"],
        )

        tuition = st.selectbox(
            "Do you receive tuition?",
            category_options["Tuition"],
        )

        family_income = st.selectbox(
            "Family Income Level",
            category_options["Family_Income_Level"],
        )

        st.markdown("### 2. Academic Information")

        study_hours = st.number_input(
            "Study Hours",
            min_value=0.0,
            max_value=24.0,
            value=4.0,
            step=0.5,
        )

        class_attendance = st.number_input(
            "Class Attendance (%)",
            min_value=0.0,
            max_value=100.0,
            value=70.0,
            step=1.0,
        )

        exam_frequency = st.number_input(
            "Exam Frequency",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=1.0,
        )

        assignment_load = st.number_input(
            "Assignment Load",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=1.0,
        )

        st.markdown("### 3. Lifestyle Information")

        sleep_hours = st.number_input(
            "Sleep Hours",
            min_value=0.0,
            max_value=24.0,
            value=6.0,
            step=0.5,
        )

        physical_exercise = st.selectbox(
            "Do you exercise?",
            category_options["Physical_Exercise"],
        )

        social_media_use = st.number_input(
            "Social Media Use",
            min_value=0.0,
            max_value=24.0,
            value=4.0,
            step=0.5,
        )

        screen_time = st.number_input(
            "Daily Screen Time",
            min_value=0.0,
            max_value=24.0,
            value=6.0,
            step=0.5,
        )

        st.markdown("### 4. Personal and Emotional Factors")

        peer_pressure = st.number_input(
            "Peer Pressure",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=1.0,
        )

        family_support = st.number_input(
            "Family Support",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=1.0,
        )

        anxiety_level = st.number_input(
            "Anxiety Level",
            min_value=0.0,
            max_value=10.0,
            value=5.0,
            step=1.0,
        )

        # Submit all 16 features together.
        predict_button = st.form_submit_button(
            "Predict My Stress Level",
            use_container_width=True,
        )

    if predict_button:

        # Build the input dictionary using the exact training column names.
        student_data = {
            "Age": age,
            "Gender": gender,
            "Study_Hours": study_hours,
            "Class_Attendance": class_attendance,
            "Tuition": tuition,
            "Exam_Frequency": exam_frequency,
            "Assignment_Load": assignment_load,
            "Sleep_Hours": sleep_hours,
            "Physical_Exercise": physical_exercise,
            "Social_Media_Use": social_media_use,
            "Screen_Time": screen_time,
            "Family_Income_Level": family_income,
            "Peer_Pressure": peer_pressure,
            "Family_Support": family_support,
            "Anxiety_Level": anxiety_level,
            "University_Type": university_type,
        }

        try:

            # Use the trained model to predict the stress category.
            prediction = predict_stress(student_data)

            st.markdown("---")
            st.subheader("Your Prediction Result")

            if prediction == "Low":

                st.success(
                    "🌱 Predicted Stress Category: LOW"
                )

                st.write(
                    "The model classified your responses "
                    "in the Low category."
                )

            elif prediction == "Medium":

                st.warning(
                    "🌿 Predicted Stress Category: MEDIUM"
                )

                st.write(
                    "The model classified your responses "
                    "in the Medium category."
                )

            else:

                st.error(
                    "💚 Predicted Stress Category: HIGH"
                )

                st.write(
                    "The model classified your responses "
                    "in the High category."
                )

            st.caption(
                "This result reflects patterns learned from the "
                "University Student Stress Dataset. It should not "
                "be treated as a clinical or medical assessment."
            )

        except Exception as error:

            st.error(
                "Something went wrong while generating "
                "your prediction."
            )

            st.exception(error)


# =====================================================
# 12. STUDENT DASHBOARD AND CHAT INTERFACE
# =====================================================

def open_previous_conversation(conversation_id):
    # This callback runs before Streamlit rebuilds the page.
    # Therefore, it is safe to update the navigation widget here.
    st.session_state.active_conversation_id = conversation_id
    st.session_state.dashboard_page = "AI Companion"


def show_dashboard():

    student = st.session_state.student
    user_id = student["id"]

    # Require a daily check-in before opening the dashboard.
    if not st.session_state.checkin_completed:
        show_wellbeing_checkin(student, user_id)
        st.stop()

    # ---------------- SIDEBAR ----------------

    st.sidebar.title("🌱 StudentWell AI")
    st.sidebar.caption(f"Welcome, {student['full_name']}!")
    st.sidebar.divider()

    # Initialize the navigation value before creating its widget.
    if "dashboard_page" not in st.session_state:
        st.session_state.dashboard_page = "AI Companion"

    # Navigation between the AI companion and stress prediction.
    selected_page = st.sidebar.radio(
        "Navigate",
        ["AI Companion", "Stress Prediction"],
        key="dashboard_page",
    )

    st.sidebar.divider()

    # Create a new conversation.
    if st.sidebar.button(
        "➕ New Chat",
        use_container_width=True,
    ):
        start_new_conversation(user_id)

    st.sidebar.subheader("Your Conversations")

    conversations = get_user_conversations(user_id)

    if conversations:

        for conversation in conversations:

            conversation_id = conversation["id"]
            title = conversation["title"] or "New Conversation"

            # The callback opens the selected conversation
            # and switches the page to AI Companion.
            st.sidebar.button(
                f"💬 {title}",
                key=f"conversation_{conversation_id}",
                use_container_width=True,
                on_click=open_previous_conversation,
                args=(conversation_id,),
            )

    else:
        st.sidebar.caption("No previous conversations yet.")

    st.sidebar.divider()
    st.sidebar.subheader("Your Account")

    st.sidebar.write(student["full_name"])
    st.sidebar.caption(student["email"])

    # Log out the current student.
    if st.sidebar.button(
        "Log Out",
        use_container_width=True,
    ):

        st.session_state.authenticated = False
        st.session_state.student = None
        st.session_state.active_conversation_id = None
        st.session_state.checkin_completed = False
        st.session_state.selected_mood = None

        st.rerun()

    # ---------------- STRESS PREDICTION PAGE ----------------

    if selected_page == "Stress Prediction":
        show_stress_prediction_page()
        return

    # ---------------- MAIN AI CHAT AREA ----------------

    show_header()

    st.subheader("Your StudentWell AI Companion")

    st.caption(
        "Talk about your wellbeing, academic pressure, "
        "personal challenges, and everyday life. 💚"
    )

    conversation_id = st.session_state.active_conversation_id

    if conversation_id is None:

        st.info(
            "Start a new conversation using the button "
            "in the sidebar."
        )

        st.markdown(
            """
            **I'm here to support you with:**

            - 🌱 Everyday wellbeing
            - 📚 Academic stress and study pressure
            - 📅 Study schedules and time management
            - 💭 Emotional and personal challenges
            - 💡 Motivation and learning
            """
        )

        return

    # Retrieve messages belonging to this student's conversation.
    messages = get_messages(user_id, conversation_id)

    last_assistant_turn = None

    # Display the conversation history.
    for index, message in enumerate(messages):

        role = message["role"]

        if role not in ("user", "assistant"):
            continue

        with st.chat_message(role):

            if role == "assistant":

                ai_turn = decode_assistant_content(
                    message["content"]
                )

                st.markdown(ai_turn["message"])

                if index == len(messages) - 1:
                    last_assistant_turn = ai_turn

            else:
                st.write(message["content"])

    # Display choices only for the latest AI response.
    if last_assistant_turn:

        show_ai_options(
            last_assistant_turn,
            user_id,
            conversation_id,
            messages,
        )

    # Students can always type their own answers.
    user_prompt = st.chat_input(
        "Or type your own answer..."
    )

    if user_prompt:

        if process_student_message(
            user_id,
            conversation_id,
            messages,
            user_prompt,
        ):
            st.rerun()

    # ---------------- ACCOUNT INFORMATION ----------------

    with st.expander("Account Information"):

        st.write("**Student ID:**", student["id"])
        st.write("**Full Name:**", student["full_name"])
        st.write("**Email:**", student["email"])


# =====================================================
# 13. APPLICATION FOOTER
# =====================================================

def show_footer():

    st.markdown(
        """
        <div class="footer">
            StudentWell AI © 2026<br>
            Supporting student wellbeing through AI
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================================
# 14. MAIN APPLICATION
# =====================================================

if st.session_state.authenticated:

    show_dashboard()

else:

    show_authentication()

show_footer()
