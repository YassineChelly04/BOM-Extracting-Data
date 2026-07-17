"""Unit tests for normalization."""
import pytest
from material_extractor.normalization import ScalableNormalizer
from material_extractor.models import MaterialCategory, NormalizationMethod


class TestScalableNormalizer:
    """Tests for ScalableNormalizer."""
    
    @pytest.fixture
    def normalizer(self, tmp_path):
        """Create a fresh normalizer with temp data dir."""
        normalizer = ScalableNormalizer(data_dir=tmp_path / "normalization")
        normalizer.load()
        return normalizer
    
    def test_unknown_material(self, normalizer):
        """Test unknown material returns as-is with low confidence."""
        result = normalizer.normalize("Completely Unknown Material XYZ")
        
        assert result.normalized == "Completely Unknown Material XYZ"
        assert result.category == MaterialCategory.UNKNOWN
        assert result.confidence == 0.5
        assert result.method == NormalizationMethod.EXACT_MATCH
    
    def test_load_default_data(self, tmp_path):
        """Test loading default normalization data from YAML."""
        normalizer = ScalableNormalizer(data_dir=tmp_path / "normalization")
        # Create test materials.yaml
        import yaml
        normalizer.data_dir.mkdir(parents=True, exist_ok=True)
        with open(normalizer.data_dir / "materials.yaml", "w") as f:
            yaml.dump({
                "Copper (Cu)": {"category": "Metal", "aliases": ["copper", "cu"]},
                "Gold (Au)": {"category": "Metal", "aliases": ["gold", "au"]},
            }, f)
        
        normalizer.load()
        
        result = normalizer.normalize("copper")
        assert result.normalized == "Copper (Cu)"
        assert result.category == MaterialCategory.METAL
        assert result.method == NormalizationMethod.ALIAS_MAP
        assert result.confidence == 1.0
        
        # Test case insensitive
        result = normalizer.normalize("COPPER")
        assert result.normalized == "Copper (Cu)"
        
        result = normalizer.normalize("gold")
        assert result.normalized == "Gold (Au)"
    
    def test_fuzzy_match(self, tmp_path):
        """Test fuzzy matching."""
        normalizer = ScalableNormalizer(data_dir=tmp_path / "normalization")
        import yaml
        normalizer.data_dir.mkdir(parents=True, exist_ok=True)
        with open(normalizer.data_dir / "materials.yaml", "w") as f:
            yaml.dump({
                "Aluminum (Al)": {"category": "Metal", "aliases": ["aluminum", "al"]},
            }, f)
        
        normalizer.config.fuzzy_threshold = 0.85
        normalizer.load()
        
        result = normalizer.normalize("aluminium")
        assert result.method == NormalizationMethod.FUZZY_MATCH
        assert result.confidence > 0.8
        assert result.normalized == "Aluminum (Al)"
    
    def test_substance_normalization(self, tmp_path):
        """Test substance normalization."""
        normalizer = ScalableNormalizer(data_dir=tmp_path / "normalization")
        import yaml
        normalizer.data_dir.mkdir(parents=True, exist_ok=True)
        with open(normalizer.data_dir / "substances.yaml", "w") as f:
            yaml.dump({
                "Copper (Cu)": {"aliases": ["cu", "copper"], "cas_number": "7440-50-8"},
            }, f)
        
        normalizer.load()
        
        # Substance normalization works when material is provided but unknown
        result = normalizer.normalize("unknown material", "cu")
        assert result.normalized == "Copper (Cu)"
        assert result.method == NormalizationMethod.CAS_NUMBER
    
    def test_add_and_save_material(self, normalizer, tmp_path):
        """Test adding and saving material to YAML."""
        normalizer.add_material("Test Material", ["test"], MaterialCategory.METAL)
        normalizer.save_material("Test Material", ["test"], MaterialCategory.METAL)
        
        # Create new normalizer and load
        new_normalizer = ScalableNormalizer(data_dir=normalizer.data_dir)
        new_normalizer.load()
        
        result = new_normalizer.normalize("test")
        assert result.normalized == "Test Material"
        assert result.category == MaterialCategory.METAL
    
    def test_stats(self, tmp_path):
        """Test statistics."""
        normalizer = ScalableNormalizer(data_dir=tmp_path / "normalization")
        import yaml
        normalizer.data_dir.mkdir(parents=True, exist_ok=True)
        with open(normalizer.data_dir / "materials.yaml", "w") as f:
            yaml.dump({
                "Test 1": {"category": "Metal", "aliases": ["t1"]},
                "Test 2": {"category": "Polymer", "aliases": ["t2"]},
            }, f)
        with open(normalizer.data_dir / "substances.yaml", "w") as f:
            yaml.dump({
                "Substance 1": {"aliases": ["s1"]},
            }, f)
        
        normalizer.load()
        
        stats = normalizer.stats()
        
        assert stats["materials"] == 2
        assert stats["substances"] == 1
        assert stats["total_aliases"] >= 3
    
    def test_normalize_record(self, tmp_path):
        """Test normalizing a MaterialRecord."""
        normalizer = ScalableNormalizer(data_dir=tmp_path / "normalization")
        import yaml
        normalizer.data_dir.mkdir(parents=True, exist_ok=True)
        with open(normalizer.data_dir / "materials.yaml", "w") as f:
            yaml.dump({
                "Copper (Cu)": {"category": "Metal", "aliases": ["copper", "cu"]},
            }, f)
        
        normalizer.load()
        
        from material_extractor.models import MaterialRecord
        record = MaterialRecord(
            material="copper",
            substance="cu",
            weight_mg=1.0,
            raw_material="copper",
            raw_substance="cu"
        )
        
        result = normalizer.normalize_record(record)
        
        assert result.material == "Copper (Cu)"
        assert result.category == MaterialCategory.METAL
        assert result.confidence <= 1.0
        assert result.normalization_method is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])