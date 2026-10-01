import sys
from google.cloud import firestore
from google.api_core.exceptions import NotFound, PermissionDenied

# Hardcoded project ID as string to prevent Agent Platform project-number mismatch
PROJECT_ID = "qwiklabs-gcp-02-8e9f153f9a2f"

print(f"Initializing Firestore client for project ID: '{PROJECT_ID}'...")
db = firestore.Client(project=PROJECT_ID)

seed_items = [
    {
        "id": "organic_whole_milk",
        "name": "Organic Whole Milk",
        "category": "Dairy",
        "quantity": "1 Half Gallon",
        "expiration_date": "2026-10-10"
    },
    {
        "id": "sourdough_bread",
        "name": "Sourdough Bread",
        "category": "Bakery",
        "quantity": "1 Loaf",
        "expiration_date": "2026-10-05"
    },
    {
        "id": "free_range_eggs",
        "name": "Free-Range Eggs",
        "category": "Dairy",
        "quantity": "12 Eggs",
        "expiration_date": "2026-10-20"
    },
    {
        "id": "extra_virgin_olive_oil",
        "name": "Italian Extra Virgin Olive Oil",
        "category": "Pantry Staples",
        "quantity": "500ml Bottle",
        "expiration_date": "2027-01-15"
    },
    {
        "id": "fresh_spinach",
        "name": "Fresh Spinach",
        "category": "Produce",
        "quantity": "1 Bag (8oz)",
        "expiration_date": "2026-10-04"
    }
]

print(f"Seeding Firestore collection 'pantry_items'...")
try:
    for item in seed_items:
        doc_ref = db.collection("pantry_items").document(item["id"])
        doc_ref.set(item)
        print(f"  ✓ Seeded document '{item['id']}': {item['name']} ({item['category']})")
    print("Firestore seeding finished successfully!")
except NotFound:
    print(f"Notice: Default Firestore database for project '{PROJECT_ID}' is not yet created on GCP console.")
except PermissionDenied:
    print(f"Notice: Permission denied when writing to Firestore for project '{PROJECT_ID}'. Check IAM roles.")
except Exception as e:
    print(f"Seeding error encountered: {e}")
