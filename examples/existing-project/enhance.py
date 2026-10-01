"""Optional intelligence around an existing parser; preserve its API and source."""
import argparse
import hashlib
import json
from pathlib import Path

from parser import parse


def enhance(input_path, output_path, profile_path=None):
    parser_path = Path(__file__).with_name("parser.py")
    baseline = hashlib.sha256(parser_path.read_bytes()).hexdigest()
    source = input_path.read_bytes()
    result = {"parsed": parse(source.decode("utf-8")), "intelligence": None, "parser_sha256": baseline}
    if profile_path is not None:
        from awb_core.contracts import AWBError, read_json
        from awb_core.execution import execute_node, Budget
        from awb_core.intelligence import compile_profile
        profile = read_json(profile_path)
        config = compile_profile(profile)
        if config["mode"] not in {"noninteractive", "mixed"}:
            raise AWBError("configuration", "Choose a noninteractive profile or --no-intelligence")
        config.update(id="annotation", sandbox="read-only", workspace_write_authorized=False,
            output_schema={"type": "object", "properties": {"summary": {"type": "string"}, "uncertainties": {"type": "array", "items": {"type": "string"}}},
                           "required": ["summary", "uncertainties"], "additionalProperties": False})
        execution = execute_node(config, {"instruction": "Annotate this parser result without modifying code. State uncertainty.", "parsed": result["parsed"]},
            {"workspace": output_path.parent / "annotation-attempts"}, Budget(profile["budget"]["max_calls"], profile["budget"]["max_seconds"]))
        result["intelligence"] = {"execution_status": execution["status"], "annotation": execution["result"],
                                  "semantic_acceptance": "requires_user_or_domain_verification"}
    if hashlib.sha256(parser_path.read_bytes()).hexdigest() != baseline or input_path.read_bytes() != source:
        raise RuntimeError("Existing parser or input drifted; preserve files and reconcile")
    output_path.write_text(json.dumps(result, ensure_ascii=False) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--profile", type=Path)
    choice.add_argument("--no-intelligence", action="store_true")
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Input and output must be distinct")
    enhance(args.input, args.output, args.profile)
