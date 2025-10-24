# ladder_calculator.py — Ladder Entries Calculator (Helvetica, crisp UI)
# Inputs: Direction, Market, Zone Upper/Lower, ATR (4H)
# Optional: ADX(14), RSI trigger (20/50), MACD(1h), SL buffer×ATR, TP×ATR
# Logic: L0 at market; ladder count from zone/ATR with ADX; spacing 0.5×ATR + MACD nudge; clip to zone.

import streamlit as st

# ---------------- Page setup ----------------
st.set_page_config(page_title="Ladder Entries Calculator", page_icon="🪜", layout="centered")

# ---------------- Global style (Helvetica + subtle cards) ----------------
st.markdown("""
<style>
* { font-family: 'Helvetica', sans-serif !important; }
.stMetric, .stAlert { font-weight: 600 !important; }
.card { border: 1px solid rgba(255,255,255,0.12); border-radius: 16px; padding: 16px; }
.badge { display:inline-block; padding:6px 10px; border-radius:999px;
         border:1px solid rgba(255,255,255,0.14); margin-right:8px; font-size:0.9rem; }
.valbox { border-radius: 12px; padding: 10px 12px; text-align:center; font-weight:700; }
.val-red   { background: #3b1d1d; color:#ff6b6b; }
.val-green { background: #1d3b1d; color:#66ff91; }
.val-blue  { background: #1d263b; color:#7bb5ff; }
.small { opacity:.85; font-size:.92rem; }
</style>
""", unsafe_allow_html=True)

# ---------------- Defaults ----------------
DEC = 4
BASE_STEP_MULT = 0.5         # 0.5 × ATR base spacing
NUDGE_MULT = 0.25            # MACD nudge size (±0.25 × ATR)
TP_DEFAULT = 2.0
SLBUF_DEFAULT = 0.8

st.title("🪜 Ladder Entries Calculator")
st.caption("1st at market • ATR-based spacing • Zone-aware • ADX & MACD aware")

# ---------------- Inputs (no form → no 'press enter' hint) ----------------
row1 = st.columns(4)
with row1[0]:
    side = st.radio("Direction", ["Long", "Short"], horizontal=True)
with row1[1]:
    market = st.number_input("Market price", min_value=0.0, format="%.4f", key="mkt")
with row1[2]:
    zone_upper = st.number_input("Zone Upper (ZU)", min_value=0.0, format="%.4f", key="zu")
with row1[3]:
    zone_lower = st.number_input("Zone Lower (ZL)", min_value=0.0, format="%.4f", key="zl")

row2 = st.columns(4)
with row2[0]:
    atr = st.number_input("ATR (4H, 14)", min_value=0.0, format="%.4f", key="atr")
with row2[1]:
    adx = st.number_input("ADX (4H, 14) (optional)", min_value=0.0, format="%.2f", value=0.0, step=0.5)
with row2[2]:
    rsi_trigger = st.selectbox("RSI-3 trigger (optional)", ["None", "Crossed 20↑", "Crossed 50↑"])
with row2[3]:
    macd = st.selectbox("1h MACD", ["Neutral", "Bullish", "Bearish"])

row3 = st.columns(2)
with row3[0]:
    sl_buf = st.number_input("SL buffer × ATR", min_value=0.0, value=SLBUF_DEFAULT, step=0.1, format="%.2f")
with row3[1]:
    tp_mult = st.number_input("TP × ATR", min_value=0.0, value=TP_DEFAULT, step=0.1, format="%.2f")

calc = st.button("Calculate ladders")

# ---------------- Core helpers ----------------
def ladder_count(zone_w: float, atr_val: float, adx_val: float) -> int:
    if atr_val <= 0: return 2
    k = zone_w / atr_val
    base = 2 if k < 1.2 else 3
    if adx_val >= 25:
        base = max(2, base - 1)  # strong trend → fewer rungs (min 2)
    return base, k

def macd_nudged_step(side: str, base_step: float, macd_state: str) -> float:
    # Long: Bullish → closer (smaller step), Bearish → deeper (bigger step)
    # Short: Bearish → closer, Bullish → deeper
    if macd_state == "Neutral": 
        return base_step
    if side == "Long":
        return max(0.0, base_step - NUDGE_MULT*atr) if macd_state == "Bullish" else (base_step + NUDGE_MULT*atr)
    else:
        return max(0.0, base_step - NUDGE_MULT*atr) if macd_state == "Bearish" else (base_step + NUDGE_MULT*atr)

def clamp(x, lo, hi):  # keep inside [lo, hi]
    return max(lo, min(hi, x))

def deltas_from_market(px: float, mkt: float, side: str):
    d = abs(px - mkt)
    pct = (d / mkt * 100) if mkt > 0 else 0.0
    # direction label relative to market
    if side == "Long":
        dirlabel = "below" if px < mkt else "above"
    else:
        dirlabel = "above" if px > mkt else "below"
    return d, pct, dirlabel

# ---------------- Compute ----------------
if calc:
    # Validate basics
    if market <= 0 or atr <= 0 or zone_upper <= 0 or zone_lower <= 0:
        st.error("Please enter positive numbers for **Market**, **ATR**, **Zone Upper**, and **Zone Lower**.")
        st.stop()
    if zone_lower >= zone_upper:
        st.error("**Zone Lower** must be less than **Zone Upper**.")
        st.stop()

    zone_w = zone_upper - zone_lower
    ladders, k = ladder_count(zone_w, atr, adx)
    base_step = BASE_STEP_MULT * atr
    step = macd_nudged_step(side, base_step, macd)

    # Build ladders
    L = [market]  # L0 always at market
    if side == "Long":
        # ladders descend into zone
        L1 = clamp(market - step, zone_lower, zone_upper)
        L.append(L1)
        if ladders == 3:
            L2 = clamp(L1 - step, zone_lower, zone_upper)
            L.append(L2)
    else:  # Short
        # ladders ascend into zone
        L1 = clamp(market + step, zone_lower, zone_upper)
        L.append(L1)
        if ladders == 3:
            L2 = clamp(L1 + step, zone_lower, zone_upper)
            L.append(L2)

    # SL/TP
    if side == "Long":
        sl = zone_lower - sl_buf*atr
        tp = market + tp_mult*atr
    else:
        sl = zone_upper + sl_buf*atr
        tp = market - tp_mult*atr

    # ---------------- Results ----------------
    st.markdown("### Results")

    # Ladders table
    cols = st.columns(len(L))
    for i, px in enumerate(L):
        d, pct, where = deltas_from_market(px, market, side)
        title = "L0 (Market)" if i == 0 else f"L{i}"
        with cols[i]:
            st.markdown(f"**{title}**")
            st.markdown(f"<div class='valbox val-blue'>{px:.{DEC}f}</div>", unsafe_allow_html=True)
            st.caption(f"Δ {d:.{DEC}f} ({pct:.2f}%), {where} market")
            # Clip flag
            clipped = (px == zone_lower) or (px == zone_upper)
            if clipped:
                st.caption("🔒 Clipped to zone edge")

    st.markdown("---")

    # SL / TP / RR
    rr = ((tp - market) / max(market - sl, 1e-12)) if side == "Long" else ((market - tp) / max(sl - market, 1e-12))
    a, b, c = st.columns(3)
    with a:
        st.markdown("**Stop Loss**")
        st.markdown(f"<div class='valbox val-red'>{sl:.{DEC}f}</div>", unsafe_allow_html=True)
        st.caption(f"Rule: {'ZL -' if side=='Long' else 'ZU +'} {sl_buf}×ATR")
    with b:
        st.markdown("**Take Profit**")
        st.markdown(f"<div class='valbox val-green'>{tp:.{DEC}f}</div>", unsafe_allow_html=True)
        st.caption(f"Rule: Entry {'+' if side=='Long' else '−'} {tp_mult}×ATR")
    with c:
        st.markdown("**Reward : Risk**")
        st.markdown(f"<div class='valbox val-blue'>{rr:.2f} : 1</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Decision notes
    st.markdown("#### Notes")
    st.markdown(
        f"<span class='badge'>Zone width: {zone_w:.{DEC}f}</span>"
        f"<span class='badge'>ATR: {atr:.{DEC}f}</span>"
        f"<span class='badge'>k = width/ATR: {k:.2f}</span>"
        f"<span class='badge'>Ladders: {ladders}</span>"
        f"<span class='badge'>Base step: {base_step:.{DEC}f}</span>"
        f"<span class='badge'>MACD step: {step:.{DEC}f}</span>",
        unsafe_allow_html=True
    )
    tips = []
    if adx >= 25: tips.append("ADX≥25 → reduced ladders (trend).")
    if rsi_trigger != "None": tips.append(f"RSI rule noted: {rsi_trigger}.")
    if macd != "Neutral": tips.append(f"MACD bias applied: {macd}.")
    if tips:
        st.caption(" • ".join(tips))

else:
    st.info("Enter values and press **Calculate** to generate ladder entries.", icon="ℹ️")
