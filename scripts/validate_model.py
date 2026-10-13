"""Read-only Cubism package checks. A pass is not a rendering-quality result."""

import argparse
import hashlib
import json
from pathlib import Path


def validate(model_path):
    model_path = Path(model_path).resolve()
    root = model_path.parent
    errors, warnings, files = [], [], {}

    def read_json(path):
        try:
            value = json.loads(path.read_text(encoding="utf-8-sig"))
            if not isinstance(value, dict):
                raise ValueError("expected a JSON object")
            return value
        except (OSError, ValueError) as exc:
            errors.append(f"{path.name}: {exc}")
            return {}

    def check_file(name, kind):
        if not isinstance(name, str) or not name:
            errors.append(f"{kind}: missing or invalid filename")
            return
        path = (root / name).resolve()
        if Path(name).is_absolute() or not path.is_relative_to(root):
            errors.append(f"{kind}: reference is outside package: {name}")
            return
        try:
            if not path.is_file() or path.stat().st_size == 0:
                raise ValueError("file missing or empty")
            with path.open("rb") as stream:
                signature = stream.read(4)
                stream.seek(0)
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            files[name] = {"bytes": path.stat().st_size, "sha256": digest}
            if kind == "Moc" and signature != b"MOC3":
                errors.append(f"{name}: invalid MOC3 signature")
            if name.lower().endswith(".json"):
                value = read_json(path)
                if kind == "Motion":
                    curves = value.get("Curves")
                    meta = value.get("Meta", {})
                    if not isinstance(curves, list) or not isinstance(meta, dict):
                        errors.append(f"{name}: invalid motion Curves/Meta")
                    elif meta.get("CurveCount") != len(curves):
                        errors.append(f"{name}: CurveCount does not match Curves")
        except (OSError, ValueError) as exc:
            errors.append(f"{name}: {exc}")

    model = read_json(model_path)
    check_file(model_path.name, "Model")
    if model.get("Version") != 3:
        errors.append("model: expected Cubism model3 Version 3")
    refs = model.get("FileReferences", {})
    if not isinstance(refs, dict):
        errors.append("model: FileReferences must be an object")
        refs = {}
    check_file(refs.get("Moc"), "Moc")
    textures = refs.get("Textures")
    if not isinstance(textures, list) or not textures:
        errors.append("model: Textures must be a nonempty array")
    else:
        for name in textures:
            check_file(name, "Texture")
    for kind in ("Physics", "Pose", "DisplayInfo", "UserData"):
        if kind in refs:
            check_file(refs[kind], kind)
    groups = refs.get("Motions", {})
    if not isinstance(groups, dict):
        errors.append("model: Motions must be an object")
        groups = {}
    for group, motions in groups.items():
        if not isinstance(motions, list):
            errors.append(f"Motions.{group}: expected an array")
            continue
        for motion in motions:
            check_file(motion.get("File") if isinstance(motion, dict) else None, "Motion")
            if isinstance(motion, dict) and "Sound" in motion:
                check_file(motion["Sound"], "Sound")
    expressions = refs.get("Expressions", [])
    if not isinstance(expressions, list):
        errors.append("model: Expressions must be an array")
    else:
        for expression in expressions:
            check_file(expression.get("File") if isinstance(expression, dict) else None, "Expression")
    if "Physics" not in refs:
        warnings.append("No Physics reference; physics was not verified.")
    if not groups:
        warnings.append("No motion groups; animations were not verified.")
    stem = model_path.name.removesuffix(".model3.json")
    diagnostic_path = root / f"{stem}.psd2live.json"
    if diagnostic_path.is_file():
        diagnostic = read_json(diagnostic_path)
        diagnostic_warnings = diagnostic.get("warnings", [])
        warnings.append({"diagnostic": diagnostic_path.name, "summary": diagnostic.get("summary"),
                         "warning_count": len(diagnostic_warnings) if isinstance(diagnostic_warnings, list) else None})
    return {"model": str(model_path), "structural_pass": not errors,
            "rendering_verified": False, "motion_groups": list(groups),
            "files": files, "errors": errors, "warnings": warnings}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path, help="Path to a .model3.json file")
    args = parser.parse_args()
    result = validate(args.model)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["structural_pass"] else 1)


if __name__ == "__main__":
    main()
