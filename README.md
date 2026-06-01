# Math I/O

**Math I/O** е десктоп апликација која овозможува извлекување текст и решавање математички равенки директно од слики. Апликацијата е **crossplatform** и работи на **Windows** и **macOS**.

---

## Што прави?

Апликацијата нуди два режима на работа:

### Текст режим
Апликацијата автоматски ја детектира хартијата во сликата, ја исправа перспективата и го извлекува текстот преку Tesseract OCR. Поддржува **англиски** и **македонски** јазик. Извлечениот текст може да се копира во клипборд или да се зачува како `.txt` датотека.

### Режим за равенки
Апликацијата ја препознава математичката равенка од сликата и ја конвертира во LaTeX форма преку `pix2tex` (LatexOCR). Потоа равенката се решава со `SymPy`, а решението се објаснува чекор-по-чекор преку локален Ollama AI модел.

### Дополнителни функции
- **Верификација** — пред обработката, апликацијата ги прикажува детектираните агли на хартијата за да може корисникот да провери дали се точни.
- **Рачно кропирање** — корисникот може рачно да означи 4 точки на сликата за прецизно исекување.
- **Светла / Темна тема** — менување на темата преку менито.

---

## Потребни алатки

Пред да ја стартувате апликацијата, треба да ги инсталирате следните надворешни алатки:

---

### 1. Tesseract OCR

Tesseract е потребен за извлекување на текст од слики.

#### macOS (Homebrew)
```bash
brew install tesseract
brew install tesseract-lang
```

#### Windows
1. Преземете го инсталерот од: https://github.com/UB-Mannheim/tesseract/wiki
2. Стартувајте го инсталерот и при инсталација штиклирајте го **Macedonian** јазичниот пакет.
3. Додадете го Tesseract во системскиот `PATH` (инсталерот нуди оваа опција автоматски).

---

### 2. Ollama (AI модел за објаснување)

Ollama е потребен за чекор-по-чекор објаснување на решенијата на равенките.

#### macOS (Homebrew)
```bash
brew install ollama
```

#### Windows
1. Преземете го инсталерот од: https://ollama.com/download
2. Стартувајте го инсталерот и следете ги инструкциите.

#### Преземање на моделот (Windows и macOS)

По инсталацијата на Ollama, преземете го потребниот модел:
```bash
ollama pull gemma3:4b
```

Потоа стартувајте го Ollama:
```bash
ollama serve
```

> Ollama мора да биде активен додека ја користите апликацијата.

---

## Отворање на апликацијата

> Поради големиот број на зависности, апликацијата може да се отвори побавно — ова е очекувано однесување и на Windows и на macOS.

### macOS

Моменталниот начин за отворање на апликацијата е преку терминал, поради потреба од поправки на релативни/апсолутни патеки.

Одете до root фолдерот на проектот и извршете ја следната команда:

```bash
"./Math IO v1.1.app/Contents/MacOS/Math IO v1.1"
```

### Windows

Двоен клик на извршната датотека (`Math IO v1.1.exe`).

---

## Самостојно билдање на апликацијата

### Чекори

**1.** Активирајте го вашиот виртуелен environment и инсталирајте ги зависностите:

```bash
pip install -r requirements.txt
```

**2.** Извршете ја командата за билдање:

#### macOS

> Заменете ги патеките кон `pix2tex/model` и `sympy/parsing/latex` со патеките до вашиот venv.

```bash
flet pack math_io_flet.py \
--name "Math IO v1.1" \
--product-name "Math IO" \
--product-version "1.1" \
--file-version "1.1" \
--copyright "DV ON" \
--add-data "assets:assets" \
--add-data "/your/venv/lib/python3.10/site-packages/pix2tex/model:pix2tex/model" \
--add-data "/your/venv/lib/python3.10/site-packages/sympy/parsing/latex:sympy/parsing/latex" \
--hidden-import sympy \
--hidden-import sympy.core \
--hidden-import sympy.solvers \
--hidden-import sympy.parsing.sympy_parser \
--hidden-import sympy.parsing.latex \
--hidden-import sympy.parsing.latex._parse_latex_antlr \
--hidden-import sympy.parsing.latex.errors \
--hidden-import antlr4 \
--hidden-import antlr4.error \
--hidden-import antlr4.error.ErrorListener \
--hidden-import antlr4.InputStream \
--hidden-import antlr4.CommonTokenStream
```

**3.** Почекајте билдот да заврши. Апликацијата ќе се наоѓа во `dist/` фолдерот.

**4.** Отворете ја апликацијата преку терминал (погледнете ја секцијата [Отворање на апликацијата](#отворање-на-апликацијата)).

#### Windows

_(Наскоро)_

---
