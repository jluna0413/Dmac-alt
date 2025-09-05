from src.mcp_adapter.client import ByteroverClient


def test_endpoints_create_and_update(tmp_path, stub_server):
    client = ByteroverClient(endpoint=stub_server, offline_dir=str(tmp_path))

    # create project
    pr = client.byterover_create_project('proj-1', description='desc')
    assert pr.get('ok') is True
    assert 'project' in pr

    # create task
    t = client.byterover_create_task('proj-1', 'task-1', description='task desc', assignee='me', task_order=1)
    assert t.get('ok') is True
    assert 'task' in t

    # save implementation plan
    plan = client.byterover_save_implementation_plan({'title': 'plan-1', 'items': []})
    assert plan.get('ok') is True

    # update plan progress
    upd = client.byterover_update_plan_progress('proj-1', task_name='task-1', is_completed=True)
    assert isinstance(upd, dict)

    # store knowledge
    sk = client.byterover_store_knowledge('a short knowledge message')
    assert sk.get('ok') is True

    # retrieve knowledge (stub returns empty results)
    rk = client.byterover_retrieve_knowledge('query', limit=2)
    assert isinstance(rk, dict)
    assert 'results' in rk

