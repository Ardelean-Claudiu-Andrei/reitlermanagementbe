"""
Shared DXF rendering utility.

Converts a DXF file to an SVG or PNG data-URI suitable for embedding in HTML/PDF.

Key behaviour
─────────────
* Uses ezdxf's SVG backend as the primary path (no extra runtime deps).
* Falls back to matplotlib if the SVG path raises an exception.
* After the SVG is produced, near-white stroke colours are replaced with a
  dark ink colour.  This makes "True Colour white" entities (dxf.true_color
  == 0xFFFFFF) — which bypass ezdxf's ACI palette remapping — visible on a
  white background without touching the original file.
* LayoutProperties are passed to both rendering paths so ezdxf also remaps
  ACI palette colour 7 (AutoCAD "background-dependent white") to black.
"""

import re
import io
import base64


# ── Threshold for "near white" (0-255 per channel) ───────────────────────────
# 230/255 ≈ 90 %.  Catches pure white and very light colours that are
# invisible on a white page; leaves normal mid-tones untouched.
_NEAR_WHITE_THRESHOLD = 230


def _is_near_white_hex(hex_color: str) -> bool:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = h[0] * 2 + h[1] * 2 + h[2] * 2
    if len(h) != 6:
        return False
    try:
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
    except ValueError:
        return False
    return r >= _NEAR_WHITE_THRESHOLD and g >= _NEAR_WHITE_THRESHOLD and b >= _NEAR_WHITE_THRESHOLD


# Match SVG attribute form:  stroke="#ffffff"
_STROKE_ATTR_RE = re.compile(r'stroke="(#[0-9a-fA-F]{3,6})"', re.ASCII)
# Match CSS inline form:  stroke: #fff
_STROKE_STYLE_RE = re.compile(r'(stroke\s*:\s*)(#[0-9a-fA-F]{3,6})', re.ASCII)

_DARK_INK = "#1a1a1a"


def _darken_white_strokes(svg: str) -> str:
    """
    Replace near-white stroke colours in an ezdxf-generated SVG with a dark
    ink colour so they are visible when rendered on a white background.

    Only stroke colours are touched; fill colours are left intact so that
    solid-filled regions (hatches etc.) are not accidentally darkened.
    """

    def _fix_attr(m: re.Match) -> str:
        return f'stroke="{_DARK_INK}"' if _is_near_white_hex(m.group(1)) else m.group(0)

    def _fix_style(m: re.Match) -> str:
        return f"{m.group(1)}{_DARK_INK}" if _is_near_white_hex(m.group(2)) else m.group(0)

    svg = _STROKE_ATTR_RE.sub(_fix_attr, svg)
    svg = _STROKE_STYLE_RE.sub(_fix_style, svg)
    return svg


def render_dxf_to_data_uri(abs_path: str) -> "str | None":
    """
    Render a DXF file to a base-64-encoded data-URI (SVG or PNG).

    Returns None if all rendering attempts fail (bad file, missing deps, …).
    """
    try:
        import ezdxf
        doc = ezdxf.readfile(abs_path)
        msp = doc.modelspace()
    except Exception:
        return None

    # ── Attempt 1: ezdxf SVG backend (no matplotlib required) ────────────────
    try:
        from ezdxf.addons.drawing import RenderContext, Frontend, layout
        from ezdxf.addons.drawing.svg import SVGBackend
        from ezdxf.addons.drawing.properties import LayoutProperties

        ctx = RenderContext(doc)
        lp = LayoutProperties.from_layout(msp)
        # White background + black default: remaps ACI 7 (white) → black.
        # True Colour white entities are handled by _darken_white_strokes below.
        lp.set_colors("#ffffff", "#000000")

        backend = SVGBackend()
        Frontend(ctx, backend).draw_layout(msp, layout_properties=lp)
        page = layout.Page(width=80, height=80, units=layout.Units.mm)
        svg = backend.get_string(page)
        if svg:
            svg = _darken_white_strokes(svg)
            return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()
    except Exception:
        pass

    # ── Attempt 2: matplotlib PNG fallback ────────────────────────────────────
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from ezdxf.addons.drawing import RenderContext, Frontend
        from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
        from ezdxf.addons.drawing.properties import LayoutProperties

        ctx = RenderContext(doc)
        lp = LayoutProperties.from_layout(msp)
        lp.set_colors("#ffffff", "#000000")

        fig = plt.figure(figsize=(3, 3), dpi=96)
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_aspect("equal")
        backend = MatplotlibBackend(ax)
        # Pass layout_properties so ACI 7 is remapped to black.
        Frontend(ctx, backend).draw_layout(msp, layout_properties=lp)
        ax.set_axis_off()

        buf = io.BytesIO()
        fig.savefig(
            buf, format="png", dpi=96, bbox_inches="tight",
            facecolor="white", edgecolor="none", pad_inches=0.1,
        )
        plt.close(fig)
        buf.seek(0)
        raw = buf.read()
        if raw:
            return "data:image/png;base64," + base64.b64encode(raw).decode()
    except Exception:
        pass

    return None
