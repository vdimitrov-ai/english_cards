import os
from typing import List, Tuple

DB_DIR = "db"
DATABASE = os.path.join(DB_DIR, "cards.db")
UPLOAD_FOLDER = "static/card_images"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

ADVANCED_WORDS: List[Tuple[str, str, str, str, str]] = [
    (
        "ubiquitous",
        "вездесущий",
        'Присутствующий или находящийся повсюду одновременно. Пример: "Smartphones have become ubiquitous in modern society."',
        "/juːˈbɪkwɪtəs/",
        "https://dictionary.cambridge.org/dictionary/english-russian/ubiquitous",
    ),
    (
        "ephemeral",
        "мимолётный",
        'Существующий очень короткое время. Пример: "The ephemeral nature of social media trends."',
        "/ɪˈfem.ər.əl/",
        "https://dictionary.cambridge.org/dictionary/english-russian/ephemeral",
    ),
    (
        "paradigm",
        "парадигма",
        'Типичный пример или модель чего-либо. Пример: "This discovery represents a paradigm shift in our understanding."',
        "/ˈpær.ə.daɪm/",
        "https://dictionary.cambridge.org/dictionary/english-russian/paradigm",
    ),
    (
        "eloquent",
        "красноречивый",
        'Способный выражать мысли чётко и убедительно. Пример: "Her eloquent speech moved the audience."',
        "/ˈel.ə.kwənt/",
        "https://dictionary.cambridge.org/dictionary/english-russian/eloquent",
    ),
    (
        "meticulous",
        "скрупулёзный",
        'Проявляющий чрезвычайное внимание к деталям. Пример: "He is meticulous in his research."',
        "/məˈtɪk.jə.ləs/",
        "https://dictionary.cambridge.org/dictionary/english-russian/meticulous",
    ),
    (
        "ambiguous",
        "двусмысленный",
        'Имеющий более одного возможного значения. Пример: "The contract contained several ambiguous clauses."',
        "/æmˈbɪɡ.ju.əs/",
        "https://dictionary.cambridge.org/dictionary/english-russian/ambiguous",
    ),
    (
        "enigmatic",
        "загадочный",
        'Трудный для понимания, таинственный. Пример: "She gave an enigmatic smile."',
        "/ˌen.ɪɡˈmæt.ɪk/",
        "https://dictionary.cambridge.org/dictionary/english-russian/enigmatic",
    ),
    (
        "cognizant",
        "осведомлённый",
        'Имеющий знание или осознание чего-либо. Пример: "We are cognizant of the risks involved."',
        "/ˈkɒɡ.nɪ.zənt/",
        "https://dictionary.cambridge.org/dictionary/english-russian/cognizant",
    ),
    (
        "ethereal",
        "неземной",
        'Крайне деликатный и лёгкий, неземной. Пример: "The ethereal beauty of the northern lights."',
        "/ɪˈθɪə.ri.əl/",
        "https://dictionary.cambridge.org/dictionary/english-russian/ethereal",
    ),
    (
        "fastidious",
        "привередливый",
        'Уделяющий большое внимание точности и деталям. Пример: "He is fastidious about his appearance."',
        "/fæˈstɪd.i.əs/",
        "https://dictionary.cambridge.org/dictionary/english-russian/fastidious",
    ),
]
RANDOM_NAMES = [
    "Александр",
    "Мария",
    "Дмитрий",
    "Анна",
    "Иван",
    "Елена",
    "Сергей",
    "Ольга",
    "Андрей",
    "Наталья",
    "Михаил",
    "Екатерина",
    "Владимир",
    "Татьяна",
    "Алексей",
    "Светлана",
    "Николай",
    "Юлия",
]
DEFAULT_PAIRS = [
    {
        "english_word": "resilient",
        "russian_word": "стойкий"
    },
    {
        "english_word": "arbitrary",
        "russian_word": "произвольный"
    },
    {
        "english_word": "profound",
        "russian_word": "глубокий"
    },
    {
        "english_word": "intricate",
        "russian_word": "сложный"
    },
    {
        "english_word": "adamant",
        "russian_word": "непреклонный"
    },
    {
        "english_word": "peculiar",
        "russian_word": "своеобразный"
    },
    {
        "english_word": "eloquent",
        "russian_word": "красноречивый"
    },
    {
        "english_word": "tenacious",
        "russian_word": "упорный"
    },
]
