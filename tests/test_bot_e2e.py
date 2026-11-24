"""The real aiogram handlers against a mocked Bot API: people press buttons by their visible text, like in Telegram.
No network: files are "downloaded" from the simulator, the AI is off."""

from __future__ import annotations

from testustasi import scheduler
from testustasi.core.clock import at_local

from .helpers import FOTO, JASUR, NODIRA, STRANGER, TODAY, published, service_env
from .pdfmake import pdf
from .tg_sim import TgSim

LINES = [line for para in FOTO.split("\n\n") for line in [para[i:i + 90] for i in range(0, len(para), 90)]]


async def test_a_new_person_picks_a_role_and_every_screen_has_back():
    async with service_env() as (svc, _clock):
        tg = TgSim(svc)
        await tg.say(STRANGER, "/start")
        assert "Siz kimsiz?" in tg.last(STRANGER) and tg.buttons(STRANGER) == ["👩‍🏫 Men o'qituvchiman", "🎓 Men o'quvchiman", "🇷🇺 Русский"]
        await tg.tap(STRANGER, "🇷🇺 Русский")
        assert "Кто вы?" in tg.last(STRANGER)
        await tg.tap(STRANGER, "🇺🇿 O'zbekcha")
        await tg.tap(STRANGER, "Men o'qituvchiman")
        assert tg.last(STRANGER).startswith("👩‍🏫 <b>Begona</b>") and "📝 Yangi test" in tg.buttons(STRANGER)
        for label in ("📝 Yangi test", "📋 Testlarim", "👥 Sinflarim", "❓ Yordam"):
            await tg.tap(STRANGER, label)
            assert "⬅️ Orqaga" in tg.buttons(STRANGER), label
            await tg.tap(STRANGER, "⬅️ Orqaga")
        await tg.tap(STRANGER, "👥 Sinflarim")
        await tg.tap(STRANGER, "➕ Yangi sinf")
        await tg.say(STRANGER, "8-A")
        assert "8-A</b> sinfi ochildi" in tg.last(STRANGER)
        await tg.tap(STRANGER, "👥 8-A")
        assert "https://t.me/ustasi_test_bot?start=g" in tg.last(STRANGER)


async def test_teacher_sends_a_text_and_gets_a_draft_to_review():
    async with service_env() as (svc, _clock):
        tg = TgSim(svc)
        await tg.say(NODIRA, "/start")
        assert "Sinflar: 1 · testlar: 3" in tg.last(NODIRA)
        await tg.say(NODIRA, "Fotosintez haqida")
        assert "juda qisqa" in tg.last(NODIRA)
        await tg.say(NODIRA, FOTO)
        assert "<b>Fotosintez nima</b> qabul qilindi" + chr(10) + "6 ta bo'lim · 1 696 belgi" in tg.last(NODIRA)
        assert tg.buttons(NODIRA) == ["5 ta", "10 ta", "15 ta", "20 ta", "⬅️ Orqaga"]
        await tg.tap(NODIRA, "15 ta")
        assert "Qiyinligi qanday bo'lsin?" in tg.last(NODIRA)
        await tg.tap(NODIRA, "⚖️ Aralash")
        text = tg.last(NODIRA)
        assert text.startswith("✅ <b>Qoralama tayyor") and "11 ta savol (so'ralgani 15 ta edi: matndan shuncha sifatli savol chiqdi)" in text
        assert "AI" not in text and "sun'iy" not in text, "no technical notes on a screen"
        tid = (await svc.tests(NODIRA))[0]["id"]
        assert tg.apps(NODIRA) == [f"https://ustasi.example/webapp/#t={tid}"]
        await tg.tap(NODIRA, "📋 Testlarim")
        assert any(m.startswith("✅ <b>Qoralama tayyor") for m in tg.texts(NODIRA)), "the ready message stays in the chat"


async def test_a_pdf_and_a_scanned_pdf():
    async with service_env() as (svc, _clock):
        tg = TgSim(svc)
        await tg.send_file(NODIRA, pdf([LINES]), "Fotosintez_darslik.pdf")
        assert "<b>Fotosintez darslik</b> qabul qilindi" in tg.last(NODIRA)
        await tg.send_file(NODIRA, pdf([[], []]), "skaner.pdf")
        assert "matn topilmadi" in tg.last(NODIRA) and "Matnni nusxalab yuboring" in tg.last(NODIRA)
        await tg.send_file(JASUR, pdf([LINES]))
        assert "Fayllarni o'qituvchilar yuboradi" in tg.last(JASUR)


async def test_students_join_get_tests_and_the_teacher_gets_results():
    async with service_env() as (svc, clock):
        tg = TgSim(svc)
        t = await published(svc, clock)
        await tg.notifier.send([{"to": JASUR, "kind": "new_test", "test": t["id"], "title": t["title"], "count": 10, "minutes": 15,
                                 "deadline": at_local(TODAY, 23 * 60 + 59)}])
        assert tg.last(JASUR) == "📝 <b>Yangi test: Fotosintez</b>\n10 ta savol · 15 daqiqa\nMuddat: bugun, 23:59"
        assert tg.apps(JASUR) == [f"https://ustasi.example/webapp/#s={t['id']}"]
        await tg.say(JASUR, "/start")
        await tg.tap(JASUR, "📋 Testlarim")
        assert any("🆕 Fotosintez · 10 ta savol" in b for b in tg.buttons(JASUR))
        await tg.say(STRANGER, f"/start t{t['code']}")
        assert "<b>7-B</b> sinfi · 📝 Fotosintez" in tg.last(STRANGER) and (await svc.me(STRANGER))["role"] == "student"
        await tg.say(9001, "/start")
        await tg.tap(9001, "Men o'quvchiman")
        await tg.tap(9001, "🔑 Test kodini kiritish")
        await tg.say(9001, "zzzzzz")
        assert "Bunday kodli test topilmadi" in tg.last(9001)
        await tg.say(9001, t["code"].lower())
        assert "📝 Fotosintez" in tg.last(9001)
        await tg.say(NODIRA, "/start")
        await tg.tap(NODIRA, "📋 Testlarim")
        await tg.tap(NODIRA, "✅ Fotosintez")
        card = tg.last(NODIRA)
        assert f"Kod: <code>{t['code']}</code>" in card and "Topshirdi: 0/27" in card and "O'rtacha: —" in card
        assert tg.buttons(NODIRA) == ["📊 Natijalar", "🧩 Xatolar tahlili", "⬅️ Orqaga"]


async def test_the_bot_escapes_what_people_type():
    async with service_env() as (svc, _clock):
        tg = TgSim(svc)
        await tg.say(NODIRA, "/start")
        await tg.say(NODIRA, "<b>Qalin</b> & " + FOTO)
        assert "<b>&lt;b&gt;Qalin&lt;/b&gt; &amp; Fotosintez nima</b>" in tg.last(NODIRA)


async def test_retest_csv_and_the_summary_from_the_scheduler():
    async with service_env() as (svc, clock):
        tg = TgSim(svc)
        t = await published(svc, clock)
        from testustasi.core.seedgen import simulate, students

        qs = t["questions"]
        people = [{**s, "id": {-101: JASUR}.get(s["id"], s["id"])} for s in students()]
        sims = simulate(qs, people, "bot", {2: {"kind": "pick", "option": 0, "share": 60}, 5: {"kind": "key", "option": 0}})
        for s in sims:
            v, _ = await svc.start(s["user"], t["id"])
            by = {i["stem"]: i for i in v["questions"]}
            for q in qs:
                await svc.answer(s["user"], v["attempt"], by[q["stem"]]["pos"], by[q["stem"]]["options"].index(q["options"][s["answers"][q["id"]]]))
            _r, notes = await svc.submit(s["user"], v["attempt"])
            await tg.notifier.send(notes)
        summary = tg.last(NODIRA)
        assert summary.startswith("📊 <b>Fotosintez</b> — hamma topshirdi\nTopshirdi: 25/25\nO'rtacha: ")
        await tg.say(NODIRA, "/start")
        await tg.tap(NODIRA, "📋 Testlarim")
        await tg.tap(NODIRA, "✅ Fotosintez")
        assert "⚠️ Tekshiring: 1 ta savolda kuchli o'quvchilar ham xato qilgan." in tg.last(NODIRA)
        await tg.tap(NODIRA, "📥 Excel uchun fayl (CSV)")
        chat, data, name = tg.session.documents[-1]
        assert chat == NODIRA and name == "Fotosintez.csv" and data.startswith("﻿№;Ism;Ball".encode())
        await tg.tap(NODIRA, "🔁 Xato savollar bo'yicha qayta test")
        assert tg.last(NODIRA).startswith("🔁 <b>Qayta test</b>\nMavzular: ")
        await tg.tap(NODIRA, "✅ Yuborish")
        assert tg.last(NODIRA).startswith("🔁 Qayta test yuborildi: ")
        got = [u for u in (s["user"] for s in sims) if u > 0 and any("Qayta test: Fotosintez" in m for m in tg.texts(u))]
        assert got == [JASUR] or got == [], "seeded students cannot receive messages; Jasur gets it only if he missed"
        clock.skip(days=3)
        assert await scheduler.tick(svc, tg.notifier) >= 1
        assert "muddat tugadi" in tg.last(NODIRA)
