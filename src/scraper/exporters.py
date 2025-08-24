"""
Data exporters for various formats
"""

import json
import csv
import time
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import structlog

try:
    import pandas as pd

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl

    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False


class DataExporter:
    """
    Exporterar skrapad data till olika format
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)
        self.supported_formats = ["json", "csv", "excel", "xml"]

    def export(
        self, data: Union[Dict[str, Any], List[Dict[str, Any]]], format: str, output_path: str, **kwargs
    ) -> bool:
        """
        Exporterar data till specificerat format

        Args:
            data: Data att exportera
            format: Export-format ("json", "csv", "excel", "xml")
            output_path: Sökväg för output-fil
            **kwargs: Ytterligare parametrar för export

        Returns:
            True om export lyckades
        """
        try:
            # Normalisera data
            if isinstance(data, dict):
                data = [data]

            # Skapa output-mapp om den inte finns
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Exportera baserat på format
            if format.lower() == "json":
                return self._export_json(data, output_path, **kwargs)
            elif format.lower() == "csv":
                return self._export_csv(data, output_path, **kwargs)
            elif format.lower() == "excel":
                return self._export_excel(data, output_path, **kwargs)
            elif format.lower() == "xml":
                return self._export_xml(data, output_path, **kwargs)
            else:
                raise ValueError(f"Unsupported format: {format}")

        except Exception as e:
            self.logger.error(f"Export error: {str(e)}")
            return False

    def _export_json(self, data: List[Dict[str, Any]], output_path: Path, pretty: bool = True, **kwargs) -> bool:
        """Exporterar till JSON-format"""
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                else:
                    json.dump(data, f, ensure_ascii=False, default=str)

            self.logger.info(f"Data exported to JSON: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"JSON export error: {str(e)}")
            return False

    def _export_csv(self, data: List[Dict[str, Any]], output_path: Path, flatten: bool = True, **kwargs) -> bool:
        """Exporterar till CSV-format"""
        try:
            if not data:
                self.logger.warning("No data to export")
                return False

            # Flatten data om det behövs
            if flatten:
                flattened_data = [self._flatten_dict(item) for item in data]
            else:
                flattened_data = data

            # Hitta alla unika kolumner
            all_keys = set()
            for item in flattened_data:
                all_keys.update(item.keys())

            # Skriv CSV
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=sorted(all_keys))
                writer.writeheader()
                writer.writerows(flattened_data)

            self.logger.info(f"Data exported to CSV: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"CSV export error: {str(e)}")
            return False

    def _export_excel(self, data: List[Dict[str, Any]], output_path: Path, sheet_name: str = "Data", **kwargs) -> bool:
        """Exporterar till Excel-format"""
        if not EXCEL_AVAILABLE:
            self.logger.error("Excel export requires openpyxl package")
            return False

        try:
            if not data:
                self.logger.warning("No data to export")
                return False

            # Flatten data för Excel
            flattened_data = [self._flatten_dict(item) for item in data]

            # Skapa DataFrame och exportera
            df = pd.DataFrame(flattened_data)
            df.to_excel(output_path, sheet_name=sheet_name, index=False)

            self.logger.info(f"Data exported to Excel: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"Excel export error: {str(e)}")
            return False

    def _export_xml(
        self, data: List[Dict[str, Any]], output_path: Path, root_name: str = "data", item_name: str = "item", **kwargs
    ) -> bool:
        """Exporterar till XML-format"""
        try:
            xml_content = self._dict_to_xml(data, root_name, item_name)

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(xml_content)

            self.logger.info(f"Data exported to XML: {output_path}")
            return True

        except Exception as e:
            self.logger.error(f"XML export error: {str(e)}")
            return False

    def _flatten_dict(self, data: Dict[str, Any], parent_key: str = "", sep: str = "_") -> Dict[str, Any]:
        """
        Flattar en nästlad dict till en platt struktur

        Args:
            data: Dict att flattena
            parent_key: Föräldernyckel
            sep: Separator för nästlade nycklar

        Returns:
            Flattenad dict
        """
        items = []
        for k, v in data.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k

            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            elif isinstance(v, list):
                # Hantera listor genom att konvertera till sträng
                items.append((new_key, str(v)))
            else:
                items.append((new_key, v))

        return dict(items)

    def _dict_to_xml(self, data: List[Dict[str, Any]], root_name: str, item_name: str) -> str:
        """Konverterar dict till XML-sträng"""
        xml_parts = [f'<?xml version="1.0" encoding="UTF-8"?>']
        xml_parts.append(f"<{root_name}>")

        for item in data:
            xml_parts.append(f"  <{item_name}>")
            xml_parts.extend(self._dict_to_xml_elements(item, indent=4))
            xml_parts.append(f"  </{item_name}>")

        xml_parts.append(f"</{root_name}>")
        return "\n".join(xml_parts)

    def _dict_to_xml_elements(self, data: Dict[str, Any], indent: int = 0) -> List[str]:
        """Konverterar dict-element till XML-element"""
        elements = []
        indent_str = " " * indent

        for key, value in data.items():
            # Rensa nyckel för XML
            clean_key = re.sub(r"[^a-zA-Z0-9_]", "_", str(key))

            if isinstance(value, dict):
                elements.append(f"{indent_str}<{clean_key}>")
                elements.extend(self._dict_to_xml_elements(value, indent + 2))
                elements.append(f"{indent_str}</{clean_key}>")
            elif isinstance(value, list):
                for item in value:
                    elements.append(f"{indent_str}<{clean_key}>")
                    if isinstance(item, dict):
                        elements.extend(self._dict_to_xml_elements(item, indent + 2))
                    else:
                        elements.append(f"{indent_str}  {self._escape_xml(str(item))}")
                    elements.append(f"{indent_str}</{clean_key}>")
            else:
                elements.append(f"{indent_str}<{clean_key}>{self._escape_xml(str(value))}</{clean_key}>")

        return elements

    def _escape_xml(self, text: str) -> str:
        """Escape XML-specialtecken"""
        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def export_with_timestamp(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        format: str,
        output_dir: str,
        prefix: str = "data",
        **kwargs,
    ) -> Optional[str]:
        """
        Exporterar data med timestamp i filnamnet

        Args:
            data: Data att exportera
            format: Export-format
            output_dir: Output-mapp
            prefix: Prefix för filnamn
            **kwargs: Ytterligare parametrar

        Returns:
            Sökväg till skapad fil eller None vid fel
        """
        try:
            timestamp = int(time.time())
            filename = f"{prefix}_{timestamp}.{format}"
            output_path = Path(output_dir) / filename

            success = self.export(data, format, str(output_path), **kwargs)

            if success:
                return str(output_path)
            else:
                return None

        except Exception as e:
            self.logger.error(f"Timestamp export error: {str(e)}")
            return None

    def get_export_summary(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Skapar sammanfattning av data för export

        Args:
            data: Data att sammanfatta

        Returns:
            Sammanfattning
        """
        if not data:
            return {"error": "No data to summarize"}

        summary = {"total_items": len(data), "fields": {}, "data_types": {}, "validation_summary": {}}

        # Analysera fält
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())

        summary["unique_fields"] = len(all_keys)
        summary["field_names"] = sorted(all_keys)

        # Analysera datatyper
        for key in all_keys:
            values = [item.get(key) for item in data if key in item]
            non_null_values = [v for v in values if v is not None]

            if non_null_values:
                summary["fields"][key] = {
                    "count": len(non_null_values),
                    "null_count": len(values) - len(non_null_values),
                    "unique_count": len(set(str(v) for v in non_null_values)),
                }

        # Valideringssammanfattning
        validation_data = [item for item in data if "_validation" in item]
        if validation_data:
            valid_count = sum(1 for item in validation_data if item["_validation"].get("overall_valid", False))
            summary["validation_summary"] = {
                "total_validated": len(validation_data),
                "valid_items": valid_count,
                "invalid_items": len(validation_data) - valid_count,
            }

        return summary


# Import regex för XML-escape
import re
