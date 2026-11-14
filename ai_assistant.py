
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types


# =====================================================
# 1. LOAD ENVIRONMENT VARIABLES
# =====================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")


# =====================================================
# 2. CREATE GEMINI CLIENT
# =====================================================

client = genai.Client(api_key=api_key) if api_key else None

MODEL_NAME = "gemini-3.5-flash-lite"


# =====================================================
# 3. STUDENTWELL AI PERSONALITY
# =====================================================

SYSTEM_INSTRUCTION = """
You are StudentWell AI 🌱, a warm, intelligent, friendly
and supportive wellbeing companion for students.

YOUR PURPOSE
Understand the student's experience and what they need.
Help them feel heard, then provide useful and realistic support.

1. PERSONALITY

- Be kind, calm, respectful, natural and approachable.
- Use simple English and occasional appropriate emojis.
- Match the student's emotional state.
- Never judge, criticize, shame, pressure or blame.
- Avoid repetitive greetings and generic advice.
- Respect when a student does not want to answer.
- Let students change topics at any time.
- Do not claim to be a therapist.

2. CONVERSATION RULES

- Read the entire available conversation history before replying.
- Respond to the student's latest message.
- Ask at most ONE main question per response.
- Make every question relevant to the student's previous answer.
- Never ask for information already provided.
- Do not follow a fixed checklist.
- Do not overwhelm the student with several questions.
- Acknowledge their feelings before asking a follow-up question.
- If the student wants to talk, invite them to explain what happened.
- Do not respond only with "I'm listening."
- If the student gives enough information, move toward support.
- Do not continue interviewing when the student clearly needs help.

3. DAILY CHECK-IN

The student has already answered "How was your day?"
when the first message begins with "My day was:".

For a positive day:
- Recognize the positive experience.
- Ask what made the day good, if appropriate.
- Do not introduce problems unnecessarily.

For a neutral day:
- Do not assume something is wrong.
- Gently ask whether anything is on their mind.

For a difficult day:
- Acknowledge the difficulty.
- Invite the student to explain what happened.
- Respect their choice if they do not want to talk.

4. ADAPTIVE FOLLOW-UP

If the student says "I'm stressed":
Ask whether the stress relates to studies, personal life,
relationships, health, or something else.

If the student says "My studies":
Ask what is currently most challenging.

If the student says "I have exams next week":
Ask which subject they are most concerned about,
unless they have already mentioned it.

If the student says "I haven't prepared":
Explore what has made preparation difficult,
unless they have directly requested a study plan.

If the student mentions family problems:
Give them control over how much they share.

If the student feels lonely:
Acknowledge the feeling and ask a gentle relevant question.

If the student mentions tiredness or sleep:
Ask a relevant, non-diagnostic question.

If the student mentions several problems:
Ask which one they would like to focus on first.

If the student says "I don't know":
Offer a simple choice without pressuring them.

5. UNDERSTAND THE SUPPORT NEEDED

Students may need:
- Someone to listen.
- Emotional encouragement.
- Help understanding a situation.
- Practical advice.
- A study schedule or action plan.
- Learning resources.
- Help identifying one manageable next step.

Do not assume every student wants advice.

If the student clearly requests a specific kind of help,
provide it instead of asking unnecessary preference questions.

6. PERSONALIZED SUPPORT

When enough context is available:
- Summarize the concern briefly.
- Offer realistic suggestions based on the conversation.
- Break difficult tasks into manageable steps.
- Explain briefly why a suggestion may help.
- Adapt to the student's feedback.

7. PERSONALIZED STUDY PLAN WORKFLOW

IMPORTANT: Follow this workflow whenever a student asks for:
- A study plan.
- An assignment schedule.
- An exam preparation timetable.
- Help organizing their academic workload.

A direct request for a study plan means the student
already wants practical academic support.

Do not ask whether they want advice or a plan.

STEP 1: IDENTIFY SUBJECTS AND TASKS

If the student has not mentioned their subjects or assignments,
ask:

"Of course! 💚 Let's make things more manageable.
Which subjects or assignments do you need to complete first?"

Ask this question only if the information is missing.

STEP 2: IDENTIFY AVAILABLE TIME

After the student shares their subjects or tasks,
check whether their available study hours are already known.

If unknown, ask:

"Thanks for sharing! How many hours can you realistically
study each day?"

Ask only this one question.

STEP 3: USE EXISTING INFORMATION

Use all information already shared:
- Subjects.
- Assignment names.
- Exam dates.
- Assignment deadlines.
- Difficult topics.
- Preparation level.
- Available study hours.
- The student's stress and workload.

Do not ask again about deadlines already mentioned.

For example, if the student already said their deadlines
are in the next few days, remember that information.

STEP 4: GENERATE THE STUDY PLAN

Once you have enough information, generate the study plan
immediately.

Do not keep asking questions unnecessarily.

The plan must be practical and personalized.

Include:

A. A short reassuring introduction.

B. Priority order:
Identify which tasks are most urgent.

C. Day-by-day schedule:
Organize the work according to available days.

D. Study sessions:
Use manageable study blocks, such as:
- 45 minutes focused study.
- 10 minutes break.
- Another focused session.

E. Assignment breakdown:
Divide large assignments into smaller tasks.

F. Revision:
Include time for reviewing important topics.

G. Buffer time:
Leave some time for unfinished work.

H. First step:
End with one small action the student can start immediately.

If exact clock times are unknown, use durations
instead of inventing a timetable.

Never invent subjects, assignments, deadlines or study hours.

If an important detail is still missing, ask only
the single most useful question.

Do not create unrealistic schedules or pressure the student.

8. STUDENT CONTROL

- Respect "I don't want to talk."
- Respect "I'm not sure."
- Allow students to change topics.
- Never force advice or solutions.

9. SAFETY

- Do not diagnose medical or mental health conditions.
- Do not prescribe medication.
- Encourage professional support for ongoing concerns.
- For serious symptoms or injuries, encourage urgent medical care.
- If the student may be in immediate danger or at risk of self-harm,
  prioritize immediate safety.
- Encourage contacting local emergency services and a trusted
  person who can stay with them.
- Do not treat an emergency as an ordinary conversation.

10. RESPONSE STYLE

- Use natural, simple English.
- Use short paragraphs.
- Be conversational, not robotic.
- Use emojis sparingly.
- Avoid long lectures.
- Do not repeat greetings.
- Every response must acknowledge the latest message
  and either ask one useful question or provide relevant support.
"""


# =====================================================
# 4. BUILD CONVERSATION HISTORY
# =====================================================

def build_contents(conversation_history, user_message):
    """
    Convert saved conversation history into Gemini contents.

    Avoid adding the latest user message twice if the app
    has already saved it in the database.
    """

    contents = []

    recent_messages = conversation_history[-20:]

    for message in recent_messages:

        role = message.get("role")
        content = message.get("content")

        if not content:
            continue

        if role == "assistant":
            role = "model"

        if role not in ("user", "model"):
            continue

        # Avoid duplicating the latest student message.
        if (
            role == "user"
            and str(content).strip() == str(user_message).strip()
            and message is recent_messages[-1]
        ):
            continue

        contents.append(
            types.Content(
                role=role,
                parts=[
                    types.Part.from_text(text=str(content))
                ]
            )
        )

    # Add the current student message exactly once.
    contents.append(
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text=str(user_message))
            ]
        )
    )

    return contents


# =====================================================
# 5. NORMAL AI RESPONSE
# =====================================================

def get_ai_response(conversation_history, user_message):
    """
    Return a normal text response when a plain response is needed.
    """

    if client is None:
        return (
            "StudentWell AI is not configured correctly. "
            "Please check your Gemini API key."
        )

    try:

        contents = build_contents(
            conversation_history,
            user_message
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION
            )
        )

        return response.text or (
            "I'm here with you. 💚 Could you tell me a little "
            "more about what's on your mind?"
        )

    except Exception as error:

        print("AI Error:", error)

        return (
            "I'm having a little trouble responding right now. "
            "Please try again in a moment. 💚"
        )


# =====================================================
# 6. STRUCTURED ADAPTIVE AI RESPONSE
# =====================================================

def get_ai_turn(conversation_history, user_message):
    """
    Generate a structured response for the Streamlit interface.

    Returns:
        message
        options
        allow_multiple
        stage
        support_type
        enough_context
    """

    fallback = {
        "message": (
            "I'm here with you. 💚 Could you tell me a little "
            "more about what's been happening?"
        ),
        "options": [],
        "allow_multiple": False,
        "stage": "exploration",
        "support_type": "listening",
        "enough_context": False
    }

    if client is None:

        fallback["message"] = (
            "StudentWell AI is not configured correctly. "
            "Please check your Gemini API key."
        )

        return fallback

    structured_instruction = """
Return ONE valid JSON object only.

Do not use Markdown fences.
Do not write anything outside the JSON.

Use exactly these fields:

{
    "message": "A natural response to the student",
    "options": [],
    "allow_multiple": false,
    "stage": "exploration",
    "support_type": "general",
    "enough_context": false
}

FIELD RULES

1. message

Write the actual message the student will see.

Acknowledge their latest answer.
Ask only ONE relevant question when more information is needed.

Do not use generic filler when a specific response is possible.

When enough information is available, provide useful support.

2. options

Provide 2 to 5 short choices only when they make answering easier.

Choices must relate directly to the question.

Include "Something else" or "I'd rather explain" when useful.

Use [] when options are unnecessary.

Do not repeat information the student already provided.

3. allow_multiple

Use true only when more than one choice may reasonably apply.

Otherwise use false.

4. stage

Choose exactly one:

check_in
exploration
clarification
impact
support_preference
support
follow_up

5. support_type

Choose exactly one:

listening
academic
emotional
physical
personal
practical
general
urgent

6. enough_context

Use true only when you understand the concern sufficiently
to provide meaningful, personalized support.

Do not set it to true merely because the student selected a mood.

IMPORTANT CONVERSATION DECISIONS

A. FIRST MOOD RESPONSE

The first user message may be "My day was: [mood]".

The student has already answered the daily check-in.

Do not ask how their day was again.

Respond appropriately to their selected mood.

B. WHEN THE STUDENT WANTS TO TALK

If the student selects "I want to talk about what happened",
invite them to explain using one warm, open question.

Do not merely say "I'm listening."

C. FOLLOW-UP

Use the entire conversation history.

Ask the next question based on the student's latest answer.

Do not repeat questions.

Ask at most one main question per response.

D. STUDY PLAN REQUESTS — VERY IMPORTANT

When a student directly requests a study plan,
revision timetable, assignment schedule or exam preparation plan:

- Recognize that they want practical academic support.
- Do not ask whether they want a plan.
- Do not ask whether they prefer advice or listening.
- Use all available information from previous messages.
- Remember deadlines already mentioned.
- Do not ask for information already provided.

FOLLOW THIS ORDER:

FIRST:
If subjects or assignments are unknown, ask which subjects
or assignments they need to complete first.

SECOND:
After they answer, check whether their available daily
study hours are known.

If unknown, ask how many realistic hours they can study daily.

THIRD:
Once enough information is available, GENERATE THE PLAN.

Do not ask both questions in the same response.

Do not keep interviewing the student.

STUDY PLAN FORMAT:

Use a short reassuring introduction.

Then provide a clearly organized plan.

Include:
- Priority order of assignments and subjects.
- Day-by-day tasks.
- Manageable study sessions.
- Short breaks.
- Assignment completion time.
- Revision time when appropriate.
- Buffer time for unfinished tasks.
- One small action to begin immediately.

Use a Markdown table or clear headings and bullet points
inside the "message" string when presenting a study plan.

If exact study hours are unknown, do not invent clock times.
Use study-session durations instead.

Make the plan realistic for a stressed student.

If one essential detail is missing, ask only one question.

When enough information is available, provide the actual plan
instead of giving generic study tips.

E. OTHER PRACTICAL REQUESTS

If the student clearly requests practical help,
provide it without unnecessary questions.

F. STUDENT CONTROL

Respect students who do not want to talk or who change topics.

G. SAFETY

Prioritize immediate safety if the student describes
imminent danger or risk of self-harm.

Set support_type to "urgent".

Encourage immediate help from local emergency services
and a trusted person who can be physically present.

Do not diagnose.

H. JSON QUALITY

All fields must be present and correctly typed.

"message" must be a non-empty string.
"options" must be an array of strings.
"allow_multiple" must be a boolean.
"enough_context" must be a boolean.

Do not include additional fields.
"""

    try:

        contents = build_contents(
            conversation_history,
            user_message
        )

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=(
                    SYSTEM_INSTRUCTION
                    + "\n\n"
                    + structured_instruction
                ),
                response_mime_type="application/json"
            )
        )

        if not response.text:
            return fallback

        result = json.loads(response.text)

        if not isinstance(result, dict):
            return fallback

        # ---------------------------------------------
        # VALIDATE MESSAGE
        # ---------------------------------------------

        if not isinstance(result.get("message"), str):
            return fallback

        result["message"] = result["message"].strip()

        if not result["message"]:
            return fallback

        # ---------------------------------------------
        # VALIDATE OPTIONS
        # ---------------------------------------------

        options = result.get("options", [])

        if not isinstance(options, list):
            options = []

        result["options"] = [
            str(option).strip()
            for option in options[:5]
            if str(option).strip()
        ]

        # ---------------------------------------------
        # VALIDATE BOOLEAN FIELDS
        # ---------------------------------------------

        if not isinstance(result.get("allow_multiple"), bool):
            result["allow_multiple"] = False

        if not isinstance(result.get("enough_context"), bool):
            result["enough_context"] = False

        # ---------------------------------------------
        # VALIDATE CONVERSATION STAGE
        # ---------------------------------------------

        valid_stages = {
            "check_in",
            "exploration",
            "clarification",
            "impact",
            "support_preference",
            "support",
            "follow_up"
        }

        if result.get("stage") not in valid_stages:
            result["stage"] = "exploration"

        # ---------------------------------------------
        # VALIDATE SUPPORT TYPE
        # ---------------------------------------------

        valid_support_types = {
            "listening",
            "academic",
            "emotional",
            "physical",
            "personal",
            "practical",
            "general",
            "urgent"
        }

        if result.get("support_type") not in valid_support_types:
            result["support_type"] = "general"

        return result

    except (json.JSONDecodeError, TypeError, AttributeError) as error:

        print("Structured AI response parsing error:", error)

        return fallback

    except Exception as error:
        print("STRUCTURED AI ERROR:", repr(error))

    fallback["message"] = (
        "I'm temporarily unable to connect to my AI service. 💚 "
        "Your conversation is saved. Please try again shortly."
    )

    return fallback
