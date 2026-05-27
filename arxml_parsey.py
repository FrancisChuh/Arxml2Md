from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Set
import xml.etree.ElementTree as ET

import xmltodict


VALUE_CONTAINER_KEYS = (
    "ECUC-REFERENCE-VALUE",
    "ECUC-NUMERICAL-PARAM-VALUE",
    "ECUC-TEXTUAL-PARAM-VALUE",
)


class UnsupportedInputFormatError(ValueError):
    pass


class NoExtractableNodesError(ValueError):
    pass


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
        raise NoExtractableNodesError("No extractable hierarchy nodes were found in the input file, so Markdown cannot be generated.")

    output_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")


def read_dbc_text(dbc_path: Path) -> str:
    content = dbc_path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "gbk", "latin-1"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    return content.decode("latin-1", errors="replace")


def parse_signal_name(signal_line: str) -> str:
    signal_prefix, _, _ = signal_line.partition(":")
    signal_parts = signal_prefix.split()
    if len(signal_parts) >= 2:
        return signal_parts[1]
    return signal_line


def parse_signal_receivers(signal_line: str) -> List[str]:
    _, _, signal_body = signal_line.partition(":")
    body = signal_body.strip()
    if not body:
        return []

    receiver_segment = body.rsplit(" ", 1)[-1].strip()
    if not receiver_segment or '"' in receiver_segment:
        return []

    return [receiver.strip() for receiver in receiver_segment.split(",") if receiver.strip()]


def parse_declared_nodes(dbc_line: str) -> List[str]:
    _, _, nodes_segment = dbc_line.partition(":")
    return [node for node in nodes_segment.strip().split() if node]


def format_message_heading(message: Dict[str, Any], include_sender: bool) -> str:
    if include_sender:
        return (
            f"##### {message['name']} "
            f"(ID: {message['id']}, DLC: {message['dlc']}, Sender: {message['sender']})"
        )
    return f"##### {message['name']} (ID: {message['id']}, DLC: {message['dlc']})"


def message_sort_key(message: Dict[str, Any]) -> tuple[int, str]:
    return (int(message["id"]), str(message["name"]))


def dbc_to_markdown_lines(dbc_path: Path) -> List[str]:
    lines: List[str] = [f"# {dbc_path.stem}", "## Nodes"]
    dbc_text = read_dbc_text(dbc_path)

    declared_nodes: Set[str] = set()
    messages: List[Dict[str, Any]] = []
    current_message: Dict[str, Any] | None = None

    for raw_line in dbc_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("BU_:"):
            declared_nodes.update(parse_declared_nodes(line))
            continue

        if line.startswith("BO_ "):
            message_match = re.match(r"^BO_\s+(\d+)\s+([^\s:]+)\s*:\s*(\d+)\s+(\S+)", line)
            if message_match:
                message_id, message_name, dlc, sender = message_match.groups()
                current_message = {
                    "id": message_id,
                    "name": message_name,
                    "dlc": dlc,
                    "sender": sender,
                    "signals": [],
                }
                messages.append(current_message)
            else:
                current_message = None
            continue

        if line.startswith("SG_ ") and current_message is not None:
            signal_name = parse_signal_name(line)
            signal_receivers = parse_signal_receivers(line)
            current_message["signals"].append(
                {"name": signal_name, "receivers": signal_receivers}
            )

    if not messages:
        raise NoExtractableNodesError("No extractable hierarchy nodes were found in the input file, so Markdown cannot be generated.")

    sent_by_node: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    received_by_node: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)

    for message in messages:
        sender = str(message["sender"])
        sent_by_node[sender].append(message)

        for signal in message["signals"]:
            signal_name = str(signal["name"])
            for receiver in signal["receivers"]:
                message_key = str(message["id"])
                node_receive_entry = received_by_node[receiver].get(message_key)
                if node_receive_entry is None:
                    node_receive_entry = {"message": message, "signals": []}
                    received_by_node[receiver][message_key] = node_receive_entry
                node_receive_entry["signals"].append(signal_name)

    all_nodes = sorted(set(declared_nodes) | set(sent_by_node) | set(received_by_node))
    for node in all_nodes:
        node_sent_messages = sent_by_node.get(node, [])
        node_received_entries = list(received_by_node.get(node, {}).values())
        if not node_sent_messages and not node_received_entries:
            continue

        lines.append(f"### {node}")

        lines.append("#### Receive")
        if node_received_entries:
            node_received_entries.sort(key=lambda item: message_sort_key(item["message"]))
            for receive_entry in node_received_entries:
                message = receive_entry["message"]
                lines.append(format_message_heading(message, include_sender=True))
                for signal_name in receive_entry["signals"]:
                    lines.append(f"###### {signal_name}")
        else:
            lines.append("##### None")

        lines.append("#### Send")
        if node_sent_messages:
            node_sent_messages.sort(key=message_sort_key)
            for message in node_sent_messages:
                lines.append(format_message_heading(message, include_sender=False))
                for signal in message["signals"]:
                    lines.append(f"###### {signal['name']}")
        else:
            lines.append("##### None")

    return lines


def dbc_to_markdown(dbc_path: Path, output_path: Path) -> None:
    markdown_lines = dbc_to_markdown_lines(dbc_path)
    output_path.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")


def input_to_markdown(input_path: Path, output_path: Path) -> None:
    file_ext = input_path.suffix.lower()
    if file_ext == ".arxml":
        arxml_to_markdown(input_path, output_path)
        return
    if file_ext == ".dbc":
        dbc_to_markdown(input_path, output_path)
        return
    raise UnsupportedInputFormatError("Unsupported input file format. Please use a .arxml or .dbc file.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert AUTOSAR ARXML or DBC files to markdown headings for markmap."
    )
    parser.add_argument("input", type=Path, help="Input ARXML/DBC file path")
    parser.add_argument("output", type=Path, help="Output markdown file path")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    input_to_markdown(args.input, args.output)


if __name__ == "__main__":
    main()
 