- **Name of the dataset:**
    IIOT protocols study for high frequency data in the edge and cloud

- **Description:**
    The provided data is the following:
    1. *EXPERIMENTS RAW DATA:*
        * Data inside *produce/results* and *consume/results* folders contain raw information about the performed experiments.
            - Inside *produce/results* there are 45 numbered folders containing *edge* experiments and 45 numbered folders containin *cloud* experiments, each of them corresponding to 1 iteration. One folder is created for each of the iterations, example: *results_RUN{iteration_number}_{edge or cloud scenario}*. Inside each of theese folders, 3 different files are created associated to each *protocol/data_packet_length/data_packet_rate* combination. There are 9 possible combitations, with the following parameters: data_packet_rate: "[10, 20, 40, 10, 20, 40, 10, 20, 40]", data_packet_length: "[25000, 12500, 6250, 100000, 50000, 25000, 200000, 100000, 50000]" 
                - **metadata_{protocol}_{experiment_number}.txt:** file containing the metadata of the experiment, with:  protocol, data type, data packet length, data packet rate, number of cycles of the experiment.
                - **send_{protocol}_{experiment_number}.csv:** csv containing all the T1 timestamps of the experiment, with: ID (id of each individual data packet in the experiment), TIME1 (T1 timestamp), location (IIOT host), metadata_id (id associated to the experiment)
                - **receive_{protocol}_{experiment_number}.csv:** csv containing all the T4 timestamps of the experiment, with: ID (id of each individual data packet in the experiment), TIME4 (T4 timestamp), SCRIPT_TIME (processing time of the IIOT receive script, it must be substracted later for measuring the real latency and jitter of the protocol), location (IIOT host), metadata_id (id associated to the experiment)

        * Data inside *consume/results* and *consume/results* folders contain raw information about the performed experiments.
            - Inside *produce/results* there are 45 numbered folders containing *edge* experiments and 45 numbered folders containin *cloud* experiments. As the experiments has been performed 45 times, each of the folder contains the same files corresponding to different iterations. One folder is created for each of the performed experiments, ex: *results_RUN{id of the experiment}_{edge or cloud scenario}*. Inside each of theese folders, 2 different files are created associated to each *protocol/data_packet_length/data_packet_rate* combination: 
                - **process_receive_{protocol}_{experiment_number}.csv:** csv containing all the T2 timestamps of the experiment, with: ID (id of each individual data packet in the experiment), TIME2 (T2 timestamp), location (AI host), metadata_id (id associated to the experiment)
                - **process_send_{protocol}_{experiment_number}.csv:** csv containing all the T3 timestamps of the experiment, with: ID (id of each individual data packet in the experiment), TIME3 (T3 timestamp), SCRIPT_TIME (processing time of the AI service script, it must be substracted later for measuring the real latency and jitter of the protocol), location (AI host), metadata_id (id associated to the experiment)

    2. *EXPERIMENTS PROCESSED DATA:*
        * *experimental_results/* folder contains processed edge and cloud experiment .csv files.
            * *experimental_results/{edge or cloud}* folder contains 45 .csv numbered files with the following name structure *{edge or cloud}_experiments_RUN{iteration_number}.csv*. Each of them contain the following extracted metrics and metadata over the raw .csv files: 
                - Metrics: mean latency, latency_stdev, mean jitter, jitter_stdev lost_packages, not_ordered_packages.
                - Metadata:	protocol (employed protocol), data_type (data type employed in the experiments), list_length (data packet size), sampl_freq (data packet rate), cycles (duration of the experiment), Mbytes/Sec (experiment troughput), Payload(Kbytes) (data packet payload).
            * *experimental_results/{edge or cloud}/{edge or cloud}_experiments.csv*: This file contains the mean of all the *{edge or cloud}_experiments_RUN{id}.csv* individual experiment iterations grouped by same *protocol/data_packet_length/data_packet_rate* combination. This file is employed for visualizing the results. For visualizing them, please refer to *https://github.com/telmobarrena98/Protocols_tester/2-Result_Visualizer_edgeORcloud.py*.
        
            

- **Relación de link de descarga a cada una de las partes del dataset comprimido:**

- **Authors:**
Telmo Fernández De Barrena, Ander García and Juan Luis Ferrando

- **Contact:** 
tfernandez@vicomtech.org

- **Usage License:** 
This agreement grants the Recipient a non-exclusive, non-transferable license to access and use the *IIOT protocols high frequency data  edge and cloud experiments* dataset for internal research and analysis purposes only. Recipient may not distribute, sell, or modify the Dataset without prior written consent from Vicomtech. Recipient agrees to maintain the confidentiality of the Dataset. All intellectual property rights remain with Vicomtech.
