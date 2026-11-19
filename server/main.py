"""
==============================================================================
보이어-무어(Boyer-Moore) 문자열 검색 알고리즘 시각화 백엔드 API (FastAPI)
- 지원 기능:
  1. 보이어-무어법 로직 (Bad Character Table & Good Suffix Table)
  2. 단계별 듀얼 히스토그램 스냅샷 데이터 생성 (Bad Character vs Good Suffix)
  3. 단계별 누적 소요 시간(ms) 및 시간 복잡도 진행률(Progress %) 메타데이터
==============================================================================
"""

import time
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Boyer-Moore Visualizer API",
    description="보이어-무어 알고리즘의 나쁜 문자표와 착한 접미부 비교 시각화 API",
    version="2.4.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SearchRequest(BaseModel):
    text: Optional[str] = Field(default="BABBABABAC", description="검색 대상 텍스트")
    pattern: Optional[str] = Field(default="BABACB", description="검색할 패턴")


def build_bad_character_table(pattern: str) -> Dict[str, int]:
    """나쁜 문자 규칙 룩업 테이블 생성"""
    return {char: i for i, char in enumerate(pattern)}


def build_good_suffix_table(pattern: str) -> List[int]:
    """착한 접미부 규칙 이동 테이블 생성"""
    m = len(pattern)
    suff = [0] * m
    suff[m - 1] = m
    g = m - 1
    f = m - 1

    for i in range(m - 2, -1, -1):
        if i > g and suff[i + m - 1 - f] < i - g:
            suff[i] = suff[i + m - 1 - f]
        else:
            if i < g:
                g = i
            f = i
            while g >= 0 and pattern[g] == pattern[g + m - 1 - f]:
                g -= 1
            suff[i] = f - g

    shift = [m] * (m + 1)
    j = 0
    for i in range(m - 1, -1, -1):
        if suff[i] == i + 1:
            while j < m - 1 - i:
                if shift[j] == m:
                    shift[j] = m - 1 - i
                j += 1

    for i in range(m - 1):
        shift[m - 1 - suff[i]] = m - 1 - i

    return shift


def simulate_boyer_moore(text: str, pattern: str) -> Dict[str, Any]:
    """보이어-무어 알고리즘 단계별 히스토그램 및 시간 복잡도 메타데이터 생성"""
    start_perf = time.perf_counter()
    n = len(text)
    m = len(pattern)

    if m == 0 or n == 0 or m > n:
        return {
            "text": text,
            "pattern": pattern,
            "steps": [],
            "matches": [],
            "total_comparisons": 0,
            "brute_force_comparisons": 0,
            "efficiency_gain_pct": 0.0,
            "elapsed_ms": 0.0
        }

    bad_char = build_bad_character_table(pattern)
    good_suffix = build_good_suffix_table(pattern)

    steps: List[Dict[str, Any]] = []
    matches: List[int] = []
    total_comps = 0
    k = 0

    max_k = max(n - m, 1)
    bc_comp_counts: Dict[int, int] = {}
    gs_comp_counts: Dict[int, int] = {}

    while k <= n - m:
        j = m - 1
        matched_sub: List[str] = []
        is_mismatch = False

        while j >= 0:
            total_comps += 1
            curr_char_t = text[k + j]
            curr_char_p = pattern[j]
            comp_match = (curr_char_t == curr_char_p)

            bc_comp_counts[k] = bc_comp_counts.get(k, 0) + 1
            gs_comp_counts[k] = gs_comp_counts.get(k, 0) + 1

            # 복잡도 진행률: 윈도우 진행(k/max_k)과 현재 문자 비교(m-1-j)/m의 결합
            progress_pct = min(100.0, round(((k + (m - 1 - j) / m) / (max_k + 1)) * 100, 1))
            curr_elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

            # 히스토그램 스냅샷 생성 (나쁜 문자 vs 착한 접미부)
            bc_bars = [
                {
                    "k": offset,
                    "label": f"k={offset}",
                    "comparisons": bc_comp_counts.get(offset, 0),
                    "is_active": (offset == k)
                }
                for offset in range(0, n - m + 1)
            ]
            gs_bars = [
                {
                    "k": offset,
                    "label": f"k={offset}",
                    "comparisons": gs_comp_counts.get(offset, 0),
                    "is_active": (offset == k)
                }
                for offset in range(0, n - m + 1)
            ]

            if comp_match:
                matched_sub.append(curr_char_p)
                steps.append({
                    "step_index": len(steps) + 1,
                    "k": k,
                    "j": j,
                    "text_index": k + j,
                    "char_text": curr_char_t,
                    "char_pattern": curr_char_p,
                    "type": "MATCH",
                    "matched_suffix": "".join(reversed(matched_sub)),
                    "shift_bad_char": 0,
                    "shift_good_suffix": 0,
                    "final_shift": 0,
                    "next_k": k,
                    "time_ms": curr_elapsed_ms,
                    "complexity_progress_pct": progress_pct,
                    "histogram": {
                        "bad_char_bars": bc_bars,
                        "good_suffix_bars": gs_bars
                    },
                    "explanation": f"P[{j}]('{curr_char_p}') == T[{k+j}]('{curr_char_t}') 일치 (우측→좌측 진행)"
                })
                j -= 1
            else:
                is_mismatch = True
                bc_pos = bad_char.get(curr_char_t, -1)
                bc_shift = max(1, j - bc_pos)
                gs_shift = good_suffix[j + 1] if (j + 1) < len(good_suffix) else 1
                final_shift = max(bc_shift, gs_shift)
                next_k = k + final_shift

                rule_adopted = "Good Suffix(Δ₂)" if gs_shift >= bc_shift else "Bad Character(Δ₁)"

                steps.append({
                    "step_index": len(steps) + 1,
                    "k": k,
                    "j": j,
                    "text_index": k + j,
                    "char_text": curr_char_t,
                    "char_pattern": curr_char_p,
                    "type": "MISMATCH",
                    "matched_suffix": "".join(reversed(matched_sub)),
                    "shift_bad_char": bc_shift,
                    "shift_good_suffix": gs_shift,
                    "final_shift": final_shift,
                    "next_k": next_k,
                    "rule_adopted": rule_adopted,
                    "time_ms": curr_elapsed_ms,
                    "complexity_progress_pct": progress_pct,
                    "histogram": {
                        "bad_char_bars": bc_bars,
                        "good_suffix_bars": gs_bars
                    },
                    "explanation": (
                        f"P[{j}]('{curr_char_p}') != T[{k+j}]('{curr_char_t}') 불일치! "
                        f"Δ₁={bc_shift}, Δ₂={gs_shift} -> {rule_adopted}에 따라 {final_shift}칸 우측 도약"
                    )
                })
                k = next_k
                break

        if not is_mismatch:
            matches.append(k)
            final_shift = good_suffix[0] if len(good_suffix) > 0 else 1
            next_k = k + final_shift
            curr_elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

            steps.append({
                "step_index": len(steps) + 1,
                "k": k,
                "j": 0,
                "text_index": k,
                "char_text": text[k],
                "char_pattern": pattern[0],
                "type": "FULL_MATCH",
                "matched_suffix": pattern,
                "shift_bad_char": 0,
                "shift_good_suffix": final_shift,
                "final_shift": final_shift,
                "next_k": next_k,
                "rule_adopted": "Match Found",
                "time_ms": curr_elapsed_ms,
                "complexity_progress_pct": 100.0 if next_k > n - m else progress_pct,
                "histogram": {
                    "bad_char_bars": bc_bars,
                    "good_suffix_bars": gs_bars
                },
                "explanation": f"패턴 완전 일치 발견! (위치: {k}) -> {final_shift}칸 도약하여 후속 탐색"
            })
            k = next_k

    total_elapsed_ms = round((time.perf_counter() - start_perf) * 1000, 4)

    bf_comps = 0
    for i in range(n - m + 1):
        for pj in range(m):
            bf_comps += 1
            if text[i + pj] != pattern[pj]:
                break

    gain = round(((bf_comps - total_comps) / max(bf_comps, 1)) * 100, 1) if bf_comps > total_comps else 0.0

    return {
        "text": text,
        "pattern": pattern,
        "bad_character_table": bad_char,
        "good_suffix_table": good_suffix,
        "steps": steps,
        "matches": matches,
        "total_comparisons": total_comps,
        "brute_force_comparisons": bf_comps,
        "efficiency_gain_pct": gain,
        "elapsed_ms": total_elapsed_ms
    }


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """GAS 프록시 및 클라우드 런 헬스체크 엔드포인트"""
    return {
        "status": "healthy",
        "service": "Boyer-Moore Visualizer Engine",
        "version": "2.4.0",
        "worker": "Worker #3",
        "timestamp": int(time.time() * 1000)
    }


@app.post("/boyer-moore")
def api_boyer_moore(req: SearchRequest) -> Dict[str, Any]:
    """보이어-무어 문자열 매칭 시뮬레이션 데이터 반환"""
    if not req.text or not req.pattern:
        raise HTTPException(status_code=400, detail="텍스트와 패턴 문자열은 필수입니다.")
    return simulate_boyer_moore(req.text, req.pattern)


@app.websocket("/stream")
async def websocket_stream(websocket: WebSocket):
    """실시간 시뮬레이션 프레임 스트리밍 웹소켓"""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            text = data.get("text", "BABBABABAC")
            pattern = data.get("pattern", "BABACB")
            result = simulate_boyer_moore(text, pattern)
            await websocket.send_json(result)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        await websocket.close(code=1011, reason=str(e))
