import cadquery as cq
result = cq.Workplane("XY").box(40, 30, 10)
cq.exporters.export(result, '/scripts/test_box.stl')  # <-- absolute path inside container, shows up on your host
