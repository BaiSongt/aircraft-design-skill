
import sys
import os

# Add project root to path
sys.path.insert(0, os.getcwd())

try:
    from aircraft_design.geometry_detailed import naca4_coordinates
    print("Imported naca4_coordinates successfully")
    
    # Test with code argument
    print("Testing naca4_coordinates(code='0012')...")
    af_obj = naca4_coordinates(code="0012")
    
    if hasattr(af_obj, "coordinates"):
        xs = af_obj.coordinates.x
        ys = af_obj.coordinates.y
        points = [[float(x), float(y)] for x, y in zip(xs, ys)]
        print(f"Generated {len(points)} points")
        if len(points) < 10:
            print("ERROR: Too few points!")
        else:
            print("SUCCESS: Points generation looks good.")
            print(f"First point: {points[0]}")
    else:
        print("ERROR: Result object has no 'coordinates' attribute")
        print(f"Type: {type(af_obj)}")

except Exception as e:
    print(f"EXCEPTION: {e}")
    import traceback
    traceback.print_exc()
