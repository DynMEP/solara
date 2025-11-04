# =============================================================================
# SOLARA Advanced Optimization
# =============================================================================
# Purpose: Pluggable optimizers (Genetic/NSGA‑II, Bayesian, ML surrogate, Differential Evolution) for multi‑objective PV+Storage design.
# Version: 3.1.1
# Author: Alfonso Davila - Electrical Engineer | Power Distribution Systems | Renewable Energy Systems | Dynamo BIM
# Contact: davila.alfonso@gmail.com — www.linkedin.com/in/alfonso-davila-3a121087
# Repository: https://github.com/DynMEP/solara
# License: MIT License (see LICENSE in repository)
# Created: November 2025
# Last Updated: November 04, 2025
# Compatibility: Python 3.9+, numpy, scipy; optional: pymoo, scikit‑optimize, scikit‑learn
# Features:
#   - Genetic (NSGA‑II) multi‑objective with Pareto front
#   - Bayesian GP minimization for fast convergence
#   - Gradient Boosting surrogate with LHS sampling
#   - Differential Evolution global search
# Quick Start:
#   from solara_advanced_optimization import create_optimizer
#   opt = create_optimizer('genetic', objective_function, n_parallel=4, pop_size=20, n_gen=10)
#   results = opt.optimize()
# =============================================================================

import numpy as np
import pandas as pd
from typing import Callable, Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import logging
from abc import ABC, abstractmethod
from concurrent.futures import ProcessPoolExecutor, as_completed
import pickle
from pathlib import Path

# Advanced optimization libraries
from scipy.optimize import differential_evolution, minimize
try:
    from pymoo.algorithms.moo.nsga2 import NSGA2
    from pymoo.core.problem import Problem
    from pymoo.optimize import minimize as pymoo_minimize
    PYMOO_AVAILABLE = True
except ImportError:
    PYMOO_AVAILABLE = False
    
try:
    from skopt import gp_minimize
    from skopt.space import Real, Integer
    from skopt.utils import use_named_args
    SKOPT_AVAILABLE = True
except ImportError:
    SKOPT_AVAILABLE = False

try:
    from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import cross_val_score
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger('SOLARA.Optimization')


@dataclass
class OptimizationBounds:
    pv_capacity_min: float = 50.0  # kW
    pv_capacity_max: float = 500.0
    battery_capacity_min: float = 0.0  # kWh
    battery_capacity_max: float = 2000.0
    battery_power_min: float = 0.0  # kW
    battery_power_max: float = 500.0


@dataclass
class OptimizationObjectives:
    # Financial objectives
    npv_weight: float = 0.4  # Maximize NPV
    lcoe_weight: float = 0.3  # Minimize LCOE
    payback_weight: float = 0.1  # Minimize payback
    
    # Technical objectives
    grid_independence_weight: float = 0.1  # Maximize self-consumption
    reliability_weight: float = 0.05  # Maximize backup capability
    
    # Environmental objectives
    carbon_weight: float = 0.05  # Maximize carbon offset


class BaseOptimizer(ABC):
    
    def __init__(
        self,
        objective_function: Callable,
        bounds: OptimizationBounds,
        objectives: OptimizationObjectives,
        n_parallel: int = 4
    ):
        self.objective_function = objective_function
        self.bounds = bounds
        self.objectives = objectives
        self.n_parallel = n_parallel
        
        self.evaluation_cache = {}
        self.evaluation_history = []
        self.best_solution = None
        self.best_score = float('-inf')
        
    @abstractmethod
    def optimize(self) -> Dict[str, Any]:
        pass
    
    def _evaluate_cached(self, params: Tuple[float, ...]) -> float:
        # Create hashable key
        key = tuple(np.round(params, 4))
        
        if key in self.evaluation_cache:
            return self.evaluation_cache[key]
        
        # Evaluate
        result = self.objective_function(*params)
        score = self._calculate_weighted_score(result)
        
        # Cache and track
        self.evaluation_cache[key] = score
        self.evaluation_history.append({
            'params': params,
            'result': result,
            'score': score
        })
        
        # Update best
        if score > self.best_score:
            self.best_score = score
            self.best_solution = {'params': params, 'result': result}
        
        return score
    
    def _calculate_weighted_score(self, result: Dict) -> float:
        obj = self.objectives
        
        # Normalize metrics (0-1 scale)
        npv_normalized = result['npv_$'] / 1000000  # Assume max NPV ~$1M
        lcoe_normalized = 1 - (result['lcoe_cents_kwh'] / 20)  # Lower is better
        payback_normalized = 1 - (result.get('payback_years', 10) / 15)
        self_consumption = result.get('self_consumption_%', 50) / 100
        reliability = result.get('backup_hours', 0) / 48
        carbon = result.get('carbon_offset_tons', 0) / 500
        
        # Weighted sum
        score = (
            obj.npv_weight * max(0, npv_normalized) +
            obj.lcoe_weight * max(0, lcoe_normalized) +
            obj.payback_weight * max(0, payback_normalized) +
            obj.grid_independence_weight * self_consumption +
            obj.reliability_weight * reliability +
            obj.carbon_weight * carbon
        )
        
        return score
    
    def get_pareto_front(self) -> List[Dict]:
        if not self.evaluation_history:
            return []
        
        # For multi-objective, find non-dominated solutions
        solutions = []
        for eval in self.evaluation_history:
            result = eval['result']
            solutions.append({
                'params': eval['params'],
                'npv': result['npv_$'],
                'lcoe': result['lcoe_cents_kwh'],
                'payback': result.get('payback_years', float('inf')),
                'self_consumption': result.get('self_consumption_%', 0)
            })
        
        # Simple Pareto front (maximize NPV, minimize LCOE)
        pareto = []
        for i, sol_i in enumerate(solutions):
            dominated = False
            for j, sol_j in enumerate(solutions):
                if i != j:
                    if (sol_j['npv'] >= sol_i['npv'] and 
                        sol_j['lcoe'] <= sol_i['lcoe'] and
                        (sol_j['npv'] > sol_i['npv'] or sol_j['lcoe'] < sol_i['lcoe'])):
                        dominated = True
                        break
            
            if not dominated:
                pareto.append(sol_i)
        
        return sorted(pareto, key=lambda x: x['npv'], reverse=True)


class GeneticAlgorithmOptimizer(BaseOptimizer):
    
    def __init__(self, *args, pop_size: int = 20, n_gen: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.pop_size = pop_size
        self.n_gen = n_gen
        
        if not PYMOO_AVAILABLE:
            raise ImportError("pymoo required. Install: pip install pymoo")
    
    def optimize(self) -> Dict[str, Any]:
        logger.info(f"Starting GA optimization (pop={self.pop_size}, gen={self.n_gen})...")
        
        # Define pymoo problem
        class SOLARAProblem(Problem):
            def __init__(self, optimizer_instance):
                self.opt = optimizer_instance
                super().__init__(
                    n_var=3,  # PV capacity, battery capacity, battery power
                    n_obj=2,  # NPV (maximize), LCOE (minimize)
                    n_constr=0,
                    xl=np.array([
                        self.opt.bounds.pv_capacity_min,
                        self.opt.bounds.battery_capacity_min,
                        self.opt.bounds.battery_power_min
                    ]),
                    xu=np.array([
                        self.opt.bounds.pv_capacity_max,
                        self.opt.bounds.battery_capacity_max,
                        self.opt.bounds.battery_power_max
                    ])
                )
            
            def _evaluate(self, X, out, *args, **kwargs):
                # Evaluate population
                f1 = []  # NPV (to maximize, so negate for minimization framework)
                f2 = []  # LCOE (to minimize)
                
                for x in X:
                    result = self.opt.objective_function(*x)
                    f1.append(-result['npv_$'])  # Negate for minimization
                    f2.append(result['lcoe_cents_kwh'])
                
                out["F"] = np.column_stack([f1, f2])
        
        problem = SOLARAProblem(self)
        
        algorithm = NSGA2(
            pop_size=self.pop_size,
            eliminate_duplicates=True
        )
        
        res = pymoo_minimize(
            problem,
            algorithm,
            ('n_gen', self.n_gen),
            seed=1,
            verbose=False
        )
        
        # Extract best solutions from Pareto front
        pareto_front = []
        for i in range(len(res.X)):
            params = res.X[i]
            result = self.objective_function(*params)
            pareto_front.append({
                'params': params,
                'npv': result['npv_$'],
                'lcoe': result['lcoe_cents_kwh'],
                'payback': result.get('payback_years'),
                'result': result
            })
        
        # Select best based on weighted score
        best = max(pareto_front, key=lambda x: self._calculate_weighted_score(x['result']))
        
        logger.info(f"✓ GA complete: {len(self.evaluation_history)} evaluations")
        logger.info(f"  Best NPV: ${best['npv']:,.0f}")
        logger.info(f"  Best LCOE: {best['lcoe']:.2f} ¢/kWh")
        logger.info(f"  Pareto solutions: {len(pareto_front)}")
        
        return {
            'best_solution': best,
            'pareto_front': pareto_front,
            'n_evaluations': len(self.evaluation_history),
            'algorithm': 'genetic_algorithm'
        }


class BayesianOptimizer(BaseOptimizer):
    
    def __init__(self, *args, n_calls: int = 25, n_initial: int = 10, **kwargs):
        super().__init__(*args, **kwargs)
        self.n_calls = n_calls
        self.n_initial = n_initial
        
        if not SKOPT_AVAILABLE:
            raise ImportError("scikit-optimize required. Install: pip install scikit-optimize")
    
    def optimize(self) -> Dict[str, Any]:
        logger.info(f"Starting Bayesian optimization ({self.n_calls} evaluations)...")
        
        # Define search space
        space = [
            Real(self.bounds.pv_capacity_min, self.bounds.pv_capacity_max, name='pv_capacity'),
            Real(self.bounds.battery_capacity_min, self.bounds.battery_capacity_max, name='battery_capacity'),
            Real(self.bounds.battery_power_min, self.bounds.battery_power_max, name='battery_power')
        ]
        
        # Objective wrapper (Bayesian minimizes, so negate score)
        @use_named_args(space)
        def objective(**params):
            score = -self._evaluate_cached(tuple(params.values()))
            return score
        
        # Run optimization
        result = gp_minimize(
            objective,
            space,
            n_calls=self.n_calls,
            n_initial_points=self.n_initial,
            random_state=42,
            verbose=False
        )
        
        # Extract best
        best_params = result.x
        best_result = self.objective_function(*best_params)
        
        logger.info(f"✓ Bayesian optimization complete")
        logger.info(f"  Best NPV: ${best_result['npv_$']:,.0f}")
        logger.info(f"  Best LCOE: {best_result['lcoe_cents_kwh']:.2f} ¢/kWh")
        logger.info(f"  Total evaluations: {len(result.func_vals)}")
        
        return {
            'best_solution': {
                'params': best_params,
                'result': best_result
            },
            'convergence_curve': result.func_vals,
            'n_evaluations': len(result.func_vals),
            'algorithm': 'bayesian'
        }


class MachineLearningOptimizer(BaseOptimizer):
    
    def __init__(
        self, 
        *args, 
        n_training_samples: int = 50,
        n_refinement: int = 10,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.n_training_samples = n_training_samples
        self.n_refinement = n_refinement
        
        if not SKLEARN_AVAILABLE:
            raise ImportError("scikit-learn required. Install: pip install scikit-learn")
    
    def optimize(self) -> Dict[str, Any]:
        logger.info(f"Starting ML surrogate optimization...")
        logger.info(f"  Training samples: {self.n_training_samples}")
        logger.info(f"  Refinement evaluations: {self.n_refinement}")
        
        # Phase 1: Generate training data using Latin Hypercube Sampling
        from scipy.stats.qmc import LatinHypercube
        
        sampler = LatinHypercube(d=3, seed=42)
        samples = sampler.random(n=self.n_training_samples)
        
        # Scale to bounds
        bounds_array = np.array([
            [self.bounds.pv_capacity_min, self.bounds.pv_capacity_max],
            [self.bounds.battery_capacity_min, self.bounds.battery_capacity_max],
            [self.bounds.battery_power_min, self.bounds.battery_power_max]
        ])
        
        X_train = samples * (bounds_array[:, 1] - bounds_array[:, 0]) + bounds_array[:, 0]
        
        logger.info(f"  Evaluating {self.n_training_samples} training points...")
        
        # Parallel evaluation
        y_train = []
        with ProcessPoolExecutor(max_workers=self.n_parallel) as executor:
            futures = {executor.submit(self._evaluate_cached, tuple(x)): x for x in X_train}
            
            for i, future in enumerate(as_completed(futures), 1):
                if i % 10 == 0:
                    logger.info(f"    Progress: {i}/{self.n_training_samples}")
                y_train.append(future.result())
        
        y_train = np.array(y_train)
        
        # Phase 2: Train surrogate models
        logger.info("  Training surrogate model...")
        
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        
        # Use ensemble for robustness
        model = GradientBoostingRegressor(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            random_state=42
        )
        model.fit(X_train_scaled, y_train)
        
        # Evaluate model quality
        cv_score = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
        logger.info(f"  Surrogate R² score: {cv_score.mean():.3f} ± {cv_score.std():.3f}")
        
        # Phase 3: Find promising regions using surrogate
        logger.info("  Searching for optimal region with surrogate...")
        
        # Generate large prediction set
        n_predict = 10000
        samples_predict = sampler.random(n=n_predict)
        X_predict = samples_predict * (bounds_array[:, 1] - bounds_array[:, 0]) + bounds_array[:, 0]
        X_predict_scaled = scaler.transform(X_predict)
        
        y_predict = model.predict(X_predict_scaled)
        
        # Select top candidates
        top_indices = np.argsort(y_predict)[-self.n_refinement:]
        candidates = X_predict[top_indices]
        
        # Phase 4: Refine with actual evaluations
        logger.info(f"  Refining with {self.n_refinement} actual evaluations...")
        
        refinement_results = []
        for i, candidate in enumerate(candidates, 1):
            result = self.objective_function(*candidate)
            score = self._calculate_weighted_score(result)
            refinement_results.append({
                'params': candidate,
                'result': result,
                'score': score
            })
            logger.info(f"    Refinement {i}/{self.n_refinement}: NPV=${result['npv_$']:,.0f}")
        
        # Find best
        best = max(refinement_results, key=lambda x: x['score'])
        
        total_evals = self.n_training_samples + self.n_refinement
        
        logger.info(f"✓ ML surrogate optimization complete")
        logger.info(f"  Best NPV: ${best['result']['npv_$']:,.0f}")
        logger.info(f"  Best LCOE: {best['result']['lcoe_cents_kwh']:.2f} ¢/kWh")
        logger.info(f"  Total evaluations: {total_evals}")
        logger.info(f"  Surrogate accuracy: R²={cv_score.mean():.3f}")
        
        return {
            'best_solution': best,
            'surrogate_model': model,
            'surrogate_scaler': scaler,
            'surrogate_r2': cv_score.mean(),
            'training_data': {'X': X_train, 'y': y_train},
            'refinement_results': refinement_results,
            'n_evaluations': total_evals,
            'algorithm': 'machine_learning'
        }


class DifferentialEvolutionOptimizer(BaseOptimizer):
    
    def __init__(self, *args, maxiter: int = 20, popsize: int = 15, **kwargs):
        super().__init__(*args, **kwargs)
        self.maxiter = maxiter
        self.popsize = popsize
    
    def optimize(self) -> Dict[str, Any]:
        logger.info(f"Starting Differential Evolution (maxiter={self.maxiter})...")
        
        bounds = [
            (self.bounds.pv_capacity_min, self.bounds.pv_capacity_max),
            (self.bounds.battery_capacity_min, self.bounds.battery_capacity_max),
            (self.bounds.battery_power_min, self.bounds.battery_power_max)
        ]
        
        # Objective wrapper (DE minimizes, so negate score)
        def objective(x):
            return -self._evaluate_cached(tuple(x))
        
        # Run optimization
        result = differential_evolution(
            objective,
            bounds,
            strategy='best1bin',
            maxiter=self.maxiter,
            popsize=self.popsize,
            atol=1e-3,
            tol=0.01,
            seed=42,
            workers=self.n_parallel if self.n_parallel > 1 else 1,
            updating='deferred' if self.n_parallel > 1 else 'immediate',
            disp=False
        )
        
        # Extract best
        best_params = result.x
        best_result = self.objective_function(*best_params)
        
        logger.info(f"✓ Differential Evolution complete")
        logger.info(f"  Best NPV: ${best_result['npv_$']:,.0f}")
        logger.info(f"  Best LCOE: {best_result['lcoe_cents_kwh']:.2f} ¢/kWh")
        logger.info(f"  Total evaluations: {result.nfev}")
        logger.info(f"  Convergence: {'Success' if result.success else 'Max iterations'}")
        
        return {
            'best_solution': {
                'params': best_params,
                'result': best_result
            },
            'convergence': result.success,
            'n_evaluations': result.nfev,
            'algorithm': 'differential_evolution'
        }


# ============================================================================
# Integration with SOLARA
# ============================================================================

def create_optimizer(
    algorithm: str,
    objective_function: Callable,
    bounds: Optional[OptimizationBounds] = None,
    objectives: Optional[OptimizationObjectives] = None,
    **kwargs
) -> BaseOptimizer:
    bounds = bounds or OptimizationBounds()
    objectives = objectives or OptimizationObjectives()
    
    optimizers = {
        'genetic': GeneticAlgorithmOptimizer,
        'bayesian': BayesianOptimizer,
        'ml_surrogate': MachineLearningOptimizer,
        'differential_evolution': DifferentialEvolutionOptimizer
    }
    
    if algorithm not in optimizers:
        raise ValueError(f"Unknown algorithm: {algorithm}. Choose from {list(optimizers.keys())}")
    
    optimizer_class = optimizers[algorithm]
    return optimizer_class(objective_function, bounds, objectives, **kwargs)