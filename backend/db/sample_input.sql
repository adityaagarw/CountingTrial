INSERT INTO camera_master (
  camera_url_id,
  camera_type,
  resolution,
  fps,
  focal_length,
  mac,
  protocols,
  uid,
  pwd,
  port,
  make_model,
  added_at,
  modified_at
)
VALUES (
  'your_camera_url_id',
  'test_cam',
  'your_resolution',
  10,
  2,
  'your_mac',
  'your_protocols',
  'your_uid',
  'your_pwd',
  'your_port',
  'your_make_model',
  NOW(),
  NOW()
);

INSERT INTO feed_master (
  camera_id,
  name, 
  location,
  area_covered,
  url,
  feature_list,
  feed_type,
  config
)
VALUES (
  1,
  'ym_feed',
  'ym',
  '1024x576',
  '../ym2.mp4',
  '{1}',
  'video',
  '{"model_name":"yolov8n.pt","classes_to_count":[0],"save_frames":1000,"track_length":100,"buffer_size":0,"target_width":1024,"target_height":576,"track_confidence":0.15}'
);