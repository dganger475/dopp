import os

from test_arcface import find_matches_for_face

# Save the selfie to static/extracted_faces with a unique name
selfie_filename = "my_selfie.jpg"

# Find matches with 70% or higher similarity
matches = find_matches_for_face(selfie_filename, min_similarity=70)

# Print results
print("\nMatches found (sorted by similarity):")
print("=" * 80)

for match in matches:
    print(f"\nSimilarity: {match['similarity']:.2f}%")
    print(f"Matched with: {match['filename']}")
    print(f"Year: {match['year']}")
    print(f"School: {match['school']}") 