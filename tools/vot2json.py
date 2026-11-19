"""Convert a TABLEDATA VOTable (XML) to the draft JSON serialization. 
"""

import json
import sys
import xml.etree.ElementTree as ET

NS = "{http://www.ivoa.net/xml/VOTable/v1.3}"

INT_TYPES = {"unsignedByte", "short", "int", "long"}
FLOAT_TYPES = {"float", "double"}
COMPLEX_TYPES = {"floatComplex", "doubleComplex"}
CHAR_TYPES = {"char", "unicodeChar"}

CHILD_LISTS = {
    "COOSYS": "coosys",
    "TIMESYS": "timesys",
    "GROUP": "groups",
    "PARAM": "params",
    "FIELD": "fields",
    "INFO": "infos",
    "LINK": "links",
    "TABLE": "tables",
    "RESOURCE": "resources",
    "FIELDref": "fieldrefs",
    "PARAMref": "paramrefs",
    "OPTION": "options",
}

INT_ATTRS = {"nrows", "width"}
DROPPED_ATTRS = {"gref"}


def local(tag):
    return tag[len(NS):] if tag.startswith(NS) else tag


def parse_float(tok):
    if tok in ("NaN", "+Inf", "-Inf"):
        return tok
    if tok in ("Inf", "inf", "Infinity"):
        return "+Inf"
    if tok in ("-inf", "-Infinity"):
        return "-Inf"
    if tok.lower() == "nan":
        return "NaN"
    return float(tok)


def parse_int(tok):
    if tok.lower().startswith(("0x", "-0x", "+0x")):
        return int(tok, 16)
    return int(tok)


def parse_bool(tok):
    t = tok.strip().lower()
    if t in ("t", "true", "1"):
        return True
    if t in ("f", "false", "0"):
        return False
    return None


def parse_value(text, datatype, arraysize):
    """Parse a TD or value= string into a JSON value per datatype/arraysize."""
    if text is None or text == "":
        return None
    if datatype in CHAR_TYPES:
        return text
    if datatype in COMPLEX_TYPES:
        toks = [parse_float(t) for t in text.split()]
        pairs = [toks[i:i + 2] for i in range(0, len(toks), 2)]
        return pairs if arraysize else pairs[0]

    if datatype == "bit":
        toks = list(text.replace(" ", "").replace("\n", "").replace("\t", ""))
        conv = int
    elif datatype == "boolean":
        toks = text.split()
        conv = parse_bool
    elif datatype in INT_TYPES:
        toks = text.split()
        conv = parse_int
    elif datatype in FLOAT_TYPES:
        toks = text.split()
        conv = parse_float
    else:
        raise ValueError(f"unknown datatype {datatype!r}")

    if not toks:
        return None
    vals = [conv(t) for t in toks]
    return vals if arraysize else vals[0]


def convert_attrs(el, out):
    for k, v in el.attrib.items():
        if k.startswith("{") or k in DROPPED_ATTRS:
            continue
        out[k] = int(v) if k in INT_ATTRS else v


def convert_element(el, field_types=None):
    tag = local(el.tag)
    out = {}
    convert_attrs(el, out)

    if tag in ("FIELD", "PARAM"):
        dt, size = el.get("datatype"), el.get("arraysize")
        if tag == "PARAM":
            out["value"] = parse_value(el.get("value"), dt, size)

    if tag == "TIMESYS" and "timeorigin" in out:
        if out["timeorigin"] not in ("JD-origin", "MJD-origin"):
            out["timeorigin"] = float(out["timeorigin"])

    if tag == "INFO" and el.text and el.text.strip():
        out["content"] = el.text.strip()

    fields = []
    for child in el:
        if not isinstance(child.tag, str):
            continue
        ctag = local(child.tag)
        if ctag == "DESCRIPTION":
            out["description"] = "".join(child.itertext()).strip()
        elif ctag == "VALUES":
            out["values"] = convert_values(child, el.get("datatype"), el.get("arraysize"))
        elif ctag == "DATA":
            out["data"] = convert_data(child, fields)
        elif ctag in CHILD_LISTS:
            converted = convert_element(child)
            out.setdefault(CHILD_LISTS[ctag], []).append(converted)
            if ctag == "FIELD":
                fields.append((child.get("datatype"), child.get("arraysize")))
        elif ctag == "DEFINITIONS":
            continue
        else:
            raise ValueError(f"unsupported element {ctag} inside {tag}")
    return out


def convert_values(el, dt, size):
    out = {}
    convert_attrs(el, out)
    if "null" in out:
        out["null"] = parse_value(out["null"], dt, None)
    for child in el:
        ctag = local(child.tag)
        if ctag in ("MIN", "MAX"):
            lim = {}
            convert_attrs(child, lim)
            lim["value"] = parse_value(lim["value"], dt, size)
            out[ctag.lower()] = lim
        elif ctag == "OPTION":
            out.setdefault("options", []).append(convert_option(child, dt, size))
    return out


def convert_option(el, dt, size):
    out = {}
    convert_attrs(el, out)
    out["value"] = parse_value(out["value"], dt, size)
    for child in el:
        out.setdefault("options", []).append(convert_option(child, dt, size))
    return out


def convert_data(el, fields):
    out = {}
    for child in el:
        ctag = local(child.tag)
        if ctag == "TABLEDATA":
            rows = []
            for tr in child:
                cells = [td.text for td in tr]
                rows.append([
                    parse_value(text, dt, size)
                    for text, (dt, size) in zip(cells, fields)
                ])
            out["tabledata"] = rows
        elif ctag == "INFO":
            out.setdefault("infos", []).append(convert_element(child))
        else:
            raise ValueError(f"{ctag} serialization is not supported")
    return out


def main(argv):
    root = ET.parse(argv[1]).getroot()
    doc = convert_element(root)
    text = json.dumps(doc, indent=2, ensure_ascii=False, allow_nan=False)
    if len(argv) > 2:
        with open(argv[2], "w", encoding="utf-8", newline="\n") as f:
            f.write(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main(sys.argv)
