
import sys
import os

# Path found: /Users/baisongtao/mycode/aircraft-design-skill/OpenVSP-3.47.0-MacOS/python/openvsp
vsp_path = "/Users/baisongtao/mycode/aircraft-design-skill/OpenVSP-3.47.0-MacOS/python/openvsp"
sys.path.append(vsp_path)

try:
    import openvsp as vsp
    print("OpenVSP imported successfully!")
    vsp.ClearVSPModel()
    print("VSP ClearVSPModel called.")
except ImportError as e:
    print(f"Failed to import openvsp: {e}")
except Exception as e:
    print(f"Error calling VSP: {e}")
