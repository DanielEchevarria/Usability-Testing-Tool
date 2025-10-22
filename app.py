import streamlit as st
import pandas as pd
import time
import os
import uuid
from datetime import datetime

# -----------------------------
# Data setup
# -----------------------------
DATA_FOLDER = "data"
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

CONSENT_CSV = os.path.join(DATA_FOLDER, "consent_data.csv")
DEMOGRAPHIC_CSV = os.path.join(DATA_FOLDER, "demographic_data.csv")
TASK_CSV = os.path.join(DATA_FOLDER, "task_data.csv")
EXIT_CSV = os.path.join(DATA_FOLDER, "exit_data.csv")

# -----------------------------
# Helpers
# -----------------------------
def save_to_csv(data_dict, csv_file):
    df_new = pd.DataFrame([data_dict])
    if not os.path.isfile(csv_file):
        df_new.to_csv(csv_file, mode="w", header=True, index=False)
    else:
        df_new.to_csv(csv_file, mode="a", header=False, index=False)

def load_from_csv(csv_file):
    if os.path.isfile(csv_file):
        return pd.read_csv(csv_file)
    else:
        return pd.DataFrame()

def now_iso():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

def ensure_participant():
    """Ensure a participant_id exists in session state."""
    if "participant_id" not in st.session_state or not st.session_state["participant_id"]:
        st.session_state["participant_id"] = f"P-{str(uuid.uuid4())[:8]}"

def require_consent_warning():
    st.warning("Please complete and submit consent first. Data will only be recorded after consent is provided.")

LIKERT_5 = {
    "1 - Strongly Disagree": 1,
    "2 - Disagree": 2,
    "3 - Neutral": 3,
    "4 - Agree": 4,
    "5 - Strongly Agree": 5,
}

LIKERT_5_SIMPLE = {
    "1 - Very Poor": 1,
    "2 - Poor": 2,
    "3 - Fair": 3,
    "4 - Good": 4,
    "5 - Excellent": 5,
}

TASK_SUCCESS_OPTIONS = ["Success", "Partial", "Fail", "Abandoned"]

DEFAULT_TASKS = [
    {
        "name": "Task 1: Find an item",
        "description": "Imagine you want to find the price of 'Product X' on the website. Locate the product page and identify the listed price."
    },
    {
        "name": "Task 2: Create an account",
        "description": "Register a new user account with a mock email. Do not use personal information."
    },
    {
        "name": "Task 3: Change a setting",
        "description": "Locate the Settings page and switch the theme to Dark Mode."
    }
]

# -----------------------------
# App
# -----------------------------
def main():
    st.set_page_config(page_title="Usability Testing Tool", page_icon="🧪", layout="wide")
    st.title("Usability Testing Tool")

    # Sidebar: session & navigation info
    with st.sidebar:
        ensure_participant()
        st.write("Session")
        st.text_input("Participant ID", key="participant_id")
        st.toggle("Observer Mode", value=True, key="observer_mode", help="If enabled, notes fields are labeled as observer notes.")
        st.info("Tip: You can replace questions and tasks with your own to match the target app.")

        st.write("---")
        st.caption("For assignment setup and how to export the one-page overview to PDF, see the README.")

    home, consent, demographics, tasks, exit_survey, report = st.tabs(
        ["Home", "Consent", "Demographics", "Task", "Exit Questionnaire", "Report"]
    )

    # -----------------------------
    # Home
    # -----------------------------
    with home:
        st.header("Introduction")
        st.write(
            """
            Welcome to the Usability Testing Tool for HCI.

            This app guides a participant through a simple usability test flow and records data for later analysis. In this demonstration you will:
            1) Provide consent for data collection.
            2) Fill out a short demographic questionnaire.
            3) Complete example tasks with timing and outcome recording.
            4) Answer an exit questionnaire (Likert + open-ended).
            5) View a summary report with simple visualizations.
            """
        )
        st.markdown(
            "- Customize the consent text, questions, tasks, and report to fit your specific study.\n"
            "- Data are saved to CSV files in the `data/` folder.\n"
            "- In Project 3, you will plug in your real tasks and test your Project 2 app."
        )

    # -----------------------------
    # Consent
    # -----------------------------
    with consent:
        st.header("Consent Form")

        consent_text = """
        Purpose: You are invited to participate in a usability study to evaluate the usability of a prototype or application.
        Procedures: You will complete short tasks and answer survey questions. The session is expected to last no more than 15 minutes.
        Risks & Benefits: Minimal risk. Your feedback will help improve the design.
        Voluntary Participation: Your participation is voluntary. You may withdraw at any time without penalty.
        Data & Privacy: We will collect anonymized task performance and questionnaire responses. Do not enter personal or sensitive data.
        Contact: If you have questions about this study, contact the researcher/instructor.

        By checking the box below, you confirm that you have read and agree to the terms above and consent to participate in this usability study.
        """
        with st.expander("Read Consent Details", expanded=True):
            st.write(consent_text)

        consent_given = st.checkbox("I have read and agree to the consent terms.")
        consent_name = st.text_input("Participant (optional display name)", value="")
        if st.button("Submit Consent"):
            if not consent_given:
                st.warning("You must agree to the consent terms before proceeding.")
            else:
                ensure_participant()
                data_dict = {
                    "timestamp": now_iso(),
                    "participant_id": st.session_state["participant_id"],
                    "consent_given": True,
                    "display_name": consent_name,
                }
                save_to_csv(data_dict, CONSENT_CSV)
                st.success("Consent recorded. You may proceed to the Demographics tab.")

    # -----------------------------
    # Demographics
    # -----------------------------
    with demographics:
        st.header("Demographic Questionnaire")

        with st.form("demographic_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Name or Alias (optional)", "")
                age = st.number_input("Age", min_value=13, max_value=120, value=25, step=1)
                gender = st.selectbox("Gender (optional)", ["Prefer not to say", "Female", "Male", "Non-binary", "Self-describe"])
                if gender == "Self-describe":
                    gender = st.text_input("Please self-describe your gender")
            with col2:
                occupation = st.text_input("Occupation/Role", "Student")
                education = st.selectbox("Highest Education", ["Prefer not to say", "High School", "Associate", "Bachelor", "Master", "Doctorate", "Other"])
                country = st.text_input("Country/Region (optional)", "")

            familiarity_label = st.select_slider(
                "Familiarity with similar tools",
                options=list(LIKERT_5_SIMPLE.keys()),
                value="3 - Fair"
            )
            familiarity = LIKERT_5_SIMPLE[familiarity_label]

            submitted = st.form_submit_button("Submit Demographics")
            if submitted:
                # Ensure consent exists before saving demographics
                consent_df = load_from_csv(CONSENT_CSV)
                ensure_participant()
                pid = st.session_state["participant_id"]
                if consent_df.empty or pid not in set(consent_df.get("participant_id", [])):
                    require_consent_warning()
                else:
                    data_dict = {
                        "timestamp": now_iso(),
                        "participant_id": pid,
                        "name": name,
                        "age": int(age),
                        "gender": gender,
                        "occupation": occupation,
                        "education": education,
                        "country": country,
                        "familiarity_1to5": familiarity,
                    }
                    save_to_csv(data_dict, DEMOGRAPHIC_CSV)
                    st.success("Demographic data saved.")

    # -----------------------------
    # Tasks
    # -----------------------------
    with tasks:
        st.header("Task Page")
        st.write("Please select a task and record your experience completing it.")

        # Select a task
        task_names = [t["name"] for t in DEFAULT_TASKS]
        selected_task = st.selectbox("Select Task", task_names)
        task_def = next((t for t in DEFAULT_TASKS if t["name"] == selected_task), DEFAULT_TASKS[0])
        st.info(f"Task Description: {task_def['description']}")

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Start Task Timer"):
                st.session_state["task_start_time"] = time.time()
                st.session_state["task_duration"] = None
                st.success("Timer started.")
        with col_b:
            if st.button("Stop Task Timer"):
                if "task_start_time" in st.session_state and st.session_state["task_start_time"]:
                    duration = time.time() - st.session_state["task_start_time"]
                    st.session_state["task_duration"] = duration
                    st.success(f"Timer stopped. Duration: {duration:.2f} seconds")
                else:
                    st.warning("Timer was not started.")
        with col_c:
            st.metric(
                "Recorded Duration (seconds)",
                f"{st.session_state.get('task_duration', 0):.2f}" if st.session_state.get("task_duration") else "-"
            )

        success = st.selectbox("Task outcome", TASK_SUCCESS_OPTIONS, index=0)
        errors = st.number_input("Number of noticeable errors (optional)", min_value=0, value=0, step=1)
        perceived_difficulty_label = st.select_slider(
            "Perceived task difficulty",
            options=list(LIKERT_5_SIMPLE.keys()),
            value="3 - Fair"
        )
        perceived_difficulty = LIKERT_5_SIMPLE[perceived_difficulty_label]

        satisfaction_label = st.select_slider(
            "Task satisfaction",
            options=list(LIKERT_5_SIMPLE.keys()),
            value="4 - Good"
        )
        task_satisfaction = LIKERT_5_SIMPLE[satisfaction_label]

        notes_label = "Observer Notes" if st.session_state.get("observer_mode", True) else "Participant Notes"
        notes = st.text_area(notes_label, placeholder="Add relevant observations or comments")

        if st.button("Save Task Results"):
            # Ensure consent exists before saving task results
            consent_df = load_from_csv(CONSENT_CSV)
            ensure_participant()
            pid = st.session_state["participant_id"]
            if consent_df.empty or pid not in set(consent_df.get("participant_id", [])):
                require_consent_warning()
            else:
                duration_val = st.session_state.get("task_duration", None)
                data_dict = {
                    "timestamp": now_iso(),
                    "participant_id": pid,
                    "task_name": selected_task,
                    "success": success,
                    "duration_seconds": round(duration_val, 3) if duration_val else "",
                    "errors": int(errors),
                    "perceived_difficulty_1to5": perceived_difficulty,
                    "task_satisfaction_1to5": task_satisfaction,
                    "notes": notes
                }
                save_to_csv(data_dict, TASK_CSV)

                # Reset timer for next task if desired
                if "task_start_time" in st.session_state:
                    del st.session_state["task_start_time"]
                if "task_duration" in st.session_state:
                    del st.session_state["task_duration"]

                st.success("Task results saved.")

    # -----------------------------
    # Exit Questionnaire
    # -----------------------------
    with exit_survey:
        st.header("Exit Questionnaire")

        with st.form("exit_form"):
            st.write("Please answer the following questions about your overall experience.")
            col1, col2 = st.columns(2)
            with col1:
                satisfaction_label = st.select_slider("Overall satisfaction", options=list(LIKERT_5.keys()), value="4 - Agree")
                ease_label = st.select_slider("The system was easy to use", options=list(LIKERT_5.keys()), value="4 - Agree")
                efficiency_label = st.select_slider("I could complete tasks efficiently", options=list(LIKERT_5.keys()), value="4 - Agree")
            with col2:
                learnability_label = st.select_slider("The system was easy to learn", options=list(LIKERT_5.keys()), value="4 - Agree")
                error_prevention_label = st.select_slider("The system helped me avoid errors", options=list(LIKERT_5.keys()), value="3 - Neutral")
                nps = st.slider("How likely are you to recommend this product to a friend or colleague? (0=Not at all likely, 10=Extremely likely)", 0, 10, 7)

            likes = st.text_area("What did you like most?")
            dislikes = st.text_area("What did you like least?")
            suggestions = st.text_area("What would you improve?")

            submitted_exit = st.form_submit_button("Submit Exit Questionnaire")
            if submitted_exit:
                # Ensure consent exists before saving exit survey
                consent_df = load_from_csv(CONSENT_CSV)
                ensure_participant()
                pid = st.session_state["participant_id"]
                if consent_df.empty or pid not in set(consent_df.get("participant_id", [])):
                    require_consent_warning()
                else:
                    data_dict = {
                        "timestamp": now_iso(),
                        "participant_id": pid,
                        "satisfaction_1to5": LIKERT_5[satisfaction_label],
                        "ease_of_use_1to5": LIKERT_5[ease_label],
                        "efficiency_1to5": LIKERT_5[efficiency_label],
                        "learnability_1to5": LIKERT_5[learnability_label],
                        "error_prevention_1to5": LIKERT_5[error_prevention_label],
                        "nps_0to10": int(nps),
                        "likes": likes,
                        "dislikes": dislikes,
                        "suggestions": suggestions
                    }
                    save_to_csv(data_dict, EXIT_CSV)
                    st.success("Exit questionnaire data saved.")

    # -----------------------------
    # Report
    # -----------------------------
    with report:
        st.header("Usability Report - Aggregated Results")

        # Consent
        st.subheader("Consent Data")
        consent_df = load_from_csv(CONSENT_CSV)
        if not consent_df.empty:
            st.dataframe(consent_df, use_container_width=True)
            st.write(f"Total Consents: {len(consent_df)}")
        else:
            st.info("No consent data available yet.")

        # Demographics
        st.subheader("Demographic Data")
        demo_df = load_from_csv(DEMOGRAPHIC_CSV)
        if not demo_df.empty:
            st.dataframe(demo_df, use_container_width=True)
            col1, col2, col3 = st.columns(3)
            with col1:
                if "age" in demo_df.columns:
                    st.metric("Average Age", f"{demo_df['age'].mean():.1f}")
            with col2:
                if "familiarity_1to5" in demo_df.columns:
                    st.metric("Avg Familiarity (1-5)", f"{demo_df['familiarity_1to5'].mean():.2f}")
            with col3:
                st.metric("Responses", f"{len(demo_df)}")
        else:
            st.info("No demographic data available yet.")

        # Tasks
        st.subheader("Task Performance Data")
        task_df = load_from_csv(TASK_CSV)
        if not task_df.empty:
            st.dataframe(task_df, use_container_width=True)

            # Success rate by task
            st.markdown("**Success Rate by Task**")
            success_map = {"Success": 1.0, "Partial": 0.5, "Fail": 0.0, "Abandoned": 0.0}
            tmp = task_df.copy()
            tmp["success_score"] = tmp["success"].map(success_map).fillna(0.0)
            success_by_task = tmp.groupby("task_name")["success_score"].mean().sort_values(ascending=False)
            st.bar_chart(success_by_task)

            # Average duration by task (seconds)
            if "duration_seconds" in task_df.columns:
                st.markdown("**Average Duration (seconds) by Task**")
                dur = task_df.copy()
                # Filter non-empty duration values
                dur = dur[dur["duration_seconds"].apply(lambda x: isinstance(x, (int, float)) or (isinstance(x, str) and x.strip() != ""))]
                # Convert to numeric
                dur["duration_seconds"] = pd.to_numeric(dur["duration_seconds"], errors="coerce")
                avg_dur = dur.groupby("task_name")["duration_seconds"].mean().dropna()
                if not avg_dur.empty:
                    st.bar_chart(avg_dur)
                else:
                    st.info("No duration data to aggregate yet.")
            else:
                st.info("No duration data to aggregate yet.")
        else:
            st.info("No task data available yet.")

        # Exit
        st.subheader("Exit Questionnaire Data")
        exit_df = load_from_csv(EXIT_CSV)
        if not exit_df.empty:
            st.dataframe(exit_df, use_container_width=True)

            metrics_cols = ["satisfaction_1to5", "ease_of_use_1to5", "efficiency_1to5", "learnability_1to5", "error_prevention_1to5"]
            present = [c for c in metrics_cols if c in exit_df.columns]
            if present:
                col1, col2, col3, col4, col5 = st.columns(5)
                cols_map = {0: col1, 1: col2, 2: col3, 3: col4, 4: col5}
                for idx, c in enumerate(present):
                    cols_map[idx].metric(c.replace("_", " ").title(), f"{exit_df[c].mean():.2f}")
            if "nps_0to10" in exit_df.columns:
                st.metric("Average NPS", f"{exit_df['nps_0to10'].mean():.1f}")
        else:
            st.info("No exit questionnaire data available yet.")


if __name__ == "__main__":
    main()