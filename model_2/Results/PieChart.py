from matplotlib import pyplot as plt


# RFO occupancy data:
occupancy = [
[0.00      , 3.94      , 45.80      , 50.26], # no buffering
[75.07     , 20.18     , 0.00       ,  4.75], # single buffering N=128
[71.88     , 22.17     , 0.00       ,  5.95]  # double buffering N=128
]

titles = ["No Buffering", "Single Buffering (N=128)", "Double Buffering (N=128)"]
labels = ["OFF","setup","ON_empty","ON_occupied"]
colors = ["whitesmoke","yellow","salmon","lightgreen"]
hatching = ["",".","|","-", "/" , "\\" , "|" , "-" , "+" , "x", "o", "O", ".", "*" ]


fig = plt.figure(1, figsize=(3,3))
# There will be three pie charts and a legend, all in one column
ROWS = 2
COLS = 2
ax=[]
pies=[]
positions = [1,3,4]
for i in range(3):
    ax.append(plt.subplot(ROWS,COLS,positions[i]))
    data = occupancy[i]
    p = ax[i].pie(data, startangle=90, colors=colors)
    for j in range(len(p[0])):
        p[0][j].set_hatch(hatching[j])
    pies.append(p)
    ax[i].set_title(titles[i])
    ax[i].axis("equal")


ax2 = fig.add_subplot(ROWS,COLS,2)
ax2.axis("off") 
ax2.legend(pies[0][0],labels, loc="upper center")
plt.show()
