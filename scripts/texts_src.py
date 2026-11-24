"""The source of shared/data/texts.json: short educational texts written for this project (original wording, invented
for the demo and the tests). Run ``python scripts/texts_src.py`` after editing.

* ``fotosintez`` is the story's text (7th grade biology);
* ``barg``, ``ildiz`` and ``hujayra`` are the earlier tests of the seeded group;
* ``ot``, ``ulugbek``, ``orol`` and ``tovush`` come from other subjects: the "O'zingiz sinab ko'ring" examples and the
  generator's tests on ordinary texts a teacher would use."""

from __future__ import annotations

import json
from pathlib import Path

TEXTS = [
    {"id": "fotosintez", "title": "Fotosintez", "subject": "Biologiya", "grade": 7, "body": """Fotosintez nima?

Fotosintez — yashil o'simliklar yorug'lik energiyasi yordamida karbonat angidrid va suvdan organik modda hosil qiladigan jarayon. Bu jarayonda havoga kislorod ajralib chiqadi. Fotosintez asosan barglarda boradi.

Xlorofill va xloroplast

Barg hujayralaridagi yashil rangli moddaga xlorofill deyiladi. Xlorofill quyosh nurini yutadi va uning energiyasini jarayonga beradi. Xlorofill saqlovchi mayda tanachalar xloroplast deb ataladi. Kuzda xlorofill parchalanadi, shuning uchun barglar sarg'ayadi.

Fotosintez uchun nima kerak?

O'simlik karbonat angidridni havodan oladi. Barg sirtidagi mayda teshikchalar og'izcha deb ataladi. Karbonat angidrid bargga og'izchalar orqali kiradi. Suv tuproqdan ildiz orqali so'riladi va poya bo'ylab barglarga ko'tariladi. Yorug'lik bo'lmasa, fotosintez to'xtaydi.

Fotosintez bosqichlari

Fotosintez ikki bosqichda boradi. Birinchi bosqich faqat yorug'likda o'tadi va unda suv parchalanib, kislorod ajraladi. Ikkinchi bosqichda karbonat angidriddan glyukoza hosil bo'ladi. Glyukoza — o'simlik hosil qiladigan asosiy shakar.

Kislorod qanday aniqlangan?

1771-yilda ingliz olimi Jozef Pristli o'simlik havoni tozalashini tajribada ko'rsatdi. U yopiq idishga yonib turgan sham va yalpiz novdasini qo'ydi. Yalpiz ajratgan kislorod tufayli sham uzoq yonib turdi. Yer atmosferasidagi havoning qariyb 21 foizi kisloroddan iborat.

Fotosintezning ahamiyati

Fotosintez tufayli Yerdagi deyarli barcha tirik organizmlar oziq va kislorod oladi. Kraxmal — glyukozadan hosil bo'ladigan va o'simlikda zaxira sifatida to'planadigan modda. Kartoshka tugunagida kraxmal ko'p bo'ladi. Odam va hayvonlar nafas olganda kislorod yutib, karbonat angidrid chiqaradi."""},
    {"id": "barg", "title": "Barg tuzilishi", "subject": "Biologiya", "grade": 7, "body": """Barg qismlari

Barg — o'simlikning yon tomondan o'sadigan yassi organi. Bargning keng yassi qismi barg plastinkasi deb ataladi. Plastinkani poyaga biriktiruvchi ingichka qismga barg bandi deyiladi. Bandi bo'lmagan barglar o'troq barglar deb ataladi. Bitta bandda bitta plastinka bo'lsa, oddiy barg deyiladi. Bandda bir nechta plastinka joylashgan barg murakkab barg deb ataladi.

Tomirlanish

Barg plastinkasidagi tomirlar suv va moddalarni o'tkazadi. Tomirlari bir-biriga parallel joylashgan barglar parallel tomirlangan deyiladi. Bug'doy va makkajo'xorining barglari parallel tomirlangan. Olma va o'rik barglari esa to'rsimon tomirlangan.

Bargning ichki tuzilishi

Barg ustidan yupqa po'st bilan qoplangan. Po'st ostida ustunsimon to'qima joylashgan va unda xloroplastlar ko'p bo'ladi. Barg po'stidagi mayda teshikchalar og'izchalar deb ataladi. Barg 1 kvadrat millimetr sirtida yuzlab og'izcha bo'lishi mumkin. Bargdan suvning bug'lanishi transpiratsiya deb ataladi. Issiq kunda bitta katta daraxt transpiratsiya orqali 200 litrgacha suv bug'latadi."""},
    {"id": "ildiz", "title": "Ildiz", "subject": "Biologiya", "grade": 7, "body": """Ildiz va uning vazifalari

Ildiz — o'simlikni tuproqqa mahkamlaydigan va undan suv hamda mineral tuzlarni so'radigan yer osti organi. Urug'dan birinchi bo'lib o'sib chiqqan ildiz asosiy ildiz deb ataladi. Asosiy ildizdan tarmoqlanib chiqadigan ildizlarga yon ildizlar deyiladi.

Ildiz tizimlari

Asosiy ildizi yaxshi rivojlangan ildiz tizimi o'q ildiz tizimi deb ataladi. No'xat, loviya va kungaboqarda o'q ildiz tizimi bor. Bug'doy va piyozda esa popuk ildiz tizimi rivojlanadi.

Ildiz tuklari

Ildiz uchida joylashgan juda mayda o'simtalar ildiz tuklari deb ataladi. Ildiz tuklari suvni tuproqdan so'radi. Bitta ildiz tukining umri 10 dan 20 kungacha davom etadi. Ildiz uchini qoplab turadigan himoya qatlami ildiz qinchasi deb ataladi.

Ildiz shakl o'zgarishlari

Oziq moddalar to'planib yo'g'onlashgan ildizga ildizmeva deyiladi. Sabzi, lavlagi va sholg'om ildizmevalarida qand va vitaminlar ko'p bo'ladi. Kartoshka tugunagi esa ildiz emas, balki poyaning shakl o'zgarishidir."""},
    {"id": "hujayra", "title": "Hujayra tuzilishi", "subject": "Biologiya", "grade": 7, "body": """Hujayra

Hujayra — tirik organizmlarning eng kichik tuzilish birligi. Hujayrani birinchi bo'lib 1665-yilda ingliz olimi Robert Guk ko'rgan. U po'kak kesmasini mikroskopda kuzatib, mayda kataklarni ko'rdi.

Hujayra qismlari

O'simlik hujayrasini tashqi tomondan qattiq qobiq o'rab turadi. Qobiq ostidagi yupqa parda sitoplazmatik membrana deb ataladi. Hujayraning ichki yarim suyuq muhitiga sitoplazma deyiladi. Hujayra hayotini boshqaradigan asosiy qism yadro deb ataladi.

Vakuola

Hujayra shirasi bilan to'lgan bo'shliqqa vakuola deyiladi. Qari o'simlik hujayrasida vakuola hujayra hajmining 90 foizigacha joyni egallaydi. Vakuolada suv, qand va tuzlar to'planadi."""},
    {"id": "ot", "title": "Ot so'z turkumi", "subject": "Ona tili", "grade": 5, "body": """Ot

Ot — shaxs, narsa va hodisalarning nomini bildiradigan so'z turkumi. Otlar kim? nima? qayer? so'roqlaridan biriga javob bo'ladi. Gapda ot ko'pincha ega yoki to'ldiruvchi vazifasida keladi.

Atoqli va turdosh otlar

Bir xil narsalarning umumiy nomini bildirgan otlarga turdosh otlar deyiladi. Kishi ismlari, shahar va daryo nomlari atoqli otlar deb ataladi. Atoqli otlar doim bosh harf bilan yoziladi. Masalan, Toshkent, Amudaryo va Alisher atoqli otlardir.

Birlik va ko'plik

Otlar birlik va ko'plikda qo'llanadi. Ko'plik shakli -lar qo'shimchasi bilan yasaladi. Ba'zi otlar faqat birlikda ishlatiladi: sut, un, oltin."""},
    {"id": "ulugbek", "title": "Ulug'bek rasadxonasi", "subject": "Tarix", "grade": 7, "body": """Mirzo Ulug'bek Amir Temurning nevarasi bo'lib, 1394-yilda Sultoniya shahrida tug'ilgan. U 1409-yildan Samarqand hokimi bo'lgan va qariyb 40 yil shu shaharni boshqargan.

Ulug'bek 1420-yilda Samarqandda madrasa qurdirgan. Bu madrasa Registon maydonidagi eng qadimiy binolardan biridir. Madrasada riyoziyot, falakiyot va falsafa o'qitilgan.

1428-yilda Obirahmat ariq bo'yidagi Ko'hak tepaligida rasadxona qurib bitkazildi. Rasadxonaning asosiy asbobi ulkan sekstant bo'lgan. Olimlar bu yerda 1018 ta yulduzning o'rnini aniqlab, «Ziji jadidi Ko'ragoniy» jadvalini tuzdilar. Rasadxona xarobalarini 1908-yilda arxeolog Vasiliy Vyatkin topgan."""},
    {"id": "orol", "title": "Orol dengizi", "subject": "Geografiya", "grade": 8, "body": """Orol dengizi O'zbekiston va Qozog'iston chegarasida joylashgan berk ko'l. Unga ikki katta daryo — Amudaryo va Sirdaryo quyiladi. 1960-yillarda Orol maydoni bo'yicha dunyodagi to'rtinchi yirik ko'l edi.

Daryo suvlari paxta va sholi dalalarini sug'orish uchun ko'plab olina boshlagach, dengizga suv kam yetib keldi. Natijada dengiz sathi pasayib, suvning sho'rligi oshdi. Dengizning qurigan tubida hosil bo'lgan cho'l Orolqum deb ataladi.

Shamol Orolqumdan tuz va changni yuzlab kilometrga uchirib ketadi. Bu hodisa atrofdagi aholi salomatligiga va ekinlarga zarar yetkazadi. Hozir qurigan tubda saksovul ekilib, o'rmonzorlar barpo etilmoqda. Saksovul — qumni mustahkamlaydigan va sho'rga chidamli butasimon o'simlik."""},
    {"id": "tovush", "title": "Tovush", "subject": "Fizika", "grade": 8, "body": """Tovush — muhitda tarqaladigan mexanik to'lqin. Tovush havoda, suvda va qattiq jismlarda tarqaladi, lekin vakuumda tarqalmaydi. Havoda tovush sekundiga taxminan 340 metr tezlik bilan tarqaladi.

Bir sekunddagi tebranishlar soni chastota deb ataladi. Chastota gers bilan o'lchanadi. Odam qulog'i 20 dan 20 000 gersgacha bo'lgan tovushlarni eshitadi. Chastotasi 20 000 gersdan yuqori tovushlarga ultratovush deyiladi.

Tovushning to'siqdan qaytishi aks-sado deb ataladi. Ko'rshapalaklar ultratovush yordamida qorong'ida yo'l topadi. Suvda tovush havodagiga qaraganda taxminan 4 marta tez tarqaladi."""},
]


if __name__ == "__main__":
    out = Path(__file__).resolve().parent.parent / "shared" / "data" / "texts.json"
    out.write_bytes((json.dumps(TEXTS, ensure_ascii=False, indent=1) + "\n").encode())
    print("wrote", out.name, len(TEXTS), "texts")
