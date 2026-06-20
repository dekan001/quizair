"""Перетасовка вариантов ответов для равномерного распределения correct_answer.

Проблема: при генерации правильный ответ почти всегда оказывался на позиции 'b'
(76–90% по темам), 'd' — почти никогда. Квиз становился угадываемым.

Решение: для каждого вопроса случайно перемешиваем 4 варианта и переносим
correct_answer на новую позицию правильного текста. Объяснения ссылаются на
содержание правильного ответа, а не на букву, поэтому остаются корректными.

Детерминированно (seed=42) — повторный запуск даёт тот же результат.
Запуск из корня проекта:  python scripts/shuffle_options.py
"""
from __future__ import annotations

import glob
import json
import random
from collections import Counter

SEED = 42


def main() -> None:
    random.seed(SEED)
    grand = Counter()
    for path in sorted(glob.glob("content/questions/*.json")):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for q in data:
            opts = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
            correct_text = opts[ord(q["correct_answer"]) - ord("a")]
            random.shuffle(opts)
            q["option_a"], q["option_b"], q["option_c"], q["option_d"] = opts
            q["correct_answer"] = chr(ord("a") + opts.index(correct_text))
            grand[q["correct_answer"]] += 1
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        c = Counter(q["correct_answer"] for q in data)
        dist = "  ".join(f"{k}:{v}" for k, v in sorted(c.items()))
        print(f"{path.split('/')[-1]:18} {dist}")
    print("-" * 40)
    print("TOTAL  " + "  ".join(f"{k}:{v}" for k, v in sorted(grand.items())))


if __name__ == "__main__":
    main()
