"""Natijalar/progress hisoboti va grafik generatsiyasi."""
from __future__ import annotations

import io
from typing import List, Optional

from app.utils.logging_config import get_logger

logger = get_logger(__name__)


def build_progress_report(
    *,
    start_weight: Optional[float],
    latest_weight: Optional[float],
    weight_count: int,
    completed_workouts_week: int,
    completed_workouts_total: int,
    latest_waist: Optional[float] = None,
) -> str:
    """Progress bo'limi uchun matnli hisobot (HTML)."""
    lines = ["📊 <b>Natijalarim</b>", ""]

    if start_weight is not None:
        lines.append(f"• Boshlang'ich vazn: <b>{start_weight:g}</b> kg")
    if latest_weight is not None:
        lines.append(f"• Oxirgi vazn: <b>{latest_weight:g}</b> kg")
    if start_weight is not None and latest_weight is not None:
        diff = round(latest_weight - start_weight, 1)
        if diff < 0:
            lines.append(f"• O'zgarish: <b>{diff:g} kg</b> ⬇️")
        elif diff > 0:
            lines.append(f"• O'zgarish: <b>+{diff:g} kg</b> ⬆️")
        else:
            lines.append("• O'zgarish: <b>0 kg</b> ➡️")

    if latest_waist is not None:
        lines.append(f"• Oxirgi bel aylanasi: <b>{latest_waist:g}</b> sm")

    lines.append("")
    lines.append(f"• Bu hafta bajarilgan mashg'ulotlar: <b>{completed_workouts_week}</b>")
    lines.append(f"• Jami bajarilgan mashg'ulotlar: <b>{completed_workouts_total}</b>")
    lines.append(f"• Kiritilgan vazn qaydlari: <b>{weight_count}</b>")

    lines.append("")
    lines.append(
        "ℹ️ Vaznning kunlik tebranishi (suv, ovqat) tabiiy hol — buni yog' "
        "o'zgarishi deb hisoblamang. Haftalik o'rtacha tendensiyaga qarang."
    )
    return "\n".join(lines)


def generate_weight_chart(
    dates: List, weights: List[float]
) -> Optional[bytes]:
    """Vazn grafigini PNG bytes sifatida qaytaradi.

    Xatolik yoki ma'lumot yetarli bo'lmasa None qaytaradi (chaqiruvchi matnli
    hisobotga qaytadi).
    """
    if len(weights) < 2:
        return None
    try:
        import matplotlib

        matplotlib.use("Agg")  # serverda displaysiz ishlash
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates

        fig, ax = plt.subplots(figsize=(8, 4.5))
        ax.plot(dates, weights, marker="o", linewidth=2, color="#2e86de")
        ax.set_title("Vazn o'zgarishi", fontsize=14)
        ax.set_ylabel("Vazn (kg)")
        ax.grid(True, alpha=0.3)
        try:
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d-%m"))
            fig.autofmt_xdate()
        except Exception:
            pass

        buf = io.BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format="png", dpi=100)
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()
    except Exception as exc:  # matplotlib yo'q yoki xato
        logger.warning("Grafik generatsiyasida xato: %s", exc)
        return None
