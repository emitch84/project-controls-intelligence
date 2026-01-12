# Project Controls Intelligence

A portfolio project demonstrating a systems analyst skill set for project controls. This tool ingests project schedule and cost data, computes core metrics (CPI, SPI, EAC), performs data quality checks, and creates a lightweight Streamlit dashboard for insights.

## Features

- **Synthetic Data Generation**: Creates plausible project data for 3 projects over 2 years.
- **ETL Pipeline**: Loads CSV data into a local SQLite database with standardized views.
- **Metric Engine**: computes CPI, SPI, VAC, TCPI, and identifies health flags.
- **Quality Assurance**: Automated checks for data integrity (negative values, continuity).
- **Interactive Dashboard**: Streamlit app for visualizing project performance trends.

## Setup

1.  **Clone the repository**:
    ```bash
    git clone <repo_url>
    cd project_controls_intelligence
    ```

2.  **Install dependencies**:
    ```bash
    make setup
    # Or manually: pip install -r requirements.txt
    ```

## Usage

1.  **Generate Data**:
    ```bash
    make generate_data
    ```
    Creates CSV files in `data/raw/`.

2.  **Build Database**:
    ```bash
    make build_db
    ```
    Loads data into `data/processed/pc_intel.db`.

3.  **Run Dashboard**:
    ```bash
    make run_app
    ```
    Opens the Streamlit app in your browser.

4.  **Run Tests**:
    ```bash
    make test
    ```

## Project Structure

- `data/`: Raw CSVs and Processed SQLite DB.
- `src/`: Source code.
    - `data_gen/`: Scripts for synthetic data.
    - `etl/`: Database loading and schema definitions.
    - `metrics/`: Calculation logic.
    - `quality/`: Data validation checks.
    - `app/`: Streamlit dashboard code.
- `tests/`: Pytest unit tests.

## Screenshots

*(Placeholder for screenshots of the dashboard Overview and Trends pages)*
