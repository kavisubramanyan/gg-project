import spacy
import nltk

def main():
    # spaCy
    try:
        spacy.cli.download("en_core_web_sm")
        print("Downloaded spaCy model: en_core_web_sm")
    except Exception as e:
        print("spaCy download error:", e)

    # NLTK resources
    resources = ["punkt", "stopwords", "vader_lexicon", "averaged_perceptron_tagger"]
    for r in resources:
        try:
            nltk.download(r)
            print(f"Downloaded NLTK resource: {r}")
        except Exception as e:
            print(f"NLTK download error for {r}:", e)

if __name__ == "__main__":
    main()
