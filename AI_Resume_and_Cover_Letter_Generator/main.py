from src.generator import generate_application


# ==========================================
# Test data
# ==========================================

resume = """
Robel is an Information Technology student with experience in
Python, Machine Learning, Deep Learning, Git, and Streamlit.

He has built AI and machine learning projects.
"""


job_description = """
We are looking for a Junior AI Engineer.

The candidate should have experience with Python,
Machine Learning, Deep Learning, Git, and APIs.
"""


# ==========================================
# Generate application
# ==========================================

result_data = generate_application(
    resume,
    job_description
)


# ==========================================
# Display results
# ==========================================

print("\n" + "=" * 60)
print("SKILLS MATCH")
print("=" * 60)

print(result_data["skills_match"])


print("\n" + "=" * 60)
print("TAILORED RESUME")
print("=" * 60)

print(result_data["tailored_resume"])


print("\n" + "=" * 60)
print("COVER LETTER")
print("=" * 60)

print(result_data["cover_letter"])


print("\n" + "=" * 60)
print("IMPROVEMENT AREAS")
print("=" * 60)

print(result_data["improvement_areas"])