"""Locale source, part four: the browser demo page — the story, the captions, the "O'zingiz sinab ko'ring" box and the
footer (the only place that names the technology; see locales_src.py)."""

from __future__ import annotations

DEMO = {
    "demo.title": ("Test Ustasi — matndan test, xatolar tahlili bilan", "Test Ustasi — тест из текста и разбор ошибок"),
    "demo.lead": ("O'qituvchi darslik matnini yuboradi — bot undan test tuzadi va har bir savolga matndan iqtibos qo'yadi. O'quvchilar telefonda yechadi, "
                  "o'qituvchi esa natijalar jadvali va qaysi savolda nima uchun xato qilinganini ko'radi.",
                  "Учитель присылает учебный текст — бот составляет тест и к каждому вопросу даёт цитату из текста. Ученики решают в телефоне, "
                  "а учитель видит таблицу результатов и где и почему ошибались."),
    "demo.badge": ("Demo · brauzeringizda ishlaydi", "Демо · работает в вашем браузере"),
    "demo.play": ("▶ Hammasini ko'rsatish", "▶ Показать всё"), "demo.reset": ("↺ Boshidan", "↺ Сначала"),
    "demo.nodira": ("Nodira ustoz", "Нодира устоз"), "demo.jasur": ("Jasur", "Жасур"), "demo.try": ("Sinab ko'ring", "Попробовать"),
    "demo.role_nodira": ("biologiya o'qituvchisi · 7-B", "учитель биологии · 7-Б"), "demo.role_jasur": ("7-B sinf o'quvchisi", "ученик 7-Б"),
    "demo.chat": ("Bot", "Бот"), "demo.app": ("Ilova", "Приложение"), "demo.bot_status": ("bot", "бот"), "demo.input": ("Xabar…", "Сообщение…"),
    "demo.time": ("{date} · {time}", "{date} · {time}"), "demo.file": ("Fotosintez.txt", "Fotosintez.txt"),
    "demo.step_1": ("Matn yuboriladi", "Текст отправлен"), "demo.step_2": ("Qoralama va iqtiboslar", "Черновик и цитаты"),
    "demo.step_3": ("Ustoz tahriri", "Правка учителя"), "demo.step_4": ("Nashr: 7-B, 15 daqiqa", "Публикация: 7-Б, 15 мин"),
    "demo.step_5": ("Jasur yechadi", "Жасур решает"), "demo.step_6": ("Natija va xatolar", "Результат и ошибки"),
    "demo.step_7": ("Sinf topshiradi", "Класс сдаёт"), "demo.step_8": ("Xatolar tahlili", "Разбор ошибок"),
    "demo.step_9": ("Qayta test", "Повторный тест"), "demo.step_10": ("Natija oshdi", "Результат вырос"),
    "demo.cap_0": ("Chapda — o'qituvchi Nodira ustozning telefoni, o'ngda — o'quvchi Jasurniki. «Hammasini ko'rsatish»ni bosing yoki istalgan qadamni tanlang.",
                   "Слева — телефон учителя Нодиры устоз, справа — ученика Жасура. Нажмите «Показать всё» или выберите любой шаг."),
    "demo.cap_1": ("08:10. Nodira ustoz «Fotosintez» matnini botga yuboradi va 15 ta savol so'raydi.",
                   "08:10. Нодира устоз отправляет боту текст «Фотосинтез» и просит 15 вопросов."),
    "demo.cap_2": ("Matndan {n} ta sifatli savol chiqdi — bot qolganini to'qib chiqarmadi. Har bir savol ostida matndan iqtibos bor: tekshirish bir qarashda.",
                   "Текст дал {n} качественных вопросов — остальные бот не выдумывал. Под каждым вопросом цитата из текста: проверка с одного взгляда."),
    "demo.cap_3": ("4-savolda «kislorodni» ham qisman to'g'ri — ustoz uni o'chiradi. Keyingi bir savolda variantni o'zgartiradi: «O'simlik» o'rniga «Vodorod».",
                   "В 4-м вопросе «кислород» тоже отчасти верен — учитель удаляет его. В другом вопросе меняет вариант: вместо «Растение» — «Водород»."),
    "demo.cap_4": ("08:30. Sinf — 7-B, vaqt — 15 daqiqa, muddat — bugun 23:59. «Nashr qilish»: 25 ta o'quvchiga xabar ketdi.",
                   "08:30. Класс 7-Б, 15 минут, срок — сегодня 23:59. «Опубликовать»: 25 учеников получили сообщение."),
    "demo.cap_5": ("09:05. Jasur xabarni ochadi. Savollar va variantlar unga o'z tartibida chiqadi, vaqtni server hisoblaydi.",
                   "09:05. Жасур открывает сообщение. Вопросы и варианты у него в своём порядке, время считает сервер."),
    "demo.cap_6": ("Jasur topshirdi: {score}/{total}. Har bir xatosi ostida to'g'ri javob, izoh va matndan iqtibos.",
                   "Жасур сдал: {score}/{total}. Под каждой ошибкой — правильный ответ, пояснение и цитата из текста."),
    "demo.cap_7": ("Qolgan o'quvchilar ham topshiradi — Nodira ustozning jadvali va baholar diagrammasi jonli to'ladi.",
                   "Остальные ученики тоже сдают — таблица и диаграмма оценок у Нодиры устоз заполняются на глазах."),
    "demo.cap_8": ("Tahlil: 6-savolda kuchli o'quvchilar ham adashgan — savolni tekshirish kerak; 3-savolda {pct}% «{letter}» variantni tanlagan — mavzuni qayta tushuntirish kerak.",
                   "Разбор: в 6-м вопросе ошиблись и сильные — вопрос надо проверить; в 3-м {pct}% выбрали «{letter}» — тему стоит объяснить снова."),
    "demo.cap_9": ("«Xato savollar bo'yicha qayta test»: bot qisqa test tuzadi va uni faqat xato qilgan {n} ta o'quvchiga yuboradi.",
                   "«Повторный тест по ошибкам»: бот собирает короткий тест и отправляет его только {n} ученикам, которые ошиблись."),
    "demo.cap_10": ("Qayta testdan keyin shu mavzular bo'yicha guruh natijasi: {before} → {after}. Mavzu o'zlashtirildi.",
                    "После повторного теста результат класса по этим темам: {before} → {after}. Тема усвоена."),
    "demo.try_title": ("O'zingiz sinab ko'ring", "Попробуйте сами"),
    "demo.try_lead": ("Istalgan o'zbekcha darslik matnini qo'ying — shu zahoti test savollari va har birining matndagi iqtibosi chiqadi. Matn hech qayerga yuborilmaydi.",
                      "Вставьте любой учебный текст на узбекском — сразу появятся вопросы теста и цитата из текста к каждому. Текст никуда не отправляется."),
    "demo.try_ph": ("Matnni shu yerga qo'ying…", "Вставьте текст сюда…"), "demo.try_examples": ("Namunalar:", "Примеры:"),
    "demo.try_count": ("{n} ta savol", "вопросов: {n}"),
    "demo.try_empty": ("Bu matndan sifatli savol chiqmadi. Ta'riflar («X — …», «… deb ataladi»), sanalar va sonlar bor matnni sinab ko'ring.",
                       "Из этого текста не вышло качественных вопросов. Попробуйте текст с определениями («X — …», «… deb ataladi»), датами и числами."),
    "demo.try_short": ("Kamida 150 belgili matn qo'ying.", "Вставьте текст от 150 символов."),
    "demo.foot": ("Demo to'liq brauzeringizda ishlaydi: server yo'q, sun'iy intellektga so'rov yuborilmaydi. Savollarni sahifadagi qoidaga asoslangan generator "
                  "tuzadi — serverdagi o'sha kodning JavaScript nusxasi. Haqiqiy bot GEMINI_API_KEY berilsa savollarni sun'iy intellekt yordamida ham tuzadi, "
                  "lekin har bir savol baribir iqtibos tekshiruvidan o'tadi va o'qituvchi tasdiqlamaguncha o'quvchiga bormaydi. Ismlar, sinf va natijalar o'ylab topilgan.",
                  "Демо работает целиком в браузере: сервера нет, запросов к ИИ нет. Вопросы составляет генератор на правилах прямо на странице — JavaScript-копия "
                  "серверного кода. Настоящий бот с GEMINI_API_KEY составляет вопросы и с помощью ИИ, но каждый вопрос всё равно проходит проверку цитаты и не "
                  "попадает к ученикам без одобрения учителя. Имена, класс и результаты вымышлены."),
}
