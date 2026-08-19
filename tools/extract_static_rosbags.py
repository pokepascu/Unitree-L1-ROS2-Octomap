#!/usr/bin/env python3
import copy, csv, json
from collections import Counter
from pathlib import Path
import yaml
from mcap.reader import make_reader
from mcap.writer import Writer

SOURCES={
  'HcMR_lab':Path('bags/raw/HcMR_lab_2026-08-07_21-13-45'),
  'ISR_5th_floor_run_1':Path('bags/raw/ISR_5th_floor_run_1_2026-08-07_21-31-58'),
  'ISR_5th_floor_run_2':Path('bags/raw/ISR_5th_floor_run_2_2026-08-07_21-48-31'),
}
# Strict stationary segments verified with |v| <= 0.02 m/s and |omega| <= 0.02 rad/s.
SELECTIONS=[
  # Approach 1: one representative static acquisition per environment.
  dict(approach='approach_1_single_static',environment='HcMR_lab',scan='scan_01',source='HcMR_lab',start=1786133723637021696,end=1786133738705244672,pose=(9.251,-0.595,0.0),note='Longest strict stationary interval available in the HcMR continuous bag; shorter than the ~30 s target.'),
  dict(approach='approach_1_single_static',environment='ISR_5th_floor',scan='scan_01',source='ISR_5th_floor_run_1',start=1786134757712538368,end=1786134793011322368,pose=(1.862,-1.070,0.0),note='Strict stationary interval longer than the ~30 s target.'),
  # Approach 2 HcMR: nearby, overlapping viewpoints chosen for ICP; all are genuinely stationary but shorter than 30 s.
  dict(approach='approach_2_three_static_icp',environment='HcMR_lab',scan='scan_01',source='HcMR_lab',start=1786133698660790784,end=1786133712355343616,pose=(7.072,-1.158,0.0),note='Strict stationary interval.'),
  dict(approach='approach_2_three_static_icp',environment='HcMR_lab',scan='scan_02',source='HcMR_lab',start=1786133723637021696,end=1786133738705244672,pose=(9.251,-0.595,0.0),note='Strict stationary interval.'),
  dict(approach='approach_2_three_static_icp',environment='HcMR_lab',scan='scan_03',source='HcMR_lab',start=1786133755547356928,end=1786133762945741568,pose=(11.806,-0.188,0.0),note='Strict stationary interval; short but spatially close enough to favour cloud overlap for ICP.'),
  # Approach 2 ISR: three successive nearby stationary viewpoints; scan 2/3 are short stops, explicitly documented.
  dict(approach='approach_2_three_static_icp',environment='ISR_5th_floor',scan='scan_01',source='ISR_5th_floor_run_1',start=1786134757712538368,end=1786134793011322368,pose=(1.862,-1.070,0.0),note='Strict stationary interval >30 s.'),
  dict(approach='approach_2_three_static_icp',environment='ISR_5th_floor',scan='scan_02',source='ISR_5th_floor_run_1',start=1786134801736246528,end=1786134805059976704,pose=(2.307,-3.125,0.0),note='Strict stationary interval; only ~3.3 s, retained because it is a nearby overlapping viewpoint.'),
  dict(approach='approach_2_three_static_icp',environment='ISR_5th_floor',scan='scan_03',source='ISR_5th_floor_run_1',start=1786134817986674688,end=1786134821518245120,pose=(1.949,-5.399,0.0),note='Strict stationary interval; only ~3.5 s, retained because it is a nearby overlapping viewpoint.'),
]

def source_paths(name):
  d=SOURCES[name]
  return next(d.glob('*.mcap')), d/'metadata.yaml'

def write_subset(sel):
  src,meta_path=source_paths(sel['source'])
  dest=Path('study_data')/sel['approach']/sel['environment']/sel['scan']
  dest.mkdir(parents=True,exist_ok=True)
  out=dest/'static_segment.mcap'
  schema_map={}; channel_map={}; counts=Counter(); first=None; last=None; total=0
  with src.open('rb') as f, out.open('wb') as g:
    reader=make_reader(f); writer=Writer(g); writer.start(profile='ros2',library='mcap-python derived static subset')
    for schema,channel,msg in reader.iter_messages(start_time=sel['start'],end_time=sel['end']):
      if schema is not None and schema.id not in schema_map:
        schema_map[schema.id]=writer.register_schema(schema.name,schema.encoding,schema.data)
      if channel.id not in channel_map:
        channel_map[channel.id]=writer.register_channel(channel.topic,channel.message_encoding,schema_map.get(channel.schema_id,0),dict(channel.metadata))
      writer.add_message(channel_map[channel.id],msg.log_time,msg.data,msg.publish_time,msg.sequence)
      counts[channel.topic]+=1; total+=1
      first=msg.log_time if first is None else min(first,msg.log_time)
      last=msg.log_time if last is None else max(last,msg.log_time)
    writer.finish()
  if total==0: raise RuntimeError(f'Empty selection: {sel}')
  original=yaml.safe_load(meta_path.read_text()); info=copy.deepcopy(original['rosbag2_bagfile_information'])
  topics=[]
  for item in info.get('topics_with_message_count',[]):
    name=item['topic_metadata']['name']
    if counts.get(name,0)>0:
      ni=copy.deepcopy(item); ni['message_count']=int(counts[name]); topics.append(ni)
  duration=int(last-first) if first is not None and last is not None else 0
  info['topics_with_message_count']=topics; info['message_count']=int(total)
  info['starting_time']={'nanoseconds_since_epoch':int(first)}; info['duration']={'nanoseconds':duration}
  info['relative_file_paths']=['static_segment.mcap']; info['files']=[{'path':'static_segment.mcap','starting_time':{'nanoseconds_since_epoch':int(first)},'duration':{'nanoseconds':duration},'message_count':int(total)}]
  (dest/'metadata.yaml').write_text(yaml.safe_dump({'rosbag2_bagfile_information':info},sort_keys=False))
  selection=dict(sel); selection['duration_s']=(sel['end']-sel['start'])/1e9; selection['message_count']=total; selection['topic_counts']=dict(sorted(counts.items()))
  (dest/'selection.yaml').write_text(yaml.safe_dump(selection,sort_keys=False))
  return selection

rows=[write_subset(s) for s in SELECTIONS]
with open('study_data/static_selection_report.csv','w',newline='') as f:
  w=csv.writer(f); w.writerow(['approach','environment','scan','source','start_ns','end_ns','duration_s','pose_x_m','pose_y_m','pose_z_m','message_count','note'])
  for r in rows: w.writerow([r['approach'],r['environment'],r['scan'],r['source'],r['start'],r['end'],r['duration_s'],*r['pose'],r['message_count'],r['note']])
