import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from statistics_module import calculate_treatment_statistics
from prediction_module import predict_next_value
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
from datetime import datetime

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
        improved = 0
        worsened = 0

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

                if status == "улучшение":
                    improved += 1
                elif status == "ухудшение":
                    worsened += 1

        # Итоговая оценка эффективности
        if improved >= 3:
            patient_result["Эффективность лечения"] = "Да"
        else:
            patient_result["Эффективность лечения"] = "Нет"

        results.append(patient_result)

    st.subheader("Результаты анализа")
    st.dataframe(pd.DataFrame(results))

    results_df = pd.DataFrame(results)

    stats = calculate_treatment_statistics(results_df)

    st.subheader("Общая статистика лечения")

    col1, col2, col3 = st.columns(3)

    col1.metric("Всего пациентов", stats["total_patients"])
    col2.metric("Количество улучшений", stats["improvements"])
    col3.metric("Количество ухудшений", stats["worsenings"])

    st.subheader("Распределение результатов лечения")

    counts = results_df.drop(columns=["ID"]).stack().value_counts()

    fig = px.pie(
        names=counts.index,
        values=counts.values,
        title="Распределение результатов анализа"
    )

    pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

    def generate_pdf_report(results_df, stats):
        buffer = io.BytesIO()

        # Горизонтальный PDF
        doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

        styles = getSampleStyleSheet()
        for style_name in styles.byName:
            styles[style_name].fontName = "DejaVu"

        # ✅ Подключаем нормальный шрифт (чтобы НЕ БЫЛО КВАДРАТОВ)
        pdfmetrics.registerFont(TTFont("DejaVu", "DejaVuSans.ttf"))

        elements = []

        # ===== Заголовок =====
        elements.append(Paragraph(
            "Система анализа медицинских данных",
            styles["Title"]
        ))

        elements.append(Spacer(1, 10))

        elements.append(Paragraph(
            "Отчет по анализу эффективности лечения (ОАК)",
            styles["Heading2"]
        ))

        elements.append(Spacer(1, 10))

        elements.append(Paragraph(
            f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            styles["Normal"]
        ))

        elements.append(Spacer(1, 20))

        # ===== Статистика =====
        elements.append(Paragraph("Общая статистика", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        elements.append(Paragraph(f"Всего пациентов: {stats['total_patients']}", styles["Normal"]))
        elements.append(Paragraph(f"Улучшения: {stats['improvements']}", styles["Normal"]))
        elements.append(Paragraph(f"Ухудшения: {stats['worsenings']}", styles["Normal"]))

        elements.append(Spacer(1, 20))

        # ===== Таблица =====
        elements.append(Paragraph("Результаты анализа пациентов", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        table_data = [results_df.columns.tolist()] + results_df.values.tolist()

        table = Table(table_data, repeatRows=1)

        table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, -1), "DejaVu"),
            ("BACKGROUND", (0, 0), (-1, 0), colors.darkblue),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ]))

        # ===== Цвета ячеек =====
        for i, row in enumerate(table_data[1:], start=1):
            for j, cell in enumerate(row):
                if cell == "улучшение":
                    table.setStyle([("BACKGROUND", (j, i), (j, i), colors.lightgreen)])
                elif cell == "ухудшение":
                    table.setStyle([("BACKGROUND", (j, i), (j, i), colors.pink)])
                elif cell == "в норме (стабильно)":
                    table.setStyle([("BACKGROUND", (j, i), (j, i), colors.lightgrey)])

        elements.append(table)

        elements.append(Spacer(1, 20))

        # ===== Итоговый вывод =====
        elements.append(Paragraph("Заключение системы", styles["Heading2"]))
        elements.append(Spacer(1, 10))

        if stats["improvements"] > stats["worsenings"]:
            conclusion = "В целом наблюдается положительная динамика лечения пациентов."
        else:
            conclusion = "Эффективность лечения недостаточна, требуется корректировка терапии."

        elements.append(Paragraph(conclusion, styles["Normal"]))

        elements.append(Spacer(1, 30))

        # ===== Подпись =====
        elements.append(Paragraph("Ответственный специалист: ____________________", styles["Normal"]))
        elements.append(Paragraph("Подпись: ____________________", styles["Normal"]))

        # ===== Сборка =====
        doc.build(elements)

        buffer.seek(0)
        return buffer
    
    pdf_file = generate_pdf_report(results_df, stats)

    st.download_button(
        label="Скачать PDF-отчет",
        data=pdf_file,
        file_name="medical_report.pdf",
        mime="application/pdf"
    )

    st.plotly_chart(fig)

    st.subheader("Тепловая карта изменений показателей")

    indicators = ["RBC", "WBC", "PLT", "HGB", "HTC", "MCV", "MCH"]

    change_data = pd.DataFrame()

    change_data["patient_id"] = df["patient_id"]

    for ind in indicators:
        change_data[ind] = df[f"{ind}_after"] - df[f"{ind}_before"]

    change_data = change_data.set_index("patient_id")

    change_data = change_data.round(2)

    fig = px.imshow(
    change_data,
    color_continuous_scale="RdBu_r",  # красный = рост, синий = снижение
    labels=dict(
        x="Показатель",
        y="Пациент",
        color="Изменение"
    ),
    aspect="auto",
    zmin=0,  # центр шкалы = 0
)

    st.plotly_chart(fig, use_container_width=True)


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
                "Выбранные пациенты": "#ff4a4a",  
                "Другие пациенты": "#838181"  
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

    st.subheader("Прогноз динамики лабораторных показателей")

    indicator = st.selectbox(
        "Выберите показатель для прогноза",
        ["RBC", "WBC", "PLT", "HGB", "HTC", "MCV", "MCH"]
    )

    before = df[f"{indicator}_before"]
    after = df[f"{indicator}_after"]

    predictions = predict_next_value(before, after)

    forecast_df = df[["patient_id"]].copy()
    forecast_df["Текущее значение"] = after
    forecast_df["Прогноз следующего анализа"] = predictions.round(2)

    st.dataframe(forecast_df)

    fig = px.scatter(
        x=after,
        y=predictions,
        labels={
            "x": "Текущее значение",
            "y": "Прогноз следующего анализа"
        },
        title=f"Прогноз динамики показателя {indicator}"
    )

    st.plotly_chart(fig, use_container_width=True)