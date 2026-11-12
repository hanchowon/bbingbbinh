# [main.py] 단계별 히스토그램 막대 데이터 및 시간 복잡도 진행률 생성 블록
progress_pct = min(100.0, round(((k + (m - 1 - j) / m) / (max_k + 1)) * 100, 1))
curr_elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

# 나쁜 문자(Δ₁) vs 착한 접미부(Δ₂) 동시 비교 히스토그램 스냅샷
bc_bars = [
    {"k": offset, "label": f"k={offset}", "comparisons": bc_comp_counts.get(offset, 0), "is_active": (offset == k)}
    for offset in range(0, n - m + 1)
]
gs_bars = [
    {"k": offset, "label": f"k={offset}", "comparisons": gs_comp_counts.get(offset, 0), "is_active": (offset == k)}
    for offset in range(0, n - m + 1)
]

steps.append({
    "step_index": len(steps) + 1,
    "k": k, "j": j, "text_index": k + j,
    "char_text": curr_char_t, "char_pattern": curr_char_p,
    "type": "MISMATCH",
    "shift_bad_char": bc_shift, "shift_good_suffix": gs_shift,
    "final_shift": final_shift, "next_k": next_k,
    "rule_adopted": rule_adopted,
    "time_ms": curr_elapsed_ms,
    "complexity_progress_pct": progress_pct,
    "histogram": {
        "bad_char_bars": bc_bars,
        "good_suffix_bars": gs_bars
    }
})
