# Vendor documents — Hosyond / lcdwiki ES3C28P

`ES3C28P_Schematic.pdf` — the board schematic, fetched 2026-08-01 from
https://www.lcdwiki.com/res/ES3C28P/2.8inch_ESP32-S3_Display_Schematic.pdf
(source page: https://www.lcdwiki.com/2.8inch_ESP32-S3_Display — also hosts the
spec, user manual, size drawings, and the 3D STEP this repo's clearance check uses).

What it settled the day it was fetched (#44's electrical questions):

- **Battery block = TP4054 (U2, PROG R12 3.3K → ~290 mA) + SL2305 P-FET (Q3) power
  path + B5819W Schottky (D8) + 200K/200K ADC divider (R14/R15 → BAT_ADC).**
- **NO protection IC. None.** The 2-pin BAT connector (JP1) goes straight to the cell.
  Over-discharge floor is only the ME6217 LDO's dropout (device browns out ~3.4 V cell),
  after which the divider (~9 µA) and quiescent currents keep draining. An external 1S
  protection strip is required with bare cells — JP fits one (#44).
- **Power path is real**: plugged in, the system rail runs from VBUS and the full charge
  current goes to the cell; running never eats the charge allotment.
- Amp is SC8002B (3 W class-AB), codec ES8311, mic LMA2718B381, LDOs ME6217C33 ×2.
