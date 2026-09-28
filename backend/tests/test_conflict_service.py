from app.services.conflict_service import ConflictService


def test_parse_conflict_markers():
    sample_content = """def calculate_total(items):
<<<<<<< HEAD
    total = sum(item.price for item in items)
    return total * 1.10
=======
    total = sum(item.price * item.quantity for item in items)
    return total
>>>>>>> feature-branch
"""
    # Create service instance using local directory
    service = ConflictService("c:/Users/tejaswi.b/Desktop/code/gitpilot-ai")
    conflicts = service.parse_conflict_markers(sample_content)

    assert len(conflicts) == 1
    assert conflicts[0]["ours_header"] == "HEAD"
    assert conflicts[0]["theirs_header"] == "feature-branch"
    assert "total * 1.10" in conflicts[0]["ours_content"]
    assert "item.quantity" in conflicts[0]["theirs_content"]
    print("Conflict parser test passed successfully!")


if __name__ == "__main__":
    test_parse_conflict_markers()
