#!/usr/bin/env python3
"""
Quick script to check if reportlab is properly installed and working.
"""

print("Checking reportlab installation...")
print("=" * 60)

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Table
    from reportlab.lib.enums import TA_CENTER
    
    print("✓ reportlab is installed and all modules imported successfully!")
    print("\nImported modules:")
    print("  - reportlab.lib.pagesizes")
    print("  - reportlab.lib.styles")
    print("  - reportlab.lib.units")
    print("  - reportlab.lib.colors")
    print("  - reportlab.platypus")
    print("  - reportlab.lib.enums")
    
    # Try to get version
    try:
        import reportlab
        print(f"\nreportlab version: {reportlab.Version}")
    except:
        print("\nreportlab version: Unknown")
    
    print("\n" + "=" * 60)
    print("STATUS: ✓ reportlab is ready to use!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Restart your backend server (important!)")
    print("2. Generate a new PDF report")
    print("3. The report should now be created as .pdf instead of .txt")
    
except ImportError as e:
    print(f"✗ reportlab import failed: {e}")
    print("\nTo fix this, run:")
    print("  pip install reportlab==4.2.5")
    print("\nThen run this script again to verify.")
    exit(1)
