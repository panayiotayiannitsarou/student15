# --- Βήμα 1: Παιδιά Εκπαιδευτικών (με ισορροπία φύλου, αμοιβαία φιλία και αποφυγή συγκρούσεων) ---
def assign_teacher_children(df, n_classes):
    teacher_children = df[df['ΠΑΙΔΙ ΕΚΠΑΙΔΕΥΤΙΚΟΥ_BOOL'] & df['ΤΜΗΜΑ'].isna()].copy()
    boys = teacher_children[teacher_children['ΕΙΝΑΙ_ΑΓΟΡΙ']].index.tolist()
    girls = teacher_children[teacher_children['ΕΙΝΑΙ_ΚΟΡΙΤΣΙ']].index.tolist()

    combined = []

    # Ζεύγη αγόρι + κορίτσι -> μαζί για ισορροπία
    while boys and girls:
        combined.append((boys.pop(0), girls.pop(0)))

    # Περίσσεια αγοριών
    for boy in boys:
        combined.append((boy,))

    # Περίσσεια κοριτσιών
    for girl in girls:
        combined.append((girl,))

    class_ids = [f"Τμήμα {i+1}" for i in range(n_classes)]
    class_counts = {cid: 0 for cid in class_ids}
    teacher_counts = {cid: 0 for cid in class_ids}
    gender_counts = {cid: {'Α': 0, 'Κ': 0} for cid in class_ids}

    def has_conflict(df, idxs, class_id):
        class_students = df[df['ΤΜΗΜΑ'] == class_id]['ΟΝΟΜΑΤΕΠΩΝΥΜΟ'].tolist()
        for idx in idxs:
            conflict = df.at[idx, 'ΣΥΓΚΡΟΥΣΗ']
            if pd.notna(conflict) and conflict in class_students:
                return True
        return False

    for group in combined:
        best_class = None
        available_classes = [cid for cid in class_ids if not has_conflict(df, group, cid)]
        if not available_classes:
            available_classes = class_ids

        for cid in available_classes:
            t_count = teacher_counts[cid]
            g_count = class_counts[cid]
            g_balance = gender_counts[cid].copy()

            for idx in group:
                if df.at[idx, 'ΕΙΝΑΙ_ΑΓΟΡΙ']:
                    g_balance['Α'] += 1
                else:
                    g_balance['Κ'] += 1

            gender_diff = abs(g_balance['Α'] - g_balance['Κ'])

            if best_class is None or t_count < teacher_counts[best_class] or \
               (t_count == teacher_counts[best_class] and gender_diff < abs(gender_counts[best_class]['Α'] - gender_counts[best_class]['Κ'])) or \
               (t_count == teacher_counts[best_class] and gender_diff == abs(gender_counts[best_class]['Α'] - gender_counts[best_class]['Κ']) and g_count < class_counts[best_class]):
                best_class = cid

        for idx in group:
            df.at[idx, 'ΤΜΗΜΑ'] = best_class
            teacher_counts[best_class] += 1
            class_counts[best_class] += 1
            if df.at[idx, 'ΕΙΝΑΙ_ΑΓΟΡΙ']:
                gender_counts[best_class]['Α'] += 1
            else:
                gender_counts[best_class]['Κ'] += 1

    return df
