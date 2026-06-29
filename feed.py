# app.py
import streamlit as st
import pandas as pd
import requests
import base64
from datetime import datetime
from zoneinfo import ZoneInfo

st.set_page_config(page_title="Feedback ตรวจสุขภาพปี 1", page_icon="📝")

# ===== GitHub settings from Streamlit secrets =====
GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]      # เช่น "username/repo"
GITHUB_BRANCH = st.secrets.get("GITHUB_BRANCH", "main")
CSV_PATH = st.secrets.get("CSV_PATH", "health_check_feedback.csv")

API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{CSV_PATH}"

headers = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def now_bkk():
    return datetime.now(ZoneInfo("Asia/Bangkok")).strftime("%Y-%m-%d %H:%M:%S")

def load_csv_from_github():
    r = requests.get(API_URL, headers=headers, params={"ref": GITHUB_BRANCH})
    if r.status_code == 200:
        data = r.json()
        content = base64.b64decode(data["content"]).decode("utf-8")
        df = pd.read_csv(pd.io.common.StringIO(content))
        return df, data["sha"]
    elif r.status_code == 404:
        df = pd.DataFrame(columns=[
            "timestamp_bkk",
            "ข้อดี",
            "ข้อพัฒนา",
            "ปัญหาอุปสรรค",
            "ข้อเสนอแนะ"
        ])
        return df, None
    else:
        st.error(f"โหลดข้อมูลจาก GitHub ไม่สำเร็จ: {r.status_code}")
        st.stop()

def save_csv_to_github(df, sha=None):
    csv_text = df.to_csv(index=False)
    encoded = base64.b64encode(csv_text.encode("utf-8")).decode("utf-8")

    payload = {
        "message": f"Add anonymous feedback {now_bkk()}",
        "content": encoded,
        "branch": GITHUB_BRANCH
    }
    if sha:
        payload["sha"] = sha

    r = requests.put(API_URL, headers=headers, json=payload)
    return r.status_code in [200, 201], r.text

# ===== UI =====
st.title("📝 แบบรับฟังความคิดเห็น KU KPS Infirmary")
st.subheader("ภายหลังเริ่มโครงการตรวจสุขภาพนักศึกษาปีที่ 1 ครบ 1 สัปดาห์")

st.info("แบบฟอร์มนี้ไม่ต้องลงชื่อ และใช้เพื่อพัฒนาระบบบริการตรวจสุขภาพให้ดียิ่งขึ้น")

with st.form("feedback_form"):
    good = st.text_area("1) ข้อดีของโครงการ", height=120)
    improve = st.text_area("2) สิ่งที่ควรพัฒนา", height=120)
    obstacles = st.text_area("3) ปัญหา / อุปสรรคที่พบ", height=120)
    suggestion = st.text_area("4) ข้อเสนอแนะเพิ่มเติม", height=120)

    submitted = st.form_submit_button("ส่งความคิดเห็น")

if submitted:
    if not any([good.strip(), improve.strip(), obstacles.strip(), suggestion.strip()]):
        st.warning("กรุณากรอกอย่างน้อย 1 ช่องก่อนกดส่ง")
    else:
        df, sha = load_csv_from_github()

        new_row = {
            "timestamp_bkk": now_bkk(),
            "ข้อดี": good.strip(),
            "ข้อพัฒนา": improve.strip(),
            "ปัญหาอุปสรรค": obstacles.strip(),
            "ข้อเสนอแนะ": suggestion.strip()
        }

        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

        ok, msg = save_csv_to_github(df, sha)

        if ok:
            st.success("ส่งความคิดเห็นเรียบร้อยแล้ว ขอบคุณมากครับ")
            st.balloons()
        else:
            st.error("บันทึกข้อมูลไม่สำเร็จ กรุณาลองใหม่")
            st.code(msg)

st.caption("ข้อมูลถูกจัดเก็บแบบไม่ระบุตัวตน ไม่มีการเก็บชื่อ รหัสนักศึกษา หรืออีเมล")
