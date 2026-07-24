from __future__ import annotations

from types import SimpleNamespace

from hermes_cli import auth


def _stat(uid: int, gid: int):
    return SimpleNamespace(st_uid=uid, st_gid=gid)


def test_root_auth_write_prefers_existing_non_root_file_owner() -> None:
    assert auth._select_auth_store_owner_ids(_stat(1001, 1001), _stat(1002, 1002)) == (
        1001,
        1001,
    )


def test_root_auth_write_repairs_root_owned_file_from_non_root_parent() -> None:
    assert auth._select_auth_store_owner_ids(_stat(0, 0), _stat(1001, 1001)) == (
        1001,
        1001,
    )


def test_root_auth_write_keeps_root_owner_under_root_home() -> None:
    assert auth._select_auth_store_owner_ids(_stat(0, 0), _stat(0, 0)) == (0, 0)


def test_save_auth_store_applies_selected_owner_to_temp_and_final(
    tmp_path,
    monkeypatch,
) -> None:
    auth_path = tmp_path / "auth.json"
    calls: list[tuple[str, tuple[int, int] | None]] = []

    monkeypatch.setattr(auth, "_auth_file_path", lambda: auth_path)
    monkeypatch.setattr(
        auth,
        "_auth_store_owner_ids_for_root_write",
        lambda path: (1001, 1001) if path == auth_path else None,
    )
    monkeypatch.setattr(
        auth,
        "_apply_auth_store_owner",
        lambda path, owner_ids: calls.append((path.name, owner_ids)),
    )

    saved = auth._save_auth_store({"providers": {}})

    assert saved == auth_path
    assert any(
        name.startswith("auth.json.tmp.") and owner_ids == (1001, 1001)
        for name, owner_ids in calls
    )
    assert ("auth.json", (1001, 1001)) in calls
    assert auth_path.exists()


def test_auth_store_lock_repairs_the_selected_target_lock(
    tmp_path,
    monkeypatch,
) -> None:
    target_path = tmp_path / "profile" / "auth.json"
    repaired: list[object] = []

    monkeypatch.setattr(
        auth,
        "_repair_auth_lock_owner_for_root",
        lambda lock_path=None: repaired.append(lock_path),
    )

    with auth._auth_store_lock(target_path=target_path):
        pass

    assert repaired == [target_path.with_suffix(".lock")]
