"""Maps FTMS inclination/resistance values to bike resistance levels.

Uses piecewise linear interpolation over a configurable mapping table.
"""

import bisect
import logging
from typing import Any

logger = logging.getLogger(__name__)


class ResistanceMapper:
    """Converts FTMS inclination (grade %) or resistance (0-100%) to a
    discrete bike resistance level."""

    def __init__(self, config: dict[str, Any]):
        bridge_cfg = config["bridge"]
        self._min_level = bridge_cfg["min_level"]
        self._max_level = bridge_cfg["max_level"]

        # Build sorted lookup tables from config maps
        incl_map = bridge_cfg["inclination_map"]
        self._incl_grades = sorted(incl_map.keys())
        self._incl_levels = [incl_map[g] for g in self._incl_grades]

        res_map = bridge_cfg["resistance_pct_map"]
        self._res_pcts = sorted(res_map.keys())
        self._res_levels = [res_map[p] for p in self._res_pcts]

        logger.info(
            "Resistance mapper: inclination range %.1f%%..%.1f%% → levels %d..%d",
            self._incl_grades[0], self._incl_grades[-1],
            self._incl_levels[0], self._incl_levels[-1],
        )

    def from_inclination(self, grade_percent: float) -> int:
        """Map an inclination grade (%) to a bike resistance level."""
        level = self._interpolate(grade_percent, self._incl_grades, self._incl_levels)
        return self._clamp(level)

    def from_resistance_percent(self, resistance_pct: float) -> int:
        """Map a resistance percentage (0-100) to a bike resistance level."""
        level = self._interpolate(resistance_pct, self._res_pcts, self._res_levels)
        return self._clamp(level)

    def _clamp(self, level: float) -> int:
        """Clamp and round to valid bike level range."""
        return max(self._min_level, min(self._max_level, round(level)))

    @staticmethod
    def _interpolate(x: float, xs: list[float], ys: list[int]) -> float:
        """Piecewise linear interpolation.

        Args:
            x: Input value.
            xs: Sorted list of input breakpoints.
            ys: Corresponding output values.

        Returns:
            Interpolated output value.
        """
        if x <= xs[0]:
            return float(ys[0])
        if x >= xs[-1]:
            return float(ys[-1])

        # Find the segment containing x
        i = bisect.bisect_right(xs, x) - 1
        x0, x1 = xs[i], xs[i + 1]
        y0, y1 = ys[i], ys[i + 1]

        # Linear interpolation
        t = (x - x0) / (x1 - x0)
        return y0 + t * (y1 - y0)
