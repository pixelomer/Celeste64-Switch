"""Bound startup asset concurrency without changing parser or upload behavior."""

def optimize_asset_queue(out, replace):
    p = out / 'managed/Game/Assets.cs'
    s = p.read_text()
    s = replace(s, 'var tasks = new List<Task>();', 'var tasks = new List<Task>();\n        var loadJobs = new List<Action>();\n        int nextLoadJob = -1;')
    s = replace(s, 'tasks.Add(Task.Run(() =>', 'loadJobs.Add(() =>', 5)
    s = replace(s, '}));', '});', 5)
    s = replace(s, '// load audio', '// Fixed workers avoid thread-pool expansion while cold parsers initialize.\n        for (int worker = 0; worker < Math.Min(3, Environment.ProcessorCount); worker++)\n            tasks.Add(Task.Run(() => {\n                int job;\n                while ((job = Interlocked.Increment(ref nextLoadJob)) < loadJobs.Count)\n                    loadJobs[job]();\n            }));\n\n        // load audio')
    p.write_text(s)
