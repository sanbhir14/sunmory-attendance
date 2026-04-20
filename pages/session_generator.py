from __future__ import annotations

from datetime import date

import streamlit as st

from utils.session_tools import build_session_record, generate_session_code, session_record_to_csv


st.title("Session Generator")
st.caption("Bikin session code untuk check-in event Sunmory.")

st.info(
    "Mode sekarang belum nulis otomatis ke Google Sheets. Generate code di sini, lalu paste row-nya "
    "ke tab `sessions` di Google Sheets."
)

with st.form("session_generator_form"):
    col1, col2 = st.columns(2)
    with col1:
        session_date = st.date_input("Tanggal session", value=date.today())
        venue = st.selectbox(
            "Venue",
            [
                "Neo Padel Jatiwaringin",
                "Victoria Social Club Kemang",
            ],
        )
    with col2:
        session_slot = st.text_input("Slot / jam main", placeholder="Contoh: 07:00-09:00 atau Morning")
        status = st.selectbox("Status", ["open", "closed"], index=0)

    submitted = st.form_submit_button("Generate Session Code", use_container_width=True)

if submitted:
    st.session_state.generated_session_code = generate_session_code()
    st.session_state.generated_session_record = build_session_record(
        session_date=session_date,
        venue=venue,
        session_slot=session_slot,
        session_code=st.session_state.generated_session_code,
        status=status,
    )

record = st.session_state.get("generated_session_record")

if record:
    st.subheader("Session siap dipakai")

    k1, k2, k3 = st.columns(3)
    k1.metric("Session Code", record["session_code"])
    k2.metric("Tanggal", record["session_date"])
    k3.metric("Status", record["status"])

    st.markdown("**Session ID**")
    st.code(record["session_id"], language="text")

    st.markdown("**Row untuk tab `sessions`**")
    csv_text = session_record_to_csv(record)
    st.code(csv_text, language="csv")

    st.download_button(
        "Download session CSV",
        data=csv_text,
        file_name=f"{record['session_id'].lower()}.csv",
        mime="text/csv",
        use_container_width=True,
    )

    st.markdown("**Format tab `sessions` di Google Sheets**")
    st.dataframe(
        [record],
        hide_index=True,
        use_container_width=True,
        column_config={
            "session_id": "session_id",
            "session_code": "session_code",
            "venue": "venue",
            "session_date": "session_date",
            "session_slot": "session_slot",
            "status": "status",
            "created_at": "created_at",
        },
    )
else:
    st.markdown("**Cara pakai**")
    st.write("Pilih tanggal dan venue, generate code, lalu kasih `Session Code` ke player saat check-in.")
