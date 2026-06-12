"""
04_index_qdrant.py — Chargement des embeddings dans Qdrant
Entrée  : data/processed/product_embeddings.parquet
Sortie  : Collection Qdrant 'produits_alimentaires'
"""

import polars as pl
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from pathlib import Path

# ─── CONFIG ───────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_PATH = BASE_DIR / "data" / "processed" / "product_embeddings.parquet"
COLLECTION = "produits_alimentaires"
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333
VECTOR_SIZE = 1024
BATCH_SIZE = 100
# ──────────────────────────────────────────────────────


def main():
    print("📦 Chargement product_embeddings.parquet...")
    df = pl.read_parquet(INPUT_PATH)
    print(f"   Produits à indexer : {len(df):,}")

    # Connexion Qdrant
    print(f"🔌 Connexion Qdrant ({QDRANT_HOST}:{QDRANT_PORT})...")
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    # Supprimer collection existante
    existing = [c.name for c in client.get_collections().collections]
    if COLLECTION in existing:
        client.delete_collection(COLLECTION)
        print("🗑️  Ancienne collection supprimée")

    # Créer la collection
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    print(f"✅ Collection '{COLLECTION}' créée")

    # Indexation par batch
    print(f"🚀 Indexation (batch={BATCH_SIZE})...")
    total = len(df)
    indexed = 0
    errors = 0

    for i in range(0, total, BATCH_SIZE):
        batch = df.slice(i, BATCH_SIZE)
        points = []

        for row in batch.iter_rows(named=True):
            try:
                points.append(
                    PointStruct(
                        id=indexed + len(points),
                        vector=row["embedding"],
                        payload={
                            "product_id": row["product_id"],
                            "note_moyenne": row["note_moyenne"],
                            "nb_avis": row["nb_avis"],
                            "texte_recherche": row["texte_recherche"][:500],
                            "extraits_utiles": row["extraits_utiles"],
                        },
                    )
                )
            except Exception as e:
                errors += 1
                print(f"  ⚠️  Erreur {row['product_id']} : {e}")

        if points:
            client.upsert(collection_name=COLLECTION, points=points)
            indexed += len(points)

        pct = min((i + BATCH_SIZE) / total * 100, 100)
        print(f"  📊 {indexed}/{total} indexés ({pct:.0f}%) — erreurs: {errors}")

    # Vérification finale
    info = client.get_collection(COLLECTION)
    print("\n✅ Indexation terminée !")
    print(f"   Produits indexés  : {indexed}")
    print(f"   Erreurs           : {errors}")
    print(f"   Points dans Qdrant: {info.points_count}")
    # Test recherche rapide
    print("\n🔍 Test recherche...")
    sample_vector = df["embedding"][0]
    results = client.query_points(
        collection_name=COLLECTION, query=sample_vector, limit=3
    ).points
    print("   Top 3 résultats :")
    for r in results:
        print(
            f"   - {r.payload['product_id']} | "
            f"note: {r.payload['note_moyenne']} | "
            f"score: {r.score:.3f}"
        )


if __name__ == "__main__":
    main()
