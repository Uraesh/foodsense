from __future__ import annotations

import argparse
import json
from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw" / "Reviews.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
SAMPLES_DIR = PROJECT_ROOT / "data" / "samples"

REVIEW_SCHEMA = {
    "Id": pl.Int64,
    "ProductId": pl.String,
    "UserId": pl.String,
    "ProfileName": pl.String,
    "HelpfulnessNumerator": pl.Int64,
    "HelpfulnessDenominator": pl.Int64,
    "Score": pl.Float64,
    "Time": pl.Int64,
    "Summary": pl.String,
    "Text": pl.String,
}

DUPLICATE_SUBSET = ["ProductId", "UserId", "Score", "Time", "Summary", "Text"]


def normalize_text_expr(column: str) -> pl.Expr:
    return (
        pl.col(column)
        .cast(pl.String, strict=False)
        .fill_null("")
        .str.replace_all(r"<[^>]+>", " ")
        .str.replace_all(r"[\r\n\t]+", " ")
        .str.replace_all(r"\s+", " ")
        .str.strip_chars()
        .alias(column)
    )


def scan_reviews(csv_path: Path = RAW_DATA_PATH) -> pl.LazyFrame:
    return pl.scan_csv(
        csv_path,
        schema_overrides=REVIEW_SCHEMA,
        infer_schema_length=1000,
        quote_char='"',
    )


def cleaned_reviews_lazy(csv_path: Path = RAW_DATA_PATH) -> pl.LazyFrame:
    return (
        scan_reviews(csv_path)
        .with_columns(
            [
                normalize_text_expr("ProductId"),
                normalize_text_expr("UserId"),
                normalize_text_expr("ProfileName"),
                normalize_text_expr("Summary"),
                normalize_text_expr("Text"),
            ]
        )
        .filter(
            (pl.col("ProductId") != "")
            & ((pl.col("Summary") != "") | (pl.col("Text") != ""))
            & pl.col("Score").is_between(1, 5, closed="both")
            & (pl.col("HelpfulnessNumerator") <= pl.col("HelpfulnessDenominator"))
        )
        .unique(subset=DUPLICATE_SUBSET, keep="first")
        .with_columns(
            [
                pl.from_epoch("Time", time_unit="s").alias("review_timestamp"),
                pl.when(pl.col("HelpfulnessDenominator") > 0)
                .then(pl.col("HelpfulnessNumerator") / pl.col("HelpfulnessDenominator"))
                .otherwise(None)
                .alias("helpfulness_ratio"),
                pl.col("Summary").str.len_chars().alias("summary_length"),
                pl.col("Text").str.len_chars().alias("text_length"),
                pl.when(pl.col("Summary") != "")
                .then(pl.concat_str([pl.col("Summary"), pl.lit(". "), pl.col("Text")]))
                .otherwise(pl.col("Text"))
                .alias("review_text"),
            ]
        )
    )


def build_quality_report(cleaned_reviews: pl.DataFrame, raw_row_count: int) -> dict[str, object]:
    score_distribution = (
        cleaned_reviews.group_by("Score")
        .len()
        .sort("Score")
        .to_dicts()
    )

    reviews_per_product = cleaned_reviews.group_by("ProductId").len()["len"]

    quantiles = cleaned_reviews.select(
        [
            pl.col("text_length").quantile(0.5).alias("p50"),
            pl.col("text_length").quantile(0.9).alias("p90"),
            pl.col("text_length").quantile(0.99).alias("p99"),
        ]
    ).to_dicts()[0]

    return {
        "raw_row_count": raw_row_count,
        "cleaned_row_count": cleaned_reviews.height,
        "rows_removed": raw_row_count - cleaned_reviews.height,
        "unique_products": cleaned_reviews["ProductId"].n_unique(),
        "unique_users": cleaned_reviews["UserId"].n_unique(),
        "score_distribution": score_distribution,
        "zero_helpfulness_denominator": cleaned_reviews.filter(
            pl.col("HelpfulnessDenominator") == 0
        ).height,
        "short_reviews_under_80_chars": cleaned_reviews.filter(pl.col("text_length") < 80).height,
        "long_reviews_over_1500_chars": cleaned_reviews.filter(pl.col("text_length") > 1500).height,
        "reviews_per_product": {
            "median": int(reviews_per_product.median()),
            "p90": int(reviews_per_product.quantile(0.9, interpolation="nearest")),
            "p95": int(reviews_per_product.quantile(0.95, interpolation="nearest")),
            "max": int(reviews_per_product.max()),
        },
        "text_length_quantiles": {key: int(value) for key, value in quantiles.items()},
        "year_distribution": (
            cleaned_reviews.with_columns(pl.col("review_timestamp").dt.year().alias("year"))
            .group_by("year")
            .len()
            .sort("year")
            .to_dicts()
        ),
    }


def build_product_documents(cleaned_reviews: pl.DataFrame) -> pl.DataFrame:
    ranked = cleaned_reviews.sort(
        ["ProductId", "HelpfulnessDenominator", "HelpfulnessNumerator", "Score", "text_length"],
        descending=[False, True, True, True, True],
    )

    aggregated = ranked.group_by("ProductId").agg(
        [
            pl.len().alias("review_count"),
            pl.col("Score").mean().round(2).alias("average_score"),
            pl.col("review_timestamp").min().alias("first_review_at"),
            pl.col("review_timestamp").max().alias("last_review_at"),
            pl.col("Summary").filter(pl.col("Summary") != "").first().alias("label_hint"),
            pl.col("Summary").filter(pl.col("Summary") != "").head(6).alias("summary_samples"),
            pl.col("Text").filter(pl.col("Text") != "").str.slice(0, 280).head(8).alias("text_samples"),
            pl.col("helpfulness_ratio").drop_nulls().mean().round(3).alias("average_helpfulness_ratio"),
        ]
    )

    return (
        aggregated.with_columns(
            [
                pl.col("summary_samples").list.join(" | ").alias("summary_digest"),
                pl.col("text_samples").list.join(" ").alias("review_digest"),
            ]
        )
        .with_columns(
            [
                pl.format(
                    "ProductId: {}. Label hint: {}. Average score: {}. Review count: {}. Summary evidence: {}. Review evidence: {}",
                    pl.col("ProductId"),
                    pl.col("label_hint").fill_null("No short label available"),
                    pl.col("average_score"),
                    pl.col("review_count"),
                    pl.col("summary_digest").fill_null(""),
                    pl.col("review_digest").fill_null(""),
                ).alias("search_text"),
            ]
        )
        .select(
            [
                "ProductId",
                "label_hint",
                "review_count",
                "average_score",
                "average_helpfulness_ratio",
                "first_review_at",
                "last_review_at",
                "summary_samples",
                "text_samples",
                "search_text",
            ]
        )
        .sort("review_count", descending=True)
    )


def write_pipeline_outputs(
    csv_path: Path = RAW_DATA_PATH,
    processed_dir: Path = PROCESSED_DIR,
    samples_dir: Path = SAMPLES_DIR,
) -> dict[str, Path]:
    processed_dir.mkdir(parents=True, exist_ok=True)
    samples_dir.mkdir(parents=True, exist_ok=True)

    raw_row_count = scan_reviews(csv_path).select(pl.len().alias("row_count")).collect().item()
    cleaned_reviews = cleaned_reviews_lazy(csv_path).collect(engine="streaming")
    product_documents = build_product_documents(cleaned_reviews)
    quality_report = build_quality_report(cleaned_reviews, raw_row_count)

    cleaned_reviews_path = processed_dir / "reviews_cleaned.parquet"
    product_documents_path = processed_dir / "product_documents.parquet"
    quality_report_path = processed_dir / "quality_report.json"
    sample_reviews_path = samples_dir / "reviews_cleaned_sample.parquet"
    sample_products_path = samples_dir / "product_documents_sample.parquet"

    cleaned_reviews.write_parquet(cleaned_reviews_path)
    product_documents.write_parquet(product_documents_path)
    cleaned_reviews.head(1000).write_parquet(sample_reviews_path)
    product_documents.head(250).write_parquet(sample_products_path)
    quality_report_path.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")

    return {
        "cleaned_reviews": cleaned_reviews_path,
        "product_documents": product_documents_path,
        "quality_report": quality_report_path,
        "sample_reviews": sample_reviews_path,
        "sample_products": sample_products_path,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean and explore Amazon Fine Food Reviews with Polars.")
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=RAW_DATA_PATH,
        help="Path to the raw Reviews.csv file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    outputs = write_pipeline_outputs(csv_path=args.csv_path)
    print(json.dumps({key: str(value) for key, value in outputs.items()}, indent=2))


if __name__ == "__main__":
    main()
