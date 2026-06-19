package main

import (
	"encoding/json"
	"os"
	"sort"
)

type Field struct {
	Type     string      `json:"type"`
	Required bool        `json:"-"`
	Default  interface{} `json:"default,omitempty"`
}

type InputSchema struct {
	Type                 string           `json:"type"`
	Required             []string         `json:"required"`
	Properties           map[string]Field `json:"properties"`
	AdditionalProperties bool             `json:"additionalProperties"`
}

type Binding struct {
	URI         string            `json:"uri"`
	Kind        string            `json:"kind"`
	Adapter     string            `json:"adapter"`
	InputSchema InputSchema       `json:"inputSchema"`
	Argv        []string          `json:"argv"`
	Meta        map[string]string `json:"meta"`
}

type Document struct {
	Version  string             `json:"version"`
	Bindings map[string]Binding `json:"bindings"`
}

func uriCommand(uri string, fields map[string]Field, argv []string, label string) Binding {
	required := []string{}
	properties := map[string]Field{}
	names := make([]string, 0, len(fields))
	for name := range fields {
		names = append(names, name)
	}
	sort.Strings(names)
	for _, name := range names {
		field := fields[name]
		if field.Required {
			required = append(required, name)
		}
		field.Required = false
		properties[name] = field
	}
	return Binding{
		URI:     uri,
		Kind:    "command",
		Adapter: "argv-template",
		InputSchema: InputSchema{
			Type:                 "object",
			Required:             required,
			Properties:           properties,
			AdditionalProperties: false,
		},
		Argv: argv,
		Meta: map[string]string{"label": label},
	}
}

func main() {
	route := uriCommand(
		"go://local/text/upper",
		map[string]Field{
			"text": {Type: "string", Required: true},
		},
		[]string{"go", "run", "text_upper.go", "{text}"},
		"Go text upper",
	)
	_ = json.NewEncoder(os.Stdout).Encode(Document{
		Version:  "urirun.bindings.v2",
		Bindings: map[string]Binding{route.URI: route},
	})
}
