"""Draw the reviewed balloon contour with the active Krita brush on フキダシ.

Task-specific UI action; never injects lettering or modifies archive contents.
Requires the reviewed 1400x1000 window and 61.4% canvas zoom.
"""
import time
import win32api
from pywinauto import Desktop, mouse

window = Desktop(backend='win32').window(handle=2627462)
assert window.process_id() == 7720 and '023.kra' in window.window_text()
assert window.rectangle().left == 0 and window.rectangle().top == 0
window.set_focus()
controls = [(648,410),(720,399),(784,378),(819,335),(832,290),
            (821,247),(792,211),(744,187),(679,175),(590,170),
            (500,174),(423,194),(376,225),(353,270),(350,317),
            (373,362),(420,394),(482,412),(554,420),(611,417)]
path = []
for i in range(len(controls)-1):
    p0, p1 = controls[max(0,i-1)], controls[i]
    p2, p3 = controls[i+1], controls[min(len(controls)-1,i+2)]
    for j in range(10):
        t = j/10
        path.append(tuple(round(0.5*((2*p1[k])+(-p0[k]+p2[k])*t+
                      (2*p0[k]-5*p1[k]+4*p2[k]-p3[k])*t*t+
                      (-p0[k]+3*p1[k]-3*p2[k]+p3[k])*t*t*t))
                          for k in range(2)))
path.append(controls[-1])
for a,b in [(controls[-1],(631,473)),((631,473),controls[0])]:
    path.extend((round(a[0]+(b[0]-a[0])*j/20),
                 round(a[1]+(b[1]-a[1])*j/20)) for j in range(1,21))
mouse.press(coords=path[0])
try:
    for point in path[1:]:
        win32api.SetCursorPos(point)
        time.sleep(0.008)
finally:
    mouse.release(coords=path[-1])
