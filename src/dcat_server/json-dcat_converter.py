import json


def json_to_turtle(json_data):
    turtle_lines = [
        '@prefix dcat: <http://www.w3.org/ns/dcat#> .',
        '@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .',
        '@prefix ex: <http://example.org/> .',
        ''
    ]

    entity_id = json_data["id"].split(":")[-1]
    entity_type = json_data["type"]

    turtle_lines.append(f"ex:{entity_id} a ex:{entity_type} ;")

    for key, value in json_data.items():
        if key not in ["@context", "id", "type"]:
            prop_value = value["value"]
            prop_lines = [f"    ex:{key} [", "        a dcat:Property ;"]

            for prop_key, prop_val in prop_value.items():
                if prop_key == "value":
                    try:
                        val = float(prop_val)
                        if val.is_integer():
                            prop_lines.append(f"        ex:{prop_key} \"{int(val)}\"^^xsd:integer ;")
                        else:
                            prop_lines.append(f"        ex:{prop_key} \"{val}\"^^xsd:decimal ;")
                    except ValueError:
                        prop_lines.append(f"        ex:{prop_key} \"{prop_val}\" ;")
                elif prop_key == "dateObserved":
                    prop_lines.append(f"        ex:{prop_key} \"{prop_val}\"^^xsd:dateTime ;")
                elif prop_key == "timeWindowLengthMinutes":
                    prop_lines.append(f"        ex:{prop_key} \"{int(prop_val)}\"^^xsd:integer ;")
                else:
                    prop_lines.append(f"        ex:{prop_key} \"{prop_val}\" ;")

            prop_lines[-1] = prop_lines[-1].replace(" ;", "")
            prop_lines.append("    ] ;")
            turtle_lines.extend(prop_lines)

    turtle_lines[-1] = turtle_lines[-1].replace(" ;", " .")

    return "\n".join(turtle_lines)


def main():
    input_file = "data.json"
    with open(input_file, 'r') as file:
        json_data = json.load(file)

    turtle_data = json_to_turtle(json_data)

    print(turtle_data)

    output_file = "output.ttl"
    with open(output_file, 'w') as file:
        file.write(turtle_data)


if __name__ == "__main__":
    main()
