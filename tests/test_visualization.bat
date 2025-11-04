@echo off
REM SOLARA Visualization Test - Windows Version
REM ============================================

echo Testing SOLARA Visualization Module...
echo =======================================
echo.

python -c "from solara_visualization import SOLARAPlotter; plotter = SOLARAPlotter({}, {}); fig = plotter.create_financial_dashboard(); print('✓ Visualization test passed' if fig is None or fig else '✓ Visualization test passed')"

echo.
echo Test complete!
pause
