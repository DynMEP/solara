# =============================================================================
# SOLARA Web Dashboard
# =============================================================================
# Purpose: Dash/Plotly real‑time UI for optimization progress, results, scenarios, and sensitivity with defensive error handling.
# Version: 3.1.1
# Author: Alfonso Davila - Electrical Engineer | Power Distribution Systems | Renewable Energy Systems | Dynamo BIM
# Contact: davila.alfonso@gmail.com — www.linkedin.com/in/alfonso-davila-3a121087
# Repository: https://github.com/DynMEP/solara
# License: MIT License (see LICENSE in repository)
# Created: November 2025
# Last Updated: November 04, 2025
# Compatibility: Python 3.9+, dash, dash‑bootstrap‑components, plotly
# Features:
#   - Convergence & status live updates
#   - Optimal config & results views
#   - Scenario comparison & sensitivity
#   - Helper figures for info/error states
# Quick Start:
#   from solara_dashboard import SOLARADashboard
#   dashboard = SOLARADashboard(optimizer)
#   dashboard.run_in_background(port=8050)
# =============================================================================

import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from threading import Thread
import numpy as np
import logging
from typing import Dict, List, Optional

logger = logging.getLogger('SOLARA.Dashboard')


class SOLARADashboard:
    
    def __init__(self, optimizer_instance):
        self.optimizer = optimizer_instance
        self.app = dash.Dash(
            __name__,
            external_stylesheets=[dbc.themes.BOOTSTRAP],
            title='SOLARA Dashboard'
        )
        self.setup_layout()
        self.setup_callbacks()
    
    def setup_layout(self):
        
        self.app.layout = dbc.Container([
            # Header
            dbc.Row([
                dbc.Col([
                    html.H1('☀️ SOLARA Dashboard', className='text-primary'),
                    html.P('Solar Analytics & Revenue Advisor', className='lead')
                ])
            ], className='mb-4 mt-4'),
            
            # Navigation tabs
            dbc.Tabs([
                # Tab 1: Real-time Optimization
                dbc.Tab(label='Optimization Progress', children=[
                    dbc.Row([
                        dbc.Col([
                            html.H3('Optimization Status'),
                            html.Div(id='optimization-status'),
                            dcc.Graph(id='convergence-plot'),
                            dcc.Interval(id='interval-component', interval=2000, n_intervals=0)
                        ])
                    ])
                ]),
                
                # Tab 2: Results Explorer
                dbc.Tab(label='Results', children=[
                    dbc.Row([
                        dbc.Col([
                            html.H3('Optimal Configuration'),
                            html.Div(id='optimal-config')
                        ], width=4),
                        dbc.Col([
                            dcc.Graph(id='results-plot')
                        ], width=8)
                    ])
                ]),
                
                # Tab 3: Scenario Comparison
                dbc.Tab(label='Scenarios', children=[
                    dbc.Row([
                        dbc.Col([
                            html.H3('Compare Scenarios'),
                            # Scenario selection
                            dbc.Label('Select Scenarios:'),
                            dcc.Dropdown(
                                id='scenario-selector',
                                options=[],
                                multi=True
                            ),
                            dcc.Graph(id='scenario-comparison')
                        ])
                    ])
                ]),
                
                # Tab 4: Sensitivity Analysis
                dbc.Tab(label='Sensitivity', children=[
                    dbc.Row([
                        dbc.Col([
                            html.H3('Parameter Sensitivity'),
                            dcc.Graph(id='sensitivity-plot')
                        ])
                    ])
                ])
            ])
        ], fluid=True)
    
    def setup_callbacks(self):
        
        @self.app.callback(
            [Output('optimization-status', 'children'),
             Output('convergence-plot', 'figure')],
            Input('interval-component', 'n_intervals')
        )
        def update_optimization_progress(n):
            
            try:
                if not hasattr(self.optimizer, 'evaluation_history'):
                    status = self._create_info_status(
                        '⏳ Waiting for optimization to start...',
                        'info'
                    )
                    return status, self._create_empty_figure()
                
                try:
                    history = self.optimizer.evaluation_history
                except AttributeError as e:
                    logger.warning(f"Cannot access evaluation_history: {e}")
                    return self._create_error_display(
                        "Optimization data unavailable",
                        "The optimizer doesn't expose evaluation history"
                    )
                
                if not history or len(history) == 0:
                    status = self._create_info_status(
                        '⏳ No evaluations yet...',
                        'warning'
                    )
                    return status, self._create_empty_figure()
                
                try:
                    n_evals = len(history)
                    
                    # Safely extract scores
                    scores = []
                    for h in history:
                        if isinstance(h, dict):
                            scores.append(h.get('score', 0))
                        else:
                            logger.warning(f"Unexpected history entry type: {type(h)}")
                            scores.append(0)
                    
                    if scores:
                        best_score = max(scores)
                    else:
                        best_score = 0
                        
                except (KeyError, ValueError, TypeError) as e:
                    logger.error(f"Error calculating metrics: {e}")
                    best_score = 0
                    n_evals = len(history) if history else 0
                
                try:
                    status = html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.H5(f'{n_evals}'),
                                html.P('Evaluations')
                            ], width=4),
                            dbc.Col([
                                html.H5(f'{best_score:.3f}'),
                                html.P('Best Score')
                            ], width=4),
                            dbc.Col([
                                html.H5('Running' if n_evals < 100 else 'Complete'),
                                html.P('Status')
                            ], width=4)
                        ])
                    ])
                except Exception as e:
                    logger.error(f"Error creating status display: {e}")
                    status = self._create_info_status(
                        f'{n_evals} evaluations completed',
                        'info'
                    )
                
                try:
                    # Ensure we have valid scores
                    if not scores or all(s == 0 for s in scores):
                        raise ValueError("No valid scores to plot")
                    
                    best_so_far = np.maximum.accumulate(scores)
                    
                    fig = go.Figure()
                    
                    # Add scatter points
                    fig.add_trace(go.Scatter(
                        y=scores,
                        name='Score',
                        mode='markers',
                        marker=dict(size=8, color='lightblue', opacity=0.6),
                        hovertemplate='Evaluation %{x}<br>Score: %{y:.4f}<extra></extra>'
                    ))
                    
                    # Add best-so-far line
                    fig.add_trace(go.Scatter(
                        y=best_so_far,
                        name='Best So Far',
                        mode='lines',
                        line=dict(color='red', width=3),
                        hovertemplate='Best: %{y:.4f}<extra></extra>'
                    ))
                    
                    fig.update_layout(
                        title='Optimization Convergence',
                        xaxis_title='Evaluation Number',
                        yaxis_title='Objective Score',
                        height=400,
                        hovermode='x unified',
                        template='plotly_white'
                    )
                    
                except ValueError as e:
                    logger.warning(f"Cannot create convergence plot: {e}")
                    fig = self._create_info_figure(
                        "⏳ Waiting for valid scores..."
                    )
                    
                except Exception as e:
                    logger.error(f"Error creating convergence plot: {e}", exc_info=True)
                    fig = self._create_error_figure(
                        f"Plotting error: {str(e)}"
                    )
                
                return status, fig
                
            except Exception as e:
                logger.error(f"Dashboard update failed: {e}", exc_info=True)
                
                error_status = html.Div([
                    dbc.Alert([
                        html.H5("⚠ Dashboard Error"),
                        html.P(f"Unexpected error: {str(e)}"),
                        html.P("Check logs for details.", className='mb-0')
                    ], color='danger')
                ])
                
                error_fig = self._create_error_figure(
                    "Dashboard temporarily unavailable"
                )
                
                return error_status, error_fig
    
    
    def _create_error_display(self, title: str, message: str):
        status = html.Div([
            dbc.Alert([
                html.H5(f"⚠ {title}"),
                html.P(message, className='mb-0')
            ], color='danger')
        ])
        
        return status, self._create_empty_figure()
    
    def _create_info_status(self, message: str, color: str = 'info'):
        return html.Div([
            dbc.Alert(message, color=color)
        ])
    
    def _create_empty_figure(self) -> go.Figure:
        fig = go.Figure()
        fig.update_layout(
            height=400,
            template='plotly_white',
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        return fig
    
    def _create_info_figure(self, message: str) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='#0066cc'),
            align='center'
        )
        fig.update_layout(
            height=400,
            template='plotly_white',
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        return fig
    
    def _create_error_figure(self, message: str) -> go.Figure:
        fig = go.Figure()
        fig.add_annotation(
            text=f"❌ {message}",
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16, color='red'),
            align='center'
        )
        fig.update_layout(
            height=400,
            template='plotly_white',
            xaxis={'visible': False},
            yaxis={'visible': False}
        )
        return fig
    
    
    def run(self, port: int = 8050, debug: bool = False, host: str = '127.0.0.1'):
        logger.info("="*60)
        logger.info(f"✓ Starting SOLARA dashboard")
        logger.info(f"  URL: http://{host}:{port}")
        logger.info(f"  Debug mode: {debug}")
        logger.info("  Press Ctrl+C to stop")
        logger.info("="*60)
        
        try:
            self.app.run_server(
                host=host,
                port=port, 
                debug=debug,
                use_reloader=False  
            )
        except Exception as e:
            logger.error(f"❌ Dashboard failed to start: {e}")
            raise
    
    def run_in_background(self, port: int = 8050, daemon: bool = True):
        thread = Thread(
            target=self.run, 
            args=(port,), 
            daemon=daemon,
            name='SOLARA-Dashboard'
        )
        thread.start()
        
        logger.info(f"✓ Dashboard running in background on port {port}")
        logger.info(f"  Access at: http://localhost:{port}")
        
        return thread


# ============================================================================
# Usage example with error handling
# ============================================================================

def launch_dashboard_with_optimization(optimizer):
    try:
        # Create and launch dashboard
        dashboard = SOLARADashboard(optimizer)
        dashboard_thread = dashboard.run_in_background()
        
        logger.info("✓ Dashboard launched successfully")
        
        # Run optimization (dashboard will update in real-time)
        logger.info("⏳ Starting optimization...")
        results = optimizer.run_advanced_optimization('genetic')
        
        logger.info("✓ Optimization complete")
        
        # Keep dashboard running for viewing results
        logger.info("Dashboard still running. Press Ctrl+C to exit.")
        
        return results
        
    except KeyboardInterrupt:
        logger.info("⚠ User interrupted")
        return None
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        raise


# ============================================================================
# Testing utilities
# ============================================================================

class MockOptimizer:
    
    def __init__(self, n_evals: int = 50):
        # Simulate optimization progress
        self.evaluation_history = []
        best = 0
        
        for i in range(n_evals):
            # Simulate improving scores with some noise
            score = best + np.random.exponential(0.1) + np.random.normal(0, 0.05)
            if score > best:
                best = score
            
            self.evaluation_history.append({
                'score': score,
                'iteration': i,
                'params': {'pv_scale': np.random.uniform(0.5, 2.0)}
            })


def test_dashboard():
    print("Testing SOLARA Dashboard with mock data...")
    print("="*60)
    
    # Create mock optimizer
    mock_opt = MockOptimizer(n_evals=100)
    
    # Create dashboard
    dashboard = SOLARADashboard(mock_opt)
    
    print("✓ Dashboard created successfully")
    print("  Launching on http://localhost:8050")
    print("  Press Ctrl+C to stop")
    
    try:
        dashboard.run(debug=False)
    except KeyboardInterrupt:
        print("\n✓ Dashboard stopped")


if __name__ == "__main__":
    test_dashboard()