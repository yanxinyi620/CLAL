from example.usrlts_utils.usrlts_main import run_usrlts


if __name__ == "__main__":
    
    path_prefix = 'D:/study/project/data/'

    run_usrlts(data_type='ucr', dataset='Mallat', path=path_prefix+'UCRArchive_2018', 
               save_path='output')
    run_usrlts(data_type='ucr', dataset='Chinatown', path=path_prefix+'UCRArchive_2018', 
               save_path='output', cuda=True, gpu=0)

    run_usrlts(data_type='uea', dataset='BasicMotions', path=path_prefix+'Multivariate2018_arff', 
               save_path='output')
    run_usrlts(data_type='uea', dataset='BasicMotions', path=path_prefix+'Multivariate2018_arff', 
               save_path='output', cuda=True, gpu=0)
