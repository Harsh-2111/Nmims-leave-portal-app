import streamlit as st
import random 
import io
import pandas as pd
import qrcode
from io import BytesIO
from PIL import Image
import os
import datetime 

users = {
    "student": {"id": "student123", "password": "pass123"},
    "teacher": {"id": "teacher123", "password": "teachpass"}
}

st.set_page_config(page_title="Secure Hostel Leave App")

if "logged_in_as" not in st.session_state:
    st.session_state.logged_in_as = None

page = st.sidebar.radio("Select Role", ["🧑‍🎓Student", "🧑‍🏫Teacher"])

DATABASE = "leave_request.csv"


def login(role):
    st.subheader(f"{role.capitalize()} Login") # Shows "Student Login" or "Teacher Login"
    user_id = st.text_input("ID", key=f"{role}_id") # Unique key for each login field
    password = st.text_input("Password", type="password", key=f"{role}_password")
    login_btn = st.button("Login", key=f"{role}_login")

    if login_btn:
        if user_id == users[role]["id"] and password == users[role]["password"]:
            st.session_state.logged_in_as = role # Remember who logged in
            st.success(f"Welcome, you're logged in as a {role}!")
            st.rerun() 
        else:
            st.error("Oops! Invalid ID or Password. Please try again.")

def load_leave_requests():
    
    expected_columns_with_dtypes = {
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
            for col, dtype in expected_columns_with_dtypes.items():
                if col not in df.columns:
                    df[col] = None
                try:
                    if dtype == int:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
                    elif dtype == float:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0.0).astype(float)
                    else: 
                        df[col] = df[col].astype(str)
                        df[col] = df[col].replace('nan', None)
                except Exception as e:
                    st.warning(f"Heads up! Couldn't fully convert column '{col}' to {dtype}: {e}. It might look a bit off.")
                    df[col] = df[col].astype(str) 
            if 'qr_code_data' in df.columns:
                df['qr_code_data'] = df['qr_code_data'].astype(str)
                df['qr_code_data'] = df['qr_code_data'].replace('None', None)
                df['qr_code_data'] = df['qr_code_data'].replace('nan', None)

            return df
        except pd.errors.EmptyDataError:
            st.warning("Looks like the leave requests file is empty. Starting fresh!")
            return pd.DataFrame(columns=expected_columns_with_dtypes.keys()).astype(expected_columns_with_dtypes)
        except Exception as e:
            st.error(f"Oh dear! Had trouble loading leave requests: {e}. Starting with an empty list.")
            return pd.DataFrame(columns=expected_columns_with_dtypes.keys()).astype(expected_columns_with_dtypes)
    else:
        return pd.DataFrame(columns=expected_columns_with_dtypes.keys()).astype(expected_columns_with_dtypes)

def save_leave_request(new_request, existing_requests):
    new_request_df = pd.DataFrame([new_request])
    updated_requests = pd.concat([existing_requests, new_request_df], ignore_index=True)

    try:
        updated_requests.to_csv(DATABASE, index=False)
        return True
    except Exception as e:
        st.error(f"Couldn't save your request: {e}")
        return False

def generate_qr_code(data: str) -> Image.Image:
   
    qr = qrcode.QRCode(
        version=1, 
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10, 
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

leave_requests_df = load_leave_requests()

def student_page():
    global leave_requests_df 

    st.title("Welcome to Nmims Leave Application🧳!")
    st.write("---") 

    st.header("Your Details")
    student_name = st.text_input("Enter your full name", placeholder="Name")
    student_id = st.text_input("Enter your student ID", placeholder=" SAP ID")

    if not student_id:
        st.info("Please enter your Student ID to proceed. It's important!")
    else:
        st.write(f"Your Student ID is: **{student_id}**")

    year = st.text_input("Which year are you in ? (1, 2, 3, 4)")
    if year:
        try:
            if int(year) >= 5:
                st.error("Please enter a valid year.")
        except ValueError:
            st.error("That doesn't look like a valid number for the year. Enter Something else!")

    attendance = st.text_input("Enter your average attendance ?", placeholder="Attendance")
    if attendance:
        try:
            att_float = float(attendance)
            st.write(f"Your attendance is: **{att_float:.2f}%**")
            if att_float <= 80:
                st.warning("Your attendance is below 80%. You might need to chat with your Mentor about this.")
            
        except ValueError:
            st.error("Please enter a valid number for attendance.")

    st.header("Leave Type and Reason")
    col_a, col_b = st.columns(2)
    authorized_leave = False
    special_leave = False
    with col_a:
        authorized_leave = st.checkbox('Authorized Leave')
    with col_b:
        special_leave = st.checkbox('Special Leave')

    if authorized_leave and special_leave:
        st.error("Please pick only one type of leave.")
    elif not authorized_leave and not special_leave:
        st.error("It is compulsory to select a leave type!")

    reason = st.text_area("Reason for requesting leave", height=100)
    if reason:
        st.info("Your reason will be reviewed by your mentor.")

    email_id = st.text_input("Your Email ID:", placeholder="Email")

    st.header("Your Branch and Batch")
    branches = ['BTECH CS', 'BTECH CE', 'BTECH AI-ML', 'BTECH IT', 'MBA TECH CE', 'B-PHARM', 'TEXTILE']
    selected_branch = st.selectbox("Choose your Branch:", branches, index=0)

    batches = [] 
    if selected_branch == "BTECH CS":
        batches = ['A1','A2','B1','B2']
    elif selected_branch == "BTECH CE":
        batches = ['C1','C2','D1','D2']
    elif selected_branch == "BTECH AI-ML":
        batches = ['F1','F2']
    elif selected_branch == "BTECH IT":
        batches = ['E1','E2']
    elif selected_branch == "MBA TECH CE":
        batches = ['AB1','AB2']
    elif selected_branch == "B-PHARM":
        batches = ['P1','P2','P3']
    elif selected_branch == "TEXTILE":
        batches = ['T1','T2','T3','T4']

    selected_batch = None
    if not batches:
        st.warning("First, pick your branch to see your batch options.")
    else:
        selected_batch = st.selectbox("Choose your Batch:", batches)
        st.write(f"You're in batch: **{selected_batch}**, from the **{selected_branch}** branch.")

    st.header("Your Mentor's Details")
    mentors = ['Dileep Kumar', 'Bagal', 'Sugam Shivare', 'Rajshekhar Pothala', 'DJ', 'ASHOK PANIGRAHI', 'Sachin Bhandari', 'Rehan', 'Suraj Patil']
    selected_mentor = st.selectbox("Select Your Mentor:", mentors)

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
    if selected_batch and selected_mentor:
        if mentor_batch_map.get(selected_batch) == selected_mentor:
            st.success("Mentor and batch details verified")
            mentor_verified = True
        else:
            st.error(f"Please double-check: is '{selected_mentor}' the correct mentor for batch '{selected_batch}'?")
    elif not selected_batch:
        st.warning("Please select your batch to get verified by your mentor.")

    st.header("When are you applying for leave? 📅")
    today = datetime.date.today()
    start_date = st.date_input("Leave From:", today)
    end_date = st.date_input("Till:", today)

    num_days = 0
    if start_date > end_date:
        st.error("The 'End' date must be after or on the 'From' date.")
    else:
        num_days = (end_date - start_date).days + 1
        st.success(f"You're applying for **{num_days}** day(s) of leave.")

    if num_days <= 5:
        st.info("For short leaves (up to 5 days), you might not need extra sign-offs.")
    else:
        st.warning("For leaves longer than 5 days, permission from a higher authority might be needed.")

    st.write("---") 
    if st.button("Submit My Leave Request"):
        if all([student_name, student_id, attendance, year, selected_branch, selected_batch,
                email_id, selected_mentor, reason,
                (authorized_leave or special_leave),      
                (not (authorized_leave and special_leave)), 
                (start_date <= end_date),                
                mentor_verified,                        
                num_days > 0                            
                ]):
            is_duplicate = False
            student_pending_requests = leave_requests_df[
                (leave_requests_df["student_id"] == student_id) &
                (leave_requests_df["status"] == "Pending")
            ]

            if not student_pending_requests.empty:
                new_start_dt = datetime.datetime.combine(start_date, datetime.time.min)
                new_end_dt = datetime.datetime.combine(end_date, datetime.time.max)

                for idx, existing_req in student_pending_requests.iterrows():
                    existing_start_dt = datetime.datetime.strptime(existing_req['start_date'], '%Y-%m-%d')
                    existing_end_dt = datetime.datetime.strptime(existing_req['end_date'], '%Y-%m-%d')

                    dates_overlap = (new_start_dt <= existing_end_dt) and \
                                    (existing_start_dt <= new_end_dt)
                    reasons_match = (str(existing_req['reason']).strip().lower() == reason.strip().lower())

                    if dates_overlap and reasons_match:
                        is_duplicate = True 
                        break

            if is_duplicate:
                st.warning("Hold on! You already have a similar pending leave request for these dates and reason. Please wait for your previous request to be processed by your teacher.")
            else:
                new_request = {
                    "student_name": student_name,
                    "attendance": attendance,
                    "year": year,
                    "student_id": student_id,
                    "branch": selected_branch,
                    "batch": selected_batch,
                    "email": email_id,
                    "leave_days": num_days,
                    "start_date": start_date.isoformat(), 
                    "end_date": end_date.isoformat(),
                    "reason": reason,
                    "teacher": selected_mentor,
                    "status": "Pending", 
                    "qr_code_data": None 
                }
                if save_leave_request(new_request, leave_requests_df):
                    st.success("Great! Your leave request has been submitted. Please wait for your teacher's approval.")
                    leave_requests_df = load_leave_requests() 
                else:
                    st.error("Oh no! Couldn't save your request. Something went wrong.")
        else:
            st.error("Almost there! Please fill in all the required details correctly and fix any warnings or errors before submitting.")

    st.write("---")
    st.subheader("Your Leave Request Status and Gate Pass")
    if student_id: 
        granted_request_rows = leave_requests_df[
            (leave_requests_df["student_id"] == student_id) &
            (leave_requests_df["status"] == "Granted")
        ]

        if not granted_request_rows.empty:
            granted_request = granted_request_rows.iloc[-1]

            if pd.notna(granted_request["qr_code_data"]): 
                st.success(f"Good news! Your leave request for {granted_request['start_date']} to {granted_request['end_date']} has been **GRANTED!**")
                st.subheader("Here's Your Gate Pass:")
                try:
                    qr_image = generate_qr_code(granted_request["qr_code_data"])
                    qr_bytes = image_to_bytes(qr_image)
                    st.image(qr_image, caption="Your Approved Leave Gate Pass", use_container_width=True) 
                    st.download_button(
                        label="Download Your Gate Pass QR Code",
                        data=qr_bytes,
                        file_name=f"gatepass_{student_id}_{granted_request['start_date']}.png",
                        mime="image/png",
                    )
                except Exception as e:
                    st.error(f"Something went wrong displaying your QR code: {e}. Please contact your teacher or administrator.")
            else:
                st.info("Your leave request is approved, but the QR code data seems to be missing. Please talk to your teacher.")
        else:
            st.info("No approved leave requests found for your Student ID yet. Keep an eye out!")
    else:
        st.info("Enter your Student ID above to check your leave status and get your pass.")


def teacher_page():
    global leave_requests_df 

    st.title("Welcome to the Teacher Portal!")
    st.write("---")

    st.subheader("Pending Leave Requests (Awaiting Your Review)")
    pending_requests = leave_requests_df[leave_requests_df["status"] == "Pending"]

    if not pending_requests.empty:
        for index, request in pending_requests.iterrows():
            with st.container(border=True):
                st.info(f"**Student Name:** {request['student_name']}\n"
                          f"**Student ID:** {request['student_id']}\n"
                          f"**Branch/Batch:** {request['branch']}/{request['batch']}\n"
                          f"**Leave Days:** {request['leave_days']} ({request['start_date']} to {request['end_date']})\n"
                          f"**Reason:** {request['reason']}\n"
                          f"**Requested Teacher:** {request['teacher']}\n"
                          f"**Attendance:** {request['attendance']}%")

                col1, col2 = st.columns(2) 
                with col1:
                    if st.button(f"✅ Approve {request['student_id']}", key=f"approve_{request['student_id']}_{index}"):
                        qr_data = (f"LEAVE_GRANTED_ID:{request['student_id']} "
                                   f"NAME:{request['student_name']} "
                                   f"FROM:{request['start_date']} "
                                   f"TO:{request['end_date']} "
                                   f"TS:{datetime.datetime.now().timestamp()}") 
                        leave_requests_df.loc[index, "status"] = "Granted"
                        leave_requests_df.loc[index, "qr_code_data"] = qr_data
                        leave_requests_df.to_csv(DATABASE, index=False)

                        st.success(f"Leave granted for Student ID: {request['student_id']}! QR code generated and ready.")
                        try:
                            qr_image = generate_qr_code(qr_data)
                            qr_bytes = image_to_bytes(qr_image)
                            st.subheader("Generated Gate Pass Preview:")
                            st.image(qr_bytes, caption=f"QR Code for {request['student_id']}", use_container_width=True)
                            st.download_button(
                                label="Download Gate Pass QR Code",
                                data=qr_bytes,
                                file_name=f"gatepass_{request['student_id']}_{request['start_date']}.png",
                                mime="image/png",
                            )
                        except Exception as e:
                            st.error(f"Oops! Couldn't display the QR code preview: {e}. But the leave is still granted.")

                        st.rerun() 

                with col2:
                    # Reject button: also uses the DataFrame index for a unique key.
                    if st.button(f"❌ Reject {request['student_id']}", key=f"reject_{request['student_id']}_{index}"):
                        leave_requests_df.loc[index, "status"] = "Rejected" # Set status to 'Rejected'
                        leave_requests_df.loc[index, "qr_code_data"] = None # Clear QR data for rejected requests
                        leave_requests_df.to_csv(DATABASE, index=False) # Save changes
                        st.warning(f"Leave rejected for Student ID: {request['student_id']}.")
                        st.rerun() 
    else:
        st.info("Great news! No pending leave requests at the moment.")

    st.write("---")
    st.subheader("All Leave Requests History")
    # Display the full history of all leave requests.
    if not leave_requests_df.empty:
        st.dataframe(leave_requests_df)
        st.info("Just a note: QR code images show up when a request is approved or on the student's page, not directly within this table. The 'QR Code Data' column shows the text inside the QR.")
    else:
        st.info("No leave requests have been submitted yet.")

def logout():
   
    if st.sidebar.button("Logout"): 
        st.session_state.logged_in_as = None 
        st.rerun() 

if st.session_state.logged_in_as == "student":
    logout() 
    student_page() 
elif st.session_state.logged_in_as == "teacher":
    logout() 
    teacher_page() 
else:
    st.sidebar.title("Login to Your Portal")
    if page == "🧑‍🎓Student": 
        login("student")
    elif page == "🧑‍🏫Teacher":
        login("teacher")