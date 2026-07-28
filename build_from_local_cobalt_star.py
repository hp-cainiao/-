#!/usr/bin/env python3
"""Build a YueXinMiaoPet-style repository package from the installed Cobalt Star pet."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


CELL_WIDTH = 192
CELL_HEIGHT = 208
PET_ID = "cobalt-star"
DEFAULT_PETS_ROOT = Path.home() / ".codex" / "pets"

STATE_SPECS = [
    ("idle", 6),
    ("running-right", 8),
    ("running-left", 8),
    ("waving", 4),
    ("jumping", 5),
    ("failed", 8),
    ("waiting", 6),
    ("running", 6),
    ("review", 6),
]

LOOK_LABELS = [
    "000-up",
    "022.5-up-right",
    "045-up-right",
    "067.5-up-right",
    "090-right",
    "112.5-down-right",
    "135-down-right",
    "157.5-down-right",
    "180-down",
    "202.5-down-left",
    "225-down-left",
    "247.5-down-left",
    "270-left",
    "292.5-up-left",
    "315-up-left",
    "337.5-up-left",
]


def clear_transparent_rgb(image: Image.Image) -> Image.Image:
    rgba = image.convert("RGBA")
    data = bytearray(rgba.tobytes())
    for index in range(0, len(data), 4):
        if data[index + 3] == 0:
            data[index] = data[index + 1] = data[index + 2] = 0
    return Image.frombytes("RGBA", rgba.size, bytes(data))


def checker(size: tuple[int, int], square: int = 12) -> Image.Image:
    image = Image.new("RGBA", size, (250, 250, 250, 255))
    draw = ImageDraw.Draw(image)
    for y in range(0, size[1], square):
        for x in range(0, size[0], square):
            if ((x // square) + (y // square)) % 2:
                draw.rectangle((x, y, x + square - 1, y + square - 1), fill=(226, 232, 241, 255))
    return image


def cell_from_atlas(atlas: Image.Image, row: int, column: int) -> Image.Image:
    return clear_transparent_rgb(
        atlas.crop(
            (
                column * CELL_WIDTH,
                row * CELL_HEIGHT,
                (column + 1) * CELL_WIDTH,
                (row + 1) * CELL_HEIGHT,
            )
        )
    )


def nontransparent_pixels(image: Image.Image) -> int:
    return sum(image.getchannel("A").histogram()[1:])


def detected_state_counts(atlas: Image.Image) -> list[int]:
    counts: list[int] = []
    for row, (_state, expected_count) in enumerate(STATE_SPECS):
        last_nonempty = -1
        for column in range(8):
            if nontransparent_pixels(cell_from_atlas(atlas, row, column)):
                last_nonempty = column
        counts.append(max(expected_count, last_nonempty + 1))
    return counts


def save_preview_gif(path: Path, frames: list[Image.Image], duration: int = 110) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    gif_frames: list[Image.Image] = []
    for frame in frames:
        canvas = checker((CELL_WIDTH, CELL_HEIGHT))
        canvas.alpha_composite(frame)
        gif_frames.append(canvas.convert("P", palette=Image.Palette.ADAPTIVE))
    gif_frames[0].save(path, save_all=True, append_images=gif_frames[1:], duration=duration, loop=0, disposal=2)


def make_contact_sheet(atlas: Image.Image, output: Path, state_counts: list[int], *, rows: int = 9) -> None:
    thumb_w, thumb_h, label_h = 96, 104, 22
    sheet = Image.new("RGB", (thumb_w * 8, (thumb_h + label_h) * rows), "#F7F9FD")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for row in range(rows):
        state, count = (STATE_SPECS[row][0], state_counts[row]) if row < len(STATE_SPECS) else (f"look-{row}", 8)
        y = row * (thumb_h + label_h)
        draw.rectangle((0, y, thumb_w * 8, y + label_h - 1), fill="#0F172A")
        draw.text((6, y + 5), f"{state} ({count})", fill="white", font=font)
        for column in range(8):
            x = column * thumb_w
            bg = checker((thumb_w, thumb_h), square=8)
            cell = cell_from_atlas(atlas, row, column).resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
            bg.alpha_composite(cell)
            sheet.paste(bg.convert("RGB"), (x, y + label_h))
            draw.rectangle((x, y + label_h, x + thumb_w - 1, y + label_h + thumb_h - 1), outline="#3B82F6" if column < count else "#CBD5E1")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def make_direction_sheet(atlas: Image.Image, output: Path) -> None:
    thumb_w, thumb_h = 144, 156
    label_h = 24
    sheet = Image.new("RGB", (thumb_w * 4, (thumb_h + label_h) * 4), "#F8FAFC")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for idx, label in enumerate(LOOK_LABELS):
        row = 9 if idx < 8 else 10
        col = idx if idx < 8 else idx - 8
        grid_x = idx % 4
        grid_y = idx // 4
        x = grid_x * thumb_w
        y = grid_y * (thumb_h + label_h)
        draw.rectangle((x, y, x + thumb_w - 1, y + label_h - 1), fill="#172554")
        draw.text((x + 5, y + 6), label, fill="white", font=font)
        bg = checker((thumb_w, thumb_h), square=10)
        cell = cell_from_atlas(atlas, row, col)
        cell.thumbnail((thumb_w - 10, thumb_h - 10), Image.Resampling.LANCZOS)
        bg.alpha_composite(cell, ((thumb_w - cell.width) // 2, (thumb_h - cell.height) // 2))
        sheet.paste(bg.convert("RGB"), (x, y + label_h))
        draw.rectangle((x, y + label_h, x + thumb_w - 1, y + label_h + thumb_h - 1), outline="#93C5FD")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)


def validate_atlas(atlas: Image.Image, output: Path, state_counts: list[int]) -> dict[str, object]:
    errors: list[str] = []
    warnings: list[str] = []
    if atlas.size != (CELL_WIDTH * 8, CELL_HEIGHT * 11):
        errors.append(f"expected 1536x2288, got {atlas.width}x{atlas.height}")

    data = atlas.tobytes()
    residue = sum(1 for index in range(0, len(data), 4) if data[index + 3] == 0 and (data[index] or data[index + 1] or data[index + 2]))
    if residue:
        errors.append("transparent pixels contain RGB residue")

    cells = []
    for row in range(11):
        for column in range(8):
            cell = cell_from_atlas(atlas, row, column)
            nontransparent = nontransparent_pixels(cell)
            used = row >= 9 or column < state_counts[row]
            if used and nontransparent == 0:
                errors.append(f"row {row} frame {column:02d} is empty")
            if not used and nontransparent:
                errors.append(f"row {row} unused frame {column:02d} is not transparent")
            cells.append({"row": row, "column": column, "used": used, "nontransparent_pixels": nontransparent})

    result = {
        "ok": not errors,
        "format": "WEBP",
        "mode": "RGBA",
        "width": atlas.width,
        "height": atlas.height,
        "cell_width": CELL_WIDTH,
        "cell_height": CELL_HEIGHT,
        "rows": 11,
        "columns": 8,
        "spriteVersionNumber": 2,
        "transparent_rgb_residue_pixels": residue,
        "errors": errors,
        "warnings": warnings,
        "cells": cells,
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    root = Path(__file__).resolve().parent
    source_pet_dir = Path(os.environ.get("COBALT_STAR_SOURCE", DEFAULT_PETS_ROOT / PET_ID))
    source_spritesheet = source_pet_dir / "spritesheet.webp"
    source_pet_json = source_pet_dir / "pet.json"
    if not source_spritesheet.is_file() or not source_pet_json.is_file():
        raise SystemExit(f"missing installed Cobalt Star pet files under {source_pet_dir}")

    run_dir = root / "hatch-cobalt-star"
    final_dir = run_dir / "final"
    qa_dir = run_dir / "qa"
    previews_dir = qa_dir / "previews"
    frames_dir = run_dir / "frames"
    for directory in (final_dir, qa_dir, previews_dir, frames_dir):
        directory.mkdir(parents=True, exist_ok=True)

    with Image.open(source_spritesheet) as opened:
        atlas = clear_transparent_rgb(opened.convert("RGBA"))
    pet_json = json.loads(source_pet_json.read_text(encoding="utf-8"))
    state_counts = detected_state_counts(atlas)

    shutil.copy2(source_spritesheet, final_dir / "spritesheet.webp")
    shutil.copy2(source_pet_json, final_dir / "pet.json")

    frame_manifest = []
    for row, (state, _expected_count) in enumerate(STATE_SPECS):
        count = state_counts[row]
        frames = [cell_from_atlas(atlas, row, column) for column in range(count)]
        state_dir = frames_dir / state
        state_dir.mkdir(parents=True, exist_ok=True)
        frame_paths = []
        for index, frame in enumerate(frames):
            frame_path = state_dir / f"{index:02d}.png"
            frame.save(frame_path)
            frame_paths.append(str(frame_path))
        save_preview_gif(root / f"{state}.gif", frames)
        save_preview_gif(previews_dir / f"{state}.gif", frames)
        frame_manifest.append({"state": state, "row": row, "frames": frame_paths, "frame_count": count})

    make_contact_sheet(atlas, qa_dir / "contact-sheet.png", state_counts, rows=9)
    make_contact_sheet(atlas, qa_dir / "contact-sheet-extended.png", state_counts, rows=11)
    make_direction_sheet(atlas, qa_dir / "look-directions.png")
    validation = validate_atlas(atlas, final_dir / "validation.json", state_counts)

    pet_request = {
        "pet_id": pet_json.get("id", PET_ID),
        "display_name": pet_json.get("displayName", "钴星"),
        "description": pet_json.get("description", ""),
        "source": str(source_pet_dir),
        "cell": {"width": CELL_WIDTH, "height": CELL_HEIGHT},
        "states": [{"state": state, "frames": state_counts[row], "standard_frames": count} for row, (state, count) in enumerate(STATE_SPECS)],
        "spriteVersionNumber": 2,
    }
    (run_dir / "pet_request.json").write_text(json.dumps(pet_request, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (frames_dir / "frames-manifest.json").write_text(json.dumps({"ok": True, "rows": frame_manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "ok": validation["ok"],
        "source_pet_dir": str(source_pet_dir),
        "run_dir": str(run_dir),
        "spritesheet": str(final_dir / "spritesheet.webp"),
        "pet_json": str(final_dir / "pet.json"),
        "validation": str(final_dir / "validation.json"),
        "contact_sheet": str(qa_dir / "contact-sheet.png"),
        "extended_contact_sheet": str(qa_dir / "contact-sheet-extended.png"),
        "look_directions": str(qa_dir / "look-directions.png"),
        "previews": str(previews_dir),
    }
    (qa_dir / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
