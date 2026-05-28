from datetime import datetime, timezone
from typing import Any

import networkx as nx


SEVERITY_RANK = {
    'high': 3,
    'medium': 2,
    'low': 1,
}


def _utc_iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def _date_only(value: Any) -> Any | None:
    if value is None:
        return None
    if hasattr(value, 'date'):
        return value.date()
    return None


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _normalize_dependency_ids(raw_dependencies: Any, task_id: int, warnings: list[dict[str, Any]]) -> list[int]:
    if raw_dependencies in (None, ''):
        return []

    if not isinstance(raw_dependencies, list):
        warnings.append(
            {
                'code': 'invalid_dependency_format',
                'message': 'depends_on_task_ids 必須是陣列，已忽略該任務依賴設定',
                'task_id': task_id,
            }
        )
        return []

    normalized = []
    seen = set()

    for raw_id in raw_dependencies:
        dependency_task_id = _to_int(raw_id)
        if dependency_task_id is None or dependency_task_id <= 0:
            warnings.append(
                {
                    'code': 'invalid_dependency_id',
                    'message': '依賴任務 ID 非法，已忽略',
                    'task_id': task_id,
                    'dependency_task_id': raw_id,
                }
            )
            continue

        if dependency_task_id == task_id:
            warnings.append(
                {
                    'code': 'self_dependency',
                    'message': '任務不可依賴自己，已忽略該依賴',
                    'task_id': task_id,
                    'dependency_task_id': dependency_task_id,
                }
            )
            continue

        if dependency_task_id in seen:
            continue

        seen.add(dependency_task_id)
        normalized.append(dependency_task_id)

    return normalized


def _resolve_task_schedule(task: Any, warnings: list[dict[str, Any]]) -> dict[str, Any]:
    start_date = _date_only(task.start_date)
    end_date = _date_only(task.end_date)
    is_schedule_incomplete = False

    if start_date and end_date and end_date < start_date:
        warnings.append(
            {
                'code': 'invalid_task_dates',
                'message': '任務結束日期早於開始日期，已退化為 1 天工期估算',
                'task_id': task.task_id,
            }
        )
        end_date = start_date
        is_schedule_incomplete = True
    elif not start_date or not end_date:
        is_schedule_incomplete = True
        warnings.append(
            {
                'code': 'incomplete_schedule',
                'message': '任務缺少完整起訖日期，將以 1 天工期估算',
                'task_id': task.task_id,
            }
        )
        if start_date and not end_date:
            end_date = start_date
        elif end_date and not start_date:
            start_date = end_date

    duration_days = 1
    if start_date and end_date:
        duration_days = max((end_date - start_date).days + 1, 1)

    return {
        'start_date': start_date,
        'end_date': end_date,
        'duration_days': duration_days,
        'is_schedule_incomplete': is_schedule_incomplete,
    }


def _severity_max(current: str, target: str) -> str:
    if SEVERITY_RANK[target] > SEVERITY_RANK[current]:
        return target
    return current


def _suggest_actions(is_critical: bool, is_overdue: bool, is_schedule_incomplete: bool) -> list[str]:
    actions = []

    if is_critical:
        actions.append('此任務位於關鍵路徑，建議每日追蹤進度並優先排除阻塞')
    if is_overdue:
        actions.append('任務已逾期，建議立即調整資源或拆分交付範圍')
    if is_schedule_incomplete:
        actions.append('請先補齊開始與結束日期，提升排程與風險分析準確度')

    if not actions:
        actions.append('建議檢查前置依賴是否可並行化，以保留時程緩衝')

    return actions


def build_critical_path_analysis_payload(timeline: Any, tasks: list[Any]) -> dict[str, Any]:
    warnings = []
    task_map = {task.task_id: task for task in tasks}
    graph = nx.DiGraph()
    node_meta = {}

    for task in tasks:
        schedule_meta = _resolve_task_schedule(task, warnings)
        dependency_ids = _normalize_dependency_ids(
            raw_dependencies=getattr(task, 'depends_on_task_ids', None),
            task_id=task.task_id,
            warnings=warnings,
        )

        valid_dependency_ids = []
        for dependency_task_id in dependency_ids:
            if dependency_task_id not in task_map:
                warnings.append(
                    {
                        'code': 'missing_dependency',
                        'message': '依賴任務不存在、已刪除或不在同一專案，已忽略',
                        'task_id': task.task_id,
                        'dependency_task_id': dependency_task_id,
                    }
                )
                continue
            valid_dependency_ids.append(dependency_task_id)

        node_meta[task.task_id] = {
            'task': task,
            'depends_on_task_ids': valid_dependency_ids,
            **schedule_meta,
        }
        graph.add_node(task.task_id, duration_days=schedule_meta['duration_days'])

    for task_id, meta in node_meta.items():
        for dependency_task_id in meta['depends_on_task_ids']:
            graph.add_edge(dependency_task_id, task_id)

    removed_cycle_edges = []
    while not nx.is_directed_acyclic_graph(graph):
        try:
            cycle_edges = nx.find_cycle(graph, orientation='original')
        except nx.NetworkXNoCycle:
            break

        source, target, _direction = cycle_edges[-1]
        graph.remove_edge(source, target)
        removed_cycle_edges.append((source, target))
        warnings.append(
            {
                'code': 'cycle_edge_removed',
                'message': '偵測到循環依賴，已移除一條依賴邊以完成分析',
                'source_task_id': source,
                'target_task_id': target,
            }
        )

    if removed_cycle_edges:
        cycle_task_ids = sorted({task_id for edge in removed_cycle_edges for task_id in edge})
        warnings.append(
            {
                'code': 'cycle_detected',
                'message': '偵測到循環依賴，結果已降級為近似值',
                'task_ids': cycle_task_ids,
            }
        )

    topo_nodes = list(nx.topological_sort(graph)) if graph.nodes else []
    earliest_start = {}
    earliest_finish = {}

    for task_id in topo_nodes:
        predecessor_ids = list(graph.predecessors(task_id))
        predecessor_finish = [earliest_finish[item] for item in predecessor_ids]
        node_es = max(predecessor_finish) if predecessor_finish else 0
        node_duration = node_meta[task_id]['duration_days']
        earliest_start[task_id] = node_es
        earliest_finish[task_id] = node_es + node_duration

    projected_duration_days = max(earliest_finish.values(), default=0)

    latest_start = {}
    latest_finish = {}
    for task_id in reversed(topo_nodes):
        successor_ids = list(graph.successors(task_id))
        successor_start = [latest_start[item] for item in successor_ids]
        node_lf = min(successor_start) if successor_start else projected_duration_days
        node_duration = node_meta[task_id]['duration_days']
        latest_finish[task_id] = node_lf
        latest_start[task_id] = node_lf - node_duration

    best_length = {}
    best_previous = {}
    for task_id in topo_nodes:
        predecessor_ids = list(graph.predecessors(task_id))
        if predecessor_ids:
            best_pred = max(predecessor_ids, key=lambda item: best_length[item])
            best_length[task_id] = best_length[best_pred] + node_meta[task_id]['duration_days']
            best_previous[task_id] = best_pred
        else:
            best_length[task_id] = node_meta[task_id]['duration_days']
            best_previous[task_id] = None

    critical_path_task_ids = []
    if best_length:
        cursor = max(best_length, key=lambda task_id: best_length[task_id])
        while cursor is not None:
            critical_path_task_ids.append(cursor)
            cursor = best_previous[cursor]
        critical_path_task_ids.reverse()

    critical_task_id_set = set(critical_path_task_ids)

    for task_id in topo_nodes:
        float_days = latest_start[task_id] - earliest_start[task_id]
        node_meta[task_id]['earliest_start'] = earliest_start[task_id]
        node_meta[task_id]['earliest_finish'] = earliest_finish[task_id]
        node_meta[task_id]['latest_start'] = latest_start[task_id]
        node_meta[task_id]['latest_finish'] = latest_finish[task_id]
        node_meta[task_id]['float_days'] = max(float_days, 0)

    today = datetime.now(timezone.utc).date()
    risk_items = []
    for task_id in topo_nodes:
        meta = node_meta[task_id]
        task = meta['task']
        if task.completed:
            continue

        reasons = []
        severity = 'low'
        impact_days = 0

        is_critical = task_id in critical_task_id_set
        if is_critical:
            reasons.append('位於關鍵路徑，延誤會直接影響總工期')
            severity = _severity_max(severity, 'high')
            impact_days = max(impact_days, 1)

        due_date = meta['end_date']
        is_overdue = bool(due_date and due_date < today)
        if is_overdue:
            overdue_days = (today - due_date).days
            reasons.append(f'已逾期 {overdue_days} 天')
            severity = _severity_max(severity, 'high')
            impact_days = max(impact_days, overdue_days)

        if not is_critical and meta['float_days'] <= 2:
            reasons.append(f'緩衝僅剩 {meta["float_days"]} 天')
            severity = _severity_max(severity, 'medium')
            impact_days = max(impact_days, 1)

        if meta['is_schedule_incomplete']:
            reasons.append('缺少完整起訖日期，風險估算可信度較低')
            severity = _severity_max(severity, 'medium')
            impact_days = max(impact_days, 1)

        if not reasons:
            continue

        risk_items.append(
            {
                'task_id': task_id,
                'name': task.name,
                'severity': severity,
                'impact_days': impact_days,
                'reasons': reasons,
                'suggested_actions': _suggest_actions(
                    is_critical=is_critical,
                    is_overdue=is_overdue,
                    is_schedule_incomplete=meta['is_schedule_incomplete'],
                ),
                'due_date': due_date.isoformat() if due_date else None,
                'depends_on_task_ids': list(meta['depends_on_task_ids']),
                'float_days': meta['float_days'],
                'is_critical': is_critical,
            }
        )

    risk_items.sort(
        key=lambda item: (
            -SEVERITY_RANK[item['severity']],
            -item['impact_days'],
            item['task_id'],
        )
    )

    critical_path = []
    for task_id in critical_path_task_ids:
        meta = node_meta[task_id]
        task = meta['task']
        critical_path.append(
            {
                'task_id': task_id,
                'name': task.name,
                'start_date': meta['start_date'].isoformat() if meta['start_date'] else None,
                'end_date': meta['end_date'].isoformat() if meta['end_date'] else None,
                'duration_days': meta['duration_days'],
                'earliest_start': meta['earliest_start'],
                'earliest_finish': meta['earliest_finish'],
                'latest_start': meta['latest_start'],
                'latest_finish': meta['latest_finish'],
                'float_days': meta['float_days'],
                'is_completed': bool(task.completed),
                'depends_on_task_ids': list(meta['depends_on_task_ids']),
            }
        )

    graph_nodes = []
    for task_id in sorted(topo_nodes, key=lambda item: (node_meta[item]['earliest_start'], item)):
        meta = node_meta[task_id]
        task = meta['task']
        graph_nodes.append(
            {
                'task_id': task_id,
                'name': task.name,
                'status': task.status,
                'start_date': meta['start_date'].isoformat() if meta['start_date'] else None,
                'end_date': meta['end_date'].isoformat() if meta['end_date'] else None,
                'duration_days': meta['duration_days'],
                'float_days': meta['float_days'],
                'is_critical': task_id in critical_task_id_set,
                'depends_on_task_ids': list(meta['depends_on_task_ids']),
            }
        )

    critical_edges = {
        (critical_path_task_ids[index], critical_path_task_ids[index + 1])
        for index in range(len(critical_path_task_ids) - 1)
    }
    graph_edges = []
    for source_task_id, target_task_id in sorted(graph.edges()):
        graph_edges.append(
            {
                'source_task_id': source_task_id,
                'target_task_id': target_task_id,
                'is_critical': (source_task_id, target_task_id) in critical_edges,
            }
        )

    high_risk_count = len([item for item in risk_items if item['severity'] == 'high'])

    return {
        'timeline_id': timeline.id,
        'timeline_name': timeline.name,
        'generated_at': _utc_iso_now(),
        'summary': {
            'total_tasks': len(tasks),
            'projected_duration_days': projected_duration_days,
            'critical_path_task_count': len(critical_path),
            'critical_path_duration_days': sum(item['duration_days'] for item in critical_path),
            'risk_item_count': len(risk_items),
            'high_risk_count': high_risk_count,
            'warning_count': len(warnings),
        },
        'critical_path': critical_path,
        'risk_items': risk_items,
        'warnings': warnings,
        'graph': {
            'nodes': graph_nodes,
            'edges': graph_edges,
        },
    }
