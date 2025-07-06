import math
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from io import BytesIO

# --- Ρύθμιση Σελίδας ---
st.set_page_config(page_title="Κατανομή Μαθητών", layout="wide")

# --- Κλείδωμα Πρόσβασης με Κωδικό ---
st.sidebar.title("🔐 Κωδικός Πρόσβασης")
password = st.sidebar.text_input("Εισάγετε τον κωδικό:", type="password")
if password != "katanomi2025":
    st.warning("⛔ Παρακαλώ εισάγετε έγκυρο κωδικό για πρόσβαση στην εφαρμογή.")
    st.stop()

# --- Ενεργοποίηση/Απενεργοποίηση Εφαρμογής ---
enable_app = st.sidebar.checkbox("✅ Ενεργοποίηση Εφαρμογής", value=True)
if not enable_app:
    st.info("🔒 Η εφαρμογή είναι προσωρινά απενεργοποιημένη.")
    st.stop()

# --- Δήλωση Πνευματικών Δικαιωμάτων ---
st.sidebar.markdown("""
---
© 2025 Παναγιώτα Γιαννίτσαρου. Απαγορεύεται η χρήση χωρίς ρητή άδεια.
""")

st.title("📘 Δίκαιη Κατανομή Μαθητών Α' Δημοτικού")

# --- Εισαγωγή Excel αρχείου ---
uploaded_file = st.file_uploader("🔹 Εισάγετε αρχείο Excel με μαθητές", type=["xlsx"])

# --- Συνάρτηση: Μετατροπή Ν/Ο και ΦΥΛΟ σε boolean ---
def preprocess_booleans(df):
    binary_columns = [
        'ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ',
        'ΙΚΑΝΟΠΟΙΗΤΙΚΗ ΜΑΘΗΣΙΑΚΗ ΙΚΑΝΟΤΗΤΑ',
        'ΖΩΗΡΟΣ',
        'ΙΔΙΑΙΤΕΡΟΤΗΤΑ',
        'ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ'
    ]
    for col in binary_columns:
        if col in df.columns:
            df[col + '_BOOL'] = df[col].str.upper().str.strip() == 'Ν'

    if 'ΦΥΛΟ' in df.columns:
        df['ΕΙΝΑΙ_ΑΓΟΡΙ'] = df['ΦΥΛΟ'].str.upper().str.strip() == 'Α'
        df['ΕΙΝΑΙ_ΚΟΡΙΤΣΙ'] = df['ΦΥΛΟ'].str.upper().str.strip() == 'Κ'

    return df

# --- Συνάρτηση: Υπολογισμός Τμημάτων ---
def calculate_class_distribution(n_students, max_per_class=25):
    n_classes = math.ceil(n_students / max_per_class)
    q, r = divmod(n_students, n_classes)
    population_targets = [q + 1] * r + [q] * (n_classes - r)
    class_names = [f"Τμήμα {i+1}" for i in range(n_classes)]
    population_plan = dict(zip(class_names, population_targets))
    return n_classes, population_plan

# --- Ανέβηκε Αρχείο ---
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    df = preprocess_booleans(df)
    n_students = len(df)
    n_classes, population_plan = calculate_class_distribution(n_students)

    st.success(f"✅ Το αρχείο περιέχει {n_students} μαθητές – Υπολογίστηκαν {n_classes} τμήματα.")
    st.write("📊 Πληθυσμιακός στόχος ανά τμήμα:")
    st.json(population_plan)

    st.markdown("""
    📌 **Κανόνες Κατανομής:**
    - Κάθε παιδί αξιολογείται με βάση έως 8 χαρακτηριστικά.
    - Ελέγχεται η πιθανή σύγκρουση πριν την τοποθέτηση.
    - Τα παιδιά "κλειδώνουν" μετά τα πρώτα 4 βήματα.
    - Μέγιστο όριο: 25 μαθητές ανά τμήμα.
    - Διαφορά πληθυσμού μεταξύ τμημάτων: το πολύ 1 μαθητής.
    """)

    st.dataframe(df.head(10), height=250)

    # --- Κουμπί Κατανομής ---
    if st.button("🎯 Εκτέλεση Κατανομής (Δοκιμαστική)"):
        df['ΤΜΗΜΑ'] = [f"Τμήμα {i % n_classes + 1}" for i in range(n_students)]
        st.success("✅ Η κατανομή ολοκληρώθηκε!")
        st.dataframe(df)

        # --- Πίνακας Στατιστικών ---
        st.subheader("📊 Στατιστικά Κατανομής")
        st.write(df['ΤΜΗΜΑ'].value_counts())

        # --- Ραβδογράμματα ανά Κατηγορία ---
        show_charts = st.checkbox("📌 Εμφάνιση Ραβδογραμμάτων Κατανομής")
        if show_charts:
            categories = [
                'ΦΥΛΟ',
                'ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ',
                'ΙΚΑΝΟΠΟΙΗΤΙΚΗ ΜΑΘΗΣΙΑΚΗ ΙΚΑΝΟΤΗΤΑ',
                'ΖΩΗΡΟΣ',
                'ΙΔΙΑΙΤΕΡΟΤΗΤΑ',
                'ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ'
            ]
            for cat in categories:
                if cat in df.columns:
                    st.write(f"📌 Κατανομή ανά {cat}")
                    counts = df.groupby(['ΤΜΗΜΑ', cat]).size().unstack(fill_value=0)
                    counts.plot(kind='bar', title=f"Κατανομή ανά {cat}")
                    st.pyplot(plt.gcf())
                    plt.clf()

        # --- Εξαγωγή Excel ---
        output = BytesIO()
        df.to_excel(output, index=False)
        st.download_button("📥 Λήψη Αποτελέσματος Excel", output.getvalue(), file_name="katanomi_output.xlsx")
else:
    st.info("⏳ Παρακαλώ εισάγετε ένα αρχείο Excel για να ξεκινήσετε.")
