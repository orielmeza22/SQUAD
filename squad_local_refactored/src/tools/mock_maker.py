from typing import Dict, Any, Tuple


class ContractValidator:
    @staticmethod
    def validate_payload_against_schema(payload: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validates a payload against a simplified OpenAPI property schema block.
        """
        required = schema.get("required", [])
        for field in required:
            if field not in payload:
                return False, f"Falta el campo obligatorio '{field}' definido en el esquema OpenAPI."

        properties = schema.get("properties", {})
        for key, val in payload.items():
            if key in properties:
                expected_type = properties[key].get("type")
                if expected_type == "string" and not isinstance(val, str):
                    return False, f"Tipo de dato incorrecto para '{key}': se esperaba string, se obtuvo {type(val).__name__}."
                elif expected_type == "integer" and not isinstance(val, int) and not (isinstance(val, float) and val.is_integer()):
                    return False, f"Tipo de dato incorrecto para '{key}': se esperaba integer, se obtuvo {type(val).__name__}."
                elif expected_type == "array" and not isinstance(val, list):
                    return False, f"Tipo de dato incorrecto para '{key}': se esperaba array, se obtuvo {type(val).__name__}."
                elif expected_type == "object" and not isinstance(val, dict):
                    return False, f"Tipo de dato incorrecto para '{key}': se esperaba object, se obtuvo {type(val).__name__}."

        return True, ""


class MockMaker:
    @staticmethod
    def generate_mock_from_schema(schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates a mock JSON payload matching the properties of the provided schema.
        """
        mock = {}
        properties = schema.get("properties", {})
        for key, val in properties.items():
            prop_type = val.get("type")
            if prop_type == "string":
                mock[key] = val.get("default", "mock_value")
            elif prop_type == "integer":
                mock[key] = val.get("default", 123)
            elif prop_type == "number":
                mock[key] = val.get("default", 99.9)
            elif prop_type == "boolean":
                mock[key] = val.get("default", True)
            elif prop_type == "array":
                mock[key] = []
            elif prop_type == "object":
                mock[key] = {}
            else:
                mock[key] = None
        return mock
