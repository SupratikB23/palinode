import os
import tempfile
import pytest
from palinode.consolidation.executor import apply_operations

@pytest.fixture
def temp_memory_file():
    content = """---
id: project-alpha
category: project
---

# Project Alpha

- [2024-01-01] The project started today <!-- fact:f1 -->
- [2024-01-02] An update occurred <!-- fact:f2 -->
- [2024-01-03] Another update <!-- fact:f3 -->
"""
    fd, path = tempfile.mkstemp(suffix=".md")
    with os.fdopen(fd, 'w') as f:
        f.write(content)
    yield path
    os.remove(path)

def test_keep_operation(temp_memory_file):
    ops = [{"op": "KEEP", "id": "f1"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["kept"] == 1
    with open(temp_memory_file) as f:
        content = f.read()
    assert "The project started today <!-- fact:f1 -->" in content

def test_update_operation(temp_memory_file):
    ops = [{"op": "UPDATE", "id": "f2", "new_text": "- [2024-01-02] A significant update occurred"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["updated"] == 1
    with open(temp_memory_file) as f:
        content = f.read()
    assert "A significant update occurred <!-- fact:f2 -->" in content
    assert "An update occurred" not in content

def test_merge_operation(temp_memory_file):
    ops = [{"op": "MERGE", "ids": ["f2", "f3"], "new_text": "- [2024-01-02] Important combined updates"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["merged"] == 1
    with open(temp_memory_file) as f:
        content = f.read()
    assert "Important combined updates <!-- fact:merged-f2 -->" in content
    assert "<!-- fact:f3 -->" not in content

def test_supersede_operation(temp_memory_file):
    ops = [{"op": "SUPERSEDE", "id": "f1", "new_text": "- [2024-01-04] The project was restarted", "reason": "Change of plans"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["superseded"] == 1
    with open(temp_memory_file) as f:
        content = f.read()
    assert "~~[2024-01-01] The project started today~~" in content
    assert "The project was restarted <!-- fact:supersedes-f1 -->" in content
    
    # Check history file
    history_file = temp_memory_file.replace(".md", "-history.md")
    assert os.path.exists(history_file)
    with open(history_file) as f:
        hist = f.read()
    assert "Superseded" in hist
    os.remove(history_file)

def test_archive_operation(temp_memory_file):
    ops = [{"op": "ARCHIVE", "id": "f2", "reason": "No longer relevant"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["archived"] == 1
    with open(temp_memory_file) as f:
        content = f.read()
    assert "An update occurred" not in content
    
    history_file = temp_memory_file.replace(".md", "-history.md")
    assert os.path.exists(history_file)
    with open(history_file) as f:
        hist = f.read()
    assert "Archived" in hist
    os.remove(history_file)

def test_malformed_operations(temp_memory_file):
    # Should skip malformed items without crashing
    ops = [{"op": "KEEP", "id": "f1"}, ["nested", "list"], "string item", {"op": "UPDATE", "id": "f2", "new_text": "- New text"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["kept"] == 1
    assert stats["updated"] == 1

def test_missing_fields_are_skipped(temp_memory_file):
    stats = apply_operations(temp_memory_file, [
        {"op": "UPDATE", "id": "f1"},
        {"op": "MERGE", "ids": ["f1", "f2"]},
        {"op": "SUPERSEDE", "new_text": "Replacement"},
        {"op": "ARCHIVE"},
    ])
    assert stats == {"kept": 0, "updated": 0, "merged": 0, "superseded": 0, "archived": 0, "retracted": 0}

def test_missing_fact_id_is_noop(temp_memory_file):
    stats = apply_operations(temp_memory_file, [{"op": "SUPERSEDE", "id": "missing", "new_text": "Replacement"}])
    assert stats["superseded"] == 0
    assert not os.path.exists(temp_memory_file.replace(".md", "-history.md"))

def test_empty_operations_leave_file_unchanged(temp_memory_file):
    with open(temp_memory_file) as f:
        before = f.read()
    stats = apply_operations(temp_memory_file, [])
    with open(temp_memory_file) as f:
        after = f.read()
    assert before == after
    assert stats == {"kept": 0, "updated": 0, "merged": 0, "superseded": 0, "archived": 0, "retracted": 0}


def test_retract_operation(temp_memory_file):
    """RETRACT leaves a visible tombstone with strikethrough and reason."""
    ops = [{"op": "RETRACT", "id": "f2", "reason": "This was never true"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["retracted"] == 1
    with open(temp_memory_file) as f:
        content = f.read()
    # Fact should be struck through with RETRACTED label
    assert "~~[2024-01-02] An update occurred~~" in content
    assert "[RETRACTED" in content
    assert "This was never true" in content
    # Fact ID should still be present (tombstone, not deleted)
    assert "<!-- fact:f2 -->" in content

    # Check history file
    history_file = temp_memory_file.replace(".md", "-history.md")
    assert os.path.exists(history_file)
    with open(history_file) as f:
        hist = f.read()
    assert "Retracted" in hist
    assert "This was never true" in hist
    os.remove(history_file)


def test_retract_without_reason(temp_memory_file):
    """RETRACT should work even without a reason."""
    ops = [{"op": "RETRACT", "id": "f1"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["retracted"] == 1
    with open(temp_memory_file) as f:
        content = f.read()
    assert "~~[2024-01-01] The project started today~~" in content
    assert "[RETRACTED" in content
    # No reason text after the date
    assert "— " not in content.split("RETRACTED")[1].split("]")[0]

    history_file = temp_memory_file.replace(".md", "-history.md")
    if os.path.exists(history_file):
        os.remove(history_file)


def test_retract_missing_fact_is_noop(temp_memory_file):
    """RETRACT on a non-existent fact ID should be a no-op."""
    ops = [{"op": "RETRACT", "id": "nonexistent", "reason": "test"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["retracted"] == 0


def test_retract_missing_id_is_skipped(temp_memory_file):
    """RETRACT without an ID field should be skipped."""
    ops = [{"op": "RETRACT", "reason": "no id"}]
    stats = apply_operations(temp_memory_file, ops)
    assert stats["retracted"] == 0
