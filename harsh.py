import streamlit as st
import random
import io
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image
import os
import datetime


USERS = {
    "student": {"id": "student123", "password": "pass123"},
    "teacher_dileep": {"id": "dileep123", "password": "pass456", "name": "Dileep Kumar"},
    "teacher_bagal": {"id": "bagal123", "password": "pass789", "name": "Bagal"},
    "teacher_sugam": {"id": "sugam123", "password": "pass101", "name": "Sugam Shivare"},
    "teacher_rajshekhar": {"id": "raj123", "password": "pass102", "name": "Rajshekhar Pothala"},
    "teacher_dj": {"id": "dj123", "password": "pass103", "name": "DJ"},
    "teacher_ashok": {"id": "ashok123", "password": "pass104", "name": "ASHOK PANIGRAHI"},
    "teacher_sachin": {"id": "sachin123", "password": "pass105", "name": "Sachin Bhandari"},
    "teacher_rehan": {"id": "rehan123", "password": "pass106", "name": "Rehan"},
    "teacher_suraj": {"id": "suraj123", "password": "pass107", "name": "Suraj Patil"},
}
DATABASE = "leave_request.csv"
LEAVE_STATUS_PENDING = "Pending"
LEAVE_STATUS_GRANTED = "Granted"
LEAVE_STATUS_REJECTED = "Rejected"

st.set_page_config(page_title="Secure Hostel Leave App", layout="centered")


if "LI_AS" not in st.session_state:
    st.session_state.LI_AS = None

if "T_NAME" not in st.session_state:
    st.session_state.T_NAME = None


def login(role):
    st.subheader(f"{role.capitalize()} Login")
    u_id = st.text_input("ID", key=f"{role}_id") # Shortened: user_id -> u_id
    pwd = st.text_input("Password", type="password", key=f"{role}_password") # Shortened: password -> pwd
    login_btn = st.button("Login", key=f"{role}_login")

    if login_btn:
        if role == "student":
            if u_id == USERS["student"]["id"] and pwd == USERS["student"]["password"]:
                st.session_state.LI_AS = "student"
                st.success(f"Welcome, you're logged in as a student!")
                st.rerun()
            else:
                st.error("Oops! Invalid Student ID or Password. Please try again.")
        elif role == "teacher":
            found = False # Shortened: found_teacher -> found
            for t_key, t_info in USERS.items(): # Shortened: teacher_key -> t_key, teacher_info -> t_info
                if t_key.startswith("teacher") and u_id == t_info["id"] and pwd == t_info["password"]:
                    st.session_state.LI_AS = "teacher"
                    st.session_state.T_NAME = t_info["name"]
                    st.success(f"Welcome, {t_info['name']}! You're logged in as a teacher.")
                    found = True
                    st.rerun()
                    break
            if not found:
                st.error("Oops! Invalid Teacher ID or Password. Please try again.")


@st.cache_data(show_spinner="Loading leave requests...")
def load_leave_requests():
    exp_cols_dtypes = { 
        "student_name": str,
        "attendance": float,
        "year": str,
        "student_id": str,
        "branch": str,
        "batch": str,
        "email": str,
        "leave_days": int,
        "start_date": str,
        "end_date": str,
        "reason": str,
        "teacher": str,
        "status": str,
        "qr_code_data": str
    }

    if os.path.exists(DATABASE):
        try:
            df = pd.read_csv(DATABASE)
            for col, dtype in exp_cols_dtypes.items():
                if col not in df.columns:
                    df.insert(loc=df.shape[-1], column=col, value=None) 
                try:
                    if dtype == int:
                        df.loc[:, col] = pd.to_numeric(df.loc[:, col], errors='coerce').fillna(0).astype(int)
                    elif dtype == float:
                        df.loc[:, col] = pd.to_numeric(df.loc[:, col], errors='coerce').fillna(0.0).astype(float)
                    else:
                        df.loc[:, col] = df.loc[:, col].astype(str).replace('nan', None)
                except Exception as e:
                    st.warning(f"Heads up! Couldn't fully convert column '{col}' to {dtype}: {e}. It might look a bit off.")
                    df.loc[:, col] = df.loc[:, col].astype(str) 

            if 'qr_code_data' in df.columns:
                df.loc[:, 'qr_code_data'] = df.loc[:, 'qr_code_data'].astype(str).replace(['None', 'nan'], [None, None])

            return df
        except pd.errors.EmptyDataError:
            st.warning("Looks like the leave requests file is empty. Starting fresh!")
            return pd.DataFrame(columns=exp_cols_dtypes.keys()).astype(
                {k: object if k == 'qr_code_data' else v for k, v in exp_cols_dtypes.items()})
        except Exception as e:
            st.error(f"Oh dear! Had trouble loading leave requests: {e}. Starting with an empty list.")
            return pd.DataFrame(columns=exp_cols_dtypes.keys()).astype(
                {k: object if k == 'qr_code_data' else v for k, v in exp_cols_dtypes.items()})
    else:
        return pd.DataFrame(columns=exp_cols_dtypes.keys()).astype(
            {k: object if k == 'qr_code_data' else v for k, v in exp_cols_dtypes.items()})

def save_leave_request(new_req, existing_reqs): 
    new_req_df = pd.DataFrame([new_req])
    updated_reqs = pd.concat([existing_reqs, new_req_df], ignore_index=True) 

    try:
        updated_reqs.to_csv(DATABASE, index=False)
        load_leave_requests.clear() 
        return True
    except Exception as e:
        st.error(f"Couldn't save your request: {e}")
        return False

def generate_qr_code(data: str, box_size=6) -> Image.Image: 
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=box_size,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    return img

def image_to_bytes(img):
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue()

L_DF = load_leave_requests() 

def student_page():
    global L_DF 

    st.title("Welcome to Nmims Leave Application🧳!")
    st.write("---")

    st.header("Leave Application Form")
    s_name = st.text_input("Enter your full name", placeholder="Your name") 
    s_id = st.text_input("Enter your student ID", placeholder="Your SAP ID ") 

    if not s_id:
        st.info("Please enter your **Student ID** to proceed. It's important!")
    else:
        st.write(f"Your Student ID is: **{s_id}**")

    yr = st.text_input("Which year are you in (e.g., 1, 2, 3, 4)?") 
    yr_valid = False 
    if yr:
        try:
            yr_int = int(yr) 
            if 1 <= yr_int <= 4:
                yr_valid = True
            else:
                st.error("Please enter a valid year (like 1, 2, 3, or 4).")
        except ValueError:
            st.error("That doesn't look like a valid number for the year. Try again!")
    else:
        st.info("Please enter your academic year.")

    attn = st.number_input("What's your average attendance percentage?", min_value=0.0, max_value=100.0, value=85.0, step=0.1, format="%.1f") # Shortened: attendance -> attn
    st.write(f"Your attendance is: **{attn:.2f}%**")
    if attn <= 80:
        st.warning("Heads up! Your attendance is below 80%. You might need to chat with your Mentor about this.")

    email = st.text_input("Your Email ID:", placeholder="youremail@example.com") 

    col_a, col_b = st.columns(2)
    auth_leave = False 
    spec_leave = False 
    with col_a:
        auth_leave = st.checkbox('Authorized Leave')
    with col_b:
        spec_leave = st.checkbox('Special Leave')

    leave_type_sel = False 
    if auth_leave and spec_leave:
        st.error("Please pick only one type of leave.")
    elif not auth_leave and not spec_leave:
        st.error("Don't forget to select a leave type!")
    else:
        leave_type_sel = True

    reason = st.text_area("Why are you requesting leave?", height=100)
    if reason:
        st.info("Your reason will be reviewed by your mentor.")
    else:
        st.warning("Please provide a reason for your leave.")

    st.subheader("Your Branch and Batch")
    mentors = ['Dileep Kumar', 'Bagal', 'Sugam Shivare', 'Rajshekhar Pothala', 'DJ', 'ASHOK PANIGRAHI', 'Sachin Bhandari', 'Rehan', 'Suraj Patil']
    branches = ['BTECH CS', 'BTECH CE', 'BTECH AI-ML', 'BTECH IT', 'MBA TECH CE', 'B-PHARM', 'TEXTILE']
    sel_branch = st.selectbox("Choose your Branch:", branches, index=0) 

    batches = []
    if sel_branch == "BTECH CS":
        batches = ['A1','A2','B1','B2']
    elif sel_branch == "BTECH CE":
        batches = ['C1','C2','D1','D2']
    elif sel_branch == "BTECH AI-ML":
        batches = ['F1','F2']
    elif sel_branch == "BTECH IT":
        batches = ['E1','E2']
    elif sel_branch == "MBA TECH CE":
        batches = ['AB1','AB2']
    elif sel_branch == "B-PHARM":
        batches = ['P1','P2','P3']
    elif sel_branch == "TEXTILE":
        batches = ['T1','T2','T3','T4']

    sel_batch = None 
    if not batches:
        st.warning("First, pick your branch to see your batch options.")
    else:
        sel_batch = st.selectbox("Choose your Batch:", batches)
        if sel_batch:
            st.write(f"You're in batch: **{sel_batch}**, from the **{sel_branch}** branch.")
        else:
            st.info("Please select your batch.")

    st.subheader("Your Mentor's Details")

    sel_mentor = st.selectbox("Select Your Mentor:", mentors) 

    mentor_batch_map = {
        'A1': 'Sugam Shivare', 'A2': 'Dileep Kumar', 'B1': 'Rajshekhar Pothala', 'B2': 'DJ',
        'C1': 'ASHOK PANIGRAHI', 'C2': 'Sachin Bhandari', 'D1': 'Suraj Patil', 'D2': 'Rehan',
        'F1': 'Dileep Kumar', 'F2': 'DJ',
        'E1': 'Bagal', 'E2': 'Dileep Kumar',
        'AB1': 'Sachin Bhandari', 'AB2': 'Rehan',
        'P1': 'Dileep Kumar', 'P2': 'Dileep Kumar', 'P3': 'Dileep Kumar',
        'T1': 'DJ', 'T2': 'DJ', 'T3': 'DJ', 'T4': 'DJ'
    }

    mentor_verified = False
    if sel_batch and sel_mentor:
        if mentor_batch_map.get(sel_batch) == sel_mentor:
            st.success("Mentor and batch details look good!")
            mentor_verified = True
        else:
            st.error(f"Hmm, please double-check: is '{sel_mentor}' the correct mentor for batch '{sel_batch}'?")
    elif not sel_batch:
        st.warning("Please pick your batch to help verify your mentor.")

    st.subheader("When are you applying for leave? 📅")
    today = datetime.date.today()
    s_date = st.date_input("Leave From:", today) 
    e_date = st.date_input("Till:", max(today, s_date)) 

    num_days = 0
    date_range_valid = False
    if s_date > e_date:
        st.error("The 'End' date must be after or on the 'From' date.")
    else:
        num_days = (e_date - s_date).days + 1
        st.success(f"You're applying for **{num_days}** day(s) of leave.")
        date_range_valid = True

    if num_days > 5:
        st.warning("For leaves longer than 5 days, permission from a higher authority might be needed.")

    st.write("---")
    if st.button("Submit My Leave Request"):
        if all([
            s_name, s_id, attn is not None, yr_valid, sel_branch, sel_batch,
            email, sel_mentor, reason,
            leave_type_sel, date_range_valid, mentor_verified, num_days > 0
        ]):
            is_dup = False 
            s_pending_reqs = L_DF.loc[(L_DF["student_id"] == s_id) & (L_DF["status"] == LEAVE_STATUS_PENDING)].copy() 

            if not s_pending_reqs.empty:
                new_s_dt = s_date 
                new_e_dt = e_date 

                s_pending_reqs.loc[:, 'existing_start_dt'] = pd.to_datetime(s_pending_reqs['start_date']).dt.date
                s_pending_reqs.loc[:, 'existing_end_dt'] = pd.to_datetime(s_pending_reqs['end_date']).dt.date

                for idx, existing_req in s_pending_reqs.iterrows():
                    dates_overlap = (new_s_dt <= existing_req['existing_end_dt']) and \
                                    (existing_req['existing_start_dt'] <= new_e_dt)
                    reasons_match = (str(existing_req['reason']).strip().lower() == reason.strip().lower())

                    if dates_overlap and reasons_match:
                        is_dup = True
                        break

            if is_dup:
                st.warning("Hold on! You already have a similar pending leave request for these dates and reason. Please wait for your previous request to be processed by your teacher.")
            else:
                new_req = {
                    "student_name": s_name,
                    "attendance": attn,
                    "year": yr,
                    "student_id": s_id,
                    "branch": sel_branch,
                    "batch": sel_batch,
                    "email": email,
                    "leave_days": num_days,
                    "start_date": s_date.isoformat(),
                    "end_date": e_date.isoformat(),
                    "reason": reason,
                    "teacher": sel_mentor,
                    "status": LEAVE_STATUS_PENDING,
                    "qr_code_data": None
                }
                if save_leave_request(new_req, L_DF):
                    st.success("Great! Your leave request has been submitted. Please wait for your teacher's approval.")
                    L_DF = load_leave_requests() 
                else:
                    st.error("Oh no! Couldn't save your request. Something went wrong.")
        else:
            st.error("Almost there! Please fill in all the required details correctly and fix any warnings or errors before submitting.")

    st.write("---")
    st.subheader("Your Leave Request Status and Gate Pass")
    if s_id:
        s_reqs = L_DF.loc[(L_DF["student_id"] == s_id)].copy() # Shortened: student_requests -> s_reqs

        if not s_reqs.empty:
            st.write("### Your Leave Request History:")
            st.dataframe(s_reqs[['start_date', 'end_date', 'leave_days', 'reason', 'status', 'teacher']])

            s_reqs.loc[:, 'start_date_dt'] = pd.to_datetime(s_reqs['start_date']).dt.date
            s_reqs.loc[:, 'end_date_dt'] = pd.to_datetime(s_reqs['end_date']).dt.date

            active_granted_reqs = s_reqs.loc[(s_reqs["status"] == LEAVE_STATUS_GRANTED) & (s_reqs["end_date_dt"] >= today)].sort_values(by="end_date_dt", ascending=True) # Shortened: active_granted_requests -> active_granted_reqs

            if not active_granted_reqs.empty:
                current_active_req = active_granted_reqs.iloc[[0]] 

                if pd.notna(current_active_req["qr_code_data"].iloc(0)[0]):
                    st.success(f"Good news! Your leave request for **{current_active_req['start_date'].iloc(0)[0]}** to **{current_active_req['end_date'].iloc(0)[0]}** has been **GRANTED!** This pass is valid until **{current_active_req['end_date_dt'].iloc(0)[0]}**.")
                    st.subheader("Here's Your Active Gate Pass:")
                    try:
                        qr_data = current_active_req["qr_code_data"].iloc(0)[0]
                        qr_image = generate_qr_code(qr_data, box_size=4) 
                        qr_bytes = image_to_bytes(qr_image)
                        st.image(qr_image, caption="Your Approved Leave Gate Pass", use_container_width=False) 
                        st.download_button(
                            label="Download Your Gate Pass QR Code",
                            data=qr_bytes,
                            file_name=f"gatepass_{s_id}_{current_active_req['start_date'].iloc(0)[0]}.png",
                            mime="image/png",
                        )
                    except Exception as e:
                        st.error(f"Something went wrong displaying your QR code: {e}. Please contact your teacher or administrator.")
                else:
                    st.info("Your leave request is approved, but the QR code data seems to be missing. Please talk to your teacher.")
            else:
                st.info("No active or future approved leave requests found for your Student ID. Your previous passes have expired or none are pending.")
        else:
            st.info("No leave requests found for your Student ID. Submit one above!")
    else:
        st.info("Enter your Student ID above to check your leave status and get your pass.")

def teacher_page():
    global L_DF 

    curr_t_name = st.session_state.get("T_NAME") 
    if curr_t_name:
        st.title(f"Welcome, {curr_t_name} (Teacher Portal)!")
    else:
        st.title("Welcome to the Teacher Portal!")

    st.write("---")

    st.subheader("Pending Leave Requests (Awaiting Your Review)")

    pending_reqs = L_DF.loc[(L_DF["status"] == LEAVE_STATUS_PENDING) & (L_DF["teacher"] == curr_t_name)] 
    if not pending_reqs.empty:
        for original_index, req in pending_reqs.iterrows(): 
            with st.container(border=True):
                st.info(f"**Student Name:** {req['student_name']}\n"
                        f"**Student ID:** {req['student_id']}\n"
                        f"**Branch/Batch:** {req['branch']}/{req['batch']}\n"
                        f"**Leave Days:** {req['leave_days']} ({req['start_date']} to {req['end_date']})\n"
                        f"**Reason:** {req['reason']}\n"
                        f"**Requested Teacher:** {req['teacher']}\n"
                        f"**Attendance:** {req['attendance']}%")

                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"✅ Approve {req['student_id']}", key=f"approve_{req['student_id']}_{original_index}"):
                        qr_data = (f"LEAVE_GRANTED_ID:{req['student_id']}|"
                                   f"NAME:{req['student_name']}|"
                                   f"FROM:{req['start_date']}|"
                                   f"TO:{req['end_date']}|"
                                   f"TS:{datetime.datetime.now().timestamp()}")

                        L_DF.loc[original_index, "status"] = LEAVE_STATUS_GRANTED
                        L_DF.loc[original_index, "qr_code_data"] = qr_data

                        L_DF.to_csv(DATABASE, index=False)
                        load_leave_requests.clear() # Clear cache to force reload
                        st.success(f"Leave granted for Student ID: {req['student_id']}! QR code generated and ready.")
                        try:
                            qr_image = generate_qr_code(qr_data)
                            qr_bytes = image_to_bytes(qr_image)
                            st.subheader("Generated Gate Pass Preview:")
                            st.image(qr_bytes, caption=f"QR Code for {req['student_id']}", use_container_width=True)
                            st.download_button(
                                label="Download Gate Pass QR Code",
                                data=qr_bytes,
                                file_name=f"gatepass_{req['student_id']}_{req['start_date']}.png",
                                mime="image/png",
                            )
                        except Exception as e:
                            st.error(f"Oops! Couldn't display the QR code preview: {e}. But the leave is still granted.")
                        st.rerun()

                with col2:
                    if st.button(f"❌ Reject {req['student_id']}", key=f"reject_{req['student_id']}_{original_index}"):
                        L_DF.loc[original_index, "status"] = LEAVE_STATUS_REJECTED
                        L_DF.loc[original_index, "qr_code_data"] = None
                        L_DF.to_csv(DATABASE, index=False)
                        load_leave_requests.clear() 
                        st.warning(f"Leave rejected for Student ID: {req['student_id']}.")
                        st.rerun()
    else:
        st.info("Great news! No pending leave requests for you at the moment.")

    st.write("---")
    st.subheader("Your Approved/Rejected Leave Requests History")
    t_hist_reqs = L_DF.loc[(L_DF["teacher"] == curr_t_name) & ((L_DF["status"] == LEAVE_STATUS_GRANTED) | (L_DF["status"] == LEAVE_STATUS_REJECTED))] 

    if not t_hist_reqs.empty:
        st.dataframe(t_hist_reqs)
        st.info("Just a note: QR code images show up when a request is approved or on the student's page, not directly within this table. The 'QR Code Data' column shows the text inside the QR.")
    else:
        st.info("No approved or rejected leave requests found for you yet.")

def logout():
    if st.sidebar.button("Logout"):
        st.session_state.LI_AS = None
        st.session_state.T_NAME = None
        st.rerun()

if st.session_state.LI_AS is None:
    st.sidebar.title("Login to Your Portal")
    page = st.sidebar.radio("Select Role", ["🧑‍🎓Student", "🧑‍🏫Teacher"], key="role_selection_radio")

    if page == "🧑‍🎓Student":
        login("student")
    elif page == "🧑‍🏫Teacher":
        login("teacher") 
else:
    logout()
    if st.session_state.LI_AS == "student":
        student_page()
    elif st.session_state.LI_AS == "teacher":
        teacher_page()