#!/usr/bin/env python3
"""
Script to generate OpenAPI YAML file from FastAPI application.
"""
import yaml
from app.main import app

# Get the OpenAPI schema from FastAPI
openapi_schema = app.openapi()

# Convert to YAML
yaml_content = yaml.dump(openapi_schema, default_flow_style=False, sort_keys=False, allow_unicode=True)

# Write to file
output_file = "openapi.yaml"
with open(output_file, "w", encoding="utf-8") as f:
    f.write(yaml_content)

print(f"✅ OpenAPI YAML file generated: {output_file}")
print(f"📄 Total endpoints: {len(openapi_schema.get('paths', {}))}")

