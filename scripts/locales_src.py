"""The source of shared/locales/uz.json and ru.json (run ``python scripts/locales_src.py`` after editing).

Each entry is key: (Uzbek, Russian). The bot, the Mini App and the demo read the generated JSON files. Parameters in
braces are HTML-escaped when filled in."""

from __future__ import annotations

import json
from pathlib import Path

MONTHS_UZ = ["yanvar", "fevral", "mart", "aprel", "may", "iyun", "iyul", "avgust", "sentabr", "oktabr", "noyabr", "dekabr"]
MONTHS_RU = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]

T = {
    "fmt.day": ("{d}-{month}", "{d} {month}"),
    "fmt.when": ("{date}, {time}", "{date}, {time}"),
    "fmt.today": ("bugun, {time}", "сегодня, {time}"),
    "fmt.tomorrow": ("ertaga, {time}", "завтра, {time}"),
    "fmt.pct": ("{n}%", "{n}%"),
    "fmt.of": ("{a}/{b}", "{a}/{b}"),
    "fmt.questions": ("{n} ta savol", "вопросов: {n}"),
    "fmt.minutes": ("{n} daqiqa", "{n} мин"),
    "fmt.students": ("{n} ta o'quvchi", "учеников: {n}"),
    "fmt.time": ("{m}:{s}", "{m}:{s}"),
    "fmt.grade": ("{g} baho", "оценка {g}"),
    "lbl.avg": ("O'rtacha", "Средний"), "lbl.median": ("Median", "Медиана"), "lbl.done": ("Topshirdi", "Сдали"),
    "lbl.deadline": ("Muddat", "Срок"), "lbl.code": ("Kod", "Код"), "lbl.score": ("Ball", "Баллы"), "lbl.time": ("Vaqt", "Время"),
    "flag.key": ("Kuchli o'quvchilar ham xato qildi — savol yoki javob kaliti noto'g'ri bo'lishi mumkin, tekshiring.",
                 "Ошиблись и сильные ученики — возможно, неверен вопрос или ключ ответа, проверьте."),
    "flag.key_pick": ("Kuchli o'quvchilar ham xato qildi: {pct}% «{letter}» variantni tanlagan — savol yoki javob kaliti noto'g'ri bo'lishi mumkin, tekshiring.",
                      "Ошиблись и сильные ученики: {pct}% выбрали вариант «{letter}» — возможно, неверен вопрос или ключ ответа, проверьте."),
    "flag.hard": ("Ko'pchilik xato qildi — mavzuni qayta tushuntiring.", "Большинство ошиблось — объясните тему ещё раз."),
    "flag.hard_pick": ("Ko'pchilik xato qildi: {pct}% «{letter}» variantni tanlagan — mavzuni qayta tushuntiring.",
                       "Большинство ошиблось: {pct}% выбрали вариант «{letter}» — объясните тему ещё раз."),
    "flag.easy": ("Juda oson — deyarli hamma to'g'ri topdi.", "Очень лёгкий — почти все ответили верно."),
    "flag.few": ("Tahlil uchun kamida 5 ta natija kerak.", "Для анализа нужно не меньше 5 результатов."),
    "err.generic": ("Bu amalni bajarib bo'lmadi. Qaytadan urinib ko'ring.", "Не получилось. Попробуйте ещё раз."),
    "err.auth": ("Kirish ma'lumoti eskirgan. Ilovani bot orqali qayta oching.", "Данные входа устарели. Откройте приложение заново через бота."),
    "err.rate": ("Juda tez! Bir oz kutib, qayta urinib ko'ring.", "Слишком часто! Подождите немного и попробуйте снова."),
    "err.forbidden": ("Bu bo'lim siz uchun emas.", "Этот раздел не для вас."),
    "err.not_found": ("Topilmadi yoki sizga tegishli emas.", "Не найдено или вам недоступно."),
    "err.too_big": ("Fayl juda katta. 10 MB gacha bo'lsin.", "Файл слишком большой. До 10 МБ."),
    "err.role_teacher": ("Siz o'qituvchi sifatida ro'yxatdan o'tgansiz: o'quvchi bo'lib qo'shilib bo'lmaydi.",
                         "Вы зарегистрированы как учитель: присоединиться учеником нельзя."),
    "err.role_student": ("Siz o'quvchi sifatida ro'yxatdan o'tgansiz: test tuzish o'qituvchilar uchun.",
                         "Вы зарегистрированы как ученик: создание тестов — для учителей."),
    "err.invite": ("Taklif havolasi noto'g'ri yoki muddati o'tgan. O'qituvchingizdan yangisini so'rang.",
                   "Ссылка-приглашение неверна или устарела. Попросите у учителя новую."),
    "err.code": ("Bunday kodli test topilmadi. Kodni tekshirib, qayta yozing.", "Тест с таким кодом не найден. Проверьте код."),
    "err.closed": ("Bu testning muddati tugagan.", "Срок этого теста истёк."),
    "err.class_name": ("Sinf nomi 1–24 belgidan iborat bo'lsin, masalan: 7-B.", "Название класса — от 1 до 24 символов, например: 7-Б."),
    "err.class_exists": ("Bunday nomli sinf bor.", "Класс с таким названием уже есть."),
    "err.too_many": ("Sinflar soni chegarasiga yetdingiz.", "Достигнут предел числа классов."),
    "err.too_short": ("Matn juda qisqa: kamida 150 belgili darslik matnini yuboring.", "Текст слишком короткий: пришлите не меньше 150 символов."),
    "err.too_long": ("Matn juda uzun: 30 000 belgigacha yuboring yoki bo'lib-bo'lib yuboring.", "Текст слишком длинный: до 30 000 символов или частями."),
    "err.no_questions": ("Bu matndan sifatli savol chiqmadi. Ta'riflar, sanalar va asosiy tushunchalar bor matnni yuboring.",
                         "Из этого текста не вышло качественных вопросов. Пришлите текст с определениями, датами и ключевыми понятиями."),
    "err.no_more": ("Bu matndan boshqa savol topilmadi.", "Других вопросов из этого текста не нашлось."),
    "err.last_question": ("Testda kamida bitta savol qolishi kerak.", "В тесте должен остаться хотя бы один вопрос."),
    "err.published": ("Test nashr qilingan: savollarini endi o'zgartirib bo'lmaydi.", "Тест опубликован: вопросы уже нельзя менять."),
    "err.not_published": ("Test hali nashr qilinmagan.", "Тест ещё не опубликован."),
    "err.no_class": ("Avval sinfni tanlang.", "Сначала выберите класс."),
    "err.minutes": ("Vaqt 1 dan 180 daqiqagacha bo'lsin.", "Время — от 1 до 180 минут."),
    "err.attempts": ("Urinishlar soni 1 dan 5 gacha bo'lsin.", "Попыток — от 1 до 5."),
    "err.deadline": ("Muddat kamida 5 daqiqadan keyin va 60 kun ichida bo'lsin.", "Срок — не раньше чем через 5 минут и в пределах 60 дней."),
    "err.title": ("Nom 2–80 belgidan iborat bo'lsin.", "Название — от 2 до 80 символов."),
    "err.no_attempts": ("Urinishlaringiz tugagan.", "Попытки закончились."),
    "err.submitted": ("Javoblar allaqachon topshirilgan.", "Ответы уже сданы."),
    "err.not_submitted": ("Natija testni topshirgandan keyin ko'rinadi.", "Результат появится после сдачи теста."),
    "err.no_retest": ("Qayta test uchun xato ko'p qilingan mavzu yo'q — guruh yaxshi natija ko'rsatdi.",
                      "Для повторного теста нет темы с частыми ошибками — класс справился хорошо."),
    "err.question": ("Savol ma'lumoti noto'g'ri.", "Неверные данные вопроса."),
    "err.q_stem": ("Savol matni 8–300 belgidan iborat bo'lsin.", "Текст вопроса — от 8 до 300 символов."),
    "err.q_options": ("To'rtta variant bo'lishi kerak.", "Нужно ровно четыре варианта."),
    "err.q_option": ("Har bir variant 1–120 belgidan iborat bo'lsin.", "Каждый вариант — от 1 до 120 символов."),
    "err.q_distinct": ("Variantlar bir-biridan farq qilsin.", "Варианты должны различаться."),
    "err.q_correct": ("To'g'ri javobni belgilang.", "Отметьте правильный ответ."),
    "err.q_topic": ("Mavzu 2–40 belgidan iborat bo'lsin.", "Тема — от 2 до 40 символов."),
    "err.file_type": ("Bu faylni o'qib bo'lmadi. PDF, Word (.docx) yoki .txt yuboring.", "Не удалось прочитать файл. Пришлите PDF, Word (.docx) или .txt."),
    "err.pages": ("PDFda sahifalar juda ko'p: 30 sahifagacha bo'lgan qismini yuboring.", "В PDF слишком много страниц: пришлите часть до 30 страниц."),
    "err.encrypted": ("PDF parol bilan himoyalangan. Parolsiz nusxasini yuboring.", "PDF защищён паролем. Пришлите копию без пароля."),
    "err.broken": ("PDF fayl buzilgan. Boshqa nusxasini yoki matnning o'zini yuboring.", "PDF повреждён. Пришлите другую копию или сам текст."),
    "err.no_text": ("Bu faylda matn topilmadi (u rasm yoki skaner qilingan bo'lishi mumkin). Matnni nusxalab yuboring.",
                    "В файле не найден текст (возможно, это скан или картинка). Пришлите текст."),
    "err.slow": ("Faylni o'qish juda uzoq davom etdi. Matnni nusxalab yuboring.", "Файл читается слишком долго. Пришлите текст."),
    "err.time_up": ("Vaqt tugadi — javoblaringiz avtomatik topshirildi.", "Время вышло — ответы сданы автоматически."),
}


def build() -> dict[str, dict[str, str]]:
    from locales_app import APP
    from locales_bot import BOT
    from locales_demo import DEMO

    out: dict[str, dict[str, str]] = {"uz": {}, "ru": {}}
    merged = {}
    for part in (T, BOT, APP, DEMO):
        for key in part:
            assert key not in merged, f"duplicate key {key}"
        merged.update(part)
    for key, (uz, ru) in merged.items():
        out["uz"][key] = uz
        out["ru"][key] = ru
    for i, (uz, ru) in enumerate(zip(MONTHS_UZ, MONTHS_RU, strict=True), 1):
        out["uz"][f"month.{i}"] = uz
        out["ru"][f"month.{i}"] = ru
    return out


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent / "shared" / "locales"
    root.mkdir(parents=True, exist_ok=True)
    cats = build()
    for lang, cat in cats.items():
        (root / f"{lang}.json").write_bytes((json.dumps(cat, ensure_ascii=False, indent=1) + "\n").encode())
    print("wrote", ", ".join(f"{lang}.json ({len(cat)} keys)" for lang, cat in cats.items()))
