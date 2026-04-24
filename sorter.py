#!/usr/bin/env python3
"""
File Sorter
Sorts files in configured folders based on settings.jsonc.
Works on NixOS/Linux. Folder icons are set by copying a PNG to
.foldericon.png inside the target folder.

Dependencies (pip install):
  commentjson   - for JSONC parsing (used by lib.py)
  send2trash    - optional, for nicer TRASH support
"""

import json
import os
import re
from socket import SO_J1939_ERRQUEUE
import sys
import time
import shutil
import hashlib
from pathlib import Path
from typing import Optional

# ── Import from lib.py (must be in the same directory) ────────────────────────
_SCRIPT_DIR = Path(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(_SCRIPT_DIR))

from lib import json as libJson, f # noqa: E402

# lib.py replaces builtins.print; grab it after import
from lib import print # noqa: E402

# ── Constants ─────────────────────────────────────────────────────────────────
SCRIPT_DIR = _SCRIPT_DIR
CONFIG_FILE = SCRIPT_DIR / "settings.jsonc"
ICONS_DIR = SCRIPT_DIR / "icons" # put your .png icons here
FOLDER_ICON_NAME = ".foldericon.png"

# Special sort_folders keys (not real extensions)
_SPECIAL_KEYS = {"TRASH", "UNMOVED", "FOLDER", ""}


# ── Helpers ───────────────────────────────────────────────────────────────────


def _load_config() -> dict:
  """Load settings.jsonc and resolve all #include directives."""
  raw = f.read(str(CONFIG_FILE))
  config = libJson.parse(raw)
  config = libJson.parseincludes(config)
  f.write("a.json", text=libJson.str(config))
  return config


def _is_ignored(name: str, filepath: str, ignores: list) -> bool:
  """Return True if name/filepath matches any ignore rule."""
  for rule in ignores:
    if "#include" in rule and len(rule) == 1:
      continue # unresolved include - skip
    rule_type = rule.get("type", "plain")
    rule_in = rule.get("in", "filename")
    value = rule.get("value", "")
    ignorecase = rule.get("ignorecase", False)
    flags = re.IGNORECASE if ignorecase else 0
    target = name if rule_in == "filename" else filepath

    if rule_type == "regex":
      if re.search(value, target, flags):
        return True
    else: # plain
      cmp = (
        (lambda a, b: a.lower() == b.lower())
        if ignorecase
        else (lambda a, b: a == b)
      )
      if cmp(target, value):
        return True
  return False


def _files_identical(a: Path, b: Path) -> bool:
  """True when a and b have the same size and MD5."""
  if a.stat().st_size != b.stat().st_size:
    return False
  return (
    hashlib.md5(a.read_bytes()).hexdigest()
    == hashlib.md5(b.read_bytes()).hexdigest()
  )


def _unique_dest(dst: Path) -> Path:
  """If dst exists, append _1, _2 … until we find a free name."""
  if not dst.exists():
    return dst
  stem, suffix, parent = dst.stem, dst.suffix, dst.parent
  counter = 1
  while True:
    candidate = parent / f"{stem}_{counter}{suffix}"
    if not candidate.exists():
      return candidate
    counter += 1


def _safe_move(src: Path, dst_dir: Path, delete_if_same: bool) -> None:
  """Move *src* into *dst_dir*, handling duplicates and deletes."""
  dst_dir.mkdir(parents=True, exist_ok=True)
  dst = _unique_dest(dst_dir / src.name)

  # If the exact name already exists, check for identical content
  plain = dst_dir / src.name
  if plain.exists() and delete_if_same and plain.is_file() and src.is_file():
    if _files_identical(src, plain):
      src.unlink()
      print.info(f"Deleted duplicate: {src.name}")
      return

  shutil.move(str(src), str(dst))
  print.success(f"Moved  {src.name}  →  {dst_dir}")


def _move_to_trash(path: Path) -> None:
  """Send *path* to the system trash (XDG on NixOS/Linux)."""
  try:
    import send2trash

    send2trash.send2trash(str(path))
    print.info(f"Trashed: {path.name}")
    return
  except ImportError:
    pass
  # Fallback: XDG Trash spec
  trash = Path.home() / ".local" / "share" / "Trash" / "files"
  trash.mkdir(parents=True, exist_ok=True)
  dst = _unique_dest(trash / path.name)
  shutil.move(str(path), str(dst))
  print.info(f"Trashed (XDG fallback): {path.name}")


def _get_extensions(path: Path) -> list[str]:
  """
  Return candidate extensions to look up, most-specific first.
  E.g. "archive.tar.gz" → ["tar.gz", "gz"]
  Hidden files (leading dot, no other dot) return [].
  """
  name = path.name
  if name.startswith(".") and name.count(".") == 1:
    return [] # pure dotfile, no extension
  parts = name.lstrip(".").split(".")
  if len(parts) < 2:
    return [""]
  exts: list[str] = []
  # multi-part (e.g. tar.gz)
  if len(parts) >= 3:
    exts.append(".".join(parts[-2:]).lower())
  exts.append(parts[-1].lower())
  return exts if exts else [""]


def _resolve_dest(
  extensions: list[str],
  sort_map: dict,
  base_path: Path,
  is_file: bool,
) -> Optional[tuple[Path, bool]]:
  """
  Return (destination_dir, is_trash) for the first matching extension.
  Returns None if nothing matched (caller may then try UNMOVED/FOLDER).
  """
  for ext in extensions:
    if ext not in sort_map:
      continue
    raw: str = sort_map[ext]
    if raw == "TRASH":
      return (base_path, True) # sentinel; caller calls _move_to_trash
    dest = Path(raw)
    if not dest.is_absolute():
      dest = base_path / dest
    return (dest, False)
  return None


def _all_items_share_dest(
  folder: Path,
  sort_map: dict,
  base_path: Path,
  ignores: list,
  dest_dirs: set[str],
  move_ext_as_files: bool,
) -> Optional[Path]:
  """
  If every item in *folder* would end up in the same destination return it,
  else return None. Also returns None for empty folders.
  """
  try:
    items = [
      i
      for i in folder.iterdir()
      if not _is_ignored(i.name, str(i), ignores)
      and i.name not in (FOLDER_ICON_NAME, "desktop.ini")
    ]
  except PermissionError:
    return None

  if not items:
    return None

  destinations: set[str] = set()

  for item in items:
    if item.is_file():
      exts = _get_extensions(item)
      result = _resolve_dest(exts, sort_map, base_path, is_file=True)
      if result is None:
        unmoved = sort_map.get("UNMOVED")
        if unmoved:
          result = (base_path / unmoved, False)
        else:
          return None
      if result[1]:
        return None # would trash - don't auto-move whole folder
      destinations.add(str(result[0]))

    elif item.is_dir():
      if move_ext_as_files:
        exts = _get_extensions(item)
        result = _resolve_dest(exts, sort_map, base_path, is_file=False)
      else:
        result = None

      if result is None:
        folder_dest = sort_map.get("FOLDER")
        if folder_dest:
          result = (base_path / folder_dest, False)
        else:
          unmoved = sort_map.get("UNMOVED")
          if unmoved:
            result = (base_path / unmoved, False)
          else:
            # Recurse into subfolder
            sub = _all_items_share_dest(
              item,
              sort_map,
              base_path,
              ignores,
              dest_dirs,
              move_ext_as_files,
            )
            if sub is None:
              return None
            destinations.add(str(sub))
            continue

      if result[1]:
        return None
      destinations.add(str(result[0]))

  if len(destinations) == 1:
    return Path(destinations.pop())
  return None


def _check_time(
  path: Path, min_secs: Optional[float], max_secs: Optional[float]
) -> bool:
  """True when the item's age satisfies the configured min/max time window."""
  if min_secs is None and max_secs is None:
    return True
  age = time.time() - path.stat().st_mtime
  if min_secs is not None and age < min_secs:
    return False
  if max_secs is not None and age > max_secs:
    return False
  return True


def _secs_until_moveable(items: list[Path], min_secs: float) -> float:
  """Seconds until the first deferred item becomes moveable."""
  now = time.time()
  return max(
    (min_secs - (now - p.stat().st_mtime) for p in items),
    default=0.0,
  )


def _apply_folder_icons(base_path: Path, folder_icons: dict, icons_dir: Path) -> None:
  """
  For every entry in folder_icons, if the folder exists under base_path,
  copy the matching PNG to <folder>/.foldericon.png.
  """
  for rel_folder, icon_name in folder_icons.items():
    folder_abs = base_path / rel_folder
    if not (folder_abs.exists() and folder_abs.is_dir()):
      continue

    # Candidates: icons_dir/<name>.png, icons_dir/<name>, script_dir/<name>.png …
    candidates = [
      icons_dir / f"{icon_name}.png",
      icons_dir / icon_name,
      SCRIPT_DIR / f"{icon_name}.png",
      SCRIPT_DIR / icon_name,
    ]
    found = False
    for candidate in candidates:
      if candidate.exists() and candidate.suffix.lower() == ".png":
        dst = folder_abs / FOLDER_ICON_NAME
        shutil.copy2(str(candidate), str(dst))
        print.debug(f"Icon set: {rel_folder}  ←  {candidate.name}")
        found = True
        break
    if not found:
      print.warn(
        f"Icon PNG not found for folder '{rel_folder}' (icon name: {icon_name})"
      )


def _remove_empty_dirs(base: Path, ignores: list) -> None:
  """
  Recursively delete directories that are empty (ignoring desktop.ini and
  .foldericon.png). Deepest dirs first so parents can become empty too.
  """
  for item in sorted(base.iterdir(), reverse=True):
    if not item.is_dir():
      continue
    if _is_ignored(item.name, str(item), ignores):
      continue
    _remove_empty_dirs(item, ignores)
    leftover = [
      c for c in item.iterdir() if c.name not in ("desktop.ini", FOLDER_ICON_NAME)
    ]
    if not leftover:
      shutil.rmtree(str(item))
      print.info(f"Removed empty dir: {item}")


# ── Core sort logic ───────────────────────────────────────────────────────────


def sort_folder(base_path: Path, settings: dict) -> None:
  """Sort everything directly inside *base_path* using *settings*."""
  sort_map: dict = settings.get("sort folders", {})
  ignores: list = settings.get("ignores", [])
  ignore_folders: list = settings.get("ignorefolders", [])
  move_ext_as_files: bool = settings.get(
    "move folders with extensions as files", False
  )
  move_if_same: bool = settings.get("move folders if all same inside", True)
  min_time: Optional[float] = settings.get("min time")
  max_time: Optional[float] = settings.get("max time")
  delete_if_same: bool = settings.get("delete file if same at dest", False)
  clear_empty: bool = settings.get("clear empty on run", False)
  folder_icons: dict = settings.get("folder icons", {})

  if not base_path.exists():
    print.error(f"Path does not exist: {base_path}")
    return

  if clear_empty:
    print.info("Clearing empty folders…")
    _remove_empty_dirs(base_path, ignores)

  # Build set of all destination dirs so we never move them
  dest_dirs: set[str] = set()
  for ext, dest_str in sort_map.items():
    if ext in _SPECIAL_KEYS or not dest_str or dest_str == "TRASH":
      continue
    dest_dirs.add(str((base_path / dest_str).resolve()))

  deferred: list[Path] = []

  try:
    items = list(base_path.iterdir())
  except PermissionError as e:
    print.error(f"Cannot read {base_path}: {e}")
    return

  for item in items:
    # ── Ignore rules ──────────────────────────────────────────────────────
    if _is_ignored(item.name, str(item), ignores):
      continue
    if item.name in ignore_folders:
      continue
    if str(item.resolve()) in dest_dirs:
      continue # don't move a destination folder into itself
    if item.name in ("desktop.ini", FOLDER_ICON_NAME):
      continue

    # ── Directories ───────────────────────────────────────────────────────
    if item.is_dir():
      dest: Optional[Path] = None

      # 1. "move folders if all same inside"
      if move_if_same:
        dest = _all_items_share_dest(
          item, sort_map, base_path, ignores, dest_dirs, move_ext_as_files
        )

      # 2. "move folders with extensions as files"
      if dest is None and move_ext_as_files:
        exts = _get_extensions(item)
        result = _resolve_dest(exts, sort_map, base_path, is_file=False)
        if result:
          dest_path, is_trash = result
          if not _check_time(item, min_time, max_time):
            deferred.append(item)
            continue
          if is_trash:
            _move_to_trash(item)
          else:
            _safe_move(item, dest_path, delete_if_same)
          continue

      # 3. FOLDER catch-all
      if dest is None:
        folder_dest = sort_map.get("FOLDER")
        if folder_dest:
          dest = base_path / folder_dest

      # 4. UNMOVED catch-all
      if dest is None:
        unmoved = sort_map.get("UNMOVED")
        if unmoved:
          dest = base_path / unmoved

      if dest is not None:
        if not _check_time(item, min_time, max_time):
          deferred.append(item)
          continue
        _safe_move(item, dest, delete_if_same)

    # ── Files ─────────────────────────────────────────────────────────────
    elif item.is_file():
      exts = _get_extensions(item)

      # "" extension = file with no extension at all
      if not exts:
        exts = [""]

      result = _resolve_dest(exts, sort_map, base_path, is_file=True)

      if result is None:
        unmoved = sort_map.get("UNMOVED")
        result = (base_path / unmoved, False) if unmoved else None

      if result is None:
        print.debug(f"No rule for: {item.name}")
        continue

      dest_path, is_trash = result

      if not _check_time(item, min_time, max_time):
        deferred.append(item)
        continue

      if is_trash:
        _move_to_trash(item)
      else:
        _safe_move(item, dest_path, delete_if_same)

  # ── Folder icons ──────────────────────────────────────────────────────────
  _apply_folder_icons(base_path, folder_icons, ICONS_DIR)

  # ── Deferred items (min/max time) ─────────────────────────────────────────
  if deferred and min_time is not None:
    wait = _secs_until_moveable(deferred, min_time) + 0.5
    print.info(f"{len(deferred)} item(s) deferred — retrying in {wait:.1f}s…")
    time.sleep(wait)
    sort_folder(base_path, settings) # recurse once items are old enough


# ── Entry point ───────────────────────────────────────────────────────────────


if not CONFIG_FILE.exists():
  print.error(f"Config not found: {CONFIG_FILE}")
  sys.exit(1)

config = _load_config()
paths_to_watch: list[dict] = config.get("paths to watch", [])

if not paths_to_watch:
  print.warn("No paths configured in 'paths to watch'.")
  os._exit(1)

for entry in paths_to_watch:
  raw_path = entry.get("path", "")
  settings = entry.get("settings", {})

  # Expand ~ and env vars; make absolute
  base_path = Path(os.path.expandvars(os.path.expanduser(raw_path))).resolve()

  print.info(f"\nSorting: {base_path}")
  sort_folder(base_path, settings)

print.success("\nAll done!")

