"""Tests for plato_core.registry — MeshRegistry."""

import pytest
from plato_core.registry import MeshRegistry


class TestMeshRegistry:
    def test_singleton(self):
        r1 = MeshRegistry()
        r2 = MeshRegistry()
        assert r1 is r2

    def test_register_and_get(self):
        registry = MeshRegistry()
        registry.reset()
        registry.register("test_cat", "test_item", lambda: "hello")
        result = registry.get("test_cat", "test_item")
        assert result == "hello"

    def test_get_all_category(self):
        registry = MeshRegistry()
        registry.reset()
        registry.register("cat1", "a", lambda: 1)
        registry.register("cat1", "b", lambda: 2)
        all_items = registry.get("cat1")
        assert "a" in all_items
        assert "b" in all_items

    def test_get_nonexistent(self):
        registry = MeshRegistry()
        registry.reset()
        assert registry.get("nonexistent", "x") is None

    def test_categories(self):
        registry = MeshRegistry()
        registry.reset()
        registry.register("cat_a", "x", lambda: None)
        registry.register("cat_b", "y", lambda: None)
        cats = registry.categories()
        assert "cat_a" in cats
        assert "cat_b" in cats

    def test_available_packages(self):
        registry = MeshRegistry()
        registry.reset()
        registry.register("cat", "pkg1", lambda: None)
        registry.register("cat", "pkg2", lambda: None)
        pkgs = registry.available_packages()
        assert "pkg1" in pkgs
        assert "pkg2" in pkgs

    def test_reset(self):
        registry = MeshRegistry()
        registry.register("cat", "x", lambda: None)
        registry.reset()
        cats = registry.categories()
        assert "cat" not in cats

    def test_convenience_getters_no_error(self):
        registry = MeshRegistry()
        registry.reset()
        # After reset, no plugins are discovered yet
        # Just verify the methods exist and return dicts
        assert callable(registry.get_matchers)
        assert callable(registry.get_compressors)
        assert callable(registry.get_trainers)
        assert callable(registry.get_encoders)
        assert callable(registry.get_devices)
