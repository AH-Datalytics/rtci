import json
from typing import Any

from langchain_core.documents import Document


def get_first_value(data_dict, keys):
    if not data_dict:
        return None
    if not keys:
        return None
    for key in keys:
        value = data_dict.get(key)
        if value is not None:
            return value
        value_downcase = data_dict.get(key.lower())
        if value_downcase is not None:
            return value_downcase
    return None


def get_first_header_index(header, keys):
    if not header:
        return None
    if not keys:
        return None
    for key in keys:
        trimmed_key = key.strip()
        try:
            value = header.index(trimmed_key)
            if value is not None:
                return value
        except ValueError:
            pass
        try:
            value_downcase = header.index(trimmed_key.lower())
            if value_downcase is not None:
                return value_downcase
        except ValueError:
            pass
    return None


def concatenate_items(items, separator='', prefix='', suffix=''):
    if items is None:
        return prefix + suffix
    result = separator.join(str(item) for item in items)
    return prefix + result + suffix


def convert_structured_document_to_json(document: Document) -> list[dict[str, Any]]:
    if document is None:
        return []
    json_list = json.loads(document.page_content)
    if not json_list:
        return []
    json_items = []
    if isinstance(json_list, dict):
        key, value = flatten_descriptive_column(json_list)
        if key is not None and value is not None:
            json_items.append({key: value})
    elif isinstance(json_list, (list, tuple, set)):
        flattened_item: dict[str, Any] = {}
        for json_item in json_list:
            if isinstance(json_item, dict):
                for key, value in map(lambda x: flatten_descriptive_column(x), json_list):
                    if key is not None and value is not None:
                        flattened_item[key] = value
        if flattened_item:
            json_items.append(flattened_item)
    return json_items


def flatten_descriptive_column(row: dict[str, Any]) -> tuple[str, Any] | None:
    if not row:
        return '', None
    type = row.get("type") or "STRING"
    attribute = row.get("columnName")
    value = row.get("columnValue")
    if type == "LONG":
        value = int(value)
    else:
        value = str(value).strip()
    return attribute, value
