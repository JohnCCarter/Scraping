"""
Data validation for scraped content
"""

import re
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from urllib.parse import urlparse
import structlog


class DataValidator:
    """
    Validerar skrapad data för kvalitet och konsistens
    """

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

        # Regex-mönster för validering
        self.patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^[\+]?[1-9][\d]{0,15}$",
            "url": r"^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$",
            "date": r"^\d{4}-\d{2}-\d{2}$",
            "price": r"^[\d,]+\.?\d*$",
        }

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validerar skrapad data och lägger till valideringsmetadata

        Args:
            data: Data att validera

        Returns:
            Validerad data med metadata
        """
        if not isinstance(data, dict):
            return self._create_error_result("Data must be a dictionary")

        try:
            validated_data = data.copy()
            validation_results = {}

            # Validera varje fält
            for key, value in data.items():
                if key.startswith("_"):  # Skippa metadata
                    continue

                validation_result = self._validate_field(key, value)
                validation_results[key] = validation_result

            # Lägg till valideringsmetadata
            validated_data["_validation"] = {
                "timestamp": datetime.now().isoformat(),
                "total_fields": len(validation_results),
                "valid_fields": sum(1 for r in validation_results.values() if r["valid"]),
                "field_results": validation_results,
                "overall_valid": all(r["valid"] for r in validation_results.values()),
            }

            return validated_data

        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            return self._create_error_result(str(e))

    def _validate_field(self, field_name: str, value: Any) -> Dict[str, Any]:
        """
        Validerar ett enskilt fält

        Args:
            field_name: Fältnamn
            value: Fältvärde

        Returns:
            Valideringsresultat
        """
        result = {"valid": True, "errors": [], "warnings": [], "suggestions": []}

        # Skip None/empty values
        if value is None or value == "":
            result["valid"] = False
            result["errors"].append("Field is empty or null")
            return result

        # Fält-specifik validering
        if field_name.lower() in ["email", "e-mail", "mail"]:
            self._validate_email(value, result)
        elif field_name.lower() in ["phone", "telephone", "tel"]:
            self._validate_phone(value, result)
        elif field_name.lower() in ["url", "link", "website"]:
            self._validate_url(value, result)
        elif field_name.lower() in ["date", "created", "updated"]:
            self._validate_date(value, result)
        elif field_name.lower() in ["price", "cost", "amount"]:
            self._validate_price(value, result)
        elif field_name.lower() in ["title", "name", "heading"]:
            self._validate_text_length(value, result, min_length=1, max_length=200)
        elif field_name.lower() == "description":
            self._validate_text_length(value, result, min_length=1, max_length=2000)

        # Generell validering
        self._validate_general(value, result)

        return result

    def _validate_email(self, value: str, result: Dict[str, Any]):
        """Validerar e-postadress"""
        if not isinstance(value, str):
            result["valid"] = False
            result["errors"].append("Email must be a string")
            return

        if not re.match(self.patterns["email"], value):
            result["valid"] = False
            result["errors"].append("Invalid email format")

    def _validate_phone(self, value: str, result: Dict[str, Any]):
        """Validerar telefonnummer"""
        if not isinstance(value, str):
            result["valid"] = False
            result["errors"].append("Phone must be a string")
            return

        # Rensa telefonnummer
        cleaned = re.sub(r"[\s\-\(\)]", "", value)
        if not re.match(self.patterns["phone"], cleaned):
            result["valid"] = False
            result["errors"].append("Invalid phone number format")

    def _validate_url(self, value: str, result: Dict[str, Any]):
        """Validerar URL"""
        if not isinstance(value, str):
            result["valid"] = False
            result["errors"].append("URL must be a string")
            return

        try:
            parsed = urlparse(value)
            if not parsed.scheme or not parsed.netloc:
                result["valid"] = False
                result["errors"].append("Invalid URL format")
        except Exception:
            result["valid"] = False
            result["errors"].append("Invalid URL format")

    def _validate_date(self, value: str, result: Dict[str, Any]):
        """Validerar datum"""
        if not isinstance(value, str):
            result["valid"] = False
            result["errors"].append("Date must be a string")
            return

        try:
            # Försök parsa olika datumformat
            date_formats = ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"]

            parsed = False
            for fmt in date_formats:
                try:
                    datetime.strptime(value, fmt)
                    parsed = True
                    break
                except ValueError:
                    continue

            if not parsed:
                result["valid"] = False
                result["errors"].append("Invalid date format")

        except Exception:
            result["valid"] = False
            result["errors"].append("Invalid date format")

    def _validate_price(self, value: str, result: Dict[str, Any]):
        """Validerar pris"""
        if not isinstance(value, str):
            result["valid"] = False
            result["errors"].append("Price must be a string")
            return

        # Rensa pris från valutasymboler och whitespace
        cleaned = re.sub(r"[^\d,.]", "", value)
        if not re.match(self.patterns["price"], cleaned):
            result["valid"] = False
            result["errors"].append("Invalid price format")

    def _validate_text_length(self, value: str, result: Dict[str, Any], min_length: int = 1, max_length: int = 1000):
        """Validerar textlängd"""
        if not isinstance(value, str):
            result["valid"] = False
            result["errors"].append("Value must be a string")
            return

        if len(value) < min_length:
            result["valid"] = False
            result["errors"].append(f"Text too short (minimum {min_length} characters)")

        if len(value) > max_length:
            result["warnings"].append(f"Text very long ({len(value)} characters)")

    def _validate_general(self, value: Any, result: Dict[str, Any]):
        """Generell validering för alla fält"""
        # Kontrollera för HTML-taggar
        if isinstance(value, str) and re.search(r"<[^>]+>", value):
            result["warnings"].append("Contains HTML tags")

        # Kontrollera för specialtecken
        if isinstance(value, str) and re.search(r"[^\w\s\-.,!?@#$%&*()]", value):
            result["suggestions"].append("Contains special characters")

        # Kontrollera för duplicerade whitespace
        if isinstance(value, str) and re.search(r"\s{2,}", value):
            result["suggestions"].append("Contains multiple consecutive spaces")

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Skapar felresultat"""
        return {
            "_error": error_message,
            "_validation": {"timestamp": datetime.now().isoformat(), "valid": False, "error": error_message},
        }

    def validate_batch(self, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validerar en lista med data

        Args:
            data_list: Lista med data att validera

        Returns:
            Lista med validerad data
        """
        validated_list = []

        for i, data in enumerate(data_list):
            try:
                validated_data = self.validate(data)
                validated_list.append(validated_data)
            except Exception as e:
                self.logger.error(f"Error validating item {i}: {str(e)}")
                validated_list.append(self._create_error_result(str(e)))

        return validated_list

    def get_validation_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Skapar sammanfattning av valideringsresultat

        Args:
            data: Validerad data

        Returns:
            Valideringssammanfattning
        """
        if "_validation" not in data:
            return {"error": "No validation data found"}

        validation = data["_validation"]

        summary = {
            "total_fields": validation.get("total_fields", 0),
            "valid_fields": validation.get("valid_fields", 0),
            "invalid_fields": validation.get("total_fields", 0) - validation.get("valid_fields", 0),
            "overall_valid": validation.get("overall_valid", False),
            "field_errors": {},
            "field_warnings": {},
        }

        # Samla fel och varningar per fält
        field_results = validation.get("field_results", {})
        for field_name, result in field_results.items():
            if result.get("errors"):
                summary["field_errors"][field_name] = result["errors"]
            if result.get("warnings"):
                summary["field_warnings"][field_name] = result["warnings"]

        return summary


class SchemaValidator:
    """
    Validerar data mot ett fördefinierat schema
    """

    def __init__(self, schema: Dict[str, Any]):
        """
        Initierar schema-validator

        Args:
            schema: Schema-definition
        """
        self.schema = schema
        self.logger = structlog.get_logger(__name__)

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validerar data mot schemat

        Args:
            data: Data att validera

        Returns:
            Valideringsresultat
        """
        result = {"valid": True, "errors": [], "missing_fields": [], "extra_fields": []}

        # Kontrollera obligatoriska fält
        required_fields = self.schema.get("required", [])
        for field in required_fields:
            if field not in data or data[field] is None:
                result["missing_fields"].append(field)
                result["valid"] = False

        # Kontrollera fälttyper
        for field_name, field_value in data.items():
            if field_name in self.schema.get("fields", {}):
                field_schema = self.schema["fields"][field_name]
                field_result = self._validate_field_type(field_value, field_schema)

                if not field_result["valid"]:
                    result["errors"].extend(field_result["errors"])
                    result["valid"] = False

        # Kontrollera extra fält
        allowed_fields = set(self.schema.get("fields", {}).keys())
        data_fields = set(data.keys())
        extra_fields = data_fields - allowed_fields

        if extra_fields and not self.schema.get("allow_extra_fields", True):
            result["extra_fields"] = list(extra_fields)
            result["valid"] = False

        return result

    def _validate_field_type(self, value: Any, field_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validerar fälttyp"""
        result = {"valid": True, "errors": []}

        expected_type = field_schema.get("type")
        if expected_type:
            if expected_type == "string" and not isinstance(value, str):
                result["valid"] = False
                result["errors"].append(f"Expected string, got {type(value).__name__}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                result["valid"] = False
                result["errors"].append(f"Expected number, got {type(value).__name__}")
            elif expected_type == "boolean" and not isinstance(value, bool):
                result["valid"] = False
                result["errors"].append(f"Expected boolean, got {type(value).__name__}")

        return result
