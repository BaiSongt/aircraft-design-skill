
import sys
import os
from typing import Optional, Any

# VSP Path
VSP_PATH = "/Users/baisongtao/mycode/aircraft-design-skill/OpenVSP-3.47.0-MacOS/python/openvsp"

class OpenVSPInterface:
    """
    Singleton interface for OpenVSP.
    Handles path injection and safe importing.
    """
    _instance = None
    _vsp = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenVSPInterface, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        if VSP_PATH not in sys.path:
            sys.path.append(VSP_PATH)
            
        try:
            import openvsp as vsp
            self._vsp = vsp
            # print("OpenVSP loaded successfully.")
        except ImportError as e:
            # print(f"Warning: Could not import OpenVSP: {e}")
            self._vsp = None
        except Exception as e:
             # print(f"Warning: Error loading OpenVSP: {e}")
             self._vsp = None

    @property
    def vsp(self):
        return self._vsp
        
    def is_available(self) -> bool:
        return self._vsp is not None
        
    def clear_model(self):
        if self.is_available():
            try:
                self._vsp.ClearVSPModel()
            except Exception as e:
                print(f"VSP Error: {e}")

    def add_fuselage(self, length: float, diameter: float, x: float = 0, y: float = 0, z: float = 0) -> str:
        if not self.is_available(): return ""
        try:
            fid = self._vsp.AddGeom("FUSELAGE")
            self._vsp.SetParmVal(fid, "Length", "Design", length)
            self._vsp.SetParmVal(fid, "Diameter", "Design", diameter)
            self._vsp.SetParmVal(fid, "X_Location", "XForm", x)
            self._vsp.SetParmVal(fid, "Y_Location", "XForm", y)
            self._vsp.SetParmVal(fid, "Z_Location", "XForm", z)
            return fid
        except Exception as e:
            print(f"VSP Error: {e}")
            return ""

    def add_wing(self, area: float, span: float, x: float = 0) -> str:
        if not self.is_available(): return ""
        try:
            wid = self._vsp.AddGeom("WING")
            self._vsp.SetParmVal(wid, "TotalArea", "WingGeom", area)
            self._vsp.SetParmVal(wid, "TotalSpan", "WingGeom", span)
            self._vsp.SetParmVal(wid, "X_Location", "XForm", x)
            return wid
        except Exception as e:
            print(f"VSP Error: {e}")
            return ""
            
    def export_file(self, filename: str):
        if not self.is_available(): return
        try:
            self._vsp.WriteVSPFile(filename)
        except Exception as e:
            print(f"VSP Error: {e}")
