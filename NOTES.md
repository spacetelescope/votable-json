# VOTable JSON: draft 0.1 notes

The JSON is a fairly literal transliteration of the VOTable XML. The three examples in `tests/votable_examples/` (TAP/RegTAP, ObjObsSAP, SCS) and the TABLEDATA samples in `ref/VOTable/*.vot` were used to double check against

## Open questions

1. Should we pick OpenAPI 3.1 or 3.2? Most of the current DAL authors are going with 3.1 so the draft uses 3.1's `attribute` / `wrapped`, but 3.2 replaces those with `nodeType`.
2. `$id` is a placeholder.
3. Typed values (below), or keep everything a string like the XML? There's a huge history of issues with the difference between semantic versus actual datatype meanings in the IVOA i'd prefer not to go down. Who can tell what type <TD> 1.0 2.0 3.0</TD> is supposed to be anyway? What they mean (xtype, and how you’d query them) is the same damn problem it is in VOTable and TAP_SCHEMA.
4. Binary serializations: I'm just leaving them out for now. Headaches abound and I don't know anyone who uses them anyway.


`data.tabledata` is an array of rows, each row an array of cells in FIELD order.

Values with a `datatype` (cells, PARAM `value`, VALUES `null`/MIN/MAX/OPTION) are typed JSON as close as reasonable, numbers, booleans, strings, or arrays of tem. Complex numbers are `[re, im]`. Empty is `null`. NaN and infinities are the TABLEDATA strings.


Interleaved elements are split into one array each.

In a TABLE, INFOs before and after DATA both go in `infos`. INFOs trailing the rows inside DATA go in `data.infos`, for things like OVERFLOW.


- BINARY, BINARY2, FITS, STREAM. `data` requires `tabledata`.
- `DEFINITIONS`, FIELD `type`, LINK `gref`.
- RESOURCE `xs:any` extension points, including MIVOT.


`tools/vot2json.py` converts XML to JSON (TABLEDATA only) and generated the example JSON. No JSON→XML writer yet.