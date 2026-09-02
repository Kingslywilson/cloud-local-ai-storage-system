from ai_analysis import analyze_file

result = analyze_file(
    file_path="test.pdf",
    file_name="test.pdf",
    file_type="application/pdf"
)

print("SUMMARY:")
print(result["summary"])

print("\nDESCRIPTION:")
print(result["description"])

print("\nTAGS:")
print(result["tags"])

print("\nINSIGHTS:")
print(result["insights"])