"""Sequence preflight, Git, store routing, transfer and final publication."""
from .worksets import plan_launch, execute_repositories
from .workset_stores import plan_stores, prepare_stores
from .workset_transfer import plan_transfer, copy_change, finish_transfer


def launch(adapter, source, branch, overrides, *, name=None, change=None, store=None, keep_source=False):
    result = {"ok": False, "stage": "preflight", "name": name, "members": [],
              "stores": [], "effects": [], "transfer": None, "workspace_ready": False, "errors": []}
    try:
        plan = plan_launch(adapter, source, branch, overrides, name=name)
        result["name"] = plan.name
        stores, pointers, roots, views = plan_stores(adapter, plan)
        transfer = plan_transfer(adapter, plan, roots, views, change, store, keep_source)
        if transfer:
            result["transfer"] = {"action": "pending", "source": transfer.source, "destination": transfer.destination}
        result["stores"] = [{"original_id": s.original_id, "id": s.identity, "path": s.destination} for s in stores]
        result["stage"] = "worktrees"
        execute_repositories(plan, result["members"])
        result["stage"] = "stores"
        prepare_stores(adapter, stores, pointers, result["effects"])
        result["stage"] = "transfer"
        result["transfer"] = copy_change(adapter, transfer, result["transfer"])
        result["stage"] = "publication"
        adapter.publish(plan.output)
        result["workspace_ready"] = True
        result["opening_command"] = f"openspec workset open {plan.name} --tool code"
        result["stage"] = "cleanup"
        finish_transfer(transfer, result["transfer"])
        result["stage"] = "complete"
        result["ok"] = True
    except (ValueError, OSError) as error:
        if result["stage"] == "cleanup" and result["transfer"]:
            result["transfer"]["action"] = "cleanup-incomplete"
        result["errors"].append(str(error))
    return result
