import sys,json
TABLE=json.loads('[{"a": [1, {"hit": false}], "b": [0, {"hit": false}], "c": [0, {"hit": false}]}, {"a": [0, {"hit": false}], "b": [2, {"hit": false}], "c": [0, {"hit": false}]}, {"a": [3, {"hit": false}], "b": [0, {"hit": false}], "c": [0, {"hit": false}]}, {"a": [0, {"hit": false}], "b": [0, {"hit": false}], "c": [4, {"hit": false}]}, {"a": [5, {"hit": false}], "b": [0, {"hit": false}], "c": [0, {"hit": false}]}, {"a": [0, {"hit": false}], "b": [6, {"hit": false}], "c": [0, {"hit": false}]}, {"a": [7, {"hit": false}], "b": [0, {"hit": false}], "c": [0, {"hit": false}]}, {"a": [0, {"hit": false}], "b": [0, {"hit": false}], "c": [0, {"hit": true}]}]')
state=0
for line in sys.stdin:
 request=json.loads(line)
 if request=={"control":"reset"}:
  state=0
  output={"control":"reset","ok":True}
 elif request.get("arguments") or request.get("operation") not in TABLE[0]:
  output={"error":"unsupported_action"}
 else:
  state,output=TABLE[state][request["operation"]]
 print(json.dumps(output),flush=True)
