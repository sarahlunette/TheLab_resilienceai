# Satellite Damage Assessment Tool Integration

## Overview

The Satellite Damage Assessment Tool provides comprehensive post-disaster damage analysis using Sentinel-2 satellite imagery. It has been integrated into TheLab Crisis & Resilience AI platform as a set of LangChain tools that the AI agent can invoke to assess infrastructure damage, classify severity levels, and generate detailed reports.

## Features

The tool provides five main capabilities accessible through the LangChain agent:

### 1. Create Damage Assessment Project
**Tool Name:** `create_damage_assessment`

Creates a new disaster damage assessment project with specified parameters.

**Parameters:**
- `name` (str, required): Project name (e.g., "Hurricane Maria 2023 Assessment")
- `location` (str, required): Location name (e.g., "Puerto Rico")
- `disaster_type` (str, required): Type of disaster
  - Options: earthquake, flood, hurricane, wildfire, tornado, tsunami, landslide, other
- `latitude` (float, required): Latitude coordinate of affected area
- `longitude` (float, required): Longitude coordinate of affected area
- `before_date` (str, optional): Pre-disaster baseline date (YYYY-MM-DD format)
- `after_date` (str, optional): Post-disaster assessment date (YYYY-MM-DD format)
- `description` (str, optional): Project description

**Returns:**
```json
{
  "status": "success",
  "project_id": 1,
  "message": "Damage assessment project created successfully",
  "next_step": "Use process_damage_assessment(1) to start the analysis"
}
```

### 2. Process Damage Assessment
**Tool Name:** `process_damage_assessment`

Starts processing the satellite imagery analysis, including spectral indices calculation, infrastructure detection, and damage classification.

**Parameters:**
- `project_id` (int, required): The ID of the project to process

**Processing Steps:**
1. Calculate spectral indices:
   - **NDVI** (Normalized Difference Vegetation Index) - vegetation health
   - **NDBI** (Normalized Difference Built-up Index) - building detection
   - **MNDWI** (Modified Normalized Difference Water Index) - water detection
   - **NBR** (Normalized Burn Ratio) - fire damage assessment
2. Detect infrastructure elements (buildings, roads, bridges, power lines)
3. Classify damage by category (structural, flooding, fire, vegetation loss)
4. Assign severity levels (destroyed, heavily damaged, moderately damaged, minor)
5. Calculate sector-based statistics

**Returns:**
```json
{
  "status": "success",
  "message": "Analysis processing started",
  "processing_info": "Calculating spectral indices and detecting infrastructure",
  "next_step": "Use get_damage_assessment_results(1) to retrieve results"
}
```

### 3. Get Damage Assessment Results
**Tool Name:** `get_damage_assessment_results`

Retrieves comprehensive results from a completed damage assessment.

**Parameters:**
- `project_id` (int, required): The ID of the project

**Returns:**
```json
{
  "status": "success",
  "project_name": "Hurricane Maria Assessment",
  "location": "Puerto Rico",
  "disaster_type": "hurricane",
  "analysis_status": "completed",
  "summary": {
    "total_infrastructure_detected": 156,
    "total_damage_events": 423,
    "severity_distribution": {
      "destroyed": 89,
      "heavily_damaged": 134,
      "moderately_damaged": 156,
      "minor_damage": 44
    },
    "infrastructure_by_type": {
      "buildings": 98,
      "roads": 45,
      "bridges": 8,
      "power_lines": 5
    }
  },
  "sector_analysis": {
    "residential": {
      "total_count": 65,
      "destroyed": 23,
      "heavily_damaged": 28,
      "moderately_damaged": 12,
      "minor_damage": 2
    },
    "commercial": {...},
    "infrastructure": {...},
    "agricultural": {...}
  },
  "export_options": {
    "csv": "Use export_damage_assessment_csv(1) to download detailed CSV",
    "pdf": "Use export_damage_assessment_pdf(1) to generate PDF report"
  }
}
```

### 4. Export CSV Data
**Tool Name:** `export_damage_assessment_csv`

Exports detailed damage assessment data as a CSV file suitable for RAG systems and data analysis.

**Parameters:**
- `project_id` (int, required): The ID of the project

**CSV Contents:**
- Infrastructure type and count
- Damage category classification
- Severity level for each element
- Geographic coordinates (latitude, longitude)
- Affected area measurements (m²)
- Sector classification
- Confidence scores
- Detection timestamps

**Returns:**
```json
{
  "status": "success",
  "csv_url": "https://storage.example.com/exports/damage_assessment_1.csv",
  "filename": "damage_assessment_1.csv",
  "message": "CSV export generated successfully"
}
```

### 5. Export PDF Report
**Tool Name:** `export_damage_assessment_pdf`

Generates a comprehensive PDF report with visualizations and detailed analysis.

**Parameters:**
- `project_id` (int, required): The ID of the project

**PDF Contents:**
- Executive summary with key statistics
- Damage severity distribution charts
- Infrastructure type breakdown tables
- Sector analysis with visual charts
- Before/after imagery comparisons
- Geographic damage maps
- Detailed assessment tables

**Returns:**
```json
{
  "status": "success",
  "pdf_url": "https://storage.example.com/exports/damage_assessment_1.pdf",
  "filename": "damage_assessment_1.pdf",
  "message": "PDF report generated successfully"
}
```

## Usage Examples

### Example 1: Complete Workflow
```python
# Step 1: Create assessment project
result = create_damage_assessment(
    name="Hurricane Irma 2017 Assessment",
    location="Saint-Martin",
    disaster_type="hurricane",
    latitude=18.0708,
    longitude=-63.0501,
    before_date="2017-08-01",
    after_date="2017-09-15",
    description="Post-Hurricane Irma damage assessment for recovery planning"
)
project_id = result["project_id"]

# Step 2: Process the analysis
process_result = process_damage_assessment(project_id=project_id)

# Step 3: Retrieve results
results = get_damage_assessment_results(project_id=project_id)

# Step 4: Export data
csv_export = export_damage_assessment_csv(project_id=project_id)
pdf_export = export_damage_assessment_pdf(project_id=project_id)
```

### Example 2: Agent Conversation Flow
```
User: "Assess the damage from the recent earthquake in Haiti at coordinates 18.5944, -72.3074"

Agent: [Calls create_damage_assessment tool]
Agent: "I've created a damage assessment project for the Haiti earthquake. Now processing the satellite imagery..."

Agent: [Calls process_damage_assessment tool]
Agent: "The analysis is underway, calculating spectral indices and detecting infrastructure..."

Agent: [Calls get_damage_assessment_results tool]
Agent: "The assessment is complete. Here are the key findings:
- 234 infrastructure elements detected
- 87 buildings destroyed, 123 heavily damaged
- Residential sector most affected with 156 damaged structures
- Road network: 45 segments damaged
Would you like me to generate a detailed PDF report?"

User: "Yes, generate the PDF report"

Agent: [Calls export_damage_assessment_pdf tool]
Agent: "The comprehensive PDF report has been generated and is available at [URL]. 
It includes damage maps, severity charts, and sector-by-sector analysis."
```

## Configuration

### Environment Variables

Set the following environment variable to configure the tool:

```bash
export DAMAGE_ASSESSMENT_API_URL="https://your-deployment-url.com/api/trpc"
```

If not set, it defaults to the development server URL.

### Integration with TheLab

The tool is automatically registered in `app/main.py` and available to all LangChain agents in the system. No additional configuration is required.

## Technical Details

### API Communication
The tool communicates with the Disaster Damage Assessment System via tRPC endpoints:
- `analysis.create` - Create new project
- `analysis.processAnalysis` - Start processing
- `analysis.getResults` - Retrieve results
- `analysis.exportCSV` - Generate CSV export
- `analysis.exportPDF` - Generate PDF report

### Error Handling
All functions return structured responses with:
- `status`: "success" or "error"
- `message`: Human-readable description
- Additional fields based on the operation

### Timeout Settings
- Create/Get operations: 30 seconds
- Process operations: 120 seconds (analysis takes time)
- Export operations: 60-120 seconds (report generation)

## Testing

Test suite is available at `tests/test_satellite_damage.py`:

```bash
python -m pytest tests/test_satellite_damage.py -v
```

Tests cover:
- Successful API calls
- Error handling
- Exception handling
- Parameter validation
- Response parsing

## Damage Classification System

### Severity Levels
1. **Destroyed** (>75% damage): Complete loss, requires reconstruction
2. **Heavily Damaged** (50-75%): Major structural damage, extensive repairs needed
3. **Moderately Damaged** (25-50%): Significant but repairable damage
4. **Minor Damage** (<25%): Light damage, minor repairs required

### Damage Categories
- **Structural Destruction**: Building collapse, structural failures
- **Flooding**: Water inundation and flood damage
- **Fire/Burn Scars**: Wildfire and thermal damage
- **Vegetation Loss**: Deforestation and agricultural damage
- **Infrastructure Damage**: Roads, bridges, utilities

### Infrastructure Types
- **Buildings**: Residential and commercial structures
- **Roads/Highways**: Transportation network segments
- **Bridges**: Critical crossing infrastructure
- **Power Lines**: Electrical distribution network

### Sectors
- **Residential**: Housing and residential buildings
- **Commercial**: Business and commercial structures
- **Infrastructure**: Transportation and utilities
- **Agricultural**: Farmland and agricultural areas
- **Water Resources**: Water bodies and distribution

## Use Cases

1. **Post-Disaster Assessment**: Rapid damage evaluation after natural disasters
2. **Recovery Planning**: Prioritize reconstruction based on severity and sector
3. **Insurance Claims**: Document damage extent with quantitative data
4. **Resource Allocation**: Identify areas needing immediate assistance
5. **Progress Monitoring**: Track recovery over time with repeated assessments
6. **Risk Analysis**: Identify vulnerable infrastructure for future planning

## Limitations

- Requires clear satellite imagery (cloud cover affects accuracy)
- Resolution limited by Sentinel-2 specifications (10-60m depending on band)
- Processing time varies based on area size and complexity
- Infrastructure detection accuracy depends on spectral signatures

## Future Enhancements

1. Real-time Sentinel-2 API integration for automatic imagery fetching
2. Machine learning models for improved damage detection accuracy
3. Multi-temporal analysis to track recovery progress
4. Integration with additional satellite sources (Landsat, Planet)
5. 3D damage visualization capabilities
6. Automated change detection alerts

## Support

For issues, questions, or feature requests related to the Satellite Damage Assessment Tool:
- Check the main TheLab documentation
- Review test cases for usage examples
- Contact the development team

## License

This tool is part of TheLab Crisis & Resilience AI platform and follows the same MIT License.
