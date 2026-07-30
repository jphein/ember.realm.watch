// Host harness for the hearth-wyrm flame band (Lyra, 2026-07-29).
//
// Compiles the PROPOSED paint_flame body — fire + dragon — against minimal
// stubs and checks the two things that matter and that no compiler can:
//
//   1. TILING. auto_clear_enabled is false, so the framebuffer persists. Every
//      row of the flame band must be written EXACTLY once across 0..239. A gap
//      leaves permanent litter; an overlap silently doubles the write cost the
//      row-major design exists to avoid. Luna's harness asserts this for the
//      fire; the dragon composites into the same emitter, so it has to keep it.
//   2. BAND ISOLATION. Nothing may write outside y188..263.
//
// It also counts horizontal_line() calls and pixel writes per frame (the run
// count is the added-cost term I am least sure about), and dumps PPMs so the
// dragon can be judged against the REAL 60-column fire rather than a stand-in.
//
// RUN IT (from anywhere; the include is anchored to this file, not the cwd):
//
//   g++ -std=gnu++20 -O2 -Wall -Wextra -o /tmp/dh esphome/art/dragon_harness.cpp
//   /tmp/dh
//
// (Written on one line on purpose: a trailing backslash inside a // comment continues
// the comment and trips -Wcomment, so the build command would warn on the very flags
// this header tells you to use.)
//
// AND, whenever you touch array extents, loop bounds or NC/GRATE/MAXH, run it
// instrumented as well:
//
//   g++ -std=gnu++20 -O1 -g -fsanitize=address,undefined -o /tmp/dhs esphome/art/dragon_harness.cpp
//   /tmp/dhs
//
// THIS IS THE ONLY PLACE THIS CODE CAN BE INSTRUMENTED AT ALL. You cannot run ASan on
// the ESP32-S3. Because this harness is host code compiling the real paint body, the
// sanitizers apply to the actual production render loop — and that is worth more than
// the tiling check, because a stack write past an array corrupts something OUTSIDE the
// flame band, and every other check we have looks only inside it.
//
// >>> THE HOST IS MORE PROTECTIVE THAN THE DEVICE. Do not read a host pass as safety. <<<
// Worked example, NC raised 60 -> 80 (the arrays are literal [60]):
//
//   host, compile   warns  -Waggressive-loop-optimizations, no sanitizer needed
//   host, run       ABORTS  "*** stack smashing detected ***", exit 134
//   host, ASan      exact WRITE-of-size-1 trace at ch[i] = (uint8_t) hgt
//   DEVICE          SILENT. sdkconfig has CONFIG_COMPILER_STACK_CHECK_MODE_NONE=y and
//                   no -fstack-protector anywhere in the build's compile flags.
//
// Three independent signals here, zero on the target, so the asymmetry runs the wrong
// way: the thing that saves you locally is absent in the field, where the same overflow
// just quietly corrupts paint_flame's frame up to 20 times a second. Note the plain
// -Wall -Wextra build already catches this one; the sanitizer makes it precise rather
// than possible, so don't conclude you are unsafe without it.
//
// It prints, per state: runs/frame, px/frame, the dirty box, and the classify/memset/
// sqrtf/dragon-row counts, then dumps wyrm_<state>.ppm into the cwd so the result can
// be LOOKED AT rather than inferred.
//
// ---------------------------------------------------------------------------------
// WHAT THIS DOES NOT CHECK — read before trusting a pass.
//
//   * `FAIL negative-control: y=228 x=123 covered 0 times` IS EXPECTED. It is the
//     harness proving check_tiling can actually fail, and it prints on an unmodified
//     run. Do not read it as your change breaking tiling.
//
//   * check_tiling is BAND-SCOPED (y FLAM_Y .. FLAM_Y+FLAM_H-1). A change that writes
//     into the sigil, scroll or telemetry bands is not checked here at all.
//
//   * IT CANNOT CATCH AN OVER-TALL MAXH, and this is the subtle one. Fire occupies rows
//     FUSE_H .. base_row-1 where base_row = FLAM_H - GRATE. Raise MAXH past
//     base_row - FUSE_H and flames reach into the fuse — but the fuse branch
//     (`if (r < FUSE_H) { ...; continue; }`) runs BEFORE the fire logic, so the flame is
//     silently CLIPPED FLAT instead of failing. Every pixel is still covered exactly
//     once, by the fuse, so check_tiling is satisfied by the very mechanism that hides
//     the defect. Measured: with GRATE=8, MAXH=65 passes and is wrong; 64 is the
//     largest correct value. If you touch GRATE or MAXH, LOOK AT THE PPM — a flat-topped
//     tallest flame is the symptom, and no assertion in here will tell you.
//
//     Deliberately left as a documented gap rather than half-fixed: a correct assertion
//     needs GRATE/MAXH visible outside the paint body, and hoisting them would make this
//     file diverge structurally from the ESPHome lambda it mirrors, which is the whole
//     reason it is trustworthy. Worth doing properly, not quietly.
// ---------------------------------------------------------------------------------
//
// It mirrors the paint_flame body in esphome/ember-satellite.yaml. If you change one,
// change the other; the harness is only worth anything while it is the same code.

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

// ------------------------------------------------------------------- stubs ---
struct Color {
  uint8_t r{}, g{}, b{};
  Color() = default;
  Color(int r_, int g_, int b_) : r(r_), g(g_), b(b_) {}
};

static uint32_t g_millis = 0;
static uint32_t millis() { return g_millis; }

// Exact operation counters, declared before the stub that feeds them. The
// added cost is then ARITHMETIC against Luna's calibrated constants rather
// than a feeling about how expensive a loop looks.
static long n_classify = 0, n_memset = 0, n_sqrt = 0, n_row = 0;
static bool g_noop_emit = false;

struct Display {
  static const int W = 240, H = 320;
  uint8_t fb[H][W][3]{};
  int cover[H][W]{};
  int min_y = 9999, max_y = -1;
  long calls = 0, pixels = 0;

  void reset_counts() { min_y = 9999; max_y = -1; calls = 0; pixels = 0;
                        std::memset(cover, 0, sizeof(cover)); }
  int get_width() const { return W; }

  void horizontal_line(int x, int y, int w, Color c) {
    if (w <= 0) return;
    if (g_noop_emit) { calls++; pixels += w; return; }
    if (y < 0 || y >= H || x < 0 || x + w > W) {
      std::printf("  !! OFF-PANEL WRITE x=%d w=%d y=%d\n", x, w, y);
      std::abort();
    }
    calls++;
    pixels += w;
    min_y = std::min(min_y, y);
    max_y = std::max(max_y, y);
    for (int i = 0; i < w; i++) {
      cover[y][x + i]++;
      fb[y][x + i][0] = c.r; fb[y][x + i][1] = c.g; fb[y][x + i][2] = c.b;
    }
  }
  void filled_rectangle(int x, int y, int w, int h, Color c) {
    for (int i = 0; i < h; i++) horizontal_line(x, y + i, w, c);
  }
} it;

// globals the lambda reads (names/shapes match the YAML)
static int g_va_state = 0;
static float g_level_hist[120]{};
static int g_hist_idx = 0;
static float g_db_rms = -72.0f, g_db_peak = -72.0f;
static bool g_theme_light = false;
static uint32_t g_tts_est_ms = 0;
static int g_spark_col = -1;
static uint32_t g_spark_ms = 0;
static uint32_t g_frames = 0, g_frames_mark = 0;
static bool g_audio_live = false, g_guttering = false;
// Baseline switch: renders the fire EXACTLY as it ships, so the dragon's added
// run count is measured against the real thing rather than estimated.
static bool g_no_dragon = false;
static bool g_wake_reset = false;
static void wake_reset() { g_wake_reset = true; }

// ------------------------------------------------------------- the lambda ---
// Everything from here to END-OF-LAMBDA is the block that goes in the YAML,
// modulo id(...) -> g_... and the ${subst} numbers being spelled out.

static const int W_ = 240;
static const int FLAM_Y = 188, FLAM_H = 76;
static const int FUSE_H = 4;

static void paint_flame_frame() {
  const int W = it.get_width();
  const uint32_t now = millis();

  Color c_bg, c_ink, c_dim, c_ash, c_bed, c_ember, c_amber, c_gold, c_tip, c_alarm;
  if (g_theme_light) {
    c_bg = Color(0xF2, 0xE8, 0xDA); c_ink = Color(0x2A, 0x1C, 0x12);
    c_dim = Color(0x8A, 0x76, 0x62); c_ash = Color(0xD8, 0xCA, 0xB8);
    c_bed = Color(0x8C, 0x2E, 0x0A); c_ember = Color(0xB8, 0x3A, 0x0C);
    c_amber = Color(0xE0, 0x6A, 0x10); c_gold = Color(0xF0, 0xA8, 0x20);
    c_tip = Color(0xFF, 0xE0, 0x90); c_alarm = Color(0xA8, 0x14, 0x10);
  } else {
    c_bg = Color(0x0A, 0x06, 0x04); c_ink = Color(0xF2, 0xDC, 0xB8);
    c_dim = Color(0x6A, 0x52, 0x40); c_ash = Color(0x3A, 0x32, 0x2C);
    c_bed = Color(0x4A, 0x10, 0x02); c_ember = Color(0x8E, 0x22, 0x06);
    c_amber = Color(0xE0, 0x5A, 0x08); c_gold = Color(0xFF, 0xA8, 0x1E);
    c_tip = Color(0xFF, 0xE8, 0xB4); c_alarm = Color(0xFF, 0x3C, 0x18);
  }
  (void) c_ink; (void) c_dim;

  const int st = g_va_state;
  const bool guttering = g_guttering;
  const uint32_t frames = g_frames;
  const uint32_t spoken_ms = (frames - g_frames_mark) / 16u;
  float prog = 0.0f;
  if (g_tts_est_ms > 0) {
    prog = (float) spoken_ms / (float) g_tts_est_ms;
    if (prog > 0.97f) prog = 0.97f;
  }
  const float ph = (float) spoken_ms * (6.28318f / 900.0f);

  float spark_k = 0.0f;
  if (g_spark_col >= 0) {
    const uint32_t age = now - g_spark_ms;
    if (age < 500u) { const float t = 1.0f - (float) age / 500.0f; spark_k = t * t; }
  }

  auto db_to_frac = [&](float db) {
    float f = (db - -72.0f) / (-30.0f - -72.0f);
    return f < 0.0f ? 0.0f : (f > 1.0f ? 1.0f : f);
  };

  // ---- animation smoothers. These MUST be declared before paint_flame in the
  // real lambda (a lambda body cannot name a variable declared after it), which
  // is why they do not live with the scheduler statics further down. ----
  static float wake_s = 0.0f;
  static float lvl_s = 0.0f;
  if (g_wake_reset) { wake_s = 0.0f; lvl_s = 0.0f; g_wake_reset = false; }

  // =====================  THE HEARTH-WYRM  =====================
// Same directory as this file. A quoted include resolves relative to the INCLUDING
// FILE, so this works from any cwd and survives the repo being cloned anywhere. It
// previously read ../../../../../Projects/ha/esphome/art/dragon_spans.inc — a path from
// before this project was extracted out of ~/Projects/ha — so the harness did not
// compile at all from a clone. Keep it relative to the file, never to the cwd.
#include "dragon_spans.inc"

  // Geometry. DGN_X/Y/W/H MUST agree with the dgn_ substitutions the touch
  // hit-test uses, or "where it's drawn" and "where it's tappable" drift apart.
  //
  // TRAP: do NOT write a substitution token inside a comment in this block. The
  // lambda is run through ESPHome's substitution pass before it is ever C++, so
  // a dollar-brace in a COMMENT is still expanded — and a wildcard one is a
  // TemplateSyntaxError pointing at the whole 400-line lambda, which tells you
  // nothing about where it is. Cost me one confusing validation failure.
  // Three mouth shapes, indexed by `jaw`. Indexing rather than branching keeps
  // the row builder a single loop, and it is what makes the unused-variable
  // warning the check that the variants are actually wired up.
  const uint8_t *HB[3]  = {HED_B0, HED_B1, HED_B2};
  const int      HBN[3] = {HED_B0_N, HED_B1_N, HED_B2_N};
  const uint8_t *HD[3]  = {HED_D0, HED_D1, HED_D2};
  const int      HDN[3] = {HED_D0_N, HED_D1_N, HED_D2_N};
  const uint8_t *HM[3]  = {HED_M0, HED_M1, HED_M2};
  const int      HMN[3] = {HED_M0_N, HED_M1_N, HED_M2_N};
  const uint8_t *HT[3]  = {HED_T0, HED_T1, HED_T2};
  const uint8_t *HY[3]  = {HED_Y0, HED_Y1, HED_Y2};

  const int DGN_X = 60, DGN_Y = 22, DGN_W = 120, DGN_H = 50;
  const int HED_W = 28, HED_H = 19;
  const int HED_ATX = 21, HED_ATY = 13;      // neck attach, head-local
  const int HED_EYX = 8,  HED_EYY = 7;       // eye centre, head-local
  const int SHX = 29, SHY = 28;              // shoulder, dragon-local
  const int HSX = 4, HSY = 30;               // head pos asleep
  const int HAX = 0, HAY = 0;                // head pos alert
  // The "stage" is the dragon plus 16px of clear air in front of its muzzle, so
  // the breath sparks have somewhere to go. Only the dragon's own 120 columns
  // are ever occluded; the extra 24 hold sparks and nothing else.
  const int STG_X = DGN_X - 16, STG_W = DGN_W + 24;
  const int DOFF = DGN_X - STG_X;            // dragon-local x -> stage x
  // Rows at or below this are IN the coals: tall flames are drawn in FRONT of
  // the dragon there, so its feet dissolve into the fire instead of sitting on
  // a hard line. This is the one place the fire wins the depth test.
  const int SUBMERGE_R = FLAM_H - 11;

  // ---- wakefulness: one scalar, 0 asleep .. 1 alert. Everything the creature
  // does is a function of it, so there are no per-state poses to keep in sync. --
  float wake_t;
  int jaw = 0;
  switch (st) {
    case 1:
      // LISTENING leans in with your actual voice: the head height IS the
      // level, smoothed. Same principle as the fire being the waveform.
      lvl_s += 0.22f * (db_to_frac(g_db_rms) - lvl_s);
      wake_t = 0.74f + 0.26f * lvl_s;
      break;
    case 2:
      wake_t = 0.60f;            // held still — concentration reads as stillness
      break;
    case 3: {
      // SPEAKING: the head rocks and the jaw works on the SYLLABLE ENVELOPE,
      // whose phase comes from frames clocked to the DAC. The mouth cannot move
      // unless sound is genuinely leaving the speaker.
      const float syl = 0.55f + 0.45f * powf(fabsf(sinf(ph * 0.83f)), 1.6f);
      wake_t = 0.82f + 0.14f * syl;
      if (guttering) { wake_t = 0.30f; jaw = 0; }
      else jaw = (syl > 0.90f) ? 2 : (syl > 0.72f ? 1 : 0);
      break;
    }
    case 4:
      wake_t = 0.02f;            // guttered: head down in the ash
      break;
    default:
      wake_t = 0.03f;            // asleep
      break;
  }
  // The startle, on ANY touch.
  //
  // An earlier draft graded this: hard startle if the tap landed ON the wyrm, a
  // smaller stir if it landed elsewhere. Dropped deliberately. The gesture that
  // shipped is "anywhere means talk", and the whole hearth is the creature's —
  // so the whole hearth wakes it, at full strength, and the touch lambda needs
  // no dragon-specific hit test at all. One less global, ZERO lines changed in
  // the input path, and it cannot drift into a second input meaning later.
  //
  // WHERE you touched is still honoured: spark_col already flares the struck
  // coal under your finger, so the hearth answers locally and the creature
  // answers bodily. Luna's rule holds — feedback comes from what you touched.
  if (spark_k > 0.0f) {
    wake_t += 0.95f * spark_k;
    if (spark_k > 0.45f && st != 4) jaw = 1;
  }
  if (wake_t > 1.0f) wake_t = 1.0f;
  wake_s += 0.30f * (wake_t - wake_s);       // ~150ms settle at 18fps
  const float wake = wake_s;

  const int hx = (int) (HSX + (HAX - HSX) * wake + 0.5f);
  const int hy = (int) (HSY + (HAY - HSY) * wake + 0.5f);

  // ---- per-column top row (for the rim light) and who owns it ----
  static uint8_t topy[144], boty[144];
  static bool rim_hd[144];
  for (int i = 0; i < STG_W; i++) { topy[i] = 255; boty[i] = 0; rim_hd[i] = false; }
  for (int x = 0; x < DGN_W; x++) {
    topy[x + DOFF] = DGN_TOPY[x];
    boty[x + DOFF] = DGN_BOTY[x];
  }
  for (int x = 0; x < HED_W; x++) {
    const int sx = x + hx + DOFF;
    if (sx < 0 || sx >= STG_W || HT[jaw][x] == 255) continue;
    const int t = HT[jaw][x] + hy, b = HY[jaw][x] + hy;
    if (t < topy[sx] || topy[sx] == 255) { topy[sx] = (uint8_t) t; rim_hd[sx] = true; }
    if (b > boty[sx]) boty[sx] = (uint8_t) b;
  }

  // ---- the neck: a tapered capsule chain, shoulder -> skull, resolved to
  // per-row spans. Procedural rather than tabled precisely so that when the
  // head lifts the neck follows instead of tearing away from it. ----
  static uint8_t nk0[50], nk1[50];
  for (int r = 0; r < DGN_H; r++) { nk0[r] = 255; nk1[r] = 0; }
  {
    const float ax = (float) (hx + HED_ATX), ay = (float) (hy + HED_ATY);
    const float cxp = (float) SHX - 5.5f, cyp = ((float) SHY + ay) * 0.5f - 2.0f;
    for (int i = 0; i < 26; i++) {
      const float t = (float) i / 25.0f, u = 1.0f - t;
      const float cx = u * u * (float) SHX + 2.0f * u * t * cxp + t * t * ax;
      const float cy = u * u * (float) SHY + 2.0f * u * t * cyp + t * t * ay;
      const float rr = 4.6f * u + 2.9f * t;
      const int r0 = (int) (cy - rr), r1 = (int) (cy + rr);
      for (int r = r0; r <= r1; r++) {
        if (r < 0 || r >= DGN_H) continue;
        const float dv = (float) r + 0.5f - cy;
        if (fabsf(dv) > rr) continue;
        const float hw = sqrtf(rr * rr - dv * dv); n_sqrt++;
        int x0 = (int) (cx - hw), x1 = (int) (cx + hw) + 1;
        if (x0 < 0) x0 = 0;
        if (x1 > DGN_W) x1 = DGN_W;
        if (x1 <= x0) continue;
        if (x0 < nk0[r] || nk0[r] == 255) nk0[r] = (uint8_t) x0;
        if (x1 > nk1[r]) nk1[r] = (uint8_t) x1;
      }
      const int cx0 = (int) (cx - rr), cx1 = (int) (cx + rr);
      for (int x = cx0; x <= cx1; x++) {
        if (x < 0 || x >= DGN_W) continue;
        const float dh = (float) x + 0.5f - cx;
        if (fabsf(dh) > rr) continue;
        int t0 = (int) (cy - sqrtf(rr * rr - dh * dh)); n_sqrt++;
        if (t0 < 0) t0 = 0;
        if (t0 < topy[x + DOFF] || topy[x + DOFF] == 255) {
          topy[x + DOFF] = (uint8_t) t0; rim_hd[x + DOFF] = false;
        }
        int b0 = (int) (cy + sqrtf(rr * rr - dh * dh));
        if (b0 >= DGN_H) b0 = DGN_H - 1;
        if (b0 > boty[x + DOFF]) boty[x + DOFF] = (uint8_t) b0;
        n_sqrt++;
      }
    }
  }

  // ---- interior colour is a function of the ROW ONLY, which is the whole
  // reason this is cheap: the belly furnace, the travelling swallow and the
  // state temperature all resolve to one Color per row, and the pixel loop stays
  // a membership test. ----
  float glow, rimf;
  switch (st) {
    case 1:  glow = 0.80f; rimf = 0.95f; break;
    case 2:  glow = 0.95f; rimf = 0.50f; break;
    case 3:  glow = guttering ? 0.10f : 1.05f; rimf = guttering ? 0.05f : 1.00f; break;
    case 4:  glow = 0.00f; rimf = 0.00f; break;
    default: glow = 0.30f + 0.10f * (0.5f * (1.0f + sinf((float) now * 0.001047f)));
             rimf = 0.35f; break;
  }
  if (spark_k > 0.0f) { glow += 0.45f * spark_k; rimf += 0.40f * spark_k; }

  // The swallow: on each syllable a hot band runs belly -> throat -> muzzle. It
  // is just a row window, so it costs one compare per row.
  int swal_r = -99;
  if (st == 3 && !guttering) {
    const float sw = fmodf(ph * 0.159f, 1.0f);
    swal_r = (int) (40.0f - 42.0f * sw);
  } else if (st == 2) {
    swal_r = (int) (44.0f - 46.0f * fmodf((float) now * 0.00042f, 1.0f));
  }

  // k_up[h] is the interior colour h pixels ABOVE this column's own underside.
  // Light comes from the coals, so the furnace is brightest at the belly and dies
  // out toward the spine — and because it is indexed by height-above-bottom
  // rather than by absolute row, a thin leg glows like a thin leg instead of
  // inheriting whatever the belly happened to be doing at that row.
  static Color k_up[32];
  const bool err = (st == 4);
  for (int h = 0; h < 32; h++) {
    if (err) { k_up[h] = c_ash; continue; }
    float v = 1.0f - (float) h / 11.0f;
    if (v < 0.0f) v = 0.0f;
    float g = glow * v * v;
    k_up[h] = (g > 0.62f) ? c_gold : (g > 0.34f) ? c_amber
                                   : (g > 0.13f) ? c_ember : c_bed;
  }
  // The swallow rides on top of it: one hot ROW window travelling belly -> throat
  // -> muzzle, so it costs a single compare per row rather than per pixel.
  static Color k_row[50];
  static bool k_row_hot[50];
  for (int r = 0; r < DGN_H; r++) {
    k_row_hot[r] = false;
    k_row[r] = c_bg;
    if (err || swal_r <= -99) continue;
    const int d = r - swal_r;
    if (d > -3 && d < 3) {
      k_row_hot[r] = true;
      k_row[r] = (d == 0) ? c_tip : c_gold;
    }
  }
  // In ERROR the dragon and the grate are BOTH c_ash, so without a lighter top
  // edge the body merges into the grate line and loses its silhouette.
  const Color c_rim  = err ? c_dim : (rimf > 0.86f) ? c_tip
                                   : (rimf > 0.55f) ? c_gold : c_ember;
  const Color c_rimh = err ? c_dim : (rimf > 0.86f) ? c_tip
                                   : (rimf > 0.55f) ? c_tip : c_amber;
  const Color c_maw  = (rimf > 0.6f) ? c_tip : c_gold;
  const Color c_eye  = err ? c_alarm
                    : (spark_k > 0.3f || st == 1 || st == 3) ? c_tip
                    : (st == 2) ? c_gold : c_bg;   // c_bg == a shut lid

  // ---- classes. 0 is background AND the shadow gap: identical colour, so
  // sharing the class makes the runs longer instead of splitting them. ----
  enum : uint8_t { D_NONE = 0, D_GAP = 1, D_SOLID = 2, D_MAW = 3, D_EYE = 4,
                   D_SPK_H = 5, D_SPK_C = 6 };
  static uint8_t drow[144];

  // ---- fire: unchanged from the shipped design ----
  // `CW` is unused and -Wunused-variable WILL warn on it. It is identical to
  // esphome/ember-satellite.yaml:3344, so do not delete it here alone — that would
  // silence a warning by making this file diverge from the lambda it mirrors, which is
  // the only property that makes the harness worth running. Fix it in both or neither.
  //
  // >>> BUT DO NOT FILE THIS WARNING AS COSMETIC. An earlier version of this comment
  // did, and the compiler was telling the truth. <<<
  //
  // CW is unused because the column index below is `x >> 2`, which HARDCODES CW == 4.
  // The arrays are fixed `[60]` and filled `for (i < NC)`, while the read index runs
  // 0..59 for any NC. So yaml:1922's operator advice — "if audio hiccups, NC 60->40 with
  // CW 4->6" — does not do what it says: setting CW has no effect at all, and setting
  // NC=40 leaves ch/csa/csb/chot[40..59] UNINITIALISED and read every frame.
  //
  // Verified, not reasoned: built with NC=40/CW=6, the right third of the band renders
  // from stack garbage — a full-height bar, a detached rectangle, a stray rule — and this
  // harness still reports `tiling ok` and ALL CHECKS PASSED, because every pixel really
  // is written exactly once. It is written with rubbish. Same family as the MAXH clip.
  //
  // The knob is genuinely decoupled; a fix belongs in the yaml (guard CW == 4, or index
  // by `x / CW` and size the arrays by NC, and reword :1922 either way). Flagged to the
  // firmware owner rather than changed here.
  const int NC = 60, CW = 4;
  const int GRATE = 3;
  const int base_row = FLAM_H - GRATE;
  const int MAXH = FLAM_H - 8;
  // Flames rise from base_row and the tallest reaches row base_row-MAXH. Rows below
  // FUSE_H belong to the progress fuse, which is painted by an EARLIER branch that
  // `continue`s — so if MAXH is too tall the fire does not overflow, it is silently
  // CLIPPED FLAT and you get square-topped tallest flames.
  //
  // check_tiling cannot catch that: every pixel is still covered exactly once, by the
  // fuse. The invariant is satisfied by the very mechanism that hides the defect, which
  // is why this needs its own assertion rather than trusting a green run.
  //
  // static_assert rather than a runtime check, deliberately: it needs nothing hoisted out
  // of this body, so the harness stays structurally identical to the lambda in
  // ember-satellite.yaml — the only property that makes it worth running — and a
  // compile-time failure cannot be skipped, absorbed or ignored. At GRATE=3 there is one
  // row of slack (68+4 <= 73). At GRATE=8, MAXH must be <= 64.
  static_assert(MAXH + FUSE_H <= base_row,
                "MAXH is too tall for GRATE: the tallest flame reaches into the fuse "
                "rows and will be silently clipped flat. Lower MAXH or lower GRATE.");
  const float syl = 0.55f + 0.45f * powf(fabsf(sinf(ph * 0.83f)), 1.6f);
  const float breath = 0.5f * (1.0f + sinf((float) now * 0.001047f));
  const float orbit = fmodf((float) now * 0.00042f, 1.0f) * (float) NC;

  uint8_t ch[60], csa[60], csb[60];
  bool chot[60];
  for (int i = 0; i < NC; i++) {
    const float fx = (float) i;
    float f;
    if (st == 1) {
      int a = (g_hist_idx + i * 2) % 120;
      int b = (a + 1) % 120;
      f = 0.10f + 0.86f * (0.5f * (g_level_hist[a] + g_level_hist[b]));
    } else if (st == 3) {
      float w1 = 0.5f * (1.0f + sinf(0.27f * fx - ph * 2.3f));
      float w2 = 0.5f * (1.0f + sinf(0.11f * fx + ph * 1.4f + 1.7f));
      uint32_t h = ((uint32_t) i * 2654435761u) ^ (frames * 1013904223u);
      float crackle = (float) ((h >> 24) & 0xFFu) * (0.14f / 255.0f);
      f = 0.22f + 0.62f * w1 * w2 * syl + crackle;
      if (guttering) f *= 0.35f;
    } else if (st == 2) {
      float d = fabsf(fx - orbit);
      if (d > (float) NC * 0.5f) d = (float) NC - d;
      f = 0.10f + 0.72f * expf(-(d * d) / 18.0f);
    } else if (st == 4) {
      f = 0.16f;
    } else {
      float w = 0.5f * (1.0f + sinf(0.19f * fx + (float) now * 0.0004f));
      f = 0.06f + 0.16f * breath * (0.55f + 0.45f * w);
    }
    if (spark_k > 0.0f) {
      const float d = fabsf(fx - (float) g_spark_col);
      f += 0.85f * spark_k * expf(-(d * d) / 6.0f);
      f += 0.16f * spark_k;
    }
    if (f < 0.0f) f = 0.0f;
    if (f > 1.0f) f = 1.0f;
    int hgt = (int) (f * (float) MAXH);
    if (hgt < 1) hgt = 1;
    ch[i] = (uint8_t) hgt;
    csa[i] = (uint8_t) (hgt * 50 / 100);
    csb[i] = (uint8_t) (hgt * 82 / 100);
    chot[i] = (f > 0.72f);
  }

  int pk_row = -1;
  if (st == 1) {
    int pk = (int) (db_to_frac(g_db_peak) * (float) MAXH);
    if (pk > 1) pk_row = pk;
  }

  Color k_bed, k_body, k_tipg, k_tipw;
  if (st == 4)        { k_bed = c_ash; k_body = c_ash; k_tipg = c_ash; k_tipw = c_ash; }
  else if (st == 0)   { k_bed = c_bed; k_body = c_ember; k_tipg = c_amber; k_tipw = c_amber; }
  else if (guttering) { k_bed = c_ash; k_body = c_bed; k_tipg = c_ember; k_tipw = c_ember; }
  else                { k_bed = c_ember; k_body = c_amber; k_tipg = c_gold; k_tipw = c_tip; }

  // ---- pass 2: ROW-MAJOR render ----
  for (int r = 0; r < FLAM_H; r++) {
    const int y = FLAM_Y + r;

    if (r < FUSE_H) {
      if (st == 3 && g_tts_est_ms > 0) {
        int wpx = (int) (prog * (float) W);
        if (wpx > 3) {
          it.horizontal_line(0, y, wpx - 3, c_amber);
          it.horizontal_line(wpx - 3, y, 3, guttering ? c_ash : c_tip);
        } else if (wpx > 0) {
          it.horizontal_line(0, y, wpx, c_amber);
        }
        if (wpx < W) it.horizontal_line(wpx, y, W - wpx, c_ash);
      } else if (st == 4) {
        it.horizontal_line(0, y, W, c_alarm);
      } else {
        it.horizontal_line(0, y, W, c_bg);
      }
      continue;
    }
    if (r >= base_row) { it.horizontal_line(0, y, W, c_ash); continue; }

    const int hup = base_row - r;
    const int dr = r - DGN_Y;
    const bool drow_live = (dr >= 0 && dr < DGN_H) && !g_no_dragon;

    // ---- build the stage row: span memsets, in depth order. Doing it this way
    // rather than testing ~18 intervals per pixel is what keeps the added cost
    // near half a millisecond: the pixel loop below does ONE array load. ----
    if (drow_live) {
      std::memset(drow, D_NONE, (size_t) STG_W); n_memset += STG_W; n_row++;
      auto put = [&](int x0, int x1, uint8_t v) {
        if (x1 > STG_W) x1 = STG_W;
        if (x0 < 0) x0 = 0;
        if (x1 > x0) { std::memset(drow + x0, v, (size_t) (x1 - x0)); n_memset += x1 - x0; }
      };
      for (int s = 0; s < DGN_D_N; s++) {
        const int a = DGN_D[dr * DGN_D_N * 2 + s * 2], b = DGN_D[dr * DGN_D_N * 2 + s * 2 + 1];
        if (b > a) put(a + DOFF, b + DOFF, D_GAP);
      }
      const int hr = dr - hy;
      if (hr >= 0 && hr < HED_H) {
        for (int s = 0; s < HDN[jaw]; s++) {
          const int a = HD[jaw][hr * HDN[jaw] * 2 + s * 2];
          const int b = HD[jaw][hr * HDN[jaw] * 2 + s * 2 + 1];
          if (b > a) put(a + hx + DOFF, b + hx + DOFF, D_GAP);
        }
      }
      if (nk1[dr] > nk0[dr] && nk0[dr] != 255)
        put(nk0[dr] + DOFF, nk1[dr] + DOFF, D_SOLID);
      for (int s = 0; s < DGN_B_N; s++) {
        const int a = DGN_B[dr * DGN_B_N * 2 + s * 2], b = DGN_B[dr * DGN_B_N * 2 + s * 2 + 1];
        if (b > a) put(a + DOFF, b + DOFF, D_SOLID);
      }
      if (hr >= 0 && hr < HED_H) {
        for (int s = 0; s < HBN[jaw]; s++) {
          const int a = HB[jaw][hr * HBN[jaw] * 2 + s * 2];
          const int b = HB[jaw][hr * HBN[jaw] * 2 + s * 2 + 1];
          if (b > a) put(a + hx + DOFF, b + hx + DOFF, D_SOLID);
        }
        for (int s = 0; s < HMN[jaw]; s++) {
          const int a = HM[jaw][hr * HMN[jaw] * 2 + s * 2];
          const int b = HM[jaw][hr * HMN[jaw] * 2 + s * 2 + 1];
          if (b > a) put(a + hx + DOFF, b + hx + DOFF, D_MAW);
        }
        // the eye. Awake it is 3x2; asleep it is a 3x1 line in c_bg, which reads
        // as a shut lid rather than as a missing eye.
        if (hr == HED_EYY || (wake > 0.35f && hr == HED_EYY + 1))
          put(HED_EYX + hx + DOFF - 1, HED_EYX + hx + DOFF + 2, D_EYE);
      }
      // breath: three embers leaving the muzzle, phase-locked to real audio.
      if (st == 3 && !guttering) {
        for (int s = 0; s < 3; s++) {
          const float t = fmodf(ph * 0.159f + (float) s * 0.3333f, 1.0f);
          const int sx = hx + 1 + DOFF - 3 - (int) (t * 12.0f);
          const int sy = hy + 9 - (int) (t * 8.0f);
          const int sz = (t < 0.55f) ? 2 : 1;
          if (dr >= sy && dr < sy + sz)
            put(sx, sx + sz, (t < 0.40f) ? D_SPK_H : D_SPK_C);
        }
      }
    }

    // ---- one pass, left to right, coalescing runs. Exactly W px, once. ----
    int run_x = 0, run_k = -1, run_up = 0;
    int kin_up = 0;
    for (int x = 0; x <= W; x++) {
      n_classify++;
      kin_up = 0;
      int k;
      if (x == W) {
        k = -2;
      } else {
        const int i = x >> 2;
        if (hup > (int) ch[i])       k = (hup == pk_row) ? 5 : 0;
        else if (hup <= (int) csa[i]) k = 1;
        else if (hup <= (int) csb[i]) k = 2;
        else                          k = chot[i] ? 4 : 3;
        if (drow_live) {
          const unsigned sx = (unsigned) (x - STG_X);
          if (sx < (unsigned) STG_W) {
            const uint8_t d = drow[sx];
            // the coals win below the submerge line, so the feet dissolve into
            // the fire instead of standing on a hard edge
            const bool fire_here = (k >= 1 && k <= 4);
            if (d != D_NONE && !(r >= SUBMERGE_R && fire_here)) {
              switch (d) {
                case D_SOLID:
                  if (topy[sx] != 255 && dr - (int) topy[sx] < 2) {
                    k = rim_hd[sx] ? 8 : 7;          // fire-lit back edge
                  } else if (k_row_hot[dr]) {
                    k = 13;                          // the swallow passing
                  } else {
                    int up = (int) boty[sx] - dr;
                    if (up < 0) up = 0;
                    if (up > 31) up = 31;
                    k = 6;
                    kin_up = up;
                  }
                  break;
                case D_MAW:   k = 9;  break;
                case D_EYE:   k = 10; break;
                case D_SPK_H: k = 11; break;
                case D_SPK_C: k = 12; break;
                default:      k = 0;  break;   // shadow gap == background
              }
            }
          }
        }
      }
      // class 6 carries a payload (which rung of the furnace), so a change of
      // rung has to break the run as surely as a change of class does.
      if (k != run_k || (k == 6 && kin_up != run_up)) {
        if (run_k >= 0) {
          Color rc;
          switch (run_k) {
            case 1:  rc = k_bed;   break;
            case 2:  rc = k_body;  break;
            case 3:  rc = k_tipg;  break;
            case 4:  rc = k_tipw;  break;
            case 5:  rc = c_dim;   break;
            case 6:  rc = k_up[run_up]; break;
            case 7:  rc = c_rim;   break;
            case 8:  rc = c_rimh;  break;
            case 9:  rc = c_maw;   break;
            case 10: rc = c_eye;   break;
            case 11: rc = c_tip;   break;
            case 12: rc = c_amber; break;
            case 13: rc = k_row[dr]; break;
            default: rc = c_bg;    break;
          }
          it.horizontal_line(run_x, y, x - run_x, rc);
        }
        run_k = k; run_x = x; run_up = kin_up;
      }
    }
  }
}
// ------------------------------------------------------- END-OF-LAMBDA -------

// ------------------------------------------------------------------ checks ---
static int g_fail = 0;

static bool check_tiling(const char *what) {
  for (int y = FLAM_Y; y < FLAM_Y + FLAM_H; y++) {
    for (int x = 0; x < 240; x++) {
      if (it.cover[y][x] != 1) {
        std::printf("  FAIL %s: y=%d x=%d covered %d times (want exactly 1)\n",
                    what, y, x, it.cover[y][x]);
        g_fail++;
        return false;
      }
    }
  }
  if (it.min_y != FLAM_Y || it.max_y != FLAM_Y + FLAM_H - 1) {
    std::printf("  FAIL %s: dirty box y%d..%d, want y%d..%d\n", what,
                it.min_y, it.max_y, FLAM_Y, FLAM_Y + FLAM_H - 1);
    g_fail++;
    return false;
  }
  return true;
}

static void dump(const char *path, int reps) {
  FILE *f = fopen(path, "wb");
  std::fprintf(f, "P6\n%d %d\n255\n", 240, FLAM_H * reps);
  fwrite(&it.fb[FLAM_Y][0][0], 1, (size_t) 240 * FLAM_H * reps * 3, f);
  fclose(f);
}

int main() {
  struct Case { const char *name; int st; bool live, gut; int hit; };
  const Case cases[] = {
      {"idle",       0, false, false, -1},
      {"listening",  1, false, false, -1},
      // wake pinned to 1.0 and to 0.0: the head lift is the only thing that
      // moves geometry, so the band-isolation proof has to cover both ends.
      {"listen-loud",1, false, false, -1},
      {"thinking",   2, false, false, -1},
      {"speaking",   3, true,  false, -1},
      {"guttering",  3, true,  true,  -1},
      {"error",      4, false, false, -1},
      {"tap",        0, false, false,  0},
      {"daylight",   3, true,  false, -1},
  };

  for (int c = 0; c < (int) (sizeof(cases) / sizeof(cases[0])); c++) {
    const Case &k = cases[c];
    g_theme_light = (std::string(k.name) == "daylight");
    g_va_state = k.st;
    g_audio_live = k.live;
    g_guttering = k.gut;
    g_tts_est_ms = k.live ? 4200 : 0;
    g_frames_mark = 0;
    g_spark_col = (k.hit >= 0) ? (k.hit ? 30 : 5) : -1;
    for (int i = 0; i < 120; i++)
      g_level_hist[i] = 0.25f + 0.6f * fabsf(sinf((float) i * 0.21f));
    const bool loud = (std::string(k.name) == "listen-loud");
    g_db_rms = loud ? -12.0f : -40.0f;
    g_db_peak = loud ? -12.0f : -34.0f;

    long calls = 0, px = 0;
    int frames_ok = 0;
    n_classify = n_memset = n_sqrt = n_row = 0;
    // 60 frames at 50ms: enough for the head to finish settling and for the
    // syllable envelope and the breath to cycle several times.
    for (int fr = 0; fr < 60; fr++) {
      g_millis = 100000u + (uint32_t) fr * 50u;
      g_frames = k.live ? (uint32_t) fr * 800u : 0u;
      g_spark_ms = (k.hit >= 0) ? g_millis - (uint32_t) (fr % 10) * 50u : 0u;
      it.reset_counts();
      paint_flame_frame();
      if (check_tiling(k.name)) frames_ok++;
      else break;
      calls += it.calls;
      px += it.pixels;
    }
    if (frames_ok == 60) {
      std::printf("  %-11s 60 frames  tiling ok  box y%d..%d  runs/frame %4ld  px/frame %ld\n",
                  k.name, it.min_y, it.max_y, calls / 60, px / 60);
      std::printf("               per frame: classify %ld  memset %ldB  sqrtf %ld  dragon rows %ld\n",
                  n_classify / 60, n_memset / 60, n_sqrt / 60, n_row / 60);
    }
    char path[128];
    std::snprintf(path, sizeof(path), "wyrm_%s.ppm", k.name);
    dump(path, 1);

    // the same state with the dragon switched off — the honest delta
    g_no_dragon = true;
    long b_calls = 0;
    for (int fr = 0; fr < 60; fr++) {
      g_millis = 100000u + (uint32_t) fr * 50u;
      g_frames = k.live ? (uint32_t) fr * 800u : 0u;
      it.reset_counts();
      paint_flame_frame();
      b_calls += it.calls;
    }
    g_no_dragon = false;
    std::printf("               fire alone %4ld runs -> +%ld runs (+%.0f%%)\n",
                b_calls / 60, calls / 60 - b_calls / 60,
                100.0 * (double) (calls / 60 - b_calls / 60) / (double) (b_calls / 60));
  }

  // ---- motion strips. A still cannot show whether the startle reads as a
  // creature waking or as a light turning on, and that is the whole gesture. ----
  struct Strip { const char *name; int st; bool live; int hit; int step; };
  const Strip strips[] = {
      {"startle",        0, false, 0, 50},
      {"speak-cycle",    3, true, -1, 50},
  };
  for (const Strip &sp : strips) {
    g_theme_light = false; g_va_state = sp.st; g_guttering = false;
    g_tts_est_ms = sp.live ? 4200 : 0; g_frames_mark = 0;
    g_db_rms = -40.0f; g_db_peak = -34.0f;
    wake_reset();
    const int N = 10;
    static uint8_t strip[76 * 10][240][3];
    for (int fr = 0; fr < N; fr++) {
      g_millis = 200000u + (uint32_t) fr * (uint32_t) sp.step;
      g_frames = sp.live ? (uint32_t) fr * 1400u : 0u;
      if (sp.hit >= 0) { g_spark_col = 30; g_spark_ms = 200000u; }
      else { g_spark_col = -1; }
      it.reset_counts();
      paint_flame_frame();
      check_tiling(sp.name);
      std::memcpy(&strip[fr * 76][0][0], &it.fb[FLAM_Y][0][0], (size_t) 240 * 76 * 3);
    }
    char path[128];
    std::snprintf(path, sizeof(path), "wyrm_strip_%s.ppm", sp.name);
    FILE *f = fopen(path, "wb");
    std::fprintf(f, "P6\n240 %d\n255\n", 76 * N);
    fwrite(strip, 1, sizeof(uint8_t) * 240 * 76 * (size_t) N * 3, f);
    fclose(f);
    std::printf("  strip %-16s %d frames  ok\n", sp.name, N);
  }

  // A negative control on the tiling check itself: if it cannot fail, it is not
  // testing anything. Deliberately drop one pixel and confirm it is caught.
  {
    g_va_state = 1; g_guttering = false; g_theme_light = false;
    g_spark_col = -1; g_millis = 100000; g_frames = 0;
    it.reset_counts();
    paint_flame_frame();
    it.cover[FLAM_Y + 40][123] = 0;
    const int before = g_fail;
    check_tiling("negative-control");
    if (g_fail == before) {
      std::printf("  FAIL: the tiling check did not notice a missing pixel\n");
      g_fail++;
    } else {
      std::printf("  negative control  caught the hole  ok\n");
      g_fail = before;   // expected failure, not a real one
    }
  }

  std::printf(g_fail ? "\n  %d CHECK(S) FAILED\n" : "\n  ALL CHECKS PASSED\n", g_fail);
  return g_fail ? 1 : 0;
}
