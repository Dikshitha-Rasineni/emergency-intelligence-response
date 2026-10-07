# Emergency Intelligence & Response

## 21CSE306P – Applied Generative AI

Emergency Intelligence & Response is a geospatial decision-support system designed to understand emergency reports, assess severity, prioritize incidents, identify suitable nearby emergency resources, and generate response recommendations.

## Team

- Dikshitha – Full Stack + GenAI + Integration
- T. Himesh – Dataset + ML + Testing
- S. Mourya Veer – Hardware + IoT

## Technology Stack

### Frontend
- React
- JavaScript
- HTML
- CSS
- Leaflet
- Plotly

### Backend
- Python
- FastAPI

### Database
- PostgreSQL
- PostGIS

### GenAI
- Pretrained open-source generative language model
- Domain adaptation using emergency-response datasets

### Machine Learning
- Python
- Scikit-learn

### Geospatial
- PostGIS
- Leaflet
- OpenStreetMap

### Hardware
- ESP32
- GPS
- Emergency sensors

## Core Workflow

Emergency Input  
→ GenAI Emergency Understanding  
→ Structured Incident Data  
→ Severity & Priority Assessment  
→ Geospatial Resource Retrieval  
→ Resource Ranking  
→ GenAI Response Generation  
→ Emergency Dashboard

## Project Structure

```text
frontend/       React application
backend/        FastAPI backend
genai/          GenAI modules
ml/             Machine learning
iot/            ESP32 and sensor implementation
database/       PostgreSQL + PostGIS
datasets/       Public and synthetic datasets
testing/        Test cases and evaluation
docs/           Project documentation