import openvsp as vsp

vsp.ClearVSPModel()

vsp.SetDefaultUnits( vsp.VSP_UNITS_SI )

fuse_id = vsp.AddGeom('FUSELAGE')
vsp.SetParmVal(fuse_id, 'Length', 'Design', 9.0)
vsp.SetParmVal(fuse_id, 'Diameter', 'Design', 1.5)
vsp.SetParmVal(fuse_id, 'X_Location', 'XForm', 0.0)
vsp.SetParmVal(fuse_id, 'Y_Location', 'XForm', 0.0)
vsp.SetParmVal(fuse_id, 'Z_Location', 'XForm', 0.0)

wing_id = vsp.AddGeom('WING')
vsp.SetParmVal(wing_id, 'Span', 'XSec_1', 17.053127163920692)
vsp.SetParmVal(wing_id, 'Root_Chord', 'XSec_1', 2.7672417304536623)
vsp.SetParmVal(wing_id, 'Tip_Chord', 'XSec_1', 1.245258778704148)
vsp.SetParmVal(wing_id, 'Sweep', 'XSec_1', 0.0)
vsp.SetParmVal(wing_id, 'ThickChord', 'XSec_1', 0.12)
vsp.SetParmVal(wing_id, 'X_Location', 'XForm', 0.4)
vsp.SetParmVal(wing_id, 'Y_Location', 'XForm', 0.0)
vsp.SetParmVal(wing_id, 'Z_Location', 'XForm', 0.0)
vsp.SetParmVal(wing_id, 'Y_Rotation', 'XForm', 2.0)

tail_id = vsp.AddGeom('WING')
vsp.SetParmVal(tail_id, 'Span', 'XSec_1', 7.998625640392665)
vsp.SetParmVal(tail_id, 'Root_Chord', 'XSec_1', 1.2979514223760917)
vsp.SetParmVal(tail_id, 'Tip_Chord', 'XSec_1', 0.5840781400692413)
vsp.SetParmVal(tail_id, 'Sweep', 'XSec_1', 0.0)
vsp.SetParmVal(tail_id, 'ThickChord', 'XSec_1', 0.12)
vsp.SetParmVal(tail_id, 'X_Location', 'XForm', 4.2)
vsp.SetParmVal(tail_id, 'Y_Location', 'XForm', 0.0)
vsp.SetParmVal(tail_id, 'Z_Location', 'XForm', 2.5696056097454467)
vsp.SetParmVal(tail_id, 'Y_Rotation', 'XForm', 0.0)

vsp.Update()

vsp.WriteVSPFile('generated.vsp3')
