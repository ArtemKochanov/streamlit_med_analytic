from reference_values import REFERENCE

def get_reference_range(indicator, age, sex):
    """Возвращает (min, max) для показателя"""
    table = REFERENCE.get(indicator)

    if table is None:
        return None

    sex_key = None
    if sex == "М":
        sex_key = "male"
    elif sex == "Ж":
        sex_key = "female"

    # 1. Показатели, одинаковые всегда (PLT)
    if "all" in table:
        return table["all"]

    # 2. Показатели для одной возрастной группы (MCV)
    if "adult" in table and sex_key is None:
        return table["adult"]

    # 3. Показатели для взрослых, но с разделением по полу (MCH)
    if f"adult_{sex_key}" in table:
        return table[f"adult_{sex_key}"]

    # 4. Показатели с диапазонами по возрасту
    if sex_key in table:
        for (a1, a2, ref_range) in table[sex_key]:
            if a1 <= age <= a2:
                return ref_range

    return None


def evaluate_indicator(value_before, value_after, ref_min, ref_max):
    """Возвращает статус эффективности лечения"""
    before_ok = ref_min <= value_before <= ref_max
    after_ok = ref_min <= value_after <= ref_max

    if before_ok and after_ok:
        return "в норме (стабильно)"

    if not before_ok and after_ok:
        return "улучшение"

    if before_ok and not after_ok:
        return "ухудшение"

    if not before_ok and not after_ok:
        return "нет улучшений"

    return "неопределённо"
