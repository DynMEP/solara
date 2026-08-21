# ☀️ SOLARA - Solar Analytics & Revenue Advisor

[![Version](https://img.shields.io/badge/version-3.1.1-blue.svg)](https://github.com/dynmep/solara)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![NREL PySAM](https://img.shields.io/badge/PySAM-5.0+-orange.svg)](https://nrel-pysam.readthedocs.io/)
[![Status](https://img.shields.io/badge/status-production-brightgreen.svg)]()

**Professional-grade photovoltaic and battery energy storage system optimization platform. Open source, NREL-validated, production ready.**

<div align="center">

```
   _____ ____  _      ___    ____  ___    
  / ___// __ \| |    /   |  / __ \/   |   
  \__ \/ / / /| |   / /| | / /_/ / /| |   
 ___/ / /_/ / | |__/ ___ |/ _, _/ ___ |   
/____/\____/  |____/_/  |_/_/ |_/_/  |_|   
                                           
Solar Analytics & Revenue Advisor v3.1.1
Professional Solar+Storage Optimization Platform
```

**[Features](#-features) • [Installation](#-installation) • [Quick Start](#-quick-start) • [Examples](#-example-projects) • [Citation](#-citation)**

</div>

---

## 📖 Overview

**SOLARA** (Solar Analytics & Revenue Advisor) is a comprehensive open-source platform for designing, optimizing, and analyzing photovoltaic systems with battery energy storage. Built on NREL's validated PySAM models, SOLARA delivers professional-grade analysis capabilities comparable to commercial tools like **HOMER Pro** and **PVsyst** with the transparency and flexibility of **open source**.

Developed by [Alfonso A. Davila Vera](https://www.linkedin.com/in/alfonso-davila-vera), an electrical engineer with 20+ years of experience in power systems, renewable energy, and MEP/BIM design, SOLARA brings decades of industry expertise into a powerful, accessible tool for the renewable energy community.

### 🎯 Target Applications

| Application | Use Case |
|-------------|----------|
| **Utility-Scale Solar+Storage** | Multi-MW grid-connected systems with grid services |
| **Commercial & Industrial** | Behind-the-meter demand charge reduction |
| **Residential Systems** | Rooftop PV with backup power capability |
| **Microgrids** | Hybrid renewable energy systems |
| **Research & Academia** | Validated models for scientific publications |
| **MEP Design** | Professional system sizing and documentation |

### ⚡ Time Savings

**15-40 hours per project** compared to manual analysis or multiple tool workflows.

---

## 📦 Repository Contents

### Core Modules
1. **solara.py** - Main CLI and core engine for PV+Storage techno-economic analysis
2. **solara_weather_api.py** - NREL NSRDB TMY/PSM3 downloader with caching and validation
3. **solara_dashboard.py** - Dash/Plotly real-time UI with error handling
4. **solara_visualization.py** - Interactive Plotly dashboards and financial figures
5. **solara_advanced_optimization.py** - Multi-objective optimization (GA, Bayesian, ML surrogate, DE)

### Examples & Tests
6. **examples/example_config.json** - Complete 100kW commercial solar+storage configuration
7. **tests/** - Automated test suite (11 tests total)

---

## 💻 Installation

### Quick Install
```bash
# Clone repository
git clone https://github.com/dynmep/solara.git
cd solara

# Install dependencies
pip install -r requirements.txt

# Verify installation
python tests/test_visualization_standalone.py
```

### Requirements
- Python 3.9+
- PySAM 5.0+
- pandas, numpy
- requests, geopy
- plotly, dash, dash-bootstrap-components

**Optional for advanced optimization:**
- pymoo (NSGA-II genetic algorithm)
- scikit-optimize (Bayesian optimization)
- scikit-learn (ML surrogate models)

---

## ⚡ Quick Start

### 1. Get NREL API Key (Free)
Visit: https://developer.nrel.gov/signup/

### 2. Configure Environment
```bash
# Create .env file
cat > .env << EOF
NREL_API_KEY=your_key_here
NREL_EMAIL=your_email@domain.com
EOF

# Load environment
export $(cat .env | xargs)
```

### 3. Run Example
```bash
# Use provided example configuration
python solara.py --config examples/example_config.json

# Run with dashboard
python solara.py --config examples/example_config.json --dashboard

# Run wizard (interactive)
python solara.py
```

---

## 🎯 Features

### Core Capabilities
- ✅ **PySAM Integration** - NREL-validated PV+Storage simulations
- ✅ **Automated Weather Data** - NREL NSRDB with retry logic and caching
- ✅ **Multi-Objective Optimization** - NPV, ROI, payback, emissions
- ✅ **Interactive Dashboard** - Real-time web UI with live updates
- ✅ **Financial Analysis** - Comprehensive cashflow and NPV modeling
- ✅ **Visualizations** - Interactive Plotly figures and exports

### Optimization Methods
- **Parametric**: Grid search across parameter space
- **Genetic (NSGA-II)**: Multi-objective Pareto front optimization
- **Bayesian**: Gaussian Process-based minimization
- **ML Surrogate**: Gradient Boosting with Latin Hypercube Sampling
- **Differential Evolution**: Global optimization algorithm

### Weather Data Integration
- NREL NSRDB TMY/PSM3 data access
- Address-to-coordinates geocoding
- Local file caching system
- Rate limiting and retry logic
- NREL Terms of Service compliant

---

## 🏗️ Project Structure

```
solara/
├── .gitignore                             # Python/SOLARA ignores
├── CITATION.cff                           # Citation metadata
├── LICENSE                                # MIT License
├── NOTICE                                 # Third-party attribution
├── README.md                              # This file
├── requirements.txt                       # Dependencies
├── solara.py                              # Main CLI engine
├── solara_weather_api.py                  # Weather downloader
├── solara_dashboard.py                    # Web dashboard
├── solara_visualization.py                # Plotly figures
├── solara_advanced_optimization.py        # Advanced optimizers
├── examples/                              # Example configurations
│   └── example_config.json                # 100kW commercial example
└── tests/                                 # Test suite
    ├── test_weather_api.sh                # Weather API tests (5)
    ├── test_dashboard.sh                  # Dashboard tests (6)
    ├── test_visualization.bat             # Windows test
    └── test_visualization_standalone.py   # Cross-platform test
```

---

## 🔧 Configuration

### Environment Variables
```bash
# Required for NREL API
NREL_API_KEY=your_nrel_api_key
NREL_EMAIL=your_email@domain.com

# Optional
SOLARA_LOG_LEVEL=INFO
SOLARA_CACHE_DIR=~/.solara/weather_cache
```

### Example Configuration
See `examples/example_config.json` for a complete working example:
- 100kW commercial rooftop PV system
- 200kWh lithium-ion battery storage
- Time-of-use rates with demand charges
- Denver, CO location
- 25-year analysis period
- All parameters documented inline

### Create Your Own
```bash
# Copy example and modify
cp examples/example_config.json my_project.json
nano my_project.json

# Run your configuration
python solara.py --config my_project.json
```

### Key Sections
```json
{
  "project": { "name": "...", "description": "..." },
  "location": { "latitude": 39.74, "longitude": -104.99 },
  "pv": { "system_capacity": 100, "tilt": 20, "azimuth": 180 },
  "battery": { "initial_capacity": 200, "chemistry": 1 },
  "rates": { "structure": "tou", "peak": 0.18, "off_peak": 0.08 },
  "financial": { "analysis_period": 25, "itc_federal": 30 },
  "optimization": { "run_parametric": true }
}
```

---

## 📊 Output Files

### Reports
- `{project}_results_{timestamp}.txt` - Detailed text report
- `{project}_data_{timestamp}.csv` - Structured data export
- `optimization_history.csv` - Iteration-by-iteration results

### Visualizations
- `optimization_surface.html` - 3D parameter exploration
- `financial_dashboard.html` - NPV, cashflow, ROI charts
- `energy_profile.html` - Hourly generation/consumption
- `pareto_front.html` - Multi-objective trade-offs

### Directory Structure
```
results/
├── plots/                    # Interactive HTML figures
├── reports/                  # TXT/CSV reports
└── {project_name}/          # Project-specific outputs
```

---

## 🧪 Testing

### Quick Verification
```bash
# Cross-platform test (recommended first)
python tests/test_visualization_standalone.py

# Linux/Mac comprehensive tests
./tests/test_weather_api.sh      # 5 tests
./tests/test_dashboard.sh        # 6 tests

# Windows
tests\test_visualization.bat
```

### Make Executable (Linux/Mac)
```bash
chmod +x tests/*.sh
```

### Expected Results
- ✅ All 11 tests should pass with green checkmarks
- ✗ Red X marks indicate failures (review logs)

### Coverage
- Email requirement validation
- Environment variable loading
- Retry logic configuration
- Error handling in dashboard
- Empty data handling
- Mock optimizer integration

---

## 🚀 Usage Examples

### Basic Workflow
```python
from solara import SOLARA

# Initialize
solara = SOLARA()

# Run wizard (interactive)
solara.run_wizard()

# Or load config
solara.load_config('examples/example_config.json')

# Optimize
results = solara.optimize(method='parametric')

# Generate report
solara.generate_report(results)
```

### Advanced Optimization
```python
from solara_advanced_optimization import create_optimizer

# Create genetic optimizer
optimizer = create_optimizer(
    'genetic',
    objective_function,
    n_parallel=4,
    pop_size=50,
    n_gen=100
)

# Run optimization
results = optimizer.optimize()
```

### Weather Data
```python
from solara_weather_api import NSRDBWeatherAPI

# Initialize API
api = NSRDBWeatherAPI()

# Download weather data
weather_df = api.get_weather_data(
    latitude=39.74,
    longitude=-104.99,
    location_name='Denver_CO'
)
```

### Dashboard
```python
from solara_dashboard import SOLARADashboard

# Create dashboard
dashboard = SOLARADashboard(optimizer)

# Run in background
dashboard.run_in_background(port=8050)

# Access at: http://localhost:8050
```

### Command Line
```bash
# Basic run
python solara.py

# With config file
python solara.py --config examples/example_config.json

# With dashboard
python solara.py --config examples/example_config.json --dashboard

# Verbose output
python solara.py --config examples/example_config.json --verbose
```

---

## 🐛 Troubleshooting

### Common Issues

**"Email required" error:**
```bash
export NREL_EMAIL="your@email.com"
# Or add to .env file
echo "NREL_EMAIL=your@email.com" >> .env
```

**Weather downloads fail:**
1. Get API key: https://developer.nrel.gov/signup/
2. Verify internet connection
3. Check email format (must have @ and .)

**Dashboard crashes:**
```bash
pip install -r requirements.txt  # Reinstall dependencies
tail -f solara.log               # Check logs
```

**Import errors:**
```bash
pip install --upgrade -r requirements.txt
python -c "import PySAM; print('PySAM OK')"
```

---

## 🎓 Example Projects

### Residential Solar (5kW)
```json
{
  "pv": { "system_capacity": 5 },
  "battery": { "enabled": false },
  "rates": { "structure": "flat", "rate": 0.13 },
  "financial": { "pv_cost_per_watt": 2.50 }
}
```

### Commercial Peak Shaving (100kW + 200kWh)
See `examples/example_config.json` for complete configuration.

### Microgrid (500kW + 1MWh)
```json
{
  "pv": { "system_capacity": 500 },
  "battery": { "initial_capacity": 1000 },
  "load": { "annual_kwh": 2500000 },
  "optimization": { "dispatch_strategy": "backup_reserve" }
}
```

---

## 📚 Documentation

### Module Headers
All modules contain detailed headers with:
- Purpose and features
- Version and compatibility
- Quick start examples
- Notes and requirements

### External Resources
- **NREL Developer Portal**: https://developer.nrel.gov/
- **PySAM Documentation**: https://nrel-pysam.readthedocs.io/
- **Plotly Documentation**: https://plotly.com/python/
- **Dash Documentation**: https://dash.plotly.com/
- **NSRDB Data**: https://nsrdb.nrel.gov/

### Help Commands
```bash
python -c "import solara; help(solara)"
python solara.py --help
```

---

## 🚀 Version History

**v3.1.1** (November 4, 2025)
- ✅ Enhanced error handling in dashboard
- ✅ NREL API compliance with required email
- ✅ Improved retry logic for weather downloads
- ✅ Comprehensive test suite (11 tests)
- ✅ Example configuration included
- ✅ Updated documentation

**v3.1.0** (November 2025)
- Automated weather data download
- Advanced optimization algorithms
- Interactive dashboard
- Comprehensive visualization suite

---

## 📞 Contact & Support

### Author
**Alfonso Antonio Dávila Vera**  
- Email: davila.alfonso@gmail.com  
- LinkedIn: [https://www.linkedin.com/in/alfonso-davila-vera](https://www.linkedin.com/in/alfonso-davila-vera) 
- GitHub: [@DynMEP](https://github.com/DynMEP)

### Repository
- **URL**: https://github.com/DynMEP/solara
- **Issues**: https://github.com/DynMEP/solara/issues
- **Discussions**: https://github.com/DynMEP/solara/discussions

---

## 🙏 Acknowledgments

### Key Dependencies
- **NREL** - PySAM and NSRDB API
- **Plotly** - Interactive visualizations
- **Dash** - Web dashboard framework
- **Python Scientific Stack** - NumPy, Pandas, SciPy

### Standards & References
- NREL System Advisor Model (SAM)
- IEEE 1547-2018 (DER Interconnection)
- NFPA 70 (National Electrical Code 2023)

---

## 📄 License

MIT License - See [LICENSE](LICENSE) file for details.
Third-party attribution (NREL PySAM and SAM, both BSD-3-Clause) is recorded in [NOTICE](NOTICE).

**Free for:**
- ✅ Commercial use
- ✅ Modification
- ✅ Distribution
- ✅ Private use

**Conditions:**
- Include original license and copyright
- No warranty provided

---

## 🌟 Citation

If you use SOLARA in research or professional work, please cite:

```bibtex
@software{solara2025,
  author = {Dávila Vera, Alfonso Antonio},
  title = {SOLARA: Solar Analytics \& Revenue Advisor},
  year = {2025},
  version = {3.1.1},
  url = {https://github.com/dynmep/solara},
  license = {MIT}
}
```

GitHub citation format available via repository "Cite this repository" button.

---

## 🎯 Roadmap

### v3.2 (Planned)
- [ ] Monte Carlo uncertainty analysis
- [ ] Enhanced battery degradation modeling
- [ ] Grid services revenue stacking
- [ ] Multi-location optimization
- [ ] Advanced load forecasting

### v4.0 (Future)
- [ ] Machine learning dispatch optimization
- [ ] Real-time system monitoring
- [ ] Cloud deployment support
- [ ] API for external integrations
- [ ] Mobile dashboard

---

## ✨ Why SOLARA?

**🎯 Accuracy**
- NREL-validated PySAM simulations
- Real weather data integration
- Comprehensive financial modeling

**⚡ Performance**
- Parallel optimization support
- Efficient caching system
- Fast parametric sweeps

**🎨 Visualization**
- Interactive Plotly figures
- Real-time dashboard
- Professional reports

**🔧 Flexibility**
- Multiple optimization methods
- Customizable configurations
- Extensible architecture

**📊 Professional**
- Production-ready code
- Comprehensive testing
- Detailed documentation

---

**Thank you for using SOLARA!** ☀️

*Professional solar analytics for PV+Storage optimization*

---

**Version:** 3.1.1 | **Status:** Production Ready | **License:** MIT | **Updated:** November 04, 2025
