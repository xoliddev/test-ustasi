"""Locale source, part two: the bot's screens, buttons and the messages it sends on its own (see locales_src.py)."""

from __future__ import annotations

BOT = {
    "btn.back": ("⬅️ Orqaga", "⬅️ Назад"), "btn.menu": ("🏠 Menyu", "🏠 Меню"), "btn.lang": ("🇷🇺 Русский", "🇺🇿 O'zbekcha"),
    "btn.help": ("❓ Yordam", "❓ Помощь"), "btn.teacher": ("👩‍🏫 Men o'qituvchiman", "👩‍🏫 Я учитель"), "btn.student": ("🎓 Men o'quvchiman", "🎓 Я ученик"),
    "btn.new_test": ("📝 Yangi test", "📝 Новый тест"), "btn.tests": ("📋 Testlarim", "📋 Мои тесты"), "btn.classes": ("👥 Sinflarim", "👥 Мои классы"),
    "btn.app": ("📱 Ilovani ochish", "📱 Открыть приложение"), "btn.review": ("📱 Ko'rib chiqish va nashr qilish", "📱 Проверить и опубликовать"),
    "btn.results": ("📊 Natijalar", "📊 Результаты"), "btn.analysis": ("🧩 Xatolar tahlili", "🧩 Разбор ошибок"),
    "btn.retest": ("🔁 Xato savollar bo'yicha qayta test", "🔁 Повторный тест по ошибкам"), "btn.retest_send": ("✅ Yuborish", "✅ Отправить"),
    "btn.csv": ("📥 Excel uchun fayl (CSV)", "📥 Файл для Excel (CSV)"), "btn.new_class": ("➕ Yangi sinf", "➕ Новый класс"),
    "btn.code": ("🔑 Test kodini kiritish", "🔑 Ввести код теста"), "btn.start_test": ("▶️ Testni boshlash", "▶️ Начать тест"),
    "btn.continue": ("▶️ Davom ettirish", "▶️ Продолжить"), "btn.my_result": ("✅ Natijam", "✅ Мой результат"),
    "btn.n": ("{n} ta", "{n}"), "btn.mix_easy": ("🙂 Osonroq", "🙂 Полегче"), "btn.mix_mixed": ("⚖️ Aralash", "⚖️ Смешанно"),
    "btn.mix_hard": ("🧠 Qiyinroq", "🧠 Посложнее"),
    "bot.hello": ("Assalomu alaykum! Men — <b>Test Ustasi</b>.\n\nO'qituvchi darslik matni yoki PDF yuboradi — men undan test tuzaman, har bir savolga "
                  "matndan iqtibos qo'yaman. O'quvchilar testni telefonida yechadi, o'qituvchi esa natijalar jadvali va qaysi savollarda xato qilinganini "
                  "ko'radi.\n\nSiz kimsiz?",
                  "Здравствуйте! Я — <b>Test Ustasi</b>.\n\nУчитель присылает учебный текст или PDF — я составляю по нему тест и к каждому вопросу "
                  "даю цитату из текста. Ученики решают тест в телефоне, а учитель видит таблицу результатов и разбор ошибок.\n\nКто вы?"),
    "bot.menu_teacher": ("👩‍🏫 <b>{name}</b>\nSinflar: {classes} · testlar: {tests}\n\nYangi test uchun darslik matnini shu chatga yuboring yoki PDF / Word "
                         "faylini jo'nating.",
                         "👩‍🏫 <b>{name}</b>\nКлассов: {classes} · тестов: {tests}\n\nДля нового теста пришлите в этот чат учебный текст или файл PDF / Word."),
    "bot.menu_student": ("🎓 <b>{name}</b>\n{line}", "🎓 <b>{name}</b>\n{line}"),
    "bot.student_new": ("Yangi testlar: {n}. «📋 Testlarim» tugmasini bosing.", "Новых тестов: {n}. Нажмите «📋 Мои тесты»."),
    "bot.student_none": ("Hozircha yangi test yo'q. O'qituvchingiz test bersa, shu yerga xabar keladi.",
                         "Новых тестов пока нет. Когда учитель даст тест, сообщение придёт сюда."),
    "bot.student_join": ("O'qituvchingiz bergan havolani bosing yoki testning 6 belgili kodini shu yerga yozing.",
                         "Нажмите ссылку от учителя или напишите сюда 6-значный код теста."),
    "bot.help_teacher": ("❓ <b>Qanday ishlaydi</b>\n\n1. Darslik matnini yoki PDF ni yuboring, nechta savol kerakligini tanlang.\n"
                         "2. Ilovada qoralamani ko'rib chiqing: har bir savol yonida matndan iqtibos bor. Keraksizini o'chiring, tahrirlang.\n"
                         "3. Sinf, vaqt va muddatni belgilab, «Nashr qilish»ni bosing — o'quvchilarga xabar boradi.\n"
                         "4. Natijalar jonli yangilanadi; «Xatolar tahlili» qaysi savolda va qaysi variantda xato qilinganini ko'rsatadi.\n"
                         "5. «Qayta test» xato qilingan mavzular bo'yicha qisqa testni faqat xato qilganlarga yuboradi.",
                         "❓ <b>Как это работает</b>\n\n1. Пришлите учебный текст или PDF и выберите число вопросов.\n"
                         "2. Проверьте черновик в приложении: у каждого вопроса есть цитата из текста. Лишнее удалите, поправьте.\n"
                         "3. Укажите класс, время и срок и нажмите «Опубликовать» — ученики получат сообщение.\n"
                         "4. Результаты обновляются сразу; «Разбор ошибок» показывает, где и какой вариант выбирали.\n"
                         "5. «Повторный тест» отправит короткий тест по трудным темам только тем, кто ошибся."),
    "bot.help_student": ("❓ <b>Qanday ishlaydi</b>\n\nO'qituvchingiz test bersa, shu yerga xabar keladi. «▶️ Testni boshlash»ni bosing: savollar birma-bir "
                         "chiqadi, vaqt yuqorida ko'rinadi, javoblaringiz darhol saqlanadi. Oxirida «Topshirish»ni bosing.",
                         "❓ <b>Как это работает</b>\n\nКогда учитель даст тест, сюда придёт сообщение. Нажмите «▶️ Начать тест»: вопросы идут по одному, "
                         "время видно сверху, ответы сохраняются сразу. В конце нажмите «Сдать»."),
    "bot.new_test": ("📝 <b>Yangi test</b>\n\nDarslik matnini shu chatga yuboring (nusxalab qo'ying) yoki PDF / Word faylini jo'nating.\n"
                     "• matn: 150 dan 30 000 belgigacha\n• PDF: 10 MB gacha, 30 sahifagacha\n\nHar bir savolga matndan iqtibos qo'yaman — "
                     "tekshirish oson bo'ladi.",
                     "📝 <b>Новый тест</b>\n\nПришлите в этот чат учебный текст (скопируйте) или файл PDF / Word.\n• текст: от 150 до 30 000 символов\n"
                     "• PDF: до 10 МБ и 30 страниц\n\nК каждому вопросу дам цитату из текста — проверять легко."),
    "bot.reading": ("⏳ Fayl o'qilmoqda…", "⏳ Читаю файл…"),
    "bot.making": ("⏳ Savollar tuzilmoqda…", "⏳ Составляю вопросы…"),
    "bot.got_source": ("📄 <b>{title}</b> qabul qilindi\n{passages} ta bo'lim · {chars} belgi\n\nNechta savol tuzay?",
                       "📄 <b>{title}</b> получен\nРазделов: {passages} · символов: {chars}\n\nСколько вопросов составить?"),
    "bot.ask_mix": ("📄 <b>{title}</b> · {n} ta savol\n\nQiyinligi qanday bo'lsin?", "📄 <b>{title}</b> · вопросов: {n}\n\nКакой сложности?"),
    "bot.draft_ready": ("✅ <b>Qoralama tayyor: {title}</b>\n{count}{fewer}\n\nHar bir savol yonida matndan iqtibos bor. Ko'rib chiqing, keraksizini o'chiring "
                        "yoki tahrirlang, so'ng nashr qiling — o'quvchilar testni faqat shundan keyin ko'radi.",
                        "✅ <b>Черновик готов: {title}</b>\n{count}{fewer}\n\nУ каждого вопроса есть цитата из текста. Проверьте, лишнее удалите или "
                        "поправьте и опубликуйте — ученики увидят тест только после этого."),
    "bot.fewer": (" (so'ralgani {asked} ta edi: matndan shuncha sifatli savol chiqdi)", " (просили {asked}: столько качественных вопросов дал текст)"),
    "bot.no_app": ("Ilova manzili sozlanmagan: .env faylida PUBLIC_URL ni yozing.", "Адрес приложения не настроен: укажите PUBLIC_URL в .env."),
    "bot.tests": ("📋 <b>Testlarim</b>", "📋 <b>Мои тесты</b>"), "bot.tests_none": ("Hali test yo'q. Darslik matnini yuboring — birinchisini tuzamiz.",
                                                                          "Тестов пока нет. Пришлите учебный текст — составим первый."),
    "bot.test_draft_row": ("📝 {title} · qoralama", "📝 {title} · черновик"), "bot.test_row": ("✅ {title} · {done}/{people}", "✅ {title} · {done}/{people}"),
    "bot.test_retest_row": ("🔁 {title} · {done}/{people}", "🔁 {title} · {done}/{people}"),
    "bot.card_draft": ("📝 <b>{title}</b>\nQoralama · {count}\n\nNashr qilish uchun ilovada ko'rib chiqing.",
                       "📝 <b>{title}</b>\nЧерновик · {count}\n\nЧтобы опубликовать, проверьте его в приложении."),
    "bot.card": ("✅ <b>{title}</b> · {cls}\n{count} · {minutes}{deadline}\n{code}\n\n{done_lbl}: {done}/{people} · {avg_lbl}: {avg}{flags}",
                 "✅ <b>{title}</b> · {cls}\n{count} · {minutes}{deadline}\n{code}\n\n{done_lbl}: {done}/{people} · {avg_lbl}: {avg}{flags}"),
    "bot.card_deadline": (" · muddat {when}", " · срок {when}"), "bot.card_code": ("Kod: <code>{code}</code>", "Код: <code>{code}</code>"),
    "bot.card_retest": ("Qayta test", "Повторный тест"),
    "bot.flags": ("\n⚠️ Tekshiring: {n} ta savolda kuchli o'quvchilar ham xato qilgan.", "\n⚠️ Проверьте: в {n} вопр. ошиблись и сильные ученики."),
    "bot.flags_hard": ("\n📌 {n} ta savolni ko'pchilik xato qilgan.", "\n📌 В {n} вопр. ошиблось большинство."),
    "bot.retest_ask": ("🔁 <b>Qayta test</b>\nMavzular: {topics}\n{count} ta o'quvchiga yuboriladi: {names}\n\nYuboraymi?",
                       "🔁 <b>Повторный тест</b>\nТемы: {topics}\nПолучат учеников: {count} — {names}\n\nОтправить?"),
    "bot.retest_sent": ("🔁 Qayta test yuborildi: {students} ta o'quvchiga, {count}.", "🔁 Повторный тест отправлен: учеников — {students}, {count}."),
    "bot.retest_again": ("🔁 Bu test uchun qayta test allaqachon yuborilgan.", "🔁 Повторный тест по нему уже отправлен."),
    "bot.csv": ("📥 <b>{title}</b> — natijalar. Excel'da ochiladi.", "📥 <b>{title}</b> — результаты. Открывается в Excel."),
    "bot.classes": ("👥 <b>Sinflarim</b>\nSinfga o'quvchilar taklif havolasi orqali qo'shiladi.", "👥 <b>Мои классы</b>\nУченики присоединяются по ссылке-приглашению."),
    "bot.class_row": ("👥 {name} · {n}", "👥 {name} · {n}"),
    "bot.class": ("👥 <b>{name}</b> · {count}\n{names}\n\nO'quvchilar shu havola orqali qo'shiladi ({days} kun ishlaydi):\n{link}",
                  "👥 <b>{name}</b> · {count}\n{names}\n\nУченики присоединяются по этой ссылке (действует {days} дн.):\n{link}"),
    "bot.ask_class": ("Yangi sinf nomini yozing (masalan: 7-B):", "Напишите название нового класса (например: 7-Б):"),
    "bot.class_made": ("✅ <b>{name}</b> sinfi ochildi.", "✅ Класс <b>{name}</b> создан."),
    "bot.ask_code": ("Testning 6 belgili kodini yozing:", "Напишите 6-значный код теста:"),
    "bot.joined": ("✅ Siz <b>{cls}</b> sinfiga qo'shildingiz ({teacher}).", "✅ Вы в классе <b>{cls}</b> ({teacher})."),
    "bot.joined_code": ("✅ <b>{cls}</b> sinfi · 📝 {title}", "✅ Класс <b>{cls}</b> · 📝 {title}"),
    "bot.my_tests": ("📋 <b>Testlarim</b>", "📋 <b>Мои тесты</b>"), "bot.my_none": ("Hozircha test yo'q.", "Тестов пока нет."),
    "bot.my_new": ("🆕 {title} · {count}", "🆕 {title} · {count}"), "bot.my_working": ("⏳ {title} · davom etmoqda", "⏳ {title} · в процессе"),
    "bot.my_done": ("✅ {title} · {score}/{count}", "✅ {title} · {score}/{count}"), "bot.my_closed": ("⌛ {title} · muddati o'tgan", "⌛ {title} · срок истёк"),
    "bot.stale": ("Bu tugma eskirgan. Menyu ochildi.", "Кнопка устарела. Открыто меню."),
    "bot.short_text": ("Bu matn test uchun juda qisqa (kamida 150 belgi). Darslik matnini to'liqroq yuboring.",
                       "Текст слишком короткий для теста (от 150 символов). Пришлите учебный текст полнее."),
    "bot.file_student": ("Fayllarni o'qituvchilar yuboradi. Test kodini yozing yoki «📋 Testlarim»ni oching.",
                         "Файлы присылают учителя. Напишите код теста или откройте «📋 Мои тесты»."),
    "csv.no": ("№", "№"), "csv.name": ("Ism", "Имя"), "csv.score": ("Ball", "Баллы"), "csv.pct": ("Foiz", "Процент"), "csv.grade": ("Baho", "Оценка"),
    "csv.time": ("Vaqt (daq:son)", "Время (мин:сек)"), "csv.status": ("Holat", "Статус"), "csv.at": ("Topshirgan vaqti", "Когда сдал"),
    "csv.st_done": ("topshirdi", "сдал"), "csv.st_working": ("yechyapti", "решает"), "csv.st_waiting": ("boshlamagan", "не начал"),
    "note.new_test": ("📝 <b>Yangi test: {title}</b>\n{count} · {minutes}{deadline}", "📝 <b>Новый тест: {title}</b>\n{count} · {minutes}{deadline}"),
    "note.deadline": ("\nMuddat: {when}", "\nСрок: {when}"),
    "note.retest": ("🔁 <b>Qayta test: {title}</b>\nMavzular: {topics}\n{count} · {minutes}{deadline}\n\nXatolaringiz ustida ishlab, natijangizni oshiring!",
                    "🔁 <b>Повторный тест: {title}</b>\nТемы: {topics}\n{count} · {minutes}{deadline}\n\nПоработайте над ошибками и улучшите результат!"),
    "note.reminder": ("⏰ <b>{title}</b>: muddat {when} da tugaydi. Siz hali boshlamadingiz.", "⏰ <b>{title}</b>: срок истекает {when}. Вы ещё не начали."),
    "note.summary_all": ("📊 <b>{title}</b> — hamma topshirdi", "📊 <b>{title}</b> — сдали все"),
    "note.summary_deadline": ("📊 <b>{title}</b> — muddat tugadi", "📊 <b>{title}</b> — срок истёк"),
    "note.summary": ("{head}\n{done_lbl}: {done}/{people}\n{avg_lbl}: {avg} · {median_lbl}: {median}{flags}{progress}",
                     "{head}\n{done_lbl}: {done}/{people}\n{avg_lbl}: {avg} · {median_lbl}: {median}{flags}{progress}"),
    "note.progress": ("\n\n📈 Shu mavzular bo'yicha guruh natijasi: {before} → {after}", "\n\n📈 Результат класса по этим темам: {before} → {after}"),
}
