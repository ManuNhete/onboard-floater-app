"""
TakeOFF Driver Onboarding — Streamlit + Supabase

Run with:
    streamlit run onboard_floater_app.py

Flow: welcome (sign up / log in) -> phone -> OTP -> personal details ->
vehicle details -> payout -> document upload -> review -> submit -> completion.
Returning drivers who log in are shown their existing application status
instead of being sent back through the form.

NOTE: OTP is simulated (shown on screen) since no SMS provider is wired
up. Swap the "otp" step for real Supabase phone auth once you have one.
"""

import random

import streamlit as st

from utils.db import create_driver_profile, get_driver_by_phone, upload_document

st.set_page_config(page_title="TakeOFF Driver Onboarding", page_icon="🚗", layout="centered")

# ---------- session state ----------
DEFAULTS = {
    "step": "start",
    "mode": None,  # "signup" or "login"
    "form_data": {},
    "otp_code": None,
    "driver_id": None,
    "existing_driver": None,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def go_to(step: str):
    st.session_state.step = step
    st.rerun()


def reset():
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.rerun()


st.title("🚗 TakeOFF Driver Onboarding")

step = st.session_state.step

# ---------- 0. Welcome / sign-up vs log-in ----------
if step == "start":
    st.subheader("Welcome")
    st.write("Are you a new driver applying for the first time, or checking on an existing application?")
    col1, col2 = st.columns(2)
    if col1.button("Sign up — I'm a new driver", type="primary"):
        st.session_state.mode = "signup"
        go_to("phone")
    if col2.button("Log in — check my application"):
        st.session_state.mode = "login"
        go_to("phone")

# ---------- 1. Phone number ----------
elif step == "phone":
    is_login = st.session_state.mode == "login"
    st.subheader("Log in" if is_login else "Let's get you started")
    phone = st.text_input("Phone number", placeholder="+263 77 000 0000")
    col1, col2 = st.columns(2)
    if col1.button("Continue", type="primary"):
        if not phone.strip():
            st.error("Please enter a phone number.")
        else:
            st.session_state.form_data["phone_number"] = phone.strip()
            # Simulated OTP — replace with real Supabase phone auth later
            st.session_state.otp_code = f"{random.randint(1000, 9999)}"
            go_to("otp")
    if col2.button("Back"):
        go_to("start")

# ---------- 2. OTP verification ----------
elif step == "otp":
    st.subheader("Verify your number")
    st.info(f"Demo mode — your OTP is **{st.session_state.otp_code}**")
    code = st.text_input("Enter the 4-digit code", max_chars=4)
    col1, col2 = st.columns(2)
    if col1.button("Verify", type="primary"):
        if code == st.session_state.otp_code:
            phone = st.session_state.form_data["phone_number"]
            existing = get_driver_by_phone(phone)
            if st.session_state.mode == "login":
                if existing:
                    st.session_state.existing_driver = existing
                    go_to("status")
                else:
                    st.error("No application found for this number. Try signing up instead.")
            else:  # signup
                if existing:
                    st.session_state.existing_driver = existing
                    st.warning("An application already exists for this number.")
                    go_to("status")
                else:
                    go_to("personal")
        else:
            st.error("Incorrect code, try again.")
    if col2.button("Back"):
        go_to("phone")

# ---------- 2b. Existing application status (log-in or duplicate sign-up) ----------
elif step == "status":
    driver = st.session_state.existing_driver or {}
    st.subheader("Your application")
    st.write(f"**Name:** {driver.get('full_name', '—')}")
    st.write(f"**Vehicle:** {driver.get('vehicle_type', '—')} — {driver.get('plate_number', '—')}")
    status = driver.get("status", "pending")
    status_display = {
        "pending": "🕒 Pending review",
        "approved": "✅ Approved",
        "rejected": "❌ Rejected",
    }
    st.write(f"**Status:** {status_display.get(status, status)}")
    if st.button("Start over"):
        reset()

# ---------- 3. Personal details ----------
elif step == "personal":
    st.subheader("Personal details")
    full_name = st.text_input("Full name", value=st.session_state.form_data.get("full_name", ""))
    dob = st.date_input("Date of birth")
    national_id = st.text_input(
        "National ID number", value=st.session_state.form_data.get("national_id", "")
    )
    address = st.text_area("Residential address", value=st.session_state.form_data.get("address", ""))
    col1, col2 = st.columns(2)
    if col1.button("Continue", type="primary"):
        if not (full_name and national_id and address):
            st.error("Please fill in all fields.")
        else:
            st.session_state.form_data.update(
                {
                    "full_name": full_name,
                    "dob": str(dob),
                    "national_id": national_id,
                    "address": address,
                }
            )
            go_to("vehicle")
    if col2.button("Back"):
        go_to("otp")

# ---------- 4. Vehicle details ----------
elif step == "vehicle":
    st.subheader("Vehicle details")
    vehicle_type = st.selectbox("Vehicle type", ["Sedan", "Motorbike", "Van", "Truck"])
    plate_number = st.text_input(
        "Plate number", value=st.session_state.form_data.get("plate_number", "")
    )
    col1, col2 = st.columns(2)
    if col1.button("Continue", type="primary"):
        if not plate_number:
            st.error("Please enter your plate number.")
        else:
            st.session_state.form_data.update(
                {"vehicle_type": vehicle_type, "plate_number": plate_number}
            )
            go_to("payout")
    if col2.button("Back"):
        go_to("personal")

# ---------- 5. Payout details ----------
elif step == "payout":
    st.subheader("Payout details")
    payout_method = st.text_input(
        "Mobile money number or bank account details",
        value=st.session_state.form_data.get("payout_method", ""),
    )
    col1, col2 = st.columns(2)
    if col1.button("Continue", type="primary"):
        if not payout_method:
            st.error("Please enter your payout details.")
        else:
            st.session_state.form_data["payout_method"] = payout_method
            go_to("documents")
    if col2.button("Back"):
        go_to("vehicle")

# ---------- 6. Document capture ----------
elif step == "documents":
    st.subheader("Upload your documents")
    id_doc = st.file_uploader("National ID photo", type=["jpg", "jpeg", "png", "pdf"])
    license_doc = st.file_uploader("Driver's license", type=["jpg", "jpeg", "png", "pdf"])
    reg_doc = st.file_uploader("Vehicle registration", type=["jpg", "jpeg", "png", "pdf"])
    residence_doc = st.file_uploader("Proof of residence", type=["jpg", "jpeg", "png", "pdf"])

    col1, col2 = st.columns(2)
    if col1.button("Continue", type="primary"):
        missing = [
            label
            for label, f in [
                ("National ID", id_doc),
                ("Driver's license", license_doc),
                ("Vehicle registration", reg_doc),
                ("Proof of residence", residence_doc),
            ]
            if f is None
        ]
        if missing:
            st.error(f"Missing: {', '.join(missing)}")
        else:
            st.session_state.form_data["_documents"] = {
                "national_id": id_doc,
                "drivers_license": license_doc,
                "vehicle_registration": reg_doc,
                "proof_of_residence": residence_doc,
            }
            go_to("review")
    if col2.button("Back"):
        go_to("payout")

# ---------- 7. Review & submit ----------
elif step == "review":
    st.subheader("Review your details")
    data = st.session_state.form_data
    st.write(f"**Phone:** {data.get('phone_number')}")
    st.write(f"**Name:** {data.get('full_name')}")
    st.write(f"**DOB:** {data.get('dob')}")
    st.write(f"**National ID:** {data.get('national_id')}")
    st.write(f"**Address:** {data.get('address')}")
    st.write(f"**Vehicle:** {data.get('vehicle_type')} — {data.get('plate_number')}")
    st.write(f"**Payout:** {data.get('payout_method')}")
    st.write(f"**Documents uploaded:** {len(data.get('_documents', {}))}")

    col1, col2 = st.columns(2)
    if col1.button("Submit application", type="primary"):
        with st.spinner("Submitting your application..."):
            try:
                driver = create_driver_profile(data)
                driver_id = driver["id"]
                for doc_type, file in data["_documents"].items():
                    upload_document(driver_id, doc_type, file.getvalue(), file.name)
                st.session_state.driver_id = driver_id
                go_to("complete")
            except Exception as e:
                st.error(f"Something went wrong: {e}")
    if col2.button("Back"):
        go_to("documents")

# ---------- 8. Completion ----------
elif step == "complete":
    st.success("🎉 Application submitted!")
    st.write(f"**Reference ID:** {st.session_state.driver_id}")
    st.write("Status: **Pending review**")
    st.write("We'll notify you once your application has been approved.")
    if st.button("Start a new application"):
        reset()