# =============================================================================
# SOLARA Visualization
# =============================================================================
# Purpose: Plotly‑based interactive dashboards and figures for optimization results and PySAM‑derived cashflows and hourly profiles.
# Version: 3.1.1
# Author: Alfonso Davila - Electrical Engineer | Power Distribution Systems | Renewable Energy Systems | Dynamo BIM
# Contact: davila.alfonso@gmail.com — www.linkedin.com/in/alfonso-davila-3a121087
# Repository: https://github.com/DynMEP/solara
# License: MIT License (see LICENSE in repository)
# Created: November 2025
# Last Updated: November 04, 2025
# Compatibility: Python 3.9+, plotly, pandas, numpy
# Features:
#   - 3D optimization surface & Pareto front
#   - Financial dashboard (NPV, cashflow, ROI)
#   - Energy‑flow Sankey (est.) and hourly profile
#   - Auto‑generated plot index page
# Quick Start:
#   from solara_visualization import SOLARAPlotter
#   plotter = SOLARAPlotter(results, config)
#   plotter.save_all_plots('results/plots')
# =============================================================================

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger('SOLARA.Visualization')


class SOLARAPlotter:
    
    def __init__(self, results: Dict, config: Dict):
        self.results = results
        self.config = config
        self.theme = {
            'primary': '#FF6B35',  # Solar orange
            'secondary': '#004E89',  # Deep blue
            'success': '#00A896',  # Teal
            'warning': '#F77F00',  # Amber
            'background': '#F8F9FA'
        }
    
    def create_optimization_surface(self) -> Optional[go.Figure]:
        if 'parametric' not in self.results:
            logger.warning("No parametric results available for surface plot")
            return None
        
        try:
            df = pd.DataFrame(self.results['parametric'])
            
            # Validate required columns
            required = ['pv_capacity_kw', 'battery_capacity_kwh', 'npv_$']
            missing = [col for col in required if col not in df.columns]
            if missing:
                logger.error(f"Missing columns for surface plot: {missing}")
                return None
            
            # Create pivot for surface
            pivot = df.pivot_table(
                index='pv_capacity_kw',
                columns='battery_capacity_kwh',
                values='npv_$',
                aggfunc='mean'
            )
            
            fig = go.Figure(data=[go.Surface(
                z=pivot.values,
                x=pivot.columns,
                y=pivot.index,
                colorscale='Viridis',
                hovertemplate='<b>NPV: $%{z:,.0f}</b><br>' +
                             'Battery: %{x:.0f} kWh<br>' +
                             'PV: %{y:.0f} kW<br>' +
                             '<extra></extra>'
            )])
            
            fig.update_layout(
                title='Optimization Landscape: NPV vs System Size',
                scene=dict(
                    xaxis_title='Battery Capacity (kWh)',
                    yaxis_title='PV Capacity (kW)',
                    zaxis_title='NPV ($)',
                    camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
                ),
                height=600,
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create optimization surface: {e}")
            return None
    
    def create_pareto_front(self, pareto_solutions: List[Dict]) -> Optional[go.Figure]:
        if not pareto_solutions:
            logger.warning("No Pareto solutions provided")
            return None
        
        try:
            df = pd.DataFrame(pareto_solutions)
            
            fig = go.Figure()
            
            # Pareto frontier
            fig.add_trace(go.Scatter(
                x=df['lcoe'],
                y=df['npv'],
                mode='markers+lines',
                marker=dict(
                    size=15,
                    color=df.get('self_consumption', df['npv']),  
                    colorscale='RdYlGn',
                    showscale=True,
                    colorbar=dict(title='Self-Consumption %'),
                    line=dict(color='white', width=2)
                ),
                hovertemplate='<b>Pareto Optimal Solution</b><br>' +
                             'NPV: $%{y:,.0f}<br>' +
                             'LCOE: %{x:.2f} ¢/kWh<br>' +
                             '<extra></extra>',
                name='Pareto Front'
            ))
            
            fig.update_layout(
                title='Multi-Objective Trade-off: NPV vs LCOE',
                xaxis_title='Levelized Cost of Energy (¢/kWh)',
                yaxis_title='Net Present Value ($)',
                hovermode='closest',
                height=500,
                template='plotly_white'
            )
            
            # Add annotations for key points
            best_npv = df.loc[df['npv'].idxmax()]
            best_lcoe = df.loc[df['lcoe'].idxmin()]
            
            fig.add_annotation(
                x=best_lcoe['lcoe'],
                y=best_lcoe['npv'],
                text='Lowest LCOE',
                showarrow=True,
                arrowhead=2
            )
            
            fig.add_annotation(
                x=best_npv['lcoe'],
                y=best_npv['npv'],
                text='Highest NPV',
                showarrow=True,
                arrowhead=2
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create Pareto front: {e}")
            return None
    
    def create_financial_dashboard(self) -> Optional[go.Figure]:
        opt = self.results.get('optimal', {})
        
        if not opt:
            logger.warning("No optimal results available for financial dashboard")
            return None
        
        # Check if we have real financial data from PySAM
        has_real_data = all(key in opt for key in ['cf_annual_costs', 'cf_energy_value'])
        
        if not has_real_data:
            logger.warning("⚠ Real financial data not available - showing limited dashboard")
            logger.warning("To get full financial dashboard, ensure PySAM financial model outputs are extracted")
            return self._create_limited_financial_dashboard(opt)
        
        try:
            # Create subplots
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=(
                    'NPV Breakdown',
                    'Cash Flow Over Time (REAL DATA)',
                    'Cost Composition',
                    'ROI Metrics'
                ),
                specs=[
                    [{'type': 'indicator'}, {'type': 'scatter'}],
                    [{'type': 'pie'}, {'type': 'bar'}]
                ]
            )
            
            # 1. NPV Indicator
            fig.add_trace(go.Indicator(
                mode='number+delta',
                value=opt['npv_$'],
                title={'text': 'Net Present Value'},
                delta={'reference': 0, 'relative': False},
                number={'prefix': '$', 'valueformat': ',.0f'},
                domain={'x': [0, 1], 'y': [0, 1]}
            ), row=1, col=1)
            
            # 2. REAL Cash Flow from PySAM
            cf_costs = np.array(opt['cf_annual_costs'])
            cf_value = np.array(opt['cf_energy_value'])
            annual_net_cf = cf_value - cf_costs
            
            years = np.arange(1, len(annual_net_cf) + 1)
            cumulative_cf = np.cumsum(annual_net_cf)
            
            fig.add_trace(go.Scatter(
                x=years,
                y=cumulative_cf,
                fill='tozeroy',
                name='Cumulative Cash Flow (Real)',
                line=dict(color=self.theme['success'], width=3),
                hovertemplate='Year: %{x}<br>Cumulative CF: $%{y:,.0f}<extra></extra>'
            ), row=1, col=2)
            
            # Add payback line if available
            if opt.get('payback_years') and opt['payback_years'] > 0:
                payback_year = int(opt['payback_years'])
                if payback_year < len(years):
                    fig.add_vline(
                        x=payback_year, 
                        line_dash="dash", 
                        line_color="red",
                        annotation_text=f"Payback: {payback_year}yr",
                        row=1, col=2
                    )
            
            # 3. Cost Composition (use real data if available)
            total_cost = opt.get('total_installed_cost', 0)
            pv_capacity_kw = opt.get('pv_capacity_kw', 100)
            batt_capacity_kwh = opt.get('battery_capacity_kwh', 0)
            
            # Estimate cost breakdown (more accurate than before)
            pv_cost = pv_capacity_kw * 1000 * self.config.get('financial', {}).get('pv_cost_per_watt', 1.5)
            batt_cost = batt_capacity_kwh * self.config.get('financial', {}).get('battery_cost_per_kwh', 400) if batt_capacity_kwh > 0 else 0
            install_cost = (pv_cost + batt_cost) * 0.15  # Typical 15% installation
            soft_costs = total_cost - pv_cost - batt_cost - install_cost if total_cost > 0 else (pv_cost + batt_cost) * 0.20
            
            costs = {
                'PV System': pv_cost,
                'Battery': batt_cost,
                'Installation': install_cost,
                'Soft Costs': max(soft_costs, 0)
            }
            
            # Filter out zero costs
            costs = {k: v for k, v in costs.items() if v > 0}
            
            fig.add_trace(go.Pie(
                labels=list(costs.keys()),
                values=list(costs.values()),
                hole=0.4,
                marker=dict(colors=[self.theme['primary'], self.theme['secondary'], 
                                    self.theme['success'], self.theme['warning']][:len(costs)])
            ), row=2, col=1)
            
            # 4. ROI Metrics (REAL DATA)
            metrics = []
            values = []
            
            if 'irr_%' in opt and opt['irr_%'] > 0:
                metrics.append('IRR')
                values.append(opt['irr_%'])
            
            if 'payback_years' in opt and opt['payback_years']:
                metrics.append('Payback')
                values.append(opt['payback_years'])
            
            if 'lcoe_cents_kwh' in opt:
                metrics.append('LCOE')
                values.append(opt['lcoe_cents_kwh'])
            
            if metrics:
                fig.add_trace(go.Bar(
                    x=metrics,
                    y=values,
                    marker=dict(color=[self.theme['success'], self.theme['primary'], 
                                      self.theme['secondary']][:len(metrics)]),
                    text=[f"{v:.1f}%" if m == 'IRR' else f"{v:.1f}" for m, v in zip(metrics, values)],
                    textposition='auto',
                    hovertemplate='%{x}: %{text}<extra></extra>'
                ), row=2, col=2)
            
            fig.update_layout(
                height=800,
                showlegend=False,
                template='plotly_white',
                title_text='Financial Performance Dashboard (Real PySAM Data)'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create financial dashboard: {e}")
            return self._create_error_figure(f"Dashboard Error: {str(e)}")
    
    def _create_limited_financial_dashboard(self, opt: Dict) -> go.Figure:
        fig = go.Figure()
        
        fig.add_annotation(
            text="⚠ LIMITED DATA AVAILABLE<br><br>" +
                 "Full financial dashboard requires PySAM cash flow outputs.<br>" +
                 "Showing available metrics only.<br><br>" +
                 f"NPV: ${opt.get('npv_$', 0):,.0f}<br>" +
                 f"LCOE: {opt.get('lcoe_cents_kwh', 0):.2f} ¢/kWh<br>" +
                 f"IRR: {opt.get('irr_%', 0):.1f}%<br>" +
                 f"Payback: {opt.get('payback_years', 'N/A')} years",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color=self.theme['warning']),
            align='center',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor=self.theme['warning'],
            borderwidth=2,
            borderpad=20
        )
        
        fig.update_layout(
            title='Financial Dashboard - Limited Data Mode',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    def _create_error_figure(self, message: str) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ {message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='red')
        )
        fig.update_layout(height=400, template='plotly_white')
        return fig
    
    def create_energy_flow_sankey(self) -> Optional[go.Figure]:
        try:
            opt = self.results.get('optimal', {})
            if not opt:
                return None
            
            # Use real annual generation if available
            pv_generation = opt.get('pv_annual_kwh', 300000)
            
            to_load = pv_generation * 0.7
            to_battery = pv_generation * 0.2
            to_grid = pv_generation * 0.1
            from_battery = to_battery * 0.85  
            from_grid = 100000  
            
            fig = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color='black', width=0.5),
                    label=['PV Generation', 'Battery Charge', 'Battery Discharge', 
                           'Load', 'Grid Export', 'Grid Import'],
                    color=[self.theme['warning'], self.theme['secondary'], self.theme['success'],
                           self.theme['primary'], 'lightgray', 'lightgray']
                ),
                link=dict(
                    source=[0, 0, 0, 1, 5],  # Source nodes
                    target=[3, 1, 4, 2, 3],  # Target nodes
                    value=[to_load, to_battery, to_grid, from_battery, from_grid],
                    color=['rgba(255,107,53,0.3)', 'rgba(0,78,137,0.3)', 
                           'rgba(128,128,128,0.2)', 'rgba(0,168,150,0.3)',
                           'rgba(128,128,128,0.2)']
                )
            )])
            
            fig.update_layout(
                title='Annual Energy Flow (Estimated)',
                font=dict(size=12),
                height=500
            )
            
            fig.add_annotation(
                text="Note: Flows estimated from annual data. For accurate hourly flows, hourly simulation required.",
                xref="paper", yref="paper",
                x=0.5, y=-0.1,
                showarrow=False,
                font=dict(size=10, color='gray')
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create Sankey diagram: {e}")
            return None
    
    def create_hourly_profile(self, day_index: int = 180) -> Optional[go.Figure]:
        # Check if hourly data available
        if 'hourly_pv' not in self.results and 'hourly_gen' not in self.results:
            logger.warning("⚠ Real hourly data not available")
            logger.warning("To get real hourly profiles, extract gen, load, and batt outputs from PySAM")
            return self._create_hourly_demo_notice()
        
        try:
            hours = np.arange(24)
            day_start = day_index * 24
            day_end = day_start + 24
            
            # Extract REAL hourly data from PySAM outputs
            if 'hourly_pv' in self.results:
                pv_gen = np.array(self.results['hourly_pv'][day_start:day_end])
            else:
                pv_gen = np.array(self.results.get('hourly_gen', [0]*24)[day_start:day_end])
            
            if 'hourly_load' in self.results:
                load = np.array(self.results['hourly_load'][day_start:day_end])
            else:
                load = np.zeros(24)  # If no load data
            
            if 'hourly_batt_soc' in self.results:
                battery_soc = np.array(self.results['hourly_batt_soc'][day_start:day_end])
            else:
                battery_soc = None
            
            # Validate data length
            if len(pv_gen) != 24:
                logger.warning(f"Hourly data length mismatch: {len(pv_gen)} hours")
                return self._create_hourly_demo_notice()
            
            fig = make_subplots(
                rows=2 if battery_soc is not None else 1, 
                cols=1,
                shared_xaxes=True,
                subplot_titles=('Power Flow (Real Data)', 'Battery State of Charge') if battery_soc is not None else ('Power Flow (Real Data)',),
                vertical_spacing=0.1
            )
            
            # Power flows
            fig.add_trace(go.Scatter(
                x=hours, y=pv_gen,
                name='PV Generation',
                fill='tozeroy',
                line=dict(color=self.theme['warning'], width=2),
                hovertemplate='Hour: %{x}<br>PV: %{y:.1f} kW<extra></extra>'
            ), row=1, col=1)
            
            if np.sum(load) > 0:  # Only show if load data exists
                fig.add_trace(go.Scatter(
                    x=hours, y=load,
                    name='Load',
                    line=dict(color=self.theme['primary'], width=2, dash='dash'),
                    hovertemplate='Hour: %{x}<br>Load: %{y:.1f} kW<extra></extra>'
                ), row=1, col=1)
            
            # Battery SOC (if available)
            if battery_soc is not None and len(battery_soc) == 24:
                fig.add_trace(go.Scatter(
                    x=hours, y=battery_soc,
                    name='Battery SOC',
                    fill='tozeroy',
                    line=dict(color=self.theme['success'], width=3),
                    hovertemplate='Hour: %{x}<br>SOC: %{y:.1f}%<extra></extra>'
                ), row=2, col=1)
                
                # Add SOC limits
                fig.add_hline(y=90, line_dash='dot', line_color='red', 
                             annotation_text='Max SOC', row=2, col=1)
                fig.add_hline(y=10, line_dash='dot', line_color='red',
                             annotation_text='Min SOC', row=2, col=1)
                
                fig.update_yaxes(title_text='SOC (%)', row=2, col=1)
                fig.update_xaxes(title_text='Hour of Day', row=2, col=1)
            else:
                fig.update_xaxes(title_text='Hour of Day', row=1, col=1)
            
            fig.update_yaxes(title_text='Power (kW)', row=1, col=1)
            
            # Calculate day of year date
            from datetime import datetime, timedelta
            date = datetime(2024, 1, 1) + timedelta(days=day_index)
            
            fig.update_layout(
                title=f'Hourly Energy Profile - {date.strftime("%B %d, %Y")} (Day {day_index+1}) - REAL DATA',
                height=600,
                hovermode='x unified',
                template='plotly_white'
            )
            
            return fig
            
        except Exception as e:
            logger.error(f"Failed to create hourly profile: {e}")
            return self._create_hourly_demo_notice()
    
    def _create_hourly_demo_notice(self) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text="⚠ HOURLY DATA UNAVAILABLE<br><br>" +
                 "To view real hourly profiles, PySAM hourly outputs must be extracted.<br><br>" +
                 "Required data:<br>" +
                 "• hourly_pv or hourly_gen (PV generation)<br>" +
                 "• hourly_load (load profile)<br>" +
                 "• hourly_batt_soc (battery state of charge)<br><br>" +
                 "Add these to results dictionary during extraction.",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=14, color=self.theme['warning']),
            align='center',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor=self.theme['warning'],
            borderwidth=2,
            borderpad=20
        )
        
        fig.update_layout(
            title='Hourly Energy Profile - Data Not Available',
            height=600,
            template='plotly_white'
        )
        
        return fig
    
    def save_all_plots(self, output_dir: str = 'results/plots'):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("Generating interactive plots...")
        
        plots = {
            'optimization_surface': self.create_optimization_surface(),
            'financial_dashboard': self.create_financial_dashboard(),
            'energy_flow': self.create_energy_flow_sankey(),
            'hourly_profile': self.create_hourly_profile()
        }
        
        # Save as HTML
        for name, fig in plots.items():
            if fig:
                html_file = output_path / f'{name}.html'
                fig.write_html(str(html_file))
                logger.info(f"  ✓ Saved: {html_file}")
            else:
                logger.warning(f"  ⚠ Skipped {name} (no data available)")
        
        # Create index page
        available_plots = [name for name, fig in plots.items() if fig is not None]
        if available_plots:
            self._create_plot_index(output_path, available_plots)
        
        logger.info(f"✓ All available plots saved to: {output_dir}")
    
    def _create_plot_index(self, output_dir: Path, plot_names: List[str]):
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>SOLARA Results Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #f8f9fa; }
                h1 { color: #FF6B35; }
                .plot-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
                .plot-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .plot-card a { color: #004E89; text-decoration: none; font-size: 18px; font-weight: bold; }
                .plot-card a:hover { color: #FF6B35; }
                .notice { background: #fff3cd; border: 1px solid #ffc107; padding: 15px; margin: 20px 0; border-radius: 5px; }
            </style>
        </head>
        <body>
            <h1>☀️ SOLARA Results Dashboard</h1>
            <p>Interactive visualization of solar+storage optimization results</p>
            <div class="notice">
                <strong>v3.1.1 Update:</strong> Now uses REAL data from PySAM outputs instead of simulated data.
                If you see limited data warnings, ensure PySAM financial and hourly outputs are being extracted.
            </div>
            <div class="plot-grid">
        """
        
        for plot in plot_names:
            title = plot.replace('_', ' ').title()
            html += f"""
                <div class="plot-card">
                    <a href="{plot}.html">📊 {title}</a>
                    <p>Click to view interactive plot</p>
                </div>
            """
        
        html += """
            </div>
        </body>
        </html>
        """
        
        index_file = output_dir / 'index.html'
        with open(index_file, 'w') as f:
            f.write(html)
        
        logger.info(f"  ✓ Created index: {index_file}")