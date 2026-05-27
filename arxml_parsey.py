from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List
import xml.etree.ElementTree as ET

import xmltodict


VALUE_CONTAINER_KEYS = (
    "ECUC-REFERENCE-VALUE",
    "ECUC-NUMERICAL-PARAM-VALUE",
    "ECUC-TEXTUAL-PARAM-VALUE",
)


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def node_text(value: Any) -> str:
    if isinstance(value, dict):
        if "#text" in value:
            return str(value["#text"])
        return ""
    if value is None:
        return ""
    return str(value)


def extract_definition_value(item: Dict[str, Any]) -> str:
    value_ref = item.get("VALUE-REF")
    if value_ref is not None:
        return node_text(value_ref)
    return node_text(item.get("VALUE"))


def iter_dict_nodes(node: Any) -> Iterator[Dict[str, Any]]:
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from iter_dict_nodes(value)
        return
    if isinstance(node, list):
        for item in node:
            yield from iter_dict_nodes(item)


def iter_module_containers(arxml_dict: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for node in iter_dict_nodes(arxml_dict):
        module_values = node.get("ECUC-MODULE-CONFIGURATION-VALUES")
        for module_value in as_list(module_values):
            if not isinstance(module_value, dict):
                continue
            containers = module_value.get("CONTAINERS", {})
            for container in as_list(containers.get("ECUC-CONTAINER-VALUE")):
                if isinstance(container, dict):
                    yield container


def walk_container(container: Dict[str, Any], depth: int, lines: List[str]) -> None:
    short_name = str(container.get("SHORT-NAME", "")).strip()
    if short_name:
        lines.append(f"{'#' * depth} {short_name}")

    sub_containers = container.get("SUB-CONTAINERS", {})
    children = as_list(sub_containers.get("ECUC-CONTAINER-VALUE"))
    if children:
        for child in children:
            if isinstance(child, dict):
                walk_container(child, depth + 1, lines)
        return

    for field_name in ("REFERENCE-VALUES", "PARAMETER-VALUES"):
        field_data = container.get(field_name)
        if not isinstance(field_data, dict):
            continue
        for value_key in VALUE_CONTAINER_KEYS:
            for item in as_list(field_data.get(value_key)):
                if not isinstance(item, dict):
                    continue
                definition = node_text(item.get("DEFINITION-REF"))
                definition_value = extract_definition_value(item)
                if definition:
                    lines.append(f"{'#' * (depth + 1)} {definition}")
                if definition_value:
                    lines.append(f"{'#' * (depth + 2)} {definition_value}")


def local_tag_name(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def extract_short_name_hierarchy(arxml_path: Path) -> List[str]:
    tree = ET.parse(arxml_path)
    root = tree.getroot()
    lines: List[str] = []

    def walk(element: ET.Element, depth: int) -> None:
        short_name_value = ""
        for child in element:
            if local_tag_name(child.tag) == "SHORT-NAME":
                short_name_value = (child.text or "").strip()
                break

        next_depth = depth
        if short_name_value:
            lines.append(f"{'#' * depth} {short_name_value}")
            next_depth = depth + 1

        for child in element:
            if local_tag_name(child.tag) == "SHORT-NAME":
                continue
            walk(child, next_depth)

    walk(root, 1)
    return lines


def arxml_to_markdown(arxml_path: Path, output_path: Path) -> None:
    with arxml_path.open("r", encoding="utf-8") as source_file:
        arxml_dict = xmltodict.parse(source_file.read())

    markdown_lines: List[str] = []
    for root_container in iter_module_containers(arxml_dict):
        walk_container(root_container, depth=1, lines=markdown_lines)

    if not markdown_lines:
        markdown_lines = extract_short_name_hierarchy(arxml_path)

    if not markdown_lines:
        raise ValueError("No extractable hierarchy nodes were found in the ARXML file, so Markdown cannot be generated.")

    output_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert AUTOSAR ARXML ECUC containers to markdown headings."
    )
    parser.add_argument("input", type=Path, help="Input ARXML file path")
    parser.add_argument("output", type=Path, help="Output markdown file path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    arxml_to_markdown(args.input, args.output)


if __name__ == "__main__":
    main()
 