import statistics
from datetime import datetime


def read_execution_time(file_name):
    results = {}
    with open(file_name, "r") as f:
        try:
            data = eval(f.read())

            for tool_name in data:
                for vul_id in data[tool_name]:
                    repair = data[tool_name][vul_id]
                    repair_begin = datetime.fromisoformat(repair["repair_begin"])
                    repair_end = datetime.fromisoformat(repair["repair_end"])

                    running_time = (repair_end - repair_begin).total_seconds()
                    running_time = int(running_time)
                    print(f"{tool_name} {vul_id} {running_time}")

                    if vul_id not in results:
                        results[vul_id] = {}
                        if tool_name not in results[vul_id]:
                            results[vul_id][tool_name] = {}
                    results[vul_id][tool_name] = running_time

        except Exception as e:
            print("Error: ", e)
        return results


res_1 = read_execution_time("../data/vul4j_repairthemall_patches.json")
res_2 = read_execution_time("../data/vul4j_maestro_patches.json")
print(res_2)
for vul_id in res_1:
    overhead = int(statistics.mean([res_2[vul_id]['jGenProg'] - res_1[vul_id]['jGenProg'],
                                res_2[vul_id]['jKali'] - res_1[vul_id]['jKali'],
                                res_2[vul_id]['jMutRepair'] - res_1[vul_id]['jMutRepair']
                                ]))
    print(f"{vul_id} & {res_1[vul_id]['jGenProg']} & {res_1[vul_id]['jKali']} & {res_1[vul_id]['jMutRepair']} & {res_2[vul_id]['jGenProg']} & {res_2[vul_id]['jKali']} & {res_2[vul_id]['jMutRepair']} & {overhead} \\\\")