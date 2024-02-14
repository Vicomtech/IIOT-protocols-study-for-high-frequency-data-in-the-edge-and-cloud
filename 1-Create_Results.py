import pandas as pd 
import os
import matplotlib.pyplot as plt
import statistics as st


# Read text File
def read_text_file(file_path):
    with open(file_path, 'r') as f:
        return f.read()
    
# IF TRUE, WE PLOT EDGE VS CLOUD EXPERIMENTS IN SAME CONDITIONS, IF FALSE, WE PLOT ALL EXPERIMENTS OF CLOUD OR EDGE EXPERIMENTS
runs = 45 # HOW MUCH RUNS WE HAVE DONE TO GIVE CONSISTENCY TO THE EXPERIMENTS
broker = 'edge' # 'edge, cloud, edge_cloud
units = 1000 # 1=seconds, 10=ds, 100=cs, 1000=ms

# PATHS OF THE RESULTS
results_des = 'experimental_results'
res_produce = "produce"
res_consume = "consume"
res_folder = "results"
agregated_csv_name = broker+'_experiments.csv'


for run_number in range(1,runs+1):
    print('RUN:', run_number)
    run = 'results_RUN'+str(run_number)+'_'+broker
    
    csv_name = broker+'_experiments_RUN'+str(run_number)+'.csv'
    
    path_res_1 = os.path.join(res_produce, res_folder, run)
    path_res_2 = os.path.join(res_consume, res_folder, run)
    

    results_df = pd.DataFrame()

    num = 1
    # iterate through all txt files
    for file in os.listdir(path_res_1):
        # Check whether file is in text format or not
        print('-------------------------------------------------------------------------------')
        if file.endswith(".txt"):
            try: 
                file_path = f"{path_res_1}\{file}"
                # call read text file function
                metadata_id = file.split('_')[2].split('.')[0]
                metadata = read_text_file(file_path)
                prot, data_type, list_length, sampl_freq, cycles, connection = metadata.split(', ')
                              
                
                send_host1 = 'send_' + prot + '_' + metadata_id + '.csv'
                f = os.path.join(path_res_1, send_host1)
                experiment = pd.read_csv(f, names=['idx', 'time', 'place', 'metadata_id'], header=0)
                #experiment = pd.read_csv(f, header=None)
                # experiment[0] = experiment.index+1
                # experiment.to_csv(f, header=None)
                experiment['time'] = pd.to_datetime(experiment['time'], format='%Y-%m-%d %H:%M:%S.%f', utc=True)
                if (experiment['time'][len(experiment)-1]-experiment['time'][0]).total_seconds()>32:
                    print('ERRONEOUS EXPERIMENT DUE TO DATA GENERATION RATE:', metadata)
                else:
                
                    send_packages = experiment.shape[0]
                                        
                    send_host2 = 'process_send_' + prot + '_' + metadata_id + '.csv'
                    f = os.path.join(path_res_2, send_host2)
                    experiment_send_host2 = pd.read_csv(f)
                    experiment_send_host2 = experiment_send_host2.drop(columns='Unnamed: 0')
                    experiment_send_host2.columns = ['idx', 'time', 'script_time', 'place', 'metadata_id']
                    experiment_send_host2 = experiment_send_host2[['idx', 'script_time', 'metadata_id']]
                    
                    receive_host1 = 'receive_' + prot + '_' + metadata_id + '.csv'
                    f = os.path.join(path_res_1, receive_host1)
                    experiment_ = pd.read_csv(f, names=['idx', 'time', 'script_time', 'place', 'metadata_id'], header=0)
                    
                   
                    lost_packages = send_packages- experiment_.shape[0]
                    experiment_.columns = ['idx', 'time', 'script_time', 'place', 'metadata_id']
                    experiment_['time'] = pd.to_datetime(experiment_['time'], format='%Y-%m-%d %H:%M:%S.%f', utc=True)
                    experiment_receive_host1 = experiment_[['idx', 'script_time', 'metadata_id']]
                    experiment_ = experiment_.drop(columns='script_time')
                    
                    not_ordered_packages = 0
                    for i in range(len(experiment_['idx'])-1):
                        # if prot=='opcua' and metadata_id=='0001' and i==0:
                        #     pass
                        # else:
                        if experiment_['idx'][i]-experiment_['idx'][i+1]!=-1:
                            not_ordered_packages = not_ordered_packages + 1

                    experiment = pd.concat([experiment, experiment_], ignore_index=True)
                    
                    # grouped_df = pd.DataFrame(experiment.groupby(['idx', 'protocol'])["time"].diff().dt.total_seconds()) # planned is the planned production of that task that is not done

                    grouped_df_latency = experiment.groupby(['idx']).apply(lambda x: x['time'].diff().dt.total_seconds())
                    grouped_df_latency = grouped_df_latency.reset_index()
                    grouped_df_latency = grouped_df_latency.drop(columns='level_1')
                    grouped_df_latency = grouped_df_latency[grouped_df_latency['time'].notna()]
                    
                   
                    results = {}
                    latency = grouped_df_latency['time']
                    latency.reset_index(drop=True, inplace=True)
                    real_latency = latency - experiment_send_host2['script_time'] - experiment_receive_host1['script_time']
                    results['latency'] = real_latency.mean()*units
                    results['latency_stdev'] = st.pstdev(real_latency*units)
                    
                    # results['max'] = grouped_df['time'].max()*units
                    # results['min'] = grouped_df['time'].min()*units
                    jitter = grouped_df_latency['time'].diff()
                    jitter.reset_index(drop=True, inplace=True)
                    real_jitter = jitter - experiment_send_host2['script_time'].diff() - experiment_receive_host1['script_time'].diff()
                    results['jitter'] = abs(real_jitter).mean()*units
                    results['jitter_stdev'] = st.pstdev(real_jitter[1::]*units)
                    results['lost_packages'] = lost_packages
                    results['not_ordered_packages'] = not_ordered_packages
                    results['protocol'] = prot
                    results['data_type'] = data_type
                    
                    results['list_length'] = list_length
                    results['sampl_freq'] = sampl_freq
                    results['cycles'] = cycles
                    if data_type=='int':
                        data_size = 4 # int32, 4bytes
                    elif data_type=='float':
                        data_size = 8 # float64, 8bytes
                    results['Mbytes/Sec'] = int(list_length)*int(sampl_freq)*data_size/1000000
                    results['Payload(Kbytes)'] = int(4*int(list_length)/1000)
                    results['connection'] = connection


                    # results_df = results_df.append(results, ignore_index=True)
                    results_df = pd.concat([results_df, pd.DataFrame([results])], ignore_index=True)

                    print('EXPERIMENT:', num, 'METADATA:', metadata)
                    print('lost packages:', lost_packages)
                    print(results)
                num = num + 1
            except:
                print('error reading', file)
                
    # save results
    results_destination = os.path.join(results_des, broker, csv_name)
    results_df.to_csv(results_destination)
    if run_number==1:
        results_df_complete = results_df.copy()
    else:
        results_df_complete = pd.concat((results_df_complete, results_df)).groupby(['protocol','data_type','list_length','sampl_freq','cycles','Mbytes/Sec','connection']).mean()
        results_df_complete.reset_index(inplace=True)
results_destination = os.path.join(results_des, broker, agregated_csv_name)
results_df_complete.to_csv(results_destination)


