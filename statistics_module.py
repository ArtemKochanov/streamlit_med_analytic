import pandas as pd


def calculate_treatment_statistics(results_df):
    """
    Анализ общей эффективности лечения
    """

    total_patients = len(results_df)

    improvement_count = 0
    worsening_count = 0

    for col in results_df.columns:
        if col == "ID":
            continue

        improvement_count += (results_df[col] == "улучшение").sum()
        worsening_count += (results_df[col] == "ухудшение").sum()

    return {
        "total_patients": total_patients,
        "improvements": int(improvement_count),
        "worsenings": int(worsening_count)
    }