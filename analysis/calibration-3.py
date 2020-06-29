#!/usr/bin/env python
# coding: utf-8

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("Q", help="file containing volumetric flow")
parser.add_argument("DP", help="file containing delta pressures")
parser.add_argument("out", help="name of output CSV file")
parser.add_argument("--sanity", default="sanity-plot.png", help="name of output sanity-check plot (can be PDF)")
parser.add_argument("--calibration", default="calibration-plot.png", help="name of output calibration plot (can be PDF)")
args = parser.parse_args()

# In[1]:


import csv

import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize
import pandas as pd


# In[2]:


filename_Q = args.Q
filename_DP = args.DP
filename_sanity = args.sanity
filename_calplot = args.calibration
filename_out = args.out


# In[3]:


df_Q = pd.read_csv(filename_Q)
df_Q["Time"] = pd.to_datetime(df_Q["Time"])
df_Q


# In[4]:


def read_data(filename):
    t = []
    dp = []
    with open(filename) as file:
        start_fill = False
        for line in csv.reader(file):
            if start_fill:
                t.append(float(line[1].replace(",", "")))
                dp.append(float(line[2]))
            if line[0] == "Sample #":
                start_fill = True
    return pd.DataFrame({"Time": np.array(t), "Delta Pressure": np.array(dp)})

df_DP = read_data(filename_DP)
df_DP


# In[5]:


comparator = df_Q["Volumetric Flow"].rolling(5).mean().fillna(method="bfill").values**(7/4)
delta = abs(comparator[1:] - comparator[:-1])
origin_Q = df_Q["Time"].values[np.argmax(delta)]
df_Q["Common Time"] = (df_Q["Time"] - origin_Q).dt.total_seconds()
df_Q["Binned Time"] = (10*df_Q["Common Time"].values).astype(np.int64)

with np.errstate(divide="ignore", invalid="ignore"):
    changes, = np.nonzero(np.logical_and(delta > 1.0, delta/comparator[:-1] > 0.05))
change_times = df_Q["Common Time"].values[changes]

df_Q["Common Time"]


# In[6]:


comparator = df_DP["Delta Pressure"].rolling(5).mean().fillna(method="bfill").values
delta = abs(comparator[1:] - comparator[:-1])
origin_DP = df_DP["Time"].values[np.argmax(delta)]
df_DP["Common Time"] = df_DP["Time"] - origin_DP
df_DP["Binned Time"] = (10*df_DP["Common Time"].values).astype(np.int64)
df_DP["Common Time"]


# In[7]:


ax = df_Q.plot("Common Time", "Volumetric Flow")
for t in change_times:
    ax.axvline(t, c="lightgray", ls="--")


# In[8]:


ax = df_DP.plot("Common Time", "Delta Pressure")
for t in change_times:
    ax.axvline(t, c="lightgray", ls="--")


# In[9]:


binned_Q = df_Q[["Common Time", "Binned Time", "Volumetric Flow"]].groupby("Binned Time").mean()
binned_Q.plot("Common Time", "Volumetric Flow")
binned_Q


# In[10]:


binned_DP = df_DP[["Common Time", "Binned Time", "Delta Pressure"]].groupby("Binned Time").mean()
binned_DP.plot("Common Time", "Delta Pressure")
binned_DP


# In[11]:


df = pd.merge(binned_Q, binned_DP, how="inner", on="Binned Time")
df


# In[12]:


ax = df.plot("Common Time_x", ["Volumetric Flow", "Delta Pressure"])
for t in change_times:
    ax.axvline(t, c="lightgray", ls="--")
ax.figure.savefig(filename_sanity)


# In[13]:


since_change = df["Common Time_x"].values[:, np.newaxis] - change_times[np.newaxis, :]
df["Recent Change"] = np.any((-2 <= since_change) & (since_change < 8), axis=1)
since_change[since_change < 0] = np.inf
df["Since Change"] = np.min(since_change, axis=1)
df


# In[14]:


df[~df["Recent Change"]].plot.scatter("Common Time_x", "Volumetric Flow")


# In[15]:


df[~df["Recent Change"]].plot.scatter("Common Time_x", "Delta Pressure")


# In[16]:


df[~df["Recent Change"]].plot.scatter("Volumetric Flow", "Delta Pressure")


# In[17]:


xs = df[~df["Recent Change"]]["Volumetric Flow"].values
ys = df[~df["Recent Change"]]["Delta Pressure"].values

def fit(x, constant):
    return np.sign(x)*(constant * abs(x)**(7.0/4.0))

(fit_constant,), covariance = scipy.optimize.curve_fit(fit, xs, ys)

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(15, 5))
curve_xs = np.linspace(-35, 1000, 1000)

for ax in (ax1, ax2, ax3):
    h2, = ax.plot(curve_xs, fit(curve_xs, fit_constant), label="DP = {:.4f}*Q**7/4".format(fit_constant))
    h0, = ax.plot(xs, ys, "o", c="red", label="measurements")
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 150)
    ax.set_xlabel("flow Q (L/min)")
    ax.set_ylabel("delta pressure DP (Pa)")
    ax.legend(handles=[h0, h2])

ax2.axvline(0, c="gray")
ax2.axhline(0, c="gray")
ax2.set_xlim(-35, 35)
ax2.set_ylim(-35, 35)

ax3.set_xlim(1, 1000)
ax3.set_ylim(1, 1000)
ax3.set_yscale("log")
ax3.set_xscale("log")

fig.savefig(filename_calplot)


# In[18]:


dfout = df[["Common Time_x", "Since Change", "Recent Change", "Volumetric Flow", "Delta Pressure"]].sort_index()
dfout


# In[19]:


dfout.to_csv(filename_out)

