#!/usr/bin/env python3
"""Figures for the Tapstone shrine apron. LOOK AT THE OUTPUT.

Two views, because the two things that can be wrong here are not visible in the same picture:
the pad/LED face from above, and the apron sitting against the stand from the front-side, which
is the only view that shows whether the arms embrace and the cable leaves where it should.
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ENC = os.path.normpath(os.path.join(HERE, ".."))
sys.path.insert(0, ENC); sys.path.insert(0, HERE)

import render_util as R
import shrine as S
import ember_case as E

def main():
    apron = S.apron()
    R.render(R.tris(apron), os.path.join(ENC, "preview-shrine-apron.png"),
             tilt=58.0, yaw=8.0, ppm=9.0)
    print("preview-shrine-apron.png  — plan-ish view: pad, lip, scallop, LED channel")

    # The assembly. desk_stand() is imported READ-ONLY and never exported from here.
    both = apron + E.desk_stand()
    R.render(R.tris(both), os.path.join(ENC, "preview-shrine-assembly.png"),
             tilt=26.0, yaw=30.0, ppm=8.0)
    print("preview-shrine-assembly.png — apron against the stand, arms and cable exit")

if __name__ == "__main__":
    main()
