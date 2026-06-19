#include <stdio.h>

int main(void) {
  puts("{");
  puts("  \"version\": \"urirun.bindings.v2\",");
  puts("  \"bindings\": {");
  puts("    \"c://local/device/query/serial\": {");
  puts("      \"uri\": \"c://local/device/query/serial\",");
  puts("      \"kind\": \"command\",");
  puts("      \"adapter\": \"argv-template\",");
  puts("      \"inputSchema\": {");
  puts("        \"type\": \"object\",");
  puts("        \"required\": [\"device\"],");
  puts("        \"properties\": {");
  puts("          \"device\": {\"type\": \"string\"}");
  puts("        },");
  puts("        \"additionalProperties\": false");
  puts("      },");
  puts("      \"argv\": [\"printf\", \"serial:%s\\\\n\", \"{device}\"],");
  puts("      \"meta\": {\"label\": \"C device serial\"}");
  puts("    }");
  puts("  }");
  puts("}");
  return 0;
}
