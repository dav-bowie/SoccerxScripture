#!/usr/bin/env python3
"""
DaVinci Resolve timeline builder for: skill_chaos_001
Run with Resolve open and a project loaded.

Usage (Resolve must be running):
  /Applications/DaVinci\ Resolve/DaVinci\ Resolve.app/Contents/MacOS/DaVinci\ Resolve -script skill_chaos_001_resolve.py
"""

import DaVinciResolveScript as dvr

resolve = dvr.scriptapp("Resolve")
pm = resolve.GetProjectManager()
project = pm.GetCurrentProject()
if not project:
    raise RuntimeError("Open a Resolve project first")

media_pool = project.GetMediaPool()
root = media_pool.GetRootFolder()

TIMELINE_NAME = "skill_chaos_001"
TIMELINE_ITEMS = [{'slot': 'hook', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 14.35, 'out': 15.06}, {'slot': 'beat_1', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 39.1, 'out': 39.81}, {'slot': 'beat_2', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_3', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_4', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'payoff', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_extra_6', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_extra_7', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_extra_8', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_extra_9', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_extra_10', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'beat_extra_11', 'path': '/Users/db/Desktop/SoccerxScripture/personal/video/timeline_1.mov', 'in': 31.85, 'out': 32.56}, {'slot': 'outro', 'path': '/Users/db/Desktop/SoccerxScripture/assets/outro/outro_master_2s.mov', 'in': 0, 'out': 2.0}]

timeline = None
for i in range(1, project.GetTimelineCount() + 1):
    tl = project.GetTimelineByIndex(i)
    if tl.GetName() == TIMELINE_NAME:
        timeline = tl
        break

if not timeline:
    timeline = media_pool.CreateEmptyTimeline(TIMELINE_NAME)
    project.SetCurrentTimeline(timeline)

media_pool.SetCurrentFolder(root)

for item in TIMELINE_ITEMS:
    media_pool.ImportMedia([item["path"]])

print(f"Timeline '{TIMELINE_NAME}' ready.")
print("Import clips from EDL if auto-append fails:")
print("  /Users/db/Desktop/SoccerxScripture/plans/skill_chaos_001_edl.csv")
print("Markers file:")
print("  /Users/db/Desktop/SoccerxScripture/plans/skill_chaos_001_markers.csv")
