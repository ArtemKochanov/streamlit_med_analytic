import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from analyzer import get_reference_range, evaluate_indicator


st.title("Анализ эффективности лечения по показателям ОАК")

uploaded = st.file_uploader("Загрузите табличный файл в формате-CSV", type=["csv"], help="Если Вы не знаете как создать файл формата CSV, и какие столбцы он должен содержать - обратитесь к Вашему системному администратору")

# st.badge(label="Программный модуль для анализа медицинских материлов", color="none")

if uploaded:
    df = pd.read_csv(uploaded)
    st.subheader("Загруженные данные", help="Кликните на столбец для его сортировки")
    st.dataframe(df)

    results = []

    for _, row in df.iterrows():
        age = row["age"]
        sex = row["gender"]

        patient_result = {"ID": row["patient_id"]}

        for indicator in ["RBC", "WBC", "PLT", "HGB", "HTC", "MCV", "MCH"]:
            ref = get_reference_range(indicator, age, sex)
            if ref:
                rmin, rmax = ref
                status = evaluate_indicator(
                    row[f"{indicator}_before"],
                    row[f"{indicator}_after"],
                    rmin, rmax
                )
                patient_result[indicator] = status

        results.append(patient_result)

    st.subheader("Результаты анализа")
    st.dataframe(pd.DataFrame(results))

    # ---- Автоматические графики ----
    st.subheader("Графики изменения показателей")

    indicators = ["RBC", "WBC", "PLT", "HGB", "HTC", "MCV", "MCH"]

    for indicator in indicators:
        before_col = f"{indicator}_before"
        after_col = f"{indicator}_after"

        if before_col in df.columns and after_col in df.columns:
            st.write(f"### Изменение {indicator}")

            fig, ax = plt.subplots()
            ax.plot(df["patient_id"], df[before_col], label="До")
            ax.plot(df["patient_id"], df[after_col], label="После")
            ax.set_xlabel("ID пациента")
            ax.set_ylabel(indicator)
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

        # ---- Интерактивный анализ по выбранным пациентам ----
    st.subheader("Интерактивный анализ динамики показателей")

    indicator = st.selectbox(
        "Выберите показатель",
        ["RBC", "WBC", "PLT", "HGB", "HTC", "MCV", "MCH"]
    )

    selected_patients = st.multiselect(
        "Выберите пациентов (одного или нескольких)",
        df["patient_id"].unique(),
        default=df["patient_id"].unique()[:1]
    )

    if selected_patients:
        import plotly.express as px

        plot_df = df[[
            "patient_id",
            f"{indicator}_before",
            f"{indicator}_after"
        ]].copy()

        plot_df.columns = [
            "PatientID",
            "До лечения",
            "После лечения"
        ]

        plot_df = plot_df.melt(
            id_vars="PatientID",
            var_name="Этап",
            value_name="Значение"
        )

        plot_df["Группа"] = plot_df["PatientID"].apply(
            lambda x: "Выбранные пациенты" if x in selected_patients else "Другие пациенты"
        )

        fig = px.line(
            plot_df,
            x="Этап",
            y="Значение",
            line_group="PatientID",
            color="Группа",
            hover_data=["PatientID"],
            color_discrete_map={
                "Выбранные пациенты": "#ff4a4a",   # красный
                "Другие пациенты": "#838181"       # серый
            }
        )

        fig.update_traces(
            opacity=0.2,
            
            selector=dict(name="Другие пациенты")
        )

        fig.update_traces(
            opacity=1,
            line=dict(width=4),
            selector=dict(name="Выбранные пациенты")
        )

        fig.update_layout(
            xaxis_title="Этап лечения",
            yaxis_title=indicator,
            legend_title=""
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Выберите хотя бы одного пациента для отображения графика.")


