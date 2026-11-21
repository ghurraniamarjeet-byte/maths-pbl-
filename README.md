Chi-Square PBL - Streamlit App

Social Media Usage vs Academic Performance (Chi-Square Test of Independence).

Run locally
bash
pip install -r requirements.txt
streamlit run app.py
Edit your details

Open data.py and change TEAM, TEACHER, CLASS_NAME, SUBMISSION_DATE.

Add more real responses
Click "Download CSV template" in the sidebar to see the format (columns: Usage, Marks).
Add one row per student. Allowed values:
Usage: Less than 2 hrs | 2 to 4 hrs | 4 to 6 hrs | More than 6 hrs
Marks: Below 50% | 50-70% | 70-80% | 80%+
Upload the CSV in the sidebar. All tables, tests, graphs and the conclusion update automatically.
Deploy free on Streamlit Community Cloud
Create a free GitHub account and a new public repository.
Upload all files of this folder (app.py, data.py, chi_utils.py, plots.py, requirements.txt, README.md).
Go to share.streamlit.io and sign in with GitHub.
Click "Create app", pick your repository, branch main, main file app.py.
Click Deploy. In 2-3 minutes you get a public link you can share (or turn into a QR code).