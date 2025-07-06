# --- Βήμα 1: Παιδιά Εκπαιδευτικών ---
def assign_teacher_children(df, n_classes):
    teacher_children = df[df['ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ_BOOL'] & df['ΤΜΗΜΑ'].isna()].copy()
    grouped = {f"Τμήμα {i+1}": [] for i in range(n_classes)}
    boys = teacher_children[teacher_children['ΕΙΝΑΙ_ΑΓΟΡΙ']].index.tolist()
    girls = teacher_children[teacher_children['ΕΙΝΑΙ_ΚΟΡΙΤΣΙ']].index.tolist()

    # Εναλλάξ μοίρασμα για ισορροπία φύλου
    combined = []
    while boys or girls:
        if boys:
            combined.append(boys.pop(0))
        if girls:
            combined.append(girls.pop(0))

    for i, idx in enumerate(combined):
        class_id = f"Τμήμα {i % n_classes + 1}"
        df.at[idx, 'ΤΜΗΜΑ'] = class_id

    return df

# --- Βήμα 2: Ζωηροί Μαθητές με λογική φιλίας ---
def assign_lively_students(df, n_classes):
    lively_students = df[df['ΖΩΗΡΟΣ_BOOL']].copy()
    lively_counts = {f"Τμήμα {i+1}": 0 for i in range(n_classes)}

    # Προσμέτρηση ήδη τοποθετημένων ζωηρών (π.χ. παιδιών εκπαιδευτικών)
    for idx, row in lively_students.iterrows():
        if pd.notna(row['ΤΜΗΜΑ']):
            lively_counts[row['ΤΜΗΜΑ']] += 1

    unplaced = lively_students[df['ΤΜΗΜΑ'].isna()]
    total_lively = len(lively_students)

    for idx, row in unplaced.iterrows():
        name = row['ΟΝΟΜΑΤΕΠΩΝΥΜΟ']
        friends = str(row['ΦΙΛΙΑ']).split(',') if pd.notna(row['ΦΙΛΙΑ']) else []
        friends = [f.strip() for f in friends if f.strip()]

        placed = False
        for friend in friends:
            if friend in df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'].values:
                friend_row = df[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == friend].iloc[0]
                if is_mutual_friend(df, name, friend):
                    if friend_row['ΖΩΗΡΟΣ_BOOL']:
                        if total_lively > n_classes:
                            target_class = df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == friend, 'ΤΜΗΜΑ'].values[0]
                            if pd.notna(target_class):
                                df.at[idx, 'ΤΜΗΜΑ'] = target_class
                                lively_counts[target_class] += 1
                                placed = True
                                break
                    elif friend_row['ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ_BOOL']:
                        target_class = df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == friend, 'ΤΜΗΜΑ'].values[0]
                        if pd.notna(target_class):
                            df.at[idx, 'ΤΜΗΜΑ'] = target_class
                            lively_counts[target_class] += 1
                            placed = True
                            break

        if not placed:
            target_class = min(lively_counts, key=lively_counts.get)
            df.at[idx, 'ΤΜΗΜΑ'] = target_class
            lively_counts[target_class] += 1

    return df

# --- Βήμα 3: Παιδιά με Ιδιαιτερότητες ---
def assign_special_students(df, n_classes):
    special_students = df[df['ΙΔΙΑΙΤΕΡΟΤΗΤΑ_BOOL'] & df['ΤΜΗΜΑ'].isna()].copy()
    placed = 0
    total_special = len(special_students)
    class_assignments = {f"Τμήμα {i+1}": [] for i in range(n_classes)}

    # Αρχικά τοποθετούμε έναν μαθητή με ιδιαιτερότητα ανά τμήμα
    for i, (idx, row) in enumerate(special_students.iterrows()):
        if i < n_classes:
            class_id = f"Τμήμα {i+1}"
            df.at[idx, 'ΤΜΗΜΑ'] = class_id
            placed += 1
        else:
            break

    remaining = special_students.iloc[placed:]

    for idx, row in remaining.iterrows():
        name = row['ΟΝΟΜΑΤΕΠΩΝΥΜΟ']
        friends = str(row['ΦΙΛΙΑ']).split(',') if pd.notna(row['ΦΙΛΙΑ']) else []
        friends = [f.strip() for f in friends if f.strip()]

        # Προσπάθεια τοποθέτησης με φίλο ζωηρό ή παιδί εκπαιδευτικού με αμοιβαία φιλία
        for friend in friends:
            if friend in df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'].values:
                friend_row = df[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == friend].iloc[0]
                if is_mutual_friend(df, name, friend):
                    if friend_row['ΖΩΗΡΟΣ_BOOL'] or friend_row['ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ_BOOL']:
                        target_class = friend_row['ΤΜΗΜΑ']
                        if pd.notna(target_class):
                            df.at[idx, 'ΤΜΗΜΑ'] = target_class
                            break

        # Αν δεν τοποθετήθηκε ακόμα, τοποθέτηση με βάση λιγότερους ζωηρούς, χωρίς συγκρούσεις
        if pd.isna(df.at[idx, 'ΤΜΗΜΑ']):
            min_count = float('inf')
            best_class = None
            for class_id in [f"Τμήμα {i+1}" for i in range(n_classes)]:
                class_df = df[df['ΤΜΗΜΑ'] == class_id]
                if row['ΣΥΓΚΡΟΥΣΗ'] in class_df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'].values:
                    continue  # Απόφυγε σύγκρουση
                num_lively = class_df['ΖΩΗΡΟΣ_BOOL'].sum()
                if len(class_df) < 25 and num_lively < min_count:
                    min_count = num_lively
                    best_class = class_id
            if best_class:
                df.at[idx, 'ΤΜΗΜΑ'] = best_class

    return df

# --- Βήμα 4: Φίλοι Παιδιών των Βημάτων 1–3 ---
def assign_friends_of_placed(df, n_classes):
    placed_names = df[df['ΤΜΗΜΑ'].notna()]['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'].tolist()
    unplaced = df[df['ΤΜΗΜΑ'].isna()].copy()

    for idx, row in unplaced.iterrows():
        name = row['ΟΝΟΜΑΤΕΠΩΝΥΜΟ']
        friends = str(row['ΦΙΛΙΑ']).split(',') if pd.notna(row['ΦΙΛΙΑ']) else []
        friends = [f.strip() for f in friends if f.strip()]

        for friend in friends:
            if friend in placed_names and is_mutual_friend(df, name, friend):
                friend_class = df.loc[df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'] == friend, 'ΤΜΗΜΑ'].values[0]
                if pd.isna(friend_class):
                    continue

                # Έλεγχος: ισοκατανομή, <25, όχι σύγκρουση
                class_df = df[df['ΤΜΗΜΑ'] == friend_class]
                if len(class_df) >= 25:
                    continue
                if row['ΣΥΓΚΡΟΥΣΗ'] in class_df['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'].values:
                    continue

                df.at[idx, 'ΤΜΗΜΑ'] = friend_class
                break

    return df

# --- Βήμα 5: Έλεγχος Ποιοτικών Χαρακτηριστικών Τοποθετημένων ---
def analyze_placed_characteristics(df, n_classes):
    summary = {}
    for i in range(n_classes):
        class_id = f"Τμήμα {i+1}"
        class_df = df[df['ΤΜΗΜΑ'] == class_id]
        summary[class_id] = {
            'Αγόρια': class_df['ΕΙΝΑΙ_ΑΓΟΡΙ'].sum(),
            'Κορίτσια': class_df['ΕΙΝΑΙ_ΚΟΡΙΤΣΙ'].sum(),
            'Καλή Γνώση Ελληνικών': class_df['ΚΑΛΗ ΓΝΩΣΗ ΕΛΛΗΝΙΚΩΝ_BOOL'].sum(),
            'Μαθησιακή Ικανότητα': class_df['ΙΚΑΝΟΠΟΙΗΤΙΚΗ ΜΑΘΗΣΙΑΚΗ ΙΚΑΝΟΤΗΤΑ_BOOL'].sum()
        }
    return summary
