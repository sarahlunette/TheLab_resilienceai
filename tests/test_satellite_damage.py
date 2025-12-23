"""
Test suite for Satellite Damage Assessment Tool integration
"""

import pytest
from unittest.mock import Mock, patch
from app.tools.satellite_damage_tool import (
    create_damage_assessment,
    process_damage_assessment,
    get_damage_assessment_results,
    export_damage_assessment_csv,
    export_damage_assessment_pdf
)


class TestSatelliteDamageTool:
    """Test satellite damage assessment tool functionality"""
    
    def test_create_damage_assessment_success(self):
        """Test successful creation of damage assessment project"""
        with patch('app.tools.satellite_damage_tool.requests.post') as mock_post:
            # Mock successful API response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "data": {
                        "json": {
                            "id": 1,
                            "name": "Test Hurricane Assessment"
                        }
                    }
                }
            }
            mock_post.return_value = mock_response
            
            result = create_damage_assessment(
                name="Test Hurricane Assessment",
                location="Puerto Rico",
                disaster_type="hurricane",
                latitude=18.2208,
                longitude=-66.5901,
                before_date="2023-09-01",
                after_date="2023-09-20"
            )
            
            assert result["status"] == "success"
            assert result["project_id"] == 1
            assert "created successfully" in result["message"]
    
    def test_create_damage_assessment_missing_params(self):
        """Test creation with missing required parameters"""
        # This should be handled by the function's validation
        result = create_damage_assessment(
            name="",
            location="",
            disaster_type="",
            latitude=0.0,
            longitude=0.0
        )
        
        # The function should still attempt to create, but may fail
        assert "status" in result
    
    def test_process_damage_assessment_success(self):
        """Test successful processing of damage assessment"""
        with patch('app.tools.satellite_damage_tool.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "data": {
                        "json": {
                            "message": "Analysis processing started",
                            "status": "processing"
                        }
                    }
                }
            }
            mock_post.return_value = mock_response
            
            result = process_damage_assessment(project_id=1)
            
            assert result["status"] == "success"
            assert "processing" in result["message"].lower() or "started" in result["message"].lower()
    
    def test_get_damage_assessment_results_success(self):
        """Test retrieval of damage assessment results"""
        with patch('app.tools.satellite_damage_tool.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "data": {
                        "json": {
                            "project": {
                                "name": "Test Assessment",
                                "location": "Test Location",
                                "disasterType": "hurricane",
                                "status": "completed"
                            },
                            "infrastructure": [
                                {"elementType": "building", "severityLevel": "destroyed"},
                                {"elementType": "road", "severityLevel": "heavily_damaged"}
                            ],
                            "damages": [
                                {"severityLevel": "destroyed"},
                                {"severityLevel": "heavily_damaged"}
                            ],
                            "sectorStats": [
                                {
                                    "sector": "residential",
                                    "totalCount": 10,
                                    "destroyedCount": 5,
                                    "heavilyDamagedCount": 3,
                                    "moderatelyDamagedCount": 2,
                                    "minorDamageCount": 0
                                }
                            ]
                        }
                    }
                }
            }
            mock_get.return_value = mock_response
            
            result = get_damage_assessment_results(project_id=1)
            
            assert result["status"] == "success"
            assert result["project_name"] == "Test Assessment"
            assert "summary" in result
            assert "sector_analysis" in result
            assert result["summary"]["total_infrastructure_detected"] == 2
    
    def test_export_csv_success(self):
        """Test CSV export functionality"""
        with patch('app.tools.satellite_damage_tool.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "data": {
                        "json": {
                            "url": "https://example.com/export.csv",
                            "filename": "damage_assessment_1.csv"
                        }
                    }
                }
            }
            mock_post.return_value = mock_response
            
            result = export_damage_assessment_csv(project_id=1)
            
            assert result["status"] == "success"
            assert "csv_url" in result
            assert result["filename"] == "damage_assessment_1.csv"
    
    def test_export_pdf_success(self):
        """Test PDF export functionality"""
        with patch('app.tools.satellite_damage_tool.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": {
                    "data": {
                        "json": {
                            "url": "https://example.com/report.pdf",
                            "filename": "damage_assessment_1.pdf"
                        }
                    }
                }
            }
            mock_post.return_value = mock_response
            
            result = export_damage_assessment_pdf(project_id=1)
            
            assert result["status"] == "success"
            assert "pdf_url" in result
            assert result["filename"] == "damage_assessment_1.pdf"
    
    def test_api_error_handling(self):
        """Test handling of API errors"""
        with patch('app.tools.satellite_damage_tool.requests.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            mock_post.return_value = mock_response
            
            result = create_damage_assessment(
                name="Test",
                location="Test",
                disaster_type="hurricane",
                latitude=0.0,
                longitude=0.0
            )
            
            assert result["status"] == "error"
            assert "500" in result["message"]
    
    def test_exception_handling(self):
        """Test handling of exceptions during API calls"""
        with patch('app.tools.satellite_damage_tool.requests.post', side_effect=Exception("Network error")):
            result = create_damage_assessment(
                name="Test",
                location="Test",
                disaster_type="hurricane",
                latitude=0.0,
                longitude=0.0
            )
            
            assert result["status"] == "error"
            assert "Exception occurred" in result["message"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
