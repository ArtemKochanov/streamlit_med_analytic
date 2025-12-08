# data_generator.py
import pandas as pd
import numpy as np
import random
import sys

# reproducible
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

GENDERS = ["М", "Ж"]
DIAGNOSES = [
    "Гипертоническая болезнь",
    "Сахарный диабет 2 типа",
    "Пневмония",
    "Анемия",
    "Инфекция",
    "Хроническое воспаление"
]

def sample_rbc(age, sex):
    # ×10^12 / л
    if sex == "М":
        mu = 4.7
        sd = 0.4
    else:
        mu = 4.5
        sd = 0.4
    return round(np.random.normal(mu, sd), 2)

def sample_wbc():
    # ×10^9 / л
    return round(abs(np.random.normal(7.0, 2.0)), 1)

def sample_plt():
    # ×10^9 / л
    return int(round(abs(np.random.normal(250, 50))))

def sample_hgb(age, sex):
    # г/л
    if sex == "М":
        mu = 145
        sd = 12
    else:
        mu = 130
        sd = 12
    return round(np.random.normal(mu, sd), 1)

def sample_htc():
    # %
    return round(abs(np.random.normal(42, 5)), 1)

def sample_mcv(age):
    # фл
    return round(abs(np.random.normal(90, 6)), 1)

def sample_mch(age, sex):
    # пг
    return round(abs(np.random.normal(29, 2)), 1)

def apply_change(before, better_if_increase=True, improvement_prob=0.6, max_rel_change=0.2):
    """
    Генерирует значение after в зависимости от before.
    better_if_increase: True если повышение показателя = улучшение (например MCV/HGB),
                      False если понижение = улучшение (например CRP — но у нас CRP нет сейчас)
    improvement_prob: вероятность, что пациент улучшился
    max_rel_change: максимально относительное изменение (20%)
    """
    r = random.random()
    frac = random.uniform(0.02, max_rel_change)  # 2% .. max_rel_change
    if r < improvement_prob:
        # improvement
        if better_if_increase:
            after = before * (1 + frac)
        else:
            after = before * (1 - frac)
    elif r < improvement_prob + 0.15:
        # ухудшение
        if better_if_increase:
            after = before * (1 - frac)
        else:
            after = before * (1 + frac)
    else:
        # почти без изменений (шум)
        after = before * (1 + random.uniform(-0.01, 0.01))
    # round according to typical precision
    if isinstance(before, int):
        return int(round(after))
    else:
        # keep reasonable decimals
        return round(after, 2)

def generate_patient_record(i):
    age = random.randint(18, 90)
    sex = random.choice(GENDERS)
    diagnosis = random.choice(DIAGNOSES)

    # Сэмплим показатели до лечения
    rbc_b = sample_rbc(age, sex)           # ×10^12 / л
    wbc_b = sample_wbc()                   # ×10^9 / л
    plt_b = sample_plt()                   # ×10^9 / л
    hgb_b = sample_hgb(age, sex)           # г/л
    htc_b = sample_htc()                   # %
    mcv_b = sample_mcv(age)                # фл
    mch_b = sample_mch(age, sex)           # пг

    # Для большинства из этих показателей повышение == улучшение (RBC, HGB, HTC, MCV, MCH)
    # WBC и PLT улучшение интерпретируется клинически по-разному, но здесь считаем уменьшение WBC/PLT как улучшение при инф/восп.
    # Для простоты задаём правило:
    # - RBC, HGB, HTC, MCV, MCH: повышение = улучшение
    # - WBC: снижение = улучшение (если высоко), но в генераторе делаем общий подход: лучшее направление задаётся параметром

    # вероятность улучшения может зависеть от диагноза (немного)
    if diagnosis == "Пневмония" or diagnosis == "Инфекция":
        improvement_prob = 0.75
    elif diagnosis == "Анемия":
        improvement_prob = 0.65
    else:
        improvement_prob = 0.6

    rbc_a = apply_change(rbc_b, better_if_increase=True, improvement_prob=improvement_prob, max_rel_change=0.18)
    hgb_a = apply_change(hgb_b, better_if_increase=True, improvement_prob=improvement_prob, max_rel_change=0.18)
    htc_a = apply_change(htc_b, better_if_increase=True, improvement_prob=improvement_prob, max_rel_change=0.15)
    mcv_a = apply_change(mcv_b, better_if_increase=True, improvement_prob=improvement_prob, max_rel_change=0.08)
    mch_a = apply_change(mch_b, better_if_increase=True, improvement_prob=improvement_prob, max_rel_change=0.08)

    # WBC: обычно снижение при разрешении инфекции — считаем снижение = улучшение
    wbc_a = apply_change(wbc_b, better_if_increase=False, improvement_prob=improvement_prob, max_rel_change=0.25)
    # PLT: небольшой разброс, пусть снижение/увеличение случайно
    plt_a = apply_change(plt_b, better_if_increase=False, improvement_prob=improvement_prob, max_rel_change=0.15)

    # Простое итоговое поле treatment_effective: считаем, что улучшение если >=3 показателя перешли ближе к норме
    # Зададим простую эвристику: сравним количество показателей, которые изменились в "лучшую" сторону
    improved_count = 0
    for before, after, better_if_inc in [
        (rbc_b, rbc_a, True),
        (hgb_b, hgb_a, True),
        (htc_b, htc_a, True),
        (mcv_b, mcv_a, True),
        (mch_b, mch_a, True),
        (wbc_b, wbc_a, False),
        (plt_b, plt_a, False),
    ]:
        if better_if_inc:
            if after > before * 1.01:  # >1% improvement
                improved_count += 1
        else:
            if after < before * 0.99:
                improved_count += 1

    treatment_effective = "Да" if improved_count >= 3 else "Нет"

    return {
        "patient_id": i,
        "age": age,
        "gender": sex,
        "diagnosis": diagnosis,
        "RBC_before": rbc_b,
        "RBC_after": rbc_a,
        "WBC_before": wbc_b,
        "WBC_after": wbc_a,
        "PLT_before": plt_b,
        "PLT_after": plt_a,
        "HGB_before": hgb_b,
        "HGB_after": hgb_a,
        "HTC_before": htc_b,
        "HTC_after": htc_a,
        "MCV_before": mcv_b,
        "MCV_after": mcv_a,
        "MCH_before": mch_b,
        "MCH_after": mch_a,
        "treatment_effective": treatment_effective
    }

def generate_dataset(n=200):
    rows = []
    for i in range(1, n+1):
        rows.append(generate_patient_record(i))
    df = pd.DataFrame(rows)
    return df

def save_csv(filename="oac_data.csv", n=200):
    df = generate_dataset(n)
    df.to_csv(filename, index=False, encoding="utf-8-sig")
    print(f"Saved {len(df)} rows to {filename}")

if __name__ == "__main__":
    # optional CLI arg: number of records
    n = 200
    if len(sys.argv) > 1:
        try:
            n = int(sys.argv[1])
        except:
            pass
    save_csv("oac_data.csv", n)
