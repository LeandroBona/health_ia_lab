"""Transparent tokenization and TF-IDF representation for PT-BR examples."""
import re

from sklearn.feature_extraction.text import TfidfVectorizer

PREPROCESSING_VERSION = 2
STOPWORDS = frozenset("""a ao aos as à às o os um uma uns umas de da das do dos e em no na nos nas por para com sem sob entre sobre que quem qual quais como quando onde porque pois se eu me meu minha meus minhas você seu sua seus suas ele ela eles elas nós nosso nossa nos lhe estou está estão estava estavam fui foi foram ser ter tenho tem tinha há houve muito muita muitos muitas mais menos já ainda também só apenas até desde depois antes durante agora hoje ontem amanhã aqui ali lá esse essa esses essas este esta isto isso aquilo todo toda todos todas cada outro outra outros outras mesmo mesma mesma vez vezes tanto tanta enquanto pelo pela pelos pelas num numa nuns numas aos dela dele deles delas comigo contigo consigo não sim algo alguém algum alguma alguns algumas nenhum nenhuma nada tudo pouco poucos pouca poucas dia dias semana semanas ano anos manhã tarde noite noites além disso fim longo momento rever recentemente semana outro""".split())
TOKEN_RE = re.compile(r"[a-záàâãéêíóôõúüç]+", re.IGNORECASE)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-záàâãéêíóôõúüç\s]", " ", text.casefold())).strip()


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.casefold())


def content_tokens(text: str) -> list[str]:
    return [token for token in tokenize(text) if token not in STOPWORDS and len(token) > 1]


def processing_details(text: str, feature_count: int | None = None) -> dict:
    tokens = tokenize(text)
    removed = [token for token in tokens if token in STOPWORDS]
    kept = [token for token in tokens if token not in STOPWORDS and len(token) > 1]
    return {"original": text, "normalized": normalize_text(text), "tokens": tokens,
            "stopwords_removed": removed, "terms_kept": kept, "feature_count": feature_count}


def make_vectorizer(min_df: int = 2) -> TfidfVectorizer:
    return TfidfVectorizer(preprocessor=normalize_text, tokenizer=content_tokens, token_pattern=None,
                           lowercase=False, ngram_range=(1, 2), min_df=min_df, max_features=2000,
                           sublinear_tf=True, norm="l2")
