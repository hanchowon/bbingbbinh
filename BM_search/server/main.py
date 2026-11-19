"""
==============================================================================
BFS vs DFS 미로 탐색 비교 시뮬레이션 백엔드 API (FastAPI)
- 기능:
  1. 너비 우선 탐색 (BFS - Queue FIFO): 최단 경로 보장, O(V) 경계 큐 메모리
  2. 깊이 우선 탐색 (DFS - Stack LIFO): 깊이 우선 추적, 백트래킹, O(h) 콜스택 메모리
  3. 단계별 스냅샷 히스토그램 데이터 (Queue/Stack 버퍼, 연산량, 레이어 깊이, 진행률)
  4. 시간 복잡도 O(V+E) 진행 상태 및 누적 소요 시간 메타데이터 반환
==============================================================================
"""

import time
import random
from collections import deque
from typing import Any, Dict, List, Optional, Tuple
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Maze Pathfinding BFS vs DFS Benchmark API",
    description="미로 탈출을 위한 BFS(Queue) vs DFS(Stack) 알고리즘 비교 시각화 엔진",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 기본 17x17 결정론적 미로 토폴로지 (1: 벽, 0: 통로)
DEFAULT_17X17_MAZE = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,1],
    [1,0,1,0,1,0,1,1,1,0,1,0,1,1,1,0,1],
    [1,0,1,0,0,0,1,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,1,1,1,0,1,1,1,1,1,0,1,0,1],
    [1,0,0,0,0,0,0,0,1,0,0,0,0,0,1,0,1],
    [1,1,1,0,1,1,1,0,1,0,1,1,1,0,1,0,1],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,1,0,1],
    [1,0,1,1,1,0,1,1,1,1,1,0,1,1,1,0,1],
    [1,0,1,0,0,0,1,0,0,0,0,0,1,0,0,0,1],
    [1,0,1,0,1,1,1,0,1,1,1,1,1,0,1,0,1],
    [1,0,0,0,1,0,0,0,1,0,0,0,0,0,1,0,1],
    [1,1,1,0,1,0,1,1,1,0,1,1,1,1,1,0,1],
    [1,0,0,0,1,0,0,0,1,0,1,0,0,0,0,0,1],
    [1,0,1,1,1,1,1,0,1,0,1,0,1,1,1,0,1],
    [1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
]


class MazeRequest(BaseModel):
    maze: Optional[List[List[int]]] = Field(default=None, description="2차원 미로 배열 (0: 길, 1: 벽)")
    start: Optional[List[int]] = Field(default=[1, 1], description="시작점 [row, col]")
    goal: Optional[List[int]] = Field(default=[15, 15], description="목표점 [row, col]")


def solve_bfs(maze: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, Any]:
    """너비 우선 탐색 (Queue - FIFO) 시뮬레이션 및 스냅샷 생성"""
    start_time = time.perf_counter()
    rows, cols = len(maze), len(maze[0])
    total_passages = sum(row.count(0) for row in maze)

    queue = deque([(start, 0)])  # (coordinate, layer)
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    visited_set = {start}
    visited_order = [start]

    steps: List[Dict[str, Any]] = []
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # 북, 동, 남, 서
    ops_count = 0
    found = False

    while queue:
        curr, layer = queue.popleft()
        ops_count += 1
        curr_r, curr_c = curr

        # 현재 큐에 대기 중인 프론티어 목록 추출
        current_queue_state = [[node[0], node[1]] for node, _ in queue]

        # 시간 복잡도 O(V + E) 진행률 계산
        progress_pct = min(100.0, round((len(visited_set) / max(total_passages, 1)) * 100, 2))
        curr_elapsed = round((time.perf_counter() - start_time) * 1000, 4)

        # 히스토그램 스냅샷 데이터 기록
        steps.append({
            "step_index": len(steps) + 1,
            "algorithm": "BFS",
            "current": [curr_r, curr_c],
            "layer": layer,
            "buffer_type": "QUEUE_FIFO",
            "buffer_size": len(queue),
            "buffer_items": current_queue_state[:10],  # 상위 10개
            "visited_count": len(visited_set),
            "operations_count": ops_count,
            "time_ms": curr_elapsed,
            "complexity_progress_pct": progress_pct,
            "histogram": {
                "buffer_size": len(queue),
                "layer_depth": layer,
                "visited_count": len(visited_set),
                "visited_ratio_pct": progress_pct,
                "ops_delta": 1 + len(directions)
            }
        })

        if curr == goal:
            found = True
            break

        # 이웃 탐색
        for dr, dc in directions:
            nr, nc = curr_r + dr, curr_c + dc
            ops_count += 1
            if 0 <= nr < rows and 0 <= nc < cols:
                if maze[nr][nc] == 0 and (nr, nc) not in visited_set:
                    visited_set.add((nr, nc))
                    visited_order.append((nr, nc))
                    parent[(nr, nc)] = curr
                    queue.append(((nr, nc), layer + 1))

    # 최단 경로 역추적
    path = []
    if found:
        curr_trace: Optional[Tuple[int, int]] = goal
        while curr_trace is not None:
            path.append([curr_trace[0], curr_trace[1]])
            curr_trace = parent.get(curr_trace)
        path.reverse()

    total_elapsed = round((time.perf_counter() - start_time) * 1000, 4)

    return {
        "algorithm": "BFS",
        "data_structure": "Queue (FIFO)",
        "found": found,
        "path": path,
        "path_length": len(path),
        "is_optimal": True,
        "total_visited": len(visited_set),
        "total_operations": ops_count,
        "elapsed_ms": total_elapsed,
        "time_complexity": "O(V + E)",
        "aux_space_complexity": "O(V) Frontier Queue",
        "steps": steps
    }


def solve_dfs(maze: List[List[int]], start: Tuple[int, int], goal: Tuple[int, int]) -> Dict[str, Any]:
    """깊이 우선 탐색 (Stack - LIFO) 시뮬레이션 및 스냅샷 생성"""
    start_time = time.perf_counter()
    rows, cols = len(maze), len(maze[0])
    total_passages = sum(row.count(0) for row in maze)

    stack = [start]  # Call Stack / LIFO
    visited_set = {start}
    visited_order = [start]
    parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
    dead_ends: List[List[int]] = []

    steps: List[Dict[str, Any]] = []
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]  # 북, 동, 남, 서
    ops_count = 0
    found = False

    while stack:
        curr = stack[-1]  # Peek top
        ops_count += 1
        curr_r, curr_c = curr

        if curr == goal:
            found = True
            break

        # 미방문 이웃 탐색
        unvisited_neighbors = []
        for dr, dc in directions:
            nr, nc = curr_r + dr, curr_c + dc
            ops_count += 1
            if 0 <= nr < rows and 0 <= nc < cols:
                if maze[nr][nc] == 0 and (nr, nc) not in visited_set:
                    unvisited_neighbors.append((nr, nc))

        # 현재 콜 스택 상태 복사
        stack_items = [[node[0], node[1]] for node in stack]
        progress_pct = min(100.0, round((len(visited_set) / max(total_passages, 1)) * 100, 2))
        curr_elapsed = round((time.perf_counter() - start_time) * 1000, 4)

        if unvisited_neighbors:
            # 첫 번째 미방문 경로로 전진 (Push)
            nxt = unvisited_neighbors[0]
            visited_set.add(nxt)
            visited_order.append(nxt)
            parent[nxt] = curr
            stack.append(nxt)

            steps.append({
                "step_index": len(steps) + 1,
                "algorithm": "DFS",
                "current": [nxt[0], nxt[1]],
                "action": "PUSH",
                "buffer_type": "STACK_LIFO",
                "buffer_size": len(stack),
                "buffer_items": stack_items[-10:],
                "visited_count": len(visited_set),
                "dead_ends_count": len(dead_ends),
                "operations_count": ops_count,
                "time_ms": curr_elapsed,
                "complexity_progress_pct": progress_pct,
                "histogram": {
                    "buffer_size": len(stack),
                    "layer_depth": len(stack),
                    "visited_count": len(visited_set),
                    "visited_ratio_pct": progress_pct,
                    "ops_delta": 1 + len(directions)
                }
            })
        else:
            # 막다른 길에 도달 -> 백트래킹 (Pop)
            dead_ends.append([curr_r, curr_c])
            stack.pop()

            steps.append({
                "step_index": len(steps) + 1,
                "algorithm": "DFS",
                "current": [curr_r, curr_c],
                "action": "BACKTRACK_POP",
                "buffer_type": "STACK_LIFO",
                "buffer_size": len(stack),
                "buffer_items": stack_items[-10:],
                "visited_count": len(visited_set),
                "dead_ends_count": len(dead_ends),
                "operations_count": ops_count,
                "time_ms": curr_elapsed,
                "complexity_progress_pct": progress_pct,
                "histogram": {
                    "buffer_size": len(stack),
                    "layer_depth": len(stack),
                    "visited_count": len(visited_set),
                    "visited_ratio_pct": progress_pct,
                    "ops_delta": 2
                }
            })

    # 탐색된 DFS 경로 (스택에 남은 최종 도달 경로)
    path = [[n[0], n[1]] for n in stack]
    total_elapsed = round((time.perf_counter() - start_time) * 1000, 4)

    return {
        "algorithm": "DFS",
        "data_structure": "Call Stack (LIFO)",
        "found": found,
        "path": path,
        "path_length": len(path),
        "is_optimal": False,
        "dead_ends": dead_ends,
        "total_visited": len(visited_set),
        "total_operations": ops_count,
        "elapsed_ms": total_elapsed,
        "time_complexity": "O(V + E)",
        "aux_space_complexity": "O(h) Call Stack",
        "steps": steps
    }


@app.get("/health")
def health_check() -> Dict[str, Any]:
    """클라우드 런 및 GAS 프록시 헬스체크"""
    return {
        "status": "healthy",
        "service": "BFS vs DFS Maze Visualizer Engine",
        "version": "1.0.0",
        "timestamp": int(time.time() * 1000)
    }


@app.get("/api/maze/default")
def get_default_maze() -> Dict[str, Any]:
    """기본 17x17 미로 토폴로지 반환"""
    return {
        "size": 17,
        "maze": DEFAULT_17X17_MAZE,
        "start": [1, 1],
        "goal": [15, 15]
    }


@app.post("/api/maze/compare")
def compare_algorithms(req: MazeRequest) -> Dict[str, Any]:
    """BFS와 DFS 듀얼 탐색 시뮬레이션 및 스텝별 히스토그램 비교 데이터 반환"""
    maze = req.maze if req.maze is not None else DEFAULT_17X17_MAZE
    start_pos = (req.start[0], req.start[1])
    goal_pos = (req.goal[0], req.goal[1])

    bfs_result = solve_bfs(maze, start_pos, goal_pos)
    dfs_result = solve_dfs(maze, start_pos, goal_pos)

    # 비교 요약 메타데이터
    comparison = {
        "bfs_path_length": bfs_result["path_length"],
        "dfs_path_length": dfs_result["path_length"],
        "bfs_visited": bfs_result["total_visited"],
        "dfs_visited": dfs_result["total_visited"],
        "bfs_elapsed_ms": bfs_result["elapsed_ms"],
        "dfs_elapsed_ms": dfs_result["elapsed_ms"],
        "step_delta": dfs_result["path_length"] - bfs_result["path_length"],
        "optimal_winner": "BFS (Guaranteed Shortest Path in Unweighted Graph)"
    }

    return {
        "maze": maze,
        "start": list(start_pos),
        "goal": list(goal_pos),
        "comparison": comparison,
        "bfs": bfs_result,
        "dfs": dfs_result
    }
