/home/haoyue/anaconda3/bin/python /home/haoyue/codes/Pose-Transfer-master/test.py --dataroot /data0/haoyue/codes/datasets/market_data/ --name market_PATN_ganppssim2perl1_win7_batch32 --model PATN --phase test --dataset_mode keypoint --norm batch --batchSize 10 --resize_or_crop no --gpu_ids 2 --BP_input_nc 18 --no_flip --which_model_netG PATN --checkpoints_dir /data0/haoyue/codes/trained_models/Pose-Transfer-master/checkpoints3 --pairLst /data0/haoyue/codes/datasets/market_data/market-pairs-test.csv --with_D_PP 0 --with_D_PB 0 --which_epoch 660 --results_dir /data0/haoyue/codes/results3 --display_id 0

/home/haoyue/anaconda3/envs/TF_env2/bin/python /home/haoyue/codes/Pose-Transfer-master/tool/getMetrics_market.py --generated_images_dir /data0/haoyue/codes/results3/market_PATN_ganppssim2perl1_win7_batch32/test_660/images
