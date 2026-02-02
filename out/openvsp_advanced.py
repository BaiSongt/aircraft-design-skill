import openvsp as vsp

vsp.ClearVSPModel()
vsp.SetDefaultUnits( vsp.VSP_UNITS_SI )

fuse_id = vsp.AddGeom('FUSELAGE')
vsp.SetParmVal(fuse_id, 'Length', 'Design', 12.0)
vsp.SetParmVal(fuse_id, 'Diameter', 'Design', 2.611227140254746)
vsp.SetParmVal(fuse_id, 'X_Location', 'XForm', 0.0)

wing_id = vsp.AddGeom('WING')
vsp.SetParmVal(wing_id, 'Span', 'XSec_1', 12.0)
vsp.SetParmVal(wing_id, 'Root_Chord', 'XSec_1', 2.6666666666666665)
vsp.SetParmVal(wing_id, 'Tip_Chord', 'XSec_1', 1.3333333333333333)
vsp.SetParmVal(wing_id, 'Sweep', 'XSec_1', 15.0)
vsp.SetParmVal(wing_id, 'ThickChord', 'XSec_1', 0.12)
vsp.SetParmVal(wing_id, 'X_Location', 'XForm', 4.5)
vsp.SetParmVal(wing_id, 'Y_Location', 'XForm', 0)
vsp.SetParmVal(wing_id, 'Z_Location', 'XForm', 0)
vsp.SetParmVal(wing_id, 'Y_Rotation', 'XForm', 0)

vsp.Update()

vsp.WriteVSPFile('generated.vsp3')