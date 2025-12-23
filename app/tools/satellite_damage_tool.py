"""
Satellite Damage Assessment Tool for TheLab Crisis & Resilience AI

This tool integrates with the Disaster Damage Assessment System to provide
post-disaster damage analysis using Sentinel-2 satellite imagery.
"""

import os
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("tools")

# Configuration
DAMAGE_ASSESSMENT_API_URL = os.getenv(
    "DAMAGE_ASSESSMENT_API_URL", 
    "https://3000-isehqg9uoo7cmpv67m7o7-516a64ce.manusvm.computer/api/trpc"
)


def create_damage_assessment(
    name: str,
    location: str,
    disaster_type: str,
    latitude: float,
    longitude: float,
    before_date: Optional[str] = None,
    after_date: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new disaster damage assessment project.
    
    Args:
        name: Project name (e.g., "Hurricane Maria 2023 Assessment")
        location: Location name (e.g., "Puerto Rico")
        disaster_type: Type of disaster (earthquake, flood, hurricane, wildfire, tornado, tsunami, landslide, other)
        latitude: Latitude coordinate of the affected area
        longitude: Longitude coordinate of the affected area
        before_date: Pre-disaster baseline date (YYYY-MM-DD format)
        after_date: Post-disaster assessment date (YYYY-MM-DD format)
        description: Optional project description
        
    Returns:
        dict: {status, project_id, message}
    """
    logger.info(f"[TOOL CALLED] create_damage_assessment(name={name}, location={location})")
    
    try:
        # Prepare request payload
        payload = {
            "name": name,
            "location": location,
            "disasterType": disaster_type,
            "coordinates": {
                "lat": latitude,
                "lng": longitude
            }
        }
        
        if description:
            payload["description"] = description
            
        if before_date:
            payload["beforeDate"] = before_date
            
        if after_date:
            payload["afterDate"] = after_date
        
        # Make API request
        response = requests.post(
            f"{DAMAGE_ASSESSMENT_API_URL}/analysis.create",
            json={"json": payload},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            project_id = result.get("result", {}).get("data", {}).get("json", {}).get("id")
            
            return {
                "status": "success",
                "project_id": project_id,
                "message": f"Damage assessment project '{name}' created successfully. Project ID: {project_id}",
                "next_step": f"Use process_damage_assessment({project_id}) to start the analysis"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to create project: HTTP {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        logger.error(f"Error creating damage assessment: {e}")
        return {
            "status": "error",
            "message": f"Exception occurred: {str(e)}"
        }


def process_damage_assessment(project_id: int) -> Dict[str, Any]:
    """
    Start processing a damage assessment project to analyze satellite imagery.
    
    Args:
        project_id: The ID of the project to process
        
    Returns:
        dict: {status, message, processing_info}
    """
    logger.info(f"[TOOL CALLED] process_damage_assessment(project_id={project_id})")
    
    try:
        response = requests.post(
            f"{DAMAGE_ASSESSMENT_API_URL}/analysis.processAnalysis",
            json={"json": {"projectId": project_id}},
            headers={"Content-Type": "application/json"},
            timeout=120  # Processing may take longer
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("result", {}).get("data", {}).get("json", {})
            
            return {
                "status": "success",
                "message": data.get("message", "Analysis processing started"),
                "processing_info": "The system is calculating spectral indices (NDVI, NDBI, MNDWI, NBR), detecting infrastructure, and classifying damage severity.",
                "next_step": f"Use get_damage_assessment_results({project_id}) to retrieve the analysis results"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to process analysis: HTTP {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        logger.error(f"Error processing damage assessment: {e}")
        return {
            "status": "error",
            "message": f"Exception occurred: {str(e)}"
        }


def get_damage_assessment_results(project_id: int) -> Dict[str, Any]:
    """
    Retrieve the results of a completed damage assessment.
    
    Args:
        project_id: The ID of the project
        
    Returns:
        dict: Comprehensive damage assessment results including:
            - Infrastructure counts (buildings, roads, bridges, power lines)
            - Damage severity distribution (destroyed, heavily damaged, moderately damaged, minor)
            - Sector-based statistics (residential, commercial, infrastructure, agricultural)
            - Geographic coordinates of damage locations
    """
    logger.info(f"[TOOL CALLED] get_damage_assessment_results(project_id={project_id})")
    
    try:
        response = requests.get(
            f"{DAMAGE_ASSESSMENT_API_URL}/analysis.getResults",
            params={"input": f'{{"json":{{"projectId":{project_id}}}}}'},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("result", {}).get("data", {}).get("json", {})
            
            project = data.get("project", {})
            infrastructure = data.get("infrastructure", [])
            damages = data.get("damages", [])
            sector_stats = data.get("sectorStats", [])
            
            # Calculate summary statistics
            severity_counts = {
                "destroyed": len([d for d in damages if d.get("severityLevel") == "destroyed"]),
                "heavily_damaged": len([d for d in damages if d.get("severityLevel") == "heavily_damaged"]),
                "moderately_damaged": len([d for d in damages if d.get("severityLevel") == "moderately_damaged"]),
                "minor_damage": len([d for d in damages if d.get("severityLevel") == "minor_damage"])
            }
            
            infra_counts = {
                "buildings": len([i for i in infrastructure if i.get("elementType") == "building"]),
                "roads": len([i for i in infrastructure if i.get("elementType") == "road"]),
                "bridges": len([i for i in infrastructure if i.get("elementType") == "bridge"]),
                "power_lines": len([i for i in infrastructure if i.get("elementType") == "power_line"])
            }
            
            # Format sector statistics
            sector_summary = {}
            for sector in sector_stats:
                sector_name = sector.get("sector", "unknown")
                sector_summary[sector_name] = {
                    "total_count": sector.get("totalCount", 0),
                    "destroyed": sector.get("destroyedCount", 0),
                    "heavily_damaged": sector.get("heavilyDamagedCount", 0),
                    "moderately_damaged": sector.get("moderatelyDamagedCount", 0),
                    "minor_damage": sector.get("minorDamageCount", 0)
                }
            
            return {
                "status": "success",
                "project_name": project.get("name"),
                "location": project.get("location"),
                "disaster_type": project.get("disasterType"),
                "analysis_status": project.get("status"),
                "summary": {
                    "total_infrastructure_detected": len(infrastructure),
                    "total_damage_events": len(damages),
                    "severity_distribution": severity_counts,
                    "infrastructure_by_type": infra_counts
                },
                "sector_analysis": sector_summary,
                "export_options": {
                    "csv": f"Use export_damage_assessment_csv({project_id}) to download detailed CSV",
                    "pdf": f"Use export_damage_assessment_pdf({project_id}) to generate PDF report"
                }
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to retrieve results: HTTP {response.status_code}",
                "details": response.text
            }
            
    except Exception as e:
        logger.error(f"Error retrieving damage assessment results: {e}")
        return {
            "status": "error",
            "message": f"Exception occurred: {str(e)}"
        }


def export_damage_assessment_csv(project_id: int) -> Dict[str, Any]:
    """
    Export damage assessment results as CSV file.
    
    Args:
        project_id: The ID of the project
        
    Returns:
        dict: {status, csv_url, message}
    """
    logger.info(f"[TOOL CALLED] export_damage_assessment_csv(project_id={project_id})")
    
    try:
        response = requests.post(
            f"{DAMAGE_ASSESSMENT_API_URL}/analysis.exportCSV",
            json={"json": {"projectId": project_id}},
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("result", {}).get("data", {}).get("json", {})
            
            return {
                "status": "success",
                "csv_url": data.get("url"),
                "filename": data.get("filename"),
                "message": "CSV export generated successfully. The file contains detailed infrastructure counts, damage categories, severity levels, coordinates, and sector classifications."
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to export CSV: HTTP {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        return {
            "status": "error",
            "message": f"Exception occurred: {str(e)}"
        }


def export_damage_assessment_pdf(project_id: int) -> Dict[str, Any]:
    """
    Generate comprehensive PDF report of damage assessment.
    
    Args:
        project_id: The ID of the project
        
    Returns:
        dict: {status, pdf_url, message}
    """
    logger.info(f"[TOOL CALLED] export_damage_assessment_pdf(project_id={project_id})")
    
    try:
        response = requests.post(
            f"{DAMAGE_ASSESSMENT_API_URL}/analysis.exportPDF",
            json={"json": {"projectId": project_id}},
            headers={"Content-Type": "application/json"},
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            data = result.get("result", {}).get("data", {}).get("json", {})
            
            return {
                "status": "success",
                "pdf_url": data.get("url"),
                "filename": data.get("filename"),
                "message": "PDF report generated successfully. The report includes damage maps, statistics tables, charts, and before/after imagery comparisons."
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to export PDF: HTTP {response.status_code}"
            }
            
    except Exception as e:
        logger.error(f"Error exporting PDF: {e}")
        return {
            "status": "error",
            "message": f"Exception occurred: {str(e)}"
        }
