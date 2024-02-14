import pandas as pd 
import os
import matplotlib.pyplot as plt

    
# CONFIGURATION-------------------------------------------------------------------
broker = 'edge' # 'edge, cloud
# select protocols to plot and create a color map that maps each value in the 'value' column to a color
normalize = True
# PATHS OF THE RESULTS
results_des = 'experimental_results'
agregated_csv_name = broker+'_experiments.csv'
results_destination = os.path.join(results_des, broker, agregated_csv_name)
results_df_complete = pd.read_csv(results_destination)

results_df_complete['Payload(Kbytes)'] = (((4*results_df_complete['list_length']/1000)).astype(int)).astype(str)
results_df_complete.drop(columns=['list_length', 'data_type', 'Unnamed: 0'], inplace=True)


if broker == 'edge':
    protocols_to_plot = ['amqp', 'kafka', 'mqtt',  'zeromq', 'opcua'] 
    color_map = {'amqp': 'red',  'mqtt': 'orange', 'zeromq':'green', 'kafka':'blue', 'opcua': 'yellow'} 
else:
    protocols_to_plot = ['amqp', 'kafka', 'mqtt', 'zeromq']
    color_map = {'amqp': 'red', 'mqtt': 'orange','zeromq':'green', 'kafka':'blue'}


# ---------------------------------------------------------------------------------------
def normalize_df_col(df,col):
    min_val = min(list(df[col]))
    max_val = max(list(df[col]))
    df[col] = [(x / max_val) for x in df[col]]
    return df


# PLOT EXPERIMENTS GROUPED BY stream size AND sampling frequency COMBINATION ---------------------------------------------------------------------
results_df_complete = results_df_complete.loc[results_df_complete['protocol'].isin(protocols_to_plot)]
g_results_df = results_df_complete.set_index('protocol')
g_results_df = g_results_df.groupby(['Payload(Kbytes)', 'sampl_freq', 'cycles', 'connection', 'Mbytes/Sec'])



# PLOT ALL EXPERIMENTS BY INIDIVIDUAL STATISTIC ---------------------------------------------------------------------------------------------
gr_results_df_complete = results_df_complete.groupby('Mbytes/Sec')
results_df_complete['new_col'] = results_df_complete['protocol']+'_'+results_df_complete['Payload(Kbytes)']+'_'+results_df_complete['sampl_freq'].astype(str)
results_df_complete = results_df_complete.set_index('new_col')

# create a list of colors for each bar in the plot
reordered_df = results_df_complete.sort_values(by=['Mbytes/Sec', 'protocol', 'sampl_freq'])
colors = [color_map[val] for val in reordered_df['protocol']]
reordered_df.reset_index(inplace=True)
for col in ['latency', 'latency_stdev', 'jitter', 'jitter_stdev']:
    reordered_df = normalize_df_col(reordered_df,col)


# PLOT ALL EXPERIMENTS TOGETHER BY LATENCY OR JITTER
for statistical_feat in ['latency', 'jitter']:
    fig, ax = plt.subplots(figsize=(10, 5))
    
    reordered_df.plot(kind='bar', x='new_col', y=statistical_feat, color=colors, ax=ax, label='')
    ax2 = ax.twinx()
    reordered_df.plot(x='new_col', y='Mbytes/Sec',color='black', kind='scatter', marker='*', s=10, ax=ax2, label='')

    ax.set_ylabel('Normalized value')
    ax.set_xlabel('(Protocol, Payload(Kbytes), Sampling Frequency)')
    ax.legend('')
    ax2.set_ylabel('Throughput (Mbytes/s)')
    ax2.legend('')

    title = statistical_feat
    plt.title(title)
    # create the legend
    handles = [plt.Rectangle((0,0),1,1, color=color_map[label]) for label in color_map]
    
    plt.legend(handles, color_map.keys())
    fig.tight_layout()

    fig.savefig('experimental_results/{}/all_combinations/{}.png'.format(broker,statistical_feat), dpi=fig.dpi)

    plt.close()
    
# ---------------------------------------------------------------------------------------

# # PLOT EXPERIMENTS GROUPED BY THROUGHPUT  ---------------------------------------------------------------------------------------------

for name, gr in gr_results_df_complete:
    gr_normalized = gr.copy()
    for col in ['latency', 'latency_stdev', 'jitter', 'jitter_stdev']:
        gr_normalized = normalize_df_col(gr_normalized,col)
    
    gr['Payload(Kbytes)'] = gr['Payload(Kbytes)'].astype(int)
    gr = gr.sort_values(by=['protocol','Payload(Kbytes)', 'sampl_freq'])
    gr['Payload(Kbytes)'] = gr['Payload(Kbytes)'].astype(str)                 
    gr['sampl_freq'] = gr['sampl_freq'].astype(str)                 
    gr = gr.set_index(['protocol','Payload(Kbytes)','sampl_freq'])
    gr.index = gr.index.map('_'.join)
    
    gr_normalized['Payload(Kbytes)'] = gr_normalized['Payload(Kbytes)'].astype(int)
    gr_normalized = gr_normalized.sort_values(by=['protocol','Payload(Kbytes)', 'sampl_freq'])
    gr_normalized['Payload(Kbytes)'] = gr_normalized['Payload(Kbytes)'].astype(str)                 
    gr_normalized['sampl_freq'] = gr_normalized['sampl_freq'].astype(str)                 
    gr_normalized = gr_normalized.set_index(['protocol','Payload(Kbytes)','sampl_freq'])
    gr_normalized.index = gr_normalized.index.map('_'.join)
 

    gr = gr[['latency', 'latency_stdev', 'jitter', 'jitter_stdev']].T
    gr_normalized = gr_normalized[['latency', 'latency_stdev', 'jitter', 'jitter_stdev']].T
    print(gr)
    print(gr_normalized)
    # HOW MANY TIME BIGGER IS THE RESULT OF ONE PROTOCOL VS THE BEST??
    df_compare = gr_normalized.copy()
    df_compare.loc['latency'] = df_compare.loc['latency'].div(df_compare.loc['latency'].min())
    df_compare.loc['latency_stdev'] = df_compare.loc['latency_stdev'].div(df_compare.loc['latency_stdev'].min())
    df_compare.loc['jitter'] = df_compare.loc['jitter'].div(df_compare.loc['jitter'].min())
    df_compare.loc['jitter_stdev'] = df_compare.loc['jitter_stdev'].div(df_compare.loc['jitter_stdev'].min())
    print(df_compare.drop(df_compare.filter(like='opc',axis=1).columns.to_list(),axis=1))
    
    for num, feat in enumerate(['latency','jitter']): 
        fig, axs = plt.subplots(1,1, figsize=(12, 6))
        df = gr_normalized.loc[feat,:].to_frame()
        for k, v in color_map.items():
            df.loc[df.index.str.contains(k), 'color'] = v
        
        min_max_vals_list = []
        for prot_streamsize in gr_normalized:
            min_max_vals_list.append([[0],[gr_normalized[prot_streamsize][feat+'_stdev']]])
        
        
        data_to_plot = gr_normalized.loc[feat,:].to_frame().transpose()
        data_to_plot.plot(kind='bar', color=df['color'], ax=axs, yerr=min_max_vals_list, edgecolor="black", linewidth=3)
    
        axs.set_yscale('log')
        axs.set_ylabel('Normalized '+feat, fontsize=18)
        axs.set_xticklabels('') # x-axis
        axs.set_xlabel('Scenarios', fontsize=18)

        fig.subplots_adjust(top=0.9, bottom=0.15, right=0.95, left=0.1) # make space between subplots and figure
        #plt.show()
 
        fig.savefig('experimental_results/{}/all_combinations/SameThroughput{}_{}.png'.format(broker,name,feat), dpi=fig.dpi)

        plt.close()
    

