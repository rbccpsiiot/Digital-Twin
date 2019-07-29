# Plot k variation (from data in a csv file)

import csv

k =[]
avg_throughput = []
avg_energy=[]

with open('Results_k_double_buffering.csv', 'rb') as csvfile:
    data = csv.reader(csvfile,delimiter=",")
    r=0
    for row in data:
        if(r>0): #ignore the first row
            k.append(int(row[0]))
            avg_throughput.append(float(row[2]))
            avg_energy.append(float(row[5]))
            if(k[-1] >= 28): 
                break
        r+=1


print k
print avg_throughput
print avg_energy
        
# Plot the data:

from matplotlib import pyplot as plt

fig=plt.figure(1,figsize=(4,4)) # Size = 3 inches x 3 inches

#plot energy
ax1 = fig.add_subplot(1,1,1)
ax1.set_xlabel(r"Reflow oven turn-ON threshold $k$",fontsize=13)
plot1 = ax1.plot(k, avg_energy,'o-',color='b',label="Avg energy per PCB")
ax1.set_ylabel("Avg Energy per-PCB (kJ)",color='b',fontsize=13)

ax2 = ax1.twinx()
plot2 = ax2.plot(k, avg_throughput,'s-',color='r',label="Avg Throughput")
ax2.set_ylabel("Avg throughput",color='r',fontsize=13)

plots = plot1+plot2
labels = [l.get_label() for l in plots]
plt.legend(plots, labels).draggable()
plt.show()



