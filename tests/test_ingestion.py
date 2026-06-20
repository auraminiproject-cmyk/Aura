from services.retrieval.ingestion import load_catalog


def test_catalog_loads():
    products = load_catalog()
    assert len(products) >= 10


def test_cleaning_pipeline():
    from data.cleaning_pipeline import DataCleaningPipeline

    pipe = DataCleaningPipeline()
    out = pipe.clean_text_dataset([
        {"instruction": " ".join(["word"] * 25), "output": " ".join(["reply"] * 25)},
    ])
    assert len(out) == 1
