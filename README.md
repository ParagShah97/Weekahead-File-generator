# Financial Year Data Generator

## Overview
The Financial Year Data Generator is a Streamlit application that allows users to generate and download text files containing structured financial year data for the years 2024 to 2030. It integrates AI processing capabilities to enhance data generation, making it a valuable tool for financial reporting and analysis.

## Tech Stack
- **Frontend**: Streamlit
- **Backend**: Python
- **Data Validation**: Pydantic
- **AI Integration**: OpenAI API (via langchain_openai)
- **Environment Management**: dotenv

## Project Structure
```
.
├── main.py                   # Streamlit app for user interface
├── script_based_generation.py # Generates structured weekly financial data
├── util/
│   ├── ai_worker.py          # AI-driven prompt generation for scheduling
│   ├── ai_worker2.py         # AI-driven weekly schedule generation
│   ├── ai_worker3.py         # JSON output for weekly schedules
│   └── graph_testing.ipynb    # Testing agentic architecture with state graph
```

## Key Components/Modules
- **main.py**: User interface for selecting financial years and generating downloadable text files.
- **script_based_generation.py**: Generates structured weekly data, including key financial dates.
- **util/ai_worker.py**: Constructs prompts for AI processing using OpenAI's language model.
- **util/ai_worker2.py**: Focuses on generating weekly schedules based on user-defined parameters.
- **util/ai_worker3.py**: Outputs structured schedule data in JSON format.
- **util/graph_testing.ipynb**: Tests and develops intelligent agent behavior using a state graph.

## Setup
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
To run the Streamlit application:
```bash
streamlit run main.py
```
Once running, use the web interface to select a financial year and generate the corresponding text file.

## Configuration
| NAME                  | Purpose                                      | Required | Default |
|-----------------------|----------------------------------------------|----------|---------|
| OPENAI_API_KEY        | API key for OpenAI services                  | Yes      | N/A     |
| OTHER_ENV_VARIABLES   | Additional configuration variables as needed | No       | N/A     |

## Data Model
- **RowData**: Defines the structure of weekly data for financial years.
- **PromptStructure**: Defines the structure of prompts for AI processing.

## Testing
To run tests, ensure you have the necessary testing framework installed and execute:
```bash
pytest
```

## Deployment
Consider using Docker for containerization or CI/CD pipelines for automated deployment. Ensure environment variables are set correctly in the production environment.

## Roadmap/Limitations
- Future enhancements may include support for additional financial years and improved AI processing capabilities.
- Currently limited to generating data for the years 2024-2030. Further expansion may require additional development.
