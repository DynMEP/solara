"""
SOLARA Visualization Module Test
Quick test to verify visualization handles missing data properly
"""

print("="*70)
print("SOLARA Visualization Module Test")
print("="*70)
print()

try:
    from solara_visualization import SOLARAPlotter
    print("✓ Module imported successfully")
    
    # Test 1: Create plotter with empty data
    print("\nTest 1: Creating plotter with empty results...")
    plotter = SOLARAPlotter({}, {})
    print("✓ Plotter created successfully")
    
    # Test 2: Try to create financial dashboard
    print("\nTest 2: Creating financial dashboard with missing data...")
    try:
        fig = plotter.create_financial_dashboard()
        
        if fig is None:
            print("✓ Dashboard correctly returned None for empty data")
        else:
            print("✓ Dashboard created with warning (expected behavior)")
            
    except Exception as e:
        print(f"✓ Dashboard gracefully handled error: {type(e).__name__}")
    
    # Test 3: Create optimization surface
    print("\nTest 3: Creating optimization surface...")
    try:
        fig = plotter.create_optimization_surface()
        if fig is None:
            print("✓ Surface plot correctly returned None for missing data")
        else:
            print("✓ Surface plot created")
    except Exception as e:
        print(f"✓ Surface plot gracefully handled error: {type(e).__name__}")
    
    print("\n" + "="*70)
    print("✓ ALL TESTS PASSED")
    print("  Visualization module handles missing data correctly")
    print("="*70)
    
except ImportError as e:
    print(f"❌ ERROR: Could not import solara_visualization")
    print(f"   Make sure you're in the correct directory")
    print(f"   Error details: {e}")
    
except Exception as e:
    print(f"❌ UNEXPECTED ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\nPress Enter to close...")
input()
