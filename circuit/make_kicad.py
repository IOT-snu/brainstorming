"""
Generates the KiCad schematic for the energy-measurement circuit (INA219 in series with an ESP32 node's
5 V supply, read over I2C by a second ESP32). Output: ina219_energy_monitor.kicad_sch and .kicad_pro.

Format: KiCad 7 (version 20230121). Opens in KiCad 7, 8 and 9. All symbols are embedded in the file, so no
libraries are needed. Symbols are simple functional blocks, not manufacturer footprints: assign real
footprints (or use your breakout boards) before making a PCB.

Run: python3 make_kicad.py
"""
import os, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
NAME = "ina219_energy_monitor"
ROOT = str(uuid.uuid4())
u = lambda: str(uuid.uuid4())
FONT = "(effects (font (size 1.27 1.27)))"


def f(x):
    return f"{x:.2f}".rstrip("0").rstrip(".") if abs(x - round(x)) > 1e-9 else str(int(round(x)))


# ---------------------------------------------------------------- embedded library symbols
def block_symbol(name, ref, half_w, half_h, pins):
    """pins: list of (number, name, side 'L'|'R', y_lib). Connection points sit 2.54 mm outside the body."""
    out = [f'    (symbol "{name}" (pin_names (offset 1.016)) (in_bom yes) (on_board yes)',
           f'      (property "Reference" "{ref}" (at 0 {f(half_h + 3.81)} 0) {FONT})',
           f'      (property "Value" "{name}" (at 0 {f(-half_h - 3.81)} 0) {FONT})',
           f'      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
           f'      (symbol "{name}_0_1"',
           f'        (rectangle (start {f(-half_w)} {f(half_h)}) (end {f(half_w)} {f(-half_h)}) (stroke (width 0.254) (type default)) (fill (type background)))',
           f'      )',
           f'      (symbol "{name}_1_1"']
    for num, pname, side, y in pins:
        x = -(half_w + 2.54) if side == "L" else (half_w + 2.54)
        ang = 0 if side == "L" else 180
        out.append(f'        (pin passive line (at {f(x)} {f(y)} {ang}) (length 2.54) (name "{pname}" {FONT}) (number "{num}" {FONT}))')
    out += ["      )", "    )"]
    return "\n".join(out)


def resistor_symbol():
    return "\n".join([
        '    (symbol "R_4k7" (pin_names (offset 0)) (in_bom yes) (on_board yes)',
        '      (property "Reference" "R" (at 3.81 0 90) ' + FONT + ')',
        '      (property "Value" "4.7k" (at -3.81 0 90) ' + FONT + ')',
        '      (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
        '      (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
        '      (symbol "R_4k7_0_1"',
        '        (rectangle (start -1.016 2.54) (end 1.016 -2.54) (stroke (width 0.254) (type default)) (fill (type none)))',
        '      )',
        '      (symbol "R_4k7_1_1"',
        '        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" ' + FONT + ') (number "1" ' + FONT + '))',
        '        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" ' + FONT + ') (number "2" ' + FONT + '))',
        '      )', '    )'])


SYMS = {
    "Supply_5V": (5.08, 5.08, [("1", "+5V", "R", 2.54), ("2", "GND", "R", -2.54)]),
    "INA219_module": (7.62, 10.16, [("1", "VIN+", "L", 7.62), ("2", "VIN-", "L", 2.54),
                                    ("3", "VCC", "R", 7.62), ("4", "SDA", "R", 2.54), ("5", "SCL", "R", -2.54), ("6", "GND", "R", -7.62)]),
    "ESP32_node_under_test": (7.62, 5.08, [("1", "VIN_5V", "L", 2.54), ("2", "GND", "L", -2.54)]),
    "ESP32_monitor": (7.62, 10.16, [("1", "3V3", "L", 7.62), ("2", "GPIO21_SDA", "L", 2.54), ("3", "GPIO22_SCL", "L", -2.54), ("4", "GND", "L", -7.62)]),
}


def pin_abs(sym, origin, pin_num):
    hw, hh, pins = SYMS[sym]
    for num, name, side, y in pins:
        if num == pin_num:
            x = -(hw + 2.54) if side == "L" else (hw + 2.54)
            return (origin[0] + x, origin[1] - y)          # schematic y runs downward
    raise KeyError(pin_num)


# ---------------------------------------------------------------- placement
INST = {}   # ref -> (symbol, origin, value)
INST["J1"] = ("Supply_5V", (45.72, 60.96), "5 V supply (USB breakout or bench)")
INST["U1"] = ("INA219_module", (101.6, 66.04), "INA219 current sensor module")
INST["U2"] = ("ESP32_node_under_test", (101.6, 91.44), "ESP32-DevKitC node under test")
INST["U3"] = ("ESP32_monitor", (152.4, 66.04), "ESP32-DevKitC monitor")
RES = {"R1": (121.92, 83.82), "R2": (129.54, 83.82)}   # 4.7k I2C pull-ups (fit only if the INA219 module has none)

elements = []   # wires, labels, junctions, text


def wire(a, b):
    elements.append(f'  (wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])})) (stroke (width 0) (type default)) (uuid "{u()}"))')


def label(text, at, justify="left bottom"):
    elements.append(f'  (label "{text}" (at {f(at[0])} {f(at[1])} 0) (fields_autoplaced) (effects (font (size 1.27 1.27)) (justify {justify})) (uuid "{u()}"))')


def junction(at):
    elements.append(f'  (junction (at {f(at[0])} {f(at[1])}) (diameter 0) (color 0 0 0 0) (uuid "{u()}"))')


def text(s, at, size=1.27):
    elements.append(f'  (text "{s}" (at {f(at[0])} {f(at[1])} 0) (effects (font (size {size} {size})) (justify left top)) (uuid "{u()}"))')


P = {  # absolute pin positions
    "J1.+5V": pin_abs("Supply_5V", INST["J1"][1], "1"), "J1.GND": pin_abs("Supply_5V", INST["J1"][1], "2"),
    "U1.VIN+": pin_abs("INA219_module", INST["U1"][1], "1"), "U1.VIN-": pin_abs("INA219_module", INST["U1"][1], "2"),
    "U1.VCC": pin_abs("INA219_module", INST["U1"][1], "3"), "U1.SDA": pin_abs("INA219_module", INST["U1"][1], "4"),
    "U1.SCL": pin_abs("INA219_module", INST["U1"][1], "5"), "U1.GND": pin_abs("INA219_module", INST["U1"][1], "6"),
    "U2.VIN": pin_abs("ESP32_node_under_test", INST["U2"][1], "1"), "U2.GND": pin_abs("ESP32_node_under_test", INST["U2"][1], "2"),
    "U3.3V3": pin_abs("ESP32_monitor", INST["U3"][1], "1"), "U3.SDA": pin_abs("ESP32_monitor", INST["U3"][1], "2"),
    "U3.SCL": pin_abs("ESP32_monitor", INST["U3"][1], "3"), "U3.GND": pin_abs("ESP32_monitor", INST["U3"][1], "4"),
}
for ref, (x, y) in RES.items():
    P[ref + ".1"] = (x, y - 3.81); P[ref + ".2"] = (x, y + 3.81)

# power path: supply +5V -> VIN+ ; VIN- -> node under test VIN
assert abs(P["J1.+5V"][1] - P["U1.VIN+"][1]) < 1e-6
wire(P["J1.+5V"], P["U1.VIN+"]); label("5V_IN", (68.58, P["J1.+5V"][1]))
wire(P["U1.VIN-"], (P["U1.VIN-"][0], P["U2.VIN"][1])); label("NODE_5V", (P["U1.VIN-"][0], 76.2))
assert abs(P["U1.VIN-"][0] - P["U2.VIN"][0]) < 1e-6
# I2C and 3V3 between the INA219 and the monitor ESP32 (pins are aligned, so straight wires)
for a, b, net in (("U1.VCC", "U3.3V3", "+3V3"), ("U1.SDA", "U3.SDA", "SDA"), ("U1.SCL", "U3.SCL", "SCL"), ("U1.GND", "U3.GND", "GND")):
    assert abs(P[a][1] - P[b][1]) < 1e-6
    wire(P[a], P[b]); label(net, ((P[a][0] + P[b][0]) / 2 - 3.81, P[a][1]))
# ground: supply GND and node GND join the GND net by label
wire(P["J1.GND"], (P["J1.GND"][0] + 5.08, P["J1.GND"][1])); label("GND", (P["J1.GND"][0] + 5.08, P["J1.GND"][1]))
wire(P["U2.GND"], (P["U2.GND"][0] - 5.08, P["U2.GND"][1])); label("GND", (P["U2.GND"][0] - 5.08, P["U2.GND"][1]), "right bottom")
# optional pull-ups
for ref, net in (("R1", "SDA"), ("R2", "SCL")):
    top, bot = P[ref + ".1"], P[ref + ".2"]
    wire(top, (top[0], top[1] - 3.81)); label("+3V3", (top[0], top[1] - 3.81))
    wire(bot, (bot[0], bot[1] + 3.81)); label(net, (bot[0], bot[1] + 3.81))

text("Energy measurement: INA219 in series with the node's 5 V supply (high side).", (25.4, 25.4), 1.8)
text("The node under test is powered ONLY through the INA219 (VIN+ to VIN-). Do not also power it from its own USB.", (25.4, 31.75))
text("R1 and R2 (4.7k I2C pull-ups to 3V3): fit only if the INA219 module has no pull-ups of its own.", (25.4, 36.83))
text("All GND pins share one net. The monitor ESP32 supplies 3V3 for the INA219 logic and reads it over I2C (GPIO21 SDA, GPIO22 SCL).", (25.4, 41.91))
text("INA219 converts about every 0.5 ms: average energy over many update cycles, do not trust single short bursts.", (25.4, 46.99))
text("Check every pin against your module's datasheet before powering it. This schematic has not been built or tested.", (25.4, 52.07))

# ---------------------------------------------------------------- assemble file
out = ['(kicad_sch (version 20230121) (generator eeschema)', '', f'  (uuid "{ROOT}")', '', '  (paper "A4")', '',
       '  (title_block', '    (title "INA219 energy measurement for an ESP32 node")', '    (date "2026-10-22")', '    (rev "A")',
       '    (company "CSD457 Group G-04")', '    (comment 1 "Proposed wiring, not yet built or tested")', '  )', '', '  (lib_symbols']
for n, (hw, hh, pins) in SYMS.items():
    ref = {"Supply_5V": "J", "INA219_module": "U", "ESP32_node_under_test": "U", "ESP32_monitor": "U"}[n]
    out.append(block_symbol(n, ref, hw, hh, [(a, b, c, d) for a, b, c, d in pins]))
out.append(resistor_symbol())
out += ['  )', '']
for ref, (sym, org, val) in INST.items():
    hw, hh, pins = SYMS[sym]
    out += [f'  (symbol (lib_id "{sym}") (at {f(org[0])} {f(org[1])} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced) (uuid "{u()}")',
            f'    (property "Reference" "{ref}" (at {f(org[0])} {f(org[1] - hh - 3.81)} 0) {FONT})',
            f'    (property "Value" "{val}" (at {f(org[0])} {f(org[1] + hh + 3.81)} 0) {FONT})',
            '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))']
    out += [f'    (pin "{p[0]}" (uuid "{u()}"))' for p in pins]
    out += [f'    (instances (project "{NAME}" (path "/{ROOT}" (reference "{ref}") (unit 1))))', '  )', '']
for ref, (x, y) in RES.items():
    out += [f'  (symbol (lib_id "R_4k7") (at {f(x)} {f(y)} 0) (unit 1) (in_bom yes) (on_board yes) (dnp no) (fields_autoplaced) (uuid "{u()}")',
            f'    (property "Reference" "{ref}" (at {f(x + 3.81)} {f(y)} 90) {FONT})',
            f'    (property "Value" "4.7k (optional)" (at {f(x - 3.81)} {f(y)} 90) {FONT})',
            '    (property "Footprint" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            '    (property "Datasheet" "" (at 0 0 0) (effects (font (size 1.27 1.27)) hide))',
            f'    (pin "1" (uuid "{u()}"))', f'    (pin "2" (uuid "{u()}"))',
            f'    (instances (project "{NAME}" (path "/{ROOT}" (reference "{ref}") (unit 1))))', '  )', '']
out += elements
out += ['', '  (sheet_instances', '    (path "/" (page "1"))', '  )', ')']
path = os.path.join(HERE, NAME + ".kicad_sch")
open(path, "w").write("\n".join(out) + "\n")
open(os.path.join(HERE, NAME + ".kicad_pro"), "w").write('{\n  "meta": {\n    "filename": "%s.kicad_pro",\n    "version": 1\n  }\n}\n' % NAME)
print("wrote", path)
