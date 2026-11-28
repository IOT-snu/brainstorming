import sys, os, time, pickle, multiprocessing as mp
sys.path.insert(0, os.getcwd())
import experiments as X
import pandas as pd
tasks = X.grid("E3", 10)
for t in tasks:
    t["policies"] = ["auto", "ciota"]; t["exp"] = "E3c"; t["traces"] = False
for name in X.data.available():
    X.data.raw(name)
X.space()
t0 = time.time(); rows = []
with mp.get_context("fork").Pool(9) as pool:
    for k, rs in enumerate(pool.imap_unordered(X.run_task, tasks, chunksize=1)):
        rows += rs
        if (k + 1) % 168 == 0: print(k + 1, len(tasks), round(time.time() - t0), flush=True)
pickle.dump(rows, open(sys.argv[1], "wb"))
d = pd.DataFrame([r for r, _ in rows])
print((d.pivot_table(index="policy", columns="mode", values="compromised_attr", aggfunc="mean", margins=True) * 100).round(1))
print("fpr strong drift tail", (d.groupby("policy")["fpr_v_tail"].mean() * 100).round(1).to_dict() if "fpr_v_tail" in d else "")
