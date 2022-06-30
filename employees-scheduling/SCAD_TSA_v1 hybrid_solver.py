# -*- coding: utf-8 -*-
"""
Created on Wed May 11 07:53:34 2022

@author: scerto
"""

import pandas as pd
import numpy as np
from dwave.system import LeapHybridSampler
from dimod import Binary, quicksum
import pickle
import time

import neal

import matplotlib.pyplot as plt

dataDir = r'employees-scheduling/SCAD_TSA_simulated_data_final_v3.xlsx'

employeeDF = pd.read_excel(dataDir, sheet_name = 'Employee')
shiftDF = pd.read_excel(dataDir, sheet_name = 'Shift_details')

tot_employees = len(employeeDF['empid'].unique())

def staff_schedule(n_employees, dataDir):

    employeeDF = pd.read_excel(dataDir, sheet_name = 'Employee')
    shiftDF = pd.read_excel(dataDir, sheet_name = 'Shift_details')

    employeeDF = employeeDF[employeeDF['fam_med']!=1]
    #employeeDF = employeeDF[employeeDF['gender']==1]
    employeeDF.reset_index(drop=True, inplace=True)
    employeeDF.drop_duplicates(inplace=True)

    #total number of employees
    tot_emp = len(employeeDF['empid'].unique())
    print('Total employees ', tot_emp)
    print('Number employees to staff ', n_employees)

    
    #Start with one airport
    employeeDF = employeeDF[employeeDF['emp_airport']=='BWI']
    shiftDF = shiftDF[shiftDF['airport']=='BWI']

    employeeDF.loc[employeeDF['rank']=='Senior', 'RankInt'] = 3
    employeeDF.loc[employeeDF['rank']=='Experienced', 'RankInt'] = 2
    employeeDF.loc[employeeDF['rank']=='Novice', 'RankInt'] = 1

    #Select n number of employees
    employeeDF = employeeDF[:n_employees]

    #Create Staffing Demands (shift_demand = # of security lanes, each staffed by 2 of each gender for each of 5 terminals)
    shiftDF['Num_Sec_lanes'] = shiftDF['shift_demand']
    shiftDF['DemandReqs'] = shiftDF['shift_demand']
    # shiftDF['DemandReqs'] = shiftDF['shift_demand']*2*5
    shiftDF.drop(['Index','shift','shift_no','term_concor','sec_lane'], inplace=True, axis=1)
    shiftDF.drop_duplicates(inplace=True)

    #Start on a Sunday
    shiftDF['date'] = shiftDF['date']-pd.Timedelta(days=2)
    employeeDF.loc[employeeDF['pto_req_date_2']!=0, 'pto_req_date_1'] = employeeDF.loc[employeeDF['pto_req_date_1']!=0, 'pto_req_date_1']-pd.Timedelta(days=2)
    employeeDF.loc[employeeDF['pto_req_date_2']!=0, 'pto_req_date_2'] = employeeDF.loc[employeeDF['pto_req_date_2']!=0, 'pto_req_date_2']-pd.Timedelta(days=2)

    #Convert PTO request days to dict of employes and day numbers of PTO
    PTOReqDayNum = {}

    startingDate = min(shiftDF['date'])

    for ix, row in employeeDF.iterrows():
        if row['pto_req_date_1']==0 and row['pto_req_date_2']==0:
            continue
        elif row['pto_req_date_2']==0:
            temp = row['pto_req_date_1']-startingDate
            PTOReqDayNum[row['empid']] = []
            PTOReqDayNum[row['empid']] = [temp.days + i for i in range(row['pto_len_days_1'])]
        elif row['pto_req_date_1']==0:
            temp = row['pto_req_date_2']-startingDate
            PTOReqDayNum[row['empid']] = []
            PTOReqDayNum[row['empid']] = [temp.days + i for i in range(row['pto_len_days_2'])]
        else:
            temp = row['pto_req_date_1']-startingDate
            PTOReqDayNum[row['empid']] = []
            days1 = [temp.days + i for i in range(row['pto_len_days_1'])]
            
            temp = row['pto_req_date_2']-startingDate
            days2 = [temp.days + i for i in range(row['pto_len_days_2'])]
            days_combined = days1 + days2
            PTOReqDayNum[row['empid']] = days_combined

    for k, v in PTOReqDayNum.items():
        PTOReqDayNum[k] = list(set(v))
        PTOReqDayNum[k] = [d for d in v if d<=13]

        
    #Define variables
    xvars = {}
    for n in employeeDF['empid'].unique():
        m = int(employeeDF.loc[employeeDF['empid']==n,'RankInt'].values[0])
        for q in range(len(shiftDF['date'].unique())):
            for p in shiftDF['day_shift'].unique():
                xvars[f'E_{m}_{n}_{p}_{q}'] = Binary(label = f'E_{m}_{n}_{p}_{q}')

    #Objective Function
    obj_func = 0
    for n in list(PTOReqDayNum.keys()):
        m = int(employeeDF.loc[employeeDF['empid']==n,'RankInt'].values[0])
        for q in PTOReqDayNum[n]:
            if q >13:
                continue
            for p in shiftDF['day_shift'].unique():
                obj_func += m*xvars[f'E_{m}_{n}_{p}_{q}']
                
    #Constraint #1: No more than 1 shift per day per employee
    const_1_slacks = {}
    for n in employeeDF['empid'].unique():
        for q in range(len(shiftDF['date'].unique())):
            const_1_slacks[f'c1_slack_{n}_{q}'] = Binary(f'c1_slack_{n}_{q}')
                
    const_1 = 0
    for n in employeeDF['empid'].unique():
        m = int(employeeDF.loc[employeeDF['empid']==n,'RankInt'].values[0])
        for q in range(len(shiftDF['date'].unique())):
            day_tot = sum([xvars[f'E_{m}_{n}_{p}_{q}'] for p in shiftDF['day_shift'].unique()])
            const_1 += (day_tot + const_1_slacks[f'c1_slack_{n}_{q}'] - 1)**2
                
                    
    #Constraint #2: Night shift followed by morning shift not allowed
    const_2 = 0
    for n in employeeDF['empid'].unique():
        m = int(employeeDF.loc[employeeDF['empid']==n,'RankInt'].values[0])
        for q in range(len(shiftDF['date'].unique())-1):
            const_2 += xvars[f'E_{m}_{n}_{3}_{q}']*xvars[f'E_{m}_{n}_{1}_{q+1}']


    #Constraint #3 No more than 5 shifts per week
    #Binary encoded integer slack variables
    const_3_slacks = {}
    for n in employeeDF['empid'].unique():
        for wk in range(2):
            for b in range(3):
                const_3_slacks[f'c3_slack_{n}_{b}_{wk}'] = Binary(f'c3_slack_{n}_{wk}_{b}')
        
    const_3_slacks_bin = {}
    for n in employeeDF['empid'].unique():
        for wk in range(2):
            temp = 0
            for b in range(3):
                temp += const_3_slacks[f'c3_slack_{n}_{b}_{wk}'] * 2**b
            const_3_slacks_bin[f'c3_slack_{n}_{wk}'] = temp
        

    const_3 = 0
    for n in employeeDF['empid'].unique():
        m = int(employeeDF.loc[employeeDF['empid']==n,'RankInt'].values[0])
        
        week_tot = 0
        for q in range(7):
            for p in shiftDF['day_shift'].unique():
                week_tot += xvars[f'E_{m}_{n}_{p}_{q}']
        const_3 += (week_tot + const_3_slacks_bin[f'c3_slack_{n}_{0}'] - 5)**2

        week_tot = 0
        for q in range(7,14):
            for p in shiftDF['day_shift'].unique():
                week_tot += xvars[f'E_{m}_{n}_{p}_{q}']
        const_3 += (week_tot + const_3_slacks_bin[f'c3_slack_{n}_{1}'] - 5)**2


                
    #Staffing Demands (Constraint #4)
    const_4 = 0
    for q, d in enumerate(shiftDF['date'].unique()):
        for p in shiftDF['day_shift'].unique():
            tot_shift_demand = shiftDF[(shiftDF['date']==d) & (shiftDF['day_shift']==p)]['DemandReqs'].sum()
            
            tot_shift_supply = 0
            for n in employeeDF['empid'].unique():
                m = int(employeeDF.loc[employeeDF['empid']==n,'RankInt'].values[0])
                tot_shift_supply += xvars[f'E_{m}_{n}_{p}_{q}']
            
            const_4 += (tot_shift_supply - tot_shift_demand)**2
        
    #Constraint #5: Some employees prefer to not work weekends
    const_5 = 0
    for n in employeeDF[employeeDF['wk_pref']==0]['empid'].unique():
        m = int(employeeDF.loc[employeeDF['empid']==n,'RankInt'].values[0])
        
        wkend_tot = 0
        
        for q in [0,6,7,13]:
            for p in shiftDF['day_shift'].unique():
                wkend_tot += xvars[f'E_{m}_{n}_{p}_{q}']
        
        const_5 += wkend_tot

    bqm = 2*obj_func + const_1 + const_2 + const_3 + 3*const_4 + const_5 #here weights of constraints can be changed depending on focus

    sampler = LeapHybridSampler(token='DEV-5cb788ab47d1211cdddb54678e43ce43a12751b4')

    start = time.time()

    sampleset = sampler.sample(bqm, label = 'TSA_v2')

    TTS = time.time() - start

    print('TTS ', TTS)
    print(sampleset.info)
        
    t = sampleset.to_pandas_dataframe(sampleset)

    sample = t.loc[0,'sample']

    # pickle.dump(sample, open(dataDir + r'\Raw_Output_BWI_1.pckl', 'wb'))

    #sample = pickle.load(open(dataDir + r'\Raw_Output_BWI_1.pckl', 'rb'))


    employeeShiftAssignment = pd.DataFrame(columns = ['empid', 'rank', 'shift_day','calendar_date'])

    
    for k,v in sample.items():
        if k[:1] != 'E':
            continue
        if v != 1:
            continue
        
        rank = int(k.split('_')[1])
        empid = int(k.split('_')[2])
        shift_day = int(k.split('_')[3])
        day_num = int(k.split('_')[4])

        ix = len(employeeShiftAssignment)
        employeeShiftAssignment.loc[ix, 'empid'] = empid
        employeeShiftAssignment.loc[ix, 'rank'] = ['Novice','Experienced','Senior'][rank-1]
        employeeShiftAssignment.loc[ix, 'shift_day'] = shift_day
        employeeShiftAssignment.loc[ix, 'calendar_date'] = shiftDF['date'].unique()[day_num]

    employeeShiftAssignment.loc[:,'calendar_date'] = pd.to_datetime(employeeShiftAssignment['calendar_date'])

    #########CONSTRAINT VERIFICATION##############
    employees_staffed = len(employeeShiftAssignment['empid'].unique())
    print('Employees staffed ', employees_staffed)

    #Constraint #1: No more than 1 shift per day per employee
    temp = employeeShiftAssignment.groupby(['empid','calendar_date']).size()
    print('Constraint #1: how many employees have more than 1 shift per day? ',len(temp[temp>1]))

    #Constraint #2: Night shift followed by morning shift not allowed
    #Manually Verify
    # for emp in employeeShiftAssignment['empid'].unique():
    #     empDF = employeeShiftAssignment[employeeShiftAssignment['empid']==emp]
    #     empDF = empDF[(empDF['shift_day']==3) | (empDF['shift_day']==1)]

    #     if len(empDF)>1:
    #         print(empDF)

    #Constraint #3 No more than 5 shifts per week
    week1 = employeeShiftAssignment[employeeShiftAssignment['calendar_date']<=startingDate + pd.Timedelta(days=6)]
    week1 = week1.groupby('empid').size()
    print('Constraint #3: how many employees work more than 5 shifts per week (1)? ', len(week1[week1>5]))

    week2 = employeeShiftAssignment[employeeShiftAssignment['calendar_date']>startingDate + pd.Timedelta(days=6)]
    week2 = week2.groupby('empid').size()
    print('Constraint #3: how many employees work more than 5 shifts per week (2)? ', len(week2[week2>5]))


    #Constraint #4: Staffing Demands are met
    const4DF = shiftDF.copy()
    const4DF['ShiftSupply'] = 0

    for ix, row in const4DF.iterrows():
        temp = employeeShiftAssignment[employeeShiftAssignment['calendar_date']==row['date']]
        temp = temp[temp['shift_day']==row['day_shift']]

        const4DF.loc[ix,'ShiftSupply'] = len(temp['empid'].unique())
        
    const4DF.columns
    temp = const4DF['DemandReqs']-const4DF['ShiftSupply']

    print('Constraint #4: Staffing demand not met ', len(temp[temp!=0]))

    #Constraint #5: Some employees prefer to not work weekends
    wkendEmps = employeeDF[employeeDF['wk_pref']==0]['empid'].unique()

    weekends = [startingDate, startingDate + pd.Timedelta(days=6),startingDate + pd.Timedelta(days=7), startingDate + pd.Timedelta(days=13)]

    const5_break = 0

    for empid in wkendEmps:
        temp = employeeShiftAssignment[employeeShiftAssignment['empid']==empid]
        for ix, row in temp.iterrows():
            if row['calendar_date'] in weekends:
                const5_break += 1

    print('Constraint #5: how many employees work on weekends even if they do not want to? ', const5_break)

    #Objective: PTO days

    print('Objective: who are the employees who work even if they should be off? (employee id)')
    for k,v in PTOReqDayNum.items():
        temp = employeeShiftAssignment[employeeShiftAssignment['empid']==k]
        for ptoday in v:
            if pd.to_datetime(shiftDF['date'].unique()[ptoday]) in temp['calendar_date'].values:
                print(k)

    #OutputFile
    #employeeShiftAssignment['Gender'] = 'Female'
    employeeShiftAssignment.loc[:,'empid'] = employeeShiftAssignment['empid'].astype(int)
    outputDF = pd.merge(employeeDF[['empid','first_name','last_name']], employeeShiftAssignment, how='inner', on = 'empid')

    for d in outputDF['calendar_date'].unique():
        for p in outputDF['shift_day'].unique():
            num_sec_lanes = shiftDF[(shiftDF['date']==d)&(shiftDF['day_shift']==p)]['Num_Sec_lanes'].values[0]

            #outputDF.loc[(outputDF['calendar_date']==d) & (outputDF['shift_day']==p),'Sec_Lane'] = list(np.arange(1,num_sec_lanes+1))
            #outputDF.loc[(outputDF['calendar_date']==d) & (outputDF['shift_day']==p),'Terminal'] = ['A','B','C','D','E']

            # outputDF.loc[(outputDF['calendar_date']==d) & (outputDF['shift_day']==p),'Sec_Lane'] = list(np.arange(1,num_sec_lanes+1))*2*5
            # outputDF.loc[(outputDF['calendar_date']==d) & (outputDF['shift_day']==p),'Terminal'] = ['A','B','C','D','E']*2*num_sec_lanes


    outputDF.to_excel(r'employees-scheduling/BWI_All_Output.xlsx')

    return TTS, employees_staffed, tot_emp

TTS = []
n_employees = []

for n in range(10, tot_employees, 200):
    staff = staff_schedule(n, dataDir)
    n_employees.append(staff[1])
    TTS.append(staff[0])
    

plt.plot(n_employees, TTS)
plt.ylabel('TTS [s]')
plt.xlabel('Number of employees staffed')
plt.title('Quantum annealing of staff schedule for increasing number of employees')
plt.show()

plt.savefig('Hybridsolver_scaling.png')


        