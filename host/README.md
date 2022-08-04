#Problems
Monitor power and temperature while running a benhmark is not working

#Questions
Q1) Do we need to monitor the power and temp during the execution of a benchmark or simply to report voltage and freq. at the end of the execution?
Q2) Could you provide a non safe voltage to test the framework ?


The filesystem failed two times per month with SSD
The filesystem failed two times per month with HDD  

# Check how verification is done in 
https://www.nas.nasa.gov/assets/npb/NPB3.3.1.tar.gz

# TODO
1) compare only "Verification = SUCCESSFUL"
2) 


Unvervolting only the PMD domain (i.e., SOC domain remains at its nominal value): ./voltset PMD 960
Unvervolting only the SOC domain (i.e., PMD domain remains at its nominal value): ./voltset SOC 920
Unvervolting only the PMD + SOC domains: ./voltset ALL 930


"MG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/mg.A.8',
"CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/cg.A.8',
"CG" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ft.A.8', 
"IS" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/is.A.8',
"LU" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/lu.A.8',
"EP" : 'mpirun --allow-run-as-root --cpu-set 0-7 -np 8 --mca btl ^openib /opt/bench/NPB/NPB3.3-MPI/bin/ep.A.8'

Voltage Combinations for Beaming: In opposite priotity
PMD -  SOC
980 - 950
960 - 940
940 - 930
930 - 920


Non Safe Voltage
PMD -  SOC
910 - 950

