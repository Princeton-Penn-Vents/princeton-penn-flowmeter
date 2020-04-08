#!/usr/bin/env python
import json

def aggregate_for_nursing(time_stamp,jsons):

    for i,j_str in enumerate(jsons):
        j_info=json.loads(j_str)
        if i==0:
            nurse_info= { "version" : j_info["v"],
                          "time" : time_stamp,
                          "alarms" : {},
                          "data" : {
                              "timestamps" : [],
                              "flows" : [],
                              "pressures" : []
                              }
                          }
        nurse_info["data"]["timestamps"].append(j_info["t"])
        nurse_info["data"]["pressures"].append(j_info["P"])
        nurse_info["data"]["flows"].append(j_info["F"])

    return json.dumps(nurse_info).encode("ascii")

if __name__ == "__main__":
    from sim import VentSim

    from datetime import datetime
    now_time = datetime.now().timestamp()

    sim = VentSim(now_time,1000)
    jsons=[]
    for i in range(100):
        d=sim.get_next()
        jsons.append(json.dumps(d).encode("ascii"))
    output=aggregate_for_nursing(now_time,jsons)

    print(json.loads(output))
    
